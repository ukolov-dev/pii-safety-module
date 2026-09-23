from __future__ import annotations

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture
def configured_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config = tmp_path / "consumers.yaml"
    config.write_text("""default_consumer: portal
consumers:
  portal:
    public_access: true
  alpha:
    api_key_env: TEST_ALPHA_KEY
    mask_types: [EMAIL]
  beta:
    api_key_env: TEST_BETA_KEY
    demask_enabled: false
  disabled:
    enabled: false
""")
    monkeypatch.setenv("TEST_ALPHA_KEY", "a" * 32)
    monkeypatch.setenv("TEST_BETA_KEY", "b" * 32)
    monkeypatch.setattr(settings, "consumers_config", str(config))
    with TestClient(app) as client:
        yield client


def test_policy_auth_isolation_and_no_demasking(configured_client):
    client = configured_client
    source = "Мой email secret-person@example.com, телефон +7 999 123-45-67"
    body = {"payload": source, "payload_id": "same-id"}
    for name in ["unknown", "disabled"]:
        assert (
            client.post("/process", json=body, headers={"X-Consumer-ID": name}).status_code == 403
        )
    assert client.post("/process", json=body, headers={"X-Consumer-ID": "alpha"}).status_code == 401
    alpha = {"X-Consumer-ID": "alpha", "X-API-Key": "a" * 32}
    beta = {"X-Consumer-ID": "beta", "X-API-Key": "b" * 32}
    masked = client.post("/process", json=body, headers=alpha).json()["result"]
    assert "secret-person@example.com" not in masked
    assert "+7 999 123-45-67" in masked
    # A different consumer cannot recover the first consumer's PII with the same id.
    cross = client.post("/process", json={**body, "payload": masked}, headers=beta)
    assert "secret-person@example.com" not in cross.json()["result"]
    assert (
        client.post("/process", json={**body, "payload": masked}, headers=alpha).json()["result"]
        == source
    )
    beta_mask = client.post("/process", json={**body, "payload_id": "beta"}, headers=beta).json()[
        "result"
    ]
    assert (
        client.post(
            "/process", json={"payload": beta_mask, "payload_id": "beta"}, headers=beta
        ).status_code
        == 403
    )


def test_metrics_and_logs_do_not_contain_input(configured_client, caplog):
    with caplog.at_level(logging.INFO, logger="pii.audit"):
        result = configured_client.post(
            "/process",
            json={
                "payload": "Мой email private-canary@example.com",
                "payload_id": "private-correlation",
            },
        )
    assert result.status_code == 200
    assert result.headers["x-request-id"]
    text = configured_client.get("/metrics").text
    assert "pii_api_request_duration_seconds_bucket" in text
    assert 'pii_api_processed_tokens_total{tokenizer="whitespace"}' in text
    assert '"event": "identified"' in caplog.text
    for secret in ["private-canary@example.com", "private-correlation"]:
        assert secret not in text + caplog.text


def test_storage_failure_is_sanitized(configured_client, monkeypatch):
    from redis.exceptions import ConnectionError

    async def broken(_):
        raise ConnectionError("sensitive-backend-address")

    monkeypatch.setattr(app.state.vault, "get", broken)
    assert configured_client.get("/health/ready").status_code == 503
    response = configured_client.post("/process", json={"payload": "hello", "payload_id": "x"})
    assert response.status_code == 503
    assert "sensitive-backend-address" not in response.text
