"""Stage ``intake``: read atoms, check that they are well-formed, map subjects to classes.

The checks are rule-based on purpose. They implement the atom contract (the
answer stays out of the input: no IRIs, no prefixed names) and the properties
ISO/IEC/IEEE 29148 asks of an individual requirement that can be tested on the
wording alone (singular, unambiguous obligation). They only FLAG: an atom is
never rewritten by the tool, because the atoms are the fixed input of a run.
"""
from __future__ import annotations

import json
import re
from typing import Any

import yaml

from ..contracts import Atom, AtomAssessment, AtomSet, LintIssue, Provenance, SourceReference
from ..knowledge import KnowledgeBase

IRI_RE = re.compile(r"(https?://|urn:)\S+", re.IGNORECASE)
PREFIXED_NAME_RE = re.compile(r"\b[a-zA-Z][\w-]*:[A-Za-z_]\w*")
SUBJECT_RE = re.compile(r"^[a-z][a-z ]*$")
MODAL_WORDS = {
    "must": ("must", "shall", "has to", "have to", "is required", "are required", "needs to", "need to"),
    "should": ("should", "ought to", "is recommended", "are recommended"),
    "may": ("may", "is allowed", "are allowed", "optionally"),   # "can" states a capability ("Users can know ..."), not an obligation
}
VAGUE_WORDS = ("appropriate", "adequate", "as needed", "if possible", "where possible", "etc", "and so on",
               "user-friendly", "sufficient", "relevant information", "as appropriate")


def lint_atom(atom: Atom) -> list[LintIssue]:
    """Rule-based checks on one atom. Errors make the atom unusable as input; warnings inform review."""
    issues: list[LintIssue] = []
    statement = " ".join(atom.statement.split())
    if not statement:
        return [LintIssue(code="empty", severity="error", message="The atom has no statement.")]

    if IRI_RE.search(statement):
        issues.append(LintIssue(
            code="contains_iri", severity="error",
            message="The statement contains an IRI. Atoms must be term-free so that the answer stays out of the input.",
            suggestion="Describe the need in plain words and remove the IRI.",
        ))
    prefixed = [match.group(0) for match in PREFIXED_NAME_RE.finditer(statement)]
    if prefixed:
        issues.append(LintIssue(
            code="contains_prefixed_name", severity="error",
            message=f"The statement contains what looks like a vocabulary term ({', '.join(prefixed[:3])}).",
            suggestion="Name the information that is needed, not the property that would carry it.",
        ))
    if not SUBJECT_RE.match(atom.subject or ""):
        issues.append(LintIssue(
            code="subject_not_plain", severity="warning",
            message=f"The subject '{atom.subject}' is not a plain lower-case word such as dataset or distribution.",
        ))

    lowered = f" {statement.lower()} "
    worded = worded_modality(statement)
    if atom.modality == "unspecified":
        issues.append(LintIssue(
            code="modality_unspecified", severity="info",
            message="The atom does not say how binding it is; the strongest obligation it can justify is 'recommended'.",
        ))
    elif worded and atom.modality != worded:
        issues.append(LintIssue(
            code="modality_mismatch", severity="warning",
            message=f"The modality is recorded as '{atom.modality}' but the main clause reads as '{worded}'.",
            suggestion="Record the modality as worded in the source.",
        ))

    # Singular: one requirement per atom. A coordinated object ("X and Y") after the modal verb is the usual sign.
    body = re.split(r"\b(?:must|shall|should|may|can)\b", statement, maxsplit=1, flags=re.IGNORECASE)[-1]
    if re.search(r"\b(?:and|as well as|plus)\b", body, flags=re.IGNORECASE) or ";" in body:
        issues.append(LintIssue(
            code="compound", severity="warning",
            message="The statement appears to ask for more than one thing; an atom should hold a single requirement.",
            suggestion="Split it upstream into one atom per requirement. Until then the proposer may return several changes.",
        ))
    vague = [word for word in VAGUE_WORDS if word in lowered]
    if vague:
        issues.append(LintIssue(
            code="vague", severity="info",
            message=f"Vague wording ({', '.join(vague)}): the requirement may not be verifiable as stated.",
        ))
    if len(statement.split()) < 4:
        issues.append(LintIssue(code="too_short", severity="warning", message="The statement is too short to act on."))
    return issues


