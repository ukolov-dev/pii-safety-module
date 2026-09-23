"""Compare isolated detector v3.30 with production v3.26 on disclosed data."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import benchmark.evaluate_quality as evaluator
from app.detection.detector_v3_26 import detect as detect_v3_26
from app.detection.detector_v3_30 import detect as detect_v3_30
from app.detection.models import DetectedEntity

ROOT = Path(__file__).parent
OUTPUT_JSON = ROOT / "results" / "detector-v3-30-comparison.json"
OUTPUT_MD = ROOT / "results" / "detector-v3-30-comparison.md"


def _project_explicit_spans(dataset: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(dataset)
    for case in projected["cases"]:
        text = case["text"]
        for entity in case["entities"]:
            cursor = 0
            occurrence = 0
            while True:
                start = text.find(entity["value"], cursor)
                if start < 0 or start > entity["start"]:
                    raise ValueError(f"cannot project {entity!r}")
                if start == entity["start"]:
                    entity["occurrence"] = occurrence
                    break
                cursor = start + len(entity["value"])
                occurrence += 1
    return projected


def _evaluate(
    detector: Callable[[str], list[DetectedEntity]], dataset: dict[str, Any]
) -> dict[str, Any]:
    evaluator.__dict__["detect"] = detector
    return evaluator.evaluate_dataset(dataset)


def _metrics(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall": report["overall"],
        "mask_exact": report["mask_exact"],
        "round_trip_exact": report["round_trip_exact"],
    }


def main() -> None:
    rows: list[dict[str, Any]] = []
    for version in [*range(4, 17), 19]:
        path = ROOT / f"sealed_holdout_v{version}.json"
        dataset = json.loads(path.read_text(encoding="utf-8"))
        if version == 19:
            dataset = _project_explicit_spans(dataset)
        production = _evaluate(detect_v3_26, dataset)
        candidate = _evaluate(detect_v3_30, dataset)
        rows.append(
            {
                "dataset": path.name,
                "production_v3_26": _metrics(production),
                "candidate_v3_30": _metrics(candidate),
            }
        )

    payload = {
        "candidate": "v3.30",
        "base": "v3.26",
        "scope": "disclosed sealed holdouts v4-v16 and v19",
        "datasets": rows,
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Candidate detector v3.30 comparison",
        "",
        "| Dataset | Detector | Precision | Recall | F1 | Exact masks | Round-trip |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        for label, key in (("v3.26", "production_v3_26"), ("v3.30", "candidate_v3_30")):
            report = row[key]
            overall = report["overall"]
            lines.append(
                f"| {row['dataset']} | {label} | {overall['precision']:.4%} | "
                f"{overall['recall']:.4%} | {overall['f1']:.4%} | "
                f"{report['mask_exact']['rate']:.4%} | "
                f"{report['round_trip_exact']['rate']:.4%} |"
            )
    lines.extend(
        [
            "",
            "v3.30 is isolated and not exported by `app.detection`. Its additions are "
            "semantic labelled-record parsers with calendar, Luhn, format and issuer validation; "
            "they contain no benchmark IDs or known entity-value dictionaries.",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT_JSON)
    print(OUTPUT_MD)


if __name__ == "__main__":
    main()
