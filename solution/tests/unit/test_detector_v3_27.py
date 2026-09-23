from app.detection.detector_v3_27 import detect
from app.masking import mask_text, unmask_text


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_inflected_owned_person_is_extracted_without_leading_verb() -> None:
    text = "Обращение зарегистрировано от Тимофея Аркадьевича Белова."

    assert ("PERSON", "Тимофея Аркадьевича Белова") in pairs(text)
    assert not any(value.startswith("от ") for _, value in pairs(text))


def test_owned_address_record_supports_compound_city_and_abbreviations() -> None:
    text = (
        "Адрес регистрации заявителя: 625000, Верхняя Пышма, "
        "улица Осенняя, д. 14Б, кв. 63."
    )

    found = pairs(text)
    assert ("ADDRESS_POSTAL_CODE", "625000") in found
    assert ("ADDRESS_CITY", "Верхняя Пышма") in found
    assert ("ADDRESS_STREET", "Осенняя") in found
    assert ("ADDRESS_HOUSE", "14Б") in found
    assert ("ADDRESS_APARTMENT", "63") in found


def test_reordered_passport_and_cross_clause_issue_date_are_detected() -> None:
    text = (
        "В анкете: серия 4512 и номер паспорта 734981; "
        "выдан ОМВД России по г. Твери; дата 17.08.2020."
    )

    found = pairs(text)
    assert ("PASSPORT_RF", "серия 4512 и номер паспорта 734981") in found
    assert ("PASSPORT_ISSUE_DATE", "17.08.2020") in found


def test_public_and_technical_identifiers_are_suppressed() -> None:
    texts = (
        "Поставщики пишут на vendors@factory.example.",
        "SDK DEMO показывает карту 4111-1111-1111-1111 и CVV 123.",
        "Паспорт агрегата имеет номер 49 11 620735.",
        "Адрес партнёра: Курск, улица Мира, дом 8.",
    )

    assert all(pairs(text) == [] for text in texts)


def test_candidate_keeps_exact_offsets_and_round_trip() -> None:
    text = (
        "Доставка домой: 644000, Омск, улица Учебная, д. 7, кв. 21; "
        "тел. +7 (913) 555-42-10."
    )

    entities = detect(text)
    assert all(text[entity.start : entity.end] == entity.text for entity in entities)
    masked = mask_text(text, entities)
    assert unmask_text(masked.text, masked.mapping) == text
