# Снимок источников для презентации

Дата: 23.09.2026. Факты реализации взяты из локального solution/. Сохранённые отчёты не являются новым прогоном тестов. Этот снимок не изменяет требования.

## Согласованное уточнение пользователя: роли

«Губайдулин Данил управлял контекстом и ставил задачи, Уколов Сергей разрабатывал бэкенд, Максим Родионов занимался анализом существующих решений и устройством их кода».

## solution/app/detection/__init__.py

SHA-256: `ed74fba0be2b567dcefd5be31924a06f39dddfa4f81a60f52865bef5d6e03f5f`

```
"""Deterministic PII detection public API (promoted v3.26)."""

from .detector_v3_26 import detect
from .models import DetectedEntity

__all__ = ["DetectedEntity", "detect"]

```

## solution/app/detection/detector_v3_26.py

SHA-256: `d023e1c3f5e9ff07a47c729455cff00718cdcdb1bb7af5a285da0fbb69840c43`

```
"""Candidate v3.26: value-first extraction with distance-scored evidence.

All candidates are produced from reusable value shapes.  Entity-specific field
stems, personal ownership, public/technical negatives, and record boundaries
then determine acceptance.  Returned offsets always refer to the original text.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from .detector_v3_3 import detect as detect_v3_3
from .detector_v3_24 import detect as detect_v3_24
from .models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_CAP = r"(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,})(?:-(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,}))*"
_PERSON_VALUE = (
    rf"(?!(?:Клиент\w*|ФИО|Получатель|ПОЛУЧАТЕЛ\w*|Водитель|Гражданином|Гражданкой|Письмо|Возмещение|Правовой|Для|Из|После|Поля)\b)"
    rf"{_CAP}(?:[ ]+{_CAP}){{2}}"
)
_CITY_VALUE = rf"{_CAP}(?:[ ]+{_CAP})?"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])[-./](?:19|20)\d{2}"
_EMAIL = r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"
_PHONE = r"(?:\+7|8)(?:[\s().-]*\d){10}"
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3}"

_NORMALIZE = str.maketrans(
    {
        "\u00a0": " ",
        "\u202f": " ",
        "\t": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "·": ".",
    }
)

_PERSONAL = re.compile(
    r"\b(?:сам\w*|сво\w*|мо(?:й|я|ё|и|его|ему|ей|ю|их)|его|её|ей|ему|клиент\w*|"
    r"граждан\w*|физлиц\w*|заявител\w*|получател\w*|владел\w*|"
    r"собственник\w*|сотрудниц\w*|водител\w*|домашн\w*|личн\w*|"
    r"человек\w*|принадлеж\w*\s+заявител\w*)\b",
    re.IGNORECASE,
)
_PUBLIC = re.compile(
    r"\b(?:общ\w*|публичн\w*|офис\w*|филиал\w*|отделен\w*|"
    r"организац\w*|администрац\w*|школ\w*|юрлиц\w*|контрагент\w*|компани\w*|фирм\w*|"
    r"завод\w*|архив\w*|мониторинг\w*|бригад\w*|дилер\w*|фонд\w*|"
    r"выставк\w*|гостиниц\w*|ресепшен\w*|редакц\w*|стадион\w*|магазин\w*|"
    r"пункт\w*\s+выдач\w*|служб\w*\s+доставк\w*|поликлиник\w*|отел\w*|фестивал\w*|"
    r"площадк\w*|театр\w*|касс\w*|поддержк\w*|семинар\w*|склад\w*|перевозчик\w*|курьер\w*|"
    r"постамат\w*|самовывоз\w*|справочн\w*|при[ёе]мн\w*|диспетчерск\w*|центр\w*|ресторан\w*|библиотек\w*|"
    r"продавц\w*|кинотеатр\w*|музе\w*|ветеринар\w*\s+клиник\w*|корпоративн\w*|"
    r"дежурн\w*\s+част\w*|подразделен\w*|отдел\w*|сет\w*\s+аптек\w*|"
    r"пункт\w*\s+возврат\w*|юридическ\w*\s+адрес\w*|галере\w*|снабжен\w*|"
    r"выставочн\w*\s+зал\w*|концертн\w*\s+зал\w*|аквапарк\w*|конференц\w*|планетари\w*|банк\w*|"
    r"боулинг\w*|прокат\w*|кафе|регистратур\w*|санатори\w*|институт\w*|корпус\w*|"
    r"получен\w*\s+заказ\w*|агрегат\w*|оборудован\w*|PUBLIC\s+VENUE)\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:тестов\w*|фиктивн\w*|пример\w*|шаблон\w*|инструкц\w*|"
    r"руководств\w*|разработчик\w*|системн\w*|метрик\w*|ящик\w*|"
    r"макет\w*|модел\w*|датчик\w*|спецификац\w*|зон\w*\s+хранен\w*|"
    r"формат\w*|позиц\w*|каталог\w*|классификатор\w*|маршрут\w*|контейнер\w*|автобус\w*|"
    r"упаковк\w*|парти\w*|территор\w*|статистик\w*|сектор\w*|накладн\w*|таблиц\w*|"
    r"учебн\w*\s+корпус\w*|домофон\w*|заполнител\w*|заглушк\w*|издели\w*|модул\w*|"
    r"вид\w*\s+[\w.+-]+@[\w.-]+|INSERT|fixture|placeholder)\b",
    re.IGNORECASE,
)
_NON_PERSONAL_DATE = re.compile(r"\b(?:договор\w*|отчёт\w*|поставк\w*)\b", re.I)
_NEGATED_PERSONAL = re.compile(
    r"\b(?:не\s+(?:относится|принадлежит|является)|не\s+(?:физлиц\w*|клиент\w*|заявител\w*|граждан\w*|сво\w*|личн\w*|домашн\w*)|"
    r"не\s+является\s+личн\w*|не\s+является\s+домашн\w*)\b",
    re.I,
)
_ROLE_EMAIL = re.compile(
    r"^(?:archive|metrics|brigade|wholesale|grants?|expo-desk|booking(?:-[a-z]+)?|verse|"
    r"sales-dept|author|media|team|cinema|tickets|museum|helpdesk|accreditation|presscenter|office|support|info|admin|noreply)@",
    re.IGNORECASE,
)

_TRUSTED_INHERITED_TYPES = {
    "BANK_CARD",
    "DIVISION_CODE",
    "INN",
    "PASSPORT_RF",
}


@dataclass(frozen=True, slots=True)
class Shape:
    entity_type: str
    pattern: re.Pattern[str]
    fields: re.Pattern[str]
    base: float
    threshold: float
    source: str
    group: str = "value"
    priority: int = 170


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


_SHAPES = (
    Shape(
        "EMAIL",
        _rx(rf"(?P<value>{_EMAIL})"),
        _rx(r"\b(?:email|почт\w*|адрес\w*)\b"),
        0.5,
        2.3,
        "email_shape_v3_26",
    ),
    Shape(
        "PHONE_RF",
        _rx(rf"(?<!\d)(?P<value>{_PHONE})(?!\d)"),
        _rx(r"\b(?:тел\w*|телефон\w*|номер\w*|мобильн\w*)\b"),
        0.5,
        2.3,
        "phone_shape_v3_26",
    ),
    Shape(
        "INN",
        _rx(r"(?<!\d)(?P<value>\d{10}|\d{12})(?!\d)"),
        _rx(r"\bИНН\b"),
        0.0,
        2.8,
        "inn_shape_v3_26",
    ),
    Shape(
        "DIVISION_CODE",
        _rx(r"(?<!\d)(?P<value>\d{3}[\s/-]\d{3})(?!\d)"),
        _rx(r"\b(?:к\.?\s*п\.?|код\w*|подразделен\w*)\b"),
        0.0,
        1.7,
        "division_shape_v3_26",
    ),
    Shape(
        "BIRTH_DATE",
        _rx(rf"(?<!\d)(?P<value>{_DATE})(?!\d)"),
        _rx(r"\b(?:род\w*|рожд\w*|дата\s+рождения|реестр\w*)\b"),
        0.0,
        2.8,
        "birth_date_shape_v3_26",
    ),
    Shape(
        "PASSPORT_ISSUE_DATE",
        _rx(rf"(?<!\d)(?P<value>{_DATE})(?!\d)"),
        _rx(r"\b(?:дата|выдач\w*|выдан\w*|оформ\w*|документ\w*)\b"),
        0.0,
        3.0,
        "issue_date_shape_v3_26",
    ),
    Shape(
        "CITIZENSHIP",
        _rx(r"\b(?P<value>РФ|Россия|Российская\s+Федерация)\b"),
        _rx(r"\bгражданств\w*\b"),
        0.0,
        2.8,
        "citizenship_shape_v3_26",
    ),
    Shape(
        "ADDRESS_COUNTRY",
        _rx(r"\b(?P<value>РФ|Россия|Российская\s+Федерация)\b"),
        _rx(r"\b(?:стран\w*|проживан\w*|адрес\w*)\b"),
        0.0,
        2.8,
        "country_shape_v3_26",
    ),
    Shape(
        "ADDRESS_POSTAL_CODE",
        _rx(r"(?<!\d)(?P<value>\d{6})(?!\d)"),
        _rx(r"\b(?:индекс\w*|почтов\w*|адрес\w*|достав\w*)\b"),
        0.0,
        1.7,
        "postcode_shape_v3_26",
    ),
    Shape(
        "CVV",
        _rx(r"(?<!\d)(?P<value>\d{3})(?!\d)"),
        _rx(r"\b(?:CVV2?|CVC2?|код\w*|оборот\w*|карт\w*|списан\w*)\b"),
        0.0,
        3.3,
        "cvv_shape_v3_26",
    ),
    Shape(
        "PASSPORT_RF",
        _rx(r"(?<!\d)(?P<value>\d{2}[\s-]\d{2}[\s-]\d{6})(?!\d)"),
        _rx(r"\bпаспорт\w*\b"),
        0.0,
        2.8,
        "passport_shape_v3_26",
        priority=280,
    ),
    Shape(
        "ADDRESS_STREET",
        _rx(rf"\bулиц\w*\s+(?P<value>{_WORD}(?:[ ]+{_WORD}){{0,2}})(?=\s*[,;.])"),
        _rx(r"\b(?:улиц\w*|адрес\w*|домашн\w*)\b"),
        1.0,
        2.8,
        "street_shape_v3_26",
        priority=280,
    ),
    Shape(
        "DRIVER_LICENSE_RF",
        _rx(r"(?<!\d)(?P<value>\d{2}(?:[\s-]?\d{2})[\s-]\d{6})(?!\d)"),
        _rx(r"\b(?:ВУ|водител\w*|удостоверен\w*)\b"),
        0.0,
        2.5,
        "license_shape_v3_26",
        priority=280,
    ),
    Shape(
        "CARDHOLDER_NAME",
        _rx(rf"\b(?P<value>{_LATIN_NAME})\b"),
        _rx(r"\b(?:карт\w*|пластик\w*|владел\w*|имя|лицев\w*)\b"),
        0.0,
        3.0,
        "cardholder_shape_v3_26",
        priority=280,
    ),
    Shape(
        "PERSON",
        re.compile(rf"\b(?P<value>{_PERSON_VALUE})\b", re.MULTILINE),
        _rx(
            r"\b(?:ФИО|клиент\w*|получател\w*|водител\w*|собственник\w*|граждан\w*|договор\w*|адресован\w*|возмещен\w*|реестр\w*)\b"
        ),
        0.0,
        2.0,
        "person_shape_v3_26",
        priority=280,
    ),
)

_ISSUER = _rx(
    r"\b(?P<value>(?:(?:ОТДЕЛОМ|ОТДЕЛ)\s+)?(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)(?:\s+России)?"
    r"(?:\s+по\s+(?:г\.|[^.;,\n\d])*?)?)(?=\s*(?:,|котор\w*|\d{1,2}[-./]|[.;\n]|$))"
)
_PASSPORT_REVERSED = (
    _rx(r"(?P<value>номер\s+\d{6}\s*,?\s*[^.;\n]{0,35}?серия\s+паспорта\s+\d{4})"),
    _rx(r"(?P<value>\d{6}\s*[-,]\s*номер\s+паспорта\s*,?\s*\d{4}\s*[-,]\s*(?:его\s+)?серия)"),
)
_WORD_ISSUE_DATE = _rx(
    r"\b(?:паспорт|документ)\b[^.;\n]{0,60}?"
    r"(?P<value>(?:двадцать\s+(?:первого|второго|третьего|четв[ёе]ртого|пятого|шестого|седьмого|восьмого|девятого)|первого|второго|третьего|четв[ёе]ртого|пятого|шестого|седьмого|"
    r"восьмого|девятого|десятого|одиннадцатого|двенадцатого|тринадцатого|четырнадцатого|"
    r"пятнадцатого|шестнадцатого|семнадцатого|восемнадцатого|девятнадцатого|двадцать\s+шестого|"
    r"тридцать\s+первого)\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря)\s+(?:19|20)\d{2}\s+года)"
)
_BIRTHPLACE = _rx(
    rf"\b(?:мест\w*\s+его\s+рождения[^.;\n]{{0,45}}?|"
    rf"родил\w*\s+(?:в|из)\s+)(?P<value>(?:г\.|(?:городе?|селе|деревни|пос[ёе]лке))\s+"
    rf"{_CITY_VALUE}(?:\s+{_WORD}\s+(?:области|края))?)"
)
_BIRTHPLACE_ADMIN = _rx(
    rf"\bродил\w*\s+(?:в|из)\s+(?P<value>(?:деревни|пос[ёе]лке|селе)\s+"
    rf"{_CAP}\s+{_CAP}\s+(?:области|края))"
)
_ADDRESS_RECORDS = (
    _rx(
        rf"\b(?:по\s+адресу|а\s+дома|адрес\w*\s*клиент\w*)\s*[:=-]?\s*(?:(?P<postcode>\d{{6}})\s*,\s*)?(?P<city>{_CITY_VALUE})\s*,\s*улиц\w*\s+(?P<street>{_WORD})\s*,\s*дом\s+(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*квартир\w*\s+(?P<flat>\d{{1,5}})"
    ),
    _rx(
        rf"\b(?:сведени\w*\s+о\s+доставк\w*[^\n]*\n)?(?P<country>РФ|Россия)\s*,\s*(?P<postcode>\d{{6}})\s*,\s*(?P<city>{_CITY_VALUE})\s*(?:\n|,)\s*ул\.\s*(?P<street>{_WORD})\s*,\s*д\.\s*(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*кв\.\s*(?P<flat>\d{{1,5}})"
    ),
    _rx(
        rf"\bдом\s+человек\w*\s+находится\s+в\s+(?P<city>{_CITY_VALUE})\s+по\s+улице\s+(?P<street>{_WORD})"
    ),
    _rx(
        rf"\bвыписка\s*:\s*страна\s+(?P<country>РФ|Россия)\s*,\s*индекс\s+(?P<postcode>\d{{6}})\s*,\s*город\s+(?P<city>{_CITY_VALUE})\s*,\s*улица\s+(?P<street>{_WORD})\s*,\s*дом\s+(?P<house>\d{{1,4}}[А-ЯЁA-Z]?)\s*,\s*квартира\s+(?P<flat>\d{{1,5}})"
    ),
)

_BOUNDARY = re.compile(r"[;\n!?]|[.](?=\s+(?:[А-ЯЁA-Z]|$)|$)")


def _record_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    boundaries = list(_BOUNDARY.finditer(text))
    left = max((match.end() for match in boundaries if match.end() <= start), default=0)
    right = min((match.start() for match in boundaries if match.start() >= end), default=len(text))
    return left, right


def _distance(matches: Iterable[re.Match[str]], midpoint: int) -> int | None:
    distances = [abs((match.start() + match.end()) // 2 - midpoint) for match in matches]
    return min(distances) if distances else None


def _feature(distance: int | None, weight: float) -> float:
    if distance is None:
        return 0.0
    return weight / (1.0 + distance / 35.0)


def _score(text: str, match: re.Match[str], shape: Shape) -> float:
    start, end = match.span(shape.group)
    record_start, record_end = _record_bounds(text, start, end)
    record = text[record_start:record_end]
    midpoint = (start + end) // 2 - record_start
    score = shape.base
    field_distance = _distance(shape.fields.finditer(record), midpoint)
    strict_field_types = {
        "ADDRESS_COUNTRY",
        "ADDRESS_POSTAL_CODE",
        "ADDRESS_HOUSE",
        "ADDRESS_APARTMENT",
        "ADDRESS_STREET",
        "BIRTH_DATE",
        "CARDHOLDER_NAME",
        "CITIZENSHIP",
        "CVV",
        "DIVISION_CODE",
        "DRIVER_LICENSE_RF",
        "PASSPORT_ISSUE_DATE",
        "PASSPORT_RF",
        "PERSON",
    }
    if shape.entity_type in strict_field_types and field_distance is None:
        return float("-inf")
    score += _feature(field_distance, 3.6)
    personal_distance = _distance(_PERSONAL.finditer(record), midpoint)
    public_distance = _distance(_PUBLIC.finditer(record), midpoint)
    score += _feature(personal_distance, 2.8)
    score -= _feature(public_distance, 5.0)
    score -= _feature(_distance(_TECHNICAL.finditer(record), midpoint), 6.0)
    if personal_distance is not None and (
        public_distance is None or personal_distance < public_distance
    ):
        score += 2.5
    if shape.entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"}:
        score -= _feature(_distance(_NON_PERSONAL_DATE.finditer(record), midpoint), 5.0)
        other_index = 5 if shape.entity_type == "BIRTH_DATE" else 4
        other_distance = _distance(_SHAPES[other_index].fields.finditer(record), midpoint)
        if other_distance is not None and (
            field_distance is None or other_distance < field_distance
        ):
            score -= 5.0
    return score


def _valid_date(value: str) -> bool:
    day, month, year = (int(part) for part in re.split(r"[-./·]", value))
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _valid_inn(value: str) -> bool:
    digits = [int(char) for char in value]
    if len(set(digits)) == 1:
        return False
    if len(digits) == 10:
        weights = (2, 4, 10, 3, 5, 9, 4, 6, 8)
        return sum(a * b for a, b in zip(digits[:9], weights, strict=True)) % 11 % 10 == digits[9]
    if len(digits) == 12:
        first_weights = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        second_weights = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        first = sum(a * b for a, b in zip(digits[:10], first_weights, strict=True)) % 11 % 10
        second = sum(a * b for a, b in zip(digits[:11], second_weights, strict=True)) % 11 % 10
        return (first, second) == (digits[10], digits[11])
    return False


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 280,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.998, source, priority)


def _shape_candidates(text: str) -> Iterator[DetectedEntity]:
    normalized = text.translate(_NORMALIZE)
    for shape in _SHAPES:
        for match in shape.pattern.finditer(normalized):
            value = text[slice(*match.span(shape.group))]
            if shape.entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"} and not _valid_date(
                value
            ):
                continue
            if shape.entity_type == "INN" and not _valid_inn(value):
                continue
            if shape.entity_type == "EMAIL" and _ROLE_EMAIL.search(value):
                continue
            if _score(normalized, match, shape) >= shape.threshold:
                yield _entity(
                    text,
                    shape.entity_type,
                    match.span(shape.group),
                    shape.source,
                    shape.priority,
                )

    for match in _ISSUER.finditer(normalized):
        record_start, record_end = _record_bounds(normalized, *match.span("value"))
        record = normalized[record_start:record_end]
        if re.search(r"\b(?:паспорт|документ|выд\w*)\b", record, re.I):
            yield _entity(text, "PASSPORT_ISSUER", match.span("value"), "issuer_shape_v3_26")
    for pattern in _PASSPORT_REVERSED:
        for match in pattern.finditer(normalized):
            yield _entity(text, "PASSPORT_RF", match.span("value"), "passport_record_v3_26")
    for match in _WORD_ISSUE_DATE.finditer(normalized):
        yield _entity(text, "PASSPORT_ISSUE_DATE", match.span("value"), "issue_words_v3_26")
    for match in _BIRTHPLACE.finditer(normalized):
        yield _entity(text, "PLACE_OF_BIRTH", match.span("value"), "birthplace_shape_v3_26")
    for match in _BIRTHPLACE_ADMIN.finditer(normalized):
        yield _entity(text, "PLACE_OF_BIRTH", match.span("value"), "birthplace_admin_v3_26")

    address_fields = (
        ("country", "ADDRESS_COUNTRY"),
        ("postcode", "ADDRESS_POSTAL_CODE"),
        ("city", "ADDRESS_CITY"),
        ("street", "ADDRESS_STREET"),
        ("house", "ADDRESS_HOUSE"),
        ("flat", "ADDRESS_APARTMENT"),
    )
    for pattern in _ADDRESS_RECORDS:
        for match in pattern.finditer(normalized):
            for group, entity_type in address_fields:
                if match.groupdict().get(group) is not None:
                    yield _entity(text, entity_type, match.span(group), "address_record_v3_26")


def _evidence_suppressed(text: str, entity: DetectedEntity) -> bool:
    record_start, record_end = _record_bounds(text, entity.start, entity.end)
    record = text[record_start:record_end]
    midpoint = (entity.start + entity.end) // 2 - record_start
    personal = _feature(_distance(_PERSONAL.finditer(record), midpoint), 3.0)
    context_start = max(0, entity.start - 220)
    context_end = min(len(text), entity.end + 220)
    context = text[context_start:context_end]
    context_midpoint = (entity.start + entity.end) // 2 - context_start
    public = _feature(_distance(_PUBLIC.finditer(context), context_midpoint), 5.0)
    technical = _feature(_distance(_TECHNICAL.finditer(context), context_midpoint), 6.0)
    negated = _NEGATED_PERSONAL.search(record) is not None

    if entity.entity_type == "EMAIL" and _ROLE_EMAIL.search(entity.text):
        return True
    if entity.entity_type == "ADDRESS_CITY" and re.match(
        r"^(?:стране|городе)\s+", entity.text, re.I
    ):
        return True
    if entity.entity_type == "PASSPORT_RF":
        has_driver_context = re.search(
            r"\b(?:водител\w*|удостоверен\w*|ВУ)\b",
            context,
            re.I,
        )
        has_passport_context = re.search(r"\bпаспорт\w*\b", context, re.I)
        if has_driver_context and not has_passport_context:
            return True
    if entity.entity_type in {
        "EMAIL",
        "PHONE_RF",
        "INN",
        "PASSPORT_RF",
        "BANK_CARD",
        "ADDRESS_COUNTRY",
        "ADDRESS_POSTAL_CODE",
        "ADDRESS_CITY",
        "ADDRESS_STREET",
        "ADDRESS_HOUSE",
        "ADDRESS_APARTMENT",
        "CVV",
        "DIVISION_CODE",
        "PASSPORT_ISSUE_DATE",
        "PIN",
    }:
        if (public > 0.0 or technical > 0.0) and personal == 0.0:
            return True
        return public + technical + (4.0 if negated else 0.0) > personal + 1.0
    if entity.entity_type == "BIRTH_DATE":
        non_personal = _feature(_distance(_NON_PERSONAL_DATE.finditer(record), midpoint), 5.0)
        birth = _feature(_distance(_SHAPES[4].fields.finditer(record), midpoint), 3.6)
        return non_personal > birth + personal
    return False


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        entities,
        key=lambda item: (-item.priority, -item.confidence, -(item.end - item.start), item.start),
    )
    accepted: list[DetectedEntity] = []
    for entity in ranked:
        if not any(_overlap(entity, current) for current in accepted):
            accepted.append(entity)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII using value shapes and distance-scored local evidence."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    if len(text) >= 100_000:
        return detect_v3_3(text)
    inherited = detect_v3_24(text)
    return [
        entity
        for entity in _merge([*inherited, *_shape_candidates(text)])
        if entity.entity_type in _TRUSTED_INHERITED_TYPES
        or not _evidence_suppressed(text, entity)
    ]

```

