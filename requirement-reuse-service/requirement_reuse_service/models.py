from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ArtifactKind = Literal[
    'text',
    'ifc',
    'aas-json',
    'aas-xml',
    'aasx',
    'dcat-rdf',
    'profile-spec',
    'use-case',
    'unknown',
]

RequirementType = Literal[
    'descriptive_metadata',
    'semantic_anchor',
    'technical_metadata',
    'access_policy',
    'quality_provenance',
    'lifecycle_context',
    'controlled_vocabulary',
    'validation_constraint',
    'competency_question',
    'unknown',
]

ResourceType = Literal['Catalog', 'Dataset', 'Distribution', 'DataService', 'Agent', 'Concept', 'Unknown']
ValueKind = Literal['literal', 'uri', 'controlled_concept', 'class_reference', 'date', 'agent', 'distribution', 'unknown']
ObligationHint = Literal['mandatory', 'recommended', 'optional', 'unknown']
ReviewStatus = Literal['candidate', 'approved', 'rejected', 'merged', 'needs_review']
FairDimension = Literal['F', 'A', 'I', 'R']
ExtractionStrategy = Literal['rules', 'llm', 'hybrid']
UserTaskKind = Literal['competency_question', 'user_task', 'stakeholder_need']


class ArtifactPayload(BaseModel):
    name: str = 'artifact'
    media_type: str | None = None
    content: str
    content_encoding: Literal['text', 'base64'] = 'text'


class UserTask(BaseModel):
    """An expert-provided competency question, user task, or stakeholder need.

    Requirements link back to user tasks via ``supports_user_tasks`` so that
    competency-question coverage can be computed during evaluation (RQ1).
    """

    id: str
    statement: str
    kind: UserTaskKind = 'competency_question'
    stakeholder: str | None = None
    source: str = 'expert input'


class ExtractionProvenance(BaseModel):
    """Records how a requirement candidate was produced, for reproducibility.

    ``editor_history`` accumulates human corrections (field, old value, new
    value) so that expert editing effort can be measured (H1 / Section 6.2).
    """

    strategy: ExtractionStrategy = 'rules'
    extractor: str = 'rule-based-v1'
    model_id: str | None = None
    prompt_version: str | None = None
    created_at: str | None = None
    evidence_verified: bool | None = None
    notes: list[str] = Field(default_factory=list)
    editor_history: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    text: str | None = None
    artifacts: list[ArtifactPayload] = Field(default_factory=list)
    user_tasks: list[UserTask] = Field(default_factory=list)
    strategy: ExtractionStrategy = 'rules'
    llm_model: str | None = None


class ArtifactSummary(BaseModel):
    name: str
    kind: str
    evidence_count: int = 0
    notes: list[str] = Field(default_factory=list)


class EvidenceUnit(BaseModel):
    id: str
    source_id: str
    artifact_name: str
    artifact_kind: ArtifactKind = 'unknown'
    locator: str | None = None
    content: str
    extracted_facts: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class SourceEvidence(BaseModel):
    evidence_unit_id: str
    source_id: str
    artifact_name: str
    artifact_kind: str
    locator: str | None = None
    evidence_text: str
    extracted_facts: list[str] = Field(default_factory=list)


class NormalizedIntent(BaseModel):
    resource_type: ResourceType = 'Dataset'
    metadata_need: str = 'describe dataset for discovery'
    value_kind: ValueKind = 'unknown'
    obligation_hint: ObligationHint = 'unknown'


class CandidateMetadataAction(BaseModel):
    action: Literal[
        'reuse_existing_term',
        'specialize_existing_term',
        'create_extension',
        'add_constraint',
        'add_usage_note',
        'no_action',
    ]
    target_class: str | None = None
    candidate_terms: list[str] = Field(default_factory=list)
    rationale: str


class SemanticCandidate(BaseModel):
    id: str
    label: str
    kind: str
    identifier: str | None = None
    source: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.6


class ExtractedAttribute(BaseModel):
    id: str
    source: str
    path: str
    label: str
    value: str
    category: str
    value_type: str = 'string'
    confidence: float = 0.7


