"""Evaluate exact PII spans, masking, and reversible restoration locally."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.detection import detect
from app.detection.models import DetectedEntity
from app.masking import mask_text, unmask_text


@dataclass(frozen=True, slots=True)
class GoldEntity:
    entity_type: str
    start: int
    end: int
    text: str


@dataclass(frozen=True, slots=True)
class Counts:
    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        denominator = 2 * self.true_positive + self.false_positive + self.false_negative
        return 2 * self.true_positive / denominator if denominator else 0.0

    def to_dict(self) -> dict[str, int | float]:
        return {
            **asdict(self),
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


def _nth_span(text: str, value: str, occurrence: int) -> tuple[int, int]:
    if not value:
        raise ValueError("gold entity value must not be empty")
    cursor = 0
    for _ in range(occurrence + 1):
        start = text.find(value, cursor)
        if start < 0:
            raise ValueError(f"cannot find occurrence {occurrence} of {value!r}")
        cursor = start + len(value)
    return start, cursor


def resolve_gold(text: str, annotations: Sequence[dict[str, Any]]) -> list[GoldEntity]:
    """Resolve readable value annotations to exact half-open spans."""

    entities: list[GoldEntity] = []
    for annotation in annotations:
        value = str(annotation["value"])
        start, end = _nth_span(text, value, int(annotation.get("occurrence", 0)))
        entities.append(GoldEntity(str(annotation["type"]), start, end, value))
    entities.sort(key=lambda item: (item.start, item.end, item.entity_type))
    for left, right in zip(entities, entities[1:], strict=False):
        if left.end > right.start:
            raise ValueError(f"overlapping gold entities: {left!r}, {right!r}")
    return entities


def _key(entity: GoldEntity | DetectedEntity) -> tuple[str, int, int]:
    return entity.entity_type, entity.start, entity.end


def _counts(expected: set[tuple[str, int, int]], predicted: set[tuple[str, int, int]]) -> Counts:
    return Counts(
        true_positive=len(expected & predicted),
        false_positive=len(predicted - expected),
        false_negative=len(expected - predicted),
    )


def evaluate_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic detection and masking against a loaded benchmark dataset."""

    totals: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    case_results: list[dict[str, Any]] = []
    mask_exact_count = 0
    round_trip_count = 0

    for case in dataset["cases"]:
        text = str(case["text"])
        gold = resolve_gold(text, case["entities"])
        predicted = detect(text)
        expected_keys = {_key(entity) for entity in gold}
        predicted_keys = {_key(entity) for entity in predicted}
        case_counts = _counts(expected_keys, predicted_keys)

        types = {key[0] for key in expected_keys | predicted_keys}
        for entity_type in types:
            expected_type = {key for key in expected_keys if key[0] == entity_type}
            predicted_type = {key for key in predicted_keys if key[0] == entity_type}
            counts = _counts(expected_type, predicted_type)
            totals[entity_type][0] += counts.true_positive
            totals[entity_type][1] += counts.false_positive
            totals[entity_type][2] += counts.false_negative

        expected_mask = mask_text(text, gold)
        actual_mask = mask_text(text, predicted)
        mask_exact = actual_mask.text == expected_mask.text
        round_trip = unmask_text(actual_mask.text, actual_mask.mapping) == text
        mask_exact_count += int(mask_exact)
        round_trip_count += int(round_trip)
        case_results.append(
            {
                "id": case["id"],
                "counts": case_counts.to_dict(),
                "mask_exact": mask_exact,
                "round_trip_exact": round_trip,
                "expected_mask": expected_mask.text,
                "actual_mask": actual_mask.text,
                "missing": sorted(expected_keys - predicted_keys),
                "unexpected": sorted(predicted_keys - expected_keys),
            }
        )

    by_type = {
        entity_type: Counts(*values).to_dict()
        for entity_type, values in sorted(totals.items())
    }
    overall_values = [sum(values[index] for values in totals.values()) for index in range(3)]
    overall = Counts(*overall_values).to_dict()
    case_count = len(case_results)
    return {
        "dataset": dataset["name"],
        "dataset_version": dataset["version"],
        "sources": dataset.get("sources", []),
        "case_count": case_count,
        "overall": overall,
        "by_type": by_type,
        "mask_exact": {
            "passed": mask_exact_count,
            "total": case_count,
            "rate": mask_exact_count / case_count if case_count else 0.0,
        },
        "round_trip_exact": {
            "passed": round_trip_count,
            "total": case_count,
            "rate": round_trip_count / case_count if case_count else 0.0,
        },
        "cases": case_results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a compact, reviewable Markdown summary."""

    overall = report["overall"]
    lines = [
        f"# Quality benchmark: {report['dataset']}",
        "",
        f"Dataset version: `{report['dataset_version']}`; cases: **{report['case_count']}**.",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Precision | {overall['precision']:.2%} |",
        f"| Recall | {overall['recall']:.2%} |",
        f"| F1 | {overall['f1']:.2%} |",
        "| Exact masks | "
        f"{report['mask_exact']['passed']}/{report['mask_exact']['total']} "
        f"({report['mask_exact']['rate']:.2%}) |",
        "| Exact round trips | "
        f"{report['round_trip_exact']['passed']}/{report['round_trip_exact']['total']} "
        f"({report['round_trip_exact']['rate']:.2%}) |",
        "",
        "Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full",
        "generated string with a mask built from gold spans. Round trip verifies that the actual",
        "detected-and-masked string restores byte-for-byte to the input.",
        "",
        "## Metrics by type",
        "",
        "| Type | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for entity_type, metrics in report["by_type"].items():
        lines.append(
            f"| {entity_type} | {metrics['true_positive']} | {metrics['false_positive']} | "
            f"{metrics['false_negative']} | {metrics['precision']:.2%} | "
            f"{metrics['recall']:.2%} | {metrics['f1']:.2%} |"
        )

    failed = [case for case in report["cases"] if not case["mask_exact"]]
    lines.extend(["", "## Cases with a non-exact mask", ""])
    if failed:
        for case in failed:
            lines.append(
                f"- `{case['id']}`: missing={case['missing']}; "
                f"unexpected={case['unexpected']}"
            )
    else:
        lines.append("None.")

    lines.extend(["", "## Sources", ""])
    lines.extend(f"- `{source}`" for source in report["sources"])
    lines.append("")
    return "\n".join(lines)


def _default_dataset() -> Path:
    return Path(__file__).with_name("quality_dataset.json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=_default_dataset())
    parser.add_argument("--json-out", type=Path, default=Path("benchmark/results/quality.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("benchmark/results/quality.md"))
    args = parser.parse_args(argv)

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    report = evaluate_dataset(dataset)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
