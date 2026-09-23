"""Candidate v3.21: structural evidence windows for Russian PII documents.

The proposal extends production v3.20 without modifying it.  It parses compact
form/document blocks, carries personal ownership only across bounded adjacent
clauses, and applies public/technical counter-evidence after candidate merge.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from app.detection.detector_v3_20 import detect as detect_v3_20
from app.detection.models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_SEP = r"\s*(?::|=|№|[-–—]|\||\t)?\s*"
_VALUE_END = r"(?=\s*(?:[,;|.\n]|$))"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[./-](?:1[0-2]|0?[1-9])[./-](?:19|20)\d{2}"

_TRIGGERS = (
    "адрес",
    "жив",
    "прож",
    "паспорт",
    "документ",
    "граждан",
    "заявител",
    "получател",
    "клиент",
    "личн",
    "фио",
    "инн",
    "рожд",
    "пин",
    "pin",
    "cvv",
    "cvc",
    "телефон",
    "email",
    "почт",
)

_PERSONAL_EVIDENCE = re.compile(
    r"\b(?:сам(?:а|ому|ой)?|сво[йеёю]|мо[йяеёию]|мне|его|е[её]|"
    r"клиент\w*|граждан\w*|физлиц\w*|заявител\w*|получател\w*|"
    r"за[её]мщик\w*|застрахован\w*|владел\w*|хозя\w*|пациент\w*|"
    r"доверенн\w*\s+лиц\w*|личн\w*|домашн\w*|мест[оа]\s+жительств\w*|"
    r"регистраци\w*|прожива\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_EVIDENCE = re.compile(
    r"\b(?:администраци\w*|автосервис\w*|банк\w*|выставк\w*|галере\w*|"
    r"дежурн\w*\s+част\w*|дилер\w*|издательств\w*|институт\w*|касс\w*|"
    r"кинотеатр\w*|комитет\w*|корпус\w*|министерств\w*|музе\w*|"
    r"организаци\w*|офис\w*|производител\w*|пункт\w*\s+выдач\w*|"
    r"редакци\w*|рын\w*|служб\w*|стадион\w*|торгов\w*\s+центр\w*|"
    r"фонд\w*|юридическ\w*\s+адрес|общ\w*\s+(?:номер|контакт|ящик))\b",
    re.IGNORECASE,
)
_TECHNICAL_EVIDENCE = re.compile(
    r"\b(?:артикул\w*|детал\w*|запчаст\w*|каталог\w*|контроллер\w*|"
    r"макет\w*|модел\w*|оборудовани\w*|пример\w*|склад\w*|станок\w*|шаблон\w*|"
    r"тест\w*|фиктивн\w*)\b",
    re.IGNORECASE,
)
_NEGATED_PERSONAL = re.compile(
    r"\b(?:не\s+(?:автор\w*|домашн\w*|личн\w*|получател\w*)|"
    r"домашн\w*\s+адрес\w*[^.]{0,35}\s+не\s+указан\w*)\b",
    re.IGNORECASE,
)
_ROLE_MAILBOX = re.compile(
    r"^(?:campus-office|dealers|donations|editors-desk|exhibition|"
    r"logistics-team|nightshift|refund|reports|committee)@",
    re.IGNORECASE,
)
_STRONG_PUBLIC_CONTACT = re.compile(
    r"\b(?:клиентск\w*\s+служб\w*|дежурн\w*\s+част\w*|"
    r"общ\w*\s+(?:контакт|номер)|контакт\w*\s+(?:выставк|галере)\w*)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class EvidenceWindow:
    """A bounded document fragment carrying one ownership decision."""

    start: int
    end: int
    personal: bool
    public: bool
    technical: bool


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 210,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, priority)


def _window(text: str, start: int, end: int, radius: int = 220) -> EvidenceWindow:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    fragment = text[left:right]
    return EvidenceWindow(
        left,
        right,
        _PERSONAL_EVIDENCE.search(fragment) is not None,
        _PUBLIC_EVIDENCE.search(fragment) is not None,
        _TECHNICAL_EVIDENCE.search(fragment) is not None,
    )


_PERSON = re.compile(
    rf"\b(?:данн\w*\s+сообща\w*\s+сам\w*|пациент\w*\s+зовут|"
    rf"доверенн\w*\s+лиц\w*\s+выступил\w*){_SEP}(?P<value>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)

_ADDRESS_BLOCK = re.compile(
    r"\b(?:новый\s+адрес|адрес\s+(?:сам\w*\s+)?(?:владел|клиент|граждан|"
    r"заявител|получател)\w*(?:\s+\w+){0,3}|дом\s+(?:клиент|граждан|"
    r"заявител|получател)\w*|домашн\w*\s+корреспонденци\w*[^.\n]{0,45}?"
    r"направлять)\b\s*[:—-]?",
    re.IGNORECASE,
)
_RESIDENCE_BLOCK = re.compile(
    r"\b(?:он|она|я|клиент|гражданин|заявител\w*|получател\w*)\s+"
    r"(?:постоянно\s+)?(?:жив[её]т|живу|прожива\w*)\s+(?:в|во)\s+",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Российская\s+Федерация|Россия|РФ)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY_SEQUENCE = re.compile(
    rf"(?:^|[,;|\n]\s*)\s*(?:(?:в|во)\s+)?(?:\d{{6}}\s*[,;|\n]\s*)?"
    rf"(?P<value>{_WORD})"
    rf"(?=\s*[,;|]\s*(?:(?:на\s+)?улиц|ул\.))",
    re.IGNORECASE,
)
_CITY_AFTER_RESIDENCE = re.compile(
    rf"^(?:городе\s+)?(?P<value>{_WORD})(?=\s*[,;.\n]|$)", re.IGNORECASE
)
_STREET = re.compile(
    rf"\b(?:на\s+)?(?:улиц(?:а|е|у)|ул\.){_SEP}(?P<value>{_WORD})",
    re.IGNORECASE,
)
_HOUSE = re.compile(
    r"\b(?:дом|д\.|номер(?:\s+дома)?)\s*[:=№-]?\s*"
    r"(?P<value>\d+[А-ЯЁA-Z]?)(?!\d)",
    re.IGNORECASE,
)
_FLAT = re.compile(
    r"\b(?:квартир(?:а|е|у|ы)|кв\.)\s*[:=№-]?\s*(?P<value>\d+)(?!\d)",
    re.IGNORECASE,
)

_COUNTRY_FIELD = re.compile(
    rf"\bстрана\s+(?:мо\w*\s+)?проживани\w*[^.\n]{{0,45}}?{_SEP}"
    r"(?P<value>Российская\s+Федерация|Россия|РФ)\b",
    re.IGNORECASE,
)
_POSTCODE_FIELD = re.compile(
    rf"\b(?:для\s+доставк\w*[^.\n]{{0,45}}?домой[^.\n]{{0,20}}?индекс|"
    rf"индекс\s+(?:квартир|адрес|получател|заявител|клиент)\w*(?:\s+\w+){{0,4}})"
    rf"{_SEP}(?P<value>\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_CITY_FIELD = re.compile(
    rf"\bгород\s*,?\s+в\s+котором\s+(?:постоянно\s+)?прожива\w*\s+"
    rf"(?:физлиц|клиент|граждан|заявител)\w*{_SEP}(?P<value>{_WORD})",
    re.IGNORECASE,
)
_STREET_FIELD = re.compile(
    rf"\bулиц\w*\s+(?:мо\w*\s+)?мест\w*\s+регистраци\w*\s+"
    rf"(?:называется|указана){_SEP}(?P<value>{_WORD})",
    re.IGNORECASE,
)

_PASSPORT = re.compile(
    r"\b(?:идентификаци\w*[^.\n]{0,45}?по\s+паспорту|личн\w*\s+паспорт)"
    r"[^\d\n]{0,30}(?P<value>\d{10}|\d{2}[- ]\d{2}[- ]\d{6})(?!\d)",
    re.IGNORECASE,
)
_DIVISION = re.compile(
    rf"\b(?:КП\s+документ\w*|орган\s+выдач\w*[^.\n]{{0,35}}?код|"
    rf"код\s+подразделени\w*)[^\d\n]{{0,45}}?{_SEP}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_ISSUER = re.compile(
    r"\b(?:паспорт\s+оформлял\w*|выдавш\w*\s+ведомств\w*|"
    r"(?:его|е[её]|документ)\s+выдал\w*)\s*[:—-]?\s*"
    r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b[^;\n\d]*?)"
    r"(?=\s+(?:[0-3]?\d[./-])|\s*;|\s*\.$|$)",
    re.IGNORECASE,
)
_ISSUER_TABLE = re.compile(
    r"\b(?:выдавш\w*\s+ведомств\w*|орган\s+выдач\w*|кем\s+выдан)"
    r"\s*(?:[:=|—-])\s*"
    r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b[^;\n]*?)(?=\s*;|\s*\.$|$)",
    re.IGNORECASE,
)
_ISSUE_DATE_AFTER_ISSUER = re.compile(
    rf"\b(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b[^;\n]{{0,100}}?\s+"
    rf"(?P<value>{_DATE})(?=\s*[;.]|$)",
    re.IGNORECASE,
)
_LICENSE = re.compile(
    r"\bводител\w*\s+(?:предъявил\w*|показал\w*)\s+сво\w*\s+"
    r"(?:водительск\w*\s+)?удостоверени\w*\s*[:№-]?\s*"
    r"(?P<value>\d{2}[- ]\d{2}[- ]\d{6})(?!\d)",
    re.IGNORECASE,
)
_PIN = re.compile(
    rf"\b(?:PIN|ПИН)(?:-код)?\s*,?\s*[^.;\n]{{0,45}}?"
    rf"(?:клиент|владел|держател)\w*[^.;\n]{{0,20}}?{_SEP}"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_BIRTHPLACE = re.compile(
    rf"\bродн\w*\s+город\w*\s+(?:заявител|клиент|граждан)\w*\s+"
    rf"(?:является|указан){_SEP}(?P<value>г\.\s*{_WORD})",
    re.IGNORECASE,
)
_CITIZENSHIP = re.compile(
    rf"\b(?:лицо|гражданин|заявител\w*)\s+состоит\s+в\s+гражданстве{_SEP}"
    rf"(?P<value>Республик\w*\s+{_WORD}(?:\s+{_WORD}){{0,2}}){_VALUE_END}",
    re.IGNORECASE,
)


def _valid_date(value: str) -> bool:
    day, month, year = (int(item) for item in re.split(r"[./-]", value))
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _matches(
    text: str, pattern: re.Pattern[str], entity_type: str, source: str
) -> Iterator[DetectedEntity]:
    for match in pattern.finditer(text):
        yield _entity(text, entity_type, match.span("value"), source)


def _block_end(text: str, start: int, limit: int = 360) -> int:
    end = min(len(text), start + limit)
    newline_gap = text.find("\n\n", start, end)
    if newline_gap >= 0:
        end = newline_gap
    return end


def _address_entities(text: str, start: int, end: int, residence: bool) -> Iterator[DetectedEntity]:
    fragment = text[start:end]
    patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("ADDRESS_COUNTRY", _COUNTRY),
        ("ADDRESS_POSTAL_CODE", _POSTCODE),
        ("ADDRESS_CITY", _CITY_AFTER_RESIDENCE if residence else _CITY_SEQUENCE),
        ("ADDRESS_STREET", _STREET),
        ("ADDRESS_HOUSE", _HOUSE),
        ("ADDRESS_APARTMENT", _FLAT),
    )
    for entity_type, pattern in patterns:
        for match in pattern.finditer(fragment):
            local_start, local_end = match.span("value")
            yield _entity(
                text,
                entity_type,
                (start + local_start, start + local_end),
                "structural_address_v3_21",
            )


def _new_entities(text: str) -> Iterator[DetectedEntity]:
    for match in _PERSON.finditer(text):
        value = match.group("value")
        if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
            yield _entity(text, "PERSON", match.span("value"), "role_person_v3_21")

    for anchor in _ADDRESS_BLOCK.finditer(text):
        yield from _address_entities(text, anchor.end(), _block_end(text, anchor.end()), False)
    for anchor in _RESIDENCE_BLOCK.finditer(text):
        yield from _address_entities(text, anchor.end(), _block_end(text, anchor.end()), True)

    for pattern, entity_type, source in (
        (_COUNTRY_FIELD, "ADDRESS_COUNTRY", "country_field_v3_21"),
        (_POSTCODE_FIELD, "ADDRESS_POSTAL_CODE", "postcode_field_v3_21"),
        (_CITY_FIELD, "ADDRESS_CITY", "city_field_v3_21"),
        (_STREET_FIELD, "ADDRESS_STREET", "street_field_v3_21"),
        (_PASSPORT, "PASSPORT_RF", "passport_owner_v3_21"),
        (_DIVISION, "DIVISION_CODE", "division_field_v3_21"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_field_v3_21"),
        (_ISSUER_TABLE, "PASSPORT_ISSUER", "issuer_table_v3_21"),
        (_LICENSE, "DRIVER_LICENSE_RF", "licence_owner_v3_21"),
        (_PIN, "PIN", "pin_owner_v3_21"),
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_field_v3_21"),
        (_CITIZENSHIP, "CITIZENSHIP", "citizenship_field_v3_21"),
    ):
        yield from _matches(text, pattern, entity_type, source)

    for match in _ISSUE_DATE_AFTER_ISSUER.finditer(text):
        if _valid_date(match.group("value")):
            yield _entity(
                text,
                "PASSPORT_ISSUE_DATE",
                match.span("value"),
                "issuer_date_v3_21",
            )


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        entities,
        key=lambda item: (
            -item.priority,
            -item.confidence,
            -(item.end - item.start),
            item.start,
        ),
    )
    accepted: list[DetectedEntity] = []
    for entity in ranked:
        if not any(_overlap(entity, current) for current in accepted):
            accepted.append(entity)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    evidence = _window(text, entity.start, entity.end)
    fragment = text[evidence.start : evidence.end]
    negated = _NEGATED_PERSONAL.search(fragment) is not None
    if entity.entity_type == "EMAIL":
        return bool(
            _ROLE_MAILBOX.search(entity.text)
            or (evidence.public and not evidence.personal)
            or negated
        )
    if entity.entity_type == "PHONE_RF":
        return bool(
            _STRONG_PUBLIC_CONTACT.search(fragment)
            or (evidence.public and not evidence.personal)
            or negated
            or evidence.technical
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return bool((evidence.public and not evidence.personal) or negated)
    if entity.entity_type == "CVV":
        return evidence.technical
    if entity.entity_type in {
        "DIVISION_CODE",
        "DRIVER_LICENSE_RF",
        "PASSPORT_RF",
        "PASSPORT_ISSUE_DATE",
        "PASSPORT_ISSUER",
        "PIN",
    }:
        return evidence.technical
    if entity.entity_type == "PERSON":
        return bool(evidence.public and not evidence.personal)
    return False


def _long_regions(folded: str, radius: int = 1200) -> list[tuple[int, int]]:
    """Locate and merge bounded evidence regions in a very large document."""

    spans: list[tuple[int, int]] = []
    for trigger in _TRIGGERS:
        position = folded.find(trigger)
        while position >= 0:
            spans.append((max(0, position - radius), min(len(folded), position + radius)))
            position = folded.find(trigger, position + len(trigger))
    if not spans:
        return []
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _shift(entity: DetectedEntity, offset: int) -> DetectedEntity:
    return DetectedEntity(
        entity.entity_type,
        entity.start + offset,
        entity.end + offset,
        entity.text,
        entity.confidence,
        entity.source,
        entity.priority,
    )


def detect(text: str) -> list[DetectedEntity]:
    """Return production entities plus structural candidates and policy gates."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    folded = text.casefold()
    if len(text) >= 100_000:
        regions = _long_regions(folded)
        if not regions:
            return detect_v3_20(text)
        candidates: list[DetectedEntity] = []
        for start, end in regions:
            fragment = text[start:end]
            candidates.extend(_shift(entity, start) for entity in detect_v3_20(fragment))
            candidates.extend(_shift(entity, start) for entity in _new_entities(fragment))
        return [entity for entity in _merge(candidates) if not _suppressed(text, entity)]
    return [
        entity
        for entity in _merge([*detect_v3_20(text), *_new_entities(text)])
        if not _suppressed(text, entity)
    ]
