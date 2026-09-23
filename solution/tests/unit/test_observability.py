from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.observability import MetricsRegistry, RequestBodyLimitMiddleware


def test_metrics_have_bounded_labels_and_no_request_identifiers() -> None:
    registry = MetricsRegistry()

    registry.observe("process", 200, 0.012)
    registry.observe("process", 413, 0.003)
    registry.observe("attacker-controlled-path", 500, 0.001)
    rendered = registry.render()

    assert 'operation="process",status_class="2xx"} 1' in rendered
    assert 'operation="process",status_class="4xx"} 1' in rendered
    assert 'operation="other",status_class="5xx"} 1' in rendered
    assert "payload_id" not in rendered
    assert "payload" not in rendered


def test_body_limit_rejects_before_endpoint_reads_body() -> None:
    limited_app = FastAPI()
    limited_app.add_middleware(RequestBodyLimitMiddleware, max_bytes=32)
    reached_endpoint = False

    @limited_app.post("/process")
    async def endpoint(request: Request) -> dict[str, int]:
        nonlocal reached_endpoint
        reached_endpoint = True
        return {"size": len(await request.body())}

    with TestClient(limited_app) as client:
        rejected = client.post(
            "/process",
            content=b"x" * 33,
            headers={"content-type": "application/octet-stream"},
        )

    assert rejected.status_code == 413
    assert reached_endpoint is False


def test_body_limit_allows_request_within_limit() -> None:
    limited_app = FastAPI()
    limited_app.add_middleware(RequestBodyLimitMiddleware, max_bytes=32)

    @limited_app.post("/process")
    async def endpoint(request: Request) -> dict[str, int]:
        return {"size": len(await request.body())}

    with TestClient(limited_app) as client:
        accepted = client.post(
            "/process",
            content=b"x" * 32,
            headers={"content-type": "application/octet-stream"},
        )

    assert accepted.status_code == 200
    assert accepted.json() == {"size": 32}
