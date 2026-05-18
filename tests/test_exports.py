import io
import zipfile
from pathlib import Path

from general_ontology_editor import generate_json_schema, generate_rdf, generate_shacl

from app.profile_export import create_profile_package


SCHEMA_PATH = Path('schemas/profile.yaml')


def test_shacl_export_contains_construct_dcat_terms():
    shacl = generate_shacl(SCHEMA_PATH)
    assert 'sh:NodeShape' in shacl
    assert 'cx:ConstructionDataset' in shacl or 'cx:' in shacl


def test_rdf_export_contains_profile_terms():
    rdf = generate_rdf(SCHEMA_PATH)
    assert 'prof:Profile' in rdf
    assert 'cx:ConstructionDataset' in rdf or 'cx:' in rdf


def test_json_schema_export():
    json_schema = generate_json_schema(SCHEMA_PATH)
    assert 'ConstructionDatasetProfile' in json_schema


def test_profile_package_export():
    root = Path(__file__).resolve().parents[1]
    package_bytes = create_profile_package(root)
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
        names = set(archive.namelist())
    assert 'construct-dcat-profile/profile.yaml' in names
    assert 'construct-dcat-profile/profile.shacl.ttl' in names
    assert 'construct-dcat-profile/profile.schema.json' in names
    assert 'construct-dcat-profile/profile.ttl' in names
    assert 'construct-dcat-profile/examples/example-dataset-valid.jsonld' in names
