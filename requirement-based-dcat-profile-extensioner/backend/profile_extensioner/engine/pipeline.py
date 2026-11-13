"""The pipeline: runs the stages, writes everything to the blackboard, applies the decision policy.

Decision policy (the LLM decides most things, a human has the final say):

* A change that passes every error-level check, is judged supported by its atoms
  (when the attribution check is on) and is confident enough is ``auto_accepted``:
  it stands unless a human overrules it.
* Anything else goes through bounded repair and then, if still unresolved, to the
  review queue as ``needs_review``.
* Nothing is released until a human signs off (``require_human_signoff``). Any
  human decision is final: later machine stages never overwrite it.
"""
from __future__ import annotations

import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterable

from ..compile.docs import compile_documentation, trace_csv, trace_rows
from ..compile.linkml_dsv import compile_dsv, compile_linkml
from ..compile.model import ProfileView, build_delta, build_view
from ..compile.shacl import compile_shacl, compile_vocabulary
from ..conformance.check import check_conformance
from ..contracts import (
    STAGE_ORDER,
    Artifact,
    Atom,
    AtomAssessment,
    AtomCoverage,
    BlackboardEntry,
    CheckResult,
    Decision,
    ProfileChange,
    Project,
    ProjectSnapshot,
    SignOff,
    now_iso,
)
from ..knowledge import KnowledgeBase, load_knowledge_base
from ..llm.base import LLMError
from ..llm.client import LLMClient
from ..llm.registry import Credentials, build_provider
from ..store.blackboard import Store
from .consolidate import consolidate
from .intake import run_intake
from .prompts import JUDGE_VERSION, build_judge_prompt
from .propose import propose_for_atom
from .repair import repair_change
from .retrieve import retrieve_candidates
from .schemas import AttributionOut
from .verbalise import verbalise_change
from .verify import VerifyContext, check_shapes_valid, has_errors, verify_assessment, verify_change_set

HUMAN_STATUSES = ("accepted", "rejected")


def is_human(change: ProfileChange) -> bool:
    """A decision a person took (accept, reject or undecided). Machine stages never overwrite it."""
    return change.decision.decided_by.startswith("human:")


