"""Candidate v3.22: boundary-aware grammar ensemble over production v3.20.

The proposal keeps value extraction separate from context interpretation.  A
same-length OCR shadow is used only for labels, while returned spans always
refer to the original text.  Ambiguous candidates require a field grammar or
personal record context and are filtered by hard-negative public/technical
contexts.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from .detector_v3_20 import detect as production_detect
from .models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_CAP_WORD = r"[А-ЯЁ][а-яё]+(?:-[А-ЯЁа-яё][а-яё]+)*"
_FULL_NAME = rf"{_CAP_WORD}(?:\s+{_CAP_WORD}){{1,3}}"
_CITY = rf"{_CAP_WORD}(?:\s+{_CAP_WORD})?"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}"

# One code point in, one code point out: regex offsets stay valid.  Translation
# is deliberately limited to common OCR confusables in Russian field labels.
_OCR_TABLE = str.maketrans(
    {
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "a": "а",
        "c": "с",
        "e": "е",
        "o": "о",
        "p": "р",
        "x": "х",
        " ": " ",
        " ": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
    }
)

_PERSONAL = re.compile(
    r"\b(?:сам\w*|сво[йюяеёихгомй]*|мо[йюяеёихгомй]*|его|её|ему|ей|клиент\w*|"
    r"граждан\w*|физлиц\w*|заявител\w*|пациент\w*|владел\w*|"
    r"держател\w*|получател\w*|доверен\w*\s+лиц\w*|домашн\w*|"
    r"личн\w*|прожива\w*|мест\w*\s+(?:жительства|регистрации)|"
    r"достав\w*\s+(?:ему|ей)?\s*домой)\b",
    re.IGNORECASE,
)
_PUBLIC = re.compile(
    r"\b(?:автосервис\w*|банк\w*\s+отвеча\w*|выставк\w*|дежурн\w*\s+част\w*|"
    r"издательств\w*|клиентск\w*\s+служб\w*|офис\w*|"
    r"организац\w*|фонд\w*|склад\w*|производител\w*|дилер\w*|"
    r"пожертвован\w*|билет\w*|возврат\w*|логистик\w*|"
    r"пункт\w*\s+(?:выдач\w*|самовывоз\w*)|самовывоз\w*|постамат\w*|"
    r"ресторан\w*|магазин\w*|филиал\w*)\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:модел\w*|контроллер\w*|артикул\w*|компонент\w*|оборудован\w*|"
    r"запчаст\w*|тестов\w*|пример\w*|фиктивн\w*)\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:dealers?|donations?|logistics(?:-team)?|refund|exhibition|sales|jobs?|"
    r"billing|orders?|events?|partners?|service|support|help|info|office|press|"
    r"admin|team|noreply)@",
    re.IGNORECASE,
)
_PRIVATE_OVERRIDE = re.compile(
    r"\b(?:мо[йюяеёихгомй]*|личн\w*|домашн\w*)\b[^.;\n]{0,80}"
    r"\bне\s+адрес\s+(?:офиса|организации|магазина)\b",
    re.IGNORECASE,
)
_LONG_HOT = re.compile(
    r"@|(?<!\d)(?:\+?7|8)[\s().-]*\d{3}[\s().-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}(?!\d)|"
    r"(?<!\d)\d{4,19}(?!\d)|"
    r"\b(?:клиент\w*|граждан\w*|заявител\w*|пациент\w*|получател\w*|"
    r"владел\w*|доверен\w*|инн|снилс|паспорт\w*|удостоверен\w*|"
    r"адрес\w*|прожива\w*|рожд\w*|гражданств\w*|улиц\w*|индекс|"
    r"cvv2?|cvc2?|pin|пин)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class GrammarRule:
    entity_type: str
    pattern: re.Pattern[str]
    source: str
    requires_personal: bool = False


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


_RULES = (
    GrammarRule(
        "PERSON",
        _rx(
            rf"\b(?:данные\s+сообщает\s+сама?|пациент\w*\s+зовут|"
            rf"доверен\w*\s+лиц\w*\s+выступил\w*)\s+(?P<value>{_FULL_NAME})"
        ),
        "person_field_grammar_v3_22",
    ),
    GrammarRule(
        "ADDRESS_COUNTRY",
        _rx(
            r"\b(?:стран\w*(?:\s+мо\w*\s+проживания)?(?:\s+указан\w*)?"
            r"(?:\s+отдельно)?\s*[:=-]|"
            r"адрес\w*[^.;\n]{0,70}[=-])\s*"
            r"(?P<value>Россия|РФ|Российская\s+Федерация)"
        ),
        "country_field_grammar_v3_22",
    ),
    GrammarRule(
        "ADDRESS_POSTAL_CODE",
        _rx(
            r"\b(?:индекс|дом\w*\s+(?:адрес\w*|клиент\w*)|"
            r"достав\w*[^.;\n]{0,45}домой)"
            r"[^.;\n\d]{0,25}(?P<value>\d{6})(?!\d)"
        ),
        "postcode_field_grammar_v3_22",
    ),
    GrammarRule(
        "ADDRESS_CITY",
        _rx(rf"\bжив[ёе]т\s+в\s+(?:городе\s+)?(?P<value>{_CITY})(?=\s*[,;.])"),
        "city_residence_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_CITY",
        _rx(
            rf"\b(?:нов\w*\s+адрес\w*|дом\w*\s+клиент\w*)"
            rf"\s*[:=-]\s*\d{{6}}\s*,\s*(?P<value>{_CITY})(?=\s*[,;.])"
        ),
        "city_record_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_CITY",
        _rx(
            rf"\bадрес\w*[^.;\n]{{0,70}}[-:=]\s*"
            rf"(?:Россия|РФ|Российская\s+Федерация)\s*[;,]\s*"
            rf"\d{{6}}\s*[;,]\s*(?:город\s+)?(?P<value>(?!город\b){_CITY})(?=\s*[,;.])"
        ),
        "city_semicolon_record_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_CITY",
        _rx(rf"\bкорреспонденц\w*[^.;\n]{{0,45}}\sво\s+(?P<value>{_CITY})(?=\s*[,;.])"),
        "city_delivery_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_CITY",
        _rx(rf"\bгород\s*,?\s+в\s+котор\w*[^:;\n]{{0,40}}:\s*(?P<value>{_CITY})(?=\s*[,;.])"),
        "city_relative_field_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_STREET",
        _rx(
            rf"\b(?:улиц(?:а|е|у|ы)(?:\s+(?:проживания|регистрации|"
            rf"мо\w*\s+мест\w*\s+регистрации))?"
            rf"(?:\s+называется)?|на\s+улицу)\s*[:=-]?\s*(?P<value>{_WORD})"
        ),
        "street_field_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_HOUSE",
        _rx(r"\b(?:номер\s+)?дом(?:а|е)?\s*[:=-]?\s*(?P<value>\d{1,4}[А-ЯЁA-Z]?)(?!\d)"),
        "house_field_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_HOUSE",
        _rx(r"\bдом\b[^.;\n]{0,70}?\bномер\s+(?P<value>\d{1,4}[А-ЯЁA-Z]?)(?!\d)"),
        "house_record_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "ADDRESS_APARTMENT",
        _rx(r"\bквартир(?:а|е|у|ы)\s*[:=-]?\s*(?P<value>\d{1,5})(?!\d)"),
        "flat_field_grammar_v3_22",
        True,
    ),
    GrammarRule(
        "PASSPORT_RF",
        _rx(r"\bпаспорт\w*(?:\s+граждан\w*)?\s+(?P<value>\d{10})(?!\d)"),
        "passport_field_grammar_v3_22",
    ),
    GrammarRule(
        "DIVISION_CODE",
        _rx(
            r"\b(?:код\s+(?:орган\w*\s+)?выдач\w*|"
            r"орган\w*\s+выдач\w*[^.;\n]{0,25}код|КП\s+документ\w*)"
            r"[^.;\n\d]{0,35}(?P<value>\d{3}[\s/-]\d{3})(?!\d)"
        ),
        "division_field_grammar_v3_22",
    ),
    GrammarRule(
        "PLACE_OF_BIRTH",
        _rx(rf"\bродн\w*\s+город\w*[^.;\n]{{0,40}}?\s(?P<value>г\.\s*{_CITY})(?=\s*[.;,])"),
        "birthplace_field_grammar_v3_22",
    ),
    GrammarRule(
        "CITIZENSHIP",
        _rx(rf"\b(?:состоит\s+в\s+)?гражданств\w*\s+(?P<value>Республик\w*\s+{_CITY})"),
        "citizenship_field_grammar_v3_22",
    ),
    GrammarRule(
        "PASSPORT_ISSUER",
        _rx(
            r"\b(?:паспорт\s+оформлял\w*|выдавш\w*\s+ведомств\w*\s*[:=-])\s*"
            r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b"
            r"(?:г\.|[^.;\n])*?)(?=\s*[.;]|\s+\d{2}[./-]\d{2}[./-]\d{4}|$)"
        ),
        "issuer_field_grammar_v3_22",
    ),
    GrammarRule(
        "PASSPORT_ISSUER",
        _rx(
            r"\b(?:его\s+|её\s+)?выдал\w*\s+"
            r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b"
            r"(?:г\.|[^.;\n])*?)(?=\s*[.;]|\s+\d{2}[./-]\d{2}[./-]\d{4}|$)"
        ),
        "issuer_verb_grammar_v3_22",
    ),
    GrammarRule(
        "DRIVER_LICENSE_RF",
        _rx(r"\b(?:водител\w*[^.;\n]{0,35})?сво\w*\s+удостоверени\w*\s+(?P<value>\d{2}\s\d{2}\s\d{6})(?!\d)"),
        "license_field_grammar_v3_22",
    ),
    GrammarRule(
        "PIN",
        _rx(r"\bПИН\b[^.;\n]{0,55}?\b(?:равен|составляет)\s*(?P<value>\d{4})(?!\d)"),
        "pin_field_grammar_v3_22",
    ),
    GrammarRule(
        "PASSPORT_ISSUE_DATE",
        _rx(
            rf"\b(?:паспорт\w*[^;\n]{{0,100}}(?:выдал\w*|выдан\w*)[^;\n]{{0,100}}?)"
            rf"(?P<value>{_DATE})(?=\s*[;,])"
        ),
        "issue_date_record_grammar_v3_22",
    ),
)


def _shadow(text: str) -> str:
    return text.translate(_OCR_TABLE)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    priority: int = 220,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.998, source, priority)


def _context(text: str, start: int, end: int, radius: int = 180) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]


def _valid_date(value: str) -> bool:
    day, month, year = (int(part) for part in re.split(r"[-/.]", value))
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _grammar_candidates(text: str) -> Iterator[DetectedEntity]:
    shadow = _shadow(text)
    for rule in _RULES:
        for match in rule.pattern.finditer(shadow):
            start, end = match.span("value")
            context = _context(shadow, start, end)
            if rule.requires_personal and not _PERSONAL.search(context):
                continue
            if rule.entity_type == "PASSPORT_ISSUE_DATE" and not _valid_date(text[start:end]):
                continue
            yield _entity(text, rule.entity_type, (start, end), rule.source)


def _hard_negative(text: str, entity: DetectedEntity) -> bool:
    context = _context(_shadow(text), entity.start, entity.end)
    public = _PUBLIC.search(context) is not None
    technical = _TECHNICAL.search(context) is not None
    if entity.entity_type == "EMAIL":
        return _ROLE_EMAIL.search(entity.text) is not None or public
    if entity.entity_type == "PHONE_RF":
        return public or technical
    if entity.entity_type.startswith("ADDRESS_"):
        if entity.entity_type == "ADDRESS_HOUSE" and len(re.sub(r"\D", "", entity.text)) > 4:
            return True
        return public and _PRIVATE_OVERRIDE.search(context) is None
    if entity.entity_type == "CVV":
        before = text[max(0, entity.start - 4) : entity.start]
        return technical or before.endswith(("CVC-", "CVV-"))
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


def _detect_windowed(text: str) -> list[DetectedEntity]:
    # Long natural documents are normally sparse in PII.  Scan once for broad
    # high-recall anchors, merge nearby regions, and run inherited rules only
    # there.  This also bounds their quadratic overlap resolver.
    radius = 384
    intervals: list[tuple[int, int]] = []
    for match in _LONG_HOT.finditer(text):
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        if intervals and start <= intervals[-1][1]:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))
        else:
            intervals.append((start, end))
    if not intervals:
        return []

    entities: list[DetectedEntity] = []
    core_size = 1_024
    for interval_start, interval_end in intervals:
        for core_start in range(interval_start, interval_end, core_size):
            core_end = min(interval_end, core_start + core_size)
            window_start = max(interval_start, core_start - 256)
            window_end = min(interval_end, core_end + 256)
            segment = text[window_start:window_end]
            for item in _detect_short(segment):
                absolute_start = item.start + window_start
                absolute_end = item.end + window_start
                center = (absolute_start + absolute_end) // 2
                if core_start <= center < core_end:
                    entities.append(
                        DetectedEntity(
                            item.entity_type,
                            absolute_start,
                            absolute_end,
                            text[absolute_start:absolute_end],
                            item.confidence,
                            item.source,
                            item.priority,
                        )
                    )
    return _merge(entities)


def _detect_short(text: str) -> list[DetectedEntity]:
    return [
        entity
        for entity in _merge([*production_detect(text), *_grammar_candidates(text)])
        if not _hard_negative(text, entity)
    ]


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII using production plus validated, boundary-aware grammars."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    if len(text) >= 16_384:
        return _detect_windowed(text)
    return _detect_short(text)

