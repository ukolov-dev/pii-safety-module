import json
from pathlib import Path

import pytest

from benchmark.evaluate_quality import evaluate_dataset


@pytest.mark.parametrize("dataset_name", ["quality_dataset.json", "adversarial_dataset.json"])
def test_quality_dataset_meets_local_gate(dataset_name: str) -> None:
    dataset_path = Path(__file__).parents[2] / "benchmark" / dataset_name
    report = evaluate_dataset(json.loads(dataset_path.read_text(encoding="utf-8")))

    assert report["overall"]["precision"] >= 0.95
    assert report["overall"]["recall"] >= 0.95
    assert report["overall"]["f1"] >= 0.95
    assert report["mask_exact"]["rate"] >= 0.95
    assert report["round_trip_exact"]["rate"] == 1.0


@pytest.mark.parametrize(
    ("dataset_name", "minimum_f1", "minimum_precision"),
    [
        ("blind_holdout_v3.json", 0.95, 0.95),
        ("false_positive_stress_v3.json", 0.95, 0.95),
        ("sealed_holdout_v4.json", 0.95, 0.95),
        # Frozen v2 baseline was 0.596491; promotion requires at least +10 p.p.
        ("sealed_holdout_v5.json", 0.696491, 0.85),
        ("sealed_holdout_v6.json", 0.95, 0.95),
        ("sealed_holdout_v7.json", 0.95, 0.95),
        ("sealed_holdout_v8.json", 0.95, 0.95),
        ("sealed_holdout_v9.json", 0.95, 0.95),
        # Frozen v3.3 baseline was 0.680203; promotion requires at least +10 p.p.
        ("sealed_holdout_v10.json", 0.780203, 0.705263),
        ("sealed_holdout_v11.json", 0.95, 0.95),
        ("sealed_holdout_v12.json", 0.95, 0.95),
        # Frozen v3.13 baseline was 0.611465; promotion requires at least +10 p.p.
        ("sealed_holdout_v13.json", 0.711465, 0.705882),
        ("sealed_holdout_v14.json", 0.80, 0.807339),
        ("sealed_holdout_v15.json", 0.80, 0.762712),
        # The target is >80%; v3.20 baseline was F1 0.853333 / precision 0.864865.
        ("sealed_holdout_v16.json", 0.853334, 0.864865),
    ],
)
def test_extended_quality_gates(
    dataset_name: str, minimum_f1: float, minimum_precision: float
) -> None:
    dataset_path = Path(__file__).parents[2] / "benchmark" / dataset_name
    report = evaluate_dataset(json.loads(dataset_path.read_text(encoding="utf-8")))

    assert report["overall"]["precision"] >= minimum_precision
    assert report["overall"]["f1"] >= minimum_f1
    assert report["round_trip_exact"]["rate"] == 1.0
