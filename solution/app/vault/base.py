"""Async vault interface."""

from __future__ import annotations

from typing import Protocol

from .models import CreateResult, VaultRecord


class Vault(Protocol):
    async def create_if_absent(self, record: VaultRecord) -> CreateResult:
        """Atomically store ``record`` unless a live record already exists."""
        ...

    async def get(self, payload_id: str) -> VaultRecord | None:
        """Return a live record, or ``None`` after its TTL expires."""
        ...

    async def cleanup_expired(self) -> int:
        """Remove expired records and return the number removed."""
        ...

    async def ping(self) -> bool:
        """Return whether the backing store is currently reachable."""
        ...

    async def close(self) -> None:
        """Release backend resources."""
        ...
