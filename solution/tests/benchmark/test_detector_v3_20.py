import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_20 import DATASETS, compare_all
from proposals.detector_v3_20 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_20_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v12.json"


def test_v3_20_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v12 = report["sealed_holdout_v12.json"]
    assert v12["candidate_v3_20"]["f1"] >= v12["production_v3_13"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_20"]["precision"]
            >= comparison["production_v3_13"]["precision"]
        )


def test_v3_20_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_20_scores_owned_weak_fields() -> None:
    text = "Это мои данные: страна проживания РФ, улица регистрации Тверская, дом 7."
    entities = {(item.entity_type, item.text) for item in detect(text)}

    assert ("ADDRESS_COUNTRY", "РФ") in entities
    assert ("ADDRESS_STREET", "Тверская") in entities
    assert ("ADDRESS_HOUSE", "7") in entities


def test_v3_20_suppresses_public_and_technical_values() -> None:
    public = "Адрес кинотеатра: Россия, город Омск, улица Мира, дом 5."
    technical = "Тестовый CVC компонента равен 123."

    assert detect(public) == []
    assert detect(technical) == []


def test_v3_20_lightweight_latency_guard() -> None:
    text = "Мой адрес: 630000, Новосибирск, улица Лесная, дом 8, квартира 4."
    started = time.perf_counter()
    for _ in range(1_000):
        detect(text)
    assert time.perf_counter() - started < 5.0
