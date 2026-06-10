from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from ..models import (
    AnalysisRequest,
    CandidateMetadataAction,
    CandidateRequirement,
    ExtractionProvenance,
    NormalizedIntent,
    SourceEvidence,
    UserTask,
)
from .client import LLMClient

PROMPT_VERSION = 'rrs-extract-v1'

MAX_CHARS_PER_ARTIFACT = 12000
MAX_TOTAL_CHARS = 60000

TEXT_SOURCE_NAME = 'text description'

REQUIREMENT_TYPES = [
    'descriptive_metadata',
    'semantic_anchor',
    'technical_metadata',
    'access_policy',
    'quality_provenance',
    'lifecycle_context',
    'controlled_vocabulary',
    'validation_constraint',
    'competency_question',
]

SYSTEM_PROMPT = f"""You are a metadata profile engineering assistant supporting a reuse-first, \
requirements-driven workflow for building DCAT/DCAT-AP-compatible application profiles \
(FAIR-oriented dataset cataloging, construction domain and beyond).

You receive heterogeneous source materials: free-text requirement descriptions, competency \
questions and user tasks from domain experts, AAS (Asset Administration Shell) structures, \
IFC snippets, existing DCAT/RDF metadata, and standards or profile excerpts.

Your task: extract CANDIDATE profile-design requirements as structured, traceable records. \
You are a bounded assistant - every record will be reviewed by a human expert before acceptance.

Rules:
1. Each requirement must be a single, testable profile-design statement of the form \
"A dcat:Dataset (or dcat:Distribution / dcat:Catalog / dcat:DataService) should/must ...".
2. EVIDENCE MUST BE VERBATIM. Every evidence quote must be an exact, contiguous substring \
copied character-for-character from the named source artifact. Never paraphrase, never \
summarize, never merge text from different places into one quote. Quotes are programmatically \
verified against the sources; fabricated quotes are discarded.
3. Reuse first: prefer existing DCAT/DCAT-AP/Dublin Core terms (dcterms:, dcat:, foaf:, prov:, \
skos:). Suggest a profile-specific extension term (cx: prefix) only when no standard term fits, \
and say why in the action rationale.
4. requirement_type must be one of: {', '.join(REQUIREMENT_TYPES)}.
5. fair_dimensions uses letters F, A, I, R (Findable, Accessible, Interoperable, Reusable); \
include only dimensions the requirement genuinely supports, with a one-sentence rationale.
6. If user tasks / competency questions are provided (each with an id), list the ids of the \
tasks each requirement supports in supports_user_tasks. Only link a task if the requirement \
genuinely helps answer or accomplish it.
7. Do not invent requirements that have no support in the sources. Fewer, well-grounded \
records are better than many speculative ones.
8. Normalize: if several places express the same need, produce ONE requirement with multiple \
evidence quotes rather than near-duplicates."""


class LLMEvidence(BaseModel):
    artifact_name: str = Field(description='Exact name of the source artifact the quote comes from')
    quote: str = Field(description='Verbatim contiguous substring copied from that artifact')


class LLMRequirement(BaseModel):
    statement: str = Field(description='Normalized profile-design statement')
    requirement_type: str = Field(description='One of the allowed requirement types')
    resource_type: str = Field(description='Dataset | Distribution | Catalog | DataService | Agent | Concept')
    metadata_need: str = Field(description='Short phrase naming the metadata need')
    value_kind: str = Field(description='literal | uri | controlled_concept | class_reference | date | agent | distribution')
    obligation: str = Field(description='mandatory | recommended | optional')
    fair_dimensions: list[str] = Field(default_factory=list)
    fair_rationale: str = ''
    action: str = Field(description='reuse_existing_term | specialize_existing_term | create_extension | add_constraint | add_usage_note')
    candidate_terms: list[str] = Field(default_factory=list, description='Prefixed candidate terms, e.g. dcterms:title, dcat:theme, cx:hasLifecyclePhase')
    action_rationale: str = ''
    supports_user_tasks: list[str] = Field(default_factory=list)
    evidence: list[LLMEvidence] = Field(default_factory=list)
    confidence: float = 0.7


class LLMExtractionResult(BaseModel):
    requirements: list[LLMRequirement] = Field(default_factory=list)


RESOURCE_TYPES = {'Catalog', 'Dataset', 'Distribution', 'DataService', 'Agent', 'Concept'}
VALUE_KINDS = {'literal', 'uri', 'controlled_concept', 'class_reference', 'date', 'agent', 'distribution'}
OBLIGATIONS = {'mandatory', 'recommended', 'optional'}
ACTIONS = {'reuse_existing_term', 'specialize_existing_term', 'create_extension', 'add_constraint', 'add_usage_note', 'no_action'}