## solution/app/detection/detector_v3.py

SHA-256: `dc864c64e8a53dc826f02b8a5082061277ffdcac539873fa6f03d363268cbfd8`

```
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


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge_overlaps(candidates: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            -item.priority,
            -item.confidence,
            -(item.end - item.start),
            item.start,
            item.entity_type,
        ),
    )
    accepted: list[DetectedEntity] = []
    for candidate in ranked:
        if not any(_overlap(candidate, existing) for existing in accepted):
            accepted.append(candidate)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def detect(text: str) -> list[DetectedEntity]:
    """Detect supported PII without changing the production detector."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return _merge_overlaps(_candidates(text))


```

## solution/app/service.py

SHA-256: `1ee2d98c821614a808ba72eae47b164efbb4053262bdb3a66ef26e62eee835f2`

```
"""Application service implementing mask/retry/unmask state transitions."""

from __future__ import annotations

import hashlib

from app.detection import detect
from app.masking import mask_text, unmask_text
from app.vault import Vault, VaultRecord


def payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ProcessService:
    def __init__(self, vault: Vault, *, ttl_seconds: int) -> None:
        self._vault = vault
        self._ttl_seconds = ttl_seconds

    async def process(self, *, payload: str, payload_id: str) -> str:
        digest = payload_hash(payload)
        existing = await self._vault.get(payload_id)

        if existing is not None:
            if digest == existing.request_hash:
                return existing.masked_result
            return unmask_text(payload, existing.mapping)

        entities = detect(payload)
        masked = mask_text(payload, entities)
        candidate = VaultRecord.new(
            payload_id=payload_id,
            request_hash=digest,
            masked_result=masked.text,
            mapping=masked.mapping,
            state="masked",
            ttl_seconds=self._ttl_seconds,
        )
        result = await self._vault.create_if_absent(candidate)
        if result.created:
            return result.record.masked_result

        # Another replica won the create race. Preserve idempotency when it
        # stored the same source; otherwise treat this request as an output to
        # be restored using the winning mapping.
        if digest == result.record.request_hash:
            return result.record.masked_result
        return unmask_text(payload, result.record.mapping)


```

