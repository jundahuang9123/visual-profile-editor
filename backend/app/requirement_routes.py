from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse


ALLOWED_OPERATIONS = {'analyze', 'analyze-artifacts', 'extract-requirements', 'recommend-reuse', 'generate-shacl'}


def requirement_router(service_url: str) -> APIRouter:
    router = APIRouter(prefix='/api/requirements', tags=['requirements'])
    base_url = service_url.rstrip('/')

    @router.get('/health')
    async def requirement_service_health() -> JSONResponse:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f'{base_url}/health')
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f'Requirement reuse service unavailable: {exc}') from exc
        return JSONResponse(response.json())

    @router.post('/{operation}')
    async def forward_requirement_operation(operation: str, payload: dict[str, Any]) -> JSONResponse:
        if operation not in ALLOWED_OPERATIONS:
            raise HTTPException(status_code=404, detail=f'Unknown requirement operation: {operation}')
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f'{base_url}/{operation}', json=payload)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f'Requirement reuse service unavailable: {exc}') from exc

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return JSONResponse(response.json())

    return router
