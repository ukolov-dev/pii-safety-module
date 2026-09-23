"""Candidate v3.24: semantic field families and record association over v3.22."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from .detector_v3_22 import detect as detect_v3_22
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_CITY = rf"{_WORD}(?:[ ]+{_WORD})?"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-./·](?:1[0-2]|0?[1-9])[-./·](?:19|20)\d{2}"
_SEP = r"[\s|/>:=\[\]-]*"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3}"

_SHADOW_TABLE = str.maketrans(
    {
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "a": "а",
        "c": "с",
        "e": "е",
        "o": "о",
        "p": "р",
        "x": "х",
        " ": " ",
        " ": " ",
        "\t": " ",
        "_": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "·": ".",
    }
)


@dataclass(frozen=True, slots=True)
class FieldRule:
    entity_type: str
    pattern: re.Pattern[str]
    source: str
    validate_date: bool = False


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


_FIELD_RULES = (
    FieldRule(
        "PHONE_RF",
        _rx(
            rf"\b(?:телефон{_SEP}(?:клиент\w*)?|"
            rf"мобильн\w*{_SEP}заявител\w*|номер\s+сам\w*\s+клиент\w*){_SEP}"
            r"(?P<value>(?:\+7|8)(?:[|\s().-]*\d){10})(?!\d)"
        ),
        "phone_field_family_v3_24",
    ),
    FieldRule(
        "PASSPORT_RF",
        _rx(rf"\bпаспорт(?:\s+РФ)?{_SEP}(?P<value>\d{{2}}-\d{{2}}\s*\|\s*\d{{6}})"),
        "passport_pipe_v3_24",
    ),
    FieldRule(
        "PASSPORT_RF",
        _rx(
            r"\bдокумент\w*[^.;\n]{0,45}?"
            r"(?P<value>серия\s+\d{4}\s*;\s*паспорт\s*№\s*\d{6})"
        ),
        "passport_split_labels_v3_24",
    ),
    FieldRule(
        "DIVISION_CODE",
        _rx(rf"\bкод{_SEP}подразделения{_SEP}(?P<value>\d{{3}}[- /]\d{{3}})(?!\d)"),
        "division_field_family_v3_24",
    ),
    FieldRule(
        "BIRTH_DATE",
        _rx(rf"\bдата\s+рожд\.?{_SEP}(?P<value>{_DATE})(?!\d)"),
        "birth_date_field_family_v3_24",
        True,
    ),
    FieldRule(
        "PLACE_OF_BIRTH",
        _rx(
            rf"\bместо\s+рождения{_SEP}"
            rf"(?P<value>(?:с\.|(?:село|город|деревня|пос[ёе]лок))\s+"
            rf"{_CITY}(?:\s+{_WORD}\s+области)?)(?=\s*(?:\n|[;.]|$))"
        ),
        "birthplace_field_family_v3_24",
    ),
    FieldRule(
        "PLACE_OF_BIRTH",
        _rx(rf"\bродил\w*\s+в\s+(?P<value>городе\s+{_CITY})(?=\s+(?:и|[,;.]))"),
        "birthplace_inflected_v3_24",
    ),
    FieldRule(
        "PLACE_OF_BIRTH",
        _rx(rf"\bместо\s+рождения{_SEP}(?P<value>город\s+{_CITY})(?=\s*(?:\n|[;.]|$))"),
        "birthplace_city_field_v3_24",
    ),
    FieldRule(
        "CITIZENSHIP",
        _rx(
            rf"\bгражданство{_SEP}(?P<value>РФ|Россия|Российская\s+Федерация|"
            rf"Республик\w*\s+{_CITY})(?=\s*(?:\n|[;.]|$))"
        ),
        "citizenship_field_family_v3_24",
    ),
    FieldRule(
        "PASSPORT_ISSUER",
        _rx(
            rf"\bкем\s+выдан{_SEP}(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)"
            r"(?:\s+России)?(?:\s+по\s+(?:г\.|[^.;\n|\d])*?)?)"
            r"(?=\s+\d{1,2}[-./]\d{1,2}[-./]\d{4}|\s*(?:\n|[;.]|$))"
        ),
        "issuer_field_family_v3_24",
    ),
    FieldRule(
        "PASSPORT_ISSUER",
        _rx(
            r"\bвыдан{1,2}\s*[:|]?\s*(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)"
            r"(?:\s+России)?(?:\s+по\s+(?:г\.|[^.;\n|\d])*?)?)"
            r"(?=\s+\d{1,2}[-./]\d{1,2}[-./]\d{4}|\s*(?:\n|[;.]|$))"
        ),
        "issuer_verb_family_v3_24",
    ),
    FieldRule(
        "PASSPORT_ISSUE_DATE",
        _rx(rf"(?:\b(?:дата\s+выдачи|когда)|(?:^|\n)дата){_SEP}(?P<value>{_DATE})(?!\d)"),
        "issue_date_field_family_v3_24",
        True,
    ),
    FieldRule(
        "DRIVER_LICENSE_RF",
        _rx(rf"\bВУ\s+РФ{_SEP}(?P<value>\d{{2}}\s+\d{{2}}\s+\d{{6}})(?!\d)"),
        "license_field_family_v3_24",
    ),
    FieldRule(
        "ADDRESS_COUNTRY",
        _rx(rf"\bстрана\s+проживания{_SEP}(?P<value>РФ|Россия|Российская\s+Федерация)"),
        "country_field_family_v3_24",
    ),
    FieldRule(
        "ADDRESS_CITY",
        _rx(
            rf"\b(?:город{_SEP}место\s+жительства|домашний\s+город){_SEP}(?P<value>{_CITY})(?=\s*(?:\n|[;.]|$))"
        ),
        "city_field_family_v3_24",
    ),
    FieldRule(
        "ADDRESS_CITY",
        _rx(rf"\bживу\s+в\s+городе\s+(?P<value>{_CITY})(?=\s*[.;,])"),
        "city_inflected_residence_v3_24",
    ),
    FieldRule(
        "ADDRESS_STREET",
        _rx(rf"\bулица\s+клиента{_SEP}(?P<value>{_WORD})(?=\s*(?:\n|[;.]|$))"),
        "street_field_family_v3_24",
    ),
    FieldRule(
        "ADDRESS_HOUSE",
        _rx(rf"\bдом{_SEP}физлица{_SEP}(?P<value>\d{{1,4}}[А-ЯЁA-Z]?)(?!\d)"),
        "house_field_family_v3_24",
    ),
    FieldRule(
        "ADDRESS_HOUSE",
        _rx(rf"(?:^|\n)дом{_SEP}(?P<value>\d{{1,4}}[А-ЯЁA-Z]?)(?!\d)"),
        "house_record_field_v3_24",
    ),
    FieldRule(
        "ADDRESS_APARTMENT",
        _rx(rf"\bквартира{_SEP}(?P<value>\d{{1,5}})(?!\d)"),
        "flat_field_family_v3_24",
    ),
    FieldRule(
        "CVV",
        _rx(rf"\bCVV\s+клиента{_SEP}(?P<value>\d{{3}})(?!\d)"),
        "cvv_field_family_v3_24",
    ),
    FieldRule(
        "PIN",
        _rx(rf"\bPIN{_SEP}персональн\w*{_SEP}(?P<value>\d{{4}})(?!\d)"),
        "pin_field_family_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        _rx(rf"\bCARDHOLDER\s+NAME{_SEP}(?P<value>{_LATIN_NAME})(?=\s*(?:\n|[;.]|$))"),
        "cardholder_field_family_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        _rx(rf"\bна\s+карте\s+клиент\w*\s+выбито\s+(?P<value>{_LATIN_NAME})(?=\s*[.;])"),
        "cardholder_prose_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        _rx(rf"\bдержатель{_SEP}(?P<value>{_LATIN_NAME})(?=\s*(?:\n|[;.]|$))"),
        "cardholder_holder_field_v3_24",
    ),
)

_PERSONAL_EMAIL = _rx(
    rf"\b(?:личн\w*\s+адрес\w*\s+заявител\w*|личн\w*\s+"
    rf"почт\w*|E-MAIL|EMAIL\s+личный){_SEP}(?P<value>[\w.+-]+@[\w.-]+\.[A-Za-z]{{2,}})"
)
_PERSONAL_EMAIL_ORIGINAL = re.compile(
    rf"\b(?:личн\w*\s+адрес\w*\s+заявител\w*(?:\s+[А-ЯЁа-яё]+){{0,3}}|личн\w*\s+"
    rf"почт\w*|E-MAIL|EMAIL_ЛИЧНЫЙ){_SEP}(?P<value>[\w.+-]+@[\w.-]+\.[A-Za-z]{{2,}})",
    re.IGNORECASE,
)
_LATIN_FIELD_RULES = (
    FieldRule(
        "CVV",
        re.compile(rf"\bCVV_КЛИЕНТА{_SEP}(?P<value>\d{{3}})(?!\d)", re.I),
        "cvv_original_field_v3_24",
    ),
    FieldRule(
        "PIN",
        re.compile(rf"\bPIN{_SEP}персональн\w*{_SEP}(?P<value>\d{{4}})(?!\d)", re.I),
        "pin_original_field_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        re.compile(rf"\bCARDHOLDER_NAME{_SEP}(?P<value>{_LATIN_NAME})(?=\s*(?:\n|[;.]|$))", re.I),
        "cardholder_original_field_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        re.compile(
            rf"\bна\s+карте\s+клиент\w*\s+выбито\s+(?P<value>{_LATIN_NAME})(?=\s*[.;])", re.I
        ),
        "cardholder_original_prose_v3_24",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        re.compile(rf"\bдержатель{_SEP}(?P<value>{_LATIN_NAME})(?=\s*(?:\n|[;.]|$))", re.I),
        "cardholder_original_holder_v3_24",
    ),
)
_DELIVERY_RECORD = _rx(
    rf"\bдоставка\s+физлицу{_SEP}(?P<postcode>\d{{6}})\s*,\s*"
    rf"(?P<city>{_CITY})[ ]*(?:\n|,)\s*(?:ул\.| улица)\s*(?P<street>{_WORD})\s*,\s*"
    r"д\.\s*(?P<house>\d{1,4}[А-ЯЁA-Z]?)\s*,\s*кв\.\s*(?P<flat>\d{1,5})"
)
_PIPE_ADDRESS = _rx(
    rf"\bадрес\s*\|\s*(?P<country>РФ|Россия)\s*\|\s*"
    rf"(?P<postcode>\d{{6}})\s*\|\s*(?P<city>{_CITY})\s*\|\s*ул\.\s*(?P<street>{_WORD})\s*\|\s*"
    r"д\.\s*(?P<house>\d{1,4}[А-ЯЁA-Z]?)"
)
_PLAIN_ADDRESS = _rx(
    rf"\b(?:личные\s+данны|адрес)\b[^\n]{{0,20}}\n?"
    rf"(?P<postcode>\d{{6}})\s*,\s*(?P<city>{_CITY})\s*,\s*ул\.\s*(?P<street>{_WORD})\s*,\s*"
    r"д\.\s*(?P<house>\d{1,4}[А-ЯЁA-Z]?)\s*,\s*кв\.\s*(?P<flat>\d{1,5})"
)

_PUBLIC = _rx(
    r"\b(?:общ\w*\s+номер\w*|дежурн\w*\s+смен\w*|кафедр\w*|офис\w*|"
    r"стадион\w*|PUBLIC\s+VENUE|NO[ _-]?REPLY|общ\w*\s+почт\w*)\b"
)
_TECHNICAL = _rx(
    r"\b(?:SDK[ _-]?SAMPLE|PUBLIC[ _-]?TEST|sample|fixture|dummy|инструкц\w*|шаблон\w*|"
    r"тестов\w*|фиктивн\w*)\b"
)
_PUBLIC_LATIN = re.compile(r"\b(?:PUBLIC\s+VENUE|NO[ _-]?REPLY)\b", re.I)
_TECHNICAL_LATIN = re.compile(
    r"\b(?:SDK[ _-]?SAMPLE|PUBLIC[ _-]?TEST|sample|fixture|dummy)\b", re.I
)
_PERSONAL = _rx(r"\b(?:клиент\w*|заявител\w*|физлиц\w*|личн\w*|сам\w*|владел\w*)\b")
_ROLE_EMAIL = re.compile(r"^(?:faculty-office|robot|events?|noreply|no-reply)@", re.IGNORECASE)


def _shadow(text: str) -> str:
    return text.translate(_SHADOW_TABLE)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 260,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, priority)


def _valid_date(value: str) -> bool:
    parts = [int(part) for part in re.split(r"[-./·]", value)]
    try:
        date(parts[2], parts[1], parts[0])
    except ValueError:
        return False
    return True


def _candidates(text: str) -> Iterator[DetectedEntity]:
    shadow = _shadow(text)
    for rule in _FIELD_RULES:
        for match in rule.pattern.finditer(shadow):
            span = match.span("value")
            if rule.validate_date and not _valid_date(text[slice(*span)]):
                continue
            yield _entity(text, rule.entity_type, span, rule.source)

    for rule in _LATIN_FIELD_RULES:
        for match in rule.pattern.finditer(text):
            yield _entity(text, rule.entity_type, match.span("value"), rule.source)

    for match in _PERSONAL_EMAIL.finditer(shadow):
        yield _entity(text, "EMAIL", match.span("value"), "personal_email_field_v3_24")
    for match in _PERSONAL_EMAIL_ORIGINAL.finditer(text):
        yield _entity(text, "EMAIL", match.span("value"), "personal_email_original_v3_24")

    record_specs = (
        (
            _DELIVERY_RECORD,
            ("city", "ADDRESS_CITY"),
            ("street", "ADDRESS_STREET"),
            ("house", "ADDRESS_HOUSE"),
            ("flat", "ADDRESS_APARTMENT"),
        ),
        (
            _PIPE_ADDRESS,
            ("country", "ADDRESS_COUNTRY"),
            ("postcode", "ADDRESS_POSTAL_CODE"),
            ("city", "ADDRESS_CITY"),
            ("street", "ADDRESS_STREET"),
            ("house", "ADDRESS_HOUSE"),
        ),
        (
            _PLAIN_ADDRESS,
            ("city", "ADDRESS_CITY"),
            ("street", "ADDRESS_STREET"),
            ("house", "ADDRESS_HOUSE"),
            ("flat", "ADDRESS_APARTMENT"),
        ),
    )
    for pattern, *fields in record_specs:
        for match in pattern.finditer(shadow):
            for group, entity_type in fields:
                yield _entity(text, entity_type, match.span(group), "address_record_v3_24")


def _context(text: str, start: int, end: int, radius: int = 220) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    original_context = _context(text, entity.start, entity.end)
    context = _shadow(original_context)
    public = (
        _PUBLIC.search(context) is not None or _PUBLIC_LATIN.search(original_context) is not None
    )
    technical = (
        _TECHNICAL.search(context) is not None
        or _TECHNICAL_LATIN.search(original_context) is not None
    )
    if entity.entity_type == "PERSON" and re.search(r"_{3,}|\n", entity.text):
        return True
    if technical and entity.entity_type in {
        "BANK_CARD",
        "CVV",
        "PIN",
        "DIVISION_CODE",
        "PASSPORT_ISSUE_DATE",
    }:
        return True
    if entity.entity_type == "EMAIL":
        return _ROLE_EMAIL.search(entity.text) is not None or (
            public and not _PERSONAL.search(context)
        )
    if entity.entity_type == "PHONE_RF":
        if not public:
            return False
        personal_matches = list(_PERSONAL.finditer(context))
        public_matches = list(_PUBLIC.finditer(context))
        if not personal_matches or not public_matches:
            return True
        window_start = max(0, entity.start - 220)
        relative_midpoint = (entity.start + entity.end) // 2 - window_start
        personal_distance = min(
            abs((item.start() + item.end()) // 2 - relative_midpoint) for item in personal_matches
        )
        public_distance = min(
            abs((item.start() + item.end()) // 2 - relative_midpoint) for item in public_matches
        )
        return public_distance <= personal_distance
    if entity.entity_type.startswith("ADDRESS_"):
        return re.search(r"\bстадион\w*\b", context, re.I) is not None
    return False


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with semantic field families and local evidence suppression."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge([*detect_v3_22(text), *_candidates(text)])
        if not _suppressed(text, entity)
    ]
