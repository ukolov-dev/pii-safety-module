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

from app.detection.detector_v3_3 import detect as detect_v3_3
from app.detection.models import DetectedEntity
from proposals.detector_v3_24 import detect as detect_v3_24

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
