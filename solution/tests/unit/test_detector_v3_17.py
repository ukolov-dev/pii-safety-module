from app.masking import mask_text, unmask_text
from proposals.detector_v3_17 import detect, detect_candidates, should_mask


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_person_semantic_families_are_inflection_aware() -> None:
    assert pairs("Полис принадлежит Артёму Николаевичу Зуеву.") == [
        ("PERSON", "Артёму Николаевичу Зуеву")
    ]
    assert pairs("От имени несовершеннолетнего действует Елена Сергеевна Орлова.") == [
        ("PERSON", "Елена Сергеевна Орлова")
    ]
    assert pairs("ФИО клиента по заявке: СИДОРОВ ПАВЕЛ АНДРЕЕВИЧ.") == [
        ("PERSON", "СИДОРОВ ПАВЕЛ АНДРЕЕВИЧ")
    ]


def test_residence_clauses_extract_complete_address() -> None:
    home = "Это адрес, где я живу: 630000, Новосибирск, улица Лесная, дом 7, квартира 14."
    assert pairs(home) == [
        ("ADDRESS_POSTAL_CODE", "630000"),
        ("ADDRESS_CITY", "Новосибирск"),
        ("ADDRESS_STREET", "Лесная"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "14"),
    ]
    registration = "Я прописан во Владимире по улице Горького, в доме 8, квартире 12."
    assert pairs(registration) == [
        ("ADDRESS_CITY", "Владимире"),
        ("ADDRESS_STREET", "Горького"),
        ("ADDRESS_HOUSE", "8"),
        ("ADDRESS_APARTMENT", "12"),
    ]


def test_document_and_owned_payment_fields() -> None:
    assert pairs("В документе указаны серия 4510 и паспортный номер 123456.") == [
        ("PASSPORT_RF", "серия 4510 и паспортный номер 123456")
    ]
    assert pairs("Поле КП заполнено значением 770/321.") == [
        ("DIVISION_CODE", "770/321")
    ]
    assert pairs("Место рождения клиента: г. Кимры.") == [
        ("PLACE_OF_BIRTH", "г. Кимры")
    ]
    assert pairs("В поле гражданства указано: Россия.") == [
        ("CITIZENSHIP", "Россия")
    ]
    assert pairs("ПИН, заданный самим владельцем: 4826.") == [("PIN", "4826")]


def test_cardholder_and_public_contact_policy() -> None:
    assert pairs("На пластике владельца выбито MARIA BELOVA.") == [
        ("CARDHOLDER_NAME", "MARIA BELOVA")
    ]
    public = "Контакт диспетчера аэропорта: +7 (495) 777-20-30."
    phone = next(
        item for item in detect_candidates(public) if item.entity.entity_type == "PHONE_RF"
    )
    assert should_mask(public, phone) is False
    assert detect(public) == []


def test_invalid_card_and_equipment_passport_are_rejected() -> None:
    assert pairs("Номер карты 5555555555554451 имеет неверную контрольную сумму.") == []
    assert pairs("Паспорт промышленной установки имеет номер 45 10 123456.") == []


def test_v3_17_round_trip_is_exact() -> None:
    text = (
        "Я прописан во Владимире по улице Горького, в доме 8; "
        "полис принадлежит Артёму Николаевичу Зуеву."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
