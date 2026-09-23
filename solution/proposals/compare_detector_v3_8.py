"""Compare production v3.3 and candidate v3.8 on disclosed datasets only."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from app.detection.detector_v3_3 import detect as production_detect
from proposals.compare_detector_v3_6 import score
from proposals.detector_v3_8 import detect as detector_v3_8

DATASETS = (
    "quality_dataset.json",
    "adversarial_dataset.json",
    "blind_holdout_v3.json",
    "false_positive_stress_v3.json",
    "sealed_holdout_v4.json",
    "sealed_holdout_v5.json",
    "sealed_holdout_v6.json",
)


def compare_all(root: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for filename in DATASETS:
        dataset = json.loads((root / filename).read_text(encoding="utf-8"))
        result[filename] = {
            "production_v3_3": score(dataset, production_detect),
            "candidate_v3_8": score(dataset, detector_v3_8),
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
