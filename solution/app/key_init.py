"""Create the persistent shared mapping key used by all API replicas."""

from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path

from app.vault.crypto import load_mapping_key


def ensure_mapping_key(path: Path) -> None:
    """Create a 256-bit key exactly once, or validate the existing key."""

    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = base64.urlsafe_b64encode(secrets.token_bytes(32))
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    except FileExistsError:
        load_mapping_key(path.read_text(encoding="ascii"))
        return
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> None:
    target = Path(os.environ.get("MAPPING_ENCRYPTION_KEY_FILE", "/run/pii-secrets/mapping.key"))
    ensure_mapping_key(target)


if __name__ == "__main__":
    main()
