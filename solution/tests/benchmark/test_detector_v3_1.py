from pathlib import Path

from proposals.compare_detector_v3_1 import PUBLIC_DATASETS, compare_all

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_1_comparison_uses_only_declared_public_datasets() -> None:
    assert PUBLIC_DATASETS == (
        "quality_dataset.json",
        "adversarial_dataset.json",
        "blind_holdout_v3.json",
        "false_positive_stress_v3.json",
    )


def test_v3_1_meets_public_quality_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    quality = report["quality_dataset.json"]["candidate_v3_1"]
    adversarial = report["adversarial_dataset.json"]["candidate_v3_1"]
    blind = report["blind_holdout_v3.json"]
    stress = report["false_positive_stress_v3.json"]

    assert quality["f1"] >= 0.95
    assert adversarial["f1"] >= 0.95
    assert blind["candidate_v3_1"]["f1"] >= blind["production"]["f1"] + 0.10
    assert stress["candidate_v3_1"]["f1"] >= stress["production"]["f1"]
