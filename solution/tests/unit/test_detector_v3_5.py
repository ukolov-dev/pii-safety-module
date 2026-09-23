from app.masking import mask_text, unmask_text
from proposals.detector_v3_5 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_inflected_person_in_ownership_context() -> None:
    assert pairs("Договор заключён с Максимом Андреевичем Королёвым.") == [
        ("PERSON", "Максимом Андреевичем Королёвым")
    ]
    assert pairs("Школьники изучали образ Евгения Онегина.") == []


def test_dotted_card_requires_payment_context_and_luhn() -> None:
    assert pairs("Номер PAN карты: 4111.1111.1111.1111.") == [
        ("BANK_CARD", "4111.1111.1111.1111")
    ]
    assert pairs("В справочнике показан тестовый PAN 4111.1111.1111.1111.") == []


def test_document_and_issuing_authority_variants() -> None:
    text = "Паспорт 4510123456; код органа выдачи 770-123."
    assert pairs(text) == [
        ("PASSPORT_RF", "4510123456"),
        ("DIVISION_CODE", "770-123"),
    ]


def test_dates_use_semantic_context_and_reject_events() -> None:
    assert pairs("Пациентка появилась на свет 9 апреля 1999 года.") == [
        ("BIRTH_DATE", "9 апреля 1999 года")
    ]
    assert pairs("Музей открылся 9 апреля 1999 года.") == []


def test_address_chain_and_public_contact_suppression() -> None:
    text = "Домашний адрес: РФ, 300000, г. Тула, бульвар Мира, дом 8, кв. 4."
    assert pairs(text) == [
        ("ADDRESS_COUNTRY", "РФ"),
        ("ADDRESS_POSTAL_CODE", "300000"),
        ("ADDRESS_CITY", "Тула"),
        ("ADDRESS_STREET", "Мира"),
        ("ADDRESS_HOUSE", "8"),
        ("ADDRESS_APARTMENT", "4"),
    ]
    assert pairs("Общий адрес HR: hr@example.org.") == []


def test_cardholder_and_cvv_product_code_are_disambiguated() -> None:
    assert pairs("NAME ON CARD: ELENA ORLOVA.") == [
        ("CARDHOLDER_NAME", "ELENA ORLOVA")
    ]
    assert pairs("Артикул краски CVV2-731 нужен для поиска.") == []


def test_round_trip_is_exact_for_new_recognizers() -> None:
    text = (
        "Застрахованное лицо: Белова Мария Олеговна; "
        "PAN карты 4111.1111.1111.1111."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
