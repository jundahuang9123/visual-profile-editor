"""Typed contracts of the requirement-based DCAT profile extensioner.

Everything that moves between pipeline stages, is stored on the blackboard, is
shown on the workbench or is exported is one of the models below.

Conventions
-----------
* IRIs are stored EXPANDED. CURIEs appear only in what the LLM reads/writes and
  in what the workbench renders (see ``iri.Prefixes``).
* A requirement atom is the unit of input. A ``ProfileChange`` is the unit of
  decision. A ``ProfileElement`` (one target class + one property path) is the
  unit of output and of scoring; it mirrors ``profile_element.linkml.yaml`` of
  the RQ2 contracts so that an external evaluator can consume our deltas.
* Traceability is structural, not a comment field: a change lists the atoms it
  covers (``covers``) and every constraint it sets or tightens carries its own
  justification (``facet_justifications``).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

CONTRACT_VERSION = "rbdpe-contracts-v1"

# ---------------------------------------------------------------------------
# Vocabulary of small enumerations
# ---------------------------------------------------------------------------

Modality = Literal["must", "should", "may", "unspecified"]
Obligation = Literal["mandatory", "recommended", "optional", "unknown"]
NodeKind = Literal["IRI", "BlankNode", "Literal", "BlankNodeOrIRI", "BlankNodeOrLiteral", "IRIOrLiteral"]
Severity = Literal["Violation", "Warning", "Info"]

# Reuse-first ordering: reuse an existing term > refine (tighten) what the base
# already constrains > mint a new term.
ChangeKind = Literal[
    "reuse_property",   # existing vocabulary property, newly constrained on a class
    "refine_property",  # the base already constrains (class, path); this tightens it
    "mint_property",    # new property in the profile's own namespace
    "reuse_class",      # existing vocabulary class, newly brought into the profile
    "mint_class",       # new class in the profile's own namespace
    "usage_note",       # documentation-only guidance on an existing element
]

ElementKind = Literal["reuse", "refine", "mint", "class_addition"]
DeltaStatus = Literal["added", "tightened", "unchanged", "loosened"]
ElementSource = Literal["gold", "generated"]

FacetName = Literal[
    "obligation",
    "min_count",
    "max_count",
    "range",
    "node_kind",
    "controlled_vocabulary",
    "pattern",
    "label",
    "definition",
    "usage_note",
]

AtomDisposition = Literal[
    "needs_change",      # the base does not satisfy the atom: a change is required
    "covered_by_base",   # the base profile already satisfies the atom as stated
    "out_of_scope",      # not a requirement on the metadata profile (process, tooling, ...)
    "unclear",           # cannot be decided from the atom as written -> human review
]

AtomCoverage = Literal[
    "addressed",            # at least one accepted change covers the atom in full
    "partially_addressed",  # only partial coverage links
    "covered_by_base",
    "out_of_scope",
    "pending_review",       # covering changes exist but wait for a human
    "unaddressed",
]

DecisionStatus = Literal[
    "proposed",       # produced, not yet verified
    "auto_accepted",  # verified; the machine decision stands unless a human overrules it
    "needs_review",   # the machine could not settle it: queued for a human
    "accepted",       # a human accepted (or edited and accepted) it
    "rejected",       # a human rejected it, or the proposer withdrew it
    "superseded",     # replaced by a repair, an edit or a merge
]
INCLUDED_STATUSES: tuple[str, ...] = ("auto_accepted", "accepted")

AuthorType = Literal["llm", "rule", "human"]

Stage = Literal[
    "intake",       # load atoms, lint them, map each subject to a class of the base
    "retrieve",     # per atom: candidate terms from the vocabulary index
    "propose",      # per atom: disposition against the base + typed profile changes
    "verify",       # symbolic checks + trace checks
    "repair",       # bounded LLM repair of violations
    "consolidate",  # merge duplicates, surface conflicts
    "compile",      # LinkML, SHACL, DSV, documentation, trace matrix
    "conformance",  # does the extension still conform to its base?
    "review",       # human review queue and final sign-off
]
STAGE_ORDER: tuple[str, ...] = (
    "intake", "retrieve", "propose", "verify", "repair",
    "consolidate", "compile", "conformance", "review",
)

StageState = Literal["pending", "running", "done", "stale", "failed", "skipped"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_id(prefix: str, *parts: object) -> str:
    """Deterministic short id from the given parts (same inputs -> same id)."""
    digest = hashlib.sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:12]}"


# ---------------------------------------------------------------------------
# Input: requirement atoms
# ---------------------------------------------------------------------------


class SourceReference(BaseModel):
    document: str
    locator: str | None = None   # section, table row, page or line range
    quote: str | None = None     # verbatim source evidence when the upstream pipeline kept it


class Atom(BaseModel):
    """One atomic, term-free requirement (RQ2 atom contract).

    ``statement`` must not contain IRIs, prefixed names or profile names: the
    answer stays out of the input. Vocabulary terms that an upstream extraction
    observed are kept apart in ``hints`` and are NOT shown to the proposer
    unless the run explicitly allows it.
    """

    id: str
    statement: str
    subject: str = "dataset"
    modality: Modality = "unspecified"
    source_reference: SourceReference | None = None
    counterfactual_of: str | None = None
    expected_change: str | None = None
    hints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    active: bool = True


class AtomSet(BaseModel):
    title: str = ""
    description: str = ""
    benchmark_id: str | None = None
    base_profile_ids: list[str] = Field(default_factory=list)
    atoms: list[Atom] = Field(default_factory=list)


class LintIssue(BaseModel):
    code: str                                   # e.g. contains_term, compound, vague_modality
    severity: Literal["error", "warning", "info"] = "warning"
    message: str
    suggestion: str | None = None


# ---------------------------------------------------------------------------
# Symbolic knowledge base: vocabulary terms and the base profile
# ---------------------------------------------------------------------------


class Term(BaseModel):
    """One reusable class or property in the vocabulary index."""

    iri: str
    kind: Literal["class", "property"]
    label: str = ""
    definition: str = ""
    vocabulary: str = ""                         # prefix of the vocabulary, e.g. dcterms
    domain: list[str] = Field(default_factory=list)
    range: list[str] = Field(default_factory=list)
    super_terms: list[str] = Field(default_factory=list)   # rdfs:subClassOf / rdfs:subPropertyOf
    property_type: Literal["object", "datatype", "annotation", "unknown"] = "unknown"
    deprecated: bool = False
    source: str = ""                             # vendored file the term was read from


class Facets(BaseModel):
    """Constraints on one (target class, property path)."""

    obligation: Obligation = "unknown"
    min_count: int | None = None
    max_count: int | None = None                 # None = unbounded
    range_class: str | None = None               # sh:class
    range_datatype: str | None = None            # sh:datatype
    node_kind: NodeKind | None = None
    controlled_vocabulary: list[str] = Field(default_factory=list)   # sh:in members or concept scheme IRIs
    pattern: str | None = None


class BaseElement(BaseModel):
    """What the base profile says about one (target class, property path)."""

    target_class: str
    path: str
    facets: Facets = Field(default_factory=Facets)
    label: str = ""
    definition: str = ""
    usage_note: str = ""
    severity: Severity | None = None
    source: str = ""                             # shape IRI or file the constraint came from


class BaseClass(BaseModel):
    iri: str
    label: str = ""
    definition: str = ""
    obligation: Obligation = "unknown"           # mandatory / recommended / optional class in the base


class BaseProfileInfo(BaseModel):
    """Catalogue entry for a base profile that can be extended."""

    id: str                                      # e.g. dcat-ap-3.0.1
    title: str
    version: str = ""
    description: str = ""
    homepage: str = ""
    licence: str = ""
    shape_files: list[str] = Field(default_factory=list)
    class_count: int = 0
    element_count: int = 0


class Candidate(BaseModel):
    """A retrieved reusable term offered to the proposer for one atom."""

    iri: str
    curie: str
    kind: Literal["class", "property"]
    label: str = ""
    definition: str = ""
    vocabulary: str = ""
    domain: list[str] = Field(default_factory=list)
    range: list[str] = Field(default_factory=list)
    score: float = 0.0
    rank: int = 0
    in_base_on_class: bool = False               # the base already constrains this path on the atom's class
    base_classes: list[str] = Field(default_factory=list)   # classes on which the base uses this path
    base_facets: Facets | None = None            # the base's constraints when in_base_on_class
    matched: list[str] = Field(default_factory=list)   # query word stems that matched
    why: str = ""                                # how it was found (matched words, boost reasons)


# ---------------------------------------------------------------------------
# Decisions: assessments and profile changes, with their trace
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    author_type: AuthorType = "rule"
    author: str = "rule:engine"                  # llm:<provider>/<model> | rule:<name> | human:<name>
    model: str | None = None
    prompt_version: str | None = None
    call_ids: list[str] = Field(default_factory=list)
    repair_round: int = 0
    votes_total: int = 1
    votes_agreeing: int = 1
    created_at: str = Field(default_factory=now_iso)


class ElementRef(BaseModel):
    target_class: str
    path: str | None = None


class AtomAssessment(BaseModel):
    """What an atom asks of the profile, judged against the base.

    ``intake`` fills the lint results and the resource class; ``propose`` fills
    the disposition, its reason and the base elements that already cover the atom.
    """

    atom_id: str
    disposition: AtomDisposition = "needs_change"
    reason: str = ""
    reading: str = ""                            # how the proposer read the atom (one sentence)
    information_needed: str = ""                 # the piece of information asked for, in plain words
    resource_class: str | None = None            # the class the atom's subject maps to
    covered_by: list[ElementRef] = Field(default_factory=list)   # base elements that already satisfy it
    lint: list[LintIssue] = Field(default_factory=list)
    confidence: float = 0.5
    provenance: Provenance = Field(default_factory=Provenance)


class CoverageLink(BaseModel):
    """Why a change covers an atom. ``evidence_quote`` is a verbatim span of the atom statement."""

    atom_id: str
    reason: str
    evidence_quote: str = ""
    coverage: Literal["full", "partial"] = "full"


class FacetJustification(BaseModel):
    """One constraint set or modified by a change, with its own reason.

    ``base_value`` is what the base profile had (None = the base did not
    constrain it); ``status`` is filled by the refinement checker.
    """

    facet: FacetName
    base_value: str | None = None
    new_value: str | None = None
    status: DeltaStatus | Literal["editorial"] | None = None
    atom_ids: list[str] = Field(default_factory=list)
    reason: str = ""


class RejectedCandidate(BaseModel):
    iri: str
    reason: str


class MintJustification(BaseModel):
    """Stored with every minted term: why no existing candidate fits (check V4)."""

    reason_no_reuse: str
    rejected_candidates: list[RejectedCandidate] = Field(default_factory=list)


class CheckResult(BaseModel):
    check: str                                   # V1..V6, T1..T3, C1.. (conformance)
    passed: bool
    severity: Literal["error", "warning", "info"] = "error"
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    status: DecisionStatus = "proposed"
    decided_by: str = "rule:engine"
    note: str = ""
    decided_at: str = Field(default_factory=now_iso)


class ProfileChange(BaseModel):
    """One typed, verifiable, traceable change to the profile.

    The proposer (an LLM, a rule, or a human on the workbench) fills the upper
    part; the engine fills ids, IRIs, verification and decision.
    """

    id: str
    kind: ChangeKind
    target_class: str                            # expanded IRI
    path: str | None = None                      # expanded IRI; None for class changes
    label: str = ""
    definition: str = ""
    usage_note: str = ""
    facets: Facets = Field(default_factory=Facets)
    severity: Severity | None = None

    # minted terms
    super_class: str | None = None               # for mint_class
    sub_property_of: str | None = None           # for mint_property
    mint: MintJustification | None = None

    # trace
    covers: list[CoverageLink] = Field(default_factory=list)
    facet_justifications: list[FacetJustification] = Field(default_factory=list)
    rationale: str = ""
    alternatives: list[RejectedCandidate] = Field(default_factory=list)
    confidence: float = 0.5

    # engine-owned
    engine_notes: list[str] = Field(default_factory=list)  # what the engine normalised, and why
    merged_from: list[str] = Field(default_factory=list)   # change ids folded into this one
    supersedes: str | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    verification: list[CheckResult] = Field(default_factory=list)
    decision: Decision = Field(default_factory=Decision)

    @property
    def atom_ids(self) -> list[str]:
        return list(dict.fromkeys(link.atom_id for link in self.covers))

    @property
    def is_class_change(self) -> bool:
        return self.kind in ("reuse_class", "mint_class")

    @property
    def included(self) -> bool:
        return self.decision.status in INCLUDED_STATUSES

    def failed_checks(self, *, errors_only: bool = True) -> list[CheckResult]:
        return [
            result for result in self.verification
            if not result.passed and (result.severity == "error" or not errors_only)
        ]


class Conflict(BaseModel):
    """Two or more changes or atoms that cannot all hold (stage ``consolidate``)."""

    id: str
    change_ids: list[str] = Field(default_factory=list)
    atom_ids: list[str] = Field(default_factory=list)
    description: str = ""
    resolution: str = ""                         # how it was resolved, or empty when open
    resolved_by: str | None = None


# ---------------------------------------------------------------------------
# Output: profile elements (scoring contract), artefacts, conformance
# ---------------------------------------------------------------------------


class ProfileElement(BaseModel):
    """One (target class, property path) the profile adds or tightens on its base."""

    id: str | None = None
    target_class: str
    path: str | None = None                      # empty only for class_addition
    kind: ElementKind
    obligation: Obligation | None = None
    min_count: int | None = None
    max_count: int | None = None
    range_class: str | None = None
    range_datatype: str | None = None
    node_kind: NodeKind | None = None
    controlled_vocabulary: list[str] = Field(default_factory=list)
    severity: Severity | None = None
    delta_status: DeltaStatus | None = None
    source: ElementSource | None = None
    source_atom_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class ProfileDelta(BaseModel):
    profile_id: str
    base_profile_ids: list[str] = Field(default_factory=list)
    source: ElementSource | None = "generated"
    elements: list[ProfileElement] = Field(default_factory=list)
    notes: str | None = None


class Artifact(BaseModel):
    name: str                                    # file name, e.g. extension.shacl.ttl
    title: str = ""
    media_type: str = "text/plain"
    content: str = ""
    sha256: str = ""
    created_at: str = Field(default_factory=now_iso)


class ConformanceItem(BaseModel):
    target_class: str | None = None
    path: str | None = None
    change_id: str | None = None
    facet: str | None = None
    base_value: str | None = None
    new_value: str | None = None
    status: str | None = None
    message: str = ""


class ConformanceCheck(BaseModel):
    id: str                                      # C1, C2, ...
    title: str
    passed: bool
    severity: Literal["error", "warning", "info"] = "error"
    message: str = ""
    source: str = ""                             # the rule's origin (guideline quote or "derived")
    items: list[ConformanceItem] = Field(default_factory=list)


class ConformanceReport(BaseModel):
    base_profile_id: str
    verdict: Literal["conformant", "conformant_with_warnings", "non_conformant", "not_checked"] = "not_checked"
    summary: str = ""
    checks: list[ConformanceCheck] = Field(default_factory=list)
    delta_counts: dict[str, int] = Field(default_factory=dict)   # added / tightened / unchanged / loosened
    witness_turtle: str = ""
    generated_at: str = Field(default_factory=now_iso)


# ---------------------------------------------------------------------------
# Blackboard, LLM calls, projects
# ---------------------------------------------------------------------------


class BlackboardEntry(BaseModel):
    """An append-only record of something a knowledge source (or a human) put on the workbench."""

    id: str = ""
    project_id: str = ""
    seq: int = 0
    stage: Stage
    kind: str                                    # atom_lint, assessment, candidates, proposal, check, repair,
                                                 # merge, conflict, artifact, conformance, human_decision, note ...
    subject_type: Literal["atom", "change", "project"] = "project"
    subject_id: str = ""
    author: str = "rule:engine"
    summary: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


class LLMCallRecord(BaseModel):
    """Audit record of one model call. Never holds credentials."""

    id: str = ""
    project_id: str = ""
    stage: str = ""
    purpose: str = ""                            # propose, repair, attribution ...
    subject_id: str = ""
    provider: str = ""
    model: str = ""
    prompt_version: str = ""
    request_hash: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    response_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    duration_ms: int = 0
    cached: bool = False                         # served from the local replay cache
    status: Literal["ok", "error", "refused", "invalid_output"] = "ok"
    error: str = ""
    created_at: str = Field(default_factory=now_iso)


class LLMSettings(BaseModel):
    """Which model does the work. The API key is NOT part of this model: it is
    held in server memory only and never written to the store or to exports."""

    provider: Literal["mock", "anthropic", "openai-compatible"] = "mock"
    model: str | None = None
    base_url: str | None = None
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    temperature: float | None = None             # openai-compatible only; ignored elsewhere
    max_output_tokens: int = 16000
    timeout_seconds: float = 240.0
    step_models: dict[str, str] = Field(default_factory=dict)   # optional model per step


class PipelineConfig(BaseModel):
    """Switches of the pipeline. Each component can be turned off on its own,
    which is what the experiment conditions C2..C5 need."""

    retrieval: bool = True
    top_k: int = 8
    verify: bool = True
    repair_rounds: int = 3
    attribution_check: bool = True               # T2: model-judged "is this element supported by its atom?"
    votes: int = 1                               # independent proposals per atom; majority wins (1 = off)
    auto_accept: bool = True                     # verified changes stand without a human
    auto_accept_min_confidence: float = 0.5
    require_human_signoff: bool = True           # nothing is released without a final human review
    use_hints: bool = False                      # show upstream vocabulary hints to the proposer
    exclude_namespaces: list[str] = Field(default_factory=list)   # leakage control: hide these from the index
    max_parallel_calls: int = 4


class SignOff(BaseModel):
    by: str
    note: str = ""
    change_set_hash: str = ""
    at: str = Field(default_factory=now_iso)


class Project(BaseModel):
    id: str
    name: str
    description: str = ""
    base_profile_id: str = "dcat-ap-3.0.1"
    profile_title: str = ""
    profile_namespace: str = "https://example.org/profile#"
    profile_prefix: str = "ex"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    stage_states: dict[str, StageState] = Field(default_factory=dict)
    signoff: SignOff | None = None


class ProjectSnapshot(BaseModel):
    """Everything the workbench needs to render one project."""

    project: Project
    atoms: list[Atom] = Field(default_factory=list)
    assessments: list[AtomAssessment] = Field(default_factory=list)
    candidates: dict[str, list[Candidate]] = Field(default_factory=dict)   # atom id -> candidates
    changes: list[ProfileChange] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    coverage: dict[str, AtomCoverage] = Field(default_factory=dict)        # atom id -> coverage
    artifacts: list[Artifact] = Field(default_factory=list)
    conformance: ConformanceReport | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mappings to the RQ2 contracts of the existing repositories
# ---------------------------------------------------------------------------

# profile_change.linkml.yaml (legacy change types) <- our change kinds
LEGACY_CHANGE_TYPE: dict[str, str] = {
    "reuse_property": "reuse_property",
    "refine_property": "add_constraint",
    "mint_property": "create_extension_property",
    "reuse_class": "create_profile_class",
    "mint_class": "create_profile_class",
    "usage_note": "add_usage_note",
}

# profile_element.linkml.yaml (scoring kinds) <- our change kinds; usage notes are not scored
ELEMENT_KIND: dict[str, str | None] = {
    "reuse_property": "reuse",
    "refine_property": "refine",
    "mint_property": "mint",
    "reuse_class": "class_addition",
    "mint_class": "class_addition",
    "usage_note": None,
}

OBLIGATION_RANK: dict[str, int] = {"unknown": 0, "optional": 1, "recommended": 2, "mandatory": 3}
OBLIGATION_SEVERITY: dict[str, str] = {
    "mandatory": "Violation", "recommended": "Warning", "optional": "Info", "unknown": "Warning",
}
# The strongest obligation an atom's wording licenses.
MODALITY_OBLIGATION: dict[str, str] = {
    "must": "mandatory", "should": "recommended", "may": "optional", "unspecified": "recommended",
}
