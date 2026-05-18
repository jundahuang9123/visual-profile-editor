from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

from general_ontology_editor import generate_json_schema, generate_linkml, generate_rdf, generate_shacl, load_schema, save_schema

TEMPLATES = [
    {
        'id': 'empty-profile',
        'title': 'Empty Semantic Profile',
        'description': 'Start with an empty profile model.',
    },
    {
        'id': 'dcat-profile',
        'title': 'DCAT Profile',
        'description': 'Start from core DCAT classes and properties.',
    },
    {
        'id': 'dcat-ap-profile',
        'title': 'DCAT-AP Profile',
        'description': 'Start from a DCAT-AP-oriented profile structure.',
    },
    {
        'id': 'construct-dcat-profile',
        'title': 'Construct-DCAT Starter Profile',
        'description': 'Start with DCAT/DCAT-AP plus construction-domain semantic anchors.',
    },
]


def profile_schema_path(base_dir: Path) -> Path:
    primary = base_dir / 'schemas' / 'profile.yaml'
    return primary if primary.exists() else base_dir / 'schemas' / 'construct_dcat.yaml'


def load_profile(base_dir: Path) -> dict[str, Any]:
    return load_schema(profile_schema_path(base_dir))


def save_profile(base_dir: Path, schema: dict[str, Any] | str) -> dict[str, Any]:
    return save_schema(base_dir / 'schemas' / 'profile.yaml', schema)


def template_path(base_dir: Path, template_id: str) -> Path:
    allowed = {item['id'] for item in TEMPLATES}
    if template_id not in allowed:
        raise KeyError(template_id)
    return base_dir / 'profiles' / 'templates' / f'{template_id}.yaml'


def load_template(base_dir: Path, template_id: str) -> dict[str, Any]:
    return load_schema(template_path(base_dir, template_id))


def apply_template(base_dir: Path, template_id: str) -> dict[str, Any]:
    schema = load_template(base_dir, template_id)
    return save_profile(base_dir, schema)


def create_profile_package(base_dir: Path) -> bytes:
    schema = load_profile(base_dir)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('construct-dcat-profile/profile.yaml', generate_linkml(schema))
        archive.writestr('construct-dcat-profile/profile.shacl.ttl', generate_shacl(schema))
        archive.writestr('construct-dcat-profile/profile.schema.json', format_json_schema(generate_json_schema(schema)))
        archive.writestr('construct-dcat-profile/profile.ttl', generate_rdf(schema))
        archive.writestr('construct-dcat-profile/README.md', package_readme(schema))

        examples_dir = base_dir / 'profiles' / 'examples'
        for example in ['example-dataset-valid.jsonld', 'example-dataset-valid.ttl']:
            example_path = examples_dir / example
            if example_path.exists():
                archive.write(example_path, f'construct-dcat-profile/examples/{example}')

    buffer.seek(0)
    return buffer.read()


def format_json_schema(text: str) -> str:
    try:
        return json.dumps(json.loads(text), indent=2)
    except json.JSONDecodeError:
        return text


def package_readme(schema: dict[str, Any]) -> str:
    title = schema.get('title') or 'Construct-DCAT Application Profile'
    description = schema.get('description') or 'A DCAT-compatible construction-domain application profile.'
    return f"""# {title}

{description}

This package contains LinkML source, SHACL validation shapes, JSON Schema, RDF/Turtle profile terms, and valid example dataset metadata.

Generated artifacts:

- `profile.yaml`
- `profile.shacl.ttl`
- `profile.schema.json`
- `profile.ttl`
- `examples/example-dataset-valid.jsonld`
- `examples/example-dataset-valid.ttl`
"""
