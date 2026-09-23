"""Validate structural and semantic invariants of sealed holdout v19."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ALLOWLIST = {
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
DATE_TYPES = {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"}
DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")


def digits(value: str) -> str:
    return "".join(char for char in value if char.isascii() and char.isdigit())


def valid_inn(value: str) -> bool:
    value = digits(value)
    if len(value) == 10:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (
            int(value[9])
            == sum(int(d) * w for d, w in zip(value[:9], weights, strict=True)) % 11 % 10
        )
    if len(value) == 12:
        w11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        d11 = sum(int(d) * w for d, w in zip(value[:10], w11, strict=True)) % 11 % 10
        d12 = sum(int(d) * w for d, w in zip(value[:11], w12, strict=True)) % 11 % 10
        return int(value[10]) == d11 and int(value[11]) == d12
    return False


def valid_luhn(value: str) -> bool:
    value = digits(value)
    if not 16 <= len(value) <= 19:
        return False
    parity = len(value) % 2
    total = 0
    for pos, char in enumerate(value):
        digit = int(char)
        if pos % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate(dataset: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    cases = dataset.get("cases")
    if not isinstance(cases, list):
        return {"green": False, "errors": ["cases must be a list"]}
    if not 260 <= len(cases) <= 320:
        errors.append(f"case count {len(cases)} outside 260..320")
    seen_texts: set[str] = set()
    clean_cases = 0

    for case_index, case in enumerate(cases):
        case_id = str(case.get("id", f"index-{case_index}"))
        text = case.get("text")
        entities = case.get("entities")
        if not isinstance(text, str) or not text:
            errors.append(f"{case_id}: text must be non-empty string")
            continue
        if text in seen_texts:
            errors.append(f"{case_id}: duplicate case text")
        seen_texts.add(text)
        if not isinstance(entities, list):
            errors.append(f"{case_id}: entities must be a list")
            continue
        if not entities:
            clean_cases += 1
        spans: list[tuple[int, int, str]] = []
        search_cursor = 0
        for entity_index, entity in enumerate(entities):
            prefix = f"{case_id}.entities[{entity_index}]"
            entity_type = entity.get("type")
            value = entity.get("value")
            if entity_type not in ALLOWLIST:
                errors.append(f"{prefix}: disallowed type {entity_type!r}")
                continue
            counts[entity_type] += 1
            if not isinstance(value, str) or not value:
                errors.append(f"{prefix}: value must be non-empty string")
                continue
            start = entity.get("start")
            end = entity.get("end")
            if not isinstance(start, int) or not isinstance(end, int):
                errors.append(f"{prefix}: explicit integer span required")
                continue
            if not (0 <= start < end <= len(text)) or text[start:end] != value:
                errors.append(f"{prefix}: span does not exactly select value")
            located = text.find(value, search_cursor)
            if located != start:
                errors.append(f"{prefix}: evaluator resolution differs ({located} != {start})")
            search_cursor = end
            spans.append((start, end, entity_type))

            normalized = digits(value)
            if entity_type == "PHONE_RF" and not (len(normalized) == 11 and normalized[0] in "78"):
                errors.append(f"{prefix}: PHONE_RF must contain exactly 11 digits beginning 7/8")
            elif entity_type == "DIVISION_CODE" and re.fullmatch(r"\d{3}-\d{3}", value) is None:
                errors.append(f"{prefix}: DIVISION_CODE must be 3-3")
            elif entity_type == "INN" and not valid_inn(value):
                errors.append(f"{prefix}: invalid INN checksum")
            elif entity_type == "BANK_CARD" and not valid_luhn(value):
                errors.append(f"{prefix}: invalid 16..19 digit Luhn card")
            elif entity_type in DATE_TYPES:
                valid_date = False
                for date_format in DATE_FORMATS:
                    try:
                        datetime.strptime(value, date_format)
                        valid_date = True
                        break
                    except ValueError:
                        pass
                if not valid_date:
                    errors.append(f"{prefix}: invalid/unsupported calendar date")

        for left, right in zip(sorted(spans), sorted(spans)[1:], strict=False):
            if left[1] > right[0]:
                errors.append(f"{case_id}: overlapping spans {left} and {right}")

    missing = sorted(entity_type for entity_type in ALLOWLIST if counts[entity_type] < 8)
    if missing:
        errors.append("types below 8 positives: " + ", ".join(f"{t}={counts[t]}" for t in missing))
    return {
        "green": not errors,
        "case_count": len(cases),
        "positive_cases": len(cases) - clean_cases,
        "clean_cases": clean_cases,
        "unique_texts": len(seen_texts),
        "entity_count": sum(counts.values()),
        "counts_by_type": dict(sorted(counts.items())),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dataset", nargs="?", type=Path, default=Path(__file__).with_name("sealed_holdout_v19.json")
    )
    args = parser.parse_args()
    report = validate(json.loads(args.dataset.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
