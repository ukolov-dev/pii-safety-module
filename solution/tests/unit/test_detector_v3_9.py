from app.masking import mask_text, unmask_text
from proposals.detector_v3_9 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_person_grammar_uses_strong_ownership_roles() -> None:
    assert pairs("Договор подписан Максимом Андреевичем Королёвым лично.") == [
        ("PERSON", "Максимом Андреевичем Королёвым")
    ]
    assert pairs("Автор жалобы — Белова Мария Олеговна.") == [
        ("PERSON", "Белова Мария Олеговна")
    ]


def test_new_card_document_and_birth_variants() -> None:
    assert pairs("Личная дебетовая карта: 4012/8888/8888/1881.") == [
        ("BANK_CARD", "4012/8888/8888/1881")
    ]
    assert pairs("Код выдавшего органа: 770 123.") == [
        ("DIVISION_CODE", "770 123")
    ]
    assert pairs("Рождение клиента: 1990/01/02.") == [
        ("BIRTH_DATE", "1990/01/02")
    ]


def test_semantic_document_fields_are_span_exact() -> None:
    assert pairs("Место рождения заявителя: село Никольское Тверской области.") == [
        ("PLACE_OF_BIRTH", "село Никольское Тверской области")
    ]
    assert pairs("Гражданская принадлежность клиента: Республика Беларусь.") == [
        ("CITIZENSHIP", "Республика Беларусь")
    ]
    issuer = "Паспорт оформлен УМВД России по Ленинскому району г. Кирова."
    assert pairs(issuer) == [
        ("PASSPORT_ISSUER", "УМВД России по Ленинскому району г. Кирова")
    ]


def test_address_and_payment_labels_are_composable() -> None:
    address = (
        "Адрес проживания клиента: Россия; 630000; Новосибирск; "
        "улица Лесная; дом 7; квартира 14."
    )
    assert pairs(address) == [
        ("ADDRESS_COUNTRY", "Россия"),
        ("ADDRESS_POSTAL_CODE", "630000"),
        ("ADDRESS_CITY", "Новосибирск"),
        ("ADDRESS_STREET", "Лесная"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "14"),
    ]
    assert pairs("Личный ПИН-код владельца: 4826.") == [("PIN", "4826")]
    assert pairs("CARDHOLDER / владелец пластика: MARIA BELOVA.") == [
        ("CARDHOLDER_NAME", "MARIA BELOVA")
    ]


def test_public_shared_and_non_person_values_are_suppressed() -> None:
    assert pairs("Телефон диспетчерской службы: +7 (812) 777-30-50.") == []
    assert pairs("Это корпоративная почта отдела: team@company.example.") == []
    assert pairs("Адрес библиотеки — 630000, Новосибирск, улица Советская, дом 4.") == []
    assert pairs("Деталь с маркировкой CVV-381 стоит в насосе.") == []
    assert pairs("Подсказка формы: дата рождения 02.01.1990.") == []


def test_v3_9_round_trip_is_exact() -> None:
    text = (
        "Личная дебетовая карта: 4012/8888/8888/1881; "
        "CARDHOLDER / владелец пластика: MARIA BELOVA."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
