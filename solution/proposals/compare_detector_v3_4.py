"""Compare v3.1, v3.2, and recall-oriented v3.4 on declared datasets."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from proposals.compare_detector_v3_1 import score
from proposals.detector_v3_1 import detect as detector_v3_1
from proposals.detector_v3_2 import detect as detector_v3_2
from proposals.detector_v3_4 import detect as detector_v3_4

DATASETS = (
    "quality_dataset.json",
    "adversarial_dataset.json",
    "blind_holdout_v3.json",
    "false_positive_stress_v3.json",
    "sealed_holdout_v4.json",
)


def compare_all(root: Path) -> dict[str, object]:
    detectors = {
        "candidate_v3_1": detector_v3_1,
        "candidate_v3_2": detector_v3_2,
        "candidate_v3_4": detector_v3_4,
    }
    result: dict[str, object] = {}
    for filename in DATASETS:
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