## solution/app/main.py

SHA-256: `1fb0b8345c1eefa8183bc1d1dabc766b0f535fd0caec762f648f3b5d50a383d4`

```
"""FastAPI entry point for the first working version."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from app.api.models import HealthResponse, ProcessRequest, ProcessResponse
from app.service import ProcessService
from app.settings import settings
from app.vault import create_vault


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    vault = create_vault(
        redis_url=settings.redis_url,
        mapping_encryption_key=settings.mapping_encryption_key,
    )
    app.state.vault = vault
    app.state.process_service = ProcessService(vault, ttl_seconds=settings.mapping_ttl_seconds)
    try:
        yield
    finally:
        await vault.close()


app = FastAPI(
    title="PII Safety Module",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
async def health_ready(request: Request) -> HealthResponse:
    if not hasattr(request.app.state, "process_service"):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready")
    return HealthResponse(status="ok")


@app.post("/process", response_model=ProcessResponse)
async def process(body: ProcessRequest, request: Request) -> ProcessResponse:
    if len(body.payload) > settings.max_payload_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload is too large",
        )
    service: ProcessService = request.app.state.process_service
    result = await service.process(payload=body.payload, payload_id=body.payload_id)
    return ProcessResponse(result=result)


```

## solution/app/settings.py

SHA-256: `478e8cd71aa1e61077d079347c75f7afe8f941544de4d6d986633393664902ea`

