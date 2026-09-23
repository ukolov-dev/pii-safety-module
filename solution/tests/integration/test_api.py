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

