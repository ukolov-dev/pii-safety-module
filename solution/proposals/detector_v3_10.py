"""Candidate v3.10: clause ownership and field-family extensions over v3.8.

This isolated proposal learns reusable grammar and ownership classes from disclosed
v7 failures. It does not modify production or reference a future holdout.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from app.detection.models import DetectedEntity
from proposals.detector_v3_8 import detect as detect_v3_8

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3}"
_END = r"(?=\s*(?:[,;]|\.(?:\s|$)|$))"

_PERSON = (
    re.compile(
        rf"\b(?:акт|договор|заявлени[ея]|обращение)\s+"
        rf"(?:подписан[оа]?|подписал[аи]?)\s+(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:Ф\.?И\.?О\.?\s+(?:доверителя|представителя|пациента)|"
        rf"автор\s+обращения|водитель)\s*[:—-]?\s*(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)
_SLASH_CARD = re.compile(r"(?<!\d)(?P<value>\d{4}(?:/\d{4}){3})(?!\d)")
_PERSONAL_CARD = re.compile(
    r"\b(?:личн\w*(?:\s+банковск\w*)?\s+карт\w*|"
    r"банковск\w*\s+карт\w*\s+(?:клиента|владельца)|"
    r"PAN\s+(?:клиента|гражданина)|данн\w*\s+(?:моей|личной)\s+карт\w*)\b",
    re.IGNORECASE,
)
_OWN_PASSPORT = re.compile(
    r"\b(?:вв[её]л|указал|сообщил|предъявил)\w*\s+(?:в\s+форму\s+)?"
    r"номер\s+(?:своего|личного)\s+паспорта\s*№?\s*"
    r"(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_NUMERIC_DATE = (
    r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{2}[-/.](?:1[0-2]|0?[1-9])[-/.](?:3[01]|[12]\d|0?[1-9])"
)
_BIRTH_DATE = re.compile(
    rf"\b(?:рождени[ея](?:\s+(?:клиента|застрахованного|физлица))?|"
    rf"день\s+рождения(?:\s+(?:клиента|физлица))?|д\.?\s*р\.?)\s*"
    rf"[:—-]?\s*(?P<value>{_NUMERIC_DATE})",
    re.IGNORECASE,
)
_BIRTHPLACE = (
    re.compile(
        rf"\bместо\s+рождения(?:\s+{_WORD})?\s*[:—-]?\s*"
        rf"(?P<value>(?:(?:рабочий|городской|сельский)\s+)?(?:пос[её]лок|"
        rf"станица|деревня|село|город|г\.)\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bродом\s+из\s+(?P<value>(?:города|села|деревни|пос[её]лка)\s+"
        rf"{_WORD}(?:\s+{_WORD}){{0,2}})(?=\s*[,;.])",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP = re.compile(
    rf"\b(?:гражданская\s+принадлежность|подданство)(?:\s+(?:заявителя|"
    rf"клиента|гражданина))?\s*[:—-]?\s*(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}){_END}",
    re.IGNORECASE,
)
_ISSUER = re.compile(
    r"\b(?:паспорт|документ)\s+оформлен\s+"
    r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+МВД)\b[^,;\n]*?)"
    r"(?=\.\s*$|[,;]|$)",
    re.IGNORECASE,
)
_ISSUE_DATE = re.compile(
    rf"\bвыдан\s+(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+МВД)\b[^;\n]*?\s+"
    rf"(?P<value>{_NUMERIC_DATE})(?=[,;.]|$)",
    re.IGNORECASE,
)
_DIVISION = re.compile(
    r"\bкод\s+(?:выдавшего\s+)?подразделения\s*[:=—-]?\s*"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_LICENSE = re.compile(
    r"\b(?:водительск(?:ие|ое)\s+(?:права|удостоверение)\s+"
    r"(?:имеют|имеет|содержат|содержит)\s+(?:реквизиты|номер)|"
    r"удостоверение\s+водителя,?\s+серия|"
    r"для\s+аренды\s+\w+\s+предъявлено\s+ВУ)\s*(?:№\s*)?"
    r"(?P<value>\d{2}(?:\s?\d{2}|-\d{2})[- ]\d{6})(?!\d)",
    re.IGNORECASE,
)
_LICENSE_SERIES = re.compile(
    r"\bудостоверение\s+водителя,?\s*серия\s+"
    r"(?P<value>\d{2}\s+\d{2}\s*№\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_PIN = re.compile(
    r"\b(?:личный|персональный)\s+(?:PIN|ПИН)(?:[- ]код)?"
    r"(?:\s+(?:клиента|владельца|держателя))?\s*[:—=-]?\s*"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER = re.compile(
    rf"\b(?:CARDHOLDER\s*/\s*)?(?:владелец\s+пластика|имя\s+(?:на\s+"
    rf"пластике|держателя)|имя)(?:\s+карты)?\s*[:—-]?\s*"
    rf"(?P<value>{_LATIN_NAME}){_END}",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:адрес\s+проживания\s+(?:физлица|клиента)|"
    r"место\s+жительства|"
    r"(?:мой|наш)\s+дом\s+находится|доставить\s+(?:гражданину|клиенту|"
    r"получателю)|личный\s+адрес|домашний\s+адрес)\b",
    re.IGNORECASE,
)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"(?:\b(?:город|г\.|находится\s+в)\s*(?P<labelled>{_WORD})|"
    rf"(?<![А-ЯЁа-яё])(?P<bare>{_WORD})(?=\s*[,;]\s*(?:улица|ул\.|"
    rf"на\s+проспекте|проспект|переулок)))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:улица|ул\.|переулок|проспект|на\s+проспекте)\s+"
    rf"(?P<value>{_WORD})(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE = re.compile(r"\b(?:дом|д\.)\s*(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;])", re.IGNORECASE)
_FLAT = re.compile(r"\b(?:квартира|кв\.)\s*(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)

_PERSONAL_CUE = re.compile(
    r"\b(?:личн\w*|мой|моя|мне|меня|клиент\w*|заявител\w*|граждан\w*|"
    r"физлиц\w*|владел\w*|держател\w*|получател\w*)\b",
    re.IGNORECASE,
)
_NEGATED_OWNERSHIP = re.compile(
    r"\b(?:не\s+(?:ему|ей|клиенту|клиента|заявителю|получателю|покупателю)|"
    r"не\s+(?:личн\w*|свой|своего|получателя)|вместо\s+(?:своего|личного)|"
    r"а\s+не\s+(?:покупателя|клиента|заявителя)|"
    r"не\s+адрес\s+(?:получателя|клиента|заявителя))\b",
    re.IGNORECASE,
)
_PUBLIC_CONTACT = re.compile(
    r"\b(?:диспетчерск\w*|ресепшен|секретариат\w*|клиник\w*|кинотеатр\w*|"
    r"музе\w*|магазин\w*|офис\w*|компани\w*|организаци\w*|дежурн\w*\s+част\w*|"
    r"подразделени\w*|служб\w*|касс\w*|сайт\w*)\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:invoices?|quality|team|cinema|pressroom|museum|media|archive|events|"
    r"tickets|helpdesk|library|office|security|webmaster|editor|press|sales|"
    r"support|info|hr)@",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:библиотек\w*|склад\w*|пункт\w*\s+выдач\w*|кинотеатр\w*|"
    r"музе\w*|театр\w*|ресторан\w*|стадион\w*|офис\w*|магазин\w*|"
    r"компани\w*|организаци\w*|не\s+адрес\s+получателя)\b",
    re.IGNORECASE,
)
_NONPERSONAL_DOCUMENT = re.compile(
    r"\b(?:оборудовани\w*|заводск\w*|маркировк\w*|коробк\w*|складск\w*|"
    r"каталог\w*|детал\w*|насос\w*|издели\w*|модул\w*|API[- ]?документац\w*|"
    r"тестов\w*|макет\w*|пример\w*|шаблон\w*)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_CONTEXT = re.compile(
    r"\b(?:подсказк\w*|инструкц\w*|макет\w*|пример\w*|шаблон\w*|"
    r"ошиб\w*|неверн\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 130,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.997, source, priority)


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    parity = len(digits) % 2
    total = 0
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit = digit * 2
            if digit > 9:
                digit -= 9
        total += digit
    return 13 <= len(digits) <= 19 and total % 10 == 0


def _title_name(value: str) -> bool:
    """Reject grammar phrases accidentally captured as a three-token name."""

    return all(part[0].isupper() for part in value.split())


def _valid_date(value: str) -> bool:
    """Validate numeric dates instead of accepting impossible calendar examples."""

    parts = [int(part) for part in re.split(r"[-/.]", value)]
    year, month, day = parts if len(str(parts[0])) == 4 else parts[::-1]
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON:
        for match in pattern.finditer(text):
            if _title_name(match.group("value")):
                yield _entity(text, "PERSON", match.span("value"), "person_context_v3_10")
    if _PERSONAL_CARD.search(text):
        for match in _SLASH_CARD.finditer(text):
            if _valid_luhn(match.group("value")):
                yield _entity(text, "BANK_CARD", match.span("value"), "slash_card_v3_10")
    for pattern, entity_type, source in (
        (_OWN_PASSPORT, "PASSPORT_RF", "passport_owned_v3_10"),
        (_BIRTH_DATE, "BIRTH_DATE", "birth_label_v3_10"),
        (_CITIZENSHIP, "CITIZENSHIP", "citizenship_v3_10"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_v3_10"),
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_v3_10"),
        (_DIVISION, "DIVISION_CODE", "division_label_v3_10"),
        (_LICENSE, "DRIVER_LICENSE_RF", "license_v3_10"),
        (_LICENSE_SERIES, "DRIVER_LICENSE_RF", "license_series_v3_10"),
        (_PIN, "PIN", "pin_owned_v3_10"),
        (_CARDHOLDER, "CARDHOLDER_NAME", "cardholder_v3_10"),
    ):
        for match in pattern.finditer(text):
            if entity_type == "BIRTH_DATE" and (
                _PLACEHOLDER_CONTEXT.search(text) or not _valid_date(match.group("value"))
            ):
                continue
            yield _entity(text, entity_type, match.span("value"), source)
    for pattern in _BIRTHPLACE:
        for match in pattern.finditer(text):
            yield _entity(text, "PLACE_OF_BIRTH", match.span("value"), "birthplace_v3_10")
    if _ADDRESS_ANCHOR.search(text):
        for entity_type, pattern in (
            ("ADDRESS_POSTAL_CODE", _POSTCODE),
            ("ADDRESS_CITY", _CITY),
            ("ADDRESS_STREET", _STREET),
            ("ADDRESS_HOUSE", _HOUSE),
            ("ADDRESS_APARTMENT", _FLAT),
        ):
            for match in pattern.finditer(text):
                groups = match.groupdict()
                group = "value"
                if groups.get("labelled") is not None:
                    group = "labelled"
                elif groups.get("bare") is not None:
                    group = "bare"
                yield _entity(text, entity_type, match.span(group), "address_v3_10")


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


def _low_entropy_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    subscriber = digits[1:] if len(digits) == 11 else digits
    return len(set(subscriber)) <= 2


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    personal = _PERSONAL_CUE.search(text) is not None
    negative_owner = _NEGATED_OWNERSHIP.search(text) is not None
    public_contact = _PUBLIC_CONTACT.search(text) is not None
    nonpersonal_document = _NONPERSONAL_DOCUMENT.search(text) is not None

    if entity.entity_type == "PHONE_RF":
        return _low_entropy_phone(entity.text) or (
            public_contact and (not personal or negative_owner)
        )
    if entity.entity_type == "EMAIL":
        return bool(
            _ROLE_EMAIL.search(entity.text)
            and (public_contact or not personal or negative_owner)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return _PUBLIC_ADDRESS.search(text) is not None and (not personal or negative_owner)
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "CVV"}:
        return nonpersonal_document
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Return v3.8 plus general grammar and negative-ownership rules."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge([*detect_v3_8(text), *_supplemental(text)])
        if not _suppressed(text, entity)
    ]
