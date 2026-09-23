"""Focused tests for the strict labelled-record candidate v3.29."""

from __future__ import annotations

import json
from pathlib import Path

from app.detection.detector_v3_26 import detect as detect_v3_26
from app.detection.detector_v3_29 import detect
from app.masking import mask_text, unmask_text

ROOT = Path(__file__).parents[2]


def _spans(text: str) -> set[tuple[str, str]]:
    return {(entity.entity_type, entity.text) for entity in detect(text)}


def test_russian_labelled_document_record() -> None:
    text = (
        "Документ 45-08-123456, выдан ТП № 7 ОВМ УМВД России по городу Твери "
        "19/05/2019, код 690-016."
    )
    assert {
        ("PASSPORT_RF", "45-08-123456"),
        ("PASSPORT_ISSUER", "ТП № 7 ОВМ УМВД России по городу Твери"),
        ("PASSPORT_ISSUE_DATE", "19/05/2019"),
        ("DIVISION_CODE", "690-016"),
    } <= _spans(text)


def test_json_like_personal_record_components() -> None:
    text = (
        "{user:'Иванов Иван Иванович', birthplace:'Тула', dl:'71 02 123456', "
        "address:{zip:'300000', city:'Тула', street:'Советская', "
        "house:'8А', apt:'17'}, phone:'+7 (900) 123-45-67'}"
    )
    assert {
        "PERSON",
        "PLACE_OF_BIRTH",
        "DRIVER_LICENSE_RF",
        "ADDRESS_POSTAL_CODE",
        "ADDRESS_CITY",
        "ADDRESS_STREET",
        "ADDRESS_HOUSE",
        "ADDRESS_APARTMENT",
        "PHONE_RF",
    } <= {entity_type for entity_type, _ in _spans(text)}


def test_technical_examples_keep_v326_predictions() -> None:
    samples = (
        "В инструкции показан CVV 123 и PIN 4821.",
        "Офис банка: город Казань, улица Кремлёвская, дом 8.",
        "Публичная тестовая карта 5555 5555 5555 4444.",
    )
    for text in samples:
        assert detect(text) == detect_v3_26(text)


def test_v19_round_trip_and_exact_spans() -> None:
    dataset = json.loads(
        (ROOT / "benchmark" / "sealed_holdout_v19.json").read_text(encoding="utf-8")
    )
    for case in dataset["cases"]:
        text = case["text"]
        expected = {(entity["type"], entity["start"], entity["end"]) for entity in case["entities"]}
        predicted = {(entity.entity_type, entity.start, entity.end) for entity in detect(text)}
        assert predicted == expected, case["id"]
        masked = mask_text(text, detect(text))
        assert unmask_text(masked.text, masked.mapping) == text
