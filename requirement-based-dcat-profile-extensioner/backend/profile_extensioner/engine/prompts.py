"""Versioned prompts of the three model roles: proposer, repairer, judge.

Every prompt has the same anatomy: a stable system prompt (role, procedure,
strict constraints, common mistakes) and a user prompt made of named sections
filled from typed inputs. An empty section prints "None". The rendered prompts
are stored with every call, so a reviewer can read exactly what the model saw.

Change a prompt -> change its version constant: the version is part of each
call's record and of the replay-cache key.
"""
from __future__ import annotations

from typing import Any, Sequence

from ..contracts import MODALITY_OBLIGATION, Atom, AtomAssessment, Candidate, CheckResult, ProfileChange, Project
from ..knowledge import KnowledgeBase
from .retrieve import query_tokens
from .verbalise import base_element_line, facets_text, verbalise_change

PROPOSE_VERSION = "propose-v1"
REPAIR_VERSION = "repair-v1"
JUDGE_VERSION = "judge-v1"

PROPOSE_SYSTEM = """\
You are the proposer of a requirements-driven profile engineering workbench. An existing DCAT application \
profile (the BASE) is extended so that it satisfies requirement atoms. You never write SHACL, Turtle or \
LinkML. You fill one typed decision record per atom. A symbolic verifier checks every field you write, and \
a human reviewer has the final say, so be precise and say plainly when something cannot be decided.

[PROCEDURE] Work through these steps for the atom you are given.
1. Read the atom. Restate in one sentence which information must be recorded, and about what (field: reading).
2. Fix the context: the class the atom is about (RESOURCE CLASS, when given).
3. Split the need into: the thing described (a class), the information needed (a property), and the kind of \
value (a class of things, or a literal datatype).
4. Look at BASE PROFILE SLICE first. Does the base already define a property on this class that carries this \
information?
   - Yes, and its obligation is at least as strong as the atom's wording licenses: the disposition is \
covered_by_base; cite the property in covered_by; return no change.
   - Yes, but weaker than the atom demands: return one refine_property change that tightens exactly what the \
atom demands and nothing else.
5. Otherwise look at CANDIDATE TERMS and reuse an existing property that carries the information (reuse_property).
6. Only if no candidate carries the information, mint a term (mint_property, or mint_class when a new kind of \
thing is needed), written NEW:localName. Say for each plausible candidate why it does not fit.
7. Derive the constraints from the atom's wording only, and give a reason for every constraint you set.
8. State your confidence between 0 and 1.

[STRICT CONSTRAINTS]
- Use only terms that appear in BASE PROFILE SLICE or CANDIDATE TERMS, written exactly as shown there, or \
NEW:localName for a term you mint. Never invent a prefixed name.
- The obligation follows the atom's modality: must -> mandatory, should -> recommended, may -> optional, \
unspecified -> recommended at most. Never stronger than the wording licenses.
- mandatory implies min_count of at least 1. Set max_count only when the atom says so ("exactly one", \
"a single", "at most ...").
- A refinement may tighten the base and never loosen it: do not lower an obligation or a minimum, do not \
raise a maximum, do not widen a range.
- One primary change per atom. Return several changes only when the atom explicitly asks for several distinct \
pieces of information, or when a minted property needs a minted class as its range.
- evidence_quote must be copied verbatim from the atom's statement.
- If the atom is not about what the metadata of a catalogued resource must contain (for example system \
performance, user interface, organisational process), the disposition is out_of_scope.
- If the atom cannot be decided as written, the disposition is unclear. Do not guess.
- Do not repeat a change that is listed under PENDING CHANGES; cover the atom by pointing to the same term instead.

[COMMON MISTAKES]
- Minting a property although the base slice already has one for the same information.
- Setting mandatory for an atom worded with "should" or "may".
- Declaring covered_by_base although the base obligation is weaker than the atom's.
- Using a term that is in neither list.
- Paraphrasing instead of quoting in evidence_quote.
- Adding a range, a vocabulary or a maximum that the atom does not ask for.
"""

REPAIR_SYSTEM = """\
You are the repairer of a requirements-driven profile engineering workbench. A proposed change to a DCAT \
application profile failed symbolic checks. Return a corrected change that fixes every listed violation and \
changes nothing else, or withdraw the change when it should not exist at all. The rules of the proposer still \
hold: use only the terms shown (or NEW:localName), keep the obligation within what the atom's wording licenses, \
tighten the base and never loosen it, and quote the atom verbatim in evidence_quote.
"""

