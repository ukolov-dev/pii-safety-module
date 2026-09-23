"""Environment-driven vault construction."""

from __future__ import annotations

import os
from pathlib import Path

from .base import Vault
from .crypto import load_mapping_key
from .memory import InMemoryVault
from .redis import RedisVault


def create_vault(
    *,
    redis_url: str | None = None,
    mapping_encryption_key: str | None = None,
    mapping_encryption_key_file: str | None = None,
) -> Vault:
    """Build Redis storage when configured, otherwise a local MVP vault."""

    if mapping_encryption_key and mapping_encryption_key_file:
        raise ValueError(
            "configure only one of MAPPING_ENCRYPTION_KEY and "
            "MAPPING_ENCRYPTION_KEY_FILE"
        )
    configured_key = mapping_encryption_key
    if mapping_encryption_key_file:
        configured_key = Path(mapping_encryption_key_file).read_text(encoding="ascii")
    key = load_mapping_key(configured_key)
    configured_redis_url = redis_url or os.getenv("REDIS_URL")
    if configured_redis_url:
        return RedisVault(configured_redis_url, encryption_key=key)
    return InMemoryVault(encryption_key=key)
