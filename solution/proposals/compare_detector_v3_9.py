"""Compare v3.3, v3.7, and v3.9 on disclosed datasets through v7."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from proposals.detector_v3_3 import detect as detector_v3_3
from proposals.detector_v3_7 import detect as detector_v3_7
from proposals.detector_v3_9 import detect as detector_v3_9

Detector = Callable[[str], list[DetectedEntity]]
DISCLOSED_DATASETS = (
    "quality_dataset.json",
    "adversarial_dataset.json",
    "blind_holdout_v3.json",
    "false_positive_stress_v3.json",
    "sealed_holdout_v4.json",
    "sealed_holdout_v5.json",
    "sealed_holdout_v6.json",
    "sealed_holdout_v7.json",
)


def score(dataset: dict[str, Any], detector: Detector) -> dict[str, int | float]:
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
            (case_id, entity.entity_type, entity.start, entity.end)
            for entity in detector(text)
        )
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    denominator = 2 * true_positive + false_positive + false_negative
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": true_positive / len(predicted) if predicted else 0.0,
        "recall": true_positive / len(expected) if expected else 0.0,
        "f1": 2 * true_positive / denominator if denominator else 0.0,
    }


def compare_all(root: Path) -> dict[str, dict[str, dict[str, int | float]]]:
    detectors = {
        "v3.3": detector_v3_3,
        "v3.7": detector_v3_7,
        "v3.9": detector_v3_9,
    }
    result: dict[str, dict[str, dict[str, int | float]]] = {}
    for filename in DISCLOSED_DATASETS:
        dataset = json.loads((root / filename).read_text(encoding="utf-8"))
        result[filename] = {
            name: score(dataset, detector) for name, detector in detectors.items()
        }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path(__file__).parents[1] / "benchmark",
    )
    args = parser.parse_args(argv)
    print(json.dumps(compare_all(args.benchmark_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
