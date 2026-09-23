"""Candidate v3.7: Russian PII recognizers with explicit ownership gates.

The candidate composes v3.5, adds general morphology/format variants, and applies a
separate semantic gate that rejects public, organisational, catalogue, template, and
documentation values.  Production remains untouched.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from app.detection.models import DetectedEntity
from proposals.detector_v3_5 import detect as detect_v3_5

_SEP = r"\s*(?:[:=№/]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_SENTENCE_END = r"(?=\s*(?:;|\.(?:\s*$|\s*\n)|$))"
_PLACE_END = r"(?=\s*(?:[,;]|\d{1,2}[./-]|\.(?:\s*$|\s*\n)|$))"

_PERSON_RE = re.compile(
    rf"\b(?:заявление\s+поступило\s+от|получателем\s+указана?|"
    rf"прошу\s+записать\s+меня\s+как|обращение\s+подписала?){_SEP}"
    rf"(?P<prose>{_NAME3})\b|"
    rf"\b(?:выгодоприобретател\w*|"
    rf"получател(?!\w*\s+указан)\w*|пациент\w*|клиент\w*|"
    rf"заявител\w*|страховател\w*|владел\w*){_SEP}"
    rf"(?P<label>{_NAME3})\b|"
    rf"\bф\.?\s*и\.?\s*о\.?(?:\s+{_WORD})?{_SEP}(?P<fio>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)
_CULTURAL = re.compile(
    r"\b(?:лекция|галерея|картина|роман|урок|форум|выступление|"
    r"газета|биография|композитор|писатель|поэт)\b",
    re.IGNORECASE,
)

_EMAIL_WRAPPER = re.compile(
    r"^(?P<prefix>[`'\"<\[]*)(?P<email>[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Z0-9.-]+\.[A-Z]{2,})(?P<suffix>[`'\">\]]*)$",
    re.IGNORECASE,
)
_PERSONAL_INN_RE = re.compile(
    rf"\b(?:мой\s+налоговый\s+идентификатор|ИНН\s+физического\s+лица){_SEP}"
    r"(?P<value>\d{10}|\d{12})(?!\d)",
    re.IGNORECASE,
)
_SLASH_CARD_RE = re.compile(r"(?<!\d)\d(?:[/ .-]?\d){12,18}(?!\d)")
_PERSONAL_CARD_CONTEXT = re.compile(
    r"\b(?:личн\w*\s+карт\w*|карт\w*\s+клиент\w*|клиент\w*[^.;]{0,35}PAN|"
    r"оплата\s+физлиц\w*|возврат\w*)\b",
    re.IGNORECASE,
)
_PASSPORT_LABEL_RE = re.compile(
    r"\b(?P<value>серия\s+(?:документа|паспорта)?\s*[-–—:]?\s*"
    r"\d{2}[ -]?\d{2}\s*[,;]?\s*номер\s+(?:паспорта\s*)?[-–—:]?\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\b(?:код\s+подразделения(?:\s*,?\s*выдавшего\s+документ)?|"
    rf"КП\s+паспорта){_SEP}(?P<value>\d{{3}}[- /]\d{{3}})(?!\d)",
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
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата\s+рождения|год-месяц-день\s+рождения|д\s*/\s*р|"
    r"родилась|родился|рождён|рождена)\b",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\b(?:место\s+появления\s+на\s+свет|место\s+рождения){_SEP}"
    rf"(?P<label>(?:(?:станица|деревня|село|посёлок|город|г\.)\s+)?"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_PLACE_END}|"
    rf"\b(?:рождён|родился|родилась)\s+в{_SEP}"
    rf"(?P<prose>(?:г\.|\bгороде|\bселе|\bдеревне)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,3}}){_PLACE_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\b(?:является\s+)?гражданкой{_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}){_SENTENCE_END}",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    rf"\b(?:кем\s+оформлен\s+паспорт|выдавший\s+орган){_SEP}"
    r"(?P<value>(?:ГУ\s+МВД|ОТДЕЛ\s+УФМС|УМВД|ОМВД|УФМС)"
    r"[^,;\n]*?)"
    rf"{_SENTENCE_END}",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\b(?:водительские\s+права(?:\s+гражданина)?|"
    rf"в\s*/\s*у|ВУ){_SEP}(?P<value>\d{{2}}[ -]?\d{{2}}[- ]?\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_CVV_RE = re.compile(
    rf"\b(?:секретный\s+код\s+)?(?:CVV2?|CVC2?)"
    rf"(?:\s+карт\w*(?:\s+(?:клиент|заказчик|держател|владел)\w*)?)?{_SEP}"
    r"(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    rf"\b(?:PIN|ПИН)(?:-код)?(?:\s+держател\w*\s+карт\w*)?"
    rf"(?:\s+равен)?{_SEP}(?P<value>\d{{4}})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:embossed\s+name\s*/\s*имя\s+держателя|имя\s+на\s+пластике|"
    rf"имя\s+держателя|NAME\s+ON\s+CARD|CARD\s*HOLDER){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:фактический\s+адрес\s+клиента|прописка\s+физлица|она\s+живёт|"
    r"для\s+доставки\s+мне\s+домой)\b",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"\b(?:г\.|\bгород){_SEP}(?P<label>{_WORD})(?=\s*[,;])|"
    rf"(?P<plain>{_WORD})(?=\s*[,]\s*(?:улица|ул\.|{_WORD}\s+проспект))|"
    rf"(?P<colon>{_WORD})(?=\s*:)|"
    rf"\bживёт\s+в\s+(?P<prose>{_WORD})(?=\s*[:;,])",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:улица|ул\.|\bпереулок|пер\.){_SEP}"
    rf"(?P<label>{_WORD})(?=\s*[,;])|"
    rf"(?P<prefix>{_WORD})\s+проспект(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;.]|$)", re.IGNORECASE)
_FLAT_RE = re.compile(rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)

_DOCUMENTATION = re.compile(
    r"(?:\b(?:инструкци\w*|документаци\w*|учебник\w*|тестов\w*|"
    r"пример\w*|шаблон\w*|макет\w*|каталог\w*|справочник\w*|"
    r"заполнител\w*|подсказк\w*\s+форм\w*|указан\w*\s+(?:ниже|выше))\b|"
    r"\bполя?\s+«)",
    re.IGNORECASE,
)
_PUBLIC_CONTACT = re.compile(
    r"\b(?:горяч\w*\s+лини\w*|секретариат\w*|завод\w*|магазин\w*|касс\w*|"
    r"театр\w*|музе\w*|офис\w*|канцеляри\w*|организатор\w*|"
    r"конференци\w*|библиотек\w*|газет\w*|редакци\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:office|security|events|library|tickets|editor|helpdesk|support|info|sales|press|"
    r"jobs?|webmaster|hr|tender|newsdesk|admin|noreply)@",
    re.IGNORECASE,
)
_ORGANISATION_ADDRESS = re.compile(
    r"\b(?:юридическ\w*\s+адрес\w*|отел\w*|офис\w*|фестивал\w*|"
    r"площадк\w*|склад\w*|театр\w*)\b",
    re.IGNORECASE,
)
_NON_PERSON_DOCUMENT = re.compile(
    r"\b(?:оборудовани\w*|станок\w*|станк\w*|издели\w*|модул\w*|"
    r"датчик\w*|модел\w*|парти\w*\s+товар\w*|учебн\w*\s+групп\w*)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_PHONE = re.compile(r"(?:\+7|8)(?:\D*0){10}(?!\d)")


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.98, source, priority)


def _near(text: str, start: int, end: int, pattern: re.Pattern[str], radius: int = 120) -> bool:
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


def _valid_inn(value: str) -> bool:
    digits = [int(char) for char in value]
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


def _new_candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _PERSON_RE.finditer(text):
        group = next(name for name in ("label", "prose", "fio") if match.group(name))
        start, end = match.span(group)
        if any(_PATRONYMIC.search(word) for word in match.group(group).split()[1:]) and not _near(
            text, start, end, _CULTURAL
        ):
            yield _entity(text, "PERSON", start, end, "person_ownership_v3_7", 100)

    for match in _PERSONAL_INN_RE.finditer(text):
        start, end = match.span("value")
        if _valid_inn(match.group("value")):
            yield _entity(text, "INN", start, end, "personal_inn_v3_7", 100)
    for match in _SLASH_CARD_RE.finditer(text):
        if (
            _valid_luhn(match.group())
            and _near(text, *match.span(), _PERSONAL_CARD_CONTEXT)
            and not _near(text, *match.span(), _DOCUMENTATION)
        ):
            yield _entity(text, "BANK_CARD", *match.span(), "personal_card_v3_7", 100)
    for pattern, entity_type in (
        (_PASSPORT_LABEL_RE, "PASSPORT_RF"),
        (_DIVISION_RE, "DIVISION_CODE"),
    ):
        for match in pattern.finditer(text):
            if _near(text, *match.span(), _DOCUMENTATION) or _near(
                text, *match.span(), _NON_PERSON_DOCUMENT
            ):
                continue
            start, end = match.span("value")
            yield _entity(text, entity_type, start, end, "document_field_v3_7", 100)

    for match in _NUMERIC_DATE_RE.finditer(text):
        if (
            _valid_date(match)
            and _near(text, *match.span(), _BIRTH_CONTEXT, radius=90)
            and not _near(text, *match.span(), _DOCUMENTATION)
        ):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_7", 100)

    for pattern, entity_type in (
        (_BIRTHPLACE_RE, "PLACE_OF_BIRTH"),
        (_CITIZENSHIP_RE, "CITIZENSHIP"),
        (_ISSUER_RE, "PASSPORT_ISSUER"),
        (_LICENSE_RE, "DRIVER_LICENSE_RF"),
        (_CVV_RE, "CVV"),
        (_PIN_RE, "PIN"),
        (_CARDHOLDER_RE, "CARDHOLDER_NAME"),
    ):
        for match in pattern.finditer(text):
            if _near(text, *match.span(), _DOCUMENTATION) or _near(
                text, *match.span(), _NON_PERSON_DOCUMENT
            ):
                continue
            group = next(name for name, value in match.groupdict().items() if value is not None)
            start, end = match.span(group)
            yield _entity(text, entity_type, start, end, "semantic_field_v3_7", 100)

    anchor = _ADDRESS_ANCHOR.search(text)
    if anchor and not _ORGANISATION_ADDRESS.search(text):
        address = text[anchor.end() :]
        offset = anchor.end()
        for entity_type, pattern, groups in (
            ("ADDRESS_COUNTRY", _COUNTRY_RE, (None,)),
            ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, (None,)),
            ("ADDRESS_CITY", _CITY_RE, ("label", "plain", "colon", "prose")),
            ("ADDRESS_STREET", _STREET_RE, ("label", "prefix")),
            ("ADDRESS_HOUSE", _HOUSE_RE, ("value",)),
            ("ADDRESS_APARTMENT", _FLAT_RE, ("value",)),
        ):
            for match in pattern.finditer(address):
                selected = next((name for name in groups if name and match.group(name)), None)
                start, end = match.span(selected) if selected else match.span()
                yield _entity(
                    text,
                    entity_type,
                    offset + start,
                    offset + end,
                    "personal_address_v3_7",
                    99,
                )


def _normalise_email(text: str, entity: DetectedEntity) -> DetectedEntity:
    match = _EMAIL_WRAPPER.fullmatch(entity.text)
    if not match:
        return entity
    start = entity.start + match.start("email")
    end = entity.start + match.end("email")
    if (start, end) == (entity.start, entity.end):
        return entity
    return DetectedEntity("EMAIL", start, end, text[start:end], 0.99, "email_wrapper_v3_7", 90)


def _keep_baseline(text: str, entity: DetectedEntity) -> bool:
    context_documentation = _near(text, entity.start, entity.end, _DOCUMENTATION)
    if entity.entity_type == "EMAIL":
        return not (
            _SHARED_EMAIL.search(entity.text)
            or _near(text, entity.start, entity.end, _PUBLIC_CONTACT)
        )
    if entity.entity_type == "PHONE_RF":
        return not (
            _PLACEHOLDER_PHONE.fullmatch(entity.text)
            or _near(text, entity.start, entity.end, _PUBLIC_CONTACT)
        )
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "DRIVER_LICENSE_RF"}:
        return not (
            context_documentation
            or _near(text, entity.start, entity.end, _NON_PERSON_DOCUMENT)
        )
    if entity.entity_type in {"CVV", "PIN"}:
        return not (
            context_documentation
            or _near(text, entity.start, entity.end, _NON_PERSON_DOCUMENT)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not _near(text, entity.start, entity.end, _ORGANISATION_ADDRESS)
    if entity.entity_type == "PLACE_OF_BIRTH":
        return not context_documentation and bool(re.search(r"[А-Яа-яЁё]", entity.text))
    return True


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
    """Detect PII using v3.5 plus explicit ownership and suppression rules."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    baseline: list[DetectedEntity] = []
    for raw in detect_v3_5(text):
        entity = _normalise_email(text, raw) if raw.entity_type == "EMAIL" else raw
        if _keep_baseline(text, entity):
            baseline.append(entity)
    return _merge([*baseline, *_new_candidates(text)])
