from app.masking import mask_text, unmask_text
from proposals.detector_v3_25 import (
    Family,
    FieldStateMachine,
    NormalizedText,
    _valid_inn,
    _valid_luhn,
    detect,
    tokenize,
)


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_normalization_preserves_reversible_source_offsets() -> None:
    text = "EMAIL_ЛИЧНЫЙ=Name_1@Example.RU; ДАТА РОЖД. 23·09·1982"
    normalized = NormalizedText.build(text)
    assert "email_личный name_1@example.ru" in normalized.text
    assert "23.09.1982" in normalized.text
    for entity in detect(text):
        assert text[entity.start : entity.end] == entity.text
    assert ("EMAIL", "Name_1@Example.RU") in pairs(text)
    assert ("BIRTH_DATE", "23·09·1982") in pairs(text)


def test_tokenizer_tracks_record_boundaries() -> None:
    document = NormalizedText.build(
        "ФИО: Иванов Иван Иванович; Телефон: +7 999 123-45-67\nГород: Омск"
    )
    tokens = tokenize(document)
    assert {token.record for token in tokens} == {0, 1, 2}


def test_state_machine_never_binds_across_records() -> None:
    document = NormalizedText.build("Телефон клиента: нет; служебный номер +7 999 123-45-67")
    machine = FieldStateMachine(document, tokenize(document))
    assert list(machine.candidates()) == []


def test_shape_validators_reject_plausible_but_invalid_identifiers() -> None:
    assert _valid_inn("7707083893")
    assert not _valid_inn("7707083894")
    assert _valid_luhn("4111111111111111")
    assert not _valid_luhn("4111111111111112")


def test_ownership_policy_separates_private_and_public_addresses() -> None:
    public = "Клиент выбрал постамат: Норильск, улица Талнахская, дом 30."
    private = "Домашний адрес клиента: Норильск, улица Талнахская, дом 30."
    assert not any(entity_type.startswith("ADDRESS_") for entity_type, _ in pairs(public))
    assert ("ADDRESS_STREET", "Талнахская") in pairs(private)
    assert ("ADDRESS_HOUSE", "30") in pairs(private)


def test_technical_passport_number_is_not_a_person_document() -> None:
    assert pairs("Паспорт промышленной установки маркирован номером 41 09 628304.") == []


def test_round_trip_preserves_original_unicode_and_separators() -> None:
    text = "АНКЕТА\nФИО=Ёлкин Семён Петрович; EMAIL_ЛИЧНЫЙ=Name_1@Example.RU; ДАТА РОЖД. 23·09·1982"
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
    assert all(text[item.start : item.end] == item.text for item in detect(text))


def test_field_family_is_emitted_with_expected_type() -> None:
    document = NormalizedText.build("АНКЕТА|Гражданство|Российская Федерация")
    candidates = list(FieldStateMachine(document, tokenize(document)).candidates())
    assert any(candidate.family is Family.CITIZENSHIP for candidate in candidates)
