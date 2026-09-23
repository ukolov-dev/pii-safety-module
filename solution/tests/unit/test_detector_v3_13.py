from app.masking import mask_text, unmask_text
from proposals.detector_v3_13 import detect, detect_candidates, should_mask


def pairs(text: str) -> list[tuple[str, str]]:
    return [(entity.entity_type, entity.text) for entity in detect(text)]


def test_role_person_and_document_fields() -> None:
    assert pairs("Заявка подана Куликовой Яной Сергеевной.") == [
        ("PERSON", "Куликовой Яной Сергеевной")
    ]
    assert pairs("Представителем назначен Воронов Пётр Семёнович.") == [
        ("PERSON", "Воронов Пётр Семёнович")
    ]
    assert pairs("Паспортные данные гражданина: серия 4510 и номер 123456.") == [
        ("PASSPORT_RF", "серия 4510 и номер 123456")
    ]


def test_dates_places_citizenship_and_license() -> None:
    assert pairs("Дата фактической выдачи паспорта: 03/06/2014.") == [
        ("PASSPORT_ISSUE_DATE", "03/06/2014")
    ]
    assert pairs("В строке «место рождения» написано: хутор Белый Ростовской области.") == [
        ("PLACE_OF_BIRTH", "хутор Белый Ростовской области")
    ]
    assert pairs("В миграционной анкете гражданство лица указано как Россия.") == [
        ("CITIZENSHIP", "Россия")
    ]
    assert pairs("Для проверки водителя загружены права: 77 11 654321.") == [
        ("DRIVER_LICENSE_RF", "77 11 654321")
    ]


def test_card_and_subscriber_labels() -> None:
    text = "Моя карта: защитный код 381; надпись на карте MARIA BELOVA."
    assert pairs(text) == [("CVV", "381"), ("CARDHOLDER_NAME", "MARIA BELOVA")]
    assert pairs("Сотовый абонента: +7/921/555/12/34.") == [
        ("PHONE_RF", "+7/921/555/12/34")
    ]


def test_personal_delivery_address_chain() -> None:
    text = "Мне домой: 630000, Новосибирск, улица Лесная, д. 7, кв. 14."
    assert pairs(text) == [
        ("ADDRESS_POSTAL_CODE", "630000"),
        ("ADDRESS_CITY", "Новосибирск"),
        ("ADDRESS_STREET", "Лесная"),
        ("ADDRESS_HOUSE", "7"),
        ("ADDRESS_APARTMENT", "14"),
    ]


def test_candidate_detection_is_separate_from_mask_policy() -> None:
    text = "Служебный номер аварийной бригады: +7 (495) 777-20-30."
    candidates = detect_candidates(text)
    phone = next(item for item in candidates if item.entity.entity_type == "PHONE_RF")
    assert phone.evidence == "inherited_v3_11"
    assert should_mask(text, phone) is False
    assert detect(text) == []


def test_v3_13_round_trip_is_exact() -> None:
    text = (
        "Мне домой: 630000, Новосибирск, улица Лесная, д. 7; "
        "сотовый +7/921/555/12/34."
    )
    masked = mask_text(text, detect(text))
    assert unmask_text(masked.text, masked.mapping) == text
