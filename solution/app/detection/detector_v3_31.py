"""Candidate v3.31: schema-aware labelled values over production v3.26.

The candidate keeps the production detector as its broad baseline and adds a
small, value-validated parser for common prose, OCR, JSON and ``key=value``
field representations.  Rules are based on semantic field names and value
shapes, not on known people, cities, issuers or complete record templates.
All normalization is length preserving, so offsets refer to the source text.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from datetime import date

from .detector_v3_26 import detect as detect_v3_26
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

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
        "·": ".",
    }
)

_WORD = r"[А-ЯЁа-яёA-Za-z]+(?:-[А-ЯЁа-яёA-Za-z]+)*"
_TEXT = rf"{_WORD}(?:[ ]+{_WORD}){{0,11}}"
_PERSON = r"[А-ЯЁ][а-яё-]+(?:[ ]+[А-ЯЁ][а-яё-]+){2}"
_UPPER_NAME = r"(?:[А-ЯЁA-Z][А-ЯЁA-Z'\-’]+)(?:[ ]+(?:[А-ЯЁA-Z][А-ЯЁA-Z'\-’]+)){1,3}"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])[-./](?:19|20)\d{2}"
_PASSPORT = r"(?:\d{4}|\d{2}[ -]\d{2})[ -]\d{6}"
_LICENSE = r"\d{2}[ -]\d{2}[ -]\d{6}"
_PHONE = r"(?:\+7|8|7)(?:[ ().-]*\d){10}"
_EMAIL = r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def _valid_date(value: str) -> bool:
    try:
        day, month, year = (int(part) for part in re.split(r"[-./]", value))
        date(year, month, day)
    except ValueError:
        return False
    return True


def _digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _valid_phone(value: str) -> bool:
    digits = _digits(value)
    return len(digits) == 11 and digits[0] in "78"


def _valid_passport(value: str) -> bool:
    return len(_digits(value)) == 10


Validator = Callable[[str], bool]


def _always(_: str) -> bool:
    return True


# Each grammar captures only ``value`` and requires an explicit semantic label.
# Quoted forms cover JSON-like records; bare forms cover configuration fields.
_FIELD_RULES: tuple[tuple[str, re.Pattern[str], Validator], ...] = (
    (
        "PERSON",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?"
            rf"(?:customer|person|full[_ .-]?name|owner|user|ФИО)[\"']?"
            rf"\s*[:=]\s*[\"']?(?P<value>{_PERSON})(?=\s*[\"',;}}\n]|$)"
        ),
        _always,
    ),
    (
        "BIRTH_DATE",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?"
            rf"(?:birth(?:[_ .-]?date)?|date[_ .-]?of[_ .-]?birth|"
            rf"дата[_ .-]?рождения)[\"']?\s*[:=]\s*[\"']?"
            rf"(?P<value>{_DATE})(?=\s*[\"',;}}\n]|$)"
        ),
        _valid_date,
    ),
    (
        "PASSPORT_RF",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?"
            rf"(?:passport(?:[_ .-]?rf)?|пасп[0о]рт|серия[/ _.-]?номер)"
            rf"[\"']?\s*[:=]?\s*[\"']?(?P<value>{_PASSPORT})"
            rf"(?=\s*[\"',;}}\n]|$)"
        ),
        _valid_passport,
    ),
    (
        "DRIVER_LICENSE_RF",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?"
            rf"(?:license[_ .-]?rf|driver[_ .-]?licen[cs]e|dl|"
            rf"водительское[_ .-]?удостоверение)[\"']?\s*[:=]\s*[\"']?"
            rf"(?P<value>{_LICENSE})(?=\s*[\"',;}}\n]|$)"
        ),
        _valid_passport,
    ),
    (
        "EMAIL",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?"
            rf"(?:contact[_ .-]?email|e-?mail|электронная[_ .-]?почта)"
            rf"[\"']?\s*[:=]\s*[\"']?(?P<value>{_EMAIL})"
            rf"(?=\s*[\"',;}}\n]|$)"
        ),
        _always,
    ),
    (
        "PHONE_RF",
        _rx(
            rf"(?:^|[{{,;\n])\s*[\"']?(?:phone|mobile|телефон|мобильный)[\"']?\s*[:=]?\s*[\"']?(?P<value>{_PHONE})(?=\s*[\"',;}}\n]|$)"
        ),
        _valid_phone,
    ),
    (
        "ADDRESS_COUNTRY",
        _rx(
            rf"(?:^|[{{,\n])\s*[\"']?(?:country|страна)[\"']?\s*[:=]\s*[\"'](?P<value>{_TEXT})[\"']"
        ),
        _always,
    ),
    (
        "ADDRESS_POSTAL_CODE",
        _rx(
            r"(?:^|[{,\n])\s*[\"']?"
            r"(?:postal[_ .-]?code|postcode|zip|почтовый[_ .-]?индекс|индекс)"
            r"[\"']?\s*[:=]\s*[\"']?(?P<value>\d{6})(?=\s*[\"',;}}\n]|$)"
        ),
        _always,
    ),
    (
        "ADDRESS_CITY",
        _rx(rf"(?:^|[{{,\n])\s*[\"']?(?:city|город)[\"']?\s*[:=]\s*[\"'](?P<value>{_TEXT})[\"']"),
        _always,
    ),
    (
        "ADDRESS_STREET",
        _rx(rf"(?:^|[{{,\n])\s*[\"']?(?:street|улица)[\"']?\s*[:=]\s*[\"'](?P<value>{_TEXT})[\"']"),
        _always,
    ),
    (
        "ADDRESS_HOUSE",
        _rx(
            r"(?:^|[{,\n])\s*[\"']?(?:house|дом)[\"']?\s*[:=]\s*[\"'](?P<value>\d{1,4}[А-ЯЁA-Z]?)[\"']"
        ),
        _always,
    ),
    (
        "ADDRESS_APARTMENT",
        _rx(
            r"(?:^|[{,\n])\s*[\"']?(?:apartment|flat|apt|квартира|кв)[\"']?\s*[:=]\s*[\"'](?P<value>\d{1,5})[\"']"
        ),
        _always,
    ),
)

_PROSE_RULES: tuple[tuple[str, re.Pattern[str], Validator], ...] = (
    ("PERSON", _rx(rf"\bзаявка\s*:\s*(?P<value>{_PERSON})(?=\s*[;,.\n]|$)"), _always),
    ("CITIZENSHIP", _rx(rf"\bгражданство\s*[:=-]\s*(?P<value>{_TEXT})(?=\s*[;,.\n]|$)"), _always),
    (
        "ADDRESS_CITY",
        _rx(rf"(?:^|[;\n])\s*город\s*[:=-]?\s+(?P<value>{_WORD}(?:\s+{_WORD})?)(?=\s*[;,.\n]|$)"),
        _always,
    ),
    (
        "CARDHOLDER_NAME",
        re.compile(
            rf"\bна\s+имя\s+(?P<value>{_UPPER_NAME})"
            rf"(?=\s+(?:указан\w*|CVV|CVC|PIN|ПИН)\b|\s*[;,.\n]|$)",
            re.MULTILINE,
        ),
        _always,
    ),
)

_PERSON_SCHEMA = _rx(
    rf"(?:^|[{{,;\n])\s*[\"']?(?:customer|person|full[_ .-]?name|owner|user|ФИО|заявка)[\"']?"
    rf"\s*[:=]\s*[\"']?{_PERSON}(?=\s*[\"',;}}\n]|$)"
)

# OCR passport fields are line scoped.  Capturing everything after the label
# prevents the old partial-issuer false positive (for example dropping "ОВМ").
_OCR_RULES: tuple[tuple[str, re.Pattern[str], Validator], ...] = (
    (
        "PASSPORT_ISSUER",
        _rx(
            r"^(?:ВЫДАН|выдан|issued[_ .-]?by)\s*[:=-]?\s*"
            r"(?P<value>(?:(?:ОВМ|(?:ОТДЕЛ(?:ЕНИЕ|ОМ)?)|"
            r"(?:ГУ|[УО]МВД)|УФМС)\b)[^\n]{2,119}?)(?=\s*$)"
        ),
        _always,
    ),
    (
        "PASSPORT_ISSUE_DATE",
        _rx(rf"^(?:ДАТА\s+ВЫДАЧИ|issue[_ .-]?date)\s*[:=-]?\s*(?P<value>{_DATE})\s*$"),
        _valid_date,
    ),
)


def _entity(text: str, entity_type: str, match: re.Match[str]) -> DetectedEntity:
    start, end = match.span("value")
    return DetectedEntity(
        entity_type,
        start,
        end,
        text[start:end],
        0.999,
        "label_schema_v3_31",
        500,
    )


def _labelled_candidates(text: str) -> Iterator[DetectedEntity]:
    normalized = text.translate(_TRANSLATE)
    for entity_type, pattern, validator in (*_FIELD_RULES, *_PROSE_RULES, *_OCR_RULES):
        for match in pattern.finditer(normalized):
            value = normalized[slice(*match.span("value"))]
            personal_contact = entity_type not in {"EMAIL", "PHONE_RF"} or bool(
                _PERSON_SCHEMA.search(normalized)
            )
            if personal_contact and validator(value):
                yield _entity(text, entity_type, match)


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with production rules plus validated labelled fields."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return _merge([*detect_v3_26(text), *_labelled_candidates(text)])
