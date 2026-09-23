"""Production detector v3.9: ownership-first recognizers and negative semantic gates.

The proposal composes v3.7, adds reusable Russian label/grammar variants, and
filters inherited entities when the surrounding text explicitly identifies a
public, shared, template, pickup-point, or non-person value. Production is not
modified.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime

from .detector_v3_7 import detect as detect_v3_7
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_SEP = r"\s*(?:[:=№/]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"

_PERSON_RE = re.compile(
    rf"\b(?:акт|договор|заявление)\s+подписан\w*{_SEP}"
    rf"(?P<signed>{_NAME3})\b|"
    rf"\bавтор\s+(?:обращения|заявления|жалобы){_SEP}"
    rf"(?P<author>{_NAME3})\b|"
    rf"\bводитель{_SEP}(?P<driver>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)

_CARD_RE = re.compile(r"(?<!\d)\d(?:[/ .-]?\d){12,18}(?!\d)")
_PERSONAL_CARD = re.compile(
    r"\b(?:личн\w*(?:\s+\w+){0,2}\s+карт\w*|"
    r"банковск\w*\s+карт\w*\s+клиент\w*|"
    r"данные\s+моей\s+карты)\b",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\bкод\s+(?:выдавшего\s+органа|органа,?\s+выдавшего\s+паспорт)"
    rf"{_SEP}(?P<value>\d{{3}}[- /]\d{{3}})(?!\d)",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"(?<!\d)(?:(?P<year>(?:19|20)\d{2})[./-](?P<month_y>0?[1-9]|1[0-2])[./-]"
    r"(?P<day_y>0?[1-9]|[12]\d|3[01])|"
    r"(?P<day>0?[1-9]|[12]\d|3[01])[./-](?P<month>0?[1-9]|1[0-2])[./-]"
    r"(?P<year_d>(?:19|20)\d{2}))(?!\d)"
)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:рождение(?:\s+\w+)?|д\s*[./]\s*р|дата\s+рождения|"
    r"родился|родилась|рождён|рождена)\b",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\bместо\s+рождения(?:\s+(?:граждан|заявител|клиент)\w*)?{_SEP}"
    rf"(?P<label>(?:(?:рабочий\s+)?посёлок|село|деревня|станица|город)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_END}|"
    rf"\bродом\s+из{_SEP}(?P<origin>(?:города|села|деревни)\s+{_WORD}){_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\bгражданская\s+принадлежность(?:\s+\w+)?{_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}}){_END}",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    r"\bпаспорт\s+оформлен\w*\s+(?P<value>(?:ОМВД|УМВД|УФМС|ГУ\s+МВД)"
    r"[^;\n]*?)(?=\s*(?:\.\s*$|$))",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\bводительские\s+права\s+(?:имеют\s+)?реквизиты{_SEP}"
    r"(?P<value>\d{2}[ -]?\d{2}[- ]?\d{6})(?!\d)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    rf"\b(?:личн\w*\s+)?(?:PIN|ПИН)(?:-код)?"
    rf"(?:\s+(?:клиент\w*|владелец|владельц\w*|держател\w*))?"
    rf"{_SEP}(?P<value>\d{{4}})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:CARDHOLDER\s*/\s*владелец\s+пластика|имя(?:\s+на\s+карте)?){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;./]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:адрес\s+проживания\s+(?:физлица|клиента|гражданина)|"
    r"доставить\s+(?:гражданину|получателю)|мой\s+дом\s+находится\s+в)\b",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"(?P<first>{_WORD})(?=\s*[,;])|"
    rf"(?P<before_street>{_WORD})(?=\s*[,;]\s*(?:улица|ул\.|(?:на\s+)?проспект))",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:улица|ул\.|(?:на\s+)?проспекте?|переулок|пер\.){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;.]|$)", re.IGNORECASE)
_FLAT_RE = re.compile(rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)

_PUBLIC_PHONE = re.compile(
    r"\b(?:диспетчерск\w*\s+служб\w*|ресепшен\w*(?:\s+бизнес-центр\w*)?|"
    r"клиник\w*\s+публикует\s+номер|контакт\w*\s+кинотеатр\w*|"
    r"общ\w*\s+номер\s+подразделени\w*|не\s+принадлежит\s+абонент\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:invoices?|quality|team|cinema|pressroom|reception|dispatch|billing|"
    r"accounts?|contact|service)@",
    re.IGNORECASE,
)
_SHARED_EMAIL_CONTEXT = re.compile(
    r"\b(?:корпоративн\w*\s+почт\w*|служба\s+качества|"
    r"счета\s+поставщик\w*|пресс-релиз|кинотеатр\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:адрес\s+библиотек\w*|пункт\s+выдачи|"
    r"не\s+адрес\s+получател\w*)\b",
    re.IGNORECASE,
)
_NON_PERSON_CODE = re.compile(
    r"\b(?:детал\w*|насос\w*|маркировк\w*|коробк\w*|складск\w*\s+код)\b",
    re.IGNORECASE,
)
_DOCUMENTATION = re.compile(
    r"\b(?:инструкци\w*|документаци\w*|подсказк\w*\s+форм\w*|"
    r"шаблон\w*|пример\w*|условн\w*\s+(?:PIN|ПИН|код))\b",
    re.IGNORECASE,
)
_TEMPLATE_PHONE = re.compile(r"\b(?:макет|шаблон|пример)\w*\s+телефон\w*\b", re.IGNORECASE)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int = 110
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _near(text: str, entity: DetectedEntity, pattern: re.Pattern[str], radius: int = 150) -> bool:
    window = text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]
    return pattern.search(window) is not None


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


def _is_repeated_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits[0] in "78":
        digits = digits[1:]
    return len(digits) == 10 and len(set(digits)) == 1


def _keep_inherited(text: str, entity: DetectedEntity) -> bool:
    if entity.entity_type == "PHONE_RF":
        return not (
            _is_repeated_phone(entity.text)
            or _near(text, entity, _PUBLIC_PHONE)
            or _near(text, entity, _TEMPLATE_PHONE)
        )
    if entity.entity_type == "EMAIL":
        return not (
            _SHARED_EMAIL.search(entity.text) or _near(text, entity, _SHARED_EMAIL_CONTEXT)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not _near(text, entity, _PUBLIC_ADDRESS)
    if entity.entity_type in {"CVV", "PASSPORT_RF", "DIVISION_CODE"}:
        return not _near(text, entity, _NON_PERSON_CODE)
    return True


def _new_candidates(text: str) -> Iterator[DetectedEntity]:
    for match in _PERSON_RE.finditer(text):
        group = next(name for name, value in match.groupdict().items() if value)
        value = match.group(group)
        if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
            yield _entity(text, "PERSON", *match.span(group), "person_ownership_v3_9")

    for match in _CARD_RE.finditer(text):
        if _valid_luhn(match.group()) and _PERSONAL_CARD.search(
            text[max(0, match.start() - 80) : match.start()]
        ):
            yield _entity(text, "BANK_CARD", *match.span(), "personal_card_v3_9")

    for match in _DIVISION_RE.finditer(text):
        yield _entity(text, "DIVISION_CODE", *match.span("value"), "division_label_v3_9")

    for match in _DATE_RE.finditer(text):
        window = text[max(0, match.start() - 100) : match.end()]
        if (
            _valid_date(match)
            and _BIRTH_CONTEXT.search(window)
            and not _DOCUMENTATION.search(window)
        ):
            yield _entity(text, "BIRTH_DATE", *match.span(), "birth_context_v3_9")

    for pattern, entity_type in (
        (_BIRTHPLACE_RE, "PLACE_OF_BIRTH"),
        (_CITIZENSHIP_RE, "CITIZENSHIP"),
        (_ISSUER_RE, "PASSPORT_ISSUER"),
        (_LICENSE_RE, "DRIVER_LICENSE_RF"),
        (_PIN_RE, "PIN"),
        (_CARDHOLDER_RE, "CARDHOLDER_NAME"),
    ):
        for match in pattern.finditer(text):
            window = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)]
            if _DOCUMENTATION.search(window):
                continue
            group = next(name for name, value in match.groupdict().items() if value)
            yield _entity(text, entity_type, *match.span(group), "semantic_field_v3_9")

    for anchor in _ADDRESS_ANCHOR.finditer(text):
        address = text[anchor.end() :]
        offset = anchor.end()
        for entity_type, pattern, groups in (
            ("ADDRESS_COUNTRY", _COUNTRY_RE, ()),
            ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, ()),
            ("ADDRESS_STREET", _STREET_RE, ("value",)),
            ("ADDRESS_CITY", _CITY_RE, ("first", "before_street")),
            ("ADDRESS_HOUSE", _HOUSE_RE, ("value",)),
            ("ADDRESS_APARTMENT", _FLAT_RE, ("value",)),
        ):
            for match in pattern.finditer(address):
                selected_group = next((name for name in groups if match.group(name)), None)
                start, end = match.span(selected_group) if selected_group else match.span()
                yield _entity(
                    text,
                    entity_type,
                    offset + start,
                    offset + end,
                    "personal_address_v3_9",
                    109,
                )


def _merge(candidates: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(candidates)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with v3.7 plus generalized ownership and suppression rules."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = [entity for entity in detect_v3_7(text) if _keep_inherited(text, entity)]
    return _merge([*inherited, *_new_candidates(text)])
