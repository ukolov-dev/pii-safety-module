from app.masking import mask_text, unmask_text
from proposals.detector_v3_21 import detect


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_inflected_person_roles_require_personal_evidence() -> None:
    assert pairs("Данные сообщает сама Элеонора-Мария Витальевна Баженова.") == [
        ("PERSON", "Элеонора-Мария Витальевна Баженова")
    ]
    assert pairs("Лекция посвящена философу Николаю Бердяеву.") == []


def test_multiline_form_and_ocr_separators_are_parsed_as_one_address_block() -> None:
    text = (
        "АДРЕС ЗАЯВИТЕЛЯ |\n"
        "РОССИЯ | 190000 | Санкт-Петербург | улица Почтамтская | "
        "дом 7 | квартира 12"
    )
    assert pairs(text) == [
        ("ADDRESS_COUNTRY", "РОССИЯ"),
        ("ADDRESS_POSTAL_CODE", "190000"),
        ("ADDRESS_CITY", "Санкт-Петербург"),
        ("ADDRESS_STREET", "Почтамтская"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "12"),
    ]


def test_adjacent_sentence_residence_keeps_bounded_ownership() -> None:
    text = "Он живёт в Ульяновске. Его дом стоит на улице Федерации, номер 21, квартира 47."
    assert pairs(text) == [
        ("ADDRESS_CITY", "Ульяновске"),
        ("ADDRESS_STREET", "Федерации"),
        ("ADDRESS_HOUSE", "21"),
        ("ADDRESS_APARTMENT", "47"),
    ]


def test_document_table_fields_accept_common_separators() -> None:
    text = (
        "Личный документ гражданина\n"
        "КП документа | 260/114\n"
        "ВЫДАВШЕЕ ВЕДОМСТВО | ОМВД РОССИИ ПО Г. КАЛУГЕ."
    )
    assert pairs(text) == [
        ("DIVISION_CODE", "260/114"),
        ("PASSPORT_ISSUER", "ОМВД РОССИИ ПО Г. КАЛУГЕ"),
    ]


def test_public_and_technical_counter_evidence_wins() -> None:
    assert pairs("Клиентская служба банка отвечает по +7 (495) 650-27-38.") == []
    assert pairs("Шаблон допускает код подразделения 770-001.") == []
    assert pairs("Контакты выставки: exhibition@venue.example, +7 812 630-47-58.") == []


def test_large_sparse_document_preserves_global_offsets() -> None:
    prefix = "служебная запись без данных " * 5000
    value = "Иванов Иван Иванович"
    text = f"{prefix}\nФИО заявителя: {value}\n{prefix}"
    entities = detect(text)
    person = next(entity for entity in entities if entity.entity_type == "PERSON")
    assert person.text == value
    assert text[person.start : person.end] == value


def test_v3_21_round_trip_is_exact() -> None:
    text = "Новый адрес заявителя: 190000; Санкт-Петербург; улица Почтамтская; дом 7."
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
