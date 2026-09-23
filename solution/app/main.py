"""FastAPI entry point for the first working version."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from app.api.models import HealthResponse, ProcessRequest, ProcessResponse
from app.service import ProcessService
from app.settings import settings
from app.vault import create_vault


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    vault = create_vault(
        redis_url=settings.redis_url,
        mapping_encryption_key=settings.mapping_encryption_key,
    )
    app.state.vault = vault
    app.state.process_service = ProcessService(vault, ttl_seconds=settings.mapping_ttl_seconds)
    try:
        yield
    finally:
        await vault.close()


app = FastAPI(
    title="PII Safety Module",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
async def health_ready(request: Request) -> HealthResponse:
    if not hasattr(request.app.state, "process_service"):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready")
    return HealthResponse(status="ok")


@app.post("/process", response_model=ProcessResponse)
async def process(body: ProcessRequest, request: Request) -> ProcessResponse:
    if len(body.payload) > settings.max_payload_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload is too large",
        )
    service: ProcessService = request.app.state.process_service
    result = await service.process(payload=body.payload, payload_id=body.payload_id)
    return ProcessResponse(result=result)

