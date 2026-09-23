"""FastAPI entry point for the first working version."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response, status

from app.api.models import HealthResponse, ProcessRequest, ProcessResponse
from app.observability import (
    MetricsRegistry,
    RequestBodyLimitMiddleware,
    RequestMetricsMiddleware,
)
from app.service import PayloadConflictError, ProcessService
from app.settings import settings
from app.vault import create_vault


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    vault = create_vault(
        redis_url=settings.redis_url,
        mapping_encryption_key=settings.mapping_encryption_key,
        mapping_encryption_key_file=settings.mapping_encryption_key_file,
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
metrics = MetricsRegistry()
app.add_middleware(
    RequestBodyLimitMiddleware,
    max_bytes=settings.max_request_body_bytes,
)
app.add_middleware(RequestMetricsMiddleware, registry=metrics)


@app.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
async def health_ready(request: Request) -> HealthResponse:
    if not hasattr(request.app.state, "vault"):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready")
    try:
        ready = await request.app.state.vault.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="storage unavailable",
        ) from exc
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="storage unavailable",
        )
    return HealthResponse(status="ok")


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    return Response(content=metrics.render(), media_type="text/plain; version=0.0.4")


@app.post("/process", response_model=ProcessResponse)
async def process(
    body: ProcessRequest,
    request: Request,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ProcessResponse:
    if settings.process_api_key is not None and (
        api_key is None or not hmac.compare_digest(api_key, settings.process_api_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid API key",
        )
    if len(body.payload) > settings.max_payload_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload is too large",
        )
    metrics.add_processed_characters(len(body.payload))
    service: ProcessService = request.app.state.process_service
    try:
        result = await service.process(payload=body.payload, payload_id=body.payload_id)
    except PayloadConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ProcessResponse(result=result)
