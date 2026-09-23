"""In-memory encrypted vault for the portal MVP and tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .crypto import MappingCipher, load_mapping_key
from .models import CreateResult, VaultRecord


@dataclass(frozen=True, slots=True)
class _EncryptedRecord:
    payload_id: str
    request_hash: str
    masked_result: str
    encrypted_mapping: bytes
    state: str
    created_at: datetime
    expires_at: datetime


class InMemoryVault:
    """Process-local vault with atomic writes and lazy/eager TTL cleanup."""

    def __init__(
        self,
        *,
        encryption_key: bytes | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._cipher = MappingCipher(encryption_key or load_mapping_key())
        self._clock = clock or (lambda: datetime.now(UTC))
        self._records: dict[str, _EncryptedRecord] = {}
        self._lock = asyncio.Lock()

    def _encrypt(self, record: VaultRecord) -> _EncryptedRecord:
        return _EncryptedRecord(
            payload_id=record.payload_id,
            request_hash=record.request_hash,
            masked_result=record.masked_result,
            encrypted_mapping=self._cipher.encrypt(record.payload_id, record.mapping),
            state=record.state,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

    def _decrypt(self, record: _EncryptedRecord) -> VaultRecord:
        return VaultRecord(
            payload_id=record.payload_id,
            request_hash=record.request_hash,
            masked_result=record.masked_result,
            mapping=self._cipher.decrypt(
                record.payload_id, record.encrypted_mapping
            ),
            state=record.state,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

    def _is_expired(self, record: _EncryptedRecord) -> bool:
        return record.expires_at <= self._clock()

    async def create_if_absent(self, record: VaultRecord) -> CreateResult:
        encrypted = self._encrypt(record)
        async with self._lock:
            existing = self._records.get(record.payload_id)
            if existing is not None and self._is_expired(existing):
                del self._records[record.payload_id]
                existing = None
            if existing is not None:
                return CreateResult(created=False, record=self._decrypt(existing))
            self._records[record.payload_id] = encrypted
            return CreateResult(created=True, record=self._decrypt(encrypted))

    async def get(self, payload_id: str) -> VaultRecord | None:
        async with self._lock:
            record = self._records.get(payload_id)
            if record is None:
                return None
            if self._is_expired(record):
                del self._records[payload_id]
                return None
            return self._decrypt(record)

    async def cleanup_expired(self) -> int:
        async with self._lock:
            expired_ids = [
                payload_id
                for payload_id, record in self._records.items()
                if self._is_expired(record)
            ]
            for payload_id in expired_ids:
                del self._records[payload_id]
            return len(expired_ids)

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None
