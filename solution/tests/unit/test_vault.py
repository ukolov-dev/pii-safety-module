from __future__ import annotations

import asyncio
import base64
import logging
from datetime import UTC, datetime, timedelta

import pytest

from app.vault import InMemoryVault, RedisVault, VaultRecord, create_vault
from app.vault.crypto import load_mapping_key

KEY = b"v" * 32


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.closed = False

    async def set(self, key: str, value: bytes, *, ex: int, nx: bool) -> bool:
        assert ex > 0
        assert nx is True
        if key in self.values:
            return False
        self.values[key] = value
        return True

    async def get(self, key: str) -> bytes | None:
        return self.values.get(key)

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self.closed = True


def make_record(
    *,
    payload_id: str = "payload-1",
    masked_result: str = "Hello {{PERSON_1}}",
    now: datetime | None = None,
    ttl_seconds: int = 60,
) -> VaultRecord:
    return VaultRecord.new(
        payload_id=payload_id,
        request_hash="sha256:original",
        masked_result=masked_result,
        mapping={"{{PERSON_1}}": "Иван Иванов"},
        state="masked",
        ttl_seconds=ttl_seconds,
        now=now,
    )


@pytest.mark.asyncio
async def test_create_get_and_mapping_is_not_stored_as_plaintext() -> None:
    vault = InMemoryVault(encryption_key=KEY)
    record = make_record()

    result = await vault.create_if_absent(record)

    assert result.created is True
    assert dict(result.record.mapping) == {"{{PERSON_1}}": "Иван Иванов"}
    restored = await vault.get("payload-1")
    assert restored == record
    stored = vault._records["payload-1"]  # noqa: SLF001 - verify at-rest form
    assert "Иван Иванов".encode() not in stored.encrypted_mapping


@pytest.mark.asyncio
async def test_retry_returns_first_masked_result() -> None:
    vault = InMemoryVault(encryption_key=KEY)
    first = make_record(masked_result="first {{PERSON_1}}")
    retry_candidate = make_record(masked_result="different result")

    assert (await vault.create_if_absent(first)).created is True
    retry = await vault.create_if_absent(retry_candidate)

    assert retry.created is False
    assert retry.record.masked_result == "first {{PERSON_1}}"
    assert retry.record.request_hash == first.request_hash


@pytest.mark.asyncio
async def test_concurrent_create_if_absent_has_one_winner() -> None:
    vault = InMemoryVault(encryption_key=KEY)
    records = [make_record(masked_result=f"candidate-{index}") for index in range(20)]

    results = await asyncio.gather(*(vault.create_if_absent(item) for item in records))

    assert sum(result.created for result in results) == 1
    assert len({result.record.masked_result for result in results}) == 1


@pytest.mark.asyncio
async def test_ttl_cleanup_and_recreate() -> None:
    current = datetime(2026, 9, 23, tzinfo=UTC)

    def clock() -> datetime:
        return current

    vault = InMemoryVault(encryption_key=KEY, clock=clock)
    await vault.create_if_absent(make_record(now=current, ttl_seconds=5))
    current += timedelta(seconds=6)

    assert await vault.cleanup_expired() == 1
    assert await vault.get("payload-1") is None
    replacement = await vault.create_if_absent(
        make_record(now=current, masked_result="replacement")
    )
    assert replacement.created is True


def test_development_key_warning_does_not_reveal_key(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("MAPPING_ENCRYPTION_KEY", raising=False)
    with caplog.at_level(logging.WARNING):
        key = load_mapping_key()

    assert len(key) == 32
    assert "ephemeral" in caplog.text
    assert base64.b64encode(key).decode("ascii") not in caplog.text
    assert key.hex() not in caplog.text


def test_factory_defaults_to_memory_and_accepts_configured_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    encoded_key = base64.urlsafe_b64encode(KEY).decode("ascii")

    vault = create_vault(mapping_encryption_key=encoded_key)

    assert isinstance(vault, InMemoryVault)


@pytest.mark.asyncio
async def test_redis_vault_uses_atomic_create_and_encrypted_mapping() -> None:
    redis = FakeRedis()
    vault = RedisVault("redis://unused", encryption_key=KEY, redis_client=redis)
    first = make_record(masked_result="winner")

    assert (await vault.create_if_absent(first)).created is True
    retry = await vault.create_if_absent(make_record(masked_result="loser"))

    assert retry.created is False
    assert retry.record.masked_result == "winner"
    raw = next(iter(redis.values.values()))
    assert "Иван Иванов".encode() not in raw
    assert dict((await vault.get("payload-1")).mapping) == {
        "{{PERSON_1}}": "Иван Иванов"
    }
    assert await vault.ping() is True
    await vault.close()
    assert redis.closed is True
