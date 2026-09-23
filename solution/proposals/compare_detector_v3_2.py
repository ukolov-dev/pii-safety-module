"""Compare production, v3, and ownership-gated v3.2 candidates."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection import detect as production_detect
from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from proposals.detector_v3 import detect as detector_v3
from proposals.detector_v3_2 import detect as detector_v3_2

Detector = Callable[[str], list[DetectedEntity]]


def _score(dataset: dict[str, Any], detector: Detector) -> dict[str, int | float]:
    expected: set[tuple[str, str, int, int]] = set()
    predicted: set[tuple[str, str, int, int]] = set()
    for case in dataset["cases"]:
        case_id = str(case["id"])
        text = str(case["text"])
        expected.update(
            (case_id, item.entity_type, item.start, item.end)
            for item in resolve_gold(text, case["entities"])
        )
        predicted.update(
            (case_id, item.entity_type, item.start, item.end) for item in detector(text)
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
    }


def compare(dataset: dict[str, Any]) -> dict[str, dict[str, int | float]]:
    return {
        "production": _score(dataset, production_detect),
        "candidate_v3": _score(dataset, detector_v3),
        "candidate_v3_2": _score(dataset, detector_v3_2),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args(argv)
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(json.dumps(compare(dataset), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
