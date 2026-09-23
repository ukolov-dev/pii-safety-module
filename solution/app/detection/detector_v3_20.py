"""Candidate v3.20: normalized evidence scoring over candidate v3.18.

Unlike the preceding label-specific expansion, this proposal extracts weak value
shapes and scores nearby ownership, field, public, and technical evidence before
accepting them. Production remains unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

from .detector_v3_13 import detect as detect_v3_13
from .detector_v3_18 import detect as detect_v3_18
from .models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_DATE = (
    r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{2}[-/.](?:1[0-2]|0?[1-9])[-/.](?:3[01]|[12]\d|0?[1-9])"
)
_LATIN_NAME = r"[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3}"
_END = r"(?=\s*(?:[,;.]|$))"

_PERSONAL = re.compile(
    r"\b(?:сам\w*|свой|своего|мо[йяё]|мои|мне|я\s+живу|клиент\w*|"
    r"граждан\w*|физлиц\w*|заявител\w*|собственник\w*|получател\w*|"
    r"держател\w*|владел\w*|домашн\w*|личн\w*|прожива\w*|"
    r"место\s+жительства)\b",
    re.IGNORECASE,
)
_PUBLIC = re.compile(
    r"\b(?:администраци\w*|аэропорт\w*|бассейн\w*|бизнес\w*|галере\w*|"
    r"кинотеатр\w*|магазин\w*|организаци\w*|отдел\w*|офис\w*|партн[её]р\w*|"
    r"постамат\w*|пункт\w*\s+(?:выдач\w*|самовывоз\w*)|публичн\w*|ресторан\w*|"
    r"самовывоз\w*|служб\w*|склад\w*|центр\w*|филиал\w*|франшиз\w*|школ\w*|"
    r"не\s+(?:домашн\w*|жиль[её]|свой|заявител\w*))\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:запчаст\w*|компонент\w*|детал\w*|оборудовани\w*|склад\w*|"
    r"фиктивн\w*|заглушк\w*|макет\w*|пример\w*|тестов\w*)\b",
    re.IGNORECASE,
)
_AUTOMATED = re.compile(
    r"\b(?:автоматическ\w*|робот\w*|рассылк\w*|уведомлени\w*|общ\w*\s+ящик)\b",
    re.IGNORECASE,
)
_NEGATED_PUBLIC = re.compile(
    r"\b(?:не\s+адрес\s+(?:офиса|организации|магазина)|"
    r"а\s+не\s+(?:офиса|организации|магазина))\b",
    re.IGNORECASE,
)

_V3_20_TRIGGER_WORDS = (
    "инн",
    "налогов",
    "рожд",
    "права",
    "удостоверени",
    "паспорт",
    "подразделени",
    "выдан",
    "гражданств",
    "страна",
    "адрес",
    "индекс",
    "город",
    "улиц",
    "дом",
    "квартир",
    "cvv",
    "cvc",
    "pin",
    "пин",
    "держател",
)


@dataclass(frozen=True, slots=True)
class ScoredRule:
    entity_type: str
    value: re.Pattern[str]
    field: re.Pattern[str]
    source: str
    threshold: int = 3


def _rx(value: str) -> re.Pattern[str]:
    return re.compile(value, re.IGNORECASE)


_RULES = (
    ScoredRule(
        "INN",
        _rx(r"(?<!\d)(?P<value>\d{10}|\d{12})(?!\d)"),
        _rx(r"\b(?:ИНН|идентификатор\w*\s+(?:в|для)\s+ФНС|налогов\w*\s+номер)\b"),
        "inn_scored_v3_20",
    ),
    ScoredRule(
        "BIRTH_DATE",
        _rx(rf"(?<!\d)(?P<value>{_DATE})(?!\d)"),
        _rx(r"\b(?:день|дата)\s+рождения|\bрождени[ея]\b|\bд\.?\s*р\.?\b"),
        "birth_scored_v3_20",
    ),
    ScoredRule(
        "DRIVER_LICENSE_RF",
        _rx(r"(?<!\d)(?P<value>\d{2}(?:[- ]?\d{2})[- ]\d{6})(?!\d)"),
        _rx(r"\b(?:водительск\w*\s+(?:права|удостоверение)|права|ВУ)\b"),
        "license_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_COUNTRY",
        _rx(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b"),
        _rx(r"\b(?:страна|государство)(?:\s+проживания)?\b|\bдомашн\w*\s+адрес\b"),
        "country_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_POSTAL_CODE",
        _rx(r"(?<!\d)(?P<value>\d{6})(?!\d)"),
        _rx(r"\b(?:почтовый\s+)?индекс\b|\b(?:адрес|доставк\w*)\b"),
        "postcode_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_CITY",
        _rx(
            rf"\b(?:жив[её]т|живу|прожива\w*)\s+(?:в|во)\s+"
            rf"(?:городе\s+)?(?P<value>(?!квартир\w*\b){_WORD})|"
            rf"\bгород\s+проживания[^:—\n]{{0,60}}[:—-]\s*(?P<label>{_WORD})"
        ),
        _rx(r"\b(?:город|жив[её]т|живу|прожива\w*)\b"),
        "city_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_STREET",
        _rx(
            rf"\b(?:улиц(?:а|е)(?:\s+(?:проживания|регистрации|"
            rf"в\s+адресе\s+\w+))?|ул\.)\s*"
            rf"[:—-]?\s*(?P<value>{_WORD})"
        ),
        _rx(r"\b(?:улиц\w*|домашн\w*\s+адрес|адрес\w*)\b"),
        "street_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_HOUSE",
        _rx(
            r"\b(?:номер\s+дом(?:а|е)?(?:\s+[А-ЯЁа-яё-]+)?|дом(?:а|е)?)\s*"
            r"[:—-]?\s*(?P<value>\d+[А-ЯЁA-Z]?)(?!\d)"
        ),
        _rx(r"\b(?:номер\s+дома|домашн\w*\s+адрес|адрес\w*|дом\s+граждан\w*|дом)\b"),
        "house_scored_v3_20",
    ),
    ScoredRule(
        "ADDRESS_APARTMENT",
        _rx(
            r"\bквартир(?:а|е|ы)(?:\s+(?:самого\s+)?[А-ЯЁа-яё-]+)?\s*"
            r"[:—-]?\s*(?P<value>\d+)(?!\d)"
        ),
        _rx(r"\b(?:квартир\w*|прожива\w*|домашн\w*\s+адрес)\b"),
        "flat_scored_v3_20",
    ),
    ScoredRule(
        "CVV",
        _rx(
            r"\b(?:CVV2?|CVC2?)\s*(?:на\s+карт\w*(?:\s+\w+)?)?\s*"
            r"(?:составляет|равен)?\s*[:=-]?\s*(?P<value>\d{3,4})(?!\d)"
        ),
        _rx(r"\b(?:CVV2?|CVC2?|код\s+безопасности)\b"),
        "cvv_scored_v3_20",
    ),
    ScoredRule(
        "CARDHOLDER_NAME",
        _rx(
            rf"\b(?:CARD\s+HOLDER\s+NAME|имя\s+владельца|на\s+пластике\s+"
            rf"(?:написано|напечатано)\s+имя\s+владельца)\s*[:—-]?\s*"
            rf"(?P<value>{_LATIN_NAME}){_END}"
        ),
        _rx(r"\b(?:CARD\s+HOLDER|имя\s+владельца|на\s+пластике)\b"),
        "cardholder_scored_v3_20",
        2,
    ),
    ScoredRule(
        "PASSPORT_ISSUER",
        _rx(
            r"\b(?:орган|кем\s+выдан)\s*[:—-]?\s*"
            r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b[^,;\n]*?)"
            r"(?=\s*[,;]|\.\s*$|$)"
        ),
        _rx(r"\b(?:личн\w*\s+документ\w*|паспорт|орган\s+выдачи|кем\s+выдан)\b"),
        "issuer_scored_v3_20",
    ),
)

_WORD_ISSUE_DATE = re.compile(
    r"\b(?:паспорт|документ)\s+(?:оформили|выдали)(?:\s+(?:ему|ей|мне))?\s+"
    r"(?P<value>(?:первого|второго|третьего|четв[её]ртого|пятого|шестого|"
    r"седьмого|восьмого|девятого|десятого|одиннадцатого|двенадцатого|"
    r"тринадцатого|четырнадцатого|пятнадцатого|шестнадцатого|семнадцатого|"
    r"восемнадцатого|девятнадцатого|двадцатого|двадцать\s+\w+|тридцатого|"
    r"тридцать\s+первого)\s+(?:января|февраля|марта|апреля|мая|июня|июля|"
    r"августа|сентября|октября|ноября|декабря)\s+(?:19|20)\d{2}\s+года)",
    re.IGNORECASE,
)
_BIRTHPLACE_PROSE = re.compile(
    rf"\b(?:родил(?:ся|ась)|рожд[её]н\w*)\b[^;\n]{{0,35}}?\s+в\s+"
    rf"(?P<value>(?:селе|деревне|городе|г\.|ауле|хуторе|станице)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}})(?=\s+(?:и\s+теперь|[,;.]|$))",
    re.IGNORECASE,
)

_ROLE_EMAIL = re.compile(
    r"^(?:franchise|notifier|office-manager|gallery-office|business|rewards?|"
    r"accreditation|internship|receipt|concierge|culture|mailer|presscenter|"
    r"supportdesk|expo|service|office|team|press|support|help|info|hr|admin|noreply)@",
    re.IGNORECASE,
)


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    confidence: float,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], confidence, source, 180)


def _window(text: str, start: int, end: int, radius: int = 150) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]


def _score(text: str, match: re.Match[str], rule: ScoredRule) -> int:
    window = _window(text, *match.span("value"))
    score = 2 if rule.field.search(window) else 0
    if _PERSONAL.search(window):
        score += 2
    if _PUBLIC.search(window) and not _NEGATED_PUBLIC.search(window):
        score -= 3
    if _TECHNICAL.search(window):
        score -= 4
    return score


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
        first = sum(a * b for a, b in zip(digits[:10], weights_11, strict=True)) % 11 % 10
        second = sum(a * b for a, b in zip(digits[:11], weights_12, strict=True)) % 11 % 10
        return (first, second) == (digits[10], digits[11])
    return False


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[-/.]", value)]
    year, month, day = parts if len(str(parts[0])) == 4 else parts[::-1]
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _scored_candidates(text: str) -> Iterator[DetectedEntity]:
    for rule in _RULES:
        for match in rule.value.finditer(text):
            value = match.group("value") or match.groupdict().get("label")
            if value is None:
                continue
            group = "value" if match.group("value") is not None else "label"
            if rule.entity_type == "INN" and not _valid_inn(value):
                continue
            if rule.entity_type == "BIRTH_DATE" and not _valid_date(value):
                continue
            score = _score(text, match, rule)
            if score >= rule.threshold:
                yield _entity(
                    text,
                    rule.entity_type,
                    match.span(group),
                    rule.source,
                    min(0.999, 0.90 + score / 100),
                )
    for match in _WORD_ISSUE_DATE.finditer(text):
        yield _entity(
            text,
            "PASSPORT_ISSUE_DATE",
            match.span("value"),
            "issue_words_v3_20",
            0.998,
        )
    for match in _BIRTHPLACE_PROSE.finditer(text):
        yield _entity(
            text,
            "PLACE_OF_BIRTH",
            match.span("value"),
            "birthplace_prose_v3_20",
            0.998,
        )


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    window = _window(text, entity.start, entity.end)
    personal = _PERSONAL.search(window) is not None
    public = _PUBLIC.search(window) is not None
    technical = _TECHNICAL.search(window) is not None
    if entity.entity_type == "EMAIL":
        return bool(
            _ROLE_EMAIL.search(entity.text)
            or (public or _AUTOMATED.search(window)) and not personal
        )
    if entity.entity_type == "PHONE_RF":
        return bool((public and not personal) or technical)
    if entity.entity_type.startswith("ADDRESS_"):
        return public and not personal
    if entity.entity_type == "CVV":
        return technical
    if entity.entity_type == "PLACE_OF_BIRTH":
        before = text[max(0, entity.start - 50) : entity.start]
        return re.search(r"(?:теперь|сейчас)\s+жив[её]т\s+в\s+$", before, re.I) is not None
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
    """Return v3.18 plus normalized, scored weak-entity candidates."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    if len(text) >= 100_000:
        lowered = text.casefold()
        if not any(marker in lowered for marker in _V3_20_TRIGGER_WORDS):
            return detect_v3_13(text)
    return [
        entity
        for entity in _merge([*detect_v3_18(text), *_scored_candidates(text)])
        if not _suppressed(text, entity)
    ]