class MetadataCandidate(BaseModel):
    id: str
    property: str
    label: str
    category: str
    range: str = 'string'
    requirement_level: Literal['mandatory', 'recommended', 'optional'] = 'recommended'
    source: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.6


class CandidateRequirement(BaseModel):
    id: str

    raw_statement: str | None = None
    normalized_statement: str | None = None
    requirement_type: RequirementType = 'unknown'
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    normalized_intent: NormalizedIntent = Field(default_factory=NormalizedIntent)
    fair_dimensions: list[FairDimension] = Field(default_factory=list)
    fair_rationale: str | None = None
    candidate_metadata_actions: list[CandidateMetadataAction] = Field(default_factory=list)
    supports_user_tasks: list[str] = Field(default_factory=list)
    validation_evidence: list[str] = Field(default_factory=list)
    provenance: ExtractionProvenance | None = None
    status: ReviewStatus = 'candidate'
    review_notes: str | None = None
    merged_from: list[str] = Field(default_factory=list)

    # Backward-compatible fields used by earlier recommendation/UI code.
    title: str | None = None
    description: str | None = None
    category: str | None = None
    source: str | None = None
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.6


class DuplicateGroup(BaseModel):
    id: str
    requirement_ids: list[str]
    suggested_merged_statement: str
    reason: str
    confidence: float = 0.7


class CompetencyQuestion(BaseModel):
    id: str
    question: str
    category: str
    source: str
    evidence: str | None = None


class AnalysisResponse(BaseModel):
    strategy: ExtractionStrategy = 'rules'
    artifacts: list[ArtifactSummary] = Field(default_factory=list)
    evidence_units: list[EvidenceUnit] = Field(default_factory=list)
    extracted_attributes: list[ExtractedAttribute] = Field(default_factory=list)
    requirements: list[CandidateRequirement] = Field(default_factory=list)
    duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)
    semantic_candidates: list[SemanticCandidate] = Field(default_factory=list)
    metadata_candidates: list[MetadataCandidate] = Field(default_factory=list)
    competency_questions: list[CompetencyQuestion] = Field(default_factory=list)
    user_tasks: list[UserTask] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RequirementSetSaveRequest(BaseModel):
    name: str
    description: str | None = None
    analysis: AnalysisResponse | None = None
    requirements: list[CandidateRequirement] = Field(default_factory=list)
    user_tasks: list[UserTask] = Field(default_factory=list)


class RequirementSetInfo(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: str
    strategy: ExtractionStrategy | None = None
    requirement_count: int = 0


class RequirementSet(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: str
    strategy: ExtractionStrategy | None = None
    requirements: list[CandidateRequirement] = Field(default_factory=list)
    user_tasks: list[UserTask] = Field(default_factory=list)


class RequirementSetListResponse(BaseModel):
    requirement_sets: list[RequirementSetInfo] = Field(default_factory=list)


class RequirementSetLoadRequest(BaseModel):
    id: str


class RecommendationRequest(BaseModel):
    analysis: AnalysisResponse | None = None
    requirements: list[CandidateRequirement] = Field(default_factory=list)
    semantic_candidates: list[SemanticCandidate] = Field(default_factory=list)
    metadata_candidates: list[MetadataCandidate] = Field(default_factory=list)


class ReuseRecommendation(BaseModel):
    id: str
    label: str
    vocabulary: str
    term_uri: str
    priority: int
    action: Literal['reuse', 'profile', 'extension'] = 'reuse'
    requirement_id: str | None = None
    candidate_id: str | None = None
    rationale: str
    confidence: float = 0.6


class RecommendationResponse(BaseModel):
    recommendations: list[ReuseRecommendation] = Field(default_factory=list)
    extension_candidates: list[MetadataCandidate] = Field(default_factory=list)


class ConstraintGenerationRequest(BaseModel):
    analysis: AnalysisResponse | None = None
    requirements: list[CandidateRequirement] = Field(default_factory=list)
    recommendations: list[ReuseRecommendation] = Field(default_factory=list)
    selected_recommendation_ids: list[str] = Field(default_factory=list)


class ConstraintGenerationResponse(BaseModel):
    shacl: str
    profile_draft: dict[str, Any]
    validation_notes: list[str] = Field(default_factory=list)
