from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm import LLMConfig
from .models import (
    AnalysisRequest,
    ConstraintGenerationRequest,
    RecommendationRequest,
    RequirementSetLoadRequest,
    RequirementSetSaveRequest,
)
from .registry import list_requirement_sets, load_requirement_set, save_requirement_set
from .service import analyze_payload, export_rq1_dataset, extract_requirements, generate_constraints, recommend_reuse

app = FastAPI(
    title='Requirement Extraction & Reuse Recommendation Service',
    version='0.2.0',
    description=(
        'Semi-automated, reuse-first requirement extraction for DCAT profile engineering. '
        'Supports a rule-based baseline strategy, an LLM-assisted strategy with verbatim '
        'evidence verification, and a hybrid of both.'
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