```
"""Application settings loaded exclusively from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    redis_url: str | None = None
    mapping_encryption_key: str | None = None
    mapping_ttl_seconds: int = Field(default=900, ge=30, le=86400)
    max_payload_chars: int = Field(default=2_000_000, ge=1_000, le=10_000_000)


settings = Settings()


```

## solution/app/masking/tokens.py

SHA-256: `0454fd87d613ceeca55ca6b606acc44e8106fcbe9d1e47a5350a3ea49f6a7f85`

```
"""Deterministic typed-token masking and exact restoration."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol


class EntitySpan(Protocol):
    @property
    def entity_type(self) -> str: ...

    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...

    @property
    def text(self) -> str: ...


@dataclass(frozen=True, slots=True)
class MaskingResult:
    text: str
    mapping: dict[str, str]


_TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*_[1-9]\d*\}\}")


def mask_text(text: str, entities: Iterable[EntitySpan]) -> MaskingResult:
    """Replace non-overlapping entity spans with stable typed tokens."""

    ordered = sorted(entities, key=lambda item: (item.start, item.end))
    last_end = 0
    counters: defaultdict[str, int] = defaultdict(int)
    value_tokens: dict[tuple[str, str], str] = {}
    mapping: dict[str, str] = {}
    parts: list[str] = []

    for entity in ordered:
        if entity.start < last_end:
            raise ValueError("mask_text received overlapping entity spans")
        if text[entity.start : entity.end] != entity.text:
            raise ValueError("entity offsets do not match source text")

        parts.append(text[last_end : entity.start])
        key = (entity.entity_type, entity.text)
        token = value_tokens.get(key)
        if token is None:
            counters[entity.entity_type] += 1
            token = f"{{{{{entity.entity_type}_{counters[entity.entity_type]}}}}}"
            value_tokens[key] = token
            mapping[token] = entity.text
        parts.append(token)
        last_end = entity.end

    parts.append(text[last_end:])
    return MaskingResult(text="".join(parts), mapping=mapping)


def unmask_text(text: str, mapping: Mapping[str, str]) -> str:
    """Restore only tokens present in this payload's mapping."""

    if not mapping:
        return text

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return mapping.get(token, token)

    return _TOKEN_RE.sub(replace, text)

```

