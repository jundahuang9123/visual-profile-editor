"""The blackboard: one SQLite file that holds everything put on the workbench.

Design
------
* ``entries`` is append-only. It is the audit trail a human reads to follow what
  each knowledge source (rule, model, person) did and why.
* The other tables hold the CURRENT state of each object (atoms, assessments,
  candidates, changes, artefacts ...) as JSON documents of the contract models,
  so the workbench can render a project without replaying the log.
* API keys never reach this module.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any, Iterable, TypeVar

from pydantic import BaseModel

from ..contracts import (
    Artifact,
    Atom,
    AtomAssessment,
    BlackboardEntry,
    Candidate,
    Conflict,
    ConformanceReport,
    LLMCallRecord,
    ProfileChange,
    Project,
    now_iso,
)

ModelT = TypeVar("ModelT", bound=BaseModel)

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    doc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS objects (
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,          -- atom | assessment | candidates | change | conflict | artifact | conformance
    id TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    doc TEXT NOT NULL,
    PRIMARY KEY (project_id, kind, id)
);
CREATE TABLE IF NOT EXISTS entries (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    kind TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    doc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS entries_by_project ON entries (project_id, seq);
CREATE INDEX IF NOT EXISTS entries_by_subject ON entries (project_id, subject_type, subject_id);
CREATE TABLE IF NOT EXISTS llm_calls (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    doc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS llm_calls_by_project ON llm_calls (project_id, seq);
CREATE INDEX IF NOT EXISTS llm_calls_by_hash ON llm_calls (request_hash);
"""


