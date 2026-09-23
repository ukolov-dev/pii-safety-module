# ruff: noqa: E501
"""Candidate v3.4: high-context recall extensions over ownership-gated v3.2.

The additional recognizers model reusable Russian form/prose constructions.  They
require strong semantic anchors and do not modify the production detector.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from app.detection.models import DetectedEntity
from proposals.detector_v3_2 import detect as detect_v3_2

_RU_WORD = r"[\u0410-\u042f\u0401\u0430-\u044f\u0451]{2,}(?:-[\u0410-\u042f\u0401\u0430-\u044f\u0451]{2,})?"
_PERSON_VALUE = rf"{_RU_WORD}(?:\s+{_RU_WORD}){{2}}"
_LATIN_NAME = r"[A-Z][A-Z'\u2019-]+(?:[ /]+[A-Z][A-Z'\u2019-]+){1,3}"
_END = r"(?=\s*(?:[,;]|\.(?:\s|$)|$))"

_PERSON_PATTERNS = (
    re.compile(
        rf"\b\u0444\u0430\u043c\u0438\u043b\u0438\u044f\s*,\s*\u0438\u043c\u044f\s*,\s*\u043e\u0442\u0447\u0435\u0441\u0442\u0432\u043e\s*[:\u2014-]\s*(?P<value>{_PERSON_VALUE})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:\u043d\u0430\s+\u0438\u043c\u044f|\u043f\u043e\u043b\u0443\u0447\u0435\u043d\w*\s+\u043e\u0442|\u0437\u0430\u044f\u0432\u043a\w*\s+\u043f\u043e\u0434\u0430\u043b\w*|\u043c\u0435\u043d\u044f\s+\u0437\u043e\u0432\u0443\u0442)\s+(?P<value>{_PERSON_VALUE})",
        re.IGNORECASE,
    ),
    re.compile(rf"\b\u0430\u043d\u043a\u0435\u0442\u0430\s*:\s*(?P<value>{_PERSON_VALUE})(?=\s*[;,])", re.IGNORECASE),
)

_DIVISION_LABEL = re.compile(
    r"\b(?:\u043a\u043e\u0434\s+(?:\u0432\u044b\u0434\u0430\u0432\u0448\u0435\u0433\u043e\s+)?\u043f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u044f|\u043a\s*/\s*\u043f)\s*[:\u2116\u2014-]?\s*"
    r"(?P<value>\d{3}[ /-]\d{3})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_IN_PERSONAL_FILE = re.compile(
    r"\b\u043a\u043e\u0434\s+(?P<value>\d{3}[ /-]\d{3})(?!\d)", re.IGNORECASE
)

_ORDINAL_DAYS = (
    "\u043f\u0435\u0440\u0432\u043e\u0433\u043e|\u0432\u0442\u043e\u0440\u043e\u0433\u043e|\u0442\u0440\u0435\u0442\u044c\u0435\u0433\u043e|\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u0433\u043e|\u043f\u044f\u0442\u043e\u0433\u043e|\u0448\u0435\u0441\u0442\u043e\u0433\u043e|\u0441\u0435\u0434\u044c\u043c\u043e\u0433\u043e|"
    "\u0432\u043e\u0441\u044c\u043c\u043e\u0433\u043e|\u0434\u0435\u0432\u044f\u0442\u043e\u0433\u043e|\u0434\u0435\u0441\u044f\u0442\u043e\u0433\u043e|\u043e\u0434\u0438\u043d\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0434\u0432\u0435\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0442\u0440\u0438\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|"
    "\u0447\u0435\u0442\u044b\u0440\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u043f\u044f\u0442\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0448\u0435\u0441\u0442\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0441\u0435\u043c\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0432\u043e\u0441\u0435\u043c\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|"
    r"\u0434\u0435\u0432\u044f\u0442\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u043f\u0435\u0440\u0432\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0432\u0442\u043e\u0440\u043e\u0433\u043e|"
    r"\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0442\u0440\u0435\u0442\u044c\u0435\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u043f\u044f\u0442\u043e\u0433\u043e|"
    r"\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0448\u0435\u0441\u0442\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0441\u0435\u0434\u044c\u043c\u043e\u0433\u043e|\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0432\u043e\u0441\u044c\u043c\u043e\u0433\u043e|"
    r"\u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c\s+\u0434\u0435\u0432\u044f\u0442\u043e\u0433\u043e|\u0442\u0440\u0438\u0434\u0446\u0430\u0442\u043e\u0433\u043e|\u0442\u0440\u0438\u0434\u0446\u0430\u0442\u044c\s+\u043f\u0435\u0440\u0432\u043e\u0433\u043e"
)
_MONTH = "\u044f\u043d\u0432\u0430\u0440\u044f|\u0444\u0435\u0432\u0440\u0430\u043b\u044f|\u043c\u0430\u0440\u0442\u0430|\u0430\u043f\u0440\u0435\u043b\u044f|\u043c\u0430\u044f|\u0438\u044e\u043d\u044f|\u0438\u044e\u043b\u044f|\u0430\u0432\u0433\u0443\u0441\u0442\u0430|\u0441\u0435\u043d\u0442\u044f\u0431\u0440\u044f|\u043e\u043a\u0442\u044f\u0431\u0440\u044f|\u043d\u043e\u044f\u0431\u0440\u044f|\u0434\u0435\u043a\u0430\u0431\u0440\u044f"
_SPELLED_BIRTH_DATE = re.compile(
    rf"\b\u0440\u043e\u0434\u0438\u043b(?:\u0441\u044f|\u0430\u0441\u044c)\s+(?P<value>(?:{_ORDINAL_DAYS})\s+(?:{_MONTH})\s+(?:19|20)\d{{2}}\s+\u0433\u043e\u0434\u0430)",
    re.IGNORECASE,
)
_NUMERIC_DATE = r"(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:19|20)\d{2}"
_TEXT_DATE = rf"(?:[1-9]|[12]\d|3[01])\s+(?:{_MONTH})\s+(?:19|20)\d{{2}}(?:\s*\u0433(?:\u043e\u0434\u0430|\u043e\u0434|\.)?)?"
_ISSUE_DATE_PATTERNS = (
    re.compile(
        rf"\b(?:\u043a\u043e\u0433\u0434\u0430\s+\u0432\u044b\u0434\u0430\u043d\s+\u043f\u0430\u0441\u043f\u043e\u0440\u0442|\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\w*\s+\u043e\u0444\u043e\u0440\u043c\u0438\u043b\w*\s+\u0438\s+\u0432\u044b\u0434\u0430\u043b\w*(?:\s+\u0435\u043c\u0443|\s+\u0435\u0439)?)\s*[:\u2014-]?\s*(?P<value>{_NUMERIC_DATE}|{_TEXT_DATE})",
        re.IGNORECASE,
    ),
    re.compile(rf"\b\u043f\u0430\u0441\u043f\u043e\u0440\u0442\b[^.\n]*?\b(?P<value>{_NUMERIC_DATE})(?=[,.;]|$)", re.IGNORECASE),
    re.compile(rf"\b\u043b\u0438\u0447\u043d\u043e\u0435\s+\u0434\u0435\u043b\u043e\b[^.\n]*?\b(?P<value>{_NUMERIC_DATE})(?=[,.;]|$)", re.IGNORECASE),
)

_BIRTHPLACE_PATTERNS = (
    re.compile(
        r"\b\u043c\u0435\u0441\u0442\u043e\s+\u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f\s*[:\u2014-]?\s*(?P<value>(?:\u0433\u043e\u0440\.|\u0433\.|\u0433\u043e\u0440\u043e\u0434|\u0441\u0435\u043b\u043e|\u043f\u043e\u0441[\u0451\u0435]\u043b\u043e\u043a)\s*[^.;\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\u0440\u043e\u0434\u0438\u043b(?:\u0441\u044f|\u0430\u0441\u044c)\s+(?:[^,.;]+\s+)?\u0432\s+(?P<value>(?:\u0433\u043e\u0440\u043e\u0434\u0435|\u0433\.|\u043f\u043e\u0441[\u0451\u0435]\u043b\u043a\u0435|\u0441\u0435\u043b\u0435)\s+[^,.;\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b\u0440\u043e\u0434\u0438\u043b(?:\u0441\u044f|\u0430\u0441\u044c)\s+(?:{_NUMERIC_DATE}|{_TEXT_DATE})\s+\u0432\s+"
        r"(?P<value>(?:\u0433\u043e\u0440\u043e\u0434\u0435|\u0433\.|\u043f\u043e\u0441[\u0451\u0435]\u043b\u043a\u0435|\u0441\u0435\u043b\u0435)\s+[^,.;\n]+)",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP_PROSE = re.compile(
    r"\b\u0433\u0440\u0430\u0436\u0434\u0430\u043d\u0438\u043d\u043e\u043c\s+(?P<value>(?:\u0420\u0435\u0441\u043f\u0443\u0431\u043b\u0438\u043a\u0438\s+)?[\u0410-\u042f\u0401][\u0410-\u042f\u0401\u0430-\u044f\u0451-]+(?:\s+[\u0410-\u042f\u0401][\u0410-\u042f\u0401\u0430-\u044f\u0451-]+)?)",
    re.IGNORECASE,
)

_ISSUER_PATTERNS = (
    re.compile(
        r"\b\u043e\u0440\u0433\u0430\u043d\s*,?\s*\u0432\u044b\u0434\u0430\u0432\u0448\u0438\u0439\s+\u043f\u0430\u0441\u043f\u043e\u0440\u0442\s*:\s*"
        r"(?P<value>(?:\u0423\u041c\u0412\u0414|\u041c\u0412\u0414|\u0424\u041c\u0421|\u041e\u0422\u0414\u0415\u041b\u041e\u041c)\b[^,;\n]*?)(?=\.\s*$|[,;]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:\u0431\u044b\u043b\w*\s+)?\u0432\u044b\u0434\u0430\u043d\w*\s+"
        r"(?P<value>(?:\u0423\u041c\u0412\u0414|\u041c\u0412\u0414|\u0424\u041c\u0421|\u041e\u0422\u0414\u0415\u041b\u041e\u041c)\b[^,;\n]*?)"
        r"(?=\.\s*$|[,;]|\s+\d{2}[./-]\d{2}[./-]\d{4}|$)",
        re.IGNORECASE,
    ),
)

_DRIVER_LICENSE = re.compile(
    r"\b(?:\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u0441\u043a\u0438\u0435\s+\u043f\u0440\u0430\u0432\u0430|\u0432\s*/?\s*\u0443(?:\s+\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044f)?)\s*[:\u2116\u2014-]?\s*"
    r"(?P<value>\d{2}[ -]?\d{2}(?:\s*\u2116)?[ -]?\d{6})(?!\d)",
    re.IGNORECASE,
)
_CVV_PAREN_LABEL = re.compile(
    r"\b(?:\u043a\u043e\u0434\s+\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438\s+\u043a\u0430\u0440\u0442\u044b\s*)?\((?:CVC2?|CVV2?)\)\s*:\s*(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_PATTERNS = (
    re.compile(rf"\bCARD\s+HOLDER\s*[:\u2014-]?\s*(?P<value>{_LATIN_NAME}){_END}", re.IGNORECASE),
    re.compile(rf"\b\u0432\u043b\u0430\u0434\u0435\u043b\u0435\u0446\s*[:\u2014-]?\s*(?P<value>{_LATIN_NAME}){_END}", re.IGNORECASE),
)

_PERSONAL_ADDRESS = re.compile(
    r"\b(?:\u0430\u0434\u0440\u0435\u0441\s+\u0444\u0438\u0437\u043b\u0438\u0446\u0430|\u043c\u0435\u0441\u0442\u043e\s+\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438\s+\u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f|\u044f\s+\u0436\u0438\u0432\u0443\b)",
    re.IGNORECASE,
)
_ADDRESS_PATTERNS = (
    ("ADDRESS_COUNTRY", re.compile(r"(?P<value>\u0420\u043e\u0441\u0441\u0438\u044f)(?=\s*,)", re.IGNORECASE)),
    ("ADDRESS_POSTAL_CODE", re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")),
    ("ADDRESS_CITY", re.compile(r"\b(?:\u0433\u043e\u0440\u043e\u0434|\u0433\.|\u0433\u043e\u0440\u043e\u0434\u0435)\s*(?P<value>[\u0410-\u042f\u0401][\u0410-\u042f\u0401\u0430-\u044f\u0451-]+)", re.IGNORECASE)),
    ("ADDRESS_STREET", re.compile(r"\b(?:\u0443\u043b\u0438\u0446\u0430|\u0443\u043b\.|\u0443\u043b\u0438\u0446\u0435)\s*(?P<value>[\u0410-\u042f\u0401][\u0410-\u042f\u0401\u0430-\u044f\u0451-]+)|\b(?P<prefix>[\u0410-\u042f\u0401][\u0410-\u042f\u0401\u0430-\u044f\u0451-]+)\s+\u043f\u0440\u043e\u0441\u043f\u0435\u043a\u0442", re.IGNORECASE)),
    ("ADDRESS_HOUSE", re.compile(r"\b(?:\u0434\u043e\u043c|\u0434\.)\s*(?P<value>\d+[\u0410-\u042f\u0401A-Z]?)(?=\s*[,.;])", re.IGNORECASE)),
    ("ADDRESS_APARTMENT", re.compile(r"\b(?:\u043a\u0432\u0430\u0440\u0442\u0438\u0440\u0430|\u043a\u0432\.)\s*(?P<value>\d+)(?=\s*[,.;]|$)", re.IGNORECASE)),
)
_ROLE_MAILBOX = re.compile(
    r"^(?:tender|procurement|purchasing|newsdesk|editorial|media|press|sales|support|"
    r"info|office|jobs?|career|security|noreply|contact)(?:[+._-]|$)",
    re.IGNORECASE,
)
_PUBLIC_MAILBOX_CONTEXT = re.compile(
    r"\b(?:\u0437\u0430\u043a\u0443\u043f\u043e\u043a|\u0437\u0430\u043a\u0443\u043f\u043a\w*|\u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\w*|\u0440\u0435\u0434\u0430\u043a\u0446\u0438\u043e\u043d\u043d\w*|"
    r"\u043f\u0440\u0435\u0441\u0441[- ]\u0441\u043b\u0443\u0436\u0431\w*|\u043e\u0431\u0449\w*\s+\u044f\u0449\u0438\u043a|\u043a\u043e\u043c\u043f\u0430\u043d\u0438\w*|\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 97,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.97, source, priority)


def _valid_numeric_date(value: str) -> bool:
    day, month, year = (int(part) for part in re.split(r"[./-]", value))
    try:
        datetime(year, month, day)
    except ValueError:
        return False
    return True


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON_PATTERNS:
        for match in pattern.finditer(text):
            yield _entity(text, "PERSON", match.span("value"), "person_context_v3_4", 75)

    for match in _DIVISION_LABEL.finditer(text):
        yield _entity(text, "DIVISION_CODE", match.span("value"), "division_label_v3_4")
    if re.search(r"\b\u043b\u0438\u0447\u043d\u043e\u0435\s+\u0434\u0435\u043b\u043e\b", text, re.IGNORECASE):
        for match in _DIVISION_IN_PERSONAL_FILE.finditer(text):
            yield _entity(text, "DIVISION_CODE", match.span("value"), "division_file_v3_4")

    for match in _SPELLED_BIRTH_DATE.finditer(text):
        yield _entity(text, "BIRTH_DATE", match.span("value"), "spelled_birth_date_v3_4")

    for pattern in _ISSUE_DATE_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group("value")
            if re.fullmatch(_NUMERIC_DATE, value) is None or _valid_numeric_date(value):
                yield _entity(text, "PASSPORT_ISSUE_DATE", match.span("value"), "issue_date_v3_4")

    for pattern in _BIRTHPLACE_PATTERNS:
        for match in pattern.finditer(text):
            yield _entity(text, "PLACE_OF_BIRTH", match.span("value"), "birthplace_v3_4")
    for match in _CITIZENSHIP_PROSE.finditer(text):
        yield _entity(text, "CITIZENSHIP", match.span("value"), "citizenship_v3_4")
    for pattern in _ISSUER_PATTERNS:
        for match in pattern.finditer(text):
            yield _entity(text, "PASSPORT_ISSUER", match.span("value"), "issuer_v3_4", 98)
    for match in _DRIVER_LICENSE.finditer(text):
        yield _entity(text, "DRIVER_LICENSE_RF", match.span("value"), "driver_license_v3_4", 99)
    for match in _CVV_PAREN_LABEL.finditer(text):
        yield _entity(text, "CVV", match.span("value"), "cvv_label_v3_4", 99)
    for pattern in _CARDHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            yield _entity(text, "CARDHOLDER_NAME", match.span("value"), "cardholder_v3_4", 99)

    if _PERSONAL_ADDRESS.search(text):
        for entity_type, pattern in _ADDRESS_PATTERNS:
            for match in pattern.finditer(text):
                group = "prefix" if entity_type == "ADDRESS_STREET" and match.groupdict().get("prefix") else "value"
                yield _entity(text, entity_type, match.span(group), "personal_address_v3_4", 98)


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        entities,
        key=lambda item: (-item.priority, -item.confidence, -(item.end - item.start), item.start),
    )
    accepted: list[DetectedEntity] = []
    for entity in ranked:
        if not any(_overlap(entity, existing) for existing in accepted):
            accepted.append(entity)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def detect(text: str) -> list[DetectedEntity]:
    """Return ownership-gated v3.2 plus strongly anchored recall candidates."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    merged = _merge([*detect_v3_2(text), *_supplemental(text)])
    public_mailbox = _PUBLIC_MAILBOX_CONTEXT.search(text) is not None
    return [
        entity
        for entity in merged
        if not (
            entity.entity_type == "EMAIL"
            and public_mailbox
            and _ROLE_MAILBOX.search(entity.text.split("@", 1)[0])
        )
    ]
