"""Candidate v3.8: ownership-first recall extensions over candidate v3.6.

The rules use reusable labels, personal-action anchors, and negative ownership
contexts disclosed by v6. Production is not modified.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.models import DetectedEntity
from proposals.detector_v3_6 import detect as detect_v3_6

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3}"
_END = r"(?=\s*(?:[,;]|\.(?:\s|$)|$))"

_PERSON = (
    re.compile(
        rf"\b(?:заявлени[ея]\s+(?:поступил[оа]?|получен[оа]?)\s+от|"
        rf"получател(?:ем|ь)\s+(?:указан[ао]?|является)|"
        rf"прошу\s+(?:записать|указать)\s+меня\s+как)\s+"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bф\.?\s*и\.?\s*о\.?(?:\s+(?:пациента|работника|"
        rf"застрахованного|владельца|гражданина))?\s*[:—-]\s*"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)
_EMAIL_IN_ENTITY = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)
_MY_INN = re.compile(
    r"\b(?:мой|персональный|личный)\s+(?:налоговый\s+)?"
    r"(?:идентификатор|ИНН)\s*[:—-]?\s*(?P<value>\d{10}|\d{12})(?!\d)",
    re.IGNORECASE,
)
_SLASH_CARD = re.compile(r"(?<!\d)(?P<value>\d{4}(?:/\d{4}){3})(?!\d)")
_PERSONAL_CARD = re.compile(
    r"\b(?:личн\w*\s+карт\w*|карт\w*\s+(?:клиента|владельца)|"
    r"личн\w*\s+реквизит\w*|привязал\w*\s+PAN)\b",
    re.IGNORECASE,
)
_PASSPORT_FULL_LABEL = re.compile(
    r"\b(?P<value>серия\s+(?:документа|паспорта)\s*[:—-]?\s*\d{4}\s*[,;]\s*"
    r"(?:его\s+)?номер\s+(?:паспорта\s*)?[:—-]?\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_OWN_PASSPORT = re.compile(
    r"\b(?:гражданин|заявитель|клиент)\s+(?:предъявил|указал|предоставил)\s+"
    r"(?:свой\s+)?паспорт\s*№?\s*(?P<value>\d{10})(?!\d)",
    re.IGNORECASE,
)
_KP_DIVISION = re.compile(
    r"\b(?:КП|к\s*/\s*п)(?:\s+паспорта|\s+документа)?\s*[:—-]?\s*"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_BIRTH_NUMERIC = (
    re.compile(
        r"\b(?:год[- ]месяц[- ]день\s+рождения|д\s*/\s*р(?:\s+\w+)?)\s*[:—-]?\s*"
        r"(?P<value>(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])|"
        r"(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[0-2])[-/.](?:19|20)\d{2})",
        re.IGNORECASE,
    ),
)
_BIRTHPLACE = (
    re.compile(
        rf"\bместо\s+(?:появления\s+на\s+свет|рождения)\s*[:—-]?\s*"
        rf"(?P<value>(?:станица|город|городе|г\.|деревня|деревне|село|"
        rf"пос[её]лок|пос[её]лке)\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bродил(?:ся|ась)\s+в\s+(?P<value>(?:городе|г\.|станице|"
        rf"деревне|селе|пос[её]лке)\s+{_WORD}(?:\s+{_WORD}){{0,2}})"
        rf"(?=\s+(?:\d{{1,2}}[./-]|гражданство)|\s*[,;.])",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP = re.compile(
    rf"\b(?:является\s+)?граждан(?:кой|ином)\s+"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}){_END}",
    re.IGNORECASE,
)
_ISSUER = (
    re.compile(
        r"\bкем\s+оформлен\s+(?:документ|паспорт)\s*[:—-]?\s*"
        r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+УФМС)\b[^,;\n]*?)"
        r"(?=\.\s*$|[,;]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bвыдавший\s+орган\s*[:—-]?\s*"
        r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+УФМС)\b[^,;\n]*?)"
        r"(?=\.\s*$|[,;]|$)",
        re.IGNORECASE,
    ),
)
_LICENSE = re.compile(
    r"\bводительск(?:ие|ое)\s+(?:права|удостоверение)(?:\s+(?:РФ|гражданина|"
    r"заявителя|клиента))?\s*[:№—-]?\s*"
    r"(?P<value>\d{2}[ -]\d{2}[ -]\d{6})(?!\d)",
    re.IGNORECASE,
)
_CVV = re.compile(
    r"\b(?:секретный|проверочный|защитный)\s+код\s+(?:CVV2?|CVC2?)"
    r"(?:\s+карт\w*(?:\s+клиента)?)?\s*[:—=-]?\s*(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_PIN = re.compile(
    r"\b(?:персональный\s+)?(?:ПИН|PIN)(?:[- ]код)?\s+"
    r"(?:держателя|владельца)(?:\s+карты)?\s+(?:равен|составляет)\s*"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER = re.compile(
    rf"\b(?:embossed\s+name\s*/\s*)?(?:имя\s+(?:держателя|на\s+пластике)|"
    rf"card\s*holder)\s*[:—-]?\s*(?P<value>{_LATIN_NAME}){_END}",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:фактический\s+адрес\s+(?:клиента|заявителя)|прописка\s+физлица|"
    r"(?:он|она|клиент\w*)\s+жив[её]т|для\s+доставки\s+(?:мне|клиенту)\s+домой)\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"(?:\b(?:г\.|город|жив[её]т\s+в)\s*(?P<labelled>{_WORD})|"
    rf"(?<![А-ЯЁа-яё])(?P<bare>{_WORD})(?=\s*,\s*(?:улица|ул\.|переулок|{_WORD}\s+проспект)))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:улица|ул\.|переулок)\s+(?P<labelled>{_WORD})(?=\s*[,;])|"
    rf"\b(?P<prefix>{_WORD})\s+проспект(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE = re.compile(r"\b(?:дом|д\.)\s*(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;])", re.IGNORECASE)
_FLAT = re.compile(r"\b(?:квартира|кв\.)\s*(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)

_PERSONAL_CUE = re.compile(
    r"\b(?:клиент\w*|заявител\w*|граждан\w*|физлиц\w*|личн\w*|мой|моя|"
    r"владел\w*|держател\w*|анкета|мне|меня)\b",
    re.IGNORECASE,
)
_PUBLIC_CONTACT = re.compile(
    r"\b(?:секретариат\w*|завод\w*|касс\w*|музе\w*|театр\w*|магазин\w*|офис\s+поддержки|"
    r"справочн\w*\s+центр|организатор\w*|конференци\w*|экскурси\w*|"
    r"заказы\s+магазина|контакты\s+(?:театра|компании|организации))\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:events|tickets|helpdesk|library|office|security|webmaster|editor|"
    r"newsdesk|press|sales|support|info|hr)@",
    re.IGNORECASE,
)
_HARD_NON_PERSONAL = re.compile(
    r"\b(?:оборудовани\w*|станок|каталог\w*|издели\w*|модул\w*|"
    r"расписани\w*|учебн\w*|инструкц\w*|документац\w*|шаблон\w*|"
    r"макет\w*|пример\w*|тестов\w*|поля\s+.+пусты)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:театр\w*|отел\w*|офис\w*|склад\w*|филиал\w*|компани\w*|организаци\w*|"
    r"фестивал\w*|площадк\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 120,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.995, source, priority)


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


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON:
        for match in pattern.finditer(text):
            yield _entity(text, "PERSON", match.span("value"), "person_context_v3_8")
    for match in _MY_INN.finditer(text):
        yield _entity(text, "INN", match.span("value"), "personal_inn_v3_8")
    if _PERSONAL_CARD.search(text):
        for match in _SLASH_CARD.finditer(text):
            if _valid_luhn(match.group("value")):
                yield _entity(text, "BANK_CARD", match.span("value"), "slash_card_v3_8")
    for pattern, entity_type, source in (
        (_PASSPORT_FULL_LABEL, "PASSPORT_RF", "passport_label_v3_8"),
        (_OWN_PASSPORT, "PASSPORT_RF", "passport_owned_v3_8"),
        (_KP_DIVISION, "DIVISION_CODE", "division_label_v3_8"),
        (_LICENSE, "DRIVER_LICENSE_RF", "license_v3_8"),
        (_CVV, "CVV", "cvv_owned_v3_8"),
        (_PIN, "PIN", "pin_owned_v3_8"),
        (_CARDHOLDER, "CARDHOLDER_NAME", "cardholder_v3_8"),
    ):
        for match in pattern.finditer(text):
            yield _entity(text, entity_type, match.span("value"), source)
    for patterns, entity_type, source in (
        (_BIRTH_NUMERIC, "BIRTH_DATE", "birth_label_v3_8"),
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_v3_8"),
        ((_CITIZENSHIP,), "CITIZENSHIP", "citizenship_v3_8"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_v3_8"),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                yield _entity(text, entity_type, match.span("value"), source)
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
                elif groups.get("prefix") is not None:
                    group = "prefix"
                yield _entity(text, entity_type, match.span(group), "address_v3_8")


def _normalise_email(text: str, entity: DetectedEntity) -> DetectedEntity:
    match = _EMAIL_IN_ENTITY.search(entity.text)
    if match is None or match.span() == (0, len(entity.text)):
        return entity
    start = entity.start + match.start()
    end = entity.start + match.end()
    return DetectedEntity("EMAIL", start, end, text[start:end], 0.995, "email_boundary_v3_8", 121)


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
    personal = _PERSONAL_CUE.search(text) is not None
    hard_negative = _HARD_NON_PERSONAL.search(text) is not None
    if hard_negative and entity.entity_type in {
        "BANK_CARD",
        "CVV",
        "DIVISION_CODE",
        "PASSPORT_RF",
        "PLACE_OF_BIRTH",
    }:
        return True
    if entity.entity_type == "PHONE_RF":
        digits = re.sub(r"\D", "", entity.text)
        return digits in {"70000000000", "80000000000"} or (
            not personal and _PUBLIC_CONTACT.search(text) is not None
        )
    if entity.entity_type == "EMAIL":
        return bool(
            not personal
            and (_PUBLIC_CONTACT.search(text) or _ROLE_EMAIL.search(entity.text))
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not personal and _PUBLIC_ADDRESS.search(text) is not None
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Return v3.6 plus ownership-aware, precision-preserving v3.8 rules."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    baseline = [
        _normalise_email(text, item) if item.entity_type == "EMAIL" else item
        for item in detect_v3_6(text)
    ]
    return [
        entity
        for entity in _merge([*baseline, *_supplemental(text)])
        if not _suppressed(text, entity)
    ]
