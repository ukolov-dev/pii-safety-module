"""Application service implementing mask/retry/unmask state transitions."""

from __future__ import annotations

import hashlib

from app.detection import detect
from app.masking import mask_text, unmask_text
from app.vault import Vault, VaultRecord


def payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PayloadConflictError(ValueError):
    """The payload does not match a valid transition for an existing identifier."""


class ProcessService:
    def __init__(self, vault: Vault, *, ttl_seconds: int) -> None:
        self._vault = vault
        self._ttl_seconds = ttl_seconds

    async def process(self, *, payload: str, payload_id: str) -> str:
        digest = payload_hash(payload)
        existing = await self._vault.get(payload_id)

        if existing is not None:
            if digest == existing.request_hash:
                return existing.masked_result
            if digest == payload_hash(existing.masked_result):
                return unmask_text(payload, existing.mapping)
            raise PayloadConflictError(
                "payload_id already exists and payload is neither the source nor its mask"
            )

        entities = detect(payload)
        masked = mask_text(payload, entities)
        candidate = VaultRecord.new(
            payload_id=payload_id,
            request_hash=digest,
            masked_result=masked.text,
            mapping=masked.mapping,
            state="masked",
            ttl_seconds=self._ttl_seconds,
        )
        result = await self._vault.create_if_absent(candidate)
        if result.created:
            return result.record.masked_result

        # Another replica won the create race. Preserve idempotency when it
        # stored the same source; otherwise treat this request as an output to
        # be restored using the winning mapping.
        if digest == result.record.request_hash:
            return result.record.masked_result
        if digest == payload_hash(result.record.masked_result):
            return unmask_text(payload, result.record.mapping)
        raise PayloadConflictError(
            "payload_id was claimed concurrently by a different payload"
        )