class Store:
    """Thread-safe access to one blackboard database (``:memory:`` is fine for tests)."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            if self.path != ":memory:":
                self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(SCHEMA)
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # -- projects -----------------------------------------------------------

    def save_project(self, project: Project) -> Project:
        project.updated_at = now_iso()
        with self._lock:
            self._db.execute(
                "INSERT INTO projects (id, doc) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET doc = excluded.doc",
                (project.id, project.model_dump_json()),
            )
            self._db.commit()
        return project

    def get_project(self, project_id: str) -> Project | None:
        with self._lock:
            row = self._db.execute("SELECT doc FROM projects WHERE id = ?", (project_id,)).fetchone()
        return Project.model_validate_json(row["doc"]) if row else None

    def list_projects(self) -> list[Project]:
        with self._lock:
            rows = self._db.execute("SELECT doc FROM projects").fetchall()
        projects = [Project.model_validate_json(row["doc"]) for row in rows]
        return sorted(projects, key=lambda project: project.updated_at, reverse=True)

    def delete_project(self, project_id: str) -> None:
        with self._lock:
            for table in ("projects",):
                self._db.execute(f"DELETE FROM {table} WHERE id = ?", (project_id,))
            for table in ("objects", "entries", "llm_calls"):
                self._db.execute(f"DELETE FROM {table} WHERE project_id = ?", (project_id,))
            self._db.commit()

    # -- generic current-state objects ------------------------------------

    def _put(self, project_id: str, kind: str, object_id: str, model: BaseModel, position: int | None = None) -> None:
        with self._lock:
            if position is None:
                row = self._db.execute(
                    "SELECT position FROM objects WHERE project_id = ? AND kind = ? AND id = ?",
                    (project_id, kind, object_id),
                ).fetchone()
                if row is not None:
                    position = row["position"]
                else:
                    top = self._db.execute(
                        "SELECT COALESCE(MAX(position), -1) AS top FROM objects WHERE project_id = ? AND kind = ?",
                        (project_id, kind),
                    ).fetchone()
                    position = top["top"] + 1
            self._db.execute(
                "INSERT INTO objects (project_id, kind, id, position, doc) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(project_id, kind, id) DO UPDATE SET doc = excluded.doc, position = excluded.position",
                (project_id, kind, object_id, position, model.model_dump_json()),
            )
            self._db.commit()

    def _get(self, project_id: str, kind: str, object_id: str, model_type: type[ModelT]) -> ModelT | None:
        with self._lock:
            row = self._db.execute(
                "SELECT doc FROM objects WHERE project_id = ? AND kind = ? AND id = ?",
                (project_id, kind, object_id),
            ).fetchone()
        return model_type.model_validate_json(row["doc"]) if row else None

    def _list(self, project_id: str, kind: str, model_type: type[ModelT]) -> list[ModelT]:
        with self._lock:
            rows = self._db.execute(
                "SELECT doc FROM objects WHERE project_id = ? AND kind = ? ORDER BY position, id",
                (project_id, kind),
            ).fetchall()
        return [model_type.model_validate_json(row["doc"]) for row in rows]

    def _delete(self, project_id: str, kind: str, object_id: str | None = None) -> None:
        with self._lock:
            if object_id is None:
                self._db.execute("DELETE FROM objects WHERE project_id = ? AND kind = ?", (project_id, kind))
            else:
                self._db.execute(
                    "DELETE FROM objects WHERE project_id = ? AND kind = ? AND id = ?",
                    (project_id, kind, object_id),
                )
            self._db.commit()

    # -- atoms --------------------------------------------------------------

    def replace_atoms(self, project_id: str, atoms: Iterable[Atom]) -> None:
        self._delete(project_id, "atom")
        for position, atom in enumerate(atoms):
            self._put(project_id, "atom", atom.id, atom, position)

    def save_atom(self, project_id: str, atom: Atom) -> None:
        self._put(project_id, "atom", atom.id, atom)

    def get_atom(self, project_id: str, atom_id: str) -> Atom | None:
        return self._get(project_id, "atom", atom_id, Atom)

    def list_atoms(self, project_id: str) -> list[Atom]:
        return self._list(project_id, "atom", Atom)

    def delete_atom(self, project_id: str, atom_id: str) -> None:
        self._delete(project_id, "atom", atom_id)

    # -- assessments and candidates ----------------------------------------

    def save_assessment(self, project_id: str, assessment: AtomAssessment) -> None:
        self._put(project_id, "assessment", assessment.atom_id, assessment)

    def get_assessment(self, project_id: str, atom_id: str) -> AtomAssessment | None:
        return self._get(project_id, "assessment", atom_id, AtomAssessment)

    def list_assessments(self, project_id: str) -> list[AtomAssessment]:
        return self._list(project_id, "assessment", AtomAssessment)

    def save_candidates(self, project_id: str, atom_id: str, candidates: list[Candidate]) -> None:
        self._put(project_id, "candidates", atom_id, _CandidateList(atom_id=atom_id, candidates=candidates))

    def get_candidates(self, project_id: str, atom_id: str) -> list[Candidate]:
        found = self._get(project_id, "candidates", atom_id, _CandidateList)
        return found.candidates if found else []

    def all_candidates(self, project_id: str) -> dict[str, list[Candidate]]:
        return {item.atom_id: item.candidates for item in self._list(project_id, "candidates", _CandidateList)}

    # -- changes and conflicts ---------------------------------------------

    def save_change(self, project_id: str, change: ProfileChange) -> None:
        self._put(project_id, "change", change.id, change)

    def get_change(self, project_id: str, change_id: str) -> ProfileChange | None:
        return self._get(project_id, "change", change_id, ProfileChange)

    def list_changes(self, project_id: str, *, include_superseded: bool = False) -> list[ProfileChange]:
        changes = self._list(project_id, "change", ProfileChange)
        if include_superseded:
            return changes
        return [change for change in changes if change.decision.status != "superseded"]

    def delete_changes(self, project_id: str) -> None:
        self._delete(project_id, "change")

    def replace_conflicts(self, project_id: str, conflicts: Iterable[Conflict]) -> None:
        self._delete(project_id, "conflict")
        for position, conflict in enumerate(conflicts):
            self._put(project_id, "conflict", conflict.id, conflict, position)

    def save_conflict(self, project_id: str, conflict: Conflict) -> None:
        self._put(project_id, "conflict", conflict.id, conflict)

    def list_conflicts(self, project_id: str) -> list[Conflict]:
        return self._list(project_id, "conflict", Conflict)

    # -- artefacts and conformance -----------------------------------------

    def replace_artifacts(self, project_id: str, artifacts: Iterable[Artifact]) -> None:
        self._delete(project_id, "artifact")
        for position, artifact in enumerate(artifacts):
            self._put(project_id, "artifact", artifact.name, artifact, position)

    def list_artifacts(self, project_id: str) -> list[Artifact]:
        return self._list(project_id, "artifact", Artifact)

    def get_artifact(self, project_id: str, name: str) -> Artifact | None:
        return self._get(project_id, "artifact", name, Artifact)

    def clear_artifacts(self, project_id: str) -> None:
        self._delete(project_id, "artifact")

    def save_conformance(self, project_id: str, report: ConformanceReport) -> None:
        self._put(project_id, "conformance", "current", report, 0)

    def get_conformance(self, project_id: str) -> ConformanceReport | None:
        return self._get(project_id, "conformance", "current", ConformanceReport)

    def clear_conformance(self, project_id: str) -> None:
        self._delete(project_id, "conformance")

    # -- blackboard entries (append-only) ----------------------------------

    def append_entry(self, project_id: str, entry: BlackboardEntry) -> BlackboardEntry:
        entry.project_id = project_id
        entry.id = entry.id or f"e-{uuid.uuid4().hex[:12]}"
        with self._lock:
            cursor = self._db.execute(
                "INSERT INTO entries (id, project_id, stage, kind, subject_type, subject_id, doc) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry.id, project_id, entry.stage, entry.kind, entry.subject_type, entry.subject_id, "{}"),
            )
            entry.seq = int(cursor.lastrowid or 0)
            self._db.execute("UPDATE entries SET doc = ? WHERE seq = ?", (entry.model_dump_json(), entry.seq))
            self._db.commit()
        return entry

    def list_entries(
        self,
        project_id: str,
        *,
        stage: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        after_seq: int = 0,
        limit: int = 1000,
    ) -> list[BlackboardEntry]:
        clauses, params = ["project_id = ?", "seq > ?"], [project_id, after_seq]
        for column, value in (("stage", stage), ("subject_type", subject_type), ("subject_id", subject_id)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        params.append(limit)
        with self._lock:
            rows = self._db.execute(
                f"SELECT doc FROM entries WHERE {' AND '.join(clauses)} ORDER BY seq LIMIT ?", params
            ).fetchall()
        return [BlackboardEntry.model_validate_json(row["doc"]) for row in rows]

    # -- model call records -------------------------------------------------

    def add_llm_call(self, project_id: str, record: LLMCallRecord) -> LLMCallRecord:
        record.project_id = project_id
        record.id = record.id or f"call-{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._db.execute(
                "INSERT INTO llm_calls (id, project_id, request_hash, subject_id, doc) VALUES (?, ?, ?, ?, ?)",
                (record.id, project_id, record.request_hash, record.subject_id, record.model_dump_json()),
            )
            self._db.commit()
        return record

    def get_llm_call(self, project_id: str, call_id: str) -> LLMCallRecord | None:
        with self._lock:
            row = self._db.execute(
                "SELECT doc FROM llm_calls WHERE project_id = ? AND id = ?", (project_id, call_id)
            ).fetchone()
        return LLMCallRecord.model_validate_json(row["doc"]) if row else None

    def list_llm_calls(self, project_id: str, *, subject_id: str | None = None, limit: int = 2000) -> list[LLMCallRecord]:
        clauses, params = ["project_id = ?"], [project_id]
        if subject_id is not None:
            clauses.append("subject_id = ?")
            params.append(subject_id)
        params.append(limit)
        with self._lock:
            rows = self._db.execute(
                f"SELECT doc FROM llm_calls WHERE {' AND '.join(clauses)} ORDER BY seq LIMIT ?", params
            ).fetchall()
        return [LLMCallRecord.model_validate_json(row["doc"]) for row in rows]

    def find_cached_call(self, request_hash: str) -> LLMCallRecord | None:
        """Most recent successful call with the same request hash (replay cache)."""
        with self._lock:
            rows = self._db.execute(
                "SELECT doc FROM llm_calls WHERE request_hash = ? ORDER BY seq DESC LIMIT 20", (request_hash,)
            ).fetchall()
        for row in rows:
            record = LLMCallRecord.model_validate_json(row["doc"])
            if record.status == "ok" and record.response_text:
                return record
        return None

    # -- maintenance --------------------------------------------------------

    def clear_derived(self, project_id: str, kinds: Iterable[str]) -> None:
        """Drop current-state objects of the given kinds (the log is kept)."""
        for kind in kinds:
            self._delete(project_id, kind)

    def export_project(self, project_id: str) -> dict[str, Any]:
        """A self-contained JSON dump of a project: state, log and call records. No secrets."""
        project = self.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        conformance = self.get_conformance(project_id)
        return {
            "project": json.loads(project.model_dump_json()),
            "atoms": [json.loads(item.model_dump_json()) for item in self.list_atoms(project_id)],
            "assessments": [json.loads(item.model_dump_json()) for item in self.list_assessments(project_id)],
            "candidates": {
                atom_id: [json.loads(candidate.model_dump_json()) for candidate in candidates]
                for atom_id, candidates in self.all_candidates(project_id).items()
            },
            "changes": [
                json.loads(item.model_dump_json())
                for item in self.list_changes(project_id, include_superseded=True)
            ],
            "conflicts": [json.loads(item.model_dump_json()) for item in self.list_conflicts(project_id)],
            "artifacts": [json.loads(item.model_dump_json()) for item in self.list_artifacts(project_id)],
            "conformance": json.loads(conformance.model_dump_json()) if conformance else None,
            "entries": [json.loads(item.model_dump_json()) for item in self.list_entries(project_id, limit=100000)],
            "llm_calls": [json.loads(item.model_dump_json()) for item in self.list_llm_calls(project_id, limit=100000)],
        }


class _CandidateList(BaseModel):
    atom_id: str
    candidates: list[Candidate] = []
