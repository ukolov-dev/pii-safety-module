from app.detection.detector_v3_28 import detect
from app.masking import mask_text, unmask_text


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_new_document_shapes_are_supported_without_literal_values() -> None:
    text = (
        "Водительское удостоверение: 61 КХ 918274; "
        "паспорт выдан: ОВМ УМВД России по Тюменской области."
    )

    found = pairs(text)
    assert ("DRIVER_LICENSE_RF", "61 КХ 918274") in found
    assert ("PASSPORT_ISSUER", "ОВМ УМВД России по Тюменской области") in found


def test_cyrillic_cardholder_and_personal_pin_fields() -> None:
    text = "Имя держателя карты: АННА СОКОЛОВА; ПИН-код карты клиента: 4826."

    found = pairs(text)
    assert ("CARDHOLDER_NAME", "АННА СОКОЛОВА") in found
    assert ("PIN", "4826") in found


def test_year_day_month_order_is_calendar_validated() -> None:
    valid = 'профиль["Дата рождения"]="1997.24.08"'
    invalid = 'профиль["Дата рождения"]="1997.35.18"'

    assert ("BIRTH_DATE", "1997.24.08") in pairs(valid)
    assert ("BIRTH_DATE", "1997.35.18") not in pairs(invalid)


def test_address_component_spans_exclude_semantic_designators() -> None:
    text = (
        "Адрес регистрации: Беларусь, 625013, г. Тюмень, проспект Геологоразведчиков, "
        "владение 14А, квартира № 82."
    )

    found = pairs(text)
    assert ("ADDRESS_COUNTRY", "Беларусь") in found
    assert ("ADDRESS_CITY", "Тюмень") in found
    assert ("ADDRESS_STREET", "Геологоразведчиков") in found
    assert ("ADDRESS_HOUSE", "14А") in found
    assert ("ADDRESS_APARTMENT", "82") in found
    assert not any(value.startswith(("проспект ", "владение ", "квартира ")) for _, value in found)


def test_technical_numbers_and_public_house_are_not_masked() -> None:
    assert pairs("timeout=625013 задаёт число микросекунд.") == []
    assert pairs("Дом 7 считается памятником архитектуры.") == []


def test_v328_spans_round_trip_exactly() -> None:
    text = 'профиль["Имя держателя карты"]="ЕЛЕНА БЕЛОВА"; ВУ 72 МН 192837.'
    entities = detect(text)

    assert all(text[entity.start : entity.end] == entity.text for entity in entities)
    masked = mask_text(text, entities)
    assert unmask_text(masked.text, masked.mapping) == text
