"""Compare production v3.26 and candidate v3.29 on disclosed data."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection.detector_v3_26 import detect as detector_v3_26
from app.detection.detector_v3_29 import detect as detector_v3_29
from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from benchmark.evaluate_sealed_v19 import evaluator_projection

Detector = Callable[[str], list[DetectedEntity]]
DISCLOSED_DATASETS = (
    "quality_dataset.json",
    "adversarial_dataset.json",
    "blind_holdout_v3.json",
    "false_positive_stress_v3.json",
    *(f"sealed_holdout_v{version}.json" for version in range(4, 17)),
    "sealed_holdout_v19.json",
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
            (case_id, entity.entity_type, entity.start, entity.end) for entity in detector(text)
        )
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    denominator = 2 * true_positive + false_positive + false_negative
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": true_positive / len(predicted) if predicted else 1.0,
        "recall": true_positive / len(expected) if expected else 1.0,
        "f1": 2 * true_positive / denominator if denominator else 1.0,
    }


def compare_all(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for filename in DISCLOSED_DATASETS:
        dataset = json.loads((root / filename).read_text(encoding="utf-8"))
        if filename == "sealed_holdout_v19.json":
            dataset = evaluator_projection(dataset)
        baseline = score(dataset, detector_v3_26)
        candidate = score(dataset, detector_v3_29)
        changed_cases = sum(
            {
                (entity.entity_type, entity.start, entity.end)
                for entity in detector_v3_26(str(case["text"]))
            }
            != {
                (entity.entity_type, entity.start, entity.end)
                for entity in detector_v3_29(str(case["text"]))
            }
            for case in dataset["cases"]
        )
        result[filename] = {
            "v3.26": baseline,
            "v3.29": candidate,
            "changed_cases": changed_cases,
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
