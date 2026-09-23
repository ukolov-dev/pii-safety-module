"""Compare production detection with the isolated v2 candidate on one dataset."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection import detect as baseline_detect
from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from proposals.detector_v2 import detect as candidate_detect

Detector = Callable[[str], list[DetectedEntity]]


def _score(dataset: dict[str, Any], detector: Detector) -> dict[str, int | float]:
    expected: set[tuple[str, str, int, int]] = set()
    predicted: set[tuple[str, str, int, int]] = set()
    for case in dataset["cases"]:
        case_id = str(case["id"])
        text = str(case["text"])
        expected.update(
            (case_id, entity.entity_type, entity.start, entity.end)
            for entity in resolve_gold(text, case["entities"])
        )
        predicted.update(
            (case_id, entity.entity_type, entity.start, entity.end) for entity in detector(text)
        )
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    precision = true_positive / (true_positive + false_positive) if predicted else 0.0
    recall = true_positive / (true_positive + false_negative) if expected else 0.0
    denominator = 2 * true_positive + false_positive + false_negative
    f1 = 2 * true_positive / denominator if denominator else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def compare(dataset: dict[str, Any]) -> dict[str, dict[str, int | float]]:
    return {
        "baseline": _score(dataset, baseline_detect),
        "candidate_v2": _score(dataset, candidate_detect),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).parents[1] / "benchmark" / "quality_dataset.json",
    )
    args = parser.parse_args(argv)
    result = compare(json.loads(args.dataset.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
