import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_22 import DATASETS, compare_all
from proposals.detector_v3_22 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_22_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v13.json"


def test_v3_22_quality_and_precision_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v13 = report["sealed_holdout_v13.json"]
    assert v13["candidate_v3_22"]["f1"] > 0.80
    for comparison in report.values():
        assert (
            comparison["candidate_v3_22"]["precision"]
            >= comparison["production_v3_20"]["precision"]
        )


def test_v3_22_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_22_ocr_shadow_preserves_original_offsets() -> None:
    text = "ПAСПОРТ гражданки 6309482175 предъявлен лично."
    entities = detect(text)

    assert [(item.entity_type, item.text) for item in entities] == [
        ("PASSPORT_RF", "6309482175")
    ]
    assert text[entities[0].start : entities[0].end] == "6309482175"


def test_v3_22_clause_grammar_and_hard_negatives() -> None:
    personal = "Орган выдачи имеет код 150/208."
    public = "Доставить в офис: Ульяновск, улица Минаева, дом 11."
    technical = "Модель контроллера CVC-274 снята с производства."

    assert ("DIVISION_CODE", "150/208") in [
        (item.entity_type, item.text) for item in detect(personal)
    ]
    assert detect(public) == []
    assert detect(technical) == []


def test_v3_22_100k_token_p95_is_below_one_second() -> None:
    text = ("служебный " * 50_000) + "Телефон заявителя +7 999 123-45-67. "
    text += "служебный " * 50_000
    samples: list[float] = []
    for _ in range(10):
        started = time.perf_counter()
        entities = detect(text)
        samples.append(time.perf_counter() - started)

    assert ("PHONE_RF", "+7 999 123-45-67") in [
        (item.entity_type, item.text) for item in entities
    ]
    assert sorted(samples)[9] < 1.0
