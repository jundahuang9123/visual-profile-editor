from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from jsonschema import Draft202012Validator
from rdflib import Graph, Literal, Namespace, RDF, URIRef

from general_ontology_editor import create_app

from .profile_routes import profile_router

BASE_DIR = Path('/app') if Path('/app').exists() else Path(__file__).resolve().parents[2]
PROFILE_SCHEMA_PATH = BASE_DIR / 'schemas' / 'profile.yaml'
PROFILE_JSON_SCHEMA_PATH = BASE_DIR / 'generated' / 'jsonschema' / 'profile.schema.json'
DATASET_SCHEMA_PATH = BASE_DIR / 'generated' / 'jsonschema' / 'construct_dcat.schema.json'
EXAMPLE_PATH = BASE_DIR / 'examples' / 'dataset_minimal.json'

DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCTERMS = Namespace('http://purl.org/dc/terms/')
CX = Namespace('https://w3id.org/cx#')

app = create_app(
    schema_path=PROFILE_SCHEMA_PATH,
    json_schema_path=PROFILE_JSON_SCHEMA_PATH,
    frontend_dist=BASE_DIR / 'frontend-dist',
    product_title='Construct-DCAT Profile Editor',
    mode='profile',
    import_defaults={
        'id': 'https://w3id.org/construct-dcat/imported-profile',
        'name': 'imported_construct_dcat_profile',
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            'dcat': 'http://www.w3.org/ns/dcat#',
            'dcterms': 'http://purl.org/dc/terms/',
            'cx': 'https://w3id.org/cx#',
        },
        'imports': ['linkml:types'],
        'default_prefix': 'cx',
    },
    include_validation_route=False,
)
app.include_router(profile_router(BASE_DIR))


def load_dataset_json_schema() -> dict[str, Any]:
    if not DATASET_SCHEMA_PATH.exists():
        raise FileNotFoundError(f'Missing generated dataset JSON Schema: {DATASET_SCHEMA_PATH}')
    return json.loads(DATASET_SCHEMA_PATH.read_text(encoding='utf-8'))


def dataset_validator() -> Draft202012Validator:
    return Draft202012Validator(load_dataset_json_schema())


def payload_to_graph(data: dict[str, Any]) -> Graph:
    graph = Graph()
    graph.bind('dcat', DCAT)
    graph.bind('dcterms', DCTERMS)
    graph.bind('cx', CX)

    dataset_uri = URIRef(f"https://example.org/dataset/{data['identifier']}")
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
    graph.add((dataset_uri, RDF.type, CX.ConstructionDataset))
    graph.add((dataset_uri, DCTERMS.identifier, Literal(data['identifier'])))
    graph.add((dataset_uri, DCTERMS.title, Literal(data['title'])))

    if data.get('description'):
        graph.add((dataset_uri, DCTERMS.description, Literal(data['description'])))

    for keyword in data.get('keyword', []):
        graph.add((dataset_uri, DCAT.keyword, Literal(keyword)))

    if data.get('asset_kind'):
        graph.add((dataset_uri, CX.describesAssetType, Literal(data['asset_kind'])))
    if data.get('lifecycle_phase'):
        graph.add((dataset_uri, CX.hasLifecyclePhase, Literal(data['lifecycle_phase'])))
    if data.get('bim_model_ref'):
        graph.add((dataset_uri, CX.hasIFCEntity, URIRef(data['bim_model_ref'])))
    if data.get('aas_ref'):
        graph.add((dataset_uri, CX.hasAASSubmodel, URIRef(data['aas_ref'])))
    if data.get('geometry_format'):
        graph.add((dataset_uri, CX.hasRepresentationType, Literal(data['geometry_format'])))
    if data.get('contact_point'):
        graph.add((dataset_uri, DCAT.contactPoint, Literal(data['contact_point'])))

    for index, distribution in enumerate(data.get('distribution', []), start=1):
        distribution_uri = URIRef(f'{dataset_uri}/distribution/{index}')
        graph.add((distribution_uri, RDF.type, DCAT.Distribution))
        graph.add((dataset_uri, DCAT.distribution, distribution_uri))
        if distribution.get('access_url'):
            graph.add((distribution_uri, DCAT.accessURL, URIRef(distribution['access_url'])))
        if distribution.get('download_url'):
            graph.add((distribution_uri, DCAT.downloadURL, URIRef(distribution['download_url'])))
        if distribution.get('media_type'):
            graph.add((distribution_uri, DCAT.mediaType, Literal(distribution['media_type'])))
        if distribution.get('format'):
            graph.add((distribution_uri, DCTERMS.format, Literal(distribution['format'])))

    return graph


@app.get('/api/dataset/example')
def dataset_example() -> JSONResponse:
    if EXAMPLE_PATH.exists():
        return JSONResponse(json.loads(EXAMPLE_PATH.read_text(encoding='utf-8')))
    return JSONResponse({})


@app.post('/validate')
@app.post('/dataset/validate')
def validate_dataset(payload: dict[str, Any]) -> JSONResponse:
    errors = sorted(dataset_validator().iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        return JSONResponse(
            status_code=422,
            content={
                'valid': False,
                'errors': [
                    {
                        'path': '.'.join(str(part) for part in err.path),
                        'message': err.message,
                    }
                    for err in errors
                ],
            },
        )
    return JSONResponse({'valid': True, 'errors': []})


@app.post('/export/jsonld')
@app.post('/dataset/export/jsonld')
def export_dataset_jsonld(payload: dict[str, Any]) -> JSONResponse:
    errors = sorted(dataset_validator().iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        raise HTTPException(status_code=422, detail='Payload failed validation')
    return JSONResponse(json.loads(payload_to_graph(payload).serialize(format='json-ld', indent=2)))


@app.post('/export/turtle')
@app.post('/dataset/export/turtle')
def export_dataset_turtle(payload: dict[str, Any]) -> PlainTextResponse:
    errors = sorted(dataset_validator().iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        raise HTTPException(status_code=422, detail='Payload failed validation')
    return PlainTextResponse(payload_to_graph(payload).serialize(format='turtle'), media_type='text/turtle')
