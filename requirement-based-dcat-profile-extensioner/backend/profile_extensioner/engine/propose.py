"""Stage ``propose``: one model decision per atom, turned into typed profile changes.

The model answers with an ``AtomDecisionOut``. This module turns that answer
into an ``AtomAssessment`` and ``ProfileChange`` objects, doing everything that
can be done symbolically instead of trusting the model with it: expanding
CURIEs, minting IRIs in the profile namespace, deciding whether a change is a
reuse or a refinement (by looking at the base, not at the label the model
chose), filling a refinement with the constraints it inherits from the base,
and recording the base value next to every constraint that is set.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from ..contracts import (
    OBLIGATION_SEVERITY,
    Atom,
    AtomAssessment,
    Candidate,
    CoverageLink,
    ElementRef,
    FacetJustification,
    Facets,
    LLMCallRecord,
    MintJustification,
    ProfileChange,
    Project,
    Provenance,
    RejectedCandidate,
    stable_id,
)
from ..iri import local_name, to_local_name, words_of
from ..knowledge import KnowledgeBase
from ..llm.base import LLMError
from ..llm.client import LLMClient
from .prompts import PROPOSE_VERSION, build_propose_prompt
from .schemas import AtomDecisionOut, ProposedChangeOut

LITERAL_RANGES = ("http://www.w3.org/2000/01/rdf-schema#Literal", "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString")
XSD = "http://www.w3.org/2001/XMLSchema#"


@dataclass
class ProposalResult:
    assessment: AtomAssessment
    changes: list[ProfileChange] = field(default_factory=list)
    records: list[LLMCallRecord] = field(default_factory=list)
    error: str = ""


def propose_for_atom(
    atom: Atom,
    assessment: AtomAssessment,
    candidates: Sequence[Candidate],
    kb: KnowledgeBase,
    llm: LLMClient,
    project: Project,
    *,
    pending: Sequence[ProfileChange] = (),
    feedback: str = "",
) -> ProposalResult:
    """Ask the proposer about one atom (several independent times when voting is on)."""
    system, user, context = build_propose_prompt(
        atom, assessment, candidates, kb, project,
        pending=pending, feedback=feedback, use_candidates=project.config.retrieval,
    )
    votes = max(1, project.config.votes)
    decisions: list[AtomDecisionOut] = []
    records: list[LLMCallRecord] = []
    errors: list[str] = []
    for variant in range(votes):
        try:
            decision, record = llm.generate(
                system=system, user=user, schema=AtomDecisionOut, purpose="propose", subject_id=atom.id,
                stage="propose", prompt_version=PROPOSE_VERSION, context=context, variant=variant,
            )
        except LLMError as exc:
            errors.append(str(exc))
            continue
        decisions.append(decision)
        records.append(record)

    if not decisions:
        failed = assessment.model_copy(deep=True)
        failed.disposition = "unclear"
        failed.reason = f"The model gave no usable answer: {errors[0] if errors else 'unknown error'}"
        failed.confidence = 0.0
        return ProposalResult(assessment=failed, records=records, error=errors[0] if errors else "no answer")

    # Majority vote over the shape of the decision; the first answer with the winning shape is kept.
    signatures = [_signature(decision, kb) for decision in decisions]
    winner, agreeing = Counter(signatures).most_common(1)[0]
    chosen_index = signatures.index(winner)
    decision, record = decisions[chosen_index], records[chosen_index]

    provenance = Provenance(
        author_type="llm", author=llm.author, model=record.model or llm.model_for("propose"),
        prompt_version=PROPOSE_VERSION, call_ids=[item.id for item in records if item.id],
        votes_total=len(decisions), votes_agreeing=agreeing,
    )
    updated = _assessment_from(decision, atom, assessment, kb, provenance)
    changes = [
        change_from_output(out, atom, updated.resource_class, kb, project, provenance.model_copy(deep=True), index)
        for index, out in enumerate(decision.changes)
    ]
    if changes and updated.disposition != "needs_change":
        updated.reason = (f"{updated.reason} " if updated.reason else "") + (
            f"(The proposer answered '{updated.disposition}' but returned changes; treated as needs_change.)"
        )
        updated.disposition = "needs_change"
    elif not changes and updated.disposition == "needs_change":
        updated.disposition = "unclear"
        updated.reason = (f"{updated.reason} " if updated.reason else "") + "(No change was returned for an atom that needs one.)"
    if changes:
        updated.confidence = round(sum(change.confidence for change in changes) / len(changes), 3)
    return ProposalResult(assessment=updated, changes=changes, records=records)


def _signature(decision: AtomDecisionOut, kb: KnowledgeBase) -> tuple:
    shape = sorted(
        (change.kind, kb.expand(change.target_class) or change.target_class,
         kb.expand(change.path) or change.path or "", change.obligation)
        for change in decision.changes
    )
    return (decision.disposition, tuple(shape), tuple(sorted(decision.covered_by)))


def _assessment_from(
    decision: AtomDecisionOut, atom: Atom, previous: AtomAssessment, kb: KnowledgeBase, provenance: Provenance
) -> AtomAssessment:
    resource_class = previous.resource_class
    stated = kb.expand(decision.resource_class) if decision.resource_class else None
    if stated and (kb.base.has_class(stated) or kb.is_minted(stated) or kb.term(stated) is not None):
        resource_class = stated
    covered_by = []
    for curie in decision.covered_by:
        path = kb.expand(curie)
        if path and resource_class:
            covered_by.append(ElementRef(target_class=resource_class, path=path))
    return AtomAssessment(
        atom_id=atom.id,
        disposition=decision.disposition,
        reason=decision.disposition_reason.strip(),
        reading=decision.reading.strip(),
        information_needed=decision.information_needed.strip(),
        resource_class=resource_class,
        covered_by=covered_by,
        lint=list(previous.lint),
        confidence=0.7,
        provenance=provenance,
    )


def _resolve_range(out: ProposedChangeOut, kb: KnowledgeBase) -> tuple[str | None, str | None]:
    """(range_class, range_datatype) from the model's range + range_kind."""
    if not out.range:
        return None, None
    iri = kb.expand(out.range) or out.range
    is_datatype = out.range_kind == "datatype" or (
        out.range_kind == "unspecified" and (iri.startswith(XSD) or iri in LITERAL_RANGES)
    )
    return (None, iri) if is_datatype else (iri, None)


