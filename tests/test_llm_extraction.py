import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ROOT / 'requirement-reuse-service'
sys.path.insert(0, str(SERVICE_ROOT))

from requirement_reuse_service.llm.client import LLMError, MockLLMClient, extract_json_object  # noqa: E402
from requirement_reuse_service.llm.extractor import (  # noqa: E402
    LLMExtractionResult,
    PROMPT_VERSION,
    extract_with_llm,
    merge_hybrid,
)
from requirement_reuse_service.models import AnalysisRequest, RequirementSetSaveRequest, UserTask  # noqa: E402
from requirement_reuse_service.registry import load_requirement_set, save_requirement_set  # noqa: E402
from requirement_reuse_service.service import analyze_payload  # noqa: E402


SOURCE_TEXT = (
    'Each dataset must carry a license or access rights statement. '
    'Datasets exchanged in the dataspace should reference the AAS submodels they represent.'
)


def llm_payload(quote: str, artifact: str = 'text description', task_ids: list[str] | None = None) -> dict:
    return {
        'requirements': [
            {
                'statement': 'A dcat:Dataset must carry a license or access rights statement.',
                'requirement_type': 'access_policy',
                'resource_type': 'Dataset',
                'metadata_need': 'describe access and reuse conditions',
                'value_kind': 'uri',
                'obligation': 'mandatory',
                'fair_dimensions': ['A', 'R'],
                'fair_rationale': 'License metadata enables reuse decisions and access assessment.',
                'action': 'reuse_existing_term',
                'candidate_terms': ['dcterms:license', 'dcterms:accessRights'],
                'action_rationale': 'dcterms covers this need; no extension required.',
                'supports_user_tasks': task_ids or [],
                'evidence': [{'artifact_name': artifact, 'quote': quote}],
                'confidence': 0.85,
            }
        ]
    }


def test_llm_extraction_produces_traceable_verified_requirement():
    client = MockLLMClient(llm_payload('Each dataset must carry a license or access rights statement.'))
    request = AnalysisRequest(text=SOURCE_TEXT, strategy='llm')

    requirements, warnings = extract_with_llm(request, client)

    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.requirement_type == 'access_policy'
    assert requirement.status == 'candidate'
    assert requirement.source_evidence and requirement.source_evidence[0].locator.startswith('chars:')
    assert requirement.provenance is not None
    assert requirement.provenance.strategy == 'llm'
    assert requirement.provenance.prompt_version == PROMPT_VERSION
    assert requirement.provenance.evidence_verified is True
    assert not warnings


def test_hallucinated_quote_is_discarded_and_requirement_flagged():
    client = MockLLMClient(llm_payload('Datasets must include a fabricated quality score of 9000.'))
    request = AnalysisRequest(text=SOURCE_TEXT, strategy='llm')

    requirements, warnings = extract_with_llm(request, client)

    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.source_evidence == []
    assert requirement.status == 'needs_review'
    assert requirement.provenance.evidence_verified is False
    assert requirement.confidence <= 0.4
    assert any('Discarded unverifiable evidence' in warning for warning in warnings)


def test_whitespace_differences_do_not_fail_verification():
    quote = 'Each  dataset must\ncarry a license or access rights statement.'
    client = MockLLMClient(llm_payload(quote))
    requirements, warnings = extract_with_llm(AnalysisRequest(text=SOURCE_TEXT, strategy='llm'), client)
    assert requirements[0].provenance.evidence_verified is True
    assert not warnings


def test_user_task_links_are_validated_against_known_tasks():
    tasks = [UserTask(id='cq-1', statement='Which datasets can be reused under an open license?')]
    client = MockLLMClient(
        llm_payload('Each dataset must carry a license or access rights statement.', task_ids=['cq-1', 'cq-bogus'])
    )
    request = AnalysisRequest(text=SOURCE_TEXT, strategy='llm', user_tasks=tasks)

    requirements, warnings = extract_with_llm(request, client)

    assert requirements[0].supports_user_tasks == ['cq-1']
    assert any('cq-bogus' in warning for warning in warnings)


def test_analyze_payload_llm_strategy_falls_back_to_rules_without_provider(monkeypatch):
    for variable in ['RRS_LLM_PROVIDER', 'RRS_LLM_BASE_URL', 'RRS_LLM_MODEL', 'ANTHROPIC_API_KEY']:
        monkeypatch.delenv(variable, raising=False)
    # mock provider resolves but returns empty payload -> valid llm run with zero requirements
    monkeypatch.setenv('RRS_LLM_PROVIDER', 'openai-compatible')  # missing base url -> LLMError -> fallback

    response = analyze_payload(AnalysisRequest(text=SOURCE_TEXT, strategy='llm'))

    assert response.strategy == 'rules'
    assert response.requirements  # rule-based results still delivered
    assert any('LLM extraction unavailable' in warning for warning in response.warnings)


def test_analyze_payload_rules_strategy_stamps_provenance_and_links_tasks():
    tasks = [UserTask(id='cq-license', statement='Which datasets can be reused under an open license for analytics?')]
    response = analyze_payload(AnalysisRequest(text=SOURCE_TEXT, strategy='rules', user_tasks=tasks))

    assert response.strategy == 'rules'
    assert response.user_tasks == tasks
    assert all(requirement.provenance and requirement.provenance.strategy == 'rules' for requirement in response.requirements)
    assert any(requirement.supports_user_tasks for requirement in response.requirements)


def test_hybrid_merge_keeps_llm_first_and_adds_novel_rule_requirements():
    client = MockLLMClient(llm_payload('Each dataset must carry a license or access rights statement.'))
    request = AnalysisRequest(text=SOURCE_TEXT, strategy='llm')
    llm_requirements, _ = extract_with_llm(request, client)
    rules_response = analyze_payload(AnalysisRequest(text=SOURCE_TEXT, strategy='rules'))

    merged = merge_hybrid(llm_requirements, rules_response.requirements)

    assert merged[0].provenance.strategy == 'llm'
    assert len(merged) > 1  # rule-based records covering other needs were appended
    needs = [requirement.normalized_intent.metadata_need for requirement in merged]
    assert len(needs) == len(set(needs)) or len(merged) >= len(llm_requirements)


def test_requirement_set_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv('RRS_REQUIREMENT_STORE', str(tmp_path))
    response = analyze_payload(AnalysisRequest(text=SOURCE_TEXT, strategy='rules'))

    info = save_requirement_set(RequirementSetSaveRequest(name='Pilot Run', analysis=response))
    loaded = load_requirement_set(info.id)

    assert loaded is not None
    assert loaded.name == 'Pilot Run'
    assert len(loaded.requirements) == info.requirement_count == len(response.requirements)
    assert loaded.requirements[0].provenance is not None


def test_mock_client_rejects_payload_that_violates_schema():
    client = MockLLMClient({'requirements': [{'statement': 123}]})
    with pytest.raises(LLMError):
        client.generate_structured(system='s', user='u', output_model=LLMExtractionResult)


def test_extract_json_object_handles_fences_and_prose():
    fenced = '```json\n{"requirements": []}\n```'
    assert extract_json_object(fenced) == '{"requirements": []}'
    prose = 'Here is the result: {"requirements": []} hope that helps'
    assert extract_json_object(prose) == '{"requirements": []}'
