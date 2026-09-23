from app.detection.detector_v3_30 import detect
from app.masking import mask_text, unmask_text


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_labelled_prose_records_use_value_shapes_not_value_dictionaries() -> None:
    text = (
        "Клиент родился 1988-02-29 в Новомосковск; "
        "доставка: страна Россия, индекс 301650, город Новомосковск, "
        "улица Береговая, дом 17Б, квартира 204."
    )

    found = pairs(text)
    assert ("PLACE_OF_BIRTH", "Новомосковск") in found
    assert ("ADDRESS_CITY", "Новомосковск") in found
    assert ("ADDRESS_HOUSE", "17Б") in found


def test_passport_and_ocr_records_keep_exact_field_boundaries() -> None:
    prose = (
        "Паспорт 45 12 345678, выдан ОВМ УМВД России по Тульской области "
        "29.02.2024, код подразделения 710-004."
    )
    ocr = (
        "ПАСП0РТ:45-13-654321\nК0Д П0ДРАЗДЕЛЕНИЯ:710-009\n"
        "ВЫДАН:Отделом МВД России по району Восточный\nДАТА:01/03/2024"
    )

    assert ("PASSPORT_ISSUER", "ОВМ УМВД России по Тульской области") in pairs(prose)
    assert ("DIVISION_CODE", "710-009") in pairs(ocr)
    assert ("PASSPORT_RF", "45-13-654321") in pairs(ocr)


def test_payment_fields_require_a_valid_card_checksum() -> None:
    valid = (
        "payment.card=5555 5555 5555 4444\ncard.holder=ИВАН ПЕТРОВ\n"
        "security.cvv=527\nsecurity.pin=6041"
    )
    invalid = valid.replace("4444", "4445")

    assert ("BANK_CARD", "5555 5555 5555 4444") in pairs(valid)
    assert ("CARDHOLDER_NAME", "ИВАН ПЕТРОВ") in pairs(valid)
    assert ("BANK_CARD", "5555 5555 5555 4445") not in pairs(invalid)


def test_public_test_card_is_not_masked() -> None:
    assert pairs("Публичная тестовая карта 5555 5555 5555 4444.") == []


def test_v330_spans_round_trip_exactly() -> None:
    text = (
        "{user:'Морозов Илья Максимович', birthplace:'Дмитров', "
        "dl:'77 28 654321', address:{zip:'141800', city:'Клин', "
        "street:'Северная', house:'19А', apt:'83'}}"
    )
    entities = detect(text)

    assert all(text[entity.start : entity.end] == entity.text for entity in entities)
    masked = mask_text(text, entities)
    assert unmask_text(masked.text, masked.mapping) == text