def _show(value: object) -> str | None:
    if value is None or value == [] or value == "":
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def change_from_output(
    out: ProposedChangeOut,
    atom: Atom,
    resource_class: str | None,
    kb: KnowledgeBase,
    project: Project,
    provenance: Provenance,
    index: int = 0,
) -> ProfileChange:
    """Turn one model-written change into a ``ProfileChange`` (see the module docstring)."""
    notes: list[str] = []
    target = kb.expand(out.target_class) or (resource_class if not out.target_class else out.target_class)
    target = target or out.target_class or ""
    is_class_change = out.kind in ("reuse_class", "mint_class")
    path = None if is_class_change else (kb.expand(out.path) if out.path else None) or out.path

    # The kind follows from the facts, not from the label the model chose.
    kind = out.kind
    base_element = kb.base.element(target, path) if path else None
    if is_class_change:
        kind = "mint_class" if kb.is_minted(target) else "reuse_class"
    elif kind != "usage_note":
        if path and kb.is_minted(path):
            kind = "mint_property"
        elif base_element is not None:
            kind = "refine_property"
        else:
            kind = "reuse_property"
    if kind != out.kind:
        notes.append(f"kind set to {kind} (the proposer wrote {out.kind}) because of what the base and the namespaces say")

    range_class, range_datatype = _resolve_range(out, kb)
    facets = Facets(
        obligation=out.obligation,
        min_count=out.min_count,
        max_count=out.max_count,
        range_class=range_class,
        range_datatype=range_datatype,
        node_kind=out.node_kind,
        controlled_vocabulary=[kb.expand(value) or value for value in out.controlled_vocabulary],
    )
    if facets.obligation == "mandatory" and not facets.min_count:
        facets.min_count = 1
        notes.append("min_count set to 1 because the obligation is mandatory")

    base_facets = base_element.facets if base_element is not None else None
    if kind == "refine_property" and base_facets is not None:
        # A refinement states the RESULTING constraints: what it does not mention is inherited from the base.
        if facets.min_count is None:
            facets.min_count = base_facets.min_count
        if facets.max_count is None:
            facets.max_count = base_facets.max_count
        if facets.range_class is None and facets.range_datatype is None:
            facets.range_class, facets.range_datatype = base_facets.range_class, base_facets.range_datatype
        if facets.node_kind is None:
            facets.node_kind = base_facets.node_kind
        if not facets.controlled_vocabulary:
            facets.controlled_vocabulary = list(base_facets.controlled_vocabulary)

    reasons = {item.facet: item.reason for item in out.facet_reasons}
    atom_ids = list(dict.fromkeys([link.atom_id for link in out.covers] or [atom.id]))
    justifications: list[FacetJustification] = []
    if not is_class_change and kind != "usage_note":
        pairs = [
            ("obligation", base_facets.obligation if base_facets else None, facets.obligation),
            ("min_count", base_facets.min_count if base_facets else None, facets.min_count),
            ("max_count", base_facets.max_count if base_facets else None, facets.max_count),
            ("range", (base_facets.range_class or base_facets.range_datatype) if base_facets else None,
             facets.range_class or facets.range_datatype),
            ("node_kind", base_facets.node_kind if base_facets else None, facets.node_kind),
            ("controlled_vocabulary", base_facets.controlled_vocabulary if base_facets else None,
             facets.controlled_vocabulary),
        ]
        for facet, base_value, new_value in pairs:
            shown_base, shown_new = _show(base_value), _show(new_value)
            if shown_new is None or shown_new == shown_base:
                continue
            if facet == "obligation" and shown_base in (None, "unknown") and shown_new == "unknown":
                continue
            justifications.append(FacetJustification(
                facet=facet,  # type: ignore[arg-type]
                base_value=shown_base, new_value=shown_new, atom_ids=atom_ids,
                reason=reasons.get(facet) or out.rationale,  # type: ignore[arg-type]
            ))

    term = kb.term(path if path else target)
    minted = kind in ("mint_property", "mint_class")
    label = (out.label or "").strip() if minted else ""
    definition = (out.definition or "").strip() if minted else ""
    if not minted:
        label = (base_element.label if base_element else "") or (term.label if term else "") or " ".join(
            words_of(local_name(path or target))
        )
        definition = (base_element.definition if base_element else "") or (term.definition if term else "")

    rejected = [RejectedCandidate(iri=kb.expand(item.term) or item.term, reason=item.reason) for item in out.rejected_candidates]
    super_term = kb.expand(out.super_term) if out.super_term else None
    covers = [
        CoverageLink(atom_id=link.atom_id, reason=link.reason.strip(), evidence_quote=link.evidence_quote.strip(),
                     coverage=link.coverage)
        for link in out.covers
    ] or [CoverageLink(atom_id=atom.id, reason=out.rationale.strip(), evidence_quote="")]

    return ProfileChange(
        id=stable_id("chg", project.id, atom.id, kind, target, path or label, index),
        kind=kind,
        target_class=target,
        path=path,
        label=label,
        definition=definition,
        usage_note=(out.usage_note or "").strip(),
        facets=facets,
        severity=OBLIGATION_SEVERITY[facets.obligation],  # type: ignore[arg-type]
        super_class=super_term if kind == "mint_class" else None,
        sub_property_of=super_term if kind == "mint_property" else None,
        mint=MintJustification(reason_no_reuse=(out.reason_no_reuse or "").strip(), rejected_candidates=rejected) if minted else None,
        covers=covers,
        facet_justifications=justifications,
        rationale=out.rationale.strip(),
        alternatives=[] if minted else rejected,
        confidence=max(0.0, min(1.0, float(out.confidence))),
        engine_notes=notes,
        provenance=provenance,
    )


def suggest_local_name(text: str, *, for_class: bool = False) -> str:
    """A mintable local name from plain words (used by rule-based proposers and the manual editor)."""
    return to_local_name(text, upper_first=for_class)