def worded_modality(statement: str) -> str | None:
    """The obligation level of the FIRST modal expression, i.e. of the main clause
    ("must state the licence under which the file may be reused" reads as must)."""
    lowered = f" {' '.join(statement.lower().split())} "
    first: tuple[int, str] | None = None
    for level, words in MODAL_WORDS.items():
        for word in words:
            position = lowered.find(f" {word} ")
            if position >= 0 and (first is None or position < first[0]):
                first = (position, level)
    return first[1] if first else None


def has_blocking_issue(issues: list[LintIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def run_intake(atoms: list[Atom], kb: KnowledgeBase) -> list[AtomAssessment]:
    """Lint every atom and map its subject to a class of the base profile."""
    assessments = []
    for atom in atoms:
        issues = lint_atom(atom)
        resource_class = kb.base.class_for_subject(atom.subject)
        disposition, reason = "needs_change", ""
        if has_blocking_issue(issues):
            disposition, reason = "unclear", "The atom breaks the input contract; fix it before it is processed."
        elif resource_class is None:
            issues.append(LintIssue(
                code="subject_unmapped", severity="info",
                message=f"No class of {kb.base.info.title} corresponds to the subject '{atom.subject}'.",
            ))
        assessments.append(AtomAssessment(
            atom_id=atom.id,
            disposition=disposition,  # type: ignore[arg-type]
            reason=reason,
            resource_class=resource_class,
            lint=issues,
            confidence=1.0 if disposition == "unclear" else 0.5,
            provenance=Provenance(author_type="rule", author="rule:intake"),
        ))
    return assessments


# ---------------------------------------------------------------------------
# Reading atom sets
# ---------------------------------------------------------------------------


def parse_atom_set(text: str) -> AtomSet:
    """Read an atom set from YAML or JSON.

    Accepted shapes: the RQ2 atom contract (``{benchmark_id, base_profile_ids, atoms: [...]}``),
    a bare list of atoms, or a list of plain statements.
    """
    try:
        data: Any = json.loads(text)
    except ValueError:
        data = yaml.safe_load(text)
    if data is None:
        return AtomSet()
    if isinstance(data, list):
        data = {"atoms": data}
    if not isinstance(data, dict):
        raise ValueError("An atom set must be a mapping with an 'atoms' list, or a list of atoms.")
    raw_atoms = data.get("atoms")
    if raw_atoms is None:
        raise ValueError("No 'atoms' found. Expected the RQ2 atom contract: {benchmark_id, base_profile_ids, atoms: [...]}.")
    atoms: list[Atom] = []
    seen: set[str] = set()
    for position, raw in enumerate(raw_atoms, start=1):
        if isinstance(raw, str):
            raw = {"statement": raw}
        if not isinstance(raw, dict) or not str(raw.get("statement") or "").strip():
            raise ValueError(f"Atom {position} has no statement.")
        atom_id = str(raw.get("id") or f"atom-{position:03d}")
        if atom_id in seen:
            raise ValueError(f"Duplicate atom id: {atom_id}")
        seen.add(atom_id)
        reference = raw.get("source_reference")
        if isinstance(reference, str):
            reference = {"document": reference}
        atoms.append(Atom(
            id=atom_id,
            statement=" ".join(str(raw["statement"]).split()),
            subject=str(raw.get("subject") or "dataset").strip().lower(),
            modality=_modality(raw.get("modality")),  # type: ignore[arg-type]
            source_reference=SourceReference(**reference) if isinstance(reference, dict) and reference.get("document") else None,
            counterfactual_of=raw.get("counterfactual_of"),
            expected_change=raw.get("expected_change"),
            hints=[str(item) for item in raw.get("hints") or []],
            tags=[str(item) for item in raw.get("tags") or []],
            active=bool(raw.get("active", True)),
        ))
    return AtomSet(
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        benchmark_id=data.get("benchmark_id"),
        base_profile_ids=[str(item) for item in data.get("base_profile_ids") or []],
        atoms=atoms,
    )


def _modality(value: Any) -> str:
    text = str(value or "unspecified").strip().lower()
    return text if text in {"must", "should", "may", "unspecified"} else "unspecified"
