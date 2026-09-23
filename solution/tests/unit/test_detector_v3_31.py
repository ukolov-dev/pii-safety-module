"""Focused tests for the isolated schema-aware v3.31 candidate."""

from __future__ import annotations

from app.detection.detector_v3_31 import detect


def _keys(text: str) -> set[tuple[str, str]]:
    return {(entity.entity_type, entity.text) for entity in detect(text)}


def test_json_schema_values_are_detected_without_value_dictionaries() -> None:
    text = (
        '{{"customer":"Егорова Дарья Матвеевна","birth":"17.08.1988",'
        '"passport":"4519 603827","phone":"79161234567"}}'
    )

    assert {
        ("PERSON", "Егорова Дарья Матвеевна"),
        ("BIRTH_DATE", "17.08.1988"),
        ("PASSPORT_RF", "4519 603827"),
        ("PHONE_RF", "79161234567"),
    } <= _keys(text)


def test_config_aliases_are_typed_by_their_labels() -> None:
    text = (
        "owner=Егорова Дарья Матвеевна\n"
        "license_rf=77 11 234567\n"
        "contact_email=d.egorova@example.net\n"
        "mobile=+7 (916) 123-45-67"
    )

    assert {
        ("DRIVER_LICENSE_RF", "77 11 234567"),
        ("EMAIL", "d.egorova@example.net"),
        ("PHONE_RF", "+7 (916) 123-45-67"),
    } <= _keys(text)


def test_issuer_ocr_line_keeps_full_agency_span() -> None:
    text = "ПАСПОРТ РФ\nВЫДАН ОВМ УМВД России по г. Томску\nДАТА ВЫДАЧИ 10.09.2019"

    assert ("PASSPORT_ISSUER", "ОВМ УМВД России по г. Томску") in _keys(text)


def test_public_contacts_are_not_reintroduced_by_schema_parser() -> None:
    text = "EMAIL=author@company.example\nOWNER=корпоративный отдел\nphone=+7 495 730-48-59"

    assert not ({"EMAIL", "PHONE_RF"} & {entity.entity_type for entity in detect(text)})


def test_invalid_calendar_date_is_rejected() -> None:
    text = '{{"customer":"Егорова Дарья Матвеевна","birth":"31.02.2020"}}'

    assert "BIRTH_DATE" not in {entity.entity_type for entity in detect(text)}
