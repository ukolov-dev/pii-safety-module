"""Evaluate v3.28 on original v17 and a convention-corrected derivative.

The correction is deterministic and limited to address annotations:

* aggregate ``address`` spans become the six non-overlapping component values
  used by the application detector;
* street/house/apartment designators are excluded from value spans, matching
  every disclosed benchmark through v16;
* explicit occurrence indexes preserve the supplied source offsets when a
  short component value also occurs earlier in the same text.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from app.detection.detector_v3_28 import detect as detect_v328
from benchmark import evaluate_quality as quality
from benchmark.evaluate_sealed_v17 import (
    DATASET_PATH,
    EXPECTED_SHA256,
    TYPE_MAP,
    load_dataset,
)

ROOT = Path(__file__).resolve().parent
CORRECTED_SHA256 = "d8c840f66ad73047c3a57b0e5f2b1768ebaa79ee99e8f1361176a16c373f5fa8"

_ADDRESS = re.compile(
    r"(?P<country>[А-ЯЁ][А-ЯЁа-яё-]*(?:\s+[А-ЯЁ][А-ЯЁа-яё-]*)?)\s*,\s*"
    r"(?P<postcode>\d{6})\s*,\s*(?:г\.?\s*)?"
    r"(?P<city>[А-ЯЁ][А-ЯЁа-яё-]*(?:\s+[А-ЯЁ][А-ЯЁа-яё-]*)?)\s*,\s*"
    r"(?:улиц\w*|ул\.|проспект|пр-т|шоссе)\s+"
    r"(?P<street>[А-ЯЁа-яё-]+(?:\s+[А-ЯЁа-яё-]+){0,2})\s*,\s*"
    r"(?:дом|д\.|владение)\s*(?:№\s*)?(?P<house>\d+[А-ЯЁA-Z]?)\s*,\s*"
    r"(?:квартир\w*|кв\.?)\s*(?:№\s*)?(?P<flat>\d+)"
)
_STRIP = {
    "street": re.compile(r"^(?:улиц\w*|ул\.|проспект|пр-т|шоссе)\s+", re.I),
    "house": re.compile(r"^(?:дом|д\.|владение)\s*(?:№\s*)?", re.I),
    "apartment": re.compile(r"^(?:квартир\w*|кв\.?)\s*(?:№\s*)?", re.I),
}
_ADDRESS_TYPES = (
    ("country", "ADDRESS_COUNTRY"),
    ("postcode", "ADDRESS_POSTAL_CODE"),
    ("city", "ADDRESS_CITY"),
    ("street", "ADDRESS_STREET"),
    ("house", "ADDRESS_HOUSE"),
    ("flat", "ADDRESS_APARTMENT"),
)


def _annotation(text: str, entity_type: str, value: str, start: int) -> dict[str, Any]:
    if text[start : start + len(value)] != value:
        raise ValueError(f"value/span mismatch for {entity_type}: {value!r} at {start}")
    occurrence = sum(1 for _ in re.finditer(re.escape(value), text[:start]))
    return {"type": entity_type, "value": value, "occurrence": occurrence}


def build_corrected_dataset() -> dict[str, Any]:
    raw_bytes = DATASET_PATH.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("original v17 hash mismatch")
    source = json.loads(raw_bytes)
    cases: list[dict[str, Any]] = []
    for case in source["cases"]:
        text = str(case["text"])
        entities: list[dict[str, Any]] = []
        for raw_entity in case["expected_entities"]:
            raw_type = str(raw_entity["type"])
            value = str(raw_entity["value"])
            start = int(raw_entity["start"])
            if raw_type == "address":
                match = _ADDRESS.fullmatch(value)
                if match is None:
                    raise ValueError(f"unparseable address in {case['id']}: {value!r}")
                for group, entity_type in _ADDRESS_TYPES:
                    component = match.group(group)
                    entities.append(
                        _annotation(text, entity_type, component, start + match.start(group))
                    )
                continue
            if raw_type in _STRIP:
                prefix = _STRIP[raw_type].match(value)
                if prefix is None:
                    raise ValueError(f"missing designator in {case['id']}: {value!r}")
                start += prefix.end()
                value = value[prefix.end() :]
            entities.append(_annotation(text, TYPE_MAP[raw_type], value, start))
        cases.append({"id": case["id"], "text": text, "entities": entities})
    dataset = {
        "name": "sealed_holdout_v17_corrected_component_spans",
        "version": "17-c1",
        "sources": source["requirements_sources"],
        "cases": cases,
    }
    canonical = (
        json.dumps(dataset, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    actual = hashlib.sha256(canonical).hexdigest()
    if actual != CORRECTED_SHA256:
        raise RuntimeError(f"corrected v17 hash mismatch: {actual}")
    return dataset


def _run(dataset: dict[str, Any]) -> dict[str, Any]:
    quality.detect = detect_v328  # type: ignore[attr-defined]
    return quality.evaluate_dataset(dataset)


def main() -> int:
    typed_load = cast(Callable[[], dict[str, Any]], load_dataset)
    reports = {
        "original": _run(typed_load()),
        "corrected": _run(build_corrected_dataset()),
    }
    for name, report in reports.items():
        output = ROOT / "results" / f"sealed_holdout_v17_{name}_v328.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                name: {
                    "overall": report["overall"],
                    "mask_exact": report["mask_exact"],
                    "round_trip_exact": report["round_trip_exact"],
                }
                for name, report in reports.items()
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
