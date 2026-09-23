"""Candidate v3.28: consistent field parsing and broader document shapes.

This layer keeps the component-value span convention used by the production
detectors and disclosed datasets through v16.  It adds general field layouts,
Cyrillic cardholder names, alphanumeric driver licences, CIS-country values,
and clause-local corrections for over-wide inherited spans.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from .detector_v3_27 import detect as detect_v3_27
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_CAP = r"(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,})(?:-(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,}))*"
_NAME3 = rf"{_CAP}(?:\s+{_CAP}){{2}}"
_COUNTRY = rf"{_CAP}(?:\s+{_CAP})?"
_CITY = rf"{_CAP}(?:\s+{_CAP})?"
_STREET = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*(?:\s+[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*){0,2}"
_DATE_Y_FIRST = r"(?:19|20)\d{2}[-./](?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])"
_TEXT_DATE = (
    r"(?:[0-3]?\d|(?:перв|втор|треть|четв[ёе]рт|пят|шест|седьм|восьм|девят|десят|одиннадцат|двенадцат|тринадцат|четырнадцат|пятнадцат|шестнадцат|семнадцат|восемнадцат|девятнадцат|двадцат)(?:ого|его|ьего|надцатого)?)"
    r"\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
    r"\s+(?:19|20)\d{2}(?:\s*г(?:ода|\.)?)?"
)

_NORMALIZE = str.maketrans(
    {
        "\u00a0": " ",
        "\u202f": " ",
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


def _field_patterns(label: str, value: str) -> tuple[re.Pattern[str], ...]:
    """Build common prose, quoted-field and profile layouts."""

    return (
        _rx(
            rf"\b(?:{label})(?:\s+клиент\w*)?\s*[:=-]\s*"
            rf"(?P<value>{value})(?=\s*(?:[.;\n]|$))"
        ),
        _rx(
            rf"\bполе\s+[«\"](?:{label})(?:\s+клиент\w*)?[»\"]\s+"
            rf"содержит\s+(?P<value>{value})(?=\s*(?:[.;\n]|$))"
        ),
        _rx(
            rf"\[\s*\"(?:{label})(?:\s+клиент\w*)?\"\s*\]\s*=\s*\""
            rf"(?P<value>{value})(?=\")"
        ),
    )


def _component_patterns(
    label: str, designator: str, value: str
) -> tuple[re.Pattern[str], ...]:
    """Build field layouts where the semantic designator is outside the value span."""

    return (
        _rx(
            rf"\b(?:{label})(?:\s+клиент\w*)?\s*[:=-]\s*(?:{designator})\s*"
            rf"(?P<value>{value})(?=\s*(?:[.;\n]|$))"
        ),
        _rx(
            rf"\bполе\s+[«\"](?:{label})(?:\s+клиент\w*)?[»\"]\s+"
            rf"содержит\s+(?:{designator})\s*(?P<value>{value})(?=\s*(?:[.;\n]|$))"
        ),
        _rx(
            rf"\[\s*\"(?:{label})(?:\s+клиент\w*)?\"\s*\]\s*=\s*\""
            rf"(?:{designator})\s*(?P<value>{value})(?=\")"
        ),
    )


_FIELD_RULES: tuple[tuple[str, tuple[re.Pattern[str], ...], str], ...] = (
    (
        "PLACE_OF_BIRTH",
        _field_patterns(
            r"место\s+рождения",
            r"(?:город|г\.|село|деревня|пос[ёе]лок)\s+[^\",.;\n]+",
        ),
        "place_field_v3_28",
    ),
    (
        "CITIZENSHIP",
        _field_patterns(r"гражданство", _COUNTRY),
        "citizenship_field_v3_28",
    ),
    (
        "ADDRESS_COUNTRY",
        _field_patterns(r"страна\s+проживания", _COUNTRY),
        "country_field_v3_28",
    ),
    (
        "ADDRESS_CITY",
        _field_patterns(r"город\s+проживания", _CITY),
        "city_field_v3_28",
    ),
    (
        "DRIVER_LICENSE_RF",
        _field_patterns(
            r"водительское\s+удостоверение",
            r"\d{2}\s+[А-ЯЁA-Z]{2}\s+\d{6}",
        ),
        "license_alpha_series_v3_28",
    ),
    (
        "PIN",
        _field_patterns(r"(?:ПИН|PIN)-?код\s+карты", r"\d{4}"),
        "pin_field_v3_28",
    ),
    (
        "CARDHOLDER_NAME",
        _field_patterns(
            r"имя\s+держателя\s+карты",
            r"[А-ЯЁA-Z]{2,}(?:-[А-ЯЁA-Z]{2,})?(?:\s+[А-ЯЁA-Z]{2,}(?:-[А-ЯЁA-Z]{2,})?){1,3}",
        ),
        "cardholder_cyrillic_v3_28",
    ),
    (
        "PASSPORT_ISSUER",
        _field_patterns(
            r"паспорт\s+выдан",
            r"ОВМ\s+(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|МВД)(?:\s+России)?[^\".;\n]*",
        ),
        "issuer_field_v3_28",
    ),
    (
        "ADDRESS_STREET",
        _component_patterns(
            r"улица\s+регистрации",
            r"(?:улиц\w*|ул\.|проспект|пр-т|шоссе)",
            _STREET,
        ),
        "street_component_v3_28",
    ),
    (
        "ADDRESS_HOUSE",
        _component_patterns(
            r"дом",
            r"(?:дом|д\.|владение)\s*(?:№\s*)?",
            r"\d{1,4}[А-ЯЁA-Z]?",
        ),
        "house_component_v3_28",
    ),
    (
        "ADDRESS_APARTMENT",
        _component_patterns(
            r"квартира",
            r"(?:квартир\w*|кв\.?)\s*(?:№\s*)?",
            r"\d{1,5}",
        ),
        "flat_component_v3_28",
    ),
)

_ISSUER = _rx(
    r"\b(?:паспорт\s+выдан|орган)\b[^\",;\n]{0,35}?"
    r"(?P<value>ОВМ\s+"
    r"(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|МВД)"
    r"(?:\s+России)?[^\",;\n]*?)(?=\s*(?:[\";,\n]|[.](?:\s|$)|$))"
)
_PERSON_AFTER_ROLE = re.compile(
    rf"\b(?:заявител\w*|налогоплательщик\w*|клиент\w*|получател\w*)\s+"
    rf"(?P<value>(?-i:{_NAME3}))\b",
    re.IGNORECASE,
)
_PERSON_WITH_RECORD = re.compile(
    rf"(?:^|[;\n])\s*(?P<value>{_NAME3})(?=\s+родил\w*\s+в\s+мест\w*\s*:)",
    re.MULTILINE,
)
_LICENSE_SHORT = _rx(
    r"\bВ\s*[/.-]?У\s*[:=-]?\s*(?P<value>\d{2}\s+[А-ЯЁA-Z]{2}\s+\d{6})(?!\d)"
)
_PASSPORT_DOCUMENT = _rx(
    r"\bдокумент\w*\s*[:=-]?\s*(?P<value>\d{2}\s+\d{2}\s+\d{6})(?!\d)"
)
_DIVISION_EXPLICIT = _rx(
    r"\bкод\s+подразделения\b[^\d]{0,35}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)"
)
_PLACE_PROSE = _rx(
    r"\bродил\w*\s+в\s+мест\w*\s*:\s*"
    r"(?P<value>(?:город|г\.|село|деревня|пос[ёе]лок)\s+[^,;.\n]+)"
)
_ISSUER_AFTER_VERB = _rx(
    r"\bвыдан\w*\s+(?P<value>ОВМ\s+(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|МВД)"
    r"(?:\s+России)?[^\d,;.\n]*?)(?=\s+(?:[0-3]?\d\s+[А-ЯЁа-яё]+\s+(?:19|20)\d{2})|[,;.]|$)"
)
_CARDHOLDER_CONTEXT = _rx(
    r"\b(?:держател\w*|получател\w*\s+карт\w*|holder)\s*[:=-]?\s*"
    r"(?P<value>[А-ЯЁA-Z]{2,}(?:-[А-ЯЁA-Z]{2,})?(?:\s+[А-ЯЁA-Z]{2,}(?:-[А-ЯЁA-Z]{2,})?){1,3})(?=\s*[,;.]|$)"
)
_DATE_FIELD_PATTERNS = (
    (
        "BIRTH_DATE",
        _field_patterns(r"дата\s+рождения", _DATE_Y_FIRST),
    ),
    (
        "PASSPORT_ISSUE_DATE",
        _field_patterns(r"дата\s+выдачи\s+паспорта", _DATE_Y_FIRST),
    ),
)
_DATE_FIELD = (
    (
        "BIRTH_DATE",
        _rx(
            rf"\bдата\s+рождения\b[^\dА-ЯЁа-яё]{{0,35}}"
            rf"(?P<value>{_DATE_Y_FIRST}|{_TEXT_DATE})(?=\s*(?:[.;\n]|$))"
        ),
    ),
    (
        "PASSPORT_ISSUE_DATE",
        _rx(
            rf"\b(?:дата\s+выдачи(?:\s+паспорта)?|паспорт\s+выдан)\b"
            rf"[^\dА-ЯЁа-яё]{{0,35}}(?P<value>{_DATE_Y_FIRST}|{_TEXT_DATE})(?=\s*(?:[.;\n]|$))"
        ),
    ),
)

_ADDRESS_RECORD = _rx(
    rf"\b(?:адрес\s+(?:регистрации|проживания)|проживание|регистрация)\b[^\n]{{0,35}}?"
    rf"(?P<country>(?-i:{_COUNTRY}))\s*,\s*(?P<postcode>\d{{6}})\s*,\s*"
    rf"(?:г\.?\s*)?(?P<city>(?-i:{_CITY}))\s*,\s*"
    rf"(?:улиц\w*|ул\.|проспект|пр-т|шоссе)\s+(?P<street>{_STREET})\s*,\s*"
    rf"(?:дом|д\.|владение)\s*(?:№\s*)?(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*"
    rf"(?:квартир\w*|кв\.?)\s*(?:№\s*)?(?P<flat>\d{{1,5}})(?!\d)"
)
_ADDRESS_GROUPS = (
    ("country", "ADDRESS_COUNTRY"),
    ("postcode", "ADDRESS_POSTAL_CODE"),
    ("city", "ADDRESS_CITY"),
    ("street", "ADDRESS_STREET"),
    ("house", "ADDRESS_HOUSE"),
    ("flat", "ADDRESS_APARTMENT"),
)
_REGISTRATION_COUNTRY = _rx(
    rf"\bрегистрация\b[^.;\n]{{0,50}}?\bстрана\s+"
    rf"(?P<value>(?-i:{_COUNTRY}))(?=\s*,)"
)
_SHORT_ADDRESS = _rx(
    rf"\bадрес\s*:\s*(?P<postcode>\d{{6}})\s*,\s*"
    rf"(?P<city>(?-i:{_CITY}))\s*,\s*(?:улиц\w*|ул\.|проспект|пр-т|шоссе)\s+"
    rf"(?P<street>{_STREET})\s*,\s*(?:дом|д\.|владение)\s*(?:№\s*)?"
    rf"(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*(?:квартир\w*|кв\.?)\s*"
    rf"(?:№\s*)?(?P<flat>\d{{1,5}})(?!\d)"
)

_TECH_POSTCODE = _rx(r"\b(?:timeout|параметр\w*|микросекунд\w*|техническ\w*)\b")
_NON_PERSON_CITIZENSHIP = _rx(
    r"\b(?:книг\w*|назван\w*|не\s+описыва\w*\s+гражданств\w*)\b"
)
_PUBLIC_HOUSE = _rx(
    r"\b(?:памятник\w*|архитектур\w*|публичн\w*|музе\w*|корпус\w*)\b"
)
_EXAMPLE = _rx(
    r"\b(?:шаблон\w*|образец|пример\w*|инструкц\w*|документац\w*|подсказк\w*)\b"
)


def _entity(
    text: str, entity_type: str, span: tuple[int, int], source: str, priority: int = 380
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, priority)


def _valid_year_first(value: str) -> bool:
    year, middle, last = (int(item) for item in re.split(r"[-./]", value))
    for month, day in ((middle, last), (last, middle)):
        try:
            date(year, month, day)
        except ValueError:
            continue
        return True
    return False


def _candidates(text: str) -> Iterator[DetectedEntity]:
    shadow = text.translate(_NORMALIZE)
    for entity_type, patterns, source in _FIELD_RULES:
        for pattern in patterns:
            for match in pattern.finditer(shadow):
                yield _entity(text, entity_type, match.span("value"), source)

    for pattern, entity_type, source in (
        (_ISSUER, "PASSPORT_ISSUER", "issuer_ovm_v3_28"),
        (_PERSON_AFTER_ROLE, "PERSON", "person_role_v3_28"),
        (_PERSON_WITH_RECORD, "PERSON", "person_record_v3_28"),
        (_LICENSE_SHORT, "DRIVER_LICENSE_RF", "license_short_v3_28"),
        (_PASSPORT_DOCUMENT, "PASSPORT_RF", "passport_document_v3_28"),
        (_DIVISION_EXPLICIT, "DIVISION_CODE", "division_unicode_v3_28"),
        (_PLACE_PROSE, "PLACE_OF_BIRTH", "place_prose_v3_28"),
        (_ISSUER_AFTER_VERB, "PASSPORT_ISSUER", "issuer_verb_v3_28"),
        (_CARDHOLDER_CONTEXT, "CARDHOLDER_NAME", "cardholder_context_v3_28"),
    ):
        for match in pattern.finditer(shadow):
            yield _entity(text, entity_type, match.span("value"), source)

    for entity_type, pattern in _DATE_FIELD:
        for match in pattern.finditer(shadow):
            value = shadow[slice(*match.span("value"))]
            if re.fullmatch(_DATE_Y_FIRST, value) and not _valid_year_first(value):
                continue
            yield _entity(text, entity_type, match.span("value"), "date_field_v3_28")

    for entity_type, patterns in _DATE_FIELD_PATTERNS:
        for pattern in patterns:
            for match in pattern.finditer(shadow):
                value = shadow[slice(*match.span("value"))]
                if _valid_year_first(value):
                    yield _entity(text, entity_type, match.span("value"), "date_order_v3_28")

    for match in _ADDRESS_RECORD.finditer(shadow):
        for group, entity_type in _ADDRESS_GROUPS:
            yield _entity(text, entity_type, match.span(group), "address_record_v3_28")
    for match in _REGISTRATION_COUNTRY.finditer(shadow):
        yield _entity(text, "ADDRESS_COUNTRY", match.span("value"), "registration_country_v3_28")
    for match in _SHORT_ADDRESS.finditer(shadow):
        for group, entity_type in _ADDRESS_GROUPS[1:]:
            yield _entity(text, entity_type, match.span(group), "short_address_v3_28")


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    window = text[max(0, entity.start - 100) : min(len(text), entity.end + 150)]
    if entity.entity_type == "ADDRESS_POSTAL_CODE":
        return _TECH_POSTCODE.search(window) is not None
    if entity.entity_type == "CITIZENSHIP":
        return _NON_PERSON_CITIZENSHIP.search(window) is not None
    if entity.entity_type == "ADDRESS_HOUSE":
        return _PUBLIC_HOUSE.search(window) is not None
    if entity.entity_type in {"DIVISION_CODE", "PASSPORT_ISSUE_DATE"}:
        return _EXAMPLE.search(window) is not None
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII while retaining the established component span convention."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = detect_v3_27(text)
    if len(text) >= 100_000:
        return inherited
    return [
        entity
        for entity in _merge([*inherited, *_candidates(text)])
        if not _suppressed(text, entity)
    ]
