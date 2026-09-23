import json
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_6 import DATASETS, compare_all
from proposals.detector_v3_6 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_6_declares_only_disclosed_datasets() -> None:
    assert DATASETS == (
        "quality_dataset.json",
        "adversarial_dataset.json",
        "blind_holdout_v3.json",
        "false_positive_stress_v3.json",
        "sealed_holdout_v4.json",
        "sealed_holdout_v5.json",
    )


def test_v3_6_improves_v5_by_ten_points_without_more_false_positives() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v5 = report["sealed_holdout_v5.json"]
    assert v5["candidate_v3_6"]["f1"] >= v5["production_v3_3"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_6"]["false_positive"]
            <= comparison["production_v3_3"]["false_positive"]
        )


def test_v3_6_masking_round_trip_on_all_disclosed_cases() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_6_generic_recall_examples_and_document_suppression() -> None:
    person = "Договор заключён с Иваном Сергеевичем Петровым."
    payment = "PAN карты клиента: 4111.1111.1111.1111."
    documentation = "Инструкция: код подразделения 770-001 является примером."

    assert [(item.entity_type, item.text) for item in detect(person)] == [
        ("PERSON", "Иваном Сергеевичем Петровым")
    ]
    assert [(item.entity_type, item.text) for item in detect(payment)] == [
        ("BANK_CARD", "4111.1111.1111.1111")
    ]
    assert detect(documentation) == []
