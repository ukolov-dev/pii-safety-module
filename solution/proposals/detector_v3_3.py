"""Candidate v3.3: ownership-gated PII detection with broader Russian syntax.

This layer keeps v3.2's suppression policy and adds recognizers for semantic field
labels, inflected Russian prose, compound address chains, and payment-document
vocabulary.  It remains isolated from production for comparative evaluation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from app.detection.models import DetectedEntity
from proposals.detector_v3_2 import detect as detect_v3_2

_SEP = r"\s*(?:[:=№/]|[-–—])?\s*"
_END = r"(?=\s*(?:[;]|\.(?:\s|$)|\n|$))"
_SENTENCE_END = r"(?=\s*(?:;|\.(?:\s*$|\s*\n)|$))"
_WORD = r"[A-Яa-яЁё]{2,}(?:-[A-Яa-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"

_PERSON_PATTERNS = (
    re.compile(
        rf"\b(?:фамилия\s*[,]?\s*имя\s*[,]?\s*отчество|"
        rf"ф\.?\s*и\.?\s*о\.?)(?:\s+клиента)?{_SEP}(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:на\s+имя|согласие\s+получено\s+от|"
        rf"заявку\s+подала?|заявление\s+от|меня\s+зовут){_SEP}"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\bанкета{_SEP}(?P<value>{_NAME3})\b", re.IGNORECASE),
    re.compile(
        rf"\b(?:получатель|заявитель|клиент){_SEP}"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)
_INFLECTED_PATRONYMIC = re.compile(
    r"(?:ович(?:а|у|е|ем)?|евич(?:а|у|е|ем)?|ич(?:а|у|е|ем)?|"
    r"овн(?:а|ы|ой|у|е)|евн(?:а|ы|ой|у|е)|ичн(?:а|ы|ой|у|е))$",
    re.IGNORECASE,
)
_CULTURAL = re.compile(
    r"\b(?:автор|книга|роман|семинар|лекция|музей|"
    r"доклад|научные\s+труды|биография|герой)\b",
    re.IGNORECASE,
)

_DIVISION_RE = re.compile(r"(?<!\d)\d{3}[- /]\d{3}(?!\d)")
_DIVISION_LABEL = re.compile(
    r"\b(?:код\s+(?:выдавшего\s+)?подразделения|к\s*/\s*п)\b",
    re.IGNORECASE,
)
_PASSPORT_NEAR = re.compile(r"\b(?:паспорт|личное\s+дело)\b", re.IGNORECASE)
_LOGISTICS = re.compile(r"\b(?:склад|контейнер|маршрут|логистик)\b", re.IGNORECASE)
_PERSON_INN_RE = re.compile(
    r"\b(?:ИНН\s+(?:налогоплательщика[- ]физлица|физлица)|"
    r"налогоплательщика\s*\(ИНН\))\s*[:—-]?\s*"
    r"(?P<value>\d{10}|\d{12})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_COMPACT_PERSONAL = re.compile(
    r"\bпаспортные\s+данные(?:\s+заявителя|клиента)?"
    r"\s*[:—-]?\s*(?P<value>\d{10})(?!\d)",
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
_ORDINAL_DAY = (
    r"первого|второго|третьего|четвёртого|пятого|шестого|седьмого|восьмого|"
    r"девятого|десятого|одиннадцатого|двенадцатого|тринадцатого|четырнадцатого|"
    r"пятнадцатого|шестнадцатого|семнадцатого|восемнадцатого|девятнадцатого|"
    r"двадцатого|(?:двадцать\s+)?(?:первого|второго|третьего|четвёртого|пятого|шестого|седьмого|"
    r"восьмого|девятого)|тридцатого|тридцать\s+первого"
)
_NUMERIC_DATE = re.compile(
    r"(?<!\d)(?:(?P<year>(?:19|20)\d{2})[-/.](?P<month_y>0?[1-9]|1[0-2])[-/.]"
    r"(?P<day_y>0?[1-9]|[12]\d|3[01])|"
    r"(?P<day>0?[1-9]|[12]\d|3[01])[-/.](?P<month>0?[1-9]|1[0-2])[-/.]"
    r"(?P<year_d>(?:19|20)\d{2}))(?!\d)"
)
_WORD_DATE = re.compile(
    rf"(?<![A-Яa-яЁё])(?P<ordinal>{_ORDINAL_DAY})\s+"
    rf"(?P<month>{'|'.join(_MONTHS)})\s+(?P<year>(?:19|20)\d{{2}})\s*г(?:ода|\.)?",
    re.IGNORECASE,
)
_TEXT_DATE = re.compile(
    rf"(?<!\d)(?P<day>0?[1-9]|[12]\d|3[01])\s+"
    rf"(?P<month>{'|'.join(_MONTHS)})\s+(?P<year>(?:19|20)\d{{2}})"
    r"(?:\s*г(?:ода|\.)?)?",
    re.IGNORECASE,
)
_BIRTH_CUE = re.compile(
    r"\b(?:дата\s+рождения|число\s*,?\s*месяц\s+и\s+год\s+рождения|"
    r"родил(?:ся|ась)|рождён|рождена|днём\s+рождения|DOB)\b",
    re.IGNORECASE,
)
_ISSUE_CUE = re.compile(
    r"\b(?:когда\s+выдан\w*|дата\s+выдачи|выдали\s+(?:ему|ей)|"
    r"выдан\w*)\b",
    re.IGNORECASE,
)
_DOC_CUE = re.compile(
    r"\b(?:пример|образец|шаблон|инструкция|документация|справка|подсказка|тестовый|"
    r"демонстрационный|учебный)\b",
    re.IGNORECASE,
)

_BIRTHPLACE_LABEL = re.compile(
    rf"\bместо\s+рождения(?:\s+(?:клиента|заявителя))?"
    rf"{_SEP}(?P<value>[^;\n]+?){_SENTENCE_END}",
    re.IGNORECASE,
)
_BIRTHPLACE_PROSE = re.compile(
    rf"\bродил(?:ся|ась)\s+в{_SEP}"
    rf"(?P<value>(?:(?:город(?:е)?|гор\.?|г\.?|посёлке|селе|деревне)\s+)?"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}})(?=\s*(?:[,;]|\.(?:\s*$|\s*\n)|$))",
    re.IGNORECASE,
)
_BIRTHPLACE_AFTER_DATE = re.compile(
    rf"\bв\s+(?P<value>(?:город(?:е)?|гор\.?|г\.?|посёлке|селе|деревне)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,3}})(?=\s*[,;.])",
    re.IGNORECASE,
)
_CITIZENSHIP_PROSE = re.compile(
    rf"\b(?:является\s+)?гражданином{_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}})(?=\s+(?:является|считается)|\s*[;.]|$)",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    rf"\b(?:орган\s*,?\s*выдавший\s+паспорт|кем\s+выдан|"
    rf"(?:паспорт|удостоверение\s+личности)\s+(?:было\s+)?выдано?){_SEP}"
    rf"(?P<value>(?:(?:У|ГУ|\bО)МВД|ОТДЕЛОМ\s+МВД)[^,;\n]*?){_SENTENCE_END}",
    re.IGNORECASE,
)
_INLINE_ISSUER_RE = re.compile(
    r"\bвыдан\s+(?P<value>(?:УМВД|ГУ\s+МВД|ОМВД)[^,;\n\d]*?)"
    r"(?=\s+(?:0?[1-9]|[12]\d|3[01])[./-]|\s*[,;]|\s*\.(?:\s*$|\s*\n)|$)",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\b(?:водительские\s+права|вод\.?\s*уд\.?|"
    rf"в\s*/\s*у(?:\s+водителя)?|ВУ){_SEP}"
    r"(?P<value>\d{2}[ -]?\d{2}[ -]?\d{6})(?!\d)",
    re.IGNORECASE,
)
_LICENSE_SERIES_RE = re.compile(
    r"\b(?:удостоверение|права)\s+водителя\s*[,]?\s*"
    r"серия\s+(?P<value>\d{2}[ -]?\d{2}\s*№\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_CVV_RE = re.compile(
    rf"\b(?:CVV2?|CVC2?)\)?{_SEP}(?P<value>\d{{3,4}})(?!\d)", re.IGNORECASE
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:CARD\s*HOLDER|держатель|владелец|имя\s+на\s+карте){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:[ /]+[A-Z][A-Z'’-]+){1,3})"
    r"(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_PERSONAL_ADDRESS = re.compile(
    r"\b(?:адрес\s+(?:физлица|клиента|заявителя)|"
    r"место\s+(?:регистрации|жительства)(?:\s+заявителя)?|"
    r"адрес\s+проживания|регистрация|я\s+живу)\b",
    re.IGNORECASE,
)
_ADDRESS_COUNTRY = re.compile(r"\b(?:Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY = re.compile(
    rf"\b(?:город(?:е)?|г\.){_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}?)(?=\s*(?:[,;]|\s+на\s+улиц))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:улиц(?:а|е)|ул\.|(?:проспект|шоссе)){_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}?)(?=\s*[,;])|"
    rf"(?P<prefix>{_WORD})\s+(?:проспект|шоссе)(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[A-ZА-ЯЁ]?)(?=\s*[,;.]|$)", re.IGNORECASE)
_FLAT = re.compile(rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)
_PUBLIC_EMAIL = re.compile(
    r"^(?:tender|newsdesk|editor|procurement|media|press|sales|support|info|jobs?|security)@",
    re.IGNORECASE,
)
_PUBLIC_MAIL_CONTEXT = re.compile(
    r"\b(?:общий\s+ящик|для\s+закупок|редакционные\s+запросы)\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.96, source, priority)


def _near(text: str, start: int, end: int, pattern: re.Pattern[str], radius: int = 100) -> bool:
    return pattern.search(text[max(0, start - radius) : min(len(text), end + radius)]) is not None


def _valid_numeric_date(match: re.Match[str]) -> bool:
    try:
        if match.group("year"):
            datetime(
                int(match.group("year")),
                int(match.group("month_y")),
                int(match.group("day_y")),
            )
        else:
            datetime(int(match.group("year_d")), int(match.group("month")), int(match.group("day")))
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
        weights_11 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        weights_12 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        check_11 = sum(a * b for a, b in zip(digits[:10], weights_11, strict=True)) % 11 % 10
        check_12 = sum(a * b for a, b in zip(digits[:11], weights_12, strict=True)) % 11 % 10
        return (check_11, check_12) == (digits[10], digits[11])
    return False


def _new_candidates(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span("value")
            words = match.group("value").split()
            has_patronymic = any(_INFLECTED_PATRONYMIC.search(word) for word in words[1:])
            if has_patronymic and not _near(text, start, end, _CULTURAL):
                yield _entity(text, "PERSON", start, end, "person_syntax_v3_3", 82)

    for match in _PERSON_INN_RE.finditer(text):
        start, end = match.span("value")
        if _valid_inn(match.group("value")):
            yield _entity(text, "INN", start, end, "personal_inn_v3_3", 100)
    for match in _PASSPORT_COMPACT_PERSONAL.finditer(text):
        start, end = match.span("value")
        yield _entity(text, "PASSPORT_RF", start, end, "passport_compact_v3_3", 97)

    for match in _DIVISION_RE.finditer(text):
        context_ok = _near(text, *match.span(), _DIVISION_LABEL, radius=55) or _near(
            text, *match.span(), _PASSPORT_NEAR, radius=80
        )
        if (
            context_ok
            and not _near(text, *match.span(), _LOGISTICS)
            and not _near(text, *match.span(), _DOC_CUE)
        ):
            yield _entity(text, "DIVISION_CODE", *match.span(), "division_context_v3_3", 97)

    for match in _NUMERIC_DATE.finditer(text):
        if not _valid_numeric_date(match) or _near(text, *match.span(), _DOC_CUE):
            continue
        if _near(text, *match.span(), _BIRTH_CUE, radius=75):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_3", 97)
        elif _near(text, *match.span(), _ISSUE_CUE, radius=90) or _near(
            text, *match.span(), _PASSPORT_NEAR, radius=100
        ):
            yield _entity(text, "PASSPORT_ISSUE_DATE", *match.span(), "issue_context_v3_3", 97)
    for match in _WORD_DATE.finditer(text):
        if _near(text, *match.span(), _DOC_CUE):
            continue
        if _near(text, *match.span(), _BIRTH_CUE, radius=75):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_words_v3_3", 97)
        elif _near(text, *match.span(), _ISSUE_CUE, radius=90):
            yield _entity(text, "PASSPORT_ISSUE_DATE", *match.span(), "issue_words_v3_3", 97)
    for match in _TEXT_DATE.finditer(text):
        if _near(text, *match.span(), _DOC_CUE):
            continue
        if _near(text, *match.span(), _BIRTH_CUE, radius=75):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_text_v3_3", 97)
        elif _near(text, *match.span(), _ISSUE_CUE, radius=90):
            yield _entity(text, "PASSPORT_ISSUE_DATE", *match.span(), "issue_text_v3_3", 97)

    for pattern in (_BIRTHPLACE_LABEL, _BIRTHPLACE_PROSE, _BIRTHPLACE_AFTER_DATE):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            preceded_by_birth = pattern is not _BIRTHPLACE_AFTER_DATE or _near(
                text, start, end, _BIRTH_CUE, radius=80
            )
            if preceded_by_birth and not re.match(
                r"(?:указан|заполнен|отсутств)", match.group("value"), re.IGNORECASE
            ):
                yield _entity(text, "PLACE_OF_BIRTH", start, end, "birthplace_v3_3", 94)
    for match in _CITIZENSHIP_PROSE.finditer(text):
        start, end = match.span("value")
        yield _entity(text, "CITIZENSHIP", start, end, "citizenship_v3_3", 94)
    for pattern in (_ISSUER_RE, _INLINE_ISSUER_RE):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            yield _entity(text, "PASSPORT_ISSUER", start, end, "issuer_v3_3", 96)
    for pattern in (_LICENSE_RE, _LICENSE_SERIES_RE):
        for match in pattern.finditer(text):
            start, end = match.span("value")
            yield _entity(text, "DRIVER_LICENSE_RF", start, end, "driver_license_v3_3", 98)
    for match in _CVV_RE.finditer(text):
        if not _near(text, *match.span(), _DOC_CUE):
            start, end = match.span("value")
            yield _entity(text, "CVV", start, end, "security_code_v3_3", 97)
    for match in _CARDHOLDER_RE.finditer(text):
        start, end = match.span("value")
        yield _entity(text, "CARDHOLDER_NAME", start, end, "cardholder_v3_3", 96)

    if _PERSONAL_ADDRESS.search(text):
        anchor = _PERSONAL_ADDRESS.search(text)
        assert anchor is not None
        address_text = text[anchor.end() :]
        address_offset = anchor.end()
        for match in _ADDRESS_COUNTRY.finditer(address_text):
            start, end = match.span()
            yield _entity(
                text,
                "ADDRESS_COUNTRY",
                address_offset + start,
                address_offset + end,
                "address_v3_3",
                92,
            )
        for match in _POSTCODE.finditer(address_text):
            start, end = match.span()
            yield _entity(
                text,
                "ADDRESS_POSTAL_CODE",
                address_offset + start,
                address_offset + end,
                "address_v3_3",
                92,
            )
        for entity_type, pattern in (
            ("ADDRESS_CITY", _CITY),
            ("ADDRESS_STREET", _STREET),
            ("ADDRESS_HOUSE", _HOUSE),
            ("ADDRESS_APARTMENT", _FLAT),
        ):
            for match in pattern.finditer(address_text):
                group = (
                    "prefix"
                    if entity_type == "ADDRESS_STREET" and match.groupdict().get("prefix")
                    else "value"
                )
                start, end = match.span(group)
                yield _entity(
                    text,
                    entity_type,
                    address_offset + start,
                    address_offset + end,
                    "address_v3_3",
                    92,
                )


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


def _suppressed_public_email(text: str, entity: DetectedEntity) -> bool:
    return entity.entity_type == "EMAIL" and bool(
        _PUBLIC_EMAIL.search(entity.text)
        or _near(text, entity.start, entity.end, _PUBLIC_MAIL_CONTEXT)
    )


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with v3.2 suppression and broader semantic recognizers."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    baseline = [item for item in detect_v3_2(text) if not _suppressed_public_email(text, item)]
    return _merge([*baseline, *_new_candidates(text)])
