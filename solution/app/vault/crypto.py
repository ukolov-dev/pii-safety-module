"""Authenticated encryption for vault mappings."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
from collections.abc import Mapping

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as exc:  # pragma: no cover - dependency error at deployment
    raise RuntimeError("cryptography is required by the mapping vault") from exc


_LOGGER = logging.getLogger(__name__)
_AAD_VERSION = b"pii-vault-mapping:v1:"


def _decode_key(value: str) -> bytes:
    """Decode a 256-bit key from URL-safe base64 or hexadecimal."""

    candidate = value.strip()
    try:
        if len(candidate) == 64:
            key = bytes.fromhex(candidate)
        else:
            key = base64.b64decode(candidate, altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(
            "MAPPING_ENCRYPTION_KEY must be a base64 or hexadecimal 256-bit key"
        ) from exc
    if len(key) != 32:
        raise ValueError("MAPPING_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def load_mapping_key(value: str | None = None) -> bytes:
    """Load the configured key or create a process-local development key."""

    configured = value if value is not None else os.getenv("MAPPING_ENCRYPTION_KEY")
    if configured:
        return _decode_key(configured)

    _LOGGER.warning(
        "MAPPING_ENCRYPTION_KEY is not configured; using an ephemeral "
        "process-local development key. Stored mappings cannot survive restart."
    )
    return AESGCM.generate_key(bit_length=256)


class MappingCipher:
    """AES-256-GCM envelope for a token-to-original-value mapping."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AES-256-GCM requires a 32-byte key")
        self._aesgcm = AESGCM(key)

    @staticmethod
    def _aad(payload_id: str) -> bytes:
        return _AAD_VERSION + payload_id.encode("utf-8")

    def encrypt(self, payload_id: str, mapping: Mapping[str, str]) -> bytes:
        plaintext = json.dumps(
            dict(mapping), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        nonce = os.urandom(12)
        return nonce + self._aesgcm.encrypt(nonce, plaintext, self._aad(payload_id))

    def decrypt(self, payload_id: str, envelope: bytes) -> dict[str, str]:
        if len(envelope) < 13:
            raise ValueError("invalid encrypted mapping envelope")
        nonce, ciphertext = envelope[:12], envelope[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, self._aad(payload_id))
        decoded = json.loads(plaintext)
        if not isinstance(decoded, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in decoded.items()
        ):
            raise ValueError("decrypted mapping has an invalid shape")
        return decoded