def extract_with_llm(
    payload: AnalysisRequest,
    client: LLMClient,
) -> tuple[list[CandidateRequirement], list[str]]:
    """Run LLM-assisted requirement extraction over the request sources.

    Returns candidate requirements (with provenance and verified evidence)
    plus human-readable warnings (e.g. discarded hallucinated quotes).
    """
    sources = build_sources(payload)
    if not sources:
        return [], ['No analyzable source content was provided for LLM extraction.']

    user_prompt = build_user_prompt(sources, payload.user_tasks)
    result = client.generate_structured(system=SYSTEM_PROMPT, user=user_prompt, output_model=LLMExtractionResult)

    warnings: list[str] = []
    requirements: list[CandidateRequirement] = []
    known_task_ids = {task.id for task in payload.user_tasks}
    created_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    description = client.describe()

    for item in result.requirements:
        requirement = convert_requirement(
            item,
            sources,
            known_task_ids,
            warnings,
            provenance=ExtractionProvenance(
                strategy='llm',
                extractor=f'llm-extractor/{PROMPT_VERSION}',
                model_id=description.get('model'),
                prompt_version=PROMPT_VERSION,
                created_at=created_at,
            ),
        )
        if requirement is not None:
            requirements.append(requirement)
    return requirements, warnings


def build_sources(payload: AnalysisRequest) -> dict[str, dict[str, str]]:
    """Collect named source texts: {artifact_name: {'kind': ..., 'text': ...}}."""
    from ..service import decode_artifact_text, detect_kind

    sources: dict[str, dict[str, str]] = {}
    if payload.text and payload.text.strip():
        sources[TEXT_SOURCE_NAME] = {'kind': 'text', 'text': payload.text}
    for artifact in payload.artifacts:
        kind = detect_kind(artifact)
        text = decode_artifact_text(artifact)
        if text and text.strip():
            sources[artifact.name] = {'kind': kind, 'text': text}
    return sources


def build_user_prompt(sources: dict[str, dict[str, str]], user_tasks: list[UserTask]) -> str:
    parts: list[str] = []
    if user_tasks:
        parts.append('USER TASKS / COMPETENCY QUESTIONS (reference these ids in supports_user_tasks):')
        for task in user_tasks:
            stakeholder = f' [stakeholder: {task.stakeholder}]' if task.stakeholder else ''
            parts.append(f'- {task.id} ({task.kind}){stakeholder}: {task.statement}')
        parts.append('')

    total = 0
    for name, source in sources.items():
        text = source['text']
        if len(text) > MAX_CHARS_PER_ARTIFACT:
            text = text[:MAX_CHARS_PER_ARTIFACT]
        if total + len(text) > MAX_TOTAL_CHARS:
            remaining = MAX_TOTAL_CHARS - total
            if remaining <= 0:
                parts.append(f'=== SOURCE ARTIFACT: {name} (kind: {source["kind"]}) === [omitted: input budget exhausted]')
                continue
            text = text[:remaining]
        total += len(text)
        parts.append(f'=== SOURCE ARTIFACT: {name} (kind: {source["kind"]}) ===')
        parts.append(text)
        parts.append(f'=== END OF {name} ===')
        parts.append('')

    parts.append('Extract the candidate profile-design requirements from these sources now.')
    return '\n'.join(parts)


