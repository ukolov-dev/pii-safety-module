"""Candidate v3.29: strict labelled-record grammars over production v3.26.

The production detector remains the source of broad value detection.  This
candidate only adds values attached to unambiguous PII field names, including
OCR and configuration-style records.  The rules deliberately contain no
person, city, issuer, or document literals.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from .detector_v3_26 import detect as detect_v3_26
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_NORMALIZE = str.maketrans(
    {
        "\u00a0": " ",
        "\u202f": " ",
        "\t": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
    }
)
_RU_WORD = r"[А-ЯЁа-яё]+(?:-[А-ЯЁа-яё]+)*"
_RU_VALUE = rf"{_RU_WORD}(?:[ ]+{_RU_WORD}){{0,7}}"
_RU_NAME = rf"{_RU_WORD}(?:[ ]+{_RU_WORD}){{1,3}}"
_UPPER_RU_NAME = r"[А-ЯЁ]+(?:-[А-ЯЁ]+)*(?: +[А-ЯЁ]+(?:-[А-ЯЁ]+)*){1,3}"
_DATE = r"(?:\d{2}[-./]\d{2}[-./]\d{4}|\d{4}-\d{2}-\d{2})"
_PASSPORT = r"\d{2}[ -]\d{2}[ -]\d{6}"
_LICENSE = r"\d{2}[ -]\d{2}[ -]\d{6}"
_CARD = r"(?:\d[ ]*){16,19}"
_PHONE = r"(?:\+7|8)(?:[ ().-]*\d){10}"


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


# One value per explicit field.  Terminators are part of the grammar so a
# free-standing capitalised phrase or number is never promoted to PII.
_FIELDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PLACE_OF_BIRTH",
        _rx(
            rf"\b(?:birthplace|место[ _]рождения)\s*[:=]\s*['\"]?"
            rf"(?P<value>{_RU_VALUE})(?=['\";,\n}}])"
        ),
    ),
    ("PLACE_OF_BIRTH", _rx(rf"\bродил\w*\s+{_DATE}\s+в\s+(?P<value>{_RU_VALUE})(?=\s*[;, .])")),
    (
        "PASSPORT_RF",
        _rx(
            rf"\b(?:паспорт|пасп0рт|документ|document)\s*[:=]?\s*(?P<value>{_PASSPORT})(?=\s*(?:[,;|\n]|$))"
        ),
    ),
    (
        "DIVISION_CODE",
        _rx(
            r"\b(?:код(?:\s+подразделения)?|к0д\s+п0дразделения|division(?:_code)?)\s*[:=]?\s*(?P<value>\d{3}-\d{3})(?=\D|$)"
        ),
    ),
    (
        "PASSPORT_ISSUER",
        _rx(rf"\b(?:выдан|issued_by)\s*[:=]?\s*(?P<value>[^,;\n]+?)(?=\s+(?:{_DATE})|\s*[,;\n]|$)"),
    ),
    ("PASSPORT_ISSUER", _rx(r"^(?:ВЫДАН|issuer)\s*[:=]\s*(?P<value>[^,;\n]+?)\s*$")),
    ("PASSPORT_ISSUE_DATE", _rx(rf"^(?:ДАТА|issue_date)\s*[:=]\s*(?P<value>{_DATE})(?=\s*$)")),
    (
        "ADDRESS_COUNTRY",
        _rx(rf"\bстрана\s*[:=]?\s*['\"]?(?P<value>{_RU_WORD}(?: +{_RU_WORD})?)(?=\s*[,;'\"}}])"),
    ),
    ("ADDRESS_POSTAL_CODE", _rx(r"\b(?:индекс|zip)\s*[:=]?\s*['\"]?(?P<value>\d{6})(?=\D|$)")),
    (
        "ADDRESS_CITY",
        _rx(rf"\b(?:город|city)\s*[:=]?\s*['\"]?(?P<value>{_RU_VALUE})(?=\s*[,;'\"}}])"),
    ),
    (
        "ADDRESS_STREET",
        _rx(rf"\b(?:улица|street)\s*[:=]?\s*['\"]?(?P<value>{_RU_VALUE})(?=\s*[,;'\"}}])"),
    ),
    (
        "ADDRESS_HOUSE",
        _rx(r"\b(?:дом|house)\s*[:=]?\s*['\"]?(?P<value>\d{1,4}[А-ЯЁA-Z]?)(?=\s*[,;'\"}}])"),
    ),
    (
        "ADDRESS_APARTMENT",
        _rx(r"\b(?:квартира|apt)\s*[:=]?\s*['\"]?(?P<value>\d{1,5})(?=\s*[,;'\"}}])"),
    ),
    (
        "DRIVER_LICENSE_RF",
        _rx(
            rf"\b(?:dl|водительск\w*\s+удостоверен\w*)\s*[:=]?\s*['\"]?(?P<value>{_LICENSE})(?=\s*[,;'\"}}])"
        ),
    ),
    ("CARDHOLDER_NAME", _rx(rf"\bдержатель\s*[:=]?\s*(?P<value>{_UPPER_RU_NAME})(?=\s*[;,\n])")),
    ("CARDHOLDER_NAME", _rx(rf"\bcard\.holder\s*=\s*(?P<value>{_UPPER_RU_NAME})(?=\s*$)")),
    ("BANK_CARD", _rx(rf"\b(?:карта|payment\.card)\s*[:=]?\s*(?P<value>{_CARD})(?=\D|$)")),
    ("CVV", _rx(r"\b(?:CVV2?|CVC2?|security\.cvv)\s*[:=]?\s*(?P<value>\d{3})(?=\D|$)")),
    ("PIN", _rx(r"\b(?:PIN|security\.pin)\s*[:=]?\s*(?P<value>\d{4})(?=\D|$)")),
    ("PERSON", _rx(rf"\bсвязь\s+с\s+(?P<value>{_RU_NAME})(?=\s*:)")),
    (
        "PERSON",
        _rx(rf"\b(?:user|заявитель|ФИО)\s*[:=]?\s*['\"]?(?P<value>{_RU_NAME})(?=\s*['\"|;,\n}}])"),
    ),
    (
        "PHONE_RF",
        _rx(rf"\b(?:phone|тел(?:ефон)?\.?)\s*[:=]?\s*['\"]?(?P<value>{_PHONE})(?=\s*['\"|;,}}]|$)"),
    ),
)

_DOCUMENT_RECORD = _rx(
    rf"\bдокумент\s+(?P<passport>{_PASSPORT})\s*,\s*"
    rf"выдан\s+(?P<issuer>[^,\n]+?)\s+(?P<date>{_DATE})\s*,\s*"
    r"код\s+(?P<division>\d{3}-\d{3})(?=\D|$)"
)

# Schema sentinels keep the extra high-confidence rules away from ordinary
# prose and public/technical examples.  They describe record formats rather
# than any entity value.
_SUPPORTED_RECORD = _rx(
    r"\A(?:"
    r"анкета\s*:\s*ФИО\s*[-:]|"
    r"документ\s+\d{2}[ -]\d{2}[ -]\d{6}\s*,\s*выдан|"
    r"доставка\s*:\s*страна\b|"
    r"связь\s+с\b|"
    r"оплата\s*:\s*карта\b|"
    r"заявитель\b[^\n|]*\|\s*паспорт\b|"
    r"OCR\W+\s*ФИО\s*:|"
    r"payment\.card\s*=|"
    r"\{\s*user\s*:"
    r")"
)


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in value if char.isascii() and char.isdigit()]
    if not 16 <= len(digits) <= 19:
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


def _valid_date(value: str) -> bool:
    for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            datetime.strptime(value, date_format)
        except ValueError:
            continue
        return True
    return False


def _entity(text: str, entity_type: str, span: tuple[int, int]) -> DetectedEntity:
    start, end = span
    return DetectedEntity(
        entity_type,
        start,
        end,
        text[start:end],
        0.999,
        "labelled_record_v3_29",
        600,
    )


def _field_candidates(text: str) -> Iterator[DetectedEntity]:
    normalized = text.translate(_NORMALIZE)
    for entity_type, pattern in _FIELDS:
        for match in pattern.finditer(normalized):
            value = text[slice(*match.span("value"))]
            if entity_type == "BANK_CARD" and not _valid_luhn(value):
                continue
            if entity_type == "PASSPORT_ISSUE_DATE" and not _valid_date(value):
                continue
            yield _entity(text, entity_type, match.span("value"))
    for match in _DOCUMENT_RECORD.finditer(normalized):
        for group, entity_type in (
            ("passport", "PASSPORT_RF"),
            ("issuer", "PASSPORT_ISSUER"),
            ("date", "PASSPORT_ISSUE_DATE"),
            ("division", "DIVISION_CODE"),
        ):
            yield _entity(text, entity_type, match.span(group))


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities, entity_type_tiebreak=True)


def detect(text: str) -> list[DetectedEntity]:
    """Detect strict labelled records while preserving v3.26 as the base."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    base = detect_v3_26(text)
    if len(text) >= 100_000:
        return base
    if _SUPPORTED_RECORD.search(text.translate(_NORMALIZE)) is None:
        return base
    return _merge([*base, *_field_candidates(text)])
