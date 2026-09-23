from app.masking import mask_text, unmask_text
from proposals.detector_v3_11 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_role_owned_person_and_wrapped_email() -> None:
    assert pairs("Претензия составлена Ковалёвой Инной Романовной.") == [
        ("PERSON", "Ковалёвой Инной Романовной")
    ]
    assert pairs("Доверителем является Воронов Пётр Семёнович.") == [
        ("PERSON", "Воронов Пётр Семёнович")
    ]
    assert pairs("EMAIL владельца профиля: {user.name@Example.ONLINE}.") == [
        ("EMAIL", "user.name@Example.ONLINE")
    ]


def test_document_labels_and_textual_issue_date() -> None:
    assert pairs("Идентификация выполнена по паспорту гражданки: 4510123456.") == [
        ("PASSPORT_RF", "4510123456")
    ]
    assert pairs("Подразделение выдачи паспорта: 770/321.") == [
        ("DIVISION_CODE", "770/321")
    ]
    assert pairs("Паспорт был выдан двадцать третьего мая 2020 года.") == [
        ("PASSPORT_ISSUE_DATE", "двадцать третьего мая 2020 года")
    ]


def test_place_citizenship_issuer_and_license_labels() -> None:
    assert pairs("Родной населённый пункт: аул Новая Жизнь.") == [
        ("PLACE_OF_BIRTH", "аул Новая Жизнь")
    ]
    assert pairs("Поле «гражданство клиента»: Республика Беларусь.") == [
        ("CITIZENSHIP", "Республика Беларусь")
    ]
    assert pairs("Выдавший орган: УМВД России по Кировской области.") == [
        ("PASSPORT_ISSUER", "УМВД России по Кировской области")
    ]
    assert pairs("Реквизиты водительских прав: 77 11 654321.") == [
        ("DRIVER_LICENSE_RF", "77 11 654321")
    ]


def test_pipe_address_and_payment_labels() -> None:
    address = (
        "Домашний адрес клиента: Россия | 630000 | Новосибирск | "
        "улица Лесная | дом 7 | квартира 14."
    )
    assert pairs(address) == [
        ("ADDRESS_COUNTRY", "Россия"),
        ("ADDRESS_POSTAL_CODE", "630000"),
        ("ADDRESS_CITY", "Новосибирск"),
        ("ADDRESS_STREET", "Лесная"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "14"),
    ]
    assert pairs("ПИН владельца указан как 4826.") == [("PIN", "4826")]
    assert pairs("Имя, напечатанное на карте: MARIA BELOVA.") == [
        ("CARDHOLDER_NAME", "MARIA BELOVA")
    ]


def test_shared_and_non_person_contexts_are_suppressed() -> None:
    assert pairs("Рабочий телефон подразделения, не личный: +7 495 777-20-30.") == []
    assert pairs("Партнёрские заявки: partners@company.example.") == []
    assert pairs("Технический паспорт прибора содержит номер 45 10 123456.") == []
    assert pairs("Учебный стенд выводит карту 4012-8888-8888-1881, CVV 999.") == []


def test_v3_11_round_trip_is_exact() -> None:
    text = (
        "EMAIL владельца: {user.name@Example.ONLINE}; "
        "ПИН владельца указан как 4826."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