JUDGE_SYSTEM = """\
You are the judge of a requirements-driven profile engineering workbench. You are given requirement atoms and \
ONE proposed change to a DCAT application profile, stated in plain language. Decide whether the atoms' wording \
supports the change.
- supported: the change is what the atoms ask for, and every constraint it sets is licensed by their wording.
- partially_supported: the change answers the atoms, but at least one constraint goes beyond their wording, or \
only part of an atom is answered.
- unsupported: the atoms do not ask for this.
List in unsupported_facets every constraint the wording does not license. Judge only from the atoms as written; \
do not rely on what published profiles do. Start the explanation with the decisive words of the atom.
"""


def _section(title: str, body: str | Sequence[str]) -> str:
    if isinstance(body, str):
        text = body.strip()
    else:
        text = "\n".join(line for line in body if line)
    return f"[{title}]\n{text or 'None'}"


def _atom_block(atom: Atom) -> list[str]:
    licensed = MODALITY_OBLIGATION[atom.modality]
    lines = [
        f"id: {atom.id}",
        f'statement: "{atom.statement}"',
        f"subject: {atom.subject}",
        f"modality: {atom.modality} (strongest obligation this licenses: {licensed})",
    ]
    if atom.source_reference:
        locator = f", {atom.source_reference.locator}" if atom.source_reference.locator else ""
        lines.append(f"source: {atom.source_reference.document}{locator}")
    return lines


def _candidate_line(candidate: Candidate, kb: KnowledgeBase) -> str:
    extra = []
    if candidate.in_base_on_class and candidate.base_facets is not None:
        extra.append(f"IN BASE on this class: {facets_text(candidate.base_facets, kb)}")
    elif candidate.base_classes:
        extra.append("used by the base on " + ", ".join(kb.curie(iri) for iri in candidate.base_classes[:3]))
    if candidate.domain:
        extra.append("domain " + ", ".join(kb.curie(iri) for iri in candidate.domain[:2]))
    if candidate.range and not candidate.in_base_on_class:
        extra.append("range " + ", ".join(kb.curie(iri) for iri in candidate.range[:2]))
    detail = f" ({'; '.join(extra)})" if extra else ""
    definition = f": {candidate.definition}" if candidate.definition else ""
    return f'{candidate.rank}. {candidate.curie} [{candidate.kind}] "{candidate.label}"{detail}{definition}'


def build_propose_prompt(
    atom: Atom,
    assessment: AtomAssessment,
    candidates: Sequence[Candidate],
    kb: KnowledgeBase,
    project: Project,
    *,
    pending: Sequence[ProfileChange] = (),
    feedback: str = "",
    use_candidates: bool = True,
) -> tuple[str, str, dict[str, Any]]:
    """(system prompt, user prompt, machine-readable context for the offline provider)."""
    resource_class = assessment.resource_class
    base_elements = kb.base.elements(resource_class) if resource_class else []
    class_line = (
        f"{kb.curie(resource_class)} ({kb.base.class_label(resource_class)})" if resource_class
        else f"None: no class of the base corresponds to the subject '{atom.subject}'. "
             f"Classes of the base: {', '.join(kb.curie(cls.iri) for cls in kb.base.classes()[:12])}"
    )
    shown = list(candidates) if use_candidates else []
    sections = [
        _section("PROFILE", [
            f"Base profile: {kb.base.info.title}",
            f"Extension: {project.profile_title or project.name}; new terms are written NEW:localName "
            f"(they will be minted as {project.profile_prefix}:localName)",
        ]),
        _section("ATOM", _atom_block(atom)),
        _section("RESOURCE CLASS", class_line),
        _section(
            "BASE PROFILE SLICE",
            [f"Properties the base defines on {kb.curie(resource_class)} [obligation; cardinality; range]:"]
            + [f"- {base_element_line(element, kb)}" for element in base_elements] if base_elements else "",
        ),
        _section(
            "CANDIDATE TERMS",
            ["Retrieved for this atom, best match first:"] + [_candidate_line(candidate, kb) for candidate in shown]
            if shown else ("None retrieved." if use_candidates else "Retrieval is switched off for this run."),
        ),
        _section("PENDING CHANGES", [f"- {verbalise_change(change, kb)}" for change in pending]),
        _section("HUMAN FEEDBACK", feedback),
        _section("CORRECTION INSTRUCTIONS", ""),
        _section("OUTPUT", f"Return the decision record for atom {atom.id}."),
    ]
    context = {
        "task": "propose",
        "atom": atom.model_dump(),
        "licensed_obligation": MODALITY_OBLIGATION[atom.modality],
        "resource_class": resource_class,
        "resource_class_curie": kb.curie(resource_class) if resource_class else None,
        "lint_codes": [issue.code for issue in assessment.lint],
        "query_size": len(query_tokens(atom)[0]),
        "candidates": [candidate.model_dump() for candidate in shown],
        "pending": [
            {"kind": change.kind, "target_class": change.target_class, "path": change.path,
             "path_curie": kb.curie(change.path) if change.path else None, "label": change.label}
            for change in pending
        ],
        "profile_prefix": project.profile_prefix,
    }
    return PROPOSE_SYSTEM, "\n\n".join(sections), context


