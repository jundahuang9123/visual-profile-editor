from __future__ import annotations

import io
import json
import os
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
    {
        'id': 'construct-dcat-minimal-profile',
        'title': 'Minimal Construct-DCAT Profile',
        'description': 'Start with the minimal DCAT v3 semantic-anchor extension.',
    },
]


WORKSPACE_ENV = 'VPE_PROFILE_WORKSPACE'
WORKSPACE_DIRNAME = '.vpe-workspace'
WORKSPACE_CONFIG = 'workspace.json'
PROFILE_FILENAME = 'profile.yaml'


def default_profile_seed_path(base_dir: Path) -> Path:
    primary = base_dir / 'schemas' / 'profile.yaml'
    return primary if primary.exists() else base_dir / 'schemas' / 'construct_dcat.yaml'


def workspace_config_path(base_dir: Path) -> Path:
    return base_dir / WORKSPACE_DIRNAME / WORKSPACE_CONFIG


def default_workspace_dir(base_dir: Path) -> Path:
    env_dir = os.environ.get(WORKSPACE_ENV)
    if env_dir:
        return resolve_workspace_dir(base_dir, env_dir)
    return (base_dir / WORKSPACE_DIRNAME / 'profiles').resolve()


def configured_workspace_dir(base_dir: Path) -> Path:
    config_path = workspace_config_path(base_dir)
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding='utf-8'))
            directory = data.get('directory')
            if isinstance(directory, str) and directory.strip():
                return resolve_workspace_dir(base_dir, directory)
        except (OSError, json.JSONDecodeError):
            pass
    return default_workspace_dir(base_dir)


def profile_schema_path(base_dir: Path) -> Path:
    return ensure_workspace_profile(base_dir)


def ensure_workspace_profile(base_dir: Path) -> Path:
    workspace_dir = configured_workspace_dir(base_dir)
    validate_workspace_dir(base_dir, workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    profile_path = workspace_dir / PROFILE_FILENAME
    if not profile_path.exists():
        profile_path.write_text(default_profile_seed_path(base_dir).read_text(encoding='utf-8'), encoding='utf-8')
    return profile_path


def profile_workspace_info(base_dir: Path) -> dict[str, str]:
    profile_path = profile_schema_path(base_dir)
    return {
        'directory': str(profile_path.parent),
        'schema_path': str(profile_path),
        'default_directory': str(default_workspace_dir(base_dir)),
        'seed_path': str(default_profile_seed_path(base_dir)),
    }


def set_profile_workspace(base_dir: Path, directory: str) -> tuple[dict[str, str], dict[str, Any]]:
    if not directory.strip():
        raise ValueError('Workspace directory is required.')

    current_schema = load_profile(base_dir)
    workspace_dir = resolve_workspace_dir(base_dir, directory)
    validate_workspace_dir(base_dir, workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    config_path = workspace_config_path(base_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({'directory': str(workspace_dir)}, indent=2), encoding='utf-8')

    profile_path = workspace_dir / PROFILE_FILENAME
    if profile_path.exists():
        schema = load_schema(profile_path)
    else:
        schema = save_schema(profile_path, current_schema)
    return profile_workspace_info(base_dir), schema


def resolve_workspace_dir(base_dir: Path, directory: str) -> Path:
    expanded = Path(directory).expanduser()
    if not expanded.is_absolute():
        expanded = base_dir / expanded
    return expanded.resolve()


def validate_workspace_dir(base_dir: Path, workspace_dir: Path) -> None:
    if workspace_dir.exists() and not workspace_dir.is_dir():
        raise ValueError(f'Workspace path is not a directory: {workspace_dir}')

    protected_dirs = [
        (base_dir / 'schemas').resolve(),
        (base_dir / 'profiles' / 'templates').resolve(),
        (base_dir / '.git').resolve(),
    ]
    for protected_dir in protected_dirs:
        if workspace_dir == protected_dir or workspace_dir.is_relative_to(protected_dir):
            raise ValueError(f'Choose a workspace outside the versioned seed directory: {protected_dir}')


def load_profile(base_dir: Path) -> dict[str, Any]:
    return load_schema(profile_schema_path(base_dir))


def save_profile(base_dir: Path, schema: dict[str, Any] | str) -> dict[str, Any]:
    return save_schema(profile_schema_path(base_dir), schema)


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
