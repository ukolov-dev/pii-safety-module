from fastapi.testclient import TestClient

from app.main import app


def test_mask_retry_and_unmask_roundtrip() -> None:
    source = "Клиент: Иван Петров, телефон +7 999 123-45-67, email ivan@example.com"
    with TestClient(app) as client:
        first = client.post("/process", json={"payload": source, "payload_id": "case-1"})
        assert first.status_code == 200
        masked = first.json()["result"]
        assert "ivan@example.com" not in masked
        assert "+7 999 123-45-67" not in masked

        retry = client.post("/process", json={"payload": source, "payload_id": "case-1"})
        assert retry.status_code == 200
        assert retry.json()["result"] == masked

        second = client.post("/process", json={"payload": masked, "payload_id": "case-1"})
        assert second.status_code == 200
        assert second.json()["result"] == source


def test_contract_rejects_extra_fields() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/process",
            json={"payload": "text", "payload_id": "case-2", "unexpected": True},
        )
        assert response.status_code == 422


def test_process_api_key_can_be_enforced(monkeypatch) -> None:
    from app.main import settings

    monkeypatch.setattr(settings, "process_api_key", "test-secret-at-least-16")
    with TestClient(app) as client:
        denied = client.post(
            "/process",
            json={"payload": "text", "payload_id": "protected-1"},
        )
        allowed = client.post(
            "/process",
            json={"payload": "text", "payload_id": "protected-1"},
            headers={"X-API-Key": "test-secret-at-least-16"},
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_existing_payload_id_rejects_unrelated_payload() -> None:
    with TestClient(app) as client:
        first = client.post(
            "/process",
            json={"payload": "служебный текст", "payload_id": "shared-case"},
        )
        assert first.status_code == 200

        collision = client.post(
            "/process",
            json={
                "payload": "Клиент: Иван Петров, email ivan@example.com",
                "payload_id": "shared-case",
            },
        )
        assert collision.status_code == 409


def test_partial_token_probe_is_rejected() -> None:
    source = "Клиент: Иван Петров, email ivan@example.com"
    with TestClient(app) as client:
        masked = client.post("/process", json={"payload": source, "payload_id": "probe-case"})
        assert masked.status_code == 200

        probe = client.post(
            "/process",
            json={"payload": "{{EMAIL_1}}", "payload_id": "probe-case"},
        )
        assert probe.status_code == 409


def test_readiness_checks_storage_and_metrics_do_not_expose_request_data() -> None:
    with TestClient(app) as client:
        ready = client.get("/health/ready")
        metrics = client.get("/metrics")

        assert ready.status_code == 200
        assert metrics.status_code == 200
        assert "pii_api_request_duration_seconds" in metrics.text
        assert "pii_api_requests_in_flight" in metrics.text
        assert "pii_api_processed_characters_total" in metrics.text
        assert "payload_id" not in metrics.text
