from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from general_ontology_editor import generate_json_schema, generate_linkml, generate_rdf, generate_shacl, import_rdf_schema

from .profile_export import (
    TEMPLATES,
    apply_template,
    browse_workspace_directories,
    create_profile_package,
    load_profile,
    pick_workspace_directory,
    profile_workspace_info,
    save_profile,
    set_profile_workspace,
)
from .profile_validation import validate_profile


def profile_router(base_dir: Path) -> APIRouter:
    router = APIRouter()

    @router.get('/api/profile/model')
    def profile_model() -> JSONResponse:
        return JSONResponse(load_profile(base_dir))

    @router.get('/api/profile/workspace')
    def profile_workspace() -> JSONResponse:
        try:
            return JSONResponse(profile_workspace_info(base_dir))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get('/api/profile/workspace/browse')
    def browse_profile_workspace(directory: str | None = None) -> JSONResponse:
        try:
            return JSONResponse(browse_workspace_directories(base_dir, directory))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post('/api/profile/workspace/pick')
    def pick_profile_workspace(payload: dict[str, str] | None = None) -> JSONResponse:
        directory = payload.get('directory') if isinstance(payload, dict) else None
        try:
            return JSONResponse(pick_workspace_directory(base_dir, directory))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.put('/api/profile/workspace')
    def update_profile_workspace(payload: dict[str, str]) -> JSONResponse:
        directory = payload.get('directory')
        if not isinstance(directory, str):
            raise HTTPException(status_code=400, detail='Missing directory payload')
        try:
            workspace, schema = set_profile_workspace(base_dir, directory)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse({'workspace': workspace, 'schema': schema})

    @router.get('/api/profile/linkml')
    def profile_linkml() -> PlainTextResponse:
        return PlainTextResponse(generate_linkml(load_profile(base_dir)), media_type='application/yaml')

    @router.put('/api/profile/linkml')
    def save_profile_linkml(payload: dict[str, str]) -> JSONResponse:
        yaml_text = payload.get('yaml')
        if not isinstance(yaml_text, str) or not yaml_text.strip():
            raise HTTPException(status_code=400, detail='Missing yaml payload')
        save_profile(base_dir, yaml_text)
        return JSONResponse({'status': 'ok', **profile_workspace_info(base_dir)})

    @router.post('/api/profile/import')
    async def import_profile(file: UploadFile = File(...)) -> JSONResponse:
        content = await file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail='Uploaded file must be UTF-8 text') from exc

        defaults = {
            'id': 'https://w3id.org/construct-dcat/imported-profile',
            'name': 'imported_construct_dcat_profile',
            'title': 'Imported Construct-DCAT Profile',
            'prefixes': {
                'linkml': 'https://w3id.org/linkml/',
                'dcat': 'http://www.w3.org/ns/dcat#',
                'dcterms': 'http://purl.org/dc/terms/',
                'cx': 'https://w3id.org/cx#',
            },
            'imports': ['linkml:types'],
            'default_prefix': 'cx',
        }
        try:
            schema = import_rdf_schema(text, file.filename or 'uploaded.ttl', defaults)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(schema)

    @router.get('/api/profile/templates')
    def profile_templates() -> JSONResponse:
        return JSONResponse(TEMPLATES)

    @router.post('/api/profile/templates/{template_id}/load')
    def load_profile_template(template_id: str) -> JSONResponse:
        try:
            schema = apply_template(base_dir, template_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f'Unknown template: {template_id}') from exc
        return JSONResponse(schema)

    @router.post('/api/profile/validate')
    def validate_current_profile(payload: dict | None = None) -> JSONResponse:
        return JSONResponse(validate_profile(payload or load_profile(base_dir)))

    @router.get('/profile/export/shacl')
    def export_profile_shacl() -> PlainTextResponse:
        return PlainTextResponse(generate_shacl(load_profile(base_dir)), media_type='text/turtle')

    @router.get('/profile/export/rdf')
    def export_profile_rdf() -> PlainTextResponse:
        return PlainTextResponse(generate_rdf(load_profile(base_dir)), media_type='text/turtle')

    @router.get('/profile/export/jsonschema')
    def export_profile_json_schema() -> PlainTextResponse:
        return PlainTextResponse(generate_json_schema(load_profile(base_dir)), media_type='application/schema+json')

    @router.get('/profile/export/linkml')
    def export_profile_linkml() -> PlainTextResponse:
        return PlainTextResponse(generate_linkml(load_profile(base_dir)), media_type='application/yaml')

    @router.get('/profile/export/package')
    def export_profile_package() -> Response:
        return Response(
            create_profile_package(base_dir),
            media_type='application/zip',
            headers={'Content-Disposition': 'attachment; filename="construct-dcat-profile.zip"'},
        )

    return router
