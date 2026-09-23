import json
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_8 import DATASETS, compare_all
from proposals.detector_v3_8 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_8_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v6.json"
    assert all("v7" not in filename for filename in DATASETS)


def test_v3_8_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v6 = report["sealed_holdout_v6.json"]
    assert v6["candidate_v3_8"]["f1"] >= v6["production_v3_3"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_8"]["precision"]
            >= comparison["production_v3_3"]["precision"]
        )


def test_v3_8_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_8_general_personal_and_public_ownership() -> None:
    personal = "Заявление поступило от Ирины Сергеевны Волковой."
    public = "Номер секретариата завода +7 (831) 250-60-70 опубликован открыто."
    slash_card = "Номер личной карты: 4111/1111/1111/1111."

    assert [(item.entity_type, item.text) for item in detect(personal)] == [
        ("PERSON", "Ирины Сергеевны Волковой")
    ]
    assert detect(public) == []
    assert [(item.entity_type, item.text) for item in detect(slash_card)] == [
        ("BANK_CARD", "4111/1111/1111/1111")
    ]
