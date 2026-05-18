from pathlib import Path

from general_ontology_editor import load_schema


def test_construct_dcat_schema_loads():
    schema = load_schema(Path('schemas/profile.yaml'))
    assert schema['name'] == 'construct_dcat_profile'
    assert 'ConstructionDatasetProfile' in schema['classes']
    assert 'semanticAnchor' in schema['slots']
