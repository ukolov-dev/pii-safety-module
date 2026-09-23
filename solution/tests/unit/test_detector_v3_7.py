from app.masking import mask_text, unmask_text
from proposals.detector_v3_7 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_person_ownership_phrases_and_wrapped_email() -> None:
    text = "Заявление поступило от Крыловой Анны Сергеевны."
    assert pairs(text) == [("PERSON", "Крыловой Анны Сергеевны")]
    assert pairs("Ф.И.О. пациента — Нуриев Тимур Рашидович.") == [
        ("PERSON", "Нуриев Тимур Рашидович")
    ]
    assert pairs("Email клиента: `olga.petrov@example.org`.") == [
        ("EMAIL", "olga.petrov@example.org")
    ]


def test_personal_identifiers_require_valid_shape_and_context() -> None:
    assert pairs("Мой налоговый идентификатор: 500100732259.") == [
        ("INN", "500100732259")
    ]
    assert pairs("Оплата физлица, карта 4111/1111/1111/1111.") == [
        ("BANK_CARD", "4111/1111/1111/1111")
    ]
    assert pairs("В каталоге шаблон 4111/1111/1111/1111.") == []


def test_document_birth_and_license_variants() -> None:
    text = "Серия документа 45 10, номер 123456; КП паспорта 770/321."
    assert pairs(text) == [
        ("PASSPORT_RF", "Серия документа 45 10, номер 123456"),
        ("DIVISION_CODE", "770/321"),
    ]
    assert pairs("Д/р заёмщика: 1988-12-03.") == [("BIRTH_DATE", "1988-12-03")]
    assert pairs("Водительские права гражданина: 77 11 654321.") == [
        ("DRIVER_LICENSE_RF", "77 11 654321")
    ]


def test_semantic_fields_and_address_chain() -> None:
    assert pairs("Место появления на свет: деревня Берёзовка.") == [
        ("PLACE_OF_BIRTH", "деревня Берёзовка")
    ]
    address = (
        "Для доставки мне домой: Россия, 443000, Самара, "
        "улица Садовая, дом 12, квартира 9."
    )
    assert pairs(address) == [
        ("ADDRESS_COUNTRY", "Россия"),
        ("ADDRESS_POSTAL_CODE", "443000"),
        ("ADDRESS_CITY", "Самара"),
        ("ADDRESS_STREET", "Садовая"),
        ("ADDRESS_HOUSE", "12"),
        ("ADDRESS_APARTMENT", "9"),
    ]


def test_payment_secrets_and_non_person_suppression() -> None:
    assert pairs("Секретный код CVC карты заказчика: 391; PIN равен 2468.") == [
        ("CVV", "391"),
        ("PIN", "2468"),
    ]
    assert pairs("Имя на пластике: IRINA VOLKOVA.") == [
        ("CARDHOLDER_NAME", "IRINA VOLKOVA")
    ]
    assert pairs("Телефон кассы филармонии +7 (495) 111-22-33.") == []
    assert pairs("Поля «место рождения» и «код подразделения» не заполнены.") == []
    assert pairs("Модель датчика CVC-391 указана в каталоге.") == []


def test_v3_7_round_trip_is_exact() -> None:
    text = (
        "Email клиента: `olga.petrov@example.org`; "
        "карта 4111/1111/1111/1111."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
