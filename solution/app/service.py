"""Application service implementing mask/retry/unmask state transitions."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping

from app.consumers import ConsumerPolicy
from app.detection import detect
from app.masking import mask_text, unmask_text
from app.vault import Vault, VaultRecord

_LOGGER = logging.getLogger("pii.audit")


def payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ProcessService:
    def __init__(self, vault: Vault, *, ttl_seconds: int) -> None:
        self._vault = vault
        self._ttl_seconds = ttl_seconds

    async def process(
        self,
        *,
        payload: str,
        payload_id: str,
        consumer_id: str = "portal",
        policy: ConsumerPolicy | None = None,
        request_id: str = "internal",
    ) -> str:
        policy = policy or ConsumerPolicy(public_access=True, vault_ttl_seconds=self._ttl_seconds)
        # Hash a framed namespace: a consumer can never restore another consumer's mapping.
        payload_id = hashlib.sha256(
            json.dumps([consumer_id, payload_id], ensure_ascii=False).encode()
        ).hexdigest()

        def audit(stage: str, **fields: object) -> None:
            _LOGGER.info(
                json.dumps(
                    {"event": stage, "request_id": request_id, "consumer": consumer_id, **fields},
                    ensure_ascii=False,
                )
            )

        def restore(mapping: Mapping[str, str]) -> str:
            if not policy.demask_enabled:
                raise PermissionError("demasking is disabled for this consumer")
            result = unmask_text(payload, mapping)
            audit("unmask", mapping_count=len(mapping))
            return result

        audit("received")
        digest = payload_hash(payload)
        existing = await self._vault.get(payload_id)

        if existing is not None:
            if digest == existing.request_hash:
                audit("mask_retry")
                return existing.masked_result
            return restore(existing.mapping)

        entities = detect(payload)
        audit(
            "identified",
            entity_types=sorted({e.entity_type for e in entities}),
            entity_count=len(entities),
        )
        if policy.mask_types is not None:
            entities = [e for e in entities if e.entity_type in policy.mask_types]
        masked = mask_text(payload, entities)
        audit("masked", entity_count=len(entities))
        candidate = VaultRecord.new(
            payload_id=payload_id,
            request_hash=digest,
            masked_result=masked.text,
            mapping=masked.mapping,
            state="masked",
            ttl_seconds=policy.vault_ttl_seconds,
        )
        result = await self._vault.create_if_absent(candidate)
        if result.created:
            return result.record.masked_result

        # Another replica won the create race. Preserve idempotency when it
        # stored the same source; otherwise treat this request as an output to
        # be restored using the winning mapping.
        if digest == result.record.request_hash:
            return result.record.masked_result
        return restore(result.record.mapping)
