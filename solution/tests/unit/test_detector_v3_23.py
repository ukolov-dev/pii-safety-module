from app.masking import mask_text, unmask_text
from proposals.detector_v3_23 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_ocr_separators_preserve_exact_spans() -> None:
    text = "ТЕЛЕФОН / клиента / +7|962|407|35|18"
    assert pairs(text) == [("PHONE_RF", "+7|962|407|35|18")]
    assert pairs("ДАТА РОЖД. | 23·09·1982") == [("BIRTH_DATE", "23·09·1982")]


def test_normalized_document_fields() -> None:
    text = (
        "ПАСПОРТ\n"
        "серия/номер: 53 17 806241\n"
        "выдан: ГУ МВД России по Новгородской области\n"
        "дата: 12.08.2019\n"
        "код: 530-015"
    )
    assert pairs(text) == [
        ("PASSPORT_RF", "53 17 806241"),
        ("PASSPORT_ISSUER", "ГУ МВД России по Новгородской области"),
        ("PASSPORT_ISSUE_DATE", "12.08.2019"),
        ("DIVISION_CODE", "530-015"),
    ]


def test_address_record_parser_handles_pipes_and_multiline_fields() -> None:
    text = "OCR>>АДРЕС|РФ|625000|Тюмень|ул. Республики|д. 62|кв. 13"
    assert pairs(text) == [
        ("ADDRESS_COUNTRY", "РФ"),
        ("ADDRESS_POSTAL_CODE", "625000"),
        ("ADDRESS_CITY", "Тюмень"),
        ("ADDRESS_STREET", "Республики"),
        ("ADDRESS_HOUSE", "62"),
        ("ADDRESS_APARTMENT", "13"),
    ]


def test_record_fields_do_not_override_public_or_technical_evidence() -> None:
    assert pairs("SDK_SAMPLE|PAN=4111111111111111|CVV=123|PUBLIC_TEST=true") == []
    assert pairs("PUBLIC_ADDRESS>>Орёл|улица Лескова|дом 23") == []
    assert pairs("Пустая анкета\nФИО: ______\nДата рождения: ______") == []


def test_mixed_public_and_personal_contacts_use_nearest_field() -> None:
    text = "Телефон офиса +7 495 600-10-20. Но номер самого клиента — 8-905-714-32-86."
    assert pairs(text) == [("PHONE_RF", "8-905-714-32-86")]


def test_birthplace_and_current_city_remain_distinct() -> None:
    text = (
        "Я родился в посёлке Соловецкий Архангельской области. Теперь живу в городе Архангельске."
    )
    assert pairs(text) == [
        ("PLACE_OF_BIRTH", "посёлке Соловецкий Архангельской области"),
        ("ADDRESS_CITY", "Архангельске"),
    ]


def test_v3_23_round_trip_is_exact() -> None:
    text = "CARDHOLDER_NAME=MIKHAIL TROFIMOV|PIN=4702|CVV=583"
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
