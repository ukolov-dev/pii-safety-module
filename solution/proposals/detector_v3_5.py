"""Candidate v3.5: morphology- and ownership-aware Russian PII detection.

The module composes the isolated v3.3 candidate with broader semantic recognizers
and stricter public/example suppression.  It does not modify production state.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from app.detection.models import DetectedEntity
from proposals.detector_v3_3 import detect as detect_v3_3

_SEP = r"\s*(?:[:=№/]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME = rf"{_WORD}(?:\s+{_WORD}){{2}}"
_FINAL = r"(?=\s*(?:[,;]|\.(?:\s|$)|$))"

_PERSON_RE = re.compile(
    rf"\b(?:застрахованн\w*\s+лиц\w*|получател\w*(?:\s+посылки)?|"
    rf"сотрудник|работник|заявител\w*|клиент|ф\.?\s*и\.?\s*о\.?)"
    rf"{_SEP}(?P<label_value>{_NAME})\b|"
    rf"\b(?:договор\s+заключён\s+с|обращение\s+подписала?|"
    rf"заявку\s+подала?|меня\s+зовут|на\s+имя){_SEP}"
    rf"(?P<prose_value>{_NAME})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)
_NON_PERSON_PROSE = re.compile(
    r"\b(?:книга|роман|образ|композитор|писатель|поэт|экскурсовод|"
    r"школьник|семинар|лекция|музей)\b",
    re.IGNORECASE,
)

_CARD_RE = re.compile(r"(?<!\d)\d(?:[ .-]?\d){12,18}(?!\d)")
_CARD_CONTEXT = re.compile(
    r"\b(?:PAN|карт\w*|платеж\w*|оплат\w*|вернуть\s+деньги|возврат)\b",
    re.IGNORECASE,
)
_EXAMPLE_CONTEXT = re.compile(
    r"\b(?:тестов\w*|пример\w*|образец|шаблон\w*|учебн\w*|"
    r"документац\w*|подсказк\w*|справочник|каталог\w*|артикул)\b",
    re.IGNORECASE,
)
_PASSPORT_LABEL_RE = re.compile(
    r"\b(?P<value>серия\s+паспорта\s+\d{2}[ -]?\d{2}\s*[,;]?\s*"
    r"(?:его\s+)?номер\s+\d{6})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_COMPACT_RE = re.compile(
    r"\b(?:паспорт\w*|идентификац\w*[^.;]{0,32}паспорт)\s*[:№—-]?\s*"
    r"(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    r"\b(?:код\s+(?:органа\s+выдачи|выдавшего\s+подразделения|подразделения)|к\s*/\s*п)"
    r"\s*[:—-]?\s*(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
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
_NUMERIC_DATE_RE = re.compile(
    r"(?<!\d)(?:(?P<year>(?:19|20)\d{2})[./-](?P<month_y>0?[1-9]|1[0-2])[./-]"
    r"(?P<day_y>0?[1-9]|[12]\d|3[01])|"
    r"(?P<day>0?[1-9]|[12]\d|3[01])[./-](?P<month>0?[1-9]|1[0-2])[./-]"
    r"(?P<year_d>(?:19|20)\d{2}))(?!\d)"
)
_TEXT_DATE_RE = re.compile(
    rf"(?<!\d)(?P<day>0?[1-9]|[12]\d|3[01])\s+"
    rf"(?P<month>{'|'.join(_MONTHS)})\s+(?P<year>(?:19|20)\d{{2}})"
    r"(?:\s*г(?:ода|\.)?)?",
    re.IGNORECASE,
)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата\s+рождения|рождён\s*\(?а?\)?|родил(?:ся|ась)|"
    r"появил(?:ся|ась)\s+на\s+свет|день\s+рождения)\b",
    re.IGNORECASE,
)
_ISSUE_DATE_CONTEXT = re.compile(
    r"\b(?:дата\s+(?:выдачи|оформления)(?:\s+паспорта)?|"
    r"паспорт\s+выдан|удостоверение\s+(?:было\s+)?выдано)\b",
    re.IGNORECASE,
)
_EVENT_CONTEXT = re.compile(
    r"\b(?:музей|выставка|компания|филиал|реконструкция|доставка|заказ)\b",
    re.IGNORECASE,
)

_BIRTHPLACE_RE = re.compile(
    rf"\b(?:место|населённый\s+пункт)\s+рождения{_SEP}"
    rf"(?P<value>(?:(?:город|гор\.?|г\.?|село|деревня|посёлок)\s+)?"
    rf"{_WORD}(?:\s+{_WORD}){{0,3}}?"
    rf"(?:\s*,\s*{_WORD}(?:\s+{_WORD}){{0,2}}\s+(?:область|край|республика|округ|район))?)"
    r"(?=\s*(?:[,;.]|$))",
    re.IGNORECASE,
)
_BIRTHPLACE_PROSE_RE = re.compile(
    rf"\bродил(?:ся|ась)\s+в\s+"
    rf"(?P<value>(?:городе|деревне|селе|посёлке)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}?)(?=\s*[.;])",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\b(?:имеет|текущее)?\s*гражданство{_SEP}"
    rf"(?P<value>РФ|Россия|Российская\s+Федерация|{_WORD}(?:\s+{_WORD}){{0,2}})"
    r"(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    rf"\b(?:паспорт\s+выдал|кем\s+выдан(?:\s+документ)?|"
    rf"орган\s*,?\s*выдавший\s+паспорт){_SEP}"
    r"(?P<value>(?:(?:ГУ\s+)?МВД|УМВД|ОМВД|УФМС|ФМС|ОТДЕЛОМ\s+МВД)"
    r"[^,;\n]*?)(?=\s*(?:;|\.(?:\s*$|\s*\n)|$))",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\b(?:водительское\s+удостоверение(?:\s+РФ)?|водитель\s+предъявил\s+права){_SEP}"
    r"(?P<number>\d{2}[- ]?\d{2}[- ]?\d{6})(?!\d)|"
    r"\bправа\s+серии\s+(?P<series>\d{2}[ -]?\d{2}\s*№\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:NAME\s+ON\s+CARD|CARD\s*HOLDER|CARDHOLDER\s+NAME|держатель|владелец){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:домашний\s+адрес|адрес\s+(?:регистрации|проживания|клиента)|"
    r"место\s+(?:жительства|регистрации)|клиент\s+проживает|я\s+живу)\b",
    re.IGNORECASE,
)
_ADDRESS_COUNTRY_RE = re.compile(r"\b(?:Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"\b(?:город|г\.){_SEP}(?P<label>{_WORD}(?:\s+{_WORD}){{0,2}}?)(?=\s*[,;])|"
    rf"\bпроживает\s+в\s+(?P<prose>{_WORD})(?=\s*[,;])|"
    rf"\bв\s+(?P<after_anchor>{_WORD})(?=\s*[,;])",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:улица|ул\.|проспект|пр-т|переулок|пер\.|шоссе|бульвар|набережная){_SEP}"
    rf"(?P<label>{_WORD}(?:\s+{_WORD}){{0,2}}?)(?=\s*[,;])|"
    rf"\bна\s+улице\s+(?P<prose>{_WORD}(?:\s+{_WORD}){{0,2}}?)(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(
    r"\b(?:в\s+)?(?:доме|дом|д\.)\s*(?P<value>\d+[A-ZА-ЯЁ]?)(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_FLAT_RE = re.compile(
    r"\b(?:в\s+)?(?:квартире|квартира|кв\.)\s*(?P<value>\d+)(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_SHARED_EMAIL = re.compile(
    r"^(?:support|info|sales|press|jobs?|security|office|admin|noreply|tender|newsdesk|"
    r"webmaster|hr|reception|procurement|editor)@",
    re.IGNORECASE,
)
_SHARED_CONTEXT = re.compile(
    r"\b(?:общий\s+адрес|общий\s+ящик|отдел\s+кадров|"
    r"ошибки\s+сайта|команде|закупок|редакционн\w*)\b",
    re.IGNORECASE,
)
_NON_SECRET_CVV = re.compile(
    r"\b(?:артикул|каталог|краска|поиск|тест|пример|инструкция)\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.97, source, priority)


def _near(text: str, start: int, end: int, pattern: re.Pattern[str], radius: int = 110) -> bool:
    return pattern.search(text[max(0, start - radius) : min(len(text), end + radius)]) is not None


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
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
        if match.groupdict().get("year"):
            datetime(
                int(match.group("year")),
                int(match.group("month_y")),
                int(match.group("day_y")),
            )
        else:
            datetime(int(match.group("year_d")), int(match.group("month")), int(match.group("day")))
    except ValueError:
        return False
    return True


def _new_candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _PERSON_RE.finditer(text):
        group = "label_value" if match.group("label_value") else "prose_value"
        start, end = match.span(group)
        words = match.group(group).split()
        if any(_PATRONYMIC.search(word) for word in words[1:]) and not _near(
            text, start, end, _NON_PERSON_PROSE
        ):
            yield _entity(text, "PERSON", start, end, "person_morphology_v3_5", 90)

    for match in _CARD_RE.finditer(text):
        if (
            _valid_luhn(match.group())
            and _near(text, *match.span(), _CARD_CONTEXT)
            and not _near(text, *match.span(), _EXAMPLE_CONTEXT)
        ):
            yield _entity(text, "BANK_CARD", *match.span(), "card_context_v3_5", 100)

    for pattern in (_PASSPORT_LABEL_RE, _PASSPORT_COMPACT_RE, _DIVISION_RE):
        for match in pattern.finditer(text):
            if _near(text, *match.span(), _EXAMPLE_CONTEXT):
                continue
            start, end = match.span("value")
            entity_type = "DIVISION_CODE" if pattern is _DIVISION_RE else "PASSPORT_RF"
            yield _entity(text, entity_type, start, end, "document_label_v3_5", 99)

    for match in _NUMERIC_DATE_RE.finditer(text):
        if (
            not _valid_date(match)
            or _near(text, *match.span(), _EVENT_CONTEXT)
            or _near(text, *match.span(), _EXAMPLE_CONTEXT)
        ):
            continue
        if _near(text, *match.span(), _BIRTH_CONTEXT, radius=85):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_5", 98)
        elif _near(text, *match.span(), _ISSUE_DATE_CONTEXT, radius=95):
            yield _entity(
                text, "PASSPORT_ISSUE_DATE", *match.span(), "issue_context_v3_5", 98
            )
    for match in _TEXT_DATE_RE.finditer(text):
        if _near(text, *match.span(), _EVENT_CONTEXT) or _near(
            text, *match.span(), _EXAMPLE_CONTEXT
        ):
            continue
        if _near(text, *match.span(), _BIRTH_CONTEXT, radius=85):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_5", 98)
        elif _near(text, *match.span(), _ISSUE_DATE_CONTEXT, radius=95):
            yield _entity(
                text, "PASSPORT_ISSUE_DATE", *match.span(), "issue_context_v3_5", 98
            )

    for entity_type, pattern in (
        ("PLACE_OF_BIRTH", _BIRTHPLACE_RE),
        ("PLACE_OF_BIRTH", _BIRTHPLACE_PROSE_RE),
        ("CITIZENSHIP", _CITIZENSHIP_RE),
        ("PASSPORT_ISSUER", _ISSUER_RE),
    ):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            if entity_type == "PLACE_OF_BIRTH" and (
                re.match(r"(?:указан|отсутств|заполнен)", match.group("value"), re.IGNORECASE)
                or _near(text, start, end, _EXAMPLE_CONTEXT)
            ):
                continue
            yield _entity(text, entity_type, start, end, "semantic_field_v3_5", 98)

    for match in _LICENSE_RE.finditer(text):
        group = "number" if match.group("number") else "series"
        start, end = match.span(group)
        yield _entity(text, "DRIVER_LICENSE_RF", start, end, "driver_license_v3_5", 100)
    for match in _CARDHOLDER_RE.finditer(text):
        start, end = match.span("value")
        yield _entity(text, "CARDHOLDER_NAME", start, end, "cardholder_v3_5", 99)

    anchor = _ADDRESS_ANCHOR.search(text)
    if anchor:
        address = text[anchor.end() :]
        offset = anchor.end()
        for entity_type, pattern, group_names in (
            ("ADDRESS_COUNTRY", _ADDRESS_COUNTRY_RE, (None,)),
            ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, (None,)),
            ("ADDRESS_CITY", _CITY_RE, ("label", "prose", "after_anchor")),
            ("ADDRESS_STREET", _STREET_RE, ("label", "prose")),
            ("ADDRESS_HOUSE", _HOUSE_RE, ("value",)),
            ("ADDRESS_APARTMENT", _FLAT_RE, ("value",)),
        ):
            for match in pattern.finditer(address):
                selected_group = next(
                    (name for name in group_names if name and match.group(name)), None
                )
                start, end = match.span(selected_group) if selected_group else match.span()
                yield _entity(
                    text,
                    entity_type,
                    offset + start,
                    offset + end,
                    "personal_address_v3_5",
                    96,
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


def _keep_baseline(text: str, entity: DetectedEntity) -> bool:
    if entity.entity_type == "EMAIL" and (
        _SHARED_EMAIL.search(entity.text)
        or _near(text, entity.start, entity.end, _SHARED_CONTEXT)
    ):
        return False
    if entity.entity_type == "CVV" and _near(
        text, entity.start, entity.end, _NON_SECRET_CVV
    ):
        return False
    if entity.entity_type == "PLACE_OF_BIRTH" and not re.search(
        r"[А-Яа-яЁё]", entity.text
    ):
        return False
    return True


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII using v3.3 plus broader general recognizers and suppression."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    baseline = [entity for entity in detect_v3_3(text) if _keep_baseline(text, entity)]
    return _merge([*baseline, *_new_candidates(text)])