def convert_requirement(
    item: LLMRequirement,
    sources: dict[str, dict[str, str]],
    known_task_ids: set[str],
    warnings: list[str],
    provenance: ExtractionProvenance,
) -> CandidateRequirement | None:
    from ..service import category_for_requirement_type, stable_id, title_for_statement

    statement = item.statement.strip()
    if not statement:
        return None

    verified_evidence: list[SourceEvidence] = []
    dropped = 0
    for evidence in item.evidence:
        located = locate_quote(evidence.quote, evidence.artifact_name, sources)
        if located is None:
            dropped += 1
            warnings.append(
                f"Discarded unverifiable evidence quote for '{title_for_statement(statement)}' "
                f'(not found verbatim in {evidence.artifact_name}): "{truncate(evidence.quote, 120)}"'
            )
            continue
        artifact_name, kind, start, end, quote = located
        verified_evidence.append(
            SourceEvidence(
                evidence_unit_id=stable_id('ev', artifact_name, start, end),
                source_id=stable_id('src', artifact_name),
                artifact_name=artifact_name,
                artifact_kind=kind,
                locator=f'chars:{start}-{end}',
                evidence_text=quote,
                extracted_facts=[],
            )
        )

    evidence_verified = dropped == 0 and bool(verified_evidence)
    provenance = provenance.model_copy(update={'evidence_verified': evidence_verified})
    if not verified_evidence:
        provenance.notes.append('All evidence quotes failed verbatim verification; requirement needs manual review.')

    requirement_type = item.requirement_type if item.requirement_type in REQUIREMENT_TYPES else 'unknown'
    resource_type = item.resource_type if item.resource_type in RESOURCE_TYPES else 'Dataset'
    value_kind = item.value_kind if item.value_kind in VALUE_KINDS else 'unknown'
    obligation = item.obligation if item.obligation in OBLIGATIONS else 'unknown'
    action = item.action if item.action in ACTIONS else 'reuse_existing_term'
    fair = [dim for dim in item.fair_dimensions if dim in {'F', 'A', 'I', 'R'}]

    unknown_tasks = [task_id for task_id in item.supports_user_tasks if known_task_ids and task_id not in known_task_ids]
    if unknown_tasks:
        warnings.append(f"Requirement '{title_for_statement(statement)}' referenced unknown user task ids: {', '.join(unknown_tasks)}")
    supported_tasks = [task_id for task_id in item.supports_user_tasks if task_id in known_task_ids]

    confidence = max(0.05, min(0.95, item.confidence))
    if not evidence_verified:
        confidence = min(confidence, 0.4)

    category = category_for_requirement_type(requirement_type)
    return CandidateRequirement(
        id=stable_id('req', 'llm', statement, *(unit.evidence_unit_id for unit in verified_evidence[:4])),
        raw_statement='; '.join(unit.evidence_text for unit in verified_evidence[:3]) or statement,
        normalized_statement=statement,
        requirement_type=requirement_type,
        source_evidence=verified_evidence,
        normalized_intent=NormalizedIntent(
            resource_type=resource_type,
            metadata_need=item.metadata_need or 'describe dataset for discovery',
            value_kind=value_kind,
            obligation_hint=obligation,
        ),
        fair_dimensions=fair,
        fair_rationale=item.fair_rationale or None,
        candidate_metadata_actions=[
            CandidateMetadataAction(
                action=action,
                target_class=resource_type,
                candidate_terms=item.candidate_terms,
                rationale=item.action_rationale or 'Proposed by LLM-assisted extraction; review before acceptance.',
            )
        ],
        supports_user_tasks=supported_tasks,
        provenance=provenance,
        status='candidate' if evidence_verified else 'needs_review',
        title=title_for_statement(statement),
        description=statement,
        category=category,
        source=', '.join(sorted({unit.artifact_name for unit in verified_evidence})) or 'llm extraction',
        evidence=[unit.evidence_text for unit in verified_evidence[:8]],
        confidence=confidence,
    )


def locate_quote(
    quote: str,
    artifact_name: str,
    sources: dict[str, dict[str, str]],
) -> tuple[str, str, int, int, str] | None:
    """Verify a quote occurs verbatim in its claimed source (whitespace-tolerant).

    Returns (artifact_name, kind, start, end, matched_text) or None. Falls back
    to searching all sources if the claimed artifact name does not match.
    """
    quote = quote.strip()
    if not quote:
        return None

    candidates = []
    if artifact_name in sources:
        candidates.append((artifact_name, sources[artifact_name]))
    candidates.extend((name, source) for name, source in sources.items() if name != artifact_name)

    for name, source in candidates:
        text = source['text']
        start = text.find(quote)
        if start >= 0:
            return name, source['kind'], start, start + len(quote), quote
        match = whitespace_tolerant_search(quote, text)
        if match is not None:
            start, end = match
            return name, source['kind'], start, end, text[start:end]
    return None


def whitespace_tolerant_search(quote: str, text: str) -> tuple[int, int] | None:
    tokens = quote.split()
    if not tokens:
        return None
    pattern = r'\s+'.join(re.escape(token) for token in tokens)
    try:
        match = re.search(pattern, text)
    except re.error:
        return None
    if match:
        return match.start(), match.end()
    return None


def truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 3] + '...'


def merge_hybrid(
    llm_requirements: list[CandidateRequirement],
    rule_requirements: list[CandidateRequirement],
) -> list[CandidateRequirement]:
    """Hybrid strategy: LLM records first, rule-based records that add new
    metadata needs appended as grounding. Duplicate detection downstream
    surfaces remaining overlaps for the reviewer."""
    from ..service import token_jaccard

    merged = list(llm_requirements)
    for rule_requirement in rule_requirements:
        need = rule_requirement.normalized_intent.metadata_need
        if any(token_jaccard(need, existing.normalized_intent.metadata_need) >= 0.6 for existing in merged):
            continue
        merged.append(rule_requirement)
    return merged
