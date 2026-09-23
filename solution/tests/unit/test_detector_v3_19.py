from app.masking import mask_text, unmask_text
from proposals.detector_v3_19 import detect, detect_candidates, should_mask


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_natural_document_ownership_clauses() -> None:
    assert pairs("Документ выдали Николаю Сергеевичу Белову как владельцу.") == [
        ("PERSON", "Николаю Сергеевичу Белову")
    ]
    assert pairs("Паспорт оформили ей третьего марта 2022 года.") == [
        ("PASSPORT_ISSUE_DATE", "третьего марта 2022 года")
    ]
    assert pairs("Мои права записаны как 4510-123456.") == [("DRIVER_LICENSE_RF", "4510-123456")]


def test_address_fields_and_bounded_multisentence_transfer() -> None:
    text = (
        "Получатель — Орлова Ирина Павловна. Живёт в Туле, на улице Советской, дом 9, квартира 12."
    )
    assert pairs(text) == [
        ("PERSON", "Орлова Ирина Павловна"),
        ("ADDRESS_CITY", "Туле"),
        ("ADDRESS_STREET", "Советской"),
        ("ADDRESS_HOUSE", "9"),
        ("ADDRESS_APARTMENT", "12"),
    ]


def test_birth_and_current_residence_are_not_conflated() -> None:
    text = (
        "Клиент родился 02.03.1980 в селе Константиново Рязанской области "
        "и теперь живёт в городе Туле."
    )
    assert pairs(text) == [
        ("BIRTH_DATE", "02.03.1980"),
        ("PLACE_OF_BIRTH", "селе Константиново Рязанской области"),
        ("ADDRESS_CITY", "Туле"),
    ]


def test_public_contact_policy_is_independent_of_detection() -> None:
    text = "Контакты галереи: gallery-office@art.example, +7 495 720-38-49."
    candidates = [
        item for item in detect_candidates(text) if item.entity.entity_type in {"EMAIL", "PHONE_RF"}
    ]
    assert candidates
    assert all(not should_mask(text, item) for item in candidates)
    assert detect(text) == []


def test_non_person_codes_and_public_address_are_suppressed() -> None:
    assert pairs("Запчасть CVC-807 находится на складе.") == []
    assert pairs("Адрес кинотеатра — Тула, улица Советская, дом 9.") == []


def test_v3_19_round_trip_is_exact() -> None:
    text = "Мой адрес: Россия, 300000, Тула, улица Советская, дом 9, квартира 12."
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
