"""What the model is asked to write.

The model never writes SHACL, Turtle or LinkML. It fills the small typed
records below; the engine turns them into ``ProfileChange`` objects, checks
them symbolically and compiles every artefact deterministically.

Terms are written as CURIEs taken from the candidate list or the base profile
(for example ``dcterms:license``). A term that does not exist yet is written as
``NEW:localName`` and is minted in the profile's own namespace by the engine.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..contracts import AtomDisposition, ChangeKind, FacetName, NodeKind


class CoverageOut(BaseModel):
    atom_id: str = Field(description="Id of the requirement atom this change covers.")
    reason: str = Field(description="One or two sentences: why this change satisfies that atom.")
    evidence_quote: str = Field(description="A verbatim span copied from the atom's statement that the change answers.")
    coverage: Literal["full", "partial"] = Field(description="'full' if the change alone satisfies the atom, else 'partial'.")


class FacetReasonOut(BaseModel):
    facet: FacetName = Field(description="Which constraint this reason is about.")
    reason: str = Field(description="Why this value is needed, citing the atom's wording.")


class RejectedOut(BaseModel):
    term: str = Field(description="CURIE of a candidate that was considered and not used.")
    reason: str = Field(description="Why it does not fit the atom.")


class ProposedChangeOut(BaseModel):
    kind: ChangeKind = Field(
        description=(
            "reuse_property: an existing property newly constrained on the class. "
            "refine_property: the base already constrains this property on this class and the change tightens it. "
            "mint_property / mint_class: a new term because no candidate fits. "
            "reuse_class: an existing class brought into the profile. "
            "usage_note: guidance only, no constraint."
        )
    )
    target_class: str = Field(description="CURIE of the class the change applies to, or NEW:LocalName for a class minted in this answer.")
    path: str | None = Field(description="CURIE of the property, or NEW:localName to mint one. Null for class changes.")
    label: str | None = Field(description="Human-readable label. Required for minted terms.")
    definition: str | None = Field(description="Definition. Required for minted terms.")
    usage_note: str | None = Field(description="How the element is to be used in this profile, if worth saying.")
    obligation: Literal["mandatory", "recommended", "optional"] = Field(
        description="No stronger than the atom's wording licenses: must -> mandatory, should -> recommended, may -> optional."
    )
    min_count: int | None = Field(description="Minimum cardinality, or null. Mandatory implies at least 1.")
    max_count: int | None = Field(description="Maximum cardinality, or null for unbounded.")
    range: str | None = Field(description="CURIE of the expected class or datatype of the value, or NEW:LocalName, or null.")
    range_kind: Literal["class", "datatype", "unspecified"] = Field(description="Whether 'range' is a class or a datatype.")
    node_kind: NodeKind | None = Field(description="SHACL node kind of the value, or null.")
    controlled_vocabulary: list[str] = Field(description="IRIs of allowed values or of a concept scheme; empty if none.")
    super_term: str | None = Field(description="For a minted term: CURIE of the class or property it specialises, or null.")
    covers: list[CoverageOut] = Field(description="The atoms this change covers. Never empty.")
    facet_reasons: list[FacetReasonOut] = Field(description="One entry for every constraint this change sets or tightens.")
    reason_no_reuse: str | None = Field(description="For a minted term only: why none of the candidates can be reused.")
    rejected_candidates: list[RejectedOut] = Field(description="Candidates that were considered and rejected, with reasons.")
    rationale: str = Field(description="Short overall justification of the modelling choice.")
    confidence: float = Field(description="Between 0 and 1: how sure you are that this is the right change.")


class AtomDecisionOut(BaseModel):
    """The model's decision for ONE requirement atom."""

    atom_id: str
    reading: str = Field(description="One sentence restating what information must be recorded, and about what.")
    information_needed: str = Field(description="The piece of information the atom asks for, in two to six plain words.")
    disposition: AtomDisposition = Field(
        description=(
            "needs_change: the base profile does not satisfy the atom. "
            "covered_by_base: the base already satisfies it as stated (no change). "
            "out_of_scope: not a requirement on the metadata profile. "
            "unclear: cannot be decided from the atom as written."
        )
    )
    disposition_reason: str
    resource_class: str | None = Field(description="CURIE of the class the atom is about, or null if unknown.")
    covered_by: list[str] = Field(description="When covered_by_base: CURIEs of the base properties that satisfy the atom.")
    changes: list[ProposedChangeOut] = Field(
        description="Empty unless disposition is needs_change. One primary change per atom unless the atom explicitly asks for several distinct elements."
    )


class RepairOut(BaseModel):
    """The model's answer to a list of violations found by the verifier."""

    action: Literal["revise", "withdraw"] = Field(description="'revise' to return a corrected change, 'withdraw' if the change should not exist.")
    note: str = Field(description="What was changed and why, or why the change is withdrawn.")
    change: ProposedChangeOut | None = Field(description="The corrected change when action is 'revise', else null.")


class AttributionOut(BaseModel):
    """Is a proposed change really supported by the atom it cites?"""

    verdict: Literal["supported", "partially_supported", "unsupported"]
    explanation: str
    unsupported_facets: list[FacetName] = Field(description="Constraints that the atom's wording does not license.")
