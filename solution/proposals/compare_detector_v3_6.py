"""Compare production v3.3 and isolated v3.6 on declared disclosed datasets."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.detection.detector_v3_3 import detect as production_detect
from app.detection.models import DetectedEntity
from benchmark.evaluate_quality import resolve_gold
from proposals.detector_v3_6 import detect as detector_v3_6

Detector = Callable[[str], list[DetectedEntity]]
DATASETS = (
    "quality_dataset.json",
    "adversarial_dataset.json",
    "blind_holdout_v3.json",
    "false_positive_stress_v3.json",
    "sealed_holdout_v4.json",
    "sealed_holdout_v5.json",
)


def score(dataset: dict[str, Any], detector: Detector) -> dict[str, int | float]:
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
    result: dict[str, dict[str, dict[str, int | float]]] = {}
    for filename in DATASETS:
        dataset = json.loads((root / filename).read_text(encoding="utf-8"))
        result[filename] = {
            "production_v3_3": score(dataset, production_detect),
            "candidate_v3_6": score(dataset, detector_v3_6),
        }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path(__file__).parents[1] / "benchmark",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    rendered = json.dumps(compare_all(args.benchmark_root), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
