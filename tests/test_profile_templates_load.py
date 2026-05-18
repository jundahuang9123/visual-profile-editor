from pathlib import Path

from app.profile_export import TEMPLATES, load_template


def test_profile_templates_load():
    root = Path(__file__).resolve().parents[1]
    template_ids = {template['id'] for template in TEMPLATES}
    assert {'empty-profile', 'dcat-profile', 'dcat-ap-profile', 'construct-dcat-profile'} <= template_ids
    for template_id in template_ids:
        schema = load_template(root, template_id)
        assert schema['classes'] is not None
        assert schema['slots'] is not None
