"""Evaluate candidate v3.29 against immutable sealed holdout v19."""

from __future__ import annotations

import json
from pathlib import Path

from app.detection.detector_v3_29 import detect as detect_v3_29
from benchmark import evaluate_quality
from benchmark.evaluate_sealed_v19 import evaluator_projection

ROOT = Path(__file__).parent
DATASET = ROOT / "sealed_holdout_v19.json"


def main() -> None:
    dataset = evaluator_projection(json.loads(DATASET.read_text(encoding="utf-8")))
    evaluate_quality.detect = detect_v3_29  # type: ignore[attr-defined]
    report = evaluate_quality.evaluate_dataset(dataset)
    report["detector"] = "v3.29"
    report["annotation_adapter"] = "explicit start/end projected to occurrence in memory"
    stem = ROOT / "results" / "sealed_holdout_v19_v329"
    stem.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    stem.with_suffix(".md").write_text(evaluate_quality.render_markdown(report), encoding="utf-8")
    print(evaluate_quality.render_markdown(report))


if __name__ == "__main__":
    main()
