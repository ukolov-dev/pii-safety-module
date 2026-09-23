"""Candidate v3.23: normalized record/field parser over v3.21.

The parser accepts common OCR and table separators without rewriting source
text, so all returned spans stay exact.  Field evidence is bounded to a record;
public and technical counter-evidence is applied after candidate merging.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from app.detection.models import DetectedEntity
from proposals.detector_v3_21 import detect as detect_v3_21

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3}"
_S = r"[\s_\[\]/.:=|>—–-]*"
_EOL = r"(?=\s*(?:[|;\n]|\.?$))"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[.·/-](?:1[0-2]|0?[1-9])[.·/-](?:19|20)\d{2}"

_TRIGGERS = (
    "фио",
    "ф.и.о",
    "тел",
    "email",
    "mail",
    "паспорт",
    "выдан",
    "ведомство",
    "рожд",
    "граждан",
    "адрес",
    "страна",
    "индекс",
    "город",
    "улиц",
    "дом",
    "кварт",
    "cardholder",
    "holder",
    "pin",
    "cvv",
    "cvc",
    "ву",
)

_PERSONAL = re.compile(
    r"\b(?:я|физлиц\w*|клиент\w*|граждан\w*|заявител\w*|получател\w*|"
    r"владел\w*|держател\w*|сам\w*|"
    r"сво(?:й|я|е|ё|и|ю|его|ей|их|ему|им|ими)|мо[йяеёию]|личн\w*|"
    r"домашн\w*|регистраци\w*|мест\w*\s+жительств\w*|персональн\w*)\b",
    re.IGNORECASE,
)
_PUBLIC = re.compile(
    r"\b(?:PUBLIC(?:_PHONE|_ADDRESS|\s+VENUE)?|ORG_EMAIL|NO_REPLY|HOTLINE|"
    r"SDK_SAMPLE|PUBLIC_TEST|администраци\w*|бухгалтер\w*|выставк\w*|"
    r"горяч\w*\s+лини\w*|издательств\w*|кафедр\w*|касс\w*|магазин\w*|"
    r"банк\w*|библиотек\w*|ведомств\w*|кафедр\w*|кинотеатр\w*|концертн\w*|"
    r"корпоративн\w*|музе\w*|работодател\w*|торгов\w*\s+центр\w*|"
    r"организаци\w*|офис\w*|партн[её]р\w*|площадк\w*|поддержк\w*|"
    r"поликлиник\w*|предприяти\w*|ресторан\w*|туристическ\w*\s+центр\w*|"
    r"фестивал\w*|фонд\w*|филиал\w*|юридическ\w*\s+адрес|"
    r"пункт\w*\s+(?:выдач\w*|самовывоз\w*)|редакци\w*|ресепшен\w*|"
    r"склад\w*|справочн\w*|стадион\w*|театр\w*|фирм\w*|"
    r"общ\w*\s+(?:адрес|номер|почт|ящик))\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:BAD_|BUILD_VERSION|DATE_(?:ERROR|EVENT)|EQUIPMENT|INVALID|"
    r"LOT_NO|MODEL_CVC|OCR_ERROR|SDK(?:_SAMPLE)?|VALIDATION_SET|артикул\w*|"
    r"детал\w*|заглушк\w*|издели\w*|каталог\w*|контроллер\w*|"
    r"макет\w*|оборудовани\w*|образец\w*|ошибочн\w*|парт(?:ия|ии)|"
    r"подсказк\w*|справк\w*|тест\w*|учебн\w*|условн\w*|фиктивн\w*|"
    r"шаблон\w*)\b",
    re.IGNORECASE,
)
_NEGATED = re.compile(
    r"\b(?:не\s+(?:автор\w*|домашн\w*|клиент\w*|личн\w*|мест\w*\s+жительств\w*)|"
    r"(?:адрес|номер|телефон)\w*[^.\n]{0,45}\s+не\s+(?:принадлежит|указан)\w*|"
    r"а\s+не\s+сво[йеёю])\b",
    re.IGNORECASE,
)
_PLACEHOLDER = re.compile(r"^[_—-]+$")
_ROLE_EMAIL = re.compile(
    r"^(?:accounting|crew-support|events|faculty-office|info|partnerdesk|"
    r"poetry|press-office|robot|sales-dept)@",
    re.IGNORECASE,
)
_STRUCTURED = re.compile(
    r"(?:\|{1,2}|_{1,}|>{2,}|\t|\[[^\]\n]+\]|"
    r"\b(?:АНКЕТА|ДОКУМЕНТ|ДОСТАВКА|ПАСПОРТ|PAYMENT_FORM|OCR|"
    r"ЛИЧНЫЕ\s+ДАННЫЕ)\b)",
    re.IGNORECASE,
)
_HARD_PUBLIC = re.compile(
    r"\b(?:PUBLIC(?:_PHONE|_ADDRESS|\s+VENUE)?|ORG_EMAIL|NO_REPLY|HOTLINE|"
    r"PUBLIC_TEST|корпоративн\w*\s+отдел\w*|тип\s+адрес\w*\s*:\s*пункт\w*|"
    r"доставк\w*\s+в\s+организаци\w*|домашн\w*\s+адрес\w*[^.\n]{0,40}"
    r"(?:отсутствует|не\s+указан)|не\s+мест\w*\s+жительств\w*)\b",
    re.IGNORECASE,
)
_HARD_TECHNICAL = re.compile(
    r"\b(?:SDK_SAMPLE|PUBLIC_TEST|VALIDATION_SET|OCR_ERROR|BAD_(?:PAN|INN)|"
    r"EQUIPMENT_PASSPORT|MODEL_CVC|LOT_NO)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FieldRule:
    entity_type: str
    pattern: re.Pattern[str]
    source: str


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


_FIELD_RULES = (
    FieldRule(
        "PERSON",
        _rx(
            rf"\b(?:Ф\.?{_S}И\.?{_S}О\.?|ФИО){_S}"
            rf"(?P<value>(?!(?:получател|заявител|клиент|владел)\w*\b){_NAME3})\b"
        ),
        "record_person_v3_23",
    ),
    FieldRule(
        "PHONE_RF",
        _rx(
            rf"\b(?:телефон|тел\.|мобильн\w*|контакт){_S}"
            rf"(?:клиент|заявител|получател|физлиц)\w*{_S}"
            r"(?P<value>(?:\+7|8)[| (\d-]{10,20}\d)"
        ),
        "record_phone_v3_23",
    ),
    FieldRule(
        "PASSPORT_RF",
        _rx(rf"\bпаспорт(?:{_S}РФ)?{_S}(?P<value>\d{{2}}[- ]\d{{2}}\s*\|?\s*\d{{6}})(?!\d)"),
        "record_passport_v3_23",
    ),
    FieldRule(
        "PASSPORT_RF",
        _rx(r"\b(?P<value>серия\s+\d{4}\s*;\s*паспорт\s*№?\s*\d{6})(?!\d)"),
        "record_passport_fields_v3_23",
    ),
    FieldRule(
        "DIVISION_CODE",
        _rx(
            rf"\b(?:код{_S}подразделени\w*|к{_S}п)(?:{_S}(?:документ|паспорт)\w*)?"
            rf"{_S}(?:записан\w*{_S}(?:как)?)?{_S}(?P<value>\d{{3}}[- /]\d{{3}})(?!\d)"
        ),
        "record_division_v3_23",
    ),
    FieldRule(
        "BIRTH_DATE",
        _rx(rf"\b(?:дата{_S}рожд\w*|ДР){_S}(?P<value>{_DATE})(?!\d)"),
        "record_birth_date_v3_23",
    ),
    FieldRule(
        "PLACE_OF_BIRTH",
        _rx(
            rf"\bместо{_S}рождени\w*{_S}(?P<value>(?:с\.|г\.|село|город|"
            rf"пос[её]лок|пос[её]лке)[ \t]*{_WORD}(?:[ \t]+{_WORD}){{0,4}}){_EOL}"
        ),
        "record_birthplace_v3_23",
    ),
    FieldRule(
        "CITIZENSHIP",
        _rx(
            rf"\bгражданств\w*{_S}(?P<value>Российская\s+Федерация|Россия|РФ|"
            rf"Республик\w*[ \t]+{_WORD}(?:[ \t]+{_WORD}){{0,2}}){_EOL}"
        ),
        "record_citizenship_v3_23",
    ),
    FieldRule(
        "PASSPORT_ISSUER",
        _rx(
            r"\b(?:кем\s+выдан|выдан|выдавш\w*\s+ведомств\w*)\s*[:=|>—-]+\s*"
            r"(?P<value>(?:(?:ГУ|ОТДЕЛ)\s+МВД|УМВД|ОМВД|УФМС)\b[^;\n]*?)"
            r"(?=\s*;|\s*\.$|\n|$)"
        ),
        "record_issuer_v3_23",
    ),
    FieldRule(
        "PASSPORT_ISSUE_DATE",
        _rx(rf"\b(?:дата{_S}выдач\w*|когда){_S}(?P<value>{_DATE})(?!\d)"),
        "record_issue_date_v3_23",
    ),
    FieldRule(
        "DRIVER_LICENSE_RF",
        _rx(
            rf"\b(?:ВУ(?:{_S}РФ)?|водительск\w*\s+(?:права|удостоверени\w*))"
            rf"{_S}(?P<value>\d{{2}}[- ]?\d{{2}}[- ]\d{{6}})(?!\d)"
        ),
        "record_license_v3_23",
    ),
    FieldRule(
        "ADDRESS_COUNTRY",
        _rx(
            rf"\b(?:страна(?:{_S}проживани\w*)?|ADDRESS_COUNTRY)"
            rf"{_S}(?P<value>Российская\s+Федерация|Россия|РФ)\b"
        ),
        "record_country_v3_23",
    ),
    FieldRule(
        "ADDRESS_POSTAL_CODE",
        _rx(
            rf"\b(?:индекс|ADDRESS_POSTAL_CODE){_S}(?:домашн\w*{_S})?"
            r"(?P<value>\d{6})(?!\d)"
        ),
        "record_postcode_v3_23",
    ),
    FieldRule(
        "ADDRESS_CITY",
        _rx(
            rf"\b(?:домашн\w*_город|город\s*/\s*мест\w*\s+жительств\w*)"
            rf"\s*(?:[/=:|>—-]+)\s*(?P<value>{_WORD})\b"
        ),
        "record_city_v3_23",
    ),
    FieldRule(
        "ADDRESS_STREET",
        _rx(
            rf"\bулиц(?:а|е|у)(?:_клиент\w*)?\s*(?:[/=:|>—-]+)\s*"
            rf"(?P<value>{_WORD})\b"
        ),
        "record_street_v3_23",
    ),
    FieldRule(
        "ADDRESS_HOUSE",
        _rx(
            r"\bдом\s*\[(?:физлиц|клиент|заявител)\w*\]\s*(?:[/=:|>—-]+)\s*"
            r"(?P<value>\d+[А-ЯЁA-Z]?)(?!\d)"
        ),
        "record_house_v3_23",
    ),
    FieldRule(
        "ADDRESS_APARTMENT",
        _rx(r"\bквартир\w*\s*(?:[/=:|>—-]+)\s*(?P<value>\d+)(?!\d)"),
        "record_flat_v3_23",
    ),
    FieldRule(
        "CVV",
        _rx(rf"\b(?:CVV2?|CVC2?)(?:{_S}клиент\w*)?{_S}(?P<value>\d{{3,4}})(?!\d)"),
        "record_cvv_v3_23",
    ),
    FieldRule(
        "PIN",
        _rx(
            rf"\b(?:PIN|ПИН)(?:-код)?{_S}(?:персональн\w*{_S})?"
            r"(?P<value>\d{4})(?!\d)"
        ),
        "record_pin_v3_23",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        _rx(
            rf"\b(?:CARDHOLDER{_S}NAME|CARD\s+HOLDER{_S}NAME|HOLDER|держател\w*)"
            rf"{_S}(?P<value>{_LATIN_NAME}){_EOL}"
        ),
        "record_cardholder_v3_23",
    ),
    FieldRule(
        "CARDHOLDER_NAME",
        _rx(
            rf"\bна\s+карт\w*\s+(?:клиент|владел)\w*\s+выбит\w*{_S}"
            rf"(?P<value>{_LATIN_NAME}){_EOL}"
        ),
        "record_cardholder_prose_v3_23",
    ),
)

_ADDRESS_RECORD = re.compile(
    r"\b(?:OCR\s*>>\s*)?(?:адрес|доставк\w*\s+физлиц\w*|личн\w*\s+данн\w*)"
    r"(?:\s+регистраци\w*)?\s*[:=|>—-]*",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Российская\s+Федерация|Россия|РФ)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"(?:^|[,;|\n]\s*)\s*(?:\d{{6}}\s*[,;|\n]\s*)?"
    rf"(?P<value>{_WORD})(?=\s*[,;|\n]\s*(?:ул\.|улиц))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:ул\.|улиц(?:а|е|у))\s*[:=—-]?\s*(?P<value>{_WORD})(?=\s*[,;|\n])",
    re.IGNORECASE,
)
_HOUSE = re.compile(r"\b(?:д\.|дом)\s*[:=—-]?\s*(?P<value>\d+[А-ЯЁA-Z]?)(?!\d)", re.I)
_FLAT = re.compile(r"\b(?:кв\.|квартир\w*)\s*[:=—-]?\s*(?P<value>\d+)(?!\d)", re.I)

_PROSE_BIRTHPLACE = re.compile(
    rf"\bродил\w*\s+в\s+(?P<value>(?:городе|пос[её]лке|селе|деревне)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}})(?=\s+(?:и\b|[.;]|$))",
    re.IGNORECASE,
)
_PROSE_RESIDENCE_CITY = re.compile(
    rf"\b(?:теперь|сейчас)\s+жив\w*\s+в\s+(?:городе\s+)?(?P<value>{_WORD})",
    re.IGNORECASE,
)
_PERSONAL_EMAIL = re.compile(
    r"\b(?:(?:личн\w*[\s_]+)?(?:email|e-mail|почт\w*|адрес)\w*[\s_]+"
    r"(?:личн\w*|физлиц\w*|заявител\w*|владел\w*)|"
    r"личн\w*[\s_]+(?:email|e-mail|почт\w*|адрес)\w*|E-MAIL)"
    r"[^A-Z0-9@\n]{0,45}?"
    r"(?P<value>[A-Z0-9][A-Z0-9.!#$%&'*+/=?^_`{|}~-]*@[A-Z0-9.-]+\.[A-Z]{2,})",
    re.IGNORECASE,
)
_PROSE_ISSUER = re.compile(
    r"\bвыдан\w*\s+(?P<value>(?:(?:ГУ|ОТДЕЛ)\s+МВД|УМВД|ОМВД|УФМС)"
    r"\b[^;\n\d]*?)(?=\s+(?:[0-3]?\d[./-])|\.\s+(?:дата|когда)|\s*;|\s*$)",
    re.IGNORECASE,
)
_PERSONAL_PHONE = re.compile(
    r"\b(?:мобильн\w*|номер\s+сам\w*|личн\w*\s+тел\w*)\s+"
    r"(?:клиент|заявител|получател|владел)\w*\s*[:—=-]?\s*"
    r"(?P<value>(?:\+7|8)[| ()\d-]{10,20}\d)",
    re.IGNORECASE,
)


def _entity(text: str, entity_type: str, span: tuple[int, int], source: str) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, 230)


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[.·/-]", value)]
    try:
        date(parts[2], parts[1], parts[0])
    except ValueError:
        return False
    return True


def _field_entities(text: str) -> Iterator[DetectedEntity]:
    for rule in _FIELD_RULES:
        for match in rule.pattern.finditer(text):
            value = match.group("value")
            if _PLACEHOLDER.fullmatch(value):
                continue
            if rule.entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"} and not _valid_date(value):
                continue
            start, end = match.span("value")
            if rule.entity_type == "PASSPORT_ISSUER" and text[end - 1 : end] == ".":
                end -= 1
            yield _entity(text, rule.entity_type, (start, end), rule.source)
    for pattern, entity_type, source in (
        (_PROSE_BIRTHPLACE, "PLACE_OF_BIRTH", "prose_birthplace_v3_23"),
        (_PROSE_RESIDENCE_CITY, "ADDRESS_CITY", "prose_residence_v3_23"),
        (_PERSONAL_EMAIL, "EMAIL", "personal_email_v3_23"),
        (_PERSONAL_PHONE, "PHONE_RF", "personal_phone_v3_23"),
        (_PROSE_ISSUER, "PASSPORT_ISSUER", "prose_issuer_v3_23"),
    ):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            if entity_type == "PASSPORT_ISSUER" and text[end - 1 : end] == ".":
                end -= 1
            yield _entity(text, entity_type, (start, end), source)


def _record_end(text: str, start: int, limit: int = 420) -> int:
    return min(len(text), start + limit)


def _address_entities(text: str) -> Iterator[DetectedEntity]:
    for anchor in _ADDRESS_RECORD.finditer(text):
        start, end = anchor.end(), _record_end(text, anchor.end())
        fragment = text[start:end]
        for entity_type, pattern in (
            ("ADDRESS_COUNTRY", _COUNTRY),
            ("ADDRESS_POSTAL_CODE", _POSTCODE),
            ("ADDRESS_CITY", _CITY),
            ("ADDRESS_STREET", _STREET),
            ("ADDRESS_HOUSE", _HOUSE),
            ("ADDRESS_APARTMENT", _FLAT),
        ):
            for match in pattern.finditer(fragment):
                local_start, local_end = match.span("value")
                yield _entity(
                    text,
                    entity_type,
                    (start + local_start, start + local_end),
                    "record_address_v3_23",
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


def _bounded(text: str, entity: DetectedEntity, radius: int = 230) -> str:
    return text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]


def _nearest_field(text: str, entity: DetectedEntity, radius: int = 100) -> str:
    left = max(
        text.rfind("\n", 0, entity.start),
        text.rfind(";", 0, entity.start),
        text.rfind(".", 0, entity.start),
        entity.start - radius,
    )
    return text[max(0, left + 1) : entity.end]


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    window = _bounded(text, entity)
    nearest = _nearest_field(text, entity)
    personal_near = _PERSONAL.search(nearest) is not None
    personal_window = _PERSONAL.search(window) is not None
    if entity.priority < 230:
        hard_public = _HARD_PUBLIC.search(window) is not None
        if entity.entity_type == "EMAIL":
            return _ROLE_EMAIL.search(entity.text) is not None or hard_public
        if entity.entity_type in {"PHONE_RF"} or entity.entity_type.startswith("ADDRESS_"):
            return hard_public
        if entity.entity_type in {"BANK_CARD", "CVV"}:
            return _HARD_TECHNICAL.search(window) is not None
        if entity.entity_type == "PERSON":
            return "\n" in entity.text or _PLACEHOLDER.search(entity.text) is not None
        if entity.entity_type == "PLACE_OF_BIRTH":
            before = text[max(0, entity.start - 45) : entity.start]
            return re.search(r"(?:теперь|сейчас)\s+жив\w*\s+в\s*$", before, re.I) is not None
        return False
    if entity.priority >= 230 and not personal_window and _STRUCTURED.search(window) is None:
        return True
    public = _PUBLIC.search(window) is not None
    technical = _TECHNICAL.search(window) is not None
    negated = _NEGATED.search(window) is not None
    if entity.entity_type == "EMAIL":
        return bool(_ROLE_EMAIL.search(entity.text) or (public and not personal_near) or negated)
    if entity.entity_type == "PHONE_RF":
        return bool((public and not personal_near) or technical or negated)
    if entity.entity_type.startswith("ADDRESS_"):
        return bool((public and not personal_near) or technical or negated)
    if entity.entity_type in {
        "BANK_CARD",
        "CVV",
        "DIVISION_CODE",
        "DRIVER_LICENSE_RF",
        "PASSPORT_RF",
        "PASSPORT_ISSUE_DATE",
        "PASSPORT_ISSUER",
        "PIN",
    }:
        return technical
    if entity.entity_type == "PERSON":
        words = entity.text.split()
        valid_words = len(words) in {2, 3, 4} and all(
            re.fullmatch(r"[А-ЯЁа-яё]+(?:-[А-ЯЁа-яё]+)*", word) is not None for word in words
        )
        return not valid_words or technical
    if entity.entity_type == "PLACE_OF_BIRTH":
        before = text[max(0, entity.start - 45) : entity.start]
        return re.search(r"(?:теперь|сейчас)\s+жив\w*\s+в\s*$", before, re.I) is not None
    return False


def _regions(folded: str, radius: int = 1400) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for trigger in _TRIGGERS:
        position = folded.find(trigger)
        while position >= 0:
            spans.append((max(0, position - radius), min(len(folded), position + radius)))
            position = folded.find(trigger, position + len(trigger))
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


def _new_entities(text: str) -> Iterator[DetectedEntity]:
    yield from _field_entities(text)
    yield from _address_entities(text)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII using v3.21 plus normalized bounded record parsing."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = detect_v3_21(text)
    if len(text) >= 100_000:
        added: list[DetectedEntity] = []
        for start, end in _regions(text.casefold()):
            added.extend(_shift(entity, start) for entity in _new_entities(text[start:end]))
    else:
        added = list(_new_entities(text))
    accepted_added = [entity for entity in added if not _suppressed(text, entity)]
    return [
        entity for entity in _merge([*inherited, *accepted_added]) if not _suppressed(text, entity)
    ]
