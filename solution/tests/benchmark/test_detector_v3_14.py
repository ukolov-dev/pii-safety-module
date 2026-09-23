import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_14 import DATASETS, compare_all
from proposals.detector_v3_14 import NERSpan, detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_14_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v9.json"
    assert all("v10" not in filename for filename in DATASETS)


def test_v3_14_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v9 = report["sealed_holdout_v9.json"]
    assert v9["candidate_v3_14"]["f1"] >= v9["production_v3_3"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_14"]["precision"] >= comparison["production_v3_3"]["precision"]
        )


def test_v3_14_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_14_optional_ner_is_ownership_gated() -> None:
    personal = "Заявитель: Чижов Олег Валерьевич."
    public = "Статья посвящена поэту Чижову Олегу Валерьевичу."
    personal_value = "Чижов Олег Валерьевич"
    public_value = "Чижову Олегу Валерьевичу"

    start = personal.index(personal_value)
    span = NERSpan("PERSON", start, start + len(personal_value), 0.97)
    assert ("PERSON", personal_value) in [
        (item.entity_type, item.text) for item in detect(personal, [span])
    ]

    start = public.index(public_value)
    span = NERSpan("PERSON", start, start + len(public_value), 0.99)
    assert detect(public, [span]) == []


def test_v3_14_lightweight_path_latency_guard() -> None:
    text = "Клиент Смирнов Антон Павлович живёт: Москва, улица Лесная, дом 7."
    started = time.perf_counter()
    for _ in range(1_000):
        detect(text)
    assert time.perf_counter() - started < 5.0
