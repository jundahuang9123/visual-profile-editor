from copy import deepcopy
from pathlib import Path

from general_ontology_editor import load_schema

from app.profile_validation import validate_profile


def test_profile_validation_detects_unknown_prefix():
    schema = load_schema(Path('schemas/profile.yaml'))
    broken = deepcopy(schema)
    broken['slots']['semanticAnchor']['slot_uri'] = 'missing:semanticAnchor'
    result = validate_profile(broken)
    assert not result['valid']
    assert any(issue['code'] == 'UNKNOWN_PREFIX' for issue in result['errors'])


def test_profile_validation_accepts_starter_profile():
    schema = load_schema(Path('schemas/profile.yaml'))
    result = validate_profile(schema)
    assert result['valid']
