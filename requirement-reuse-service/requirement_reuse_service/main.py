from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalysisRequest, ConstraintGenerationRequest, RecommendationRequest
from .service import analyze_payload, extract_requirements, generate_constraints, recommend_reuse

app = FastAPI(
    title='Requirement Extraction & Reuse Recommendation Service',
    version='0.1.0',
    description='Rule-based MVP service for semi-automated, reuse-first semantic profile engineering.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/analyze-artifacts')
def analyze_artifacts(payload: AnalysisRequest):
    return analyze_payload(payload)


@app.post('/analyze')
def analyze(payload: AnalysisRequest):
    return analyze_payload(payload)


@app.post('/extract-requirements')
def extract_requirement_candidates(payload: AnalysisRequest):
    return extract_requirements(payload)


@app.post('/recommend-reuse')
def recommend_reuse_candidates(payload: RecommendationRequest):
    return recommend_reuse(payload)


@app.post('/generate-shacl')
def generate_shacl(payload: ConstraintGenerationRequest):
    return generate_constraints(payload)
