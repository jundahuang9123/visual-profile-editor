"""Stage ``repair``: bounded model repair of changes that failed verification.

Each round sends the change, the failed checks and the atoms to the repairer.
A revised change replaces the old one (the old one is kept as ``superseded``);
after ``repair_rounds`` unsuccessful rounds the change goes to the human queue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..contracts import Atom, Candidate, CheckResult, Decision, LLMCallRecord, ProfileChange, Project
from ..knowledge import KnowledgeBase
from ..llm.base import LLMError
from ..llm.client import LLMClient
from .prompts import REPAIR_VERSION, build_repair_prompt
from .propose import change_from_output
from .schemas import (
    CoverageOut,
    FacetReasonOut,
    ProposedChangeOut,
    RejectedOut,
    RepairOut,
)


@dataclass
class RepairResult:
    action: str                       # revise | withdraw | failed
    note: str = ""
    change: ProfileChange | None = None
    records: list[LLMCallRecord] = field(default_factory=list)


def change_to_output(change: ProfileChange, kb: KnowledgeBase) -> ProposedChangeOut:
    """The inverse of ``change_from_output``: how the model sees an existing change."""
    facets = change.facets
    range_value = facets.range_class or facets.range_datatype
    return ProposedChangeOut(
        kind=change.kind,
        target_class=kb.curie(change.target_class) if not kb.is_minted(change.target_class)
        else f"NEW:{change.target_class[len(kb.profile_namespace):]}",
        path=(f"NEW:{change.path[len(kb.profile_namespace):]}" if change.path and kb.is_minted(change.path)
              else kb.curie(change.path) if change.path else None),
        label=change.label or None,
        definition=change.definition or None,
        usage_note=change.usage_note or None,
        obligation=facets.obligation if facets.obligation != "unknown" else "optional",
        min_count=facets.min_count,
        max_count=facets.max_count,
        range=kb.curie(range_value) if range_value else None,
        range_kind="class" if facets.range_class else "datatype" if facets.range_datatype else "unspecified",
        node_kind=facets.node_kind,
        controlled_vocabulary=list(facets.controlled_vocabulary),
        super_term=kb.curie(change.super_class or change.sub_property_of) if (change.super_class or change.sub_property_of) else None,
        covers=[CoverageOut(atom_id=l.atom_id, reason=l.reason, evidence_quote=l.evidence_quote, coverage=l.coverage)
                for l in change.covers],
        facet_reasons=[FacetReasonOut(facet=j.facet, reason=j.reason) for j in change.facet_justifications],
        reason_no_reuse=change.mint.reason_no_reuse if change.mint else None,
        rejected_candidates=[RejectedOut(term=kb.curie(r.iri), reason=r.reason)
                             for r in (change.mint.rejected_candidates if change.mint else change.alternatives)],
        rationale=change.rationale,
        confidence=change.confidence,
    )


def repair_change(
    change: ProfileChange,
    failures: Sequence[CheckResult],
    atoms: Sequence[Atom],
    candidates: Sequence[Candidate],
    kb: KnowledgeBase,
    llm: LLMClient,
    project: Project,
    *,
    round_number: int,
) -> RepairResult:
    proposed = change_to_output(change, kb)
    system, user, context = build_repair_prompt(
        change, failures, atoms, candidates, kb, project,
        round_number=round_number, proposed_json=proposed.model_dump_json(indent=1),
    )
    try:
        answer, record = llm.generate(
            system=system, user=user, schema=RepairOut, purpose="repair", subject_id=change.id,
            stage="repair", prompt_version=REPAIR_VERSION, context=context, variant=round_number,
        )
    except LLMError as exc:
        return RepairResult(action="failed", note=str(exc))
    if answer.action == "withdraw" or answer.change is None:
        return RepairResult(action="withdraw", note=answer.note, records=[record])
    primary = atoms[0] if atoms else Atom(id=change.atom_ids[0] if change.atom_ids else "?", statement="")
    provenance = change.provenance.model_copy(deep=True)
    provenance.author_type = "llm"
    provenance.author = llm.author
    provenance.prompt_version = REPAIR_VERSION
    provenance.call_ids = [record.id] if record.id else []
    provenance.repair_round = round_number
    resource_class = change.target_class if not change.is_class_change else None
    revised = change_from_output(answer.change, primary, resource_class, kb, project, provenance, round_number)
    revised.id = f"{change.id.split('~')[0]}~r{round_number}"
    revised.supersedes = change.id
    revised.merged_from = list(change.merged_from)
    revised.engine_notes = [f"repair round {round_number}: {answer.note}", *revised.engine_notes]
    revised.decision = Decision(status="proposed", decided_by=llm.author)
    return RepairResult(action="revise", note=answer.note, change=revised, records=[record])
