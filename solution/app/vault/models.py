"""Domain models for the reversible-masking vault."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class VaultRecord:
    """Immutable state stored for a single payload identifier."""

    payload_id: str
    request_hash: str
    masked_result: str
    mapping: Mapping[str, str]
    state: str
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.payload_id:
            raise ValueError("payload_id must not be empty")
        if not self.request_hash:
            raise ValueError("request_hash must not be empty")
        if not self.state:
            raise ValueError("state must not be empty")
        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.mapping.items()
        ):
            raise ValueError("mapping keys and values must be strings")
        if self.expires_at.tzinfo is None or self.created_at.tzinfo is None:
            raise ValueError("created_at and expires_at must be timezone-aware")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        # Do not retain a caller-owned mutable dictionary.
        object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))

    @classmethod
    def new(
        cls,
        *,
        payload_id: str,
        request_hash: str,
        masked_result: str,
        mapping: Mapping[str, str],
        state: str,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> VaultRecord:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        from datetime import timedelta

        created_at = now or datetime.now(UTC)
        return cls(
            payload_id=payload_id,
            request_hash=request_hash,
            masked_result=masked_result,
            mapping=mapping,
            state=state,
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=ttl_seconds),
        )


@dataclass(frozen=True, slots=True)
class CreateResult:
    """Result of an atomic create operation.

    ``record`` is always the record that won the create race. A retry can use
    its ``masked_result`` without running detection and masking again.
    """

    created: bool
    record: VaultRecord
