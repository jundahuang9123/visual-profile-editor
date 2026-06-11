"""RQ2 tests: approved requirements -> ProfileChangeSet -> LinkML draft -> SHACL."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ROOT / 'requirement-reuse-service'
sys.path.insert(0, str(SERVICE_ROOT))

from rdflib import Graph  # noqa: E402

from requirement_reuse_service.models import (  # noqa: E402
    CandidateMetadataAction,
    CandidateRequirement,
    ConstraintHint,
    GenerateProfileChangesRequest,
    GenerateProfileDraftRequest,
    NormalizedIntent,
    RQ2ExportRequest,
    SourceEvidence,
)
from requirement_reuse_service.profile_generation import (  # noqa: E402
    build_rq2_package,
    generate_profile_changes,
    generate_profile_draft,
    generate_shacl_from_changes,
)


def make_requirement(
    requirement_id: str,
    status: str = 'approved',
    action: str = 'reuse_existing_term',
    terms: list[str] | None = None,
    resource: str = 'Dataset',
    obligation: str = 'recommended',
    value_kind: str = 'uri',
) -> CandidateRequirement:
    return CandidateRequirement(
        id=requirement_id,
        normalized_statement=f'A dcat:{resource} should satisfy {requirement_id}.',
        requirement_type='access_policy',
        requirement_scope='profile_element',
        status=status,  # type: ignore[arg-type]
        validation_status='valid',
        source_evidence=[
            SourceEvidence(
                evidence_unit_id=f'ev-{requirement_id}',
                source_id='src-1',
                artifact_name='stakeholder-needs.md',
                artifact_kind='text',
                evidence_text=f'evidence for {requirement_id}',
            )
        ],
        normalized_intent=NormalizedIntent(
            resource_type=resource,  # type: ignore[arg-type]
            metadata_need=f'metadata need {requirement_id}',
            value_kind=value_kind,  # type: ignore[arg-type]
            obligation_hint=obligation,  # type: ignore[arg-type]
        ),
        candidate_metadata_actions=[
            CandidateMetadataAction(
                action=action,  # type: ignore[arg-type]
                target_class=resource,
                candidate_terms=terms if terms is not None else ['dcterms:license'],
                rationale=f'rationale for {requirement_id}',
                constraint_hint=ConstraintHint(value_kind=value_kind, obligation=obligation),  # type: ignore[arg-type]
            )
        ],
    )


def changes_for(requirements, **kwargs):
    return generate_profile_changes(GenerateProfileChangesRequest(requirements=requirements, **kwargs))


def accept_candidate_changes(change_set):
    for change in change_set.changes:
        if change.review_status == 'candidate':
            change.review_status = 'accepted'
    return change_set


def test_approved_only_filtering_excludes_rejected_and_merged():
    requirements = [
        make_requirement('R-approved', status='approved'),
        make_requirement('R-rejected', status='rejected', terms=['dcterms:title']),
        make_requirement('R-merged', status='merged', terms=['dcat:keyword']),
        make_requirement('R-candidate', status='candidate', terms=['dcat:theme']),
    ]
    change_set = changes_for(requirements)
    requirement_ids = {requirement_id for change in change_set.changes for requirement_id in change.source_requirement_ids}
    assert requirement_ids == {'R-approved'}
    assert any('not approved' in warning for warning in change_set.warnings)


def test_zero_approved_requirements_yields_empty_change_set_with_warning():
    change_set = changes_for([make_requirement('R1', status='candidate')])
    assert change_set.changes == []
    assert any('No approved requirements' in warning for warning in change_set.warnings)


def test_reuse_existing_term_becomes_reused_slot_with_standard_uri():
    change_set = changes_for([make_requirement('R1', terms=['dcterms:license'])])
    change = change_set.changes[0]
    assert change.change_type == 'reuse_property'
    assert change.term_uri == 'http://purl.org/dc/terms/license'
    assert change.slot_name == 'license'
    assert change.source_vocabulary == 'DCAT-AP / DCTERMS'

    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    slot = generation.profile_draft['slots']['license']
    assert slot['slot_uri'] == 'dcterms:license'
    assert slot['annotations']['term_kind']['value'] == 'profile'
    assert 'R1' in slot['annotations']['source_requirement_ids']['value']
    assert 'ev-R1' in slot['annotations']['source_evidence_ids']['value']


def test_create_extension_becomes_cx_slot():
    change_set = changes_for([make_requirement('R1', action='create_extension', terms=['cx:hasAASSubmodel'])])
    change = change_set.changes[0]
    assert change.change_type == 'create_extension_property'
    assert change.term_uri == 'https://w3id.org/cx#hasAASSubmodel'

    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    slot = generation.profile_draft['slots']['hasAASSubmodel']
    assert slot['annotations']['term_kind']['value'] == 'extension'


def test_distribution_requirement_creates_distribution_profile_not_dataset():
    change_set = changes_for([make_requirement('R1', terms=['dcat:mediaType'], resource='Distribution')])
    assert change_set.changes[0].target_class == 'dcat:Distribution'

    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    classes = generation.profile_draft['classes']
    assert 'ConstructionDistributionProfile' in classes
    assert 'ConstructionDatasetProfile' not in classes
    assert classes['ConstructionDistributionProfile']['is_a'] == 'DcatDistribution'
    assert classes['ConstructionDistributionProfile']['annotations']['profile_of']['value'] == 'dcat:Distribution'


def test_mandatory_obligation_creates_required_slot_and_shacl_violation():
    change_set = changes_for([make_requirement('R1', obligation='mandatory')])
    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert generation.profile_draft['slots']['license'].get('required') is True
    assert 'sh:minCount 1' in generation.shacl
    assert 'sh:severity sh:Violation' in generation.shacl


def test_recommended_obligation_creates_optional_slot_and_shacl_warning():
    change_set = changes_for([make_requirement('R1', obligation='recommended')])
    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert 'required' not in generation.profile_draft['slots']['license']
    assert 'sh:minCount' not in generation.shacl
    assert 'sh:severity sh:Warning' in generation.shacl


def test_optional_obligation_maps_to_shacl_info():
    change_set = changes_for([make_requirement('R1', obligation='optional')])
    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert 'sh:severity sh:Info' in generation.shacl


def test_unknown_term_produces_warning_and_needs_review_change():
    change_set = changes_for([make_requirement('R1', terms=['foo:bogusTerm'])])
    change = change_set.changes[0]
    assert change.review_status == 'needs_review'
    assert any('not in the local vocabulary catalogue' in warning for warning in change.warnings)
    # needs_review changes are excluded from generation until resolved/accepted.
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert generation.profile_draft['slots'] == {}
    assert any('needs_review' in note for note in generation.validation_notes)


def test_extension_without_cx_prefix_is_needs_review():
    change_set = changes_for([make_requirement('R1', action='create_extension', terms=['dcterms:license'])])
    change = change_set.changes[0]
    assert change.review_status == 'needs_review'
    assert any('prefix' in warning for warning in change.warnings)


def test_domain_mismatch_is_needs_review():
    change_set = changes_for([make_requirement('R1', terms=['dcat:mediaType'], resource='Dataset')])
    change = change_set.changes[0]
    assert change.review_status == 'needs_review'
    assert any('domain' in warning for warning in change.warnings)


def test_duplicate_requirements_do_not_create_duplicate_slots():
    change_set = changes_for(
        [
            make_requirement('R1', terms=['dcterms:license'], obligation='recommended'),
            make_requirement('R2', terms=['dcterms:license'], obligation='mandatory'),
        ]
    )
    assert len(change_set.changes) == 1
    change = change_set.changes[0]
    assert set(change.source_requirement_ids) == {'R1', 'R2'}
    assert change.obligation_level == 'mandatory'  # strongest obligation wins

    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert list(generation.profile_draft['slots'].keys()) == ['license']


def test_accepted_changes_take_precedence_over_candidates():
    change_set = changes_for(
        [
            make_requirement('R1', terms=['dcterms:license']),
            make_requirement('R2', terms=['dcat:keyword'], value_kind='literal'),
        ]
    )
    for change in change_set.changes:
        change.review_status = 'rejected' if change.slot_name == 'keyword' else 'accepted'

    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert list(generation.profile_draft['slots'].keys()) == ['license']
    assert any('rejected' in note for note in generation.validation_notes)


def test_accepted_only_without_accepted_changes_returns_empty_draft():
    change_set = changes_for([make_requirement('R1', terms=['dcterms:license'])])

    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set, accepted_only=True))

    assert generation.profile_draft['classes'] == {}
    assert generation.profile_draft['slots'] == {}
    assert generation.shacl == ''
    assert any('no profile changes are accepted' in note for note in generation.validation_notes)


def test_unreviewed_candidate_changes_are_excluded_from_accepted_only_generation():
    change_set = changes_for(
        [
            make_requirement('R1', terms=['dcterms:license']),
            make_requirement('R2', terms=['dcat:keyword'], value_kind='literal'),
        ]
    )
    for change in change_set.changes:
        if change.slot_name == 'license':
            change.review_status = 'accepted'

    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set, accepted_only=True))

    assert list(generation.profile_draft['slots'].keys()) == ['license']
    assert 'keyword' not in generation.profile_draft['slots']
    assert any('unreviewed candidate' in note for note in generation.validation_notes)


def test_license_is_not_multivalued_by_default_even_for_uri_values():
    change_set = changes_for([make_requirement('R1', terms=['dcterms:license'], value_kind='uri')])

    assert change_set.changes[0].multivalued is False


def test_known_multivalued_terms_use_curated_defaults():
    change_set = changes_for(
        [
            make_requirement('R1', terms=['dcat:keyword'], value_kind='literal'),
            make_requirement('R2', action='create_extension', terms=['cx:hasAASSubmodel'], value_kind='uri'),
        ]
    )

    multivalued_by_slot = {change.slot_name: change.multivalued for change in change_set.changes}
    assert multivalued_by_slot['keyword'] is True
    assert multivalued_by_slot['hasAASSubmodel'] is True


def test_generated_shacl_is_valid_turtle_with_provenance():
    change_set = changes_for(
        [
            make_requirement('R1', obligation='mandatory'),
            make_requirement('R2', action='create_extension', terms=['cx:hasAASSubmodel']),
        ]
    )
    accept_candidate_changes(change_set)
    shacl = generate_shacl_from_changes(change_set)
    graph = Graph()
    graph.parse(data=shacl, format='turtle')
    assert len(graph) > 0
    assert 'R1' in shacl  # requirement provenance in sh:description


def test_rq2_package_contains_provenance_mapping_and_artifacts():
    change_set = changes_for(
        [
            make_requirement('R1', terms=['dcterms:license'], obligation='mandatory'),
            make_requirement('R2', action='create_extension', terms=['cx:hasAASSubmodel']),
        ]
    )
    accept_candidate_changes(change_set)
    package = build_rq2_package(RQ2ExportRequest(profile_change_set=change_set, source_requirement_set_id='rs-001'))

    assert package.schema_version == 'rq2-profile-generation-package-v1'
    assert package.base_profile == 'DCAT-AP'
    assert package.source_requirement_set_id == 'rs-001'
    assert package.profile_draft_linkml['classes']
    assert 'sh:NodeShape' in package.shacl
    mapping = {(entry.requirement_id, entry.profile_element) for entry in package.provenance_mapping}
    assert ('R1', 'dcterms:license') in mapping
    assert ('R2', 'cx:hasAASSubmodel') in mapping
    for entry in package.provenance_mapping:
        assert entry.evidence_unit_ids  # evidence ids preserved end-to-end


def test_usage_note_changes_annotate_without_slots():
    change_set = changes_for([make_requirement('R1', action='add_usage_note', terms=['dcterms:license'])])
    assert change_set.changes[0].change_type == 'add_usage_note'
    accept_candidate_changes(change_set)
    generation = generate_profile_draft(GenerateProfileDraftRequest(profile_change_set=change_set))
    assert generation.profile_draft['slots'] == {}
    klass = generation.profile_draft['classes']['ConstructionDatasetProfile']
    assert 'R1' in klass['annotations']['generated_from_requirements']['value']
