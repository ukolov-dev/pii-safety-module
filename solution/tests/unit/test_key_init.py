from pathlib import Path

from app.key_init import ensure_mapping_key
from app.vault.crypto import load_mapping_key


def test_key_init_is_persistent_and_idempotent(tmp_path: Path) -> None:
    key_path = tmp_path / "secrets" / "mapping.key"

    ensure_mapping_key(key_path)
    first = key_path.read_text(encoding="ascii")
    ensure_mapping_key(key_path)

    assert key_path.read_text(encoding="ascii") == first
    assert len(load_mapping_key(first)) == 32
    assert key_path.stat().st_mode & 0o777 == 0o400
