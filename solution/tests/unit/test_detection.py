from app.detection import DetectedEntity, detect


def by_type(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for entity in detect(text):
        result.setdefault(entity.entity_type, []).append(entity.text)
    return result


def test_detects_basic_contacts_and_offsets() -> None:
    text = "Email ivan.petrov@example.ru, телефон +7 (999) 123-45-67."

    entities = detect(text)

    assert [(item.entity_type, item.text) for item in entities] == [
        ("EMAIL", "ivan.petrov@example.ru"),
        ("PHONE_RF", "+7 (999) 123-45-67"),
    ]
    assert all(text[item.start : item.end] == item.text for item in entities)
    assert all(isinstance(item, DetectedEntity) for item in entities)


def test_inn_requires_valid_checksum() -> None:
    entities = by_type(
        "ИНН юрлица 7707083893, ИНН физлица 500100732259, "
        "ошибка 7707083894"
    )

    assert entities["INN"] == ["7707083893", "500100732259"]


def test_bank_card_requires_luhn_and_wins_over_generic_numbers() -> None:
    entities = by_type("Карта 4111 1111 1111 1111, неверная 4111 1111 1111 1112")

    assert entities["BANK_CARD"] == ["4111 1111 1111 1111"]


def test_contextual_document_and_birth_fields() -> None:
    text = (
        "Паспорт 45 10 123456, код подразделения 770-001, "
        "дата рождения 29.02.2000. Просто дата 01.01.2020 "
        "и число 40 20 123456."
    )

    entities = by_type(text)

    assert entities["PASSPORT_RF"] == ["45 10 123456"]
    assert entities["DIVISION_CODE"] == ["770-001"]
    assert entities["BIRTH_DATE"] == ["29.02.2000"]


def test_rejects_impossible_birth_date() -> None:
    assert "BIRTH_DATE" not in by_type("Дата рождения 31.02.2000")


def test_detects_textual_birth_date() -> None:
    entities = by_type("Дата рождения: 7 мая 1987 года")

    assert entities["BIRTH_DATE"] == ["7 мая 1987 года"]


def test_cvv_and_pin_need_explicit_bank_field_context() -> None:
    entities = by_type("Код 123, CVV 321, пин-код: 4567, просто 9876")

    assert entities["CVV"] == ["321"]
    assert entities["PIN"] == ["4567"]


def test_person_fallback_uses_russian_context_or_patronymic() -> None:
    text = (
        "ФИО: Иванов Иван Иванович. "
        "Затем Петров Пётр Сергеевич."
    )

    assert by_type(text)["PERSON"] == [
        "Иванов Иван Иванович",
        "Петров Пётр Сергеевич",
    ]
    assert "PERSON" not in by_type("клиент оплатил заказ")


def test_rejects_public_bank_contacts() -> None:
    entities = by_type(
        "Горячая линия банка: 8 800 555-35-35. "
        "Общий адрес службы поддержки: support@example.org."
    )

    assert "PHONE_RF" not in entities
    assert "EMAIL" not in entities


def test_output_is_deterministic_non_overlapping_and_source_ordered() -> None:
    text = "ИНН 7707083893; email a@b.ru; карта 4111111111111111"

    first = detect(text)
    second = detect(text)

    assert first == second
    assert first == sorted(first, key=lambda item: item.start)
    assert all(left.end <= right.start for left, right in zip(first, first[1:], strict=False))


def test_empty_and_wrong_input() -> None:
    assert detect("") == []

    try:
        detect(None)  # type: ignore[arg-type]
    except TypeError as error:
        assert str(error) == "text must be a string"
    else:
        raise AssertionError("TypeError was not raised")
