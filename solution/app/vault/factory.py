"""Environment-driven vault construction."""

from __future__ import annotations

import os

from .base import Vault
from .crypto import load_mapping_key
from .memory import InMemoryVault
from .redis import RedisVault


def create_vault(
    *, redis_url: str | None = None, mapping_encryption_key: str | None = None
) -> Vault:
    """Build Redis storage when configured, otherwise a local MVP vault."""

    key = load_mapping_key(mapping_encryption_key)
    configured_redis_url = redis_url or os.getenv("REDIS_URL")
    if configured_redis_url:
        return RedisVault(configured_redis_url, encryption_key=key)
    return InMemoryVault(encryption_key=key)
