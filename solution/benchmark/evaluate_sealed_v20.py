"""Evaluate production and candidate detectors on frozen blind holdout v20."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.detection.detector_v3_26 import detect as detect_326
from app.detection.detector_v3_29 import detect as detect_329
from app.detection.detector_v3_30 import detect as detect_330
from app.detection.models import DetectedEntity
from app.masking import mask_text, unmask_text

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "sealed_holdout_v20.json"
EXPECTED_SHA256 = "017e0664e70badd080d90df61d6d5bb8a9ed278d674fdf0178629edade971f2c"


@dataclass(frozen=True, slots=True)
class Counts:
    true_positive: int
    false_positive: int
    false_negative: int

    def to_dict(self) -> dict[str, int | float]:
        tp, fp, fn = self.true_positive, self.false_positive, self.false_negative
        return {
            **asdict(self),
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        }


def load_dataset() -> dict[str, object]:
    raw = DATASET.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"sealed dataset hash mismatch: {digest}")
    return json.loads(raw)


def key(entity: DetectedEntity) -> tuple[str, int, int]:
    return entity.entity_type, entity.start, entity.end


def counts(expected: set[tuple[str, int, int]], actual: set[tuple[str, int, int]]) -> Counts:
    return Counts(len(expected & actual), len(actual - expected), len(expected - actual))


def gold_entities(case: dict[str, Any]) -> list[DetectedEntity]:
    return [
        DetectedEntity(
            entity_type=entity["type"],
            start=entity["start"],
            end=entity["end"],
            text=entity["value"],
            confidence=1.0,
            source="sealed_holdout_v20",
        )
        for entity in case["entities"]
    ]


def evaluate(
    detector: Callable[[str], list[DetectedEntity]], dataset: dict[str, Any]
) -> dict[str, Any]:
    totals: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    cases: list[dict[str, Any]] = []
    exact_masks = 0
    round_trips = 0
    for case in dataset["cases"]:
        text = case["text"]
        gold = gold_entities(case)
        predicted = detector(text)
        expected_keys, predicted_keys = (
            {key(item) for item in gold},
            {key(item) for item in predicted},
        )
        result = counts(expected_keys, predicted_keys)
        for entity_type in {item[0] for item in expected_keys | predicted_keys}:
            expected_type = {item for item in expected_keys if item[0] == entity_type}
            predicted_type = {item for item in predicted_keys if item[0] == entity_type}
            type_counts = counts(expected_type, predicted_type)
            totals[entity_type][0] += type_counts.true_positive
            totals[entity_type][1] += type_counts.false_positive
            totals[entity_type][2] += type_counts.false_negative
        expected_mask = mask_text(text, gold).text
        actual_mask = mask_text(text, predicted)
        mask_exact = expected_mask == actual_mask.text
        round_trip = unmask_text(actual_mask.text, actual_mask.mapping) == text
        exact_masks += int(mask_exact)
        round_trips += int(round_trip)
        cases.append(
            {
                "id": case["id"],
                "counts": result.to_dict(),
                "mask_exact": mask_exact,
                "round_trip_exact": round_trip,
                "missing": sorted(expected_keys - predicted_keys),
                "unexpected": sorted(predicted_keys - expected_keys),
            }
        )
    overall_raw = [sum(value[index] for value in totals.values()) for index in range(3)]
    by_type = {name: Counts(*value).to_dict() for name, value in sorted(totals.items())}
    return {
        "case_count": len(cases),
        "overall": Counts(*overall_raw).to_dict(),
        "by_type": by_type,
        "mask_exact": {
            "passed": exact_masks,
            "total": len(cases),
            "rate": exact_masks / len(cases),
        },
        "round_trip_exact": {
            "passed": round_trips,
            "total": len(cases),
            "rate": round_trips / len(cases),
        },
        "cases": cases,
    }


def run(
    name: str,
    detector: Callable[[str], list[DetectedEntity]],
    dataset: dict[str, Any],
) -> dict[str, object]:
    report = evaluate(detector, dataset)
    exact_cases = sum(not case["missing"] and not case["unexpected"] for case in report["cases"])
    missing: Counter[str] = Counter()
    unexpected: Counter[str] = Counter()
    for case in report["cases"]:
        missing.update(item[0] for item in case["missing"])
        unexpected.update(item[0] for item in case["unexpected"])
    report["detector"] = name
    report["exact_entities"] = {
        "passed": exact_cases,
        "total": report["case_count"],
        "rate": exact_cases / report["case_count"],
    }
    report["per_type_misses"] = dict(sorted(missing.items()))
    report["per_type_unexpected"] = dict(sorted(unexpected.items()))
    output = ROOT / "results" / f"sealed_holdout_v20_{name.replace('.', '')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def compact(report: dict[str, object]) -> dict[str, object]:
    return {
        "detector": report["detector"],
        "overall": report["overall"],
        "exact_entities": report["exact_entities"],
        "mask_exact": report["mask_exact"],
        "round_trip_exact": report["round_trip_exact"],
        "per_type_misses": report["per_type_misses"],
        "per_type_unexpected": report["per_type_unexpected"],
    }


def main() -> None:
    dataset = load_dataset()
    reports = [
        run("v3.26", detect_326, dataset),
        run("v3.29", detect_329, dataset),
        run("v3.30", detect_330, dataset),
    ]
    summary = {
        "dataset_sha256": EXPECTED_SHA256,
        "case_count": len(dataset["cases"]),
        "results": [compact(report) for report in reports],
    }
    output = ROOT / "results" / "sealed_holdout_v20_summary.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
