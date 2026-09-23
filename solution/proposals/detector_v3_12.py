"""Candidate v3.12: semantic ownership generalization over candidate v3.10.

The proposal adds reusable field grammars and suppresses values owned by public,
organizational, technical, or synthetic contexts. Production remains unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.models import DetectedEntity
from proposals.detector_v3_10 import detect as detect_v3_10

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3}"
_END = r"(?=\s*(?:[,;|]|\.(?:\s|$)|$))"
_DATE = (
    r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{2}[-/.](?:1[0-2]|0?[1-9])[-/.](?:3[01]|[12]\d|0?[1-9])"
)
_MONTHS = (
    r"января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря"
)
_ORDINAL = (
    r"первого|второго|третьего|четв[её]ртого|пятого|шестого|седьмого|"
    r"восьмого|девятого|десятого|одиннадцатого|двенадцатого|"
    r"тринадцатого|четырнадцатого|пятнадцатого|шестнадцатого|"
    r"семнадцатого|восемнадцатого|девятнадцатого|двадцатого|"
    r"двадцать\s+(?:первого|второго|третьего|четв[её]ртого|пятого|"
    r"шестого|седьмого|восьмого|девятого)|тридцатого|тридцать\s+первого"
)

_PERSON = (
    re.compile(
        rf"\b(?:жалоб\w*|заявлени\w*|обращени\w*|претензи\w*)\s+"
        rf"(?:написан\w*|подписан\w*|составлен\w*)\s+(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bФ\.?И\.?О\.?(?:\s+(?:абонента|за[её]мщика|страхователя|"
        rf"доверителя|представителя|пациента|получателя))?\s*[:/—-]\s*"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:доверител\w*|представител\w*|страховател\w*)\s+"
        rf"(?:выступает|является)\s+(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)
_DOT_CARD = re.compile(r"(?<!\d)(?P<value>\d{4}(?:\.\d{4}){3})(?!\d)")
_PERSONAL_PAN = re.compile(
    r"\b(?:мой|моя|мо[её]|личн\w*|персональн\w*|плат[её]жн\w*|"
    r"клиент\w*|владел\w*|держател\w*)[^.;\n]{0,35}\b(?:PAN|карт\w*)\b|"
    r"\b(?:PAN|карт\w*)[^.;\n]{0,35}\b(?:мой|личн\w*|клиент\w*|владел\w*)\b",
    re.IGNORECASE,
)
_PASSPORT_COMPACT = re.compile(
    r"\b(?:верификаци\w*|идентификаци\w*|проверка\w*)[^.;\n]{0,35}\b"
    r"паспорту?\s+(?:гражданина|клиента|заявителя|владельца)\s*"
    r"(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_DIVISION = re.compile(
    r"\b(?:подразделение\s+выдачи(?:\s+паспорта)?|код\s+подразделения\s+выдачи)"
    r"\s*[:=—-]?\s*(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_BIRTH_DATE = re.compile(
    rf"\b(?:рождени[ея]\s+(?:клиента|заявителя|участника|пациента|физлица)|"
    rf"DOB(?:\s+(?:клиента|заявителя|пациента|физлица))?)"
    rf"(?:\s+в\s+формате\s+[A-Z]+)?\s*[:—-]?\s*(?P<value>{_DATE})",
    re.IGNORECASE,
)
_BIRTHPLACE = (
    re.compile(
        rf"\b(?:родной\s+насел[её]нный\s+пункт|насел[её]нный\s+пункт\s+рождения)"
        rf"\s*[:—-]?\s*(?P<value>(?:хутор|станица|деревня|село|пос[её]лок|город|г\.)"
        rf"\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bместо\s+рождения(?:\s+в\s+(?:паспорте|документе|удостоверении))?"
        rf"\s*[:—-]+\s*(?P<value>(?:хутор|станица|деревня|село|пос[её]лок|"
        rf"город|г\.)\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP = re.compile(
    rf"\bгражданство(?:\s+(?:клиента|заявителя|гражданина|физлица))?[»\"']?"
    rf"\s*[:—-]\s*(?P<value>РФ|{_WORD}(?:\s+{_WORD}){{0,2}}){_END}",
    re.IGNORECASE,
)
_ISSUER = re.compile(
    r"\b(?:выдачу\s+(?:паспорта|документа)\s+(?:произв[её]л|осуществил)|"
    r"(?:паспорт|документ)\s+(?:оформил|выдал))\s+"
    r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+(?:МВД|УФМС))\b[^,;\n]*?)"
    r"(?=\.\s*$|[,;]|$)",
    re.IGNORECASE,
)
_ISSUE_WORD_DATE = re.compile(
    rf"\b(?:паспорт|удостоверение|документ)\s+(?:оформили\s+и\s+)?"
    rf"(?:выдали|выдан|оформлен)\s+(?P<value>(?:{_ORDINAL})\s+(?:{_MONTHS})\s+"
    rf"(?:19|20)\d{{2}}\s*года)",
    re.IGNORECASE,
)
_LICENSE = re.compile(
    r"\b(?:реквизиты\s+водительск(?:их|ого)\s+(?:прав|удостоверения)|"
    r"(?:мо[её]|личн\w*|персональн\w*)\s+ВУ)\s*[:—-]?\s*"
    r"(?P<value>\d{2}(?:[- ]?\d{2})[- ]\d{6})(?!\d)",
    re.IGNORECASE,
)
_PIN = re.compile(
    r"\b(?:PIN|ПИН)(?:[- ]код)?\s+(?:клиента|владельца|держателя)\s+"
    r"(?:указан|записан|сохран[её]н)(?:\s+как)?\s*[:=—-]?\s*"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER = re.compile(
    rf"\b(?:имя\s*,?\s*(?:выбитое|напечатанное|указанное)\s+на\s+карте|"
    rf"имя\s+держателя\s+карты)\s*[:—-]?\s*(?P<value>{_LATIN_NAME}){_END}",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:домашн\w*\s+адрес\w*|адрес\s+(?:регистрации|проживания)|"
    r"прописан\w*\s+по\s+адресу|(?:я|клиент|заявитель|за[её]мщик)\s+прожива\w*|"
    r"привезти\s+(?:лично\s+)?мне|доставить\s+(?:лично\s+)?мне)\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"(?:\b(?:г\.|город|прожива\w*\s+(?:в|во))\s*(?P<labelled>{_WORD})|"
    rf"(?<![А-ЯЁа-яё])(?P<bare>{_WORD})(?=\s*[,;|]\s*(?:улица|ул\.|"
    rf"проспект|переулок|на\s+улице)))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:на\s+)?(?:улиц(?:а|е)|ул\.|проспект|переулок)\s+"
    rf"(?P<value>{_WORD})(?=\s*[,;|])",
    re.IGNORECASE,
)
_HOUSE = re.compile(
    r"\b(?:дом|д\.)\s*(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;|])", re.IGNORECASE
)
_FLAT = re.compile(
    r"\b(?:квартира|кв\.)\s*(?P<value>\d+)(?=\s*[,;|.]|$)", re.IGNORECASE
)

_PERSONAL = re.compile(
    r"\b(?:личн\w*|персональн\w*|мой|моя|мо[её]|мне|меня|клиент\w*|"
    r"заявител\w*|граждан\w*|физлиц\w*|пациент\w*|страховател\w*|"
    r"за[её]мщик\w*|владел\w*|держател\w*|получател\w*)\b",
    re.IGNORECASE,
)
_NEGATED_PERSONAL = re.compile(
    r"\b(?:не\s+(?:личн\w*|свой|своего|человеку|клиенту|клиента|заявителю)|"
    r"не\s+на\s+личн\w*|а\s+не\s+(?:свой|клиента|заявителя)|"
    r"вместо\s+(?:своего|личного)|не\s+используется\s+человеком)\b",
    re.IGNORECASE,
)
_PUBLIC_ORG = re.compile(
    r"\b(?:справочн\w*|дежурн\w*|инженер\w*|аптек\w*|гостиниц\w*|"
    r"бронирован\w*|диспетчерск\w*|подразделени\w*|отдел\w*|служб\w*|"
    r"редакци\w*|магазин\w*|деканат\w*|общежити\w*|галере\w*|аквапарк\w*|"
    r"театр\w*|музе\w*|офис\w*|компани\w*|организаци\w*|партн[её]р\w*)\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:partners?|shift|newsroom|aqua|returns?|docs?|booking|reception|"
    r"deanoffice|gallery|supply|contact|admin|office|team|press|sales|"
    r"support|help|info|hr)@",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:юридическ\w*\s+адрес|выставочн\w*\s+зал|концертн\w*\s+зал|"
    r"постамат\w*|ресторан\w*|офис\w*|партн[её]р\w*|магазин\w*|склад\w*|"
    r"организаци\w*|компани\w*|не\s+(?:свой|домашн\w*))\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:техническ\w*|прибор\w*|устройств\w*|компонент\w*|спецификаци\w*|"
    r"упаковк\w*|партии|поставк\w*|маршрут\w*|табличк\w*|оборудовани\w*|"
    r"заводск\w*|каталог\w*|детал\w*|издели\w*|стенд\w*|макет\w*|"
    r"пример\w*|образец\w*|тестов\w*|заполнител\w*)\b",
    re.IGNORECASE,
)


def _entity(text: str, entity_type: str, span: tuple[int, int], source: str) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.998, source, 140)


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    parity = len(digits) % 2
    total = 0
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return 13 <= len(digits) <= 19 and total % 10 == 0


def _title_name(value: str) -> bool:
    return all(part[0].isupper() for part in value.split())


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON:
        for match in pattern.finditer(text):
            if _title_name(match.group("value")):
                yield _entity(text, "PERSON", match.span("value"), "person_semantic_v3_12")
    if _PERSONAL_PAN.search(text):
        for match in _DOT_CARD.finditer(text):
            if _valid_luhn(match.group("value")):
                yield _entity(text, "BANK_CARD", match.span("value"), "dot_card_v3_12")
    for pattern, entity_type, source in (
        (_PASSPORT_COMPACT, "PASSPORT_RF", "passport_owned_v3_12"),
        (_DIVISION, "DIVISION_CODE", "division_field_v3_12"),
        (_BIRTH_DATE, "BIRTH_DATE", "birth_field_v3_12"),
        (_CITIZENSHIP, "CITIZENSHIP", "citizenship_field_v3_12"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_action_v3_12"),
        (_ISSUE_WORD_DATE, "PASSPORT_ISSUE_DATE", "issue_words_v3_12"),
        (_LICENSE, "DRIVER_LICENSE_RF", "license_field_v3_12"),
        (_PIN, "PIN", "pin_field_v3_12"),
        (_CARDHOLDER, "CARDHOLDER_NAME", "cardholder_field_v3_12"),
    ):
        for match in pattern.finditer(text):
            yield _entity(text, entity_type, match.span("value"), source)
    for pattern in _BIRTHPLACE:
        for match in pattern.finditer(text):
            yield _entity(text, "PLACE_OF_BIRTH", match.span("value"), "birthplace_v3_12")
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
                groups = match.groupdict()
                group = "value"
                if groups.get("labelled") is not None:
                    group = "labelled"
                elif groups.get("bare") is not None:
                    group = "bare"
                yield _entity(text, entity_type, match.span(group), "address_owned_v3_12")


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
    personal = _PERSONAL.search(text) is not None
    public = _PUBLIC_ORG.search(text) is not None
    negative = _NEGATED_PERSONAL.search(text) is not None
    technical = _TECHNICAL.search(text) is not None
    if entity.entity_type == "PHONE_RF":
        return (public and (not personal or negative)) or technical
    if entity.entity_type == "EMAIL":
        return bool(
            (_ROLE_EMAIL.search(entity.text) and (public or not personal or negative))
            or (public and (not personal or negative))
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return bool(_PUBLIC_ADDRESS.search(text) and (not personal or negative))
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "CVV"}:
        return technical
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Return v3.10 plus semantic field and ownership rules."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge([*detect_v3_10(text), *_supplemental(text)])
        if not _suppressed(text, entity)
    ]
