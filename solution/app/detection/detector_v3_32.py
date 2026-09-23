"""Candidate v3.32: strict field-aware extraction layered on v3.26.

The production detector remains the source of broad natural-language coverage.
This candidate adds a small record parser for JSON, dotted keys, form exports,
and OCR-like line records.  A field alias selects the entity type while a
type-specific value grammar prevents arbitrary neighbouring text from being
masked.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from .detector_v3_26 import detect as detect_v3_26
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_FLAGS = re.IGNORECASE | re.MULTILINE
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])[-./](?:19|20)\d{2}"
_EMAIL = r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"
_PHONE = r"(?:\+?7|8)(?:[\s().-]*\d){10}"
_CAP = r"(?:[\u0410-ЯЁ][\u0430-яё]+|[\u0410-ЯЁ]{2,})(?:-(?:[\u0410-ЯЁ][\u0430-яё]+|[\u0410-ЯЁ]{2,}))*"
_PERSON = rf"{_CAP}(?:\s+{_CAP}){{2}}"
_CITY = rf"{_CAP}(?:\s+{_CAP})?"
_CARDHOLDER = (
    r"[A-ZА-ЯЁ][A-ZА-ЯЁ'\-’]+"
    r"(?:\s+[A-ZА-ЯЁ][A-ZА-ЯЁ'\-’]+){1,3}?"
)

# Quotes around keys and values are deliberately optional: this covers JSON,
# logfmt, YAML-like exports, dotted keys, and ordinary web-form serialization.
_KEY_LEFT = r"(?<![\w.])(?:[\"'])?"
_KEY_RIGHT = r"(?:[\"'])?\s*[:=]\s*(?:[\"'])?"
_VALUE_RIGHT = r"(?=[\"'}\],;\s]|$)"


@dataclass(frozen=True, slots=True)
class FieldRule:
    entity_type: str
    aliases: str
    value: str
    source: str
    priority: int = 390

    def compile(self) -> re.Pattern[str]:
        return re.compile(
            rf"{_KEY_LEFT}(?:{self.aliases}){_KEY_RIGHT}"
            rf"(?P<value>{self.value}){_VALUE_RIGHT}",
            _FLAGS,
        )


_RULES = tuple(
    (rule, rule.compile())
    for rule in (
        FieldRule(
            "PERSON",
            r"customer|owner|user|person|client|full[_.-]?name|fio|фио|клиент|владелец",
            _PERSON,
            "record_person_v3_32",
        ),
        FieldRule(
            "BIRTH_DATE",
            r"birth(?:[_.-]?date)?|date[_.-]?of[_.-]?birth|dob|дата[_. -]?рождения|рождение",
            _DATE,
            "record_birth_date_v3_32",
        ),
        FieldRule(
            "PASSPORT_RF",
            r"passport(?:[_.-]?(?:rf|number|no))?|паспорт(?:[_. -]?(?:рф|номер))?",
            r"\d{2}[\s-]?\d{2}[\s-]\d{6}",
            "record_passport_v3_32",
        ),
        FieldRule(
            "DRIVER_LICENSE_RF",
            r"dl|license[_.-]?rf|driver[_.-]?licen[cs]e(?:[_.-]?(?:rf|number))?|"
            r"водительское[_. -]?удостоверение|ву",
            r"\d{2}[\s-]?\d{2}[\s-]\d{6}",
            "record_license_v3_32",
        ),
        FieldRule(
            "PHONE_RF",
            r"phone|mobile|contact[_.-]?phone|телефон|тел|мобильный",
            _PHONE,
            "record_phone_v3_32",
        ),
        FieldRule(
            "EMAIL",
            r"e[_.-]?mail|email|contact[_.-]?email|электронная[_. -]?почта|почта",
            _EMAIL,
            "record_email_v3_32",
        ),
        FieldRule(
            "ADDRESS_COUNTRY",
            r"(?:address[_.-]?)?country|страна",
            rf"РФ|{_CAP}(?:\s+{_CAP})?",
            "record_country_v3_32",
        ),
        FieldRule(
            "ADDRESS_POSTAL_CODE",
            r"zip|(?:address[_.-]?)?postal[_.-]?(?:code|index)|postcode|почтовый[_. -]?индекс|индекс",
            r"\d{6}",
            "record_postcode_v3_32",
        ),
        FieldRule(
            "ADDRESS_CITY",
            r"(?:address[_.-]?)?city|город|г\.?",
            _CITY,
            "record_city_v3_32",
        ),
        FieldRule(
            "ADDRESS_STREET",
            r"(?:address[_.-]?)?street|улица|ул\.?",
            rf"[\u0410-ЯЁа-яё]{{2,}}(?:-[\u0410-ЯЁа-яё]{{2,}})*(?:\s+{_CAP})?",
            "record_street_v3_32",
        ),
        FieldRule(
            "ADDRESS_HOUSE",
            r"(?:address[_.-]?)?house|дом|д\.?",
            r"\d{1,4}[А-ЯЁA-Z]?",
            "record_house_v3_32",
        ),
        FieldRule(
            "ADDRESS_APARTMENT",
            r"apt|(?:address[_.-]?)?(?:apartment|flat)|квартира|кв\.?",
            r"\d{1,5}",
            "record_apartment_v3_32",
        ),
        FieldRule(
            "PLACE_OF_BIRTH",
            r"birth[_.-]?place|place[_.-]?of[_.-]?birth|место[_. -]?рождения",
            _CITY,
            "record_birthplace_v3_32",
        ),
        FieldRule(
            "BANK_CARD",
            r"payment[.]card|bank[_.-]?card|card[_.-]?(?:number|no)|номер[_. -]?карты",
            r"(?:\d[ -]?){15,18}\d",
            "record_bank_card_v3_32",
            410,
        ),
        FieldRule(
            "CARDHOLDER_NAME",
            r"card[.]holder|card[_.-]?holder|holder|держатель",
            _CARDHOLDER,
            "record_cardholder_v3_32",
            410,
        ),
        FieldRule(
            "CVV",
            r"security[.]cvv|cvv2?|cvc2?",
            r"\d{3}",
            "record_cvv_v3_32",
            410,
        ),
        FieldRule(
            "PIN",
            r"security[.]pin|pin|пин",
            r"\d{4}",
            "record_pin_v3_32",
            410,
        ),
    )
)

_CITY_NATURAL = re.compile(
    rf"\bгород\s*[:=—-]?\s*(?P<value>{_CITY})(?=\s*[,.;!?]|$)",
    _FLAGS,
)
_CARDHOLDER_NATURAL = re.compile(
    rf"\b(?:карта|карты)\s+(?P<card>(?:\d[ -]?){{15}}\d)\s+на\s+имя\s+"
    rf"(?P<value>{_CARDHOLDER})(?=\s+(?:указан\w*|CVV|CVC|пин\b)|\s*[,.;]|$)",
    _FLAGS,
)
_ISSUER_LINE = re.compile(
    r"(?im)^\s*(?:выдан(?:\u043e|ный)?|issued[_. -]?by)\s*[:=—-]?\s*"
    r"(?P<value>(?:(?:ОВМ\s+|(?:ОТДЕЛЕНИЕ|ОТДЕЛ|Отделом)\s+)?"
    r"(?:ГУ\s+)?(?:УФМС|УМВД|ОМВД|МВД)\b)[^\r\n]*)\s*$"
)
_ISSUE_DATE_LINE = re.compile(
    rf"(?im)^\s*(?:дата\s+)?(?:выдачи|выдан)\s*[:=—-]?\s*"
    rf"(?P<value>{_DATE})(?=\s*$)"
)
_PHONE_NATURAL = re.compile(
    rf"\b(?:телефон|мобильный)\s*[:=—-]?\s*"
    rf"(?P<value>{_PHONE})(?=\s*[,.;!?]|$)",
    _FLAGS,
)
_PERSON_NATURAL = re.compile(
    rf"\b(?:заявка\s*:\s*|клиент\s+|связь\s+с\s+)(?P<value>{_PERSON})(?=\s*[: ,;.!?]|$)",
    _FLAGS,
)
_BIRTHPLACE_NATURAL = re.compile(
    rf"\bродил(?:ся|ась)\s+{_DATE}\s+в\s+(?P<value>{_CITY})"
    rf"(?=\s*[,;.!?]|$)",
    _FLAGS,
)
_PASSPORT_NATURAL = re.compile(
    r"\b(?:паспорт|документ)\s*[:=№—-]?\s*"
    r"(?P<value>\d{2}[\s-]\d{2}[\s-]\d{6})(?=\s*[,;.!?]|$)",
    _FLAGS,
)
_PASSPORT_INLINE = re.compile(
    rf"\b(?:паспорт|документ)\b[^;\n]{{0,30}}?"
    rf"(?P<passport>\d{{2}}[\s-]\d{{2}}[\s-]\d{{6}})\s*,?\s*"
    rf"выдан\s+(?P<issuer>[^;\n]{{3,100}}?)\s+(?P<date>{_DATE})\s*,?\s*"
    rf"код(?:\s+подразделения)?\s+(?P<division>\d{{3}}[\s/-]\d{{3}})",
    _FLAGS,
)
_ADDRESS_NATURAL = re.compile(
    rf"\bдоставка\s*:\s*страна\s+(?P<country>{_CAP}(?:\s+{_CAP})?)\s*,\s*"
    rf"индекс\s+(?P<postal>\d{{6}})\s*,\s*город\s+(?P<city>{_CITY})\s*,\s*"
    rf"улица\s+(?P<street>[А-ЯЁа-яё-]+)\s*,\s*дом\s+(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*"
    rf"квартира\s+(?P<apartment>\d{{1,5}})",
    _FLAGS,
)
_PAYMENT_NATURAL = re.compile(
    rf"\b(?:оплата\s*:\s*)?карта\s+(?P<card>(?:\d[ -]?){{15,18}}\d)\s*;\s*"
    rf"держатель\s+(?P<holder>{_CARDHOLDER})(?=\s*;)",
    _FLAGS,
)
_AGENCY = re.compile(r"\b(?:МВД|УМВД|ОМВД|УФМС|ОВМ)\b", re.IGNORECASE)


def _valid_date(value: str) -> bool:
    day, month, year = (int(part) for part in re.split(r"[-./]", value))
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 390,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, priority)


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 16 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _record_candidates(text: str) -> Iterator[DetectedEntity]:
    for rule, pattern in _RULES:
        for match in pattern.finditer(text):
            value = match.group("value")
            if rule.entity_type == "BIRTH_DATE" and not _valid_date(value):
                continue
            if rule.entity_type == "BANK_CARD" and not _valid_luhn(value):
                continue
            yield _entity(text, rule.entity_type, match.span("value"), rule.source, rule.priority)

    for match in _CITY_NATURAL.finditer(text):
        yield _entity(text, "ADDRESS_CITY", match.span("value"), "natural_city_v3_32")
    for match in _CARDHOLDER_NATURAL.finditer(text):
        if _valid_luhn(match.group("card")):
            yield _entity(
                text,
                "CARDHOLDER_NAME",
                match.span("value"),
                "natural_cardholder_v3_32",
            )
    for match in _ISSUER_LINE.finditer(text):
        yield _entity(
            text,
            "PASSPORT_ISSUER",
            match.span("value"),
            "issuer_line_v3_32",
            430,
        )
    for match in _ISSUE_DATE_LINE.finditer(text):
        value = match.group("value")
        if _valid_date(value):
            yield _entity(
                text,
                "PASSPORT_ISSUE_DATE",
                match.span("value"),
                "issue_date_line_v3_32",
            )
    for match in _PHONE_NATURAL.finditer(text):
        yield _entity(text, "PHONE_RF", match.span("value"), "natural_phone_v3_32")
    for match in _PERSON_NATURAL.finditer(text):
        yield _entity(text, "PERSON", match.span("value"), "natural_person_v3_32")
    for match in _BIRTHPLACE_NATURAL.finditer(text):
        yield _entity(
            text,
            "PLACE_OF_BIRTH",
            match.span("value"),
            "natural_birthplace_v3_32",
        )
    for match in _PASSPORT_NATURAL.finditer(text):
        yield _entity(text, "PASSPORT_RF", match.span("value"), "natural_passport_v3_32")
    for match in _PASSPORT_INLINE.finditer(text):
        if not _AGENCY.search(match.group("issuer")) or not _valid_date(match.group("date")):
            continue
        yield _entity(text, "PASSPORT_RF", match.span("passport"), "passport_record_v3_32", 430)
        yield _entity(
            text,
            "PASSPORT_ISSUER",
            match.span("issuer"),
            "passport_record_v3_32",
            430,
        )
        yield _entity(
            text,
            "PASSPORT_ISSUE_DATE",
            match.span("date"),
            "passport_record_v3_32",
            430,
        )
        yield _entity(
            text,
            "DIVISION_CODE",
            match.span("division"),
            "passport_record_v3_32",
            430,
        )
    address_fields = {
        "country": "ADDRESS_COUNTRY",
        "postal": "ADDRESS_POSTAL_CODE",
        "city": "ADDRESS_CITY",
        "street": "ADDRESS_STREET",
        "house": "ADDRESS_HOUSE",
        "apartment": "ADDRESS_APARTMENT",
    }
    for match in _ADDRESS_NATURAL.finditer(text):
        for group, entity_type in address_fields.items():
            yield _entity(text, entity_type, match.span(group), "address_record_v3_32", 420)
    for match in _PAYMENT_NATURAL.finditer(text):
        if _valid_luhn(match.group("card")):
            yield _entity(text, "BANK_CARD", match.span("card"), "payment_record_v3_32", 420)
            yield _entity(
                text,
                "CARDHOLDER_NAME",
                match.span("holder"),
                "payment_record_v3_32",
                420,
            )


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with v3.26 plus strict field-aware record parsing."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    base = detect_v3_26(text)
    if len(text) >= 100_000:
        return base
    strict_base = [
        entity
        for entity in base
        if entity.entity_type != "ADDRESS_CITY" or re.fullmatch(_CITY, entity.text) is not None
    ]
    return _merge([*strict_base, *_record_candidates(text)])
