#!/usr/bin/env sh
set -eu
mkdir -p /app/generated/jsonschema /app/generated/shacl
python -m linkml.generators.jsonschemagen /app/schemas/construct_dcat.yaml > /app/generated/jsonschema/construct_dcat.schema.json
python -m linkml.generators.shaclgen /app/schemas/construct_dcat.yaml > /app/generated/shacl/construct_dcat.shacl.ttl
python - <<'PY'
from pathlib import Path
from general_ontology_editor import generate_json_schema, generate_shacl

schema_path = Path('/app/schemas/profile.yaml')
Path('/app/generated/jsonschema/profile.schema.json').write_text(generate_json_schema(schema_path), encoding='utf-8')
Path('/app/generated/shacl/profile.shacl.ttl').write_text(generate_shacl(schema_path), encoding='utf-8')
PY
