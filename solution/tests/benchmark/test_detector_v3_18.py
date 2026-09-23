import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_18 import DATASETS, compare_all
from proposals.detector_v3_18 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_18_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v11.json"
    assert all("v12" not in filename for filename in DATASETS)


def test_v3_18_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v11 = report["sealed_holdout_v11.json"]
    assert v11["candidate_v3_18"]["f1"] >= v11["production_v3_13"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_18"]["precision"]
            >= comparison["production_v3_13"]["precision"]
        )


def test_v3_18_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_18_cross_sentence_address_and_role_name() -> None:
    name_text = "Счёт принадлежит Анне Викторовне Соколовой."
    address_text = "Курьеру нужен мой адрес. Сообщаю: Тула, улица Мира, дом 5."

    assert [(item.entity_type, item.text) for item in detect(name_text)] == [
        ("PERSON", "Анне Викторовне Соколовой")
    ]
    assert ("ADDRESS_CITY", "Тула") in [
        (item.entity_type, item.text) for item in detect(address_text)
    ]


def test_v3_18_public_and_invalid_values_are_suppressed() -> None:
    public = "Контакты культурного центра: culture@center.example, +7 812 700-20-30."
    invalid = "Номер карты 5555555555554451 имеет неверную контрольную сумму."

    assert detect(public) == []
    assert detect(invalid) == []


def test_v3_18_lightweight_latency_guard() -> None:
    text = "Мой адрес: 630000, Новосибирск, улица Лесная, дом 8, квартира 4."
    started = time.perf_counter()
    for _ in range(1_000):
        detect(text)
    assert time.perf_counter() - started < 5.0
