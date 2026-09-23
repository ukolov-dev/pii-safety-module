from proposals.detector_v3_3 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_inflected_person_requires_personal_syntax() -> None:
    assert ("PERSON", "Марии Олеговны Соколовой") in pairs(
        "Согласие получено от Марии Олеговны Соколовой."
    )
    assert "PERSON" not in dict(pairs("На лекции говорили об Антоне Павловиче Чехове."))


def test_dates_are_typed_by_nearby_semantics() -> None:
    assert pairs("Дата рождения клиента: 2001-04-17.") == [("BIRTH_DATE", "2001-04-17")]
    assert pairs("Документ выдали ему 4 апреля 2019 г.") == [
        ("PASSPORT_ISSUE_DATE", "4 апреля 2019 г.")
    ]


def test_personal_address_chain_and_organisation_suppression() -> None:
    text = "Место регистрации: РФ, 300000, г. Тула, улица Советская, дом 4, квартира 2."
    assert pairs(text) == [
        ("ADDRESS_COUNTRY", "РФ"),
        ("ADDRESS_POSTAL_CODE", "300000"),
        ("ADDRESS_CITY", "Тула"),
        ("ADDRESS_STREET", "Советская"),
        ("ADDRESS_HOUSE", "4"),
        ("ADDRESS_APARTMENT", "2"),
    ]
    assert pairs("Адрес склада: г. Тула, улица Советская, дом 4.") == []


def test_payment_labels_choose_specific_types() -> None:
    assert pairs("Код карты CVC2): 741; CARD HOLDER: MARIA VOLKOVA.") == [
        ("CVV", "741"),
        ("CARDHOLDER_NAME", "MARIA VOLKOVA"),
    ]


def test_documentation_examples_are_suppressed() -> None:
    assert pairs("В инструкции приведён пример CVV 123 и код подразделения 770-001.") == []
    assert pairs("Общий ящик для закупок: tender@example.org.") == []


def test_results_are_deterministic_ordered_and_non_overlapping() -> None:
    text = "ФИО: Соколова Мария Олеговна; личный телефон +7 999 111-22-33."
    first = detect(text)
    assert first == detect(text)
    assert first == sorted(first, key=lambda entity: entity.start)
    assert all(left.end <= right.start for left, right in zip(first, first[1:], strict=False))
