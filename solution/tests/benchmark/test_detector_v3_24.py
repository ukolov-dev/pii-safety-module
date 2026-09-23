import json
import time
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_24 import DATASETS, compare_all
from proposals.detector_v3_24 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_24_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v14.json"


def test_v3_24_quality_and_precision_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    disclosed = report["sealed_holdout_v14.json"]
    assert disclosed["candidate_v3_24"]["f1"] > 0.80
    for comparison in report.values():
        assert (
            comparison["candidate_v3_24"]["precision"]
            >= comparison["production_v3_20"]["precision"]
        )


def test_v3_24_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_24_ocr_separators_and_inflection() -> None:
    text = "ТЕЛЕФОН / клиента / +7|962|407|35|18; ДАТА РОЖД. | 23·09·1982"
    entities = {(item.entity_type, item.text) for item in detect(text)}

    assert ("PHONE_RF", "+7|962|407|35|18") in entities
    assert ("BIRTH_DATE", "23·09·1982") in entities


def test_v3_24_multiline_record_association() -> None:
    text = "Доставка физлицу:\n302000, Орёл\nул. Октябрьская, д. 48, кв. 91"
    entities = {(item.entity_type, item.text) for item in detect(text)}

    assert ("ADDRESS_CITY", "Орёл") in entities
    assert ("ADDRESS_STREET", "Октябрьская") in entities
    assert ("ADDRESS_HOUSE", "48") in entities
    assert ("ADDRESS_APARTMENT", "91") in entities


def test_v3_24_hard_negative_suppression() -> None:
    texts = (
        "Адрес стадиона — Саранск, улица Победы, дом 5.",
        "SDK_SAMPLE|PAN=4111111111111111|CVV=123|PUBLIC_TEST=true",
        "Это общий номер дежурной смены: +7-383-604-27-15.",
    )

    assert all(detect(text) == [] for text in texts)


def test_v3_24_100k_token_p95_is_below_one_second() -> None:
    text = ("служебный " * 50_000) + "Телефон заявителя +7 999 123-45-67. "
    text += "служебный " * 50_000
    samples: list[float] = []
    for _ in range(10):
        started = time.perf_counter()
        entities = detect(text)
        samples.append(time.perf_counter() - started)

    assert ("PHONE_RF", "+7 999 123-45-67") in [(item.entity_type, item.text) for item in entities]
    assert sorted(samples)[9] < 1.0