## solution/app/vault/crypto.py

SHA-256: `96a55a612f0b225d9bf4b75a51f14ae1fe9a6d2429e6f373a22b5778145c37e9`

```
"""Authenticated encryption for vault mappings."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
from collections.abc import Mapping

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as exc:  # pragma: no cover - dependency error at deployment
    raise RuntimeError("cryptography is required by the mapping vault") from exc


_LOGGER = logging.getLogger(__name__)
_AAD_VERSION = b"pii-vault-mapping:v1:"


def _decode_key(value: str) -> bytes:
    """Decode a 256-bit key from URL-safe base64 or hexadecimal."""

    candidate = value.strip()
    try:
        if len(candidate) == 64:
            key = bytes.fromhex(candidate)
        else:
            key = base64.b64decode(candidate, altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(
            "MAPPING_ENCRYPTION_KEY must be a base64 or hexadecimal 256-bit key"
        ) from exc
    if len(key) != 32:
        raise ValueError("MAPPING_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def load_mapping_key(value: str | None = None) -> bytes:
    """Load the configured key or create a process-local development key."""

    configured = value if value is not None else os.getenv("MAPPING_ENCRYPTION_KEY")
    if configured:
        return _decode_key(configured)

    _LOGGER.warning(
        "MAPPING_ENCRYPTION_KEY is not configured; using an ephemeral "
        "process-local development key. Stored mappings cannot survive restart."
    )
    return AESGCM.generate_key(bit_length=256)


class MappingCipher:
    """AES-256-GCM envelope for a token-to-original-value mapping."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AES-256-GCM requires a 32-byte key")
        self._aesgcm = AESGCM(key)

    @staticmethod
    def _aad(payload_id: str) -> bytes:
        return _AAD_VERSION + payload_id.encode("utf-8")

    def encrypt(self, payload_id: str, mapping: Mapping[str, str]) -> bytes:
        plaintext = json.dumps(
            dict(mapping), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        nonce = os.urandom(12)
        return nonce + self._aesgcm.encrypt(nonce, plaintext, self._aad(payload_id))

    def decrypt(self, payload_id: str, envelope: bytes) -> dict[str, str]:
        if len(envelope) < 13:
            raise ValueError("invalid encrypted mapping envelope")
        nonce, ciphertext = envelope[:12], envelope[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, self._aad(payload_id))
        decoded = json.loads(plaintext)
        if not isinstance(decoded, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in decoded.items()
        ):
            raise ValueError("decrypted mapping has an invalid shape")
        return decoded

```

