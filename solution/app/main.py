"""PII API with consumer policies and privacy-preserving observability."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from redis.exceptions import RedisError

from app.api.models import HealthResponse, ProcessRequest, ProcessResponse
from app.consumers import authenticate, load_consumers
from app.observability import (
    MetricsRegistry,
    RequestBodyLimitMiddleware,
    RequestMetricsMiddleware,
)
from app.service import ProcessService
from app.settings import settings
from app.vault import create_vault

logging.basicConfig(level=logging.INFO, format="%(message)s")
_LOGGER = logging.getLogger("pii.audit")
metrics = MetricsRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    key = settings.mapping_encryption_key
    if settings.mapping_encryption_key_file:
        key = Path(settings.mapping_encryption_key_file).read_text().strip()
    app.state.consumers = load_consumers(settings.consumers_config)
    vault = create_vault(redis_url=settings.redis_url, mapping_encryption_key=key)
    app.state.vault = vault
    app.state.process_service = ProcessService(vault, ttl_seconds=settings.mapping_ttl_seconds)
    try:
        yield
    finally:
        await vault.close()


app = FastAPI(title="PII Safety Module", version="0.2.0", lifespan=lifespan)
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=settings.max_request_bytes)
app.add_middleware(RequestMetricsMiddleware, registry=metrics)


@app.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
async def health_ready(request: Request) -> HealthResponse:
    try:
        async with asyncio.timeout(2):
            # Reserved non-user key: exercise the actual storage connection.
            await request.app.state.vault.get("__readiness_probe__")
    except (RedisError, TimeoutError, OSError):
        raise HTTPException(503, "storage unavailable") from None
    return HealthResponse(status="ok")


@app.get("/metrics", include_in_schema=False)
async def get_metrics() -> Response:
    return Response(metrics.render(), media_type="text/plain; version=0.0.4")


@app.post("/process", response_model=ProcessResponse)
async def process(body: ProcessRequest, request: Request, response: Response) -> ProcessResponse:
    request_id = uuid.uuid4().hex
    response.headers["X-Request-ID"] = request_id
    name, policy = authenticate(
        request.app.state.consumers,
        request.headers.get("X-Consumer-ID"),
        request.headers.get("X-API-Key"),
    )
    if len(body.payload) > settings.max_payload_chars:
        raise HTTPException(413, "payload is too large")
    metrics.add_processed_characters(len(body.payload))
    metrics.add_processed_tokens(sum(1 for _ in re.finditer(r"\S+", body.payload)))
    service: ProcessService = request.app.state.process_service
    started = time.perf_counter()
    try:
        async with asyncio.timeout(9):
            result = await service.process(
                payload=body.payload,
                payload_id=body.payload_id,
                consumer_id=name,
                policy=policy,
                request_id=request_id,
            )
    except PermissionError:
        raise HTTPException(403, "demasking is disabled for this consumer") from None
    except (RedisError, TimeoutError, OSError):
        _LOGGER.error(json.dumps({"event": "storage_unavailable", "request_id": request_id}))
        raise HTTPException(503, "storage unavailable", headers={"Retry-After": "1"}) from None
    finally:
        _LOGGER.info(
            json.dumps(
                {
                    "event": "completed",
                    "request_id": request_id,
                    "consumer": name,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            )
        )
    return ProcessResponse(result=result)
