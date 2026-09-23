"""Validate the frozen canonical blind holdout v20 without detector imports."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

DATASET = Path(__file__).resolve().parent / "sealed_holdout_v20.json"
EXPECTED_SHA256 = "017e0664e70badd080d90df61d6d5bb8a9ed278d674fdf0178629edade971f2c"
EXPECTED_TYPES = {
    "PERSON",
    "BIRTH_DATE",
    "PLACE_OF_BIRTH",
    "PASSPORT_RF",
    "CITIZENSHIP",
    "PASSPORT_ISSUER",
    "DIVISION_CODE",
    "PASSPORT_ISSUE_DATE",
    "DRIVER_LICENSE_RF",
    "ADDRESS_COUNTRY",
    "ADDRESS_POSTAL_CODE",
    "ADDRESS_CITY",
    "ADDRESS_STREET",
    "ADDRESS_HOUSE",
    "ADDRESS_APARTMENT",
    "EMAIL",
    "PHONE_RF",
    "INN",
    "BANK_CARD",
    "CVV",
    "PIN",
    "CARDHOLDER_NAME",
}


def digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def valid_luhn(value: str) -> bool:
    number = digits(value)
    total = 0
    parity = len(number) % 2
    for index, char in enumerate(number):
        digit = int(char)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return len(number) == 16 and total % 10 == 0


def valid_inn12(value: str) -> bool:
    if not re.fullmatch(r"\d{12}", value):
        return False
    number = [int(char) for char in value]
    check11 = (
        sum(a * b for a, b in zip(number[:10], [7, 2, 4, 10, 3, 5, 9, 4, 6, 8], strict=True))
        % 11
        % 10
    )
    check12 = (
        sum(a * b for a, b in zip(number[:11], [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8], strict=True))
        % 11
        % 10
    )
    return number[10:] == [check11, check12]


def valid_date(value: str) -> bool:
    return any(_can_parse(value, pattern) for pattern in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"))


def _can_parse(value: str, pattern: str) -> bool:
    try:
        datetime.strptime(value, pattern)
    except ValueError:
        return False
    return True


def main() -> None:
    raw = DATASET.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == EXPECTED_SHA256, f"immutable SHA mismatch: {digest}"
    payload = json.loads(raw)
    assert payload["version"] == 20
    assert payload["sources"] == ["RAW/requirements.md"]
    cases = payload["cases"]
    assert len(cases) >= 300
    assert len({case["id"] for case in cases}) == len(cases)
    assert len({case["text"] for case in cases}) == len(cases)

    counts: Counter[str] = Counter()
    clean = 0
    families: Counter[str] = Counter()
    for case in cases:
        text = case["text"]
        entities = case["entities"]
        families[case["family"]] += 1
        if case["family"] == "clean-negative":
            clean += 1
            assert entities == []
        previous_end = -1
        for entity in entities:
            entity_type = entity["type"]
            assert entity_type in EXPECTED_TYPES
            start, end, value = entity["start"], entity["end"], entity["value"]
            assert isinstance(start, int) and isinstance(end, int)
            assert 0 <= start < end <= len(text)
            assert text[start:end] == value
            assert start >= previous_end, f"overlap in {case['id']}"
            previous_end = end
            counts[entity_type] += 1

            if entity_type == "PHONE_RF":
                normalized = digits(value)
                assert len(normalized) == 11 and normalized[0] in "78"
            elif entity_type == "DIVISION_CODE":
                assert re.fullmatch(r"\d{3}-\d{3}", value)
            elif entity_type == "INN":
                assert valid_inn12(value)
            elif entity_type == "BANK_CARD":
                assert valid_luhn(value)
            elif entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"}:
                assert valid_date(value)

    assert set(counts) == EXPECTED_TYPES
    assert min(counts.values()) >= 30
    assert clean >= 30
    assert {
        "identity-prose",
        "passport-ocr",
        "contact-config",
        "address-json",
        "bank-prose",
        "mixed-ticket",
        "mixed-json",
    } <= set(families)
    print("validation=GREEN")
    print(f"sha256={digest}")
    minimum = min(counts.values())
    print(f"cases={len(cases)} clean={clean} types={len(counts)} min_type_count={minimum}")
    print("type_counts=" + json.dumps(dict(sorted(counts.items())), ensure_ascii=False))
    print("families=" + json.dumps(dict(sorted(families.items())), ensure_ascii=False))


if __name__ == "__main__":
    main()