class Pipeline:
    def __init__(self, store: Store, credentials: Credentials, project_id: str, *, data_dir=None) -> None:
        self.store = store
        self.credentials = credentials
        project = store.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        self.project = project
        self.kb: KnowledgeBase = load_knowledge_base(
            project.base_profile_id, profile_namespace=project.profile_namespace,
            profile_prefix=project.profile_prefix, exclude_namespaces=project.config.exclude_namespaces,
            data_dir=data_dir,
        )
        self._llm: LLMClient | None = None

    # -- helpers ------------------------------------------------------------

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            provider = build_provider(self.project.llm, self.credentials)
            self._llm = LLMClient(provider, self.project.llm, store=self.store, project_id=self.project.id)
        return self._llm

    @property
    def pid(self) -> str:
        return self.project.id

    def log(self, stage: str, kind: str, summary: str, *, subject_type: str = "project", subject_id: str = "",
            author: str = "rule:engine", payload: dict[str, Any] | None = None) -> None:
        self.store.append_entry(self.pid, BlackboardEntry(
            stage=stage, kind=kind, subject_type=subject_type, subject_id=subject_id,  # type: ignore[arg-type]
            author=author, summary=summary, payload=payload or {},
        ))

    def _update_project(self, mutate) -> None:
        """Reload the project, apply ``mutate`` and save: never write back a stale copy."""
        fresh = self.store.get_project(self.pid) or self.project
        mutate(fresh)
        self.store.save_project(fresh)
        self.project = fresh

    def set_stage(self, stage: str, state: str, *, cascade: bool = True) -> None:
        def mutate(project: Project) -> None:
            project.stage_states[stage] = state  # type: ignore[assignment]
            if state == "done" and cascade:
                for later in STAGE_ORDER[STAGE_ORDER.index(stage) + 1:]:
                    if project.stage_states.get(later) == "done":
                        project.stage_states[later] = "stale"
        self._update_project(mutate)

    def _withdraw_release(self, reason: str) -> None:
        def mutate(project: Project) -> None:
            for stage in ("compile", "conformance"):
                if project.stage_states.get(stage) == "done":
                    project.stage_states[stage] = "stale"
            if project.signoff is not None:
                project.signoff = None
                project.stage_states["review"] = "running"
        had = (self.store.get_project(self.pid) or self.project).signoff is not None
        self._update_project(mutate)
        if had:
            self.log("review", "note", f"The sign-off was withdrawn: {reason}")

    def active_atoms(self) -> list[Atom]:
        return [atom for atom in self.store.list_atoms(self.pid) if atom.active]

    def changes(self) -> list[ProfileChange]:
        return self.store.list_changes(self.pid, include_superseded=True)

    # -- stages -------------------------------------------------------------

    def run_intake(self) -> None:
        self.set_stage("intake", "running")
        atoms = self.active_atoms()
        for assessment in run_intake(atoms, self.kb):
            previous = self.store.get_assessment(self.pid, assessment.atom_id)
            if previous and previous.provenance.author_type == "human":
                previous.lint = assessment.lint
                assessment = previous
            self.store.save_assessment(self.pid, assessment)
            if assessment.lint:
                self.log("intake", "atom_lint", f"{len(assessment.lint)} finding(s): "
                         + ", ".join(issue.code for issue in assessment.lint), subject_type="atom",
                         subject_id=assessment.atom_id, author="rule:intake",
                         payload={"lint": [issue.model_dump() for issue in assessment.lint]})
        self.log("intake", "stage", f"{len(atoms)} active atom(s) checked against the atom contract.")
        self.set_stage("intake", "done")

    def run_retrieve(self) -> None:
        self.set_stage("retrieve", "running")
        config = self.project.config
        for atom in self.active_atoms():
            assessment = self.store.get_assessment(self.pid, atom.id)
            candidates = retrieve_candidates(atom, assessment, self.kb, top_k=config.top_k, use_hints=config.use_hints) \
                if config.retrieval else []
            self.store.save_candidates(self.pid, atom.id, candidates)
            self.log("retrieve", "candidates", f"{len(candidates)} candidate term(s); best: "
                     + (candidates[0].curie if candidates else "none"), subject_type="atom", subject_id=atom.id,
                     author="rule:retrieve", payload={"top": [c.curie for c in candidates[:5]]})
        self.set_stage("retrieve", "done")

    def run_propose(self, atom_ids: Iterable[str] | None = None) -> None:
        self.set_stage("propose", "running")
        selected = set(atom_ids) if atom_ids is not None else None
        atoms = [a for a in self.active_atoms() if selected is None or a.id in selected]
        self._withdraw_release("the proposals were regenerated")
        existing = [c for c in self.changes() if c.decision.status != "superseded"]
        human_owned = {aid for c in existing if is_human(c) for aid in c.atom_ids}
        chosen = {a.id for a in atoms}
        # Re-proposing replaces machine-made changes that cover ONLY re-proposed atoms; human decisions are kept.
        for change in existing:
            if not is_human(change) and change.atom_ids and set(change.atom_ids) <= chosen:
                change.decision = Decision(status="superseded", decided_by="rule:pipeline", note="re-proposed")
                self.store.save_change(self.pid, change)
        work = []
        for atom in atoms:
            assessment = self.store.get_assessment(self.pid, atom.id)
            if assessment is None or atom.id in human_owned:
                continue
            if assessment.provenance.author_type == "human" or any(i.severity == "error" for i in assessment.lint):
                continue
            work.append((atom, assessment))

        def one(item):
            atom, assessment = item
            return atom, propose_for_atom(atom, assessment, self.store.get_candidates(self.pid, atom.id),
                                          self.kb, self.llm, self.project)

        workers = max(1, self.project.config.max_parallel_calls)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, work))
        for atom, result in results:
            self.store.save_assessment(self.pid, result.assessment)
            for change in result.changes:
                self.store.save_change(self.pid, change)
            b1 = verify_assessment(result.assessment, atom, self.kb)
            self.log("propose", "proposal",
                     f"{result.assessment.disposition}: " + ("; ".join(verbalise_change(c, self.kb) for c in result.changes)
                                                             or result.assessment.reason)[:400],
                     subject_type="atom", subject_id=atom.id, author=result.assessment.provenance.author,
                     payload={"changes": [c.id for c in result.changes], "error": result.error,
                              "covered_by_check": [r.model_dump() for r in b1]})
            if b1 and not all(r.passed for r in b1):
                assessment = result.assessment
                assessment.disposition = "unclear"
                assessment.reason += " (Check B1: " + "; ".join(r.message for r in b1 if not r.passed) + ")"
                self.store.save_assessment(self.pid, assessment)
        self.log("propose", "stage", f"Proposals for {len(results)} atom(s).", author=self.llm.author)
        self.set_stage("propose", "done")

    def _context(self) -> VerifyContext:
        return VerifyContext(
            kb=self.kb, project=self.project, atoms={a.id: a for a in self.active_atoms()},
            candidates=self.store.all_candidates(self.pid),
        )

    def _attribution(self, change: ProfileChange, ctx: VerifyContext) -> CheckResult | None:
        if not self.project.config.attribution_check:
            return None
        atoms = [ctx.atoms[aid] for aid in change.atom_ids if aid in ctx.atoms]
        if not atoms:
            return None
        system, user, context = build_judge_prompt(change, atoms, self.kb)
        try:
            verdict, record = self.llm.generate(system=system, user=user, schema=AttributionOut, purpose="judge",
                                                subject_id=change.id, stage="verify", prompt_version=JUDGE_VERSION,
                                                context=context)
        except LLMError as exc:
            return CheckResult(check="T2", passed=False, severity="warning", message=f"Judge unavailable: {exc}")
        if record.id:
            change.provenance.call_ids.append(record.id)
        if verdict.verdict == "supported":
            return CheckResult(check="T2", passed=True, severity="info", message=verdict.explanation)
        return CheckResult(
            check="T2", passed=False, severity="warning" if verdict.verdict == "partially_supported" else "error",
            message=f"{verdict.verdict.replace('_', ' ')}: {verdict.explanation}",
            details={"unsupported_facets": list(verdict.unsupported_facets)},
        )

    def _decide(self, change: ProfileChange) -> None:
        if is_human(change):
            return
        errors = change.failed_checks()
        warnings = [r for r in change.verification if not r.passed and r.severity == "warning"]
        config = self.project.config
        if errors:
            status, note = "needs_review", "failed: " + ", ".join(sorted({r.check for r in errors}))
        elif not config.auto_accept:
            status, note = "needs_review", "automatic acceptance is switched off"
        elif change.confidence < config.auto_accept_min_confidence:
            status, note = "needs_review", f"confidence {change.confidence:.2f} below {config.auto_accept_min_confidence}"
        elif change.provenance.votes_total > 1 and change.provenance.votes_agreeing * 2 <= change.provenance.votes_total:
            status, note = "needs_review", "no majority among the independent proposals"
        else:
            status = "auto_accepted"
            note = "all checks passed" + (f"; {len(warnings)} warning(s) to look at" if warnings else "")
        change.decision = Decision(status=status, decided_by="rule:policy", note=note)  # type: ignore[arg-type]

    def run_verify(self) -> None:
        self.set_stage("verify", "running")
        self._withdraw_release("verification ran again")
        ctx = self._context()
        changes = self.changes()
        results = verify_change_set(changes, ctx)
        for change in changes:
            if change.id not in results:
                continue
            change.verification = results[change.id]
            if not has_errors(change.verification):
                t2 = self._attribution(change, ctx)
                if t2 is not None:
                    change.verification.append(t2)
            stored = self.store.get_change(self.pid, change.id)
            if stored is not None and is_human(stored):
                change.decision = stored.decision
            self._decide(change)
            self.store.save_change(self.pid, change)
            failed = [r for r in change.verification if not r.passed]
            self.log("verify", "check", f"{change.decision.status}: " + ("; ".join(f"{r.check} {r.message}" for r in failed)[:400]
                                                                           or "all checks passed"),
                     subject_type="change", subject_id=change.id, author="rule:verify",
                     payload={"failed": [r.model_dump() for r in failed]})
        self.set_stage("verify", "done")

    def run_repair(self) -> None:
        self.set_stage("repair", "running")
        self._withdraw_release("repair ran again")
        rounds = self.project.config.repair_rounds
        for round_number in range(1, rounds + 1):
            ctx = self._context()
            todo = [c for c in self.changes() if c.decision.status == "needs_review" and has_errors(c.verification)
                    and not is_human(c) and c.provenance.author_type != "human"
                    and c.provenance.repair_round < round_number]
            if not todo:
                break
            for change in todo:
                atoms = [ctx.atoms[a] for a in change.atom_ids if a in ctx.atoms]
                candidates = [c for a in change.atom_ids for c in ctx.candidates.get(a, [])]
                result = repair_change(change, change.failed_checks(), atoms, candidates, self.kb, self.llm,
                                       self.project, round_number=round_number)
                if result.action == "revise" and result.change is not None:
                    change.decision = Decision(status="superseded", decided_by=self.llm.author,
                                               note=f"repaired in round {round_number}")
                    self.store.save_change(self.pid, change)
                    revised = result.change
                    ctx.changes = self.changes() + [revised]
                    revised.verification = verify_change_set(
                        [c for c in ctx.changes if c.decision.status != "superseded"], ctx).get(revised.id, [])
                    if not has_errors(revised.verification):
                        t2 = self._attribution(revised, ctx)
                        if t2:
                            revised.verification.append(t2)
                    self._decide(revised)
                    self.store.save_change(self.pid, revised)
                    self.log("repair", "repair", f"round {round_number}: {result.note} -> {revised.decision.status}",
                             subject_type="change", subject_id=revised.id, author=self.llm.author,
                             payload={"supersedes": change.id})
                elif result.action == "withdraw":
                    change.decision = Decision(status="rejected", decided_by=self.llm.author,
                                               note=f"withdrawn by the repairer: {result.note}")
                    self.store.save_change(self.pid, change)
                    self.log("repair", "withdraw", result.note, subject_type="change", subject_id=change.id,
                             author=self.llm.author)
                else:
                    change.provenance.repair_round = round_number
                    self.store.save_change(self.pid, change)
                    self.log("repair", "repair_failed", result.note, subject_type="change", subject_id=change.id)
        self.set_stage("repair", "done")

    def run_consolidate(self) -> None:
        self.set_stage("consolidate", "running")
        self._withdraw_release("consolidation ran again")
        changes, conflicts = consolidate(self.changes())
        for change in changes:
            self.store.save_change(self.pid, change)
        self.store.replace_conflicts(self.pid, conflicts)
        for conflict in conflicts:
            for cid in conflict.change_ids:
                change = self.store.get_change(self.pid, cid)
                if change and not is_human(change):
                    change.decision = Decision(status="needs_review", decided_by="rule:consolidate",
                                               note=f"conflict {conflict.id}: {conflict.description}")
                    self.store.save_change(self.pid, change)
            self.log("consolidate", "conflict", conflict.description, author="rule:consolidate",
                     payload=conflict.model_dump())
        merged = sum(1 for c in changes if c.decision.status == "superseded" and c.decision.decided_by == "rule:consolidate")
        self.log("consolidate", "stage", f"{merged} duplicate change(s) merged, {len(conflicts)} conflict(s).")
        # Merged changes cover more atoms: verify again so every claim is checked.
        ctx = self._context()
        results = verify_change_set(self.changes(), ctx)
        for change in self.changes():
            if change.id in results and change.decision.status not in ("superseded", "rejected"):
                kept_t2 = [r for r in change.verification if r.check == "T2"]
                change.verification = results[change.id] + kept_t2
                self._decide(change)
                self.store.save_change(self.pid, change)
        self.set_stage("consolidate", "done")

    def view(self) -> ProfileView:
        return build_view(self.project, self.kb, self.store.list_atoms(self.pid), self.changes())

    def run_compile(self, *, cascade: bool = True) -> list[Artifact]:
        self.set_stage("compile", "running")
        view = self.view()
        shacl = compile_shacl(view)
        v6 = check_shapes_valid(shacl)
        rows = trace_rows(view, self.store.list_assessments(self.pid), self.coverage(), self.changes())
        conformance = self.store.get_conformance(self.pid)
        import yaml

        delta = build_delta(view)
        artifacts = [
            _artifact("extension.shacl.ttl", "SHACL shapes (delta on the base)", "text/turtle", shacl),
            _artifact("extension.vocabulary.ttl", "Minted terms (RDFS/OWL)", "text/turtle", compile_vocabulary(view)),
            _artifact("extension.linkml.yaml", "LinkML (Visual Profile Editor)", "application/yaml", compile_linkml(view)),
            _artifact("extension.dsv.ttl", "DSV (Dataspecer)", "text/turtle", compile_dsv(view)),
            _artifact("extension.delta.yaml", "Profile delta (RQ2 scoring contract)", "application/yaml",
                      yaml.safe_dump(delta.model_dump(exclude_none=True), sort_keys=False, allow_unicode=True)),
            _artifact("trace-matrix.csv", "Traceability matrix", "text/csv", trace_csv(rows)),
            _artifact("README.md", "Profile documentation", "text/markdown",
                      compile_documentation(view, rows, conformance.summary if conformance else "")),
        ]
        self.store.replace_artifacts(self.pid, artifacts)
        self.log("compile", "artifact", f"{len(artifacts)} artefact(s) compiled from {len(view.changes)} included change(s); "
                 f"V6 {'passed' if v6.passed else 'FAILED'}: {v6.message}", author="rule:compile",
                 payload={"v6": v6.model_dump()})
        self.set_stage("compile", "done", cascade=cascade)
        return artifacts

    def run_conformance(self) -> None:
        self.set_stage("conformance", "running")
        report = check_conformance(self.view())
        self.store.save_conformance(self.pid, report)
        self.log("conformance", "conformance", report.summary, author="rule:conformance",
                 payload={"verdict": report.verdict})
        # Documentation carries the verdict; recompiling must not make this check stale.
        self.run_compile(cascade=False)
        self.set_stage("conformance", "done", cascade=False)

    def run_all(self, *, from_stage: str = "intake") -> None:
        steps = {
            "intake": self.run_intake, "retrieve": self.run_retrieve, "propose": self.run_propose,
            "verify": self.run_verify, "repair": self.run_repair, "consolidate": self.run_consolidate,
            "compile": self.run_compile, "conformance": self.run_conformance,
        }
        start = STAGE_ORDER.index(from_stage)
        for stage in STAGE_ORDER[start:]:
            if stage in steps:
                try:
                    steps[stage]()
                except Exception as exc:
                    self.set_stage(stage, "failed")
                    self.log(stage, "error", f"{type(exc).__name__}: {exc}")
                    raise
        self._update_project(lambda project: project.stage_states.__setitem__(
            "review", "running" if project.signoff is None else "done"))

    # -- coverage and metrics ----------------------------------------------

    def coverage(self) -> dict[str, AtomCoverage]:
        assessments = {a.atom_id: a for a in self.store.list_assessments(self.pid)}
        live = [c for c in self.changes() if c.decision.status not in ("superseded", "rejected")]
        result: dict[str, AtomCoverage] = {}
        for atom in self.active_atoms():
            mine = [c for c in live if atom.id in c.atom_ids]
            assessment = assessments.get(atom.id)
            if any(c.included and any(l.atom_id == atom.id and l.coverage == "full" for l in c.covers) for c in mine):
                result[atom.id] = "addressed"
            elif any(c.included for c in mine):
                result[atom.id] = "partially_addressed"
            elif mine:
                result[atom.id] = "pending_review"
            elif assessment and assessment.disposition == "covered_by_base":
                result[atom.id] = "covered_by_base"
            elif assessment and assessment.disposition == "out_of_scope":
                result[atom.id] = "out_of_scope"
            else:
                result[atom.id] = "unaddressed"
        return result

    def metrics(self) -> dict[str, Any]:
        changes = self.changes()
        live = [c for c in changes if c.decision.status not in ("superseded",)]
        included = [c for c in live if c.included]
        coverage = self.coverage()
        counts: dict[str, int] = {}
        for value in coverage.values():
            counts[value] = counts.get(value, 0) + 1
        calls = self.store.list_llm_calls(self.pid)
        kinds: dict[str, int] = {}
        for c in included:
            kinds[c.kind] = kinds.get(c.kind, 0) + 1
        properties = [c for c in included if c.path and c.kind != "usage_note"]
        return {
            "atoms": len(coverage),
            "coverage": counts,
            "changes_included": len(included),
            "changes_by_kind": kinds,
            "auto_accepted": sum(1 for c in live if c.decision.status == "auto_accepted"),
            "accepted_by_human": sum(1 for c in live if c.decision.status == "accepted"),
            "needs_review": sum(1 for c in live if c.decision.status == "needs_review"),
            "rejected": sum(1 for c in live if c.decision.status == "rejected"),
            "extension_rate": round(sum(1 for c in properties if c.kind == "mint_property") / len(properties), 3) if properties else 0.0,
            "repaired": sum(1 for c in changes if c.provenance.repair_round > 0 and c.decision.status != "superseded"),
            "llm_calls": len(calls),
            "llm_calls_cached": sum(1 for c in calls if c.cached),
            "input_tokens": sum(c.input_tokens for c in calls),
            "output_tokens": sum(c.output_tokens for c in calls),
        }

    def snapshot(self) -> ProjectSnapshot:
        return ProjectSnapshot(
            project=self.project, atoms=self.store.list_atoms(self.pid),
            assessments=self.store.list_assessments(self.pid), candidates=self.store.all_candidates(self.pid),
            changes=self.store.list_changes(self.pid, include_superseded=True),
            conflicts=self.store.list_conflicts(self.pid), coverage=self.coverage(),
            artifacts=self.store.list_artifacts(self.pid), conformance=self.store.get_conformance(self.pid),
            metrics=self.metrics(),
        )

    # -- human actions -------------------------------------------------------

    def decide(self, change_id: str, status: str, by: str, note: str = "") -> ProfileChange:
        change = self.store.get_change(self.pid, change_id)
        if change is None:
            raise KeyError(change_id)
        if status not in ("accepted", "rejected", "needs_review"):
            raise ValueError("status must be accepted, rejected or needs_review")
        if change.decision.status == "superseded":
            raise ValueError(f"{change_id} has been replaced by a newer version; decide on that one.")
        if status == "accepted" and has_errors(change.verification):
            note = (note + " " if note else "") + "(accepted despite failing checks: " + \
                   ", ".join(sorted({r.check for r in change.failed_checks()})) + ")"
        before = change.decision.status
        change.decision = Decision(status=status, decided_by=f"human:{by}", note=note)  # type: ignore[arg-type]
        self.store.save_change(self.pid, change)
        self.log("review", "human_decision", f"{before} -> {status}" + (f": {note}" if note else ""),
                 subject_type="change", subject_id=change_id, author=f"human:{by}")
        self._mark_released_stale()
        return change

    def edit_change(self, change_id: str, edited: ProfileChange, by: str, note: str = "") -> ProfileChange:
        """A human edit creates a new version (the old one is kept as superseded) and is verified at once."""
        old = self.store.get_change(self.pid, change_id)
        if old is None:
            raise KeyError(change_id)
        new = edited.model_copy(deep=True)
        if old.decision.status == "superseded":
            raise ValueError(f"{change_id} has been replaced by a newer version; edit that one.")
        new.id = f"{change_id.split('~')[0]}~h{uuid.uuid4().hex[:8]}"
        new.supersedes = change_id
        new.provenance.author_type = "human"
        new.provenance.author = f"human:{by}"
        new.engine_notes = [*old.engine_notes, f"edited by {by}" + (f": {note}" if note else "")]
        old.decision = Decision(status="superseded", decided_by=f"human:{by}", note="edited")
        self.store.save_change(self.pid, old)
        ctx = self._context()
        ctx.changes = [c for c in self.changes() if c.id != old.id] + [new]
        new.verification = verify_change_set(ctx.changes, ctx).get(new.id, [])
        new.decision = Decision(status="accepted", decided_by=f"human:{by}", note=note or "edited and accepted")
        self.store.save_change(self.pid, new)
        self.log("review", "human_edit", f"edited {change_id}: {verbalise_change(new, self.kb)}",
                 subject_type="change", subject_id=new.id, author=f"human:{by}",
                 payload={"supersedes": change_id, "failed": [r.check for r in new.failed_checks()]})
        self._mark_released_stale()
        return new

    def override_assessment(self, atom_id: str, disposition: str, reason: str, by: str) -> AtomAssessment:
        assessment = self.store.get_assessment(self.pid, atom_id) or AtomAssessment(atom_id=atom_id)
        assessment.disposition = disposition  # type: ignore[assignment]
        assessment.reason = reason
        assessment.provenance.author_type = "human"
        assessment.provenance.author = f"human:{by}"
        self.store.save_assessment(self.pid, assessment)
        self.log("review", "human_decision", f"atom disposition set to {disposition}: {reason}",
                 subject_type="atom", subject_id=atom_id, author=f"human:{by}")
        if disposition in ("covered_by_base", "out_of_scope"):
            # Machine changes that exist only for this atom no longer have a reason to be in the profile.
            for change in self.changes():
                if change.atom_ids == [atom_id] and not is_human(change) and change.decision.status != "superseded":
                    change.decision = Decision(status="rejected", decided_by=f"human:{by}",
                                               note=f"atom set to {disposition}: {reason}")
                    self.store.save_change(self.pid, change)
        self._mark_released_stale()
        return assessment

    def change_set_hash(self) -> str:
        included = sorted(
            c.model_dump_json(include={"id", "kind", "target_class", "path", "facets", "covers", "label", "definition"})
            for c in self.changes() if c.included
        )
        return hashlib.sha256("\n".join(included).encode()).hexdigest()[:16]

    def sign_off(self, by: str, note: str = "") -> SignOff:
        open_items = [c.id for c in self.changes() if c.decision.status in ("needs_review", "proposed")]
        report = self.store.get_conformance(self.pid)
        if open_items:
            raise ValueError(f"{len(open_items)} change(s) still need review.")
        if report is None or report.verdict == "non_conformant":
            raise ValueError("Run the conformance check first; a non-conformant profile cannot be released.")
        if self.project.stage_states.get("conformance") != "done":
            raise ValueError("The conformance check is out of date; run it again.")
        signoff = SignOff(by=by, note=note, change_set_hash=self.change_set_hash())

        def mutate(project: Project) -> None:
            project.signoff = signoff
            project.stage_states["review"] = "done"
        self._update_project(mutate)
        self.log("review", "signoff", f"released by {by}" + (f": {note}" if note else ""), author=f"human:{by}")
        self.run_compile(cascade=False)
        return signoff

    def _mark_released_stale(self) -> None:
        self._withdraw_release("a decision changed after release")


def _artifact(name: str, title: str, media_type: str, content: str) -> Artifact:
    return Artifact(name=name, title=title, media_type=media_type, content=content,
                    sha256=hashlib.sha256(content.encode("utf-8")).hexdigest())