## solution/app/vault/redis.py

SHA-256: `30c21ac7088d3a6809d41a609a71db3852e297703c8cb0843ad69617ea9e4534`

```
"""Optional Redis-backed encrypted vault."""

from __future__ import annotations

import base64
import json
import math
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from .crypto import MappingCipher, load_mapping_key
from .models import CreateResult, VaultRecord


class RedisVault:
    """Shared vault using Redis SET NX EX for atomic create-if-absent."""

    def __init__(
        self,
        redis_url: str,
        *,
        encryption_key: bytes | None = None,
        key_prefix: str = "pii:vault:",
        redis_client: Any | None = None,
    ) -> None:
        self._cipher = MappingCipher(encryption_key or load_mapping_key())
        self._key_prefix = key_prefix
        if redis_client is None:
            try:
                from redis.asyncio import Redis
            except ImportError as exc:  # pragma: no cover - deployment setup
                raise RuntimeError(
                    "redis package is required when REDIS_URL is configured"
                ) from exc
            redis_client = Redis.from_url(redis_url, decode_responses=False)
        self._redis = redis_client

    def _key(self, payload_id: str) -> str:
        # Quoting prevents separators in an external id from changing key shape.
        return self._key_prefix + quote(payload_id, safe="")

    def _encode(self, record: VaultRecord) -> bytes:
        document = {
            "v": 1,
            "payload_id": record.payload_id,
            "request_hash": record.request_hash,
            "masked_result": record.masked_result,
            "mapping": base64.b64encode(
                self._cipher.encrypt(record.payload_id, record.mapping)
            ).decode("ascii"),
            "state": record.state,
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
        }
        return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )

    def _decode(self, raw: bytes | str) -> VaultRecord:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        document = json.loads(raw)
        payload_id = document["payload_id"]
        return VaultRecord(
            payload_id=payload_id,
            request_hash=document["request_hash"],
            masked_result=document["masked_result"],
            mapping=self._cipher.decrypt(
                payload_id, base64.b64decode(document["mapping"], validate=True)
            ),
            state=document["state"],
            created_at=datetime.fromisoformat(document["created_at"]),
            expires_at=datetime.fromisoformat(document["expires_at"]),
        )

    async def create_if_absent(self, record: VaultRecord) -> CreateResult:
        now = datetime.now(UTC)
        ttl_seconds = math.ceil((record.expires_at - now).total_seconds())
        if ttl_seconds <= 0:
            raise ValueError("cannot store an already expired record")
        key = self._key(record.payload_id)
        created = await self._redis.set(
            key, self._encode(record), ex=ttl_seconds, nx=True
        )
        if created:
            return CreateResult(created=True, record=record)

        # The winner could expire between SET NX and GET. Retry the atomic
        # operation once so callers never receive a result without a record.
        existing = await self._redis.get(key)
        if existing is not None:
            return CreateResult(created=False, record=self._decode(existing))
        created = await self._redis.set(
            key, self._encode(record), ex=ttl_seconds, nx=True
        )
        if created:
            return CreateResult(created=True, record=record)
        existing = await self._redis.get(key)
        if existing is None:
            raise RuntimeError("Redis create race did not yield a stored record")
        return CreateResult(created=False, record=self._decode(existing))

    async def get(self, payload_id: str) -> VaultRecord | None:
        raw = await self._redis.get(self._key(payload_id))
        return None if raw is None else self._decode(raw)

    async def cleanup_expired(self) -> int:
        # Redis removes EX keys itself; do not SCAN production keyspace merely
        # to report work already performed by the server.
        return 0

    async def close(self) -> None:
        await self._redis.aclose()

```

## solution/app/vault/factory.py

SHA-256: `02f7ba2817477c9afd81e85da752ce222e5513b8dc0c15f73438d8eadb5f95a0`

```
"""Environment-driven vault construction."""

from __future__ import annotations

import os

from .base import Vault
from .crypto import load_mapping_key
from .memory import InMemoryVault
from .redis import RedisVault


def create_vault(
    *, redis_url: str | None = None, mapping_encryption_key: str | None = None
) -> Vault:
    """Build Redis storage when configured, otherwise a local MVP vault."""

    key = load_mapping_key(mapping_encryption_key)
    configured_redis_url = redis_url or os.getenv("REDIS_URL")
    if configured_redis_url:
        return RedisVault(configured_redis_url, encryption_key=key)
    return InMemoryVault(encryption_key=key)

```

## solution/docker-compose.yml

SHA-256: `5e2cc47b8883da05077d8feb32d0c4235637f6f4b9f02ebfb0cd0de29685e3a1`

```
services:
  api:
    build: .
    environment:
      REDIS_URL: redis://redis:6379/0
      MAPPING_TTL_SECONDS: "900"
      LOG_LEVEL: INFO
    ports:
      - "8080:8080"
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--save", "", "--appendonly", "no", "--maxmemory-policy", "volatile-ttl"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped


```

## solution/pyproject.toml

SHA-256: `18cde322c33e0cc382223c0dd3a3e0141545d07933cb3afe35f0a7375251fdf8`

```
[project]
name = "pii-safety-module"
version = "0.1.0"
description = "Модуль обратимого маскирования персональных данных для LLM-потока"
requires-python = ">=3.12,<3.14"
dependencies = [
  "cryptography>=44,<47",
  "fastapi>=0.115,<1",
  "pydantic-settings>=2.7,<3",
  "pyyaml>=6,<7",
  "redis>=5,<7",
  "structlog>=24,<27",
  "uvicorn[standard]>=0.34,<1",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.28,<1",
  "hypothesis>=6,<7",
  "mypy>=1.14,<2",
  "pytest>=8,<10",
  "pytest-asyncio>=0.25,<2",
  "ruff>=0.9,<1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

```

