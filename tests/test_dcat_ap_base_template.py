"""Regression tests for the DCAT-AP 3.0 base template (slot_usage obligations).

Global slots carry only reusable property identity (slot_uri/range/default
cardinality). Per-class obligation/requiredness/cardinality/usage notes live in
each class's `slot_usage`, so the SAME reused property can be mandatory in one
class and optional/recommended in another. These tests assert that contract
directly against the template (the authoritative source), independent of
whether the editor's exporter yet consumes slot_usage.
"""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'profiles' / 'templates' / 'dcat-ap-full-profile.yaml'

PRIMITIVE_RANGES = {'string', 'integer', 'float', 'boolean', 'anyURI', 'date', 'datetime', 'uri'}


@pytest.fixture(scope='module')
def template() -> dict:
    return yaml.safe_load(TEMPLATE.read_text(encoding='utf-8'))


def mandatory_slots(template: dict, class_name: str) -> set[str]:
    usage = template['classes'][class_name].get('slot_usage', {})
    return {slot for slot, refinement in usage.items() if refinement.get('required') is True}


def obligation(template: dict, class_name: str, slot: str) -> str:
    usage = template['classes'][class_name].get('slot_usage', {}).get(slot, {})
    return usage.get('annotations', {}).get('requirement_level', {}).get('value', 'optional')


# --- per-class mandatory slots (the obligation matrix the user specified) ---


@pytest.mark.parametrize(
    'class_name, expected_mandatory',
    [
        ('DcatCatalog', {'title', 'description', 'publisher'}),
        ('DcatDataset', {'title', 'description'}),
        ('DcatDistribution', {'accessURL'}),
        ('DcatDataService', {'endpointURL', 'title'}),
        ('DcatCatalogRecord', {'modified', 'primaryTopic'}),
    ],
)
def test_class_mandatory_slots(template, class_name, expected_mandatory):
    assert mandatory_slots(template, class_name) == expected_mandatory


# --- the same reused slot has different obligations across classes ----------


def test_title_mandatory_in_some_classes_optional_in_others(template):
    # mandatory where DCAT-AP requires it ...
    for cls in ('DcatCatalog', 'DcatDataset', 'DcatDataService'):
        assert obligation(template, cls, 'title') == 'mandatory'
        assert mandatory_slots(template, cls) >= {'title'}
    # ... but NOT required on distribution / catalog record
    for cls in ('DcatDistribution', 'DcatCatalogRecord'):
        assert obligation(template, cls, 'title') == 'optional'
        assert 'title' not in mandatory_slots(template, cls)


def test_description_obligation_varies_by_class(template):
    assert obligation(template, 'DcatCatalog', 'description') == 'mandatory'
    assert obligation(template, 'DcatDataset', 'description') == 'mandatory'
    assert obligation(template, 'DcatDistribution', 'description') == 'recommended'
    assert obligation(template, 'DcatCatalogRecord', 'description') == 'optional'


def test_modified_is_optional_on_dataset_but_mandatory_on_catalog_record(template):
    assert obligation(template, 'DcatDataset', 'modified') == 'optional'
    assert 'modified' not in mandatory_slots(template, 'DcatDataset')
    assert 'modified' in mandatory_slots(template, 'DcatCatalogRecord')


def test_publisher_mandatory_on_catalog_recommended_on_dataset(template):
    assert obligation(template, 'DcatCatalog', 'publisher') == 'mandatory'
    assert obligation(template, 'DcatDataset', 'publisher') == 'recommended'


# --- global slots carry identity only (no obligation leakage) ---------------


def test_global_slots_define_identity_only(template):
    leaking = [
        name
        for name, slot in template['slots'].items()
        if 'required' in slot or slot.get('annotations', {}).get('requirement_level')
    ]
    assert leaking == [], f'global slots must not carry obligation/required: {leaking}'
    # but they must carry the reusable identity
    for name, slot in template['slots'].items():
        assert slot.get('slot_uri'), f'global slot {name} missing slot_uri'
        assert slot.get('range'), f'global slot {name} missing range'


def test_slot_usage_only_refines_member_slots(template):
    for class_name, class_def in template['classes'].items():
        members = set(class_def.get('slots', []))
        for refined in class_def.get('slot_usage', {}):
            assert refined in members, f'{class_name}.slot_usage refines non-member slot {refined}'


# --- missing DCAT-AP 3.0 terms now present ----------------------------------


def test_applicable_legislation_present_on_resource_classes(template):
    assert 'applicableLegislation' in template['slots']
    assert template['slots']['applicableLegislation']['slot_uri'] == 'dcat:applicableLegislation'
    assert 'EliLegalResource' in template['classes']  # its range class
    carriers = [c for c, d in template['classes'].items() if 'applicableLegislation' in d.get('slots', [])]
    assert {'DcatCatalog', 'DcatDataset', 'DcatDistribution', 'DcatDataService'} <= set(carriers)


def test_additional_dcat_ap_3_versioning_terms_present(template):
    for term in ('previousVersion', 'hasCurrentVersion'):
        assert term in template['slots'], f'missing DCAT-AP 3.0 term: {term}'


def test_controlled_vocabularies_are_named_where_dcat_ap_specifies_them(template):
    # named (not yet machine-enforced) controlled vocabularies on the key slots
    assert 'controlled_vocabulary' in template['classes']['DcatDataset']['slot_usage']['theme']['annotations']
    assert 'controlled_vocabulary' in template['classes']['DcatDataset']['slot_usage']['accessRights']['annotations']
    assert 'controlled_vocabulary' in template['classes']['DcatDistribution']['slot_usage']['mediaType']['annotations']


# --- honesty / status markers (do not over-claim conformance) ---------------


def test_template_declares_work_in_progress_status(template):
    assert 'work in progress' in template['title'].lower()
    assert 'conformance_status' in template.get('annotations', {})


# --- structural integrity + RQ2 base-class coverage -------------------------


def test_structural_integrity(template):
    classes, slots = template['classes'], template['slots']
    referenced = {s for c in classes.values() for s in c.get('slots', [])}
    assert referenced <= set(slots), f'undefined referenced slots: {referenced - set(slots)}'
    bad_ranges = {
        s['range'] for s in slots.values()
        if s.get('range') and s['range'] not in PRIMITIVE_RANGES and s['range'] not in classes
    }
    assert not bad_ranges, f'unresolved class ranges: {bad_ranges}'
    bad_isa = {c['is_a'] for c in classes.values() if c.get('is_a') and c['is_a'] not in classes}
    assert not bad_isa, f'unresolved is_a: {bad_isa}'


def test_rq2_base_classes_present(template):
    sys.path.insert(0, str(ROOT / 'requirement-reuse-service'))
    from requirement_reuse_service.term_registry import BASE_CLASSES

    for _, (_, linkml_name, _) in BASE_CLASSES.items():
        assert linkml_name in template['classes'], f'RQ2 base class {linkml_name} missing from template'


# --- the editor still loads/validates/exports the template ------------------


def test_editor_loads_validates_and_exports():
    pytest.importorskip('general_ontology_editor')
    from general_ontology_editor.schema_loader import load_schema
    from general_ontology_editor.validation import validate_schema
    from general_ontology_editor.exporters import generate_shacl
    from rdflib import Graph

    model = load_schema(TEMPLATE)
    assert validate_schema(model) == {'valid': True, 'errors': []}
    Graph().parse(data=generate_shacl(model), format='turtle')  # raises if invalid turtle
