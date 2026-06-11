from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm import LLMConfig
from .models import (
    AnalysisRequest,
    ConstraintGenerationRequest,
    GenerateProfileChangesRequest,
    GenerateProfileDraftRequest,
    RecommendationRequest,
    RequirementSetLoadRequest,
    RequirementSetSaveRequest,
    RQ2ExportRequest,
)
from .profile_generation import (
    build_rq2_package,
    generate_profile_changes,
    generate_profile_draft,
    generate_shacl_from_changes,
    select_changes,
)
from .registry import list_requirement_sets, load_requirement_set, save_requirement_set
from .service import analyze_payload, export_rq1_dataset, extract_requirements, generate_constraints, recommend_reuse

app = FastAPI(
    title='Requirement Extraction & Reuse Recommendation Service',
    version='0.3.0',
    description=(
        'RQ1: semi-automated, reuse-first requirement extraction for DCAT/DCAT-AP profile '
        'engineering (rule-based baseline, LLM-assisted with verbatim evidence verification, '
        'and hybrid strategies). RQ2: reviewable profile change sets, LinkML profile drafts, '
        'and SHACL generated from approved requirements only.'
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health() -> dict[str, object]:
    config = LLMConfig.from_env()
    try:
        model = config.resolved_model()
    except ValueError:
        model = None
    return {
        'status': 'ok',
        'llm': {'provider': config.provider, 'model': model, 'base_url': config.base_url},
    }


@app.post('/analyze-artifacts')
def analyze_artifacts(payload: AnalysisRequest):
    return analyze_payload(payload)


@app.post('/analyze')
def analyze(payload: AnalysisRequest):
    return analyze_payload(payload)


@app.post('/extract-requirements')
def extract_requirement_candidates(payload: AnalysisRequest):
    return extract_requirements(payload)


@app.post('/export-rq1-dataset')
def export_rq1_requirement_dataset(payload: AnalysisRequest):
    return export_rq1_dataset(payload)


@app.post('/recommend-reuse')
def recommend_reuse_candidates(payload: RecommendationRequest):
    return recommend_reuse(payload)


@app.post('/generate-shacl')
def generate_shacl(payload: ConstraintGenerationRequest):
    return generate_constraints(payload)


@app.post('/generate-profile-changes')
def profile_changes(payload: GenerateProfileChangesRequest):
    """RQ2 step 1: convert approved requirements into a reviewable ProfileChangeSet."""
    return generate_profile_changes(payload)


@app.post('/generate-profile-draft')
def profile_draft(payload: GenerateProfileDraftRequest):
    """RQ2 step 2: LinkML profile draft + SHACL from a reviewed ProfileChangeSet."""
    return generate_profile_draft(payload)


@app.post('/generate-shacl-from-profile-changes')
def shacl_from_changes(payload: GenerateProfileDraftRequest):
    included, notes = select_changes(payload.profile_change_set, payload.accepted_only)
    return {
        'shacl': generate_shacl_from_changes(payload.profile_change_set, included) if included else '',
        'validation_notes': notes,
    }


@app.post('/export-rq2-package')
def export_rq2(payload: RQ2ExportRequest):
    """RQ2 export: change set + LinkML draft + SHACL + provenance mapping."""
    return build_rq2_package(payload)


@app.post('/save-requirement-set')
def save_set(payload: RequirementSetSaveRequest):
    return save_requirement_set(payload)


@app.post('/list-requirement-sets')
def list_sets():
    return {'requirement_sets': [info.model_dump() for info in list_requirement_sets()]}


@app.post('/load-requirement-set')
def load_set(payload: RequirementSetLoadRequest):
    requirement_set = load_requirement_set(payload.id)
    if requirement_set is None:
        raise HTTPException(status_code=404, detail=f'Requirement set not found: {payload.id}')
    return requirement_set
