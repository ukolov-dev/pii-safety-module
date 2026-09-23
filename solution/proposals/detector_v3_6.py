"""Candidate v3.6: high-context recall extensions over production v3.3.

Rules are based on reusable Russian labels and ownership cues disclosed by the v5
error analysis. Production remains unchanged, and no later sealed set is imported.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.detector_v3_3 import detect as production_detect
from app.detection.models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3}"
_END = r"(?=\s*(?:[,;]|\.(?:\s|$)|$))"

_PERSON = (
    re.compile(
        rf"\b(?:договор\s+заключ[её]н\s+с|обращение\s+подписал[аи]?|"
        rf"заявлени[ея]\s+подписал[аи]?)\s+(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bполучатель(?:\s+(?:посылки|платежа|документов))?\s*[:—-]\s*"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)
_DOT_CARD = re.compile(r"(?<!\d)(?P<value>\d{4}(?:\.\d{4}){3})(?!\d)")
_PERSONAL_PAYMENT = re.compile(
    r"\b(?:PAN\s+карты\s+(?:клиента|владельца)|личн\w*\s+реквизит\w*|"
    r"карта\s+(?:клиента|владельца)|вернуть\s+деньги)\b",
    re.IGNORECASE,
)
_PASSPORT_LABELLED = re.compile(
    r"\b(?P<value>серия\s+паспорта\s+\d{4}\s*[,;]\s*"
    r"(?:его\s+)?номер\s+\d{6})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_COMPACT = re.compile(
    r"\b(?:предъявил[аи]?|предоставил[аи]?|указал[аи]?)\s+паспорт\s*"
    r"(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_DIVISION = re.compile(
    r"\b(?:код\s+(?:органа\s+выдачи|выдавшего\s+органа)|"
    r"код\s+подразделения)\s*[:—-]?\s*(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_IN_PASSPORT = re.compile(r"\bкод\s+(?P<value>\d{3}[- /]\d{3})(?!\d)", re.IGNORECASE)

_MONTHS = (
    "января|февраля|марта|апреля|мая|июня|июля|августа|"
    "сентября|октября|ноября|декабря"
)
_BIRTH_TEXT = re.compile(
    rf"\b(?:пациент|работник|застрахованн\w*|гражданин\w*)\s+"
    rf"(?:появил(?:ся|ась)\s+на\s+свет|родил(?:ся|ась))\s+"
    rf"(?P<value>(?:[1-9]|[12]\d|3[01])\s+(?:{_MONTHS})\s+"
    rf"(?:19|20)\d{{2}}\s*г(?:ода|\.)?)",
    re.IGNORECASE,
)
_NUMERIC_DATE = r"(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[0-2])[-/.](?:19|20)\d{2}"
_ISSUE_DATE = (
    re.compile(
        rf"\bдата\s+(?:оформления|выдачи)\s+(?:паспорта|документа)\s*[:—-]?\s*"
        rf"(?P<value>{_NUMERIC_DATE})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bпаспорт\b[^;\n]*?\bвыдан\b[^;\n]*?\s(?P<value>{_NUMERIC_DATE})(?=[,.;]|$)",
        re.IGNORECASE,
    ),
)
_BIRTHPLACE = (
    re.compile(
        rf"\bнасел[её]нный\s+пункт\s+рождения\s*[:—-]?\s*"
        rf"(?P<value>(?:город|г\.|деревня|село|пос[её]лок)\s+{_WORD}(?:\s+{_WORD}){{0,3}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bродил(?:ся|ась)\s+в\s+"
        rf"(?P<value>(?:городе|г\.|деревне|селе|пос[её]лке)\s+"
        rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bместо\s+рождения\s*[:—-]\s*"
        rf"(?P<value>(?:город|городе|г\.|деревня|деревне|село|пос[её]лок)\s+"
        rf"{_WORD}(?:\s+{_WORD}){{0,2}})(?=\s*,)",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP = re.compile(
    rf"\b(?:имеет\s+)?гражданство\s*[:—-]?\s*"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}){_END}",
    re.IGNORECASE,
)
_ISSUER = (
    re.compile(
        r"\bпаспорт\s+выдал\s+(?P<value>(?:У?ФМС|О?МВД|УМВД|ГУ\s+МВД)\b[^;\n]*?)"
        r"(?=\.\s*$|[,;]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bкем\s+выдан\s+(?:документ|паспорт)\s*[:—-]?\s*"
        r"(?P<value>(?:У?ФМС|О?МВД|УМВД|ГУ\s+МВД)\b[^;\n]*?)"
        r"(?=\.\s*$|[,;]|$)",
        re.IGNORECASE,
    ),
)
_LICENSE = (
    re.compile(
        r"\bводительск(?:ое|ие)\s+(?:удостоверение|права)(?:\s+РФ)?\s*[:№—-]?\s*"
        r"(?P<value>\d{2}[- ]\d{2}[- ]\d{6})(?!\d)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:водитель|гражданин|клиент)\s+(?:предъявил\s+)?права\s+серии\s+"
        r"(?P<value>\d{2}[ -]\d{2}\s*№\s*\d{6})(?!\d)",
        re.IGNORECASE,
    ),
)
_CARDHOLDER = re.compile(
    rf"\b(?:NAME\s+ON\s+CARD|CARD\s+HOLDER|держатель|владелец)\s*[:—-]?\s*"
    rf"(?P<value>{_LATIN_NAME}){_END}",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:домашний\s+адрес|адрес\s+регистрации|"
    r"клиент\w*\s+прожива\w*|место\s+жительства)\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"\b(?:город|г\.|(?:прожива\w*\s+в))\s*(?P<value>{_WORD})(?=\s*[,;])",
    re.IGNORECASE,
)
_STREET = re.compile(rf"\b(?:на\s+)?улиц(?:а|е)\s+(?P<value>{_WORD})(?=\s*[,;])", re.IGNORECASE)
_HOUSE = re.compile(r"\b(?:в\s+)?дом(?:е)?\s+(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;])", re.IGNORECASE)
_FLAT = re.compile(r"\bквартир(?:а|е)\s+(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)

_PUBLIC_EMAIL = re.compile(
    r"^(?:webmaster|postmaster|hr|recruiting|editor|newsdesk|press|sales|support|info)@",
    re.IGNORECASE,
)
_PUBLIC_EMAIL_CONTEXT = re.compile(
    r"\b(?:сайт\w*|команд\w*|отдел\w*|редакц\w*|общ\w*\s+адрес|"
    r"публичн\w*|опубликован\w*)\b",
    re.IGNORECASE,
)
_NON_SECRET_CVV_CONTEXT = re.compile(
    r"\b(?:артикул|каталог|краск\w*|модель|макет|пример|образец|тестов\w*)\b",
    re.IGNORECASE,
)
_DOC_TERMS_CONTEXT = re.compile(
    r"\b(?:учебник|словарь|глоссарий|определение\s+термин\w*)\b",
    re.IGNORECASE,
)
_DOCUMENTATION_CONTEXT = re.compile(
    r"\b(?:документац\w*|инструкц\w*|пример\w*|образец|шаблон\w*|"
    r"подсказк\w*|учебн\w*|тестов\w*|песочниц\w*|макет\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 105,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return 13 <= len(digits) <= 19 and total % 10 == 0


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON:
        for match in pattern.finditer(text):
            yield _entity(text, "PERSON", match.span("value"), "person_context_v3_6")
    if _PERSONAL_PAYMENT.search(text):
        for match in _DOT_CARD.finditer(text):
            if _valid_luhn(match.group("value")):
                yield _entity(text, "BANK_CARD", match.span("value"), "dot_card_v3_6", 110)
    for pattern, entity_type, source in (
        (_PASSPORT_LABELLED, "PASSPORT_RF", "passport_label_v3_6"),
        (_PASSPORT_COMPACT, "PASSPORT_RF", "passport_compact_v3_6"),
        (_DIVISION, "DIVISION_CODE", "division_label_v3_6"),
        (_BIRTH_TEXT, "BIRTH_DATE", "birth_text_v3_6"),
        (_CARDHOLDER, "CARDHOLDER_NAME", "cardholder_v3_6"),
    ):
        for match in pattern.finditer(text):
            yield _entity(text, entity_type, match.span("value"), source, 110)
    if re.search(r"\bпаспорт\b", text, re.IGNORECASE):
        for match in _DIVISION_IN_PASSPORT.finditer(text):
            yield _entity(text, "DIVISION_CODE", match.span("value"), "division_passport_v3_6")
    for patterns, entity_type, source in (
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_v3_6"),
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_v3_6"),
        ((_CITIZENSHIP,), "CITIZENSHIP", "citizenship_v3_6"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_v3_6"),
        (_LICENSE, "DRIVER_LICENSE_RF", "license_v3_6"),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                yield _entity(text, entity_type, match.span("value"), source, 110)
    if _ADDRESS_ANCHOR.search(text):
        for entity_type, pattern in (
            ("ADDRESS_COUNTRY", _COUNTRY),
            ("ADDRESS_POSTAL_CODE", _POSTCODE),
            ("ADDRESS_CITY", _CITY),
            ("ADDRESS_STREET", _STREET),
            ("ADDRESS_HOUSE", _HOUSE),
            ("ADDRESS_APARTMENT", _FLAT),
        ):
            for match in pattern.finditer(text):
                yield _entity(text, entity_type, match.span("value"), "address_v3_6")


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


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    if entity.source.endswith("_v3_6") and _DOCUMENTATION_CONTEXT.search(text):
        return True
    if entity.entity_type == "EMAIL":
        return bool(_PUBLIC_EMAIL.search(entity.text) and _PUBLIC_EMAIL_CONTEXT.search(text))
    if entity.entity_type == "CVV":
        return _NON_SECRET_CVV_CONTEXT.search(text) is not None
    if entity.entity_type == "PLACE_OF_BIRTH":
        return bool(
            _DOC_TERMS_CONTEXT.search(text)
            or not re.search(r"[А-ЯЁа-яё]{2}", entity.text)
        )
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Return production v3.3 plus conservative high-context candidates."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge([*production_detect(text), *_supplemental(text)])
        if not _suppressed(text, entity)
    ]
