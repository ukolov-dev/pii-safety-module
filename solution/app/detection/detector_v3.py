"""Production detector v3 base: conservative, format-tolerant recognizers for Russian PII.

The rules are based on field
semantics (labels, checksums, date validation, and personal/organisation context),
not on individual benchmark sentences.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_SEP = r"\s*(?:[:=№]|[-–—])?\s*"
_PERSON_QUALIFIER = (
    r"(?:\s+(?:клиента|заявителя|получателя|владельца|"
    r"физического\s+лица|физлица))?"
)
_VALUE_END = r"(?=\s*(?:[,;]|\.(?:\s|$)|\n|$))"

_EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+(?![\w-])",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+\s*7|8)(?:[\s().-]*\d){10}(?!\d)")
_INN_RE = re.compile(r"(?<!\d)(?:\d{12}|\d{10})(?!\d)")
_CARD_RE = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")
_PASSPORT_COMPACT_RE = re.compile(
    r"(?<!\d)\d{2}[ -]?\d{2}[ -]+(?:№\s*)?\d{6}(?!\d)", re.IGNORECASE
)
_PASSPORT_LABELLED_RE = re.compile(
    rf"\b(?P<value>сери(?:я|и){_SEP}\d{{2}}[ -]?\d{{2}}"
    rf"\s*[,;/]?\s*(?:номер(?:ом)?|№){_SEP}\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(r"(?<!\d)\d{3}[ -]\d{3}(?!\d)")

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
_DAY_FIRST_DATE_RE = re.compile(
    r"(?<!\d)(?P<day>0?[1-9]|[12]\d|3[01])[./-]"
    r"(?P<month>0?[1-9]|1[0-2])[./-](?P<year>(?:19|20)\d{2})(?!\d)"
)
_YEAR_FIRST_DATE_RE = re.compile(
    r"(?<!\d)(?P<year>(?:19|20)\d{2})[./-]"
    r"(?P<month>0?[1-9]|1[0-2])[./-](?P<day>0?[1-9]|[12]\d|3[01])(?!\d)"
)
_TEXT_DATE_RE = re.compile(
    rf"(?<!\d)(?P<day>[1-9]|[12]\d|3[01])\s+"
    rf"(?P<month>{'|'.join(_MONTHS)})\s+(?P<year>(?:19|20)\d{{2}})"
    rf"(?:\s*г(?:ода|од|оду|\.)?)?",
    re.IGNORECASE,
)

_SECURITY_CODE_RE = re.compile(
    rf"\b(?P<label>cvv2?|cvc2?|пин(?:-код)?|pin(?:-code)?){_SEP}"
    r"(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)

_RU_TITLE_WORD = r"[A-ЯЁ][a-яё]+(?:-[A-ЯЁ][a-яё]+)?"
_RU_UPPER_WORD = r"[A-ЯЁ]{2,}(?:-[A-ЯЁ]{2,})?"
_RU_NAME_WORD = rf"(?:{_RU_TITLE_WORD}|{_RU_UPPER_WORD})"
_RU_ANY_CASE_WORD = r"[A-Яa-яЁё]{2,}(?:-[A-Яa-яЁё]{2,})?"
_EXPLICIT_FIO_RE = re.compile(
    rf"\b(?i:ф\.?\s*и\.?\s*о\.?(?:{_PERSON_QUALIFIER})?){_SEP}"
    rf"(?P<value>{_RU_ANY_CASE_WORD}(?:\s+{_RU_ANY_CASE_WORD}){{1,2}})\b"
)
_PERSON_LABEL_RE = re.compile(
    rf"\b(?i:клиент|"
    rf"заявитель|получатель|владелец|гражданин){_SEP}"
    rf"(?P<value>{_RU_NAME_WORD}(?:\s+{_RU_NAME_WORD}){{1,2}})\b",
)
_PATRONYMIC_PERSON_RE = re.compile(
    rf"(?<![A-Яa-яЁё-])(?P<value>{_RU_TITLE_WORD}\s+{_RU_TITLE_WORD}\s+"
    rf"[A-ЯЁ][a-яё]+(?:ович|евич|ич|овна|евна|ична|инична))\b"
)

_PASSPORT_CONTEXT = re.compile(r"\b(?:паспорт\w*|сери(?:я|и))\b", re.IGNORECASE)
_DIVISION_CONTEXT = re.compile(r"\bкод\s+подразделения\b", re.IGNORECASE)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата\s+рождения(?:\s+в\s+формате\s+[a-яё-]+)?|"
    r"родил(?:ся|ась)|год\s+рождения|д\.?\s*р\.?)\b",
    re.IGNORECASE,
)
_ISSUE_DATE_CONTEXT = re.compile(
    r"\b(?:дата\s+выдачи(?:\s+паспорта)?|паспорт\s+выдан)\b", re.IGNORECASE
)
_PUBLIC_CONTACT_CONTEXT = re.compile(
    r"\b(?:горячая\s+линия|контактный\s+центр|колл-центр|"
    r"служба\s+поддержки|общ(?:ий|ая)\s+(?:адрес|почта)|"
    r"телефон\s+(?:банка|офиса|организации))\b",
    re.IGNORECASE,
)
_ORGANISATION_CONTEXT = re.compile(
    r"\b(?:офис|отделение|филиал|банк|магазин|компания|"
    r"организация|юридический\s+адрес|ооо|пао|ао)\b",
    re.IGNORECASE,
)
_PERSONAL_ADDRESS_ANCHOR = re.compile(
    r"\b(?:адрес(?:\s+(?:проживания|регистрации|клиента|заявителя|"
    r"получателя))?|место\s+жительства|место\s+регистрации)\b",
    re.IGNORECASE,
)

_PLACE_OF_BIRTH_RE = re.compile(
    rf"\bместо\s+рождения{_PERSON_QUALIFIER}{_SEP}"
    rf"(?P<value>(?:(?:г(?:ород|\.)|с(?:ело|\.)|деревня|п(?:ос(?:елок)?|\.))\s*)?"
    rf"[A-ЯЁ][A-Яa-яЁё-]*(?:\s+[A-ЯЁ][A-Яa-яЁё-]*){{0,4}}){_VALUE_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\bгражданств(?:о|а){_PERSON_QUALIFIER}{_SEP}"
    rf"(?P<value>РФ|Россия|Российская\s+Федерация|"
    rf"[A-ЯЁ][a-яё]+(?:\s+[A-ЯЁ][a-яё]+){{0,2}}){_VALUE_END}",
    re.IGNORECASE,
)
_PASSPORT_ISSUER_RE = re.compile(
    rf"\b(?:паспорт\s+)?(?:выдан|орган\s+выдачи){_SEP}"
    r"(?P<value>(?:(?:ГУ\s+)?МВД|ОМВД|ОУФМС|УФМС|ФМС|ОТДЕЛОМ)\b[^,;\n]*?)"
    r"(?=\s*(?:[,;]|\.(?:\s*$|\s*\n)|$))",
    re.IGNORECASE,
)
_DRIVER_LICENSE_RE = re.compile(
    rf"\b(?:водительск(?:ое|ого)\s+удостоверени(?:е|я)|"
    rf"вод\.?\s*уд\.?)\s*{_SEP}(?P<value>\d{{2}}[ -]?\d{{2}}[ -]?\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:(?:имя|фамилия\s+и\s+имя)\s+)?держател(?:я|ь)\s+карты{_SEP}"
    rf"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){{1,3}}){_VALUE_END}|"
    rf"\bCARDHOLDER\s+NAME{_SEP}(?P<latin>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){{1,3}}){_VALUE_END}",
    re.IGNORECASE,
)

_ADDRESS_COMPONENTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ADDRESS_COUNTRY",
        re.compile(
            rf"\b(?:страна|государство)(?:\s+(?:проживания|регистрации))?{_SEP}"
            r"(?P<value>РФ|Россия|Российская\s+Федерация)(?=\s*[,;.]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "ADDRESS_POSTAL_CODE",
        re.compile(
            rf"\b(?:почтовый\s+)?индекс{_PERSON_QUALIFIER}{_SEP}"
            r"(?P<value>\d{6})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        "ADDRESS_CITY",
        re.compile(
            rf"\b(?:город|г\.)(?:\s+(?:проживания|регистрации))?{_SEP}"
            rf"(?P<value>[A-ЯЁ][A-Яa-яЁё-]*(?:\s+[A-ЯЁ][A-Яa-яЁё-]*){{0,2}}){_VALUE_END}",
            re.IGNORECASE,
        ),
    ),
    (
        "ADDRESS_STREET",
        re.compile(
            rf"\b(?:улица|ул\.)(?:\s+(?:проживания|регистрации))?{_SEP}"
            rf"(?P<value>[A-ЯЁ][A-Яa-яЁё-]*(?:\s+[A-ЯЁ][A-Яa-яЁё-]*){{0,3}}){_VALUE_END}",
            re.IGNORECASE,
        ),
    ),
    (
        "ADDRESS_HOUSE",
        re.compile(
            rf"\b(?:дом|д\.){_PERSON_QUALIFIER}{_SEP}"
            r"(?P<value>\d+[A-ZА-ЯЁa-zа-яё]?"
            r"(?:[/ -](?:к(?:орпус)?\.?\s*)?\d+[A-ZА-ЯЁa-zа-яё]?)?)"
            r"(?=\s*[,;.]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "ADDRESS_APARTMENT",
        re.compile(
            rf"\b(?:квартира|кв\.){_PERSON_QUALIFIER}{_SEP}"
            r"(?P<value>\d+[A-ZА-ЯЁa-zа-яё]?)(?=\s*[,;.]|$)",
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


def _near(
    text: str, start: int, end: int, pattern: re.Pattern[str], radius: int = 72
) -> bool:
    return pattern.search(text[max(0, start - radius) : min(len(text), end + radius)]) is not None


def _after_label(text: str, start: int, pattern: re.Pattern[str], radius: int = 72) -> bool:
    prefix = text[max(0, start - radius) : start]
    return any(
        re.fullmatch(r"[\s:,№=–—-]*", prefix[match.end() :]) is not None
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
        check_11 = sum(a * b for a, b in zip(digits[:10], weights_11, strict=True)) % 11 % 10
        check_12 = sum(a * b for a, b in zip(digits[:11], weights_12, strict=True)) % 11 % 10
        return (check_11, check_12) == (digits[10], digits[11])
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


def _valid_date(match: re.Match[str]) -> bool:
    try:
        month_value = match.group("month")
        month = _MONTHS.get(month_value.lower(), int(month_value) if month_value.isdigit() else 0)
        datetime(int(match.group("year")), month, int(match.group("day")))
    except (TypeError, ValueError):
        return False
    return True


def _personal_address_context(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 120) : min(len(text), end + 40)]
    if _ORGANISATION_CONTEXT.search(window):
        return False
    # Explicit personal-address anchors cover chains.  Component-specific labels such
    # as "город проживания" and "индекс клиента" are independently personal.
    return bool(
        _PERSONAL_ADDRESS_ANCHOR.search(window)
        or re.search(
            r"\b(?:проживания|регистрации|клиента|заявителя|получателя)\b",
            window,
            re.IGNORECASE,
        )
    )


def _candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _EMAIL_RE.finditer(text):
        if not _near(text, *match.span(), _PUBLIC_CONTACT_CONTEXT, radius=88):
            yield _entity(text, "EMAIL", *match.span(), 0.99, "email_v3", 80)

    for match in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        public = digits.startswith("8800") or _near(
            text, *match.span(), _PUBLIC_CONTACT_CONTEXT, radius=88
        )
        if len(digits) == 11 and digits[0] in "78" and not public:
            yield _entity(text, "PHONE_RF", *match.span(), 0.97, "phone_rf_v3", 80)

    for match in _INN_RE.finditer(text):
        if _valid_inn(match.group()):
            yield _entity(text, "INN", *match.span(), 1.0, "inn_checksum", 100)

    for match in _CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if _valid_luhn(digits):
            yield _entity(text, "BANK_CARD", *match.span(), 1.0, "luhn_checksum", 100)

    for match in _PASSPORT_COMPACT_RE.finditer(text):
        if _near(text, *match.span(), _PASSPORT_CONTEXT):
            yield _entity(text, "PASSPORT_RF", *match.span(), 0.98, "passport_context_v3", 96)
    for match in _PASSPORT_LABELLED_RE.finditer(text):
        start, end = match.span("value")
        yield _entity(text, "PASSPORT_RF", start, end, 0.99, "passport_label_v3", 97)

    for match in _DIVISION_RE.finditer(text):
        if _near(text, *match.span(), _DIVISION_CONTEXT, radius=48):
            yield _entity(text, "DIVISION_CODE", *match.span(), 0.99, "division_label_v3", 96)

    for pattern in (_DAY_FIRST_DATE_RE, _YEAR_FIRST_DATE_RE, _TEXT_DATE_RE):
        for match in pattern.finditer(text):
            if not _valid_date(match):
                continue
            if _after_label(text, match.start(), _BIRTH_CONTEXT):
                yield _entity(text, "BIRTH_DATE", *match.span(), 0.98, "birth_date_v3", 96)
            elif _after_label(text, match.start(), _ISSUE_DATE_CONTEXT):
                yield _entity(
                    text,
                    "PASSPORT_ISSUE_DATE",
                    *match.span(),
                    0.98,
                    "passport_issue_date_v3",
                    96,
                )

    for match in _SECURITY_CODE_RE.finditer(text):
        value = match.group("value")
        is_pin = match.group("label").lower().startswith(("пин", "pin"))
        if (is_pin and len(value) == 4) or (not is_pin and len(value) in (3, 4)):
            start, end = match.span("value")
            yield _entity(
                text,
                "PIN" if is_pin else "CVV",
                start,
                end,
                0.99,
                "bank_security_label_v3",
                96,
            )

    for pattern in (_EXPLICIT_FIO_RE, _PERSON_LABEL_RE):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            if match.group("value").split(maxsplit=1)[0].upper() not in {
                "ООО",
                "АО",
                "ПАО",
                "ИП",
            }:
                yield _entity(text, "PERSON", start, end, 0.88, "person_label_v3", 72)
    for match in _PATRONYMIC_PERSON_RE.finditer(text):
        start, end = match.span("value")
        if not _near(text, start, end, _ORGANISATION_CONTEXT, radius=48):
            yield _entity(text, "PERSON", start, end, 0.82, "person_patronymic_v3", 66)

    labelled: tuple[tuple[str, re.Pattern[str], str, int], ...] = (
        ("PLACE_OF_BIRTH", _PLACE_OF_BIRTH_RE, "value", 92),
        ("CITIZENSHIP", _CITIZENSHIP_RE, "value", 92),
        ("PASSPORT_ISSUER", _PASSPORT_ISSUER_RE, "value", 94),
        ("DRIVER_LICENSE_RF", _DRIVER_LICENSE_RE, "value", 98),
    )
    for entity_type, pattern, group, priority in labelled:
        for match in pattern.finditer(text):
            start, end = match.span(group)
            yield _entity(text, entity_type, start, end, 0.97, "labelled_field_v3", priority)

    for match in _CARDHOLDER_RE.finditer(text):
        group = "value" if match.group("value") is not None else "latin"
        start, end = match.span(group)
        yield _entity(text, "CARDHOLDER_NAME", start, end, 0.98, "cardholder_label_v3", 94)

    for entity_type, pattern in _ADDRESS_COMPONENTS:
        for match in pattern.finditer(text):
            start, end = match.span("value")
            if _personal_address_context(text, start, end):
                yield _entity(text, entity_type, start, end, 0.96, "personal_address_v3", 91)


def _merge_overlaps(candidates: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(
        candidates,
        entity_type_tiebreak=True,
    )


def detect(text: str) -> list[DetectedEntity]:
    """Detect supported PII without changing the production detector."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return _merge_overlaps(_candidates(text))