def build_repair_prompt(
    change: ProfileChange,
    failures: Sequence[CheckResult],
    atoms: Sequence[Atom],
    candidates: Sequence[Candidate],
    kb: KnowledgeBase,
    project: Project,
    *,
    round_number: int,
    proposed_json: str,
) -> tuple[str, str, dict[str, Any]]:
    base_elements = kb.base.elements(change.target_class) if kb.base.has_class(change.target_class) else []
    sections = [
        _section("PROFILE", [
            f"Base profile: {kb.base.info.title}",
            f"New terms are written NEW:localName (minted as {project.profile_prefix}:localName)",
        ]),
        *[_section("ATOM", _atom_block(atom)) for atom in atoms],
        _section(
            "BASE PROFILE SLICE",
            [f"- {base_element_line(element, kb)}" for element in base_elements],
        ),
        _section("CANDIDATE TERMS", [_candidate_line(candidate, kb) for candidate in candidates]),
        _section("PROPOSED CHANGE", [verbalise_change(change, kb), "As submitted:", proposed_json]),
        _section(
            "CORRECTION INSTRUCTIONS",
            [f"Repair round {round_number}. Fix ALL of these violations:"]
            + [f"- {failure.check}: {failure.message}" for failure in failures[:20]],
        ),
        _section("OUTPUT", "Return action 'revise' with the corrected change, or 'withdraw' with the reason."),
    ]
    context = {
        "task": "repair",
        "change": change.model_dump(),
        "failures": [failure.model_dump() for failure in failures],
        "atoms": [atom.model_dump() for atom in atoms],
        "licensed_obligation": _strongest_licensed(atoms),
        "candidates": [candidate.model_dump() for candidate in candidates],
        "proposed_json": proposed_json,
        "base_facets": (
            element.facets.model_dump()
            if change.path and (element := kb.base.element(change.target_class, change.path)) is not None else None
        ),
    }
    return REPAIR_SYSTEM, "\n\n".join(sections), context


def build_judge_prompt(
    change: ProfileChange, atoms: Sequence[Atom], kb: KnowledgeBase
) -> tuple[str, str, dict[str, Any]]:
    sections = [
        *[_section("ATOM", _atom_block(atom)) for atom in atoms],
        _section("PROPOSED CHANGE", verbalise_change(change, kb)),
        _section(
            "CLAIMED COVERAGE",
            [f'- atom {link.atom_id} ({link.coverage}): {link.reason} | quote: "{link.evidence_quote}"'
             for link in change.covers],
        ),
        _section("OUTPUT", "Return the verdict."),
    ]
    context = {
        "task": "judge",
        "change": change.model_dump(),
        "atoms": [atom.model_dump() for atom in atoms],
        "licensed_obligation": _strongest_licensed(atoms),
    }
    return JUDGE_SYSTEM, "\n\n".join(sections), context


def _strongest_licensed(atoms: Sequence[Atom]) -> str:
    order = {"optional": 1, "recommended": 2, "mandatory": 3}
    levels = [MODALITY_OBLIGATION[atom.modality] for atom in atoms] or ["recommended"]
    return max(levels, key=lambda level: order[level])
