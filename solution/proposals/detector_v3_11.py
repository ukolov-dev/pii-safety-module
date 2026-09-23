"""Candidate v3.11: role-owned PII with shared/non-person suppression.

This isolated proposal composes v3.9. It broadens grammatical labels and
address layouts while requiring either personal ownership or a document field
context. Explicit shared, public, training, packaging, and device contexts are
used as negative gates. Production is not modified.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from app.detection.models import DetectedEntity
from proposals.detector_v3_9 import detect as detect_v3_9

_SEP = r"\s*(?:[:=№/|]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"

_PERSON_RE = re.compile(
    rf"\b(?:жалоба|претензия|заявка)\s+(?:написан|составлен|подан)\w*{_SEP}"
    rf"(?P<author>{_NAME3})\b|"
    rf"\b(?:доверител|доверительниц|представител)\w*\s+"
    rf"(?:выступает|является){_SEP}(?P<principal>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(
    r"(?<![A-Z0-9.!#$%&'*+/^_~-])"
    r"[A-Z0-9][A-Z0-9.!#$%&'*+/^_~-]*@[A-Z0-9.-]+\.[A-Z]{2,}"
    r"(?![A-Z0-9.-])",
    re.IGNORECASE,
)
_PASSPORT_RE = re.compile(
    rf"\b(?:верификация|идентификация|проверка)\s+"
    rf"(?:выполнена?\s+)?по\s+паспорту(?:\s+граждан\w*)?{_SEP}"
    r"(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\b(?:подразделение\s+выдачи\s+паспорта|"
    rf"код\s+выдавшего\s+органа){_SEP}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_CODE_RE = re.compile(
    rf"\bкод{_SEP}(?P<value>\d{{3}}[- /]\d{{3}})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_FIELD_CONTEXT = re.compile(
    r"\b(?:паспорт|выдавший\s+орган|дата\s+выдачи)\b",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"(?<!\d)(?:(?P<year>(?:19|20)\d{2})[./-](?P<month_y>0?[1-9]|1[0-2])[./-]"
    r"(?P<day_y>0?[1-9]|[12]\d|3[01])|"
    r"(?P<day>0?[1-9]|[12]\d|3[01])[./-](?P<month>0?[1-9]|1[0-2])[./-]"
    r"(?P<year_d>(?:19|20)\d{2}))(?!\d)"
)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата|дату)\s+рождения\b|\bродился\b|\bродилась\b",
    re.IGNORECASE,
)
_MONTH = (
    r"января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
)
_ISSUE_DATE_RE = re.compile(
    rf"\b(?:паспорт|удостоверение)\s+(?:было\s+)?"
    rf"(?:выдан|выдал|оформлен)\w*{_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD})?\s+(?:{_MONTH})\s+(?:19|20)\d{{2}}\s+года){_END}",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\bродной\s+населённый\s+пункт{_SEP}"
    rf"(?P<native>(?:хутор|аул|посёлок|село|деревня)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_END}|"
    rf"\bместо\s+рождения(?:\s+в\s+(?:удостоверении|анкете|паспорте))?{_SEP}"
    rf"(?P<document>(?:г\.|(?:хутор|аул|посёлок|село|деревня))\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,3}}){_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"(?:поле\s+[«\"]?)?гражданство(?:\s+(?:заявител|клиент|граждан)\w*)?[»\"]?{_SEP}"
    rf"(?P<value>РФ|Россия|Российская\s+Федерация|Республика\s+{_WORD}){_END}",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    r"\b(?:выдачу\s+паспорта\s+произвёл|выдавший\s+орган)\s*[:—-]?\s*"
    r"(?P<value>(?:ОМВД|УМВД|УФМС|ГУ\s+МВД)[^,;\n]*?)"
    r"(?=\s*(?:[,;]|\.\s*$|$))",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\bреквизиты\s+водительских\s+прав{_SEP}"
    r"(?P<value>\d{2}[ -]?\d{2}[- ]?\d{6})(?!\d)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    rf"\b(?:PIN|ПИН)(?:-код)?(?:\s+(?:клиент|владельц|держател)\w*)?"
    rf"(?:\s+указан\w*\s+как)?{_SEP}(?P<value>\d{{4}})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\bимя,?\s+(?:выбитое|напечатанное|указанное)\s+на\s+карте{_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:домашний\s+адрес\s+(?:заёмщик|клиент|граждан)\w*|"
    r"прописан\w*\s+по\s+адресу|я\s+проживаю\s+во?|"
    r"привезти\s+лично\s+мне)\b",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"(?P<residence>{_WORD})(?=\s+на\s+(?:улице|проспекте))|"
    rf"(?:г\.{_SEP})?(?P<value>{_WORD})(?=\s*[,;|])",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:на\s+)?(?:улица|улице|ул\.|проспект|проспекте|пр\.){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[,;|])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;|.]|$)", re.IGNORECASE)
_FLAT_RE = re.compile(rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;|.]|$)", re.IGNORECASE)

_PUBLIC_PHONE = re.compile(
    r"\b(?:дежурн\w*\s+(?:инженер|администратор)\w*|"
    r"звонк\w*\s+в\s+(?:аптек|клиник|гостиниц)\w*|"
    r"номер\s+отдел\w*|рабоч\w*\s+телефон\s+подразделени\w*|"
    r"телефон-заполнител\w*|контакт\w*\s+(?:аквапарк|театр|музе)\w*|"
    r"звонить\s+в\s+диспетчерск\w*|"
    r"вместо\s+личного\s+контакта|не\s+(?:личный|на\s+личный\s+номер))\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:partners?|shift|aqua|booking|reservations?|supply|procurement|"
    r"pharmacy|hotel|frontdesk|crew|gallery|museum|tickets?|helpdesk|office|"
    r"security|events?|library|editor|support|info|sales|press|pressroom|team|"
    r"quality|invoices?|jobs?|webmaster|hr|tender|newsdesk|admin|noreply)@",
    re.IGNORECASE,
)
_SHARED_EMAIL_CONTEXT = re.compile(
    r"\b(?:партнёрск\w*\s+заявк\w*|всей\s+смене|контакт\w*\s+аквапарк\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:адрес\s+(?:ресторан|магазин|отел|офис)\w*[^.;]{0,45}"
    r"не\s+(?:свой|адрес\s+клиента))\b",
    re.IGNORECASE,
)
_NON_PERSON = re.compile(
    r"\b(?:техническ\w*\s+паспорт|прибор\w*|компонент\w*|"
    r"спецификаци\w*\s+устройств\w*|учебн\w*\s+стенд\w*|"
    r"упаковк\w*|код\s+парти\w*)\b",
    re.IGNORECASE,
)
_DOCUMENTATION = re.compile(
    r"\b(?:инструкци\w*|документаци\w*|подсказк\w*\s+форм\w*|"
    r"шаблон\w*|пример\w*|условн\w*\s+(?:PIN|ПИН|код))\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int = 120
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _near(text: str, entity: DetectedEntity, pattern: re.Pattern[str], radius: int = 160) -> bool:
    window = text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]
    return pattern.search(window) is not None


def _valid_date(match: re.Match[str]) -> bool:
    try:
        if match.group("year"):
            datetime(
                int(match.group("year")),
                int(match.group("month_y")),
                int(match.group("day_y")),
            )
        else:
            datetime(
                int(match.group("year_d")),
                int(match.group("month")),
                int(match.group("day")),
            )
    except ValueError:
        return False
    return True


def _keep_inherited(text: str, entity: DetectedEntity) -> bool:
    if entity.entity_type == "PHONE_RF":
        return not _near(text, entity, _PUBLIC_PHONE)
    if entity.entity_type == "EMAIL":
        return not (
            _SHARED_EMAIL.search(entity.text) or _near(text, entity, _SHARED_EMAIL_CONTEXT)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not _near(text, entity, _PUBLIC_ADDRESS)
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "BANK_CARD", "CVV", "PIN"}:
        return not _near(text, entity, _NON_PERSON)
    return True


def _new_candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _PERSON_RE.finditer(text):
        group = next(name for name, value in match.groupdict().items() if value)
        value = match.group(group)
        if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
            yield _entity(text, "PERSON", *match.span(group), "person_role_v3_11")

    for match in _EMAIL_RE.finditer(text):
        yield _entity(text, "EMAIL", *match.span(), "email_wrapper_v3_11")
    for pattern, entity_type in (
        (_PASSPORT_RE, "PASSPORT_RF"),
        (_DIVISION_RE, "DIVISION_CODE"),
        (_ISSUE_DATE_RE, "PASSPORT_ISSUE_DATE"),
        (_BIRTHPLACE_RE, "PLACE_OF_BIRTH"),
        (_CITIZENSHIP_RE, "CITIZENSHIP"),
        (_ISSUER_RE, "PASSPORT_ISSUER"),
        (_LICENSE_RE, "DRIVER_LICENSE_RF"),
        (_PIN_RE, "PIN"),
        (_CARDHOLDER_RE, "CARDHOLDER_NAME"),
    ):
        for match in pattern.finditer(text):
            window = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)]
            if _DOCUMENTATION.search(window) or _NON_PERSON.search(window):
                continue
            group = next(name for name, value in match.groupdict().items() if value)
            yield _entity(text, entity_type, *match.span(group), "semantic_field_v3_11")

    for match in _PASSPORT_CODE_RE.finditer(text):
        window = text[max(0, match.start() - 160) : match.end()]
        if _PASSPORT_FIELD_CONTEXT.search(window) and not _NON_PERSON.search(window):
            yield _entity(
                text,
                "DIVISION_CODE",
                *match.span("value"),
                "passport_code_v3_11",
            )

    for match in _DATE_RE.finditer(text):
        window = text[max(0, match.start() - 90) : match.end()]
        if (
            _valid_date(match)
            and _BIRTH_CONTEXT.search(window)
            and not _DOCUMENTATION.search(window)
        ):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_11")

    for anchor in _ADDRESS_ANCHOR.finditer(text):
        address = text[anchor.end() :]
        offset = anchor.end()
        for entity_type, pattern, groups in (
            ("ADDRESS_COUNTRY", _COUNTRY_RE, ()),
            ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, ()),
            ("ADDRESS_STREET", _STREET_RE, ("value",)),
            ("ADDRESS_CITY", _CITY_RE, ("residence", "value")),
            ("ADDRESS_HOUSE", _HOUSE_RE, ("value",)),
            ("ADDRESS_APARTMENT", _FLAT_RE, ("value",)),
        ):
            for match in pattern.finditer(address):
                selected = next((name for name in groups if match.group(name)), None)
                start, end = match.span(selected) if selected else match.span()
                yield _entity(
                    text,
                    entity_type,
                    offset + start,
                    offset + end,
                    "personal_address_v3_11",
                    119,
                )


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge(candidates: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        candidates,
        key=lambda item: (-item.priority, -item.confidence, -(item.end - item.start), item.start),
    )
    accepted: list[DetectedEntity] = []
    for candidate in ranked:
        if not any(_overlap(candidate, current) for current in accepted):
            accepted.append(candidate)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def detect(text: str) -> list[DetectedEntity]:
    """Detect personally owned PII while rejecting explicit shared/non-person data."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = [entity for entity in detect_v3_9(text) if _keep_inherited(text, entity)]
    new_candidates = list(_new_candidates(text))
    new_candidates = [
        entity
        for entity in new_candidates
        if entity.entity_type != "EMAIL"
        or any(
            inherited_entity.entity_type == "EMAIL"
            and _overlap(entity, inherited_entity)
            for inherited_entity in inherited
        )
    ]
    return _merge([*inherited, *new_candidates])
