"""Optional Redis-backed encrypted vault."""

from __future__ import annotations

import base64
import json
import math
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from .crypto import MappingCipher, load_mapping_key
from .models import CreateResult, VaultRecord


class RedisVault:
    """Shared vault using Redis SET NX EX for atomic create-if-absent."""

    def __init__(
        self,
        redis_url: str,
        *,
        encryption_key: bytes | None = None,
        key_prefix: str = "pii:vault:",
        redis_client: Any | None = None,
    ) -> None:
        self._cipher = MappingCipher(encryption_key or load_mapping_key())
        self._key_prefix = key_prefix
        if redis_client is None:
            try:
                from redis.asyncio import Redis
            except ImportError as exc:  # pragma: no cover - deployment setup
                raise RuntimeError(
                    "redis package is required when REDIS_URL is configured"
                ) from exc
            redis_client = Redis.from_url(
                redis_url, decode_responses=False, socket_connect_timeout=2, socket_timeout=2
            )
        self._redis = redis_client

    def _key(self, payload_id: str) -> str:
        # Quoting prevents separators in an external id from changing key shape.
        return self._key_prefix + quote(payload_id, safe="")

    def _encode(self, record: VaultRecord) -> bytes:
        document = {
            "v": 1,
            "payload_id": record.payload_id,
            "request_hash": record.request_hash,
            "masked_result": record.masked_result,
            "mapping": base64.b64encode(
                self._cipher.encrypt(record.payload_id, record.mapping)
            ).decode("ascii"),
            "state": record.state,
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
        }
        return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )

    def _decode(self, raw: bytes | str) -> VaultRecord:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        document = json.loads(raw)
        payload_id = document["payload_id"]
        return VaultRecord(
            payload_id=payload_id,
            request_hash=document["request_hash"],
            masked_result=document["masked_result"],
            mapping=self._cipher.decrypt(
                payload_id, base64.b64decode(document["mapping"], validate=True)
            ),
            state=document["state"],
            created_at=datetime.fromisoformat(document["created_at"]),
            expires_at=datetime.fromisoformat(document["expires_at"]),
        )

    async def create_if_absent(self, record: VaultRecord) -> CreateResult:
        now = datetime.now(UTC)
        ttl_seconds = math.ceil((record.expires_at - now).total_seconds())
        if ttl_seconds <= 0:
            raise ValueError("cannot store an already expired record")
        key = self._key(record.payload_id)
        created = await self._redis.set(
            key, self._encode(record), ex=ttl_seconds, nx=True
        )
        if created:
            return CreateResult(created=True, record=record)

        # The winner could expire between SET NX and GET. Retry the atomic
        # operation once so callers never receive a result without a record.
        existing = await self._redis.get(key)
        if existing is not None:
            return CreateResult(created=False, record=self._decode(existing))
        created = await self._redis.set(
            key, self._encode(record), ex=ttl_seconds, nx=True
        )
        if created:
            return CreateResult(created=True, record=record)
        existing = await self._redis.get(key)
        if existing is None:
            raise RuntimeError("Redis create race did not yield a stored record")
        return CreateResult(created=False, record=self._decode(existing))

    async def get(self, payload_id: str) -> VaultRecord | None:
        raw = await self._redis.get(self._key(payload_id))
        return None if raw is None else self._decode(raw)

    async def cleanup_expired(self) -> int:
        # Redis removes EX keys itself; do not SCAN production keyspace merely
        # to report work already performed by the server.
        return 0

    async def close(self) -> None:
        await self._redis.aclose()
