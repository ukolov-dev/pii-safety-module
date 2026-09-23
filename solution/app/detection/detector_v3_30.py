"""Candidate v3.30: labelled record families over production v3.26.

The added rules deliberately key off semantic field labels and validate the
value shapes they capture.  They cover prose, OCR-like line records and
key/value serializations without depending on a vocabulary of known values.
Offsets always refer to the original input.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from .detector_v3_26 import detect as detect_v3_26
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_CITY = rf"{_WORD}(?:\s+{_WORD})?"
_CARDHOLDER = (
    r"(?:[A-Z][A-Z'’-]+|[А-ЯЁ][А-ЯЁ'’-]+)"
    r"(?:\s+(?:[A-Z][A-Z'’-]+|[А-ЯЁ][А-ЯЁ'’-]+)){1,3}"
)
_DATE = (
    r"(?:\d{4}[-./](?:1[0-2]|0?[1-9])[-./](?:3[01]|[12]\d|0?[1-9])|"
    r"(?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])[-./]\d{4})"
)
_PASSPORT = r"\d{2}[\s-]\d{2}[\s-]\d{6}"
_DIVISION = r"\d{3}[\s/-]\d{3}"
_CARD = r"\d(?:[\s-]*\d){15,18}"

_TRANSLATE = str.maketrans(
    {
        "\u00a0": " ",
        "\u202f": " ",
        "\u2009": " ",
        "\t": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
    }
)


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


_BIRTH_RECORDS = (
    _rx(
        rf"\b(?:родил(?:ся|ась)|дата\s+рождения\s*[:=]\s*)"
        rf"(?P<birth>{_DATE})\s+(?:в|место\s+рождения\s*[:=])\s*"
        rf"(?P<place>{_CITY})(?=\s*[,;.]|\s+(?:гражданство|и)\b)"
    ),
    _rx(rf"\bродил(?:ся|ась)\s+{_DATE}\s+в\s+(?P<place>{_CITY})(?=\s*[,;.])"),
)

_STRUCTURED_BIRTHPLACE = _rx(
    rf"(?:\bbirth[_ .-]?place\b|\bplace[_ .-]?of[_ .-]?birth\b|место[_ .-]?рождения)"
    rf"\s*[:=]\s*['\"](?P<place>{_CITY})['\"]"
)

_PASSPORT_RECORD = _rx(
    rf"\b(?:документ|паспорт(?:\s+РФ)?)\s*[:=№-]?\s*(?P<passport>{_PASSPORT})"
    rf"\s*[,;|]?\s*(?:кем\s+)?выдан\s*[:=]?\s*(?P<issuer>[^\n;,|]{{5,120}}?)"
    rf"\s*[,;]?\s*(?P<issue>{_DATE})\s*[,;|]?\s*(?:код(?:\s+подразделения)?)\s*[:=]?\s*(?P<division>{_DIVISION})(?!\d)"
)

_OCR_PASSPORT_RECORD = _rx(
    rf"^(?:ПАСП[0О]РТ|паспорт)[^\S\n]*[:=][^\S\n]*(?P<passport>{_PASSPORT})[^\S\n]*$\n"
    rf"^(?:К[0О]Д\s+П[0О]ДРАЗДЕЛЕНИЯ|код\s+подразделения)[^\S\n]*[:=][^\S\n]*(?P<division>{_DIVISION})[^\S\n]*$\n"
    rf"^ВЫДАН[^\S\n]*[:=][^\S\n]*(?P<issuer>[^\n]{{5,120}}?)[^\S\n]*$\n"
    rf"^(?:ДАТА|дата\s+выдачи)\s*[:=]\s*(?P<issue>{_DATE})(?:\s|$)"
)

_DELIVERY_ADDRESS = _rx(
    rf"\b(?:доставка|адрес(?:\s+доставки)?)\s*:\s*"
    rf"страна\s*[:=]?\s*(?P<country>{_WORD}(?:\s+{_WORD})?)\s*,\s*"
    rf"индекс\s*[:=]?\s*(?P<postcode>\d{{6}})\s*,\s*"
    rf"город\s*[:=]?\s*(?P<city>{_CITY})\s*,\s*"
    rf"улица\s*[:=]?\s*(?P<street>{_WORD}(?:\s+{_WORD})?)\s*,\s*"
    rf"дом\s*[:=]?\s*(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*"
    rf"квартира\s*[:=]?\s*(?P<flat>\d{{1,5}})(?!\d)"
)

_STRUCTURED_ADDRESS = _rx(
    rf"\baddress\s*[:=]\s*\{{\s*"
    rf"(?:zip|postal(?:[_-]?code)?)\s*[:=]\s*['\"](?P<postcode>\d{{6}})['\"]\s*,\s*"
    rf"city\s*[:=]\s*['\"](?P<city>{_CITY})['\"]\s*,\s*"
    rf"street\s*[:=]\s*['\"](?P<street>{_WORD}(?:\s+{_WORD})?)['\"]\s*,\s*"
    rf"house\s*[:=]\s*['\"](?P<house>\d{{1,4}}[А-ЯЁA-Z]?)['\"]\s*,\s*"
    rf"(?:apt|apartment|flat)\s*[:=]\s*['\"](?P<flat>\d{{1,5}})['\"]\s*\}}"
)

_STRUCTURED_USER = _rx(
    r"(?:^|[{,])\s*(?:user|person|full[_-]?name)\s*[:=]\s*['\"]"
    r"(?P<person>[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){2})['\"]"
)

_STRUCTURED_LICENSE = _rx(
    r"(?:^|[,{])\s*(?:dl|driver[_-]?licen[cs]e)\s*[:=]\s*['\"]"
    r"(?P<license>\d{2}[\s-]\d{2}[\s-]\d{6})['\"]"
)

_CONTACT_PERSON = _rx(
    r"\b(?:связь\s+с|контактное\s+лицо)\s*[:=-]?\s*"
    r"(?P<person>[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){2})"
    r"(?=\s*[:,;])"
)

_LABELED_CARD = _rx(
    rf"(?:\b(?:банковская|payment[._-]?)?карта|\bpayment[._-]?card)"
    rf"\s*[:=№-]?\s*(?P<card>{_CARD})(?=\s*(?:[;,.|\n]|$))"
)

_PAYMENT_RECORD = _rx(
    rf"(?:\b(?:оплата\s*:\s*)?карта|\bpayment[._-]?card)\s*[:=]?\s*(?P<card>{_CARD})"
    rf"\s*(?:[;\n,]|$)\s*(?:держатель|card[._-]?holder)\s*[:=]?\s*(?P<holder>{_CARDHOLDER})"
    rf"\s*(?:[;\n,]|$)\s*(?:security[._-]?)?cvv2?\s*[:=]?\s*(?P<cvv>\d{{3}})"
    rf"\s*(?:[;\n,]|$)\s*(?:security[._-]?)?pin\s*[:=]?\s*(?P<pin>\d{{4}})(?!\d)"
)


def _entity(
    text: str, entity_type: str, span: tuple[int, int], source: str
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, 320)


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[-./]", value)]
    year, month, day = parts if len(str(parts[0])) == 4 else (parts[2], parts[1], parts[0])
    try:
        date(year, month, day)
    except ValueError:
        return False
    return 1900 <= year <= 2100


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 16 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    parity = len(digits) % 2
    total = 0
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _record_entities(
    text: str,
    normalized: str,
    pattern: re.Pattern[str],
    fields: tuple[tuple[str, str], ...],
    source: str,
) -> Iterator[DetectedEntity]:
    for match in pattern.finditer(normalized):
        spans = {group: match.span(group) for group, _ in fields if match.groupdict().get(group)}
        if "birth" in spans and not _valid_date(text[slice(*spans["birth"])]):
            continue
        if "issue" in spans and not _valid_date(text[slice(*spans["issue"])]):
            continue
        if "issuer" in spans:
            issuer = normalized[slice(*spans["issuer"])]
            if re.search(r"(?:МВД|УФМС|ОВМ|миграции)", issuer, re.I) is None:
                continue
        if "card" in spans and not _valid_luhn(text[slice(*spans["card"])]):
            continue
        if "card" in spans:
            card_start, card_end = spans["card"]
            card_context = normalized[max(0, card_start - 80) : min(len(normalized), card_end + 40)]
            if re.search(
                r"\b(?:публичн\w*|тестов\w*|фиктивн\w*|пример\w*|шаблон\w*)\b",
                card_context,
                re.I,
            ):
                continue
        for group, entity_type in fields:
            span = spans.get(group)
            if span is not None:
                yield _entity(text, entity_type, span, source)


def _candidates(text: str) -> Iterator[DetectedEntity]:
    normalized = text.translate(_TRANSLATE)
    for pattern in _BIRTH_RECORDS:
        yield from _record_entities(
            text,
            normalized,
            pattern,
            (("birth", "BIRTH_DATE"), ("place", "PLACE_OF_BIRTH")),
            "birth_record_v3_30",
        )
    yield from _record_entities(
        text,
        normalized,
        _STRUCTURED_BIRTHPLACE,
        (("place", "PLACE_OF_BIRTH"),),
        "structured_birthplace_v3_30",
    )
    passport_fields = (
        ("passport", "PASSPORT_RF"),
        ("issuer", "PASSPORT_ISSUER"),
        ("issue", "PASSPORT_ISSUE_DATE"),
        ("division", "DIVISION_CODE"),
    )
    yield from _record_entities(
        text, normalized, _PASSPORT_RECORD, passport_fields, "passport_record_v3_30"
    )
    yield from _record_entities(
        text, normalized, _OCR_PASSPORT_RECORD, passport_fields, "ocr_passport_record_v3_30"
    )
    address_fields = (
        ("country", "ADDRESS_COUNTRY"),
        ("postcode", "ADDRESS_POSTAL_CODE"),
        ("city", "ADDRESS_CITY"),
        ("street", "ADDRESS_STREET"),
        ("house", "ADDRESS_HOUSE"),
        ("flat", "ADDRESS_APARTMENT"),
    )
    yield from _record_entities(
        text, normalized, _DELIVERY_ADDRESS, address_fields, "delivery_address_v3_30"
    )
    yield from _record_entities(
        text,
        normalized,
        _STRUCTURED_ADDRESS,
        address_fields[1:],
        "structured_address_v3_30",
    )
    yield from _record_entities(
        text,
        normalized,
        _STRUCTURED_USER,
        (("person", "PERSON"),),
        "structured_person_v3_30",
    )
    yield from _record_entities(
        text,
        normalized,
        _STRUCTURED_LICENSE,
        (("license", "DRIVER_LICENSE_RF"),),
        "structured_license_v3_30",
    )
    yield from _record_entities(
        text,
        normalized,
        _CONTACT_PERSON,
        (("person", "PERSON"),),
        "contact_person_v3_30",
    )
    yield from _record_entities(
        text,
        normalized,
        _LABELED_CARD,
        (("card", "BANK_CARD"),),
        "labelled_card_v3_30",
    )
    payment_fields = (
        ("card", "BANK_CARD"),
        ("holder", "CARDHOLDER_NAME"),
        ("cvv", "CVV"),
        ("pin", "PIN"),
    )
    yield from _record_entities(
        text, normalized, _PAYMENT_RECORD, payment_fields, "payment_record_v3_30"
    )


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with production rules plus validated labelled records."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    if len(text) >= 100_000:
        return detect_v3_26(text)
    return _merge([*detect_v3_26(text), *_candidates(text)])
