"""Compare production detection with the isolated v3 candidate."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection import detect as baseline_detect
from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from proposals.detector_v3 import detect as candidate_detect

Detector = Callable[[str], list[DetectedEntity]]


def _score(dataset: dict[str, Any], detector: Detector) -> dict[str, Any]:
    expected: set[tuple[str, str, int, int]] = set()
    predicted: set[tuple[str, str, int, int]] = set()
    failures: list[dict[str, Any]] = []
    for case in dataset["cases"]:
        case_id = str(case["id"])
        text = str(case["text"])
        expected_case = {
            (case_id, entity.entity_type, entity.start, entity.end)
            for entity in resolve_gold(text, case["entities"])
        }
        predicted_case = {
            (case_id, entity.entity_type, entity.start, entity.end) for entity in detector(text)
        }
        expected.update(expected_case)
        predicted.update(predicted_case)
        if expected_case != predicted_case:
            failures.append(
                {
                    "id": case_id,
                    "missing": sorted(expected_case - predicted_case),
                    "unexpected": sorted(predicted_case - expected_case),
                }
            )
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    precision = true_positive / (true_positive + false_positive) if predicted else 0.0
    recall = true_positive / (true_positive + false_negative) if expected else 0.0
    denominator = 2 * true_positive + false_positive + false_negative
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": 2 * true_positive / denominator if denominator else 0.0,
        "failed_cases": failures,
    }


def compare(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "production": _score(dataset, baseline_detect),
        "candidate_v3": _score(dataset, candidate_detect),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).parents[1] / "benchmark" / "quality_dataset.json",
    )
    args = parser.parse_args(argv)
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(json.dumps(compare(dataset), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