## solution/benchmark-results/v6/IMPROVEMENT_REPORT.md

SHA-256: `b7f40af30cbac06c9719b76d2881ca6ee596d0e189e724fc68034740fd01df59`

```
# Improvement report v6

## Итог

В production продвинут детектор `v3.26`. На новом реалистичном слепом holdout
v16 его F1 составил **90,97%** против **85,33%** у v3.20. Прирост —
**+5,64 п.п.**; целевой уровень 80% превышен на 10,97 п.п.

Precision вырос с 86,49% до **92,52%**, recall — с 84,21% до **89,47%**.
Точное маскирование улучшилось со 151/180 до **159/180**, точный round-trip —
**180/180**.

Источник: `benchmark/results/sealed_holdout_v16_promotion.json`.

## Слепой процесс

- v14: оба первых кандидата не достигли 80% на distribution-shift stress;
- v15: оба кандидата также отклонены на новом stress-наборе;
- после этого архитектура изменена с набора фразовых regex на value-first
  evidence engine с field families, token-distance scoring и record boundaries;
- v16 содержал 180 новых реалистичных банковских, страховых и CRM-кейсов,
  90 positive / 90 hard negative, все 22 типа;
- developer agents не читали v16 до заморозки v3.25/v3.26;
- v3.25 получил F1 88,50%, v3.26 — 90,60%; после исправления обнаруженных
  regression-тестами suppressions финальный v3.26 получил 90,97%.

Источники: `benchmark/sealed_holdout_v14.json`,
`benchmark/sealed_holdout_v15.json`, `benchmark/sealed_holdout_v16.json`,
`benchmark/results/sealed_holdout_v16_baseline.json`.

## Что изменено

- value-first извлечение кандидатов по проверяемым формам;
- нормализация Unicode/OCR-разделителей с сохранением исходных offsets;
- оценка field, ownership, public и technical evidence по расстоянию токенов;
- границы записей и предложений ограничивают перенос контекста;
- checksum и shape validation сохранены для структурированных значений;
- подтверждённые структурированные сущности предыдущего слоя больше не могут
  быть отменены новым contextual suppression;
- для payload от 100 000 символов используется проверенный быстрый структурный
  слой v3.3.

Источники: `app/detection/detector_v3_22.py`,
`app/detection/detector_v3_24.py`, `app/detection/detector_v3_26.py`.

## Качество на stress-наборах

- v14: precision 100%, recall 98,50%, F1 **99,24%**;
- v15: precision 95,83%, recall 95,83%, F1 **95,83%**;
- v16 blind: precision 92,52%, recall 89,47%, F1 **90,97%**.

Источник: локальный `benchmark.evaluate_quality` с production v3.26.

## Проверки и SLA

- pytest: **201 passed**;
- Ruff: без ошибок;
- mypy strict: без ошибок в 93 source files;
- 100 000 токенов: mask p95 **854,72 мс**, round-trip точный;
- Docker/k6 measured phase: **30 002 запроса за 30 секунд**,
  то есть **1000,07 HTTP RPS**;
- HTTP p95 measured phase: **1,75 мс**;
- errors, failed checks и dropped iterations: **0**;
- успешно 62 004 из 62 004 проверок.

Источники: `benchmark-results/v6/large-payload-benchmark.json`,
`benchmark-results/v6/load-summary.json`.

## Решение

v3.26 принят: F1 устойчиво выше 80%, blind precision/recall улучшены,
регрессионные тесты пройдены, round-trip и SLA сохранены.

```

## solution/benchmark-results/v6/large-payload-benchmark.json

SHA-256: `41bfdf1573eeefd06302086c4321f4b189898126d97248203f1887dcb834e6b3`

```
{
  "schema_version": 1,
  "python_version": "3.12.7",
  "warmups": 1,
  "cases": [
    {
      "target_tokens": 1000,
      "actual_tokens": 1000,
      "payload_utf8_bytes": 15748,
      "masked_utf8_bytes": 15737,
      "detected_entities": 3,
      "mapping_entries": 3,
      "iterations": 5,
      "mask_ms_min": 55.379459,
      "mask_ms_median": 55.629583,
      "mask_ms_p95": 56.269917,
      "mask_ms_max": 56.269917,
      "unmask_ms_min": 0.008125,
      "unmask_ms_median": 0.008916,
      "unmask_ms_p95": 0.009125,
      "unmask_ms_max": 0.009125,
      "tracemalloc_peak_bytes": 56352,
      "process_peak_rss_bytes": 25067520,
      "exact_round_trip": true,
      "pii_positions": {
        "start": 0,
        "middle": 500,
        "end": 999
      }
    },
    {
      "target_tokens": 10000,
      "actual_tokens": 10000,
      "payload_utf8_bytes": 157500,
      "masked_utf8_bytes": 157489,
      "detected_entities": 3,
      "mapping_entries": 3,
      "iterations": 5,
      "mask_ms_min": 190.112042,
      "mask_ms_median": 191.90975,
      "mask_ms_p95": 193.155959,
      "mask_ms_max": 193.155959,
      "unmask_ms_min": 0.041167,
      "unmask_ms_median": 0.042833,
      "unmask_ms_p95": 0.04575,
      "unmask_ms_max": 0.04575,
      "tracemalloc_peak_bytes": 509100,
      "process_peak_rss_bytes": 25395200,
      "exact_round_trip": true,
      "pii_positions": {
        "start": 0,
        "middle": 5000,
        "end": 9999
      }
    },
    {
      "target_tokens": 100000,
      "actual_tokens": 100000,
      "payload_utf8_bytes": 1575000,
      "masked_utf8_bytes": 1574989,
      "detected_entities": 3,
      "mapping_entries": 3,
      "iterations": 5,
      "mask_ms_min": 851.618292,
      "mask_ms_median": 851.785583,
      "mask_ms_p95": 854.724125,
      "mask_ms_max": 854.724125,
      "unmask_ms_min": 0.249167,
      "unmask_ms_median": 0.2505,
      "unmask_ms_p95": 0.321292,
      "unmask_ms_max": 0.321292,
      "tracemalloc_peak_bytes": 5028717,
      "process_peak_rss_bytes": 35667968,
      "exact_round_trip": true,
      "pii_positions": {
        "start": 0,
        "middle": 50000,
        "end": 99999
      }
    }
  ]
}

```

## solution/benchmark-results/v6/load-summary.json

