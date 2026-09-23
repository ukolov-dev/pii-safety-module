"""Evaluate immutable v19 with the existing evaluator and explicit-span adapter."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.detection.detector_v3_26 import detect as detect_v3_26
from app.detection.detector_v3_28 import detect as detect_v3_28
from app.detection.models import DetectedEntity
from benchmark import evaluate_quality

ROOT = Path(__file__).parent
DATASET = ROOT / "sealed_holdout_v19.json"


def occurrence_for_span(text: str, value: str, expected_start: int) -> int:
    cursor = 0
    occurrence = 0
    while True:
        start = text.find(value, cursor)
        if start < 0 or start > expected_start:
            raise ValueError(f"cannot project explicit span {expected_start} for {value!r}")
        if start == expected_start:
            return occurrence
        cursor = start + len(value)
        occurrence += 1


def evaluator_projection(dataset: dict[str, Any]) -> dict[str, Any]:
    """Add evaluator-compatible occurrences in memory; preserve sealed bytes."""

    projected = copy.deepcopy(dataset)
    for case in projected["cases"]:
        text = case["text"]
        for entity in case["entities"]:
            entity["occurrence"] = occurrence_for_span(text, entity["value"], entity["start"])
    return projected


def run(
    label: str, detector: Callable[[str], list[DetectedEntity]], dataset: dict[str, Any]
) -> None:
    evaluate_quality.detect = detector
    report = evaluate_quality.evaluate_dataset(dataset)
    report["detector"] = label
    report["annotation_adapter"] = "explicit start/end projected to occurrence in memory"
    stem = ROOT / "results" / f"sealed_holdout_v19_{label.replace('.', '')}"
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(evaluate_quality.render_markdown(report), encoding="utf-8")
    print(label)
    print(evaluate_quality.render_markdown(report))


def main() -> None:
    dataset = evaluator_projection(json.loads(DATASET.read_text(encoding="utf-8")))
    run("v3.26", detect_v3_26, dataset)
    run("v3.28", detect_v3_28, dataset)


if __name__ == "__main__":
    main()
