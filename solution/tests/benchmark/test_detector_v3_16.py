import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_16 import DATASETS, compare_all
from proposals.detector_v3_16 import NERSpan, detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_16_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v10.json"
    assert all("v11" not in filename for filename in DATASETS)


def test_v3_16_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v10 = report["sealed_holdout_v10.json"]
    assert v10["candidate_v3_16"]["f1"] >= v10["production_v3_13"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_16"]["precision"]
            >= comparison["production_v3_13"]["precision"]
        )


def test_v3_16_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_16_precision_safe_semantics() -> None:
    personal = "Договор оформлен на Власову Ирину Павловну."
    address = "Мой домашний адрес: 630000, Новосибирск, улица Лесная, дом 8."
    public = "Контакты выставочного центра: expo@hall.example, +7 495 123-45-67."

    assert [(item.entity_type, item.text) for item in detect(personal)] == [
        ("PERSON", "Власову Ирину Павловну")
    ]
    assert ("ADDRESS_CITY", "Новосибирск") in [
        (item.entity_type, item.text) for item in detect(address)
    ]
    assert detect(public) == []


def test_v3_16_optional_ner_is_confidence_and_context_gated() -> None:
    text = "Домашний адрес клиента: Тула, улица Мира, дом 5."
    value = "Тула"
    start = text.index(value)
    accepted = NERSpan("CITY", start, start + len(value), 0.97)
    rejected = NERSpan("CITY", start, start + len(value), 0.80)

    assert ("ADDRESS_CITY", value) in [
        (item.entity_type, item.text) for item in detect(text, [accepted])
    ]
    assert all(item.source != "ner_gated_v3_16" for item in detect(text, [rejected]))


def test_v3_16_lightweight_latency_guard() -> None:
    text = "Домашний адрес клиента: 630000, Новосибирск, улица Лесная, дом 8."
    started = time.perf_counter()
    for _ in range(1_000):
        detect(text)
    assert time.perf_counter() - started < 5.0
