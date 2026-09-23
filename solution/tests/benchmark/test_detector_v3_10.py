import json
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_10 import DATASETS, compare_all
from proposals.detector_v3_10 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_10_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v7.json"
    assert all("v8" not in filename for filename in DATASETS)


def test_v3_10_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v7 = report["sealed_holdout_v7.json"]
    assert v7["candidate_v3_10"]["f1"] >= v7["production_v3_3"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_10"]["precision"]
            >= comparison["production_v3_3"]["precision"]
        )


def test_v3_10_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_10_general_context_and_calendar_rules() -> None:
    person = "Договор подписан Петровой Анной Игоревной."
    license_text = "Водительские права имеют реквизиты 5019-123456."
    public = "Адрес склада, не клиента: Тула, улица Ленина, дом 7."
    impossible_date = "Дата рождения: 31.02.2020."

    assert [(item.entity_type, item.text) for item in detect(person)] == [
        ("PERSON", "Петровой Анной Игоревной")
    ]
    assert [(item.entity_type, item.text) for item in detect(license_text)] == [
        ("DRIVER_LICENSE_RF", "5019-123456")
    ]
    assert detect(public) == []
    assert detect(impossible_date) == []
