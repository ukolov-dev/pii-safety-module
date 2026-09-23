"""Offline, deterministic recognizers for common Russian PII."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from .models import DetectedEntity

_EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+(?![\w-])"
)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+7|8)(?:[\s()\-]*\d){10}(?!\d)")
_INN_RE = re.compile(r"(?<!\d)(?:\d{12}|\d{10})(?!\d)")
_CARD_RE = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")
_PASSPORT_RE = re.compile(
    r"(?<!\d)(?:\d{2}[ -]?\d{2})[ -]+(?:№\s*)?\d{6}(?!\d)", re.IGNORECASE
)
_PASSPORT_LABELLED_RE = re.compile(
    r"\bсери(?:я|и)\s*[:№-]?\s*\d{2}[ -]?\d{2}"
    r"(?:\s*[,;]?\s*(?:номер|номером|№)\s*[:№-]?\s*)\d{6}(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(r"(?<!\d)\d{3}[ -]\d{3}(?!\d)")
_NUMERIC_DATE_RE = re.compile(
    r"(?<!\d)(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:19|20)\d{2}(?!\d)"
)
_YEAR_FIRST_DATE_RE = re.compile(
    r"(?<!\d)(?P<iso_year>(?:19|20)\d{2})[./-]"
    r"(?P<iso_month>0?[1-9]|1[0-2])[./-]"
    r"(?P<iso_day>0?[1-9]|[12]\d|3[01])(?!\d)"
)
_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}
_TEXT_DATE_RE = re.compile(
    rf"(?<!\d)(?P<day>[1-9]|[12]\d|3[01])\s+"
    rf"(?P<month>{'|'.join(_MONTHS)})\s+(?P<year>(?:19|20)\d{{2}})(?:\s*г(?:ода|\.)?)?",
    re.IGNORECASE,
)
_SECURITY_CODE_RE = re.compile(
    r"\b(?P<label>cvv2?|cvc2?|пин(?:-код)?|pin)\s*[:№=-]?\s*(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_RU_WORD = r"[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?"
_RU_UPPER_WORD = r"[А-ЯЁ]{2,}(?:-[А-ЯЁ]{2,})?"
_RU_NAME_WORD = rf"(?:{_RU_WORD}|{_RU_UPPER_WORD})"
_CONTEXT_FIO_RE = re.compile(
    rf"\b(?i:фио(?:\s+(?:заявителя|клиента|получателя))?|"
    rf"клиент|гражданин|владелец|получатель|заявитель)\s*[:—-]?\s*"
    rf"(?P<name>{_RU_NAME_WORD}(?:\s+{_RU_NAME_WORD}){{1,2}})\b",
)
_PATRONYMIC_FIO_RE = re.compile(
    rf"(?<![А-Яа-яЁё-])(?P<name>{_RU_WORD}\s+{_RU_WORD}\s+"
    rf"[А-ЯЁ][а-яё]+(?:ович|евич|ич|овна|евна|ична|инична))\b"
)

_PASSPORT_CONTEXT = re.compile(
    r"\b(?:паспорт|паспорта|серия|серии)\b", re.IGNORECASE
)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата\s+рождения(?:\s+в\s+формате\s+[а-яё-]+)?|родил(?:ся|ась)|"
    r"год\s+рождения|д\.?\s*р\.?)\b",
    re.IGNORECASE,
)
_DIVISION_CONTEXT = re.compile(r"\bкод\s+подразделения\b", re.IGNORECASE)
_PASSPORT_ISSUE_CONTEXT = re.compile(r"\bдата\s+выдачи\s+паспорта\b", re.IGNORECASE)
_PUBLIC_EMAIL_CONTEXT = re.compile(
    r"\b(?:общ(?:ий|ая)\s+(?:адрес|почта)|служб[аы]\s+поддержки)\b", re.IGNORECASE
)
_PERSONAL_ADDRESS_CONTEXT = re.compile(
    r"\bадрес\s+(?:клиента|заявителя|получателя)\b", re.IGNORECASE
)

_LABELLED_PATTERNS: tuple[tuple[str, re.Pattern[str], float, int], ...] = (
    (
        "PLACE_OF_BIRTH",
        re.compile(
            r"\bместо\s+рождения(?:\s+(?:клиента|заявителя))?\s*[:—-]?\s*"
            r"(?P<value>(?:(?:г(?:ород|\.)|село|деревня|пос[её]лок)\s+)?"
            r"[А-ЯЁ][А-Яа-яЁё-]*(?:\s+[А-ЯЁ][А-Яа-яЁё-]*){0,3})(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.96,
        90,
    ),
    (
        "CITIZENSHIP",
        re.compile(
            r"\bгражданств(?:о|а)\s*[:—-]?\s*"
            r"(?P<value>Российская\s+Федерация|Россия|РФ)(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.98,
        92,
    ),
    (
        "PASSPORT_ISSUER",
        re.compile(
            r"\bпаспорт\s+выдан\s+"
            r"(?P<value>(?:(?:ГУ\s+)?МВД|[ОУ]?МВД|У?ФМС|ОТДЕЛОМ)\b[^,;\n]*?)"
            r"(?=\.\s*$|[,;]|$)",
            re.IGNORECASE,
        ),
        0.97,
        92,
    ),
    (
        "DRIVER_LICENSE_RF",
        re.compile(
            r"\b(?:водительское\s+удостоверение|вод\.?\s*уд\.?)\s*[:№—-]?\s*"
            r"(?P<value>\d{2}[ -]?\d{2}[ -]?\d{6})(?!\d)",
            re.IGNORECASE,
        ),
        0.99,
        98,
    ),
    (
        "ADDRESS_COUNTRY",
        re.compile(
            r"\bстрана\s+(?:проживания|регистрации)(?:\s+(?:клиента|заявителя))?\s*[:—-]?\s*"
            r"(?P<value>Россия|РФ|Российская\s+Федерация)(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.98,
        90,
    ),
    (
        "ADDRESS_POSTAL_CODE",
        re.compile(
            r"\b(?:почтовый\s+)?индекс(?:\s+(?:клиента|заявителя))?\s*[:—-]?\s*"
            r"(?P<value>\d{6})(?!\d)",
            re.IGNORECASE,
        ),
        0.99,
        95,
    ),
    (
        "ADDRESS_CITY",
        re.compile(
            r"\bгород\s+(?:проживания|регистрации)(?:\s+(?:клиента|заявителя))?\s*[:—-]?\s*"
            r"(?P<value>[А-ЯЁ][А-Яа-яЁё-]*(?:\s+[А-ЯЁ][А-Яа-яЁё-]*){0,2})(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.97,
        90,
    ),
    (
        "ADDRESS_STREET",
        re.compile(
            r"\bулица\s+(?:проживания|регистрации)(?:\s+(?:клиента|заявителя))?\s*[:—-]?\s*"
            r"(?P<value>[А-ЯЁ][А-Яа-яЁё-]*(?:\s+[А-ЯЁ][А-Яа-яЁё-]*){0,2})(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.97,
        90,
    ),
    (
        "ADDRESS_HOUSE",
        re.compile(
            r"\bдом\s+(?:клиента|заявителя|проживания|регистрации)\s*[:—-]?\s*"
            r"(?P<value>\d+[А-ЯA-Zа-яa-z]?(?:[/-]\d+[А-ЯA-Zа-яa-z]?)?)(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.97,
        90,
    ),
    (
        "ADDRESS_APARTMENT",
        re.compile(
            r"\bквартира\s+(?:клиента|заявителя|проживания|регистрации)\s*[:—-]?\s*"
            r"(?P<value>\d+[А-ЯA-Zа-яa-z]?)(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.97,
        90,
    ),
    (
        "CARDHOLDER_NAME",
        re.compile(
            r"\b(?:(?:имя\s+)?держател[яь]\s+карты|CARDHOLDER\s+NAME)\s*[:—-]?\s*"
            r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=[.,;]|$)",
            re.IGNORECASE,
        ),
        0.98,
        92,
    ),
)

_COMBINED_ADDRESS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ADDRESS_COUNTRY", re.compile(r"\bстрана\s+(?P<value>Россия|РФ)(?=[,;])", re.IGNORECASE)),
    ("ADDRESS_POSTAL_CODE", re.compile(r"\bиндекс\s+(?P<value>\d{6})(?!\d)", re.IGNORECASE)),
    ("ADDRESS_CITY", re.compile(r"\bгород\s+(?P<value>[А-ЯЁ][А-Яа-яЁё-]*)(?=[,;])", re.IGNORECASE)),
    (
        "ADDRESS_STREET",
        re.compile(r"\bулица\s+(?P<value>[А-ЯЁ][А-Яа-яЁё-]*)(?=[,;])", re.IGNORECASE),
    ),
    ("ADDRESS_HOUSE", re.compile(r"\bдом\s+(?P<value>\d+[А-ЯA-Zа-яa-z]?)(?=[,;])", re.IGNORECASE)),
    (
        "ADDRESS_APARTMENT",
        re.compile(
            r"\bквартира\s+(?P<value>\d+[А-ЯA-Zа-яa-z]?)(?=[.,;]|$)",
            re.IGNORECASE,
        ),
    ),
)


def _entity(
    text: str,
    entity_type: str,
    start: int,
    end: int,
    confidence: float,
    source: str,
    priority: int,
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], confidence, source, priority)


def _near_context(
    text: str, start: int, end: int, pattern: re.Pattern[str], radius: int = 64
) -> bool:
    return pattern.search(text[max(0, start - radius) : min(len(text), end + radius)]) is not None


def _immediately_after_context(
    text: str, start: int, pattern: re.Pattern[str], radius: int = 56
) -> bool:
    """Require context before a value, without leaking it into later values."""

    prefix = text[max(0, start - radius) : start]
    return any(
        re.fullmatch(r"[\s:,—-]*", prefix[match.end() :]) is not None
        for match in pattern.finditer(prefix)
    )


def _valid_inn(value: str) -> bool:
    digits = [int(char) for char in value]
    if len(set(digits)) == 1:
        return False
    if len(digits) == 10:
        weights = (2, 4, 10, 3, 5, 9, 4, 6, 8)
        return sum(a * b for a, b in zip(digits[:9], weights, strict=True)) % 11 % 10 == digits[9]
    if len(digits) == 12:
        weights_11 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        weights_12 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        digit_11 = sum(a * b for a, b in zip(digits[:10], weights_11, strict=True)) % 11 % 10
        digit_12 = sum(a * b for a, b in zip(digits[:11], weights_12, strict=True)) % 11 % 10
        return (digit_11, digit_12) == (digits[10], digits[11])
    return False


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in value]
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
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


def _valid_date_match(match: re.Match[str]) -> bool:
    try:
        if match.groupdict().get("iso_year"):
            datetime(
                int(match.group("iso_year")),
                int(match.group("iso_month")),
                int(match.group("iso_day")),
            )
        elif "month" in match.groupdict():
            datetime(
                int(match.group("year")),
                _MONTHS[match.group("month").lower()],
                int(match.group("day")),
            )
        else:
            day, month, year = (int(part) for part in re.split(r"[./-]", match.group()))
            datetime(year, month, day)
    except ValueError:
        return False
    return True


def _candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _EMAIL_RE.finditer(text):
        if not _near_context(text, *match.span(), _PUBLIC_EMAIL_CONTEXT, radius=72):
            yield _entity(text, "EMAIL", *match.span(), 0.99, "email_regex", 80)

    for match in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if len(digits) == 11 and digits[0] in "78" and not digits.startswith("8800"):
            yield _entity(text, "PHONE_RF", *match.span(), 0.96, "phone_rf_regex", 80)

    for match in _INN_RE.finditer(text):
        if _valid_inn(match.group()):
            yield _entity(text, "INN", *match.span(), 1.0, "inn_checksum", 100)

    for match in _CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if _valid_luhn(digits):
            yield _entity(text, "BANK_CARD", *match.span(), 1.0, "luhn_checksum", 100)

    for match in _PASSPORT_RE.finditer(text):
        if _near_context(text, *match.span(), _PASSPORT_CONTEXT):
            yield _entity(text, "PASSPORT_RF", *match.span(), 0.97, "passport_context", 95)
    for match in _PASSPORT_LABELLED_RE.finditer(text):
        yield _entity(text, "PASSPORT_RF", *match.span(), 0.99, "passport_context", 95)

    for match in _DIVISION_RE.finditer(text):
        if _near_context(text, *match.span(), _DIVISION_CONTEXT, radius=40):
            yield _entity(text, "DIVISION_CODE", *match.span(), 0.98, "division_code_context", 95)

    for pattern in (_NUMERIC_DATE_RE, _YEAR_FIRST_DATE_RE, _TEXT_DATE_RE):
        for match in pattern.finditer(text):
            if not _valid_date_match(match):
                continue
            if _immediately_after_context(text, match.start(), _BIRTH_CONTEXT):
                yield _entity(text, "BIRTH_DATE", *match.span(), 0.96, "birth_date_context", 95)
            elif _immediately_after_context(text, match.start(), _PASSPORT_ISSUE_CONTEXT):
                yield _entity(
                    text,
                    "PASSPORT_ISSUE_DATE",
                    *match.span(),
                    0.98,
                    "passport_issue_date_context",
                    96,
                )

    for match in _SECURITY_CODE_RE.finditer(text):
        label = match.group("label").lower()
        value = match.group("value")
        is_pin = label.startswith(("пин", "pin"))
        if (is_pin and len(value) == 4) or (not is_pin and len(value) in (3, 4)):
            entity_type = "PIN" if is_pin else "CVV"
            start, end = match.span("value")
            yield _entity(text, entity_type, start, end, 0.99, "bank_security_context", 95)

    for match in _CONTEXT_FIO_RE.finditer(text):
        start, end = match.span("name")
        if match.group("name").split(maxsplit=1)[0] not in {"ООО", "АО", "ПАО", "ИП"}:
            yield _entity(text, "PERSON", start, end, 0.84, "russian_name_context", 70)
    for match in _PATRONYMIC_FIO_RE.finditer(text):
        start, end = match.span("name")
        yield _entity(text, "PERSON", start, end, 0.80, "russian_patronymic_fallback", 65)

    for entity_type, pattern, confidence, priority in _LABELLED_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span("value")
            yield _entity(text, entity_type, start, end, confidence, "labelled_field", priority)

    if _PERSONAL_ADDRESS_CONTEXT.search(text):
        for entity_type, pattern in _COMBINED_ADDRESS_PATTERNS:
            for match in pattern.finditer(text):
                start, end = match.span("value")
                yield _entity(text, entity_type, start, end, 0.96, "personal_address", 90)


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge_overlaps(candidates: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    """Keep the strongest non-overlapping spans, then restore source order."""

    ranked = sorted(
        candidates,
        key=lambda item: (
            -item.priority,
            -item.confidence,
            -(item.end - item.start),
            item.start,
            item.entity_type,
        ),
    )
    accepted: list[DetectedEntity] = []
    for candidate in ranked:
        if not any(_overlap(candidate, existing) for existing in accepted):
            accepted.append(candidate)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def detect(text: str) -> list[DetectedEntity]:
    """Detect supported PII types without network access or mutable global state."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return _merge_overlaps(_candidates(text))
