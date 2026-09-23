from app.masking import mask_text, unmask_text
from proposals.detector_v3_15 import detect, detect_candidates, should_mask


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_personal_role_clauses_handle_inflection() -> None:
    assert pairs("Согласие от Орловой Елены Сергеевны получено.") == [
        ("PERSON", "Орловой Елены Сергеевны")
    ]
    assert pairs("Абонентский счёт оформлен на Каримова Рустама Ильдаровича.") == [
        ("PERSON", "Каримова Рустама Ильдаровича")
    ]


def test_personal_address_clauses_are_component_exact() -> None:
    home = "Мой домашний адрес: 630000, Новосибирск, улица Лесная, дом 7, квартира 14."
    assert pairs(home) == [
        ("ADDRESS_POSTAL_CODE", "630000"),
        ("ADDRESS_CITY", "Новосибирск"),
        ("ADDRESS_STREET", "Лесная"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "14"),
    ]
    residence = "Дом клиента находится во Владимире, на улице Горького, в доме 8, квартире 12."
    assert pairs(residence) == [
        ("ADDRESS_CITY", "Владимире"),
        ("ADDRESS_STREET", "Горького"),
        ("ADDRESS_HOUSE", "8"),
        ("ADDRESS_APARTMENT", "12"),
    ]
    assert pairs("Клиент сообщил, что живёт в Костроме.") == [
        ("ADDRESS_CITY", "Костроме")
    ]


def test_passport_and_birthplace_clause_variants() -> None:
    assert pairs("В форме: серия паспорта 4510 / номер 123456.") == [
        ("PASSPORT_RF", "серия паспорта 4510 / номер 123456")
    ]
    assert pairs("Место рождения по документу: рабочий посёлок Лесной Кировской области.") == [
        ("PLACE_OF_BIRTH", "рабочий посёлок Лесной Кировской области")
    ]
    assert pairs("Гражданин родом из г. Кимры.") == [("PLACE_OF_BIRTH", "г. Кимры")]


def test_issue_authority_and_date_are_document_owned() -> None:
    assert pairs("Паспорт оформило УМВД России по Кировской области.") == [
        ("PASSPORT_ISSUER", "УМВД России по Кировской области")
    ]
    assert pairs("Датой выдачи паспорта является 03.06.2014.") == [
        ("PASSPORT_ISSUE_DATE", "03.06.2014")
    ]


def test_public_clauses_are_rejected_by_policy() -> None:
    phone_text = "Секретарь подразделения отвечает по +7 495 777-20-30."
    phone = next(
        item for item in detect_candidates(phone_text) if item.entity.entity_type == "PHONE_RF"
    )
    assert should_mask(phone_text, phone) is False
    assert detect(phone_text) == []
    public_address = (
        "Для доставки выбран адрес магазина: Тула, улица Мира, дом 2. "
        "Получатель там не живёт."
    )
    assert detect(public_address) == []


def test_v3_15_round_trip_is_exact() -> None:
    text = (
        "Мой домашний адрес: 630000, Новосибирск, улица Лесная, дом 7; "
        "согласие от Орловой Елены Сергеевны."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