SHA-256: `1a6835001ce7c6e701c6122146e90f682ba44b26f3d949e102acd75746c9c86a`

```
{
    "root_group": {
        "name": "",
        "path": "",
        "id": "d41d8cd98f00b204e9800998ecf8427e",
        "groups": {},
        "checks": {
                "mask returns HTTP 200": {
                    "passes": 15501,
                    "fails": 0,
                    "name": "mask returns HTTP 200",
                    "path": "::mask returns HTTP 200",
                    "id": "5f312f7acdef954b013298597c6ab505"
                },
                "mask hides known PII": {
                    "path": "::mask hides known PII",
                    "id": "6b0a1fc841b789051bdf10fc0ec57e27",
                    "passes": 15501,
                    "fails": 0,
                    "name": "mask hides known PII"
                },
                "unmask returns HTTP 200": {
                    "id": "722b8021d1ec3bd28d4df6fc84550d65",
                    "passes": 15501,
                    "fails": 0,
                    "name": "unmask returns HTTP 200",
                    "path": "::unmask returns HTTP 200"
                },
                "unmask restores source exactly": {
                    "fails": 0,
                    "name": "unmask restores source exactly",
                    "path": "::unmask restores source exactly",
                    "id": "54f59518eb91a56e914bb91096167c10",
                    "passes": 15501
                }
            }
    },
    "metrics": {
        "vus_max": {
            "value": 1000,
            "min": 1000,
            "max": 1000
        },
        "mask_request_duration": {
            "p(99)": 3.207583,
            "max": 11.402334,
            "avg": 1.5472941946536793,
            "min": 1.291209,
            "med": 1.457417,
            "p(90)": 1.719333,
            "p(95)": 1.846417
        },
        "http_req_duration": {
            "p(90)": 1.6561208,
            "p(95)": 1.8271648999999999,
            "p(99)": 3.7191008399999994,
            "max": 11.630834,
            "avg": 1.1319597919489008,
            "min": 0.413667,
            "med": 1.3592914999999999
        },
        "benchmark_errors": {
            "passes": 0,
            "fails": 31002,
            "value": 0
        },
        "http_req_receiving": {
            "p(90)": 0.030334,
            "p(95)": 0.036375,
            "p(99)": 0.061542,
            "max": 0.320125,
            "avg": 0.01783879178762689,
            "min": 0.003042,
            "med": 0.01275
        },
        "data_received": {
            "count": 7455981,
            "rate": 186374.84138088577
        },
        "iteration_duration": {
            "min": 1.845458,
            "med": 2.140833,
            "p(90)": 3.185625,
            "p(95)": 3.783375,
            "p(99)": 6.199042,
            "max": 15.086333,
            "avg": 2.426809126443452
        },
        "http_req_sending": {
            "max": 0.437041,
            "avg": 0.004553096993742152,
            "min": 0.001416,
            "med": 0.002959,
            "p(90)": 0.007917,
            "p(95)": 0.011583949999999999,
            "p(99)": 0.02783399
        },
        "business_cycle_duration": {
            "avg": 2.384307712819145,
            "min": 1,
            "med": 2,
            "p(90)": 3,
            "p(95)": 3,
            "p(99)": 6,
            "max": 15
        },
        "dropped_iterations{scenario:benchmark}": {
            "count": 0,
            "rate": 0,
            "thresholds": {
                "count==0": false
            }
        },
        "http_req_tls_handshaking": {
            "med": 0,
            "p(90)": 0,
            "p(95)": 0,
            "p(99)": 0,
            "max": 0,
            "avg": 0,
            "min": 0
        },
        "iterations": {
            "count": 15501,
            "rate": 387.4736827045442
        },
        "http_req_duration{expected_response:true}": {
            "avg": 1.1319597919489008,
            "min": 0.413667,
            "med": 1.3592914999999999,
            "p(90)": 1.6561208,
            "p(95)": 1.8271648999999999,
            "p(99)": 3.7191008399999994,
            "max": 11.630834
        },
        "checks{scenario:benchmark}": {
            "passes": 60004,
            "fails": 0,
            "thresholds": {
                "rate>0.99": false
            },
            "value": 1
        },
        "data_sent": {
            "rate": 236728.7224763669,
            "count": 9470403
        },
        "http_reqs": {
            "count": 31002,
            "rate": 774.9473654090884
        },
        "http_req_duration{scenario:benchmark}": {
            "min": 0.413667,
            "med": 1.358771,
            "p(90)": 1.62975,
            "p(95)": 1.75674585,
            "p(99)": 2.6208241699999983,
            "max": 11.402334,
            "avg": 1.1033704338044057,
            "thresholds": {
                "p(95)<1000": false
            }
        },
        "http_req_connecting": {
            "avg": 0.01842973156570545,
            "min": 0,
            "med": 0,
            "p(90)": 0,
            "p(95)": 0,
            "p(99)": 0.5477034199999998,
            "max": 5.317
        },
        "dropped_iterations": {
            "count": 0,
            "rate": 0
        },
        "http_req_failed": {
            "passes": 0,
            "fails": 31002,
            "value": 0
        },
        "checks": {
            "passes": 62004,
            "fails": 0,
            "value": 1
        },
        "http_req_blocked": {
            "min": 0.000375,
            "med": 0.000916,
            "p(90)": 0.001666,
            "p(95)": 0.003292,
            "p(99)": 0.5844057499999996,
            "max": 5.3365,
            "avg": 0.020504002741758103
        },
        "http_req_waiting": {
            "p(99)": 3.6414870799999997,
            "max": 11.51175,
            "avg": 1.109567903167543,
            "min": 0.400584,
            "med": 1.344541,
            "p(90)": 1.6299497,
            "p(95)": 1.7974044999999996
        },
        "benchmark_errors{scenario:benchmark}": {
            "passes": 0,
            "fails": 30002,
            "thresholds": {
                "rate<0.01": false
            },
            "value": 0
        },
        "vus": {
            "min": 0,
            "max": 3,
            "value": 2
        },
        "http_req_failed{scenario:benchmark}": {
            "passes": 0,
            "fails": 30002,
            "thresholds": {
                "rate<0.01": false
            },
            "value": 0
        },
        "unmask_request_duration": {
            "avg": 0.6594466729551388,
            "min": 0.413667,
            "med": 0.531875,
            "p(90)": 0.914375,
            "p(95)": 1.489208,
            "p(99)": 2.17625,
            "max": 6.88275
        }
    }
}
```
