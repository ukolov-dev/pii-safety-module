"""Candidate v3.27: owned-record grammars and clause-local negative evidence.

The candidate extends v3.26 with reusable Russian document grammars.  It does
not depend on benchmark literals: additions describe ownership phrases,
address records, inflected full names and reordered document fields.  A final
clause-local policy removes identifiers that belong to organisations, public
contacts, examples or technical objects.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from .detector_v3_26 import detect as detect_v3_26
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_CAP = r"(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,})(?:-(?:[А-ЯЁ][а-яё]+|[А-ЯЁ]{2,}))*"
_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_CAP}(?:\s+{_CAP}){{2}}"
_CITY = rf"{_CAP}(?:\s+{_CAP})?"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[-./](?:1[0-2]|0?[1-9])[-./](?:19|20)\d{2}"

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


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


_OWNED_PERSON = _rx(
    rf"\b(?:"
    rf"(?:\w+\s+){{0,2}}(?:выплат\w*|возмещен\w*)\s+(?:назначен\w*|причита\w*)|"
    rf"анкет\w*\s+(?:заполнил\w*|подписал\w*)|"
    rf"обращен\w*\s+(?:зарегистрирован\w*\s+)?от|"
    rf"пациент\w*(?:\s+является)?|"
    rf"договор\w*(?:\s+заключен\w*)?\s+с|"
    rf"адресован\w*|"
    rf"получател\w*(?:\s+является)?|"
    rf"собственник\w*(?:\s+является)?"
    rf")[^.;:\n]{{0,28}}?(?P<value>(?-i:{_NAME3}))\b"
)

_PASSPORT_REORDERED = (
    _rx(
        r"(?P<value>\bсерия\s+\d{4}\s*(?:,|и)\s*"
        r"(?:номер\s+паспорта|паспорт\s*(?:№|N|number)?)\s+\d{6})"
    ),
    _rx(
        r"(?P<value>\bномер\s+паспорта\s+\d{6}\s*(?:,|и)\s*"
        r"серия\s+\d{4})"
    ),
)

_LICENSE = _rx(
    r"\b(?:номер\s+)?(?:В\s*[/.-]?\s*У|водител\w*\s+"
    r"(?:прав\w*|удостоверен\w*))[^.;\n\d]{0,28}"
    r"(?P<value>\d{2}\s*\d{2}[- ]\d{6})(?!\d)"
)
_LICENSE_SERIES = _rx(
    r"\b(?:удостоверен\w*\s+водител\w*|водител\w*\s+"
    r"удостоверен\w*)[^.;\n]{0,35}?\bсерия\s+"
    r"(?P<value>\d{2}\s+\d{2}\s*(?:№|N|number)\s*\d{6})(?!\d)"
)
_BIRTH_DATE = _rx(
    rf"\b(?:дат\w*\s+рожд\w*|рожден\w*(?:\s+страховател\w*)?|"
    rf"появил\w*\s+на\s+свет|"
    rf"родил\w*)[^.;\n\d]{{0,35}}(?P<value>{_DATE})(?!\d)"
)
_BIRTH_DATE_ALIASES = _rx(
    rf"\b(?:DOB(?:\s+физлиц\w*)?|д\s*/\s*р(?:\s+заёмщик\w*)?)"
    rf"\s*[:=-]?\s*(?P<value>{_DATE})(?!\d)"
)
_BIRTH_DATE_WORDS = _rx(
    r"\b(?:д(?:ень|нём)\s+рожден\w*|появил\w*\s+на\s+свет)"
    r"[^.;\n\d]{0,45}(?P<value>(?:[12]?\d|3[01])\s+"
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
    r"\s+(?:19|20)\d{2}\s+(?:г\.|года))"
)
_ISSUE_DATE = _rx(
    rf"\b(?:паспорт|документ|выдан\w*)\b[^\n]{{0,145}}?"
    rf"\b(?:дата|когда)\s*[:=-]?\s*(?P<value>{_DATE})(?!\d)"
)
_ISSUE_DATE_BEFORE_ORG = _rx(
    rf"\bвыдан\w*\s+докумен\w*[^.;\n]{{0,25}}?"
    rf"(?P<value>{_DATE})(?!\d)[^.;\n]{{0,80}}\b(?:ОМВД|УМВД|УФМС|МВД)\b"
)
_ISSUE_DATE_AFTER_ORG = _rx(
    rf"\b(?:выдан\w*\s+)?(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b"
    rf"[^\n]{{0,110}}?(?P<value>{_DATE})(?!\d)"
)
_ISSUE_DATE_STRUCTURED = _rx(
    rf"\bдокумент\w*\s+(?:владел\w*|клиент\w*|физлиц\w*)"
    rf"[\s\S]{{0,180}}?\b(?:когда|дата\s+выдач\w*)\s*[:=-]?\s*"
    rf"(?P<value>{_DATE})(?!\d)"
)

_ADDRESS_OWNER = _rx(
    r"\b(?:домашн\w*\s+адрес\w*|"
    r"адрес\w*\s+(?:регистрац\w*|проживан\w*|клиент\w*)|"
    r"мест\w*\s+жительств\w*|"
    r"доставк\w*\s+домой|для\s+доставк\w*\s+домой|"
    r"доставк\w*\s+физлиц\w*|дом\s+человек\w*)\b"
)
_COUNTRY_VALUE = _rx(r"\b(?P<value>РФ|Россия|Российская\s+Федерация)\b")
_POSTCODE_VALUE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY_AFTER_POSTCODE = re.compile(
    rf"(?<!\d)\d{{6}}\s*,\s*(?:г(?:ород)?\.?\s*)?"
    rf"(?P<value>{_CITY})(?=\s*,)"
)
_CITY_FIELD = _rx(
    rf"\b(?:город\s+проживания|домашний\s+город)\s*[:=-]?\s*"
    rf"(?P<value>(?-i:{_CITY}))(?=\s*(?:[,;.\n]|и\s+улиц))"
)
_CITY_AFTER_COUNTRY = _rx(
    rf"\b(?:РФ|Россия|Российская\s+Федерация)\s*,\s*"
    rf"(?:\d{{6}}\s*,\s*)?(?:г(?:ород)?\.?\s*)?"
    rf"(?P<value>(?-i:{_CITY}))(?=\s*,)"
)
_CITY_BEFORE_STREET = _rx(
    rf"(?:^|:\s*)(?:\d{{6}}\s*,\s*)?(?:г(?:ород)?\.?\s*)?"
    rf"(?P<value>(?-i:{_CITY}))(?=\s*,\s*улиц)"
)
_STREET_VALUE = _rx(
    rf"\b(?:улиц\w*|ул\.)\s+(?P<value>{_WORD}(?:\s+{_WORD}){{0,2}})(?=\s*(?:,|;|\.|$))"
)
_HOUSE_VALUE = _rx(r"\b(?:дом|д\.)\s*(?P<value>\d{1,4}[А-ЯЁA-Z]?)(?!\d)")
_FLAT_VALUE = _rx(r"\b(?:квартир\w*|кв\.)\s*(?P<value>\d{1,5})(?!\d)")

_OWNED_COUNTRY = _rx(
    r"\b(?:жив\w*|прожива\w*|находится)\s+в\s+стран\w*\s+"
    r"(?P<value>РФ|Россия|Российская\s+Федерация)\b"
)
_OWNED_POSTCODE = _rx(
    r"\bиндекс\b[^.;\n]{0,70}?\b(?:его|её|клиент\w*|домашн\w*|"
    r"почтов\w*\s+отделен\w*)[^.;\n\d]{0,45}(?P<value>\d{6})(?!\d)"
)
_OWNED_HOUSE = _rx(
    r"\b(?:клиент\w*|заявител\w*|он|она)\s+(?:жив\w*|прожива\w*)\s+в\s+"
    r"доме\s+(?P<value>\d{1,4}[А-ЯЁA-Z]?)(?!\d)"
)
_OWNED_FLAT = _rx(
    r"\bдоставк\w*[^.;\n]{0,70}?\b(?:ему|ей|к\s+нему|к\s+ней|"
    r"клиент\w*|физлиц\w*)[^.;\n]{0,45}?\bквартир\w*\s+"
    r"(?P<value>\d{1,5})(?!\d)"
)
_OWNED_CITY = _rx(
    rf"\b(?:я\s+живу|клиент\w*\s+жив\w*|заявител\w*\s+жив\w*)\s+в\s+"
    rf"(?P<value>(?-i:{_CAP}(?:\s+{_CAP})?))(?=\s*(?:[,;.]|$))"
)
_OWNED_COUNTRY_PHRASE = _rx(
    r"\bстран\w*\s+(?:мо\w*\s+)?проживан\w*[^.;\n]{0,45}?"
    r"(?P<value>Российская\s+Федерация|Россия|РФ)\b"
)
_OWNED_EMAIL = _rx(
    r"\b(?:ящик|почт\w*|адрес\w*)\s+(?:принадлежит|автор\w*)"
    r"[^.;\n]{0,65}?(?P<value>[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})"
)
_BANK_FORM_CVV = _rx(
    r"\bбанковск\w*\s+анкет\w*[\s\S]{0,220}?\bCVV2?\s*[:=-]?\s*"
    r"(?P<value>\d{3})(?!\d)"
)
_FOLLOWUP_ADDRESS_RECORD = _rx(
    rf"\b(?:мо\w*|личн\w*|домашн\w*)\s+адрес\w*[^.!?\n]{{0,45}}[.!?]\s*"
    rf"(?:сообща\w*|указыва\w*|данные)\s*:\s*"
    rf"(?P<city>(?-i:{_CITY}))\s*,\s*(?:улиц\w*|ул\.)\s+"
    rf"(?P<street>{_WORD}(?:\s+{_WORD}){{0,2}})\s*,\s*(?:дом|д\.)\s*"
    r"(?P<house>\d{1,4}[А-ЯЁA-Z]?)\s*,\s*(?:квартир\w*|кв\.)\s*"
    r"(?P<flat>\d{1,5})(?!\d)"
)

_PERSONAL = _rx(
    r"\b(?:клиент\w*|заявител\w*|граждан\w*|физлиц\w*|пациент\w*|"
    r"страховател\w*|получател\w*|владел\w*|его|её|ему|ей|"
    r"личн\w*|домашн\w*|доставк\w*\s+домой)\b"
)
_PUBLIC = _rx(
    r"\b(?:организац\w*|юрлиц\w*|контрагент\w*|партнёр\w*|партнер\w*|"
    r"поставщик\w*|бухгалтер\w*|автоуведомлен\w*|платформ\w*|редакц\w*|"
    r"журнал\w*|стать\w*|офис\w*|компан\w*|фирм\w*|публичн\w*|"
    r"ресторан\w*|фонд\w*|юридическ\w*\s+адрес\w*|"
    r"служебн\w*|постамат\w*|пункт\w*\s+выдач\w*)\b"
)
_TECHNICAL = _rx(
    r"\b(?:SDK|DEMO|sample|fixture|пример\w*|тестов\w*|руководств\w*|"
    r"разработчик\w*|коробк\w*|ящик\w*|агрегат\w*|оборудован\w*|"
    r"установк\w*|издели\w*|промышленн\w*|зон\w*|макет\w*|"
    r"парти\w*|детал\w*|подсказк\w*|бюджетн\w*\s+стат\w*|"
    r"не\s+учитывать|валидн\w*\s+PAN)\b"
)
_NEGATED_PERSONAL = _rx(
    r"\b(?:не\s+(?:физлиц\w*|клиент\w*|заявител\w*|личн\w*)|"
    r"не\s+(?:принадлежит|является)\s+(?:физлиц\w*|клиент\w*|личн\w*))\b"
)
_ROLE_EMAIL = re.compile(
    r"^(?:vendors?|notify|notifications?|accounting|editor|editorial|journal|billing|shift|"
    r"archive|metrics|office|info|support|sales|admin|noreply|no-reply)@",
    re.I,
)
_FOLLOWING_PUBLIC_PHONE = _rx(
    r"\b(?:это|оказался|является)\s+номер\s+"
    r"(?:офис\w*|организац\w*|работодател\w*)"
)


def _entity(
    text: str, entity_type: str, span: tuple[int, int], source: str, priority: int = 310
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.999, source, priority)


def _valid_date(value: str) -> bool:
    day, month, year = (int(item) for item in re.split(r"[-./]", value))
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _record_end(text: str, start: int, maximum: int = 320) -> int:
    end = min(len(text), start + maximum)
    stops = [match.start() for match in re.finditer(r"\n|[.!?](?=\s+[А-ЯЁA-Z]|$)", text[start:end])]
    stops = [start + position for position in stops]
    return min(stops) if stops else end


def _extra_candidates(text: str) -> Iterator[DetectedEntity]:
    normalized = text.translate(_NORMALIZE)
    for match in _OWNED_PERSON.finditer(normalized):
        yield _entity(text, "PERSON", match.span("value"), "owned_person_v3_27")
    for pattern in _PASSPORT_REORDERED:
        for match in pattern.finditer(normalized):
            yield _entity(text, "PASSPORT_RF", match.span("value"), "passport_reordered_v3_27")
    for pattern, entity_type, source in (
        (_LICENSE, "DRIVER_LICENSE_RF", "license_family_v3_27"),
        (_LICENSE_SERIES, "DRIVER_LICENSE_RF", "license_series_v3_27"),
        (_BIRTH_DATE, "BIRTH_DATE", "birth_date_family_v3_27"),
        (_BIRTH_DATE_ALIASES, "BIRTH_DATE", "birth_date_alias_v3_27"),
        (_BIRTH_DATE_WORDS, "BIRTH_DATE", "birth_date_words_v3_27"),
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_family_v3_27"),
        (_ISSUE_DATE_BEFORE_ORG, "PASSPORT_ISSUE_DATE", "issue_date_record_v3_27"),
        (_ISSUE_DATE_AFTER_ORG, "PASSPORT_ISSUE_DATE", "issue_after_org_v3_27"),
        (_ISSUE_DATE_STRUCTURED, "PASSPORT_ISSUE_DATE", "issue_structured_v3_27"),
    ):
        for match in pattern.finditer(normalized):
            value = text[slice(*match.span("value"))]
            if entity_type.endswith("DATE") and re.fullmatch(_DATE, value):
                if not _valid_date(value):
                    continue
            yield _entity(text, entity_type, match.span("value"), source)

    for anchor in _ADDRESS_OWNER.finditer(normalized):
        end = _record_end(normalized, anchor.end())
        fragment = normalized[anchor.start() : end]
        base = anchor.start()
        for pattern, entity_type in (
            (_COUNTRY_VALUE, "ADDRESS_COUNTRY"),
            (_POSTCODE_VALUE, "ADDRESS_POSTAL_CODE"),
            (_CITY_AFTER_POSTCODE, "ADDRESS_CITY"),
            (_CITY_AFTER_COUNTRY, "ADDRESS_CITY"),
            (_CITY_FIELD, "ADDRESS_CITY"),
            (_CITY_BEFORE_STREET, "ADDRESS_CITY"),
            (_STREET_VALUE, "ADDRESS_STREET"),
            (_HOUSE_VALUE, "ADDRESS_HOUSE"),
            (_FLAT_VALUE, "ADDRESS_APARTMENT"),
        ):
            for match in pattern.finditer(fragment):
                start, stop = match.span("value")
                yield _entity(
                    text,
                    entity_type,
                    (base + start, base + stop),
                    "owned_address_record_v3_27",
                )

    for pattern, entity_type in (
        (_CITY_FIELD, "ADDRESS_CITY"),
        (_OWNED_COUNTRY, "ADDRESS_COUNTRY"),
        (_OWNED_COUNTRY_PHRASE, "ADDRESS_COUNTRY"),
        (_OWNED_POSTCODE, "ADDRESS_POSTAL_CODE"),
        (_OWNED_HOUSE, "ADDRESS_HOUSE"),
        (_OWNED_FLAT, "ADDRESS_APARTMENT"),
        (_OWNED_CITY, "ADDRESS_CITY"),
        (_OWNED_EMAIL, "EMAIL"),
        (_BANK_FORM_CVV, "CVV"),
    ):
        for match in pattern.finditer(normalized):
            yield _entity(text, entity_type, match.span("value"), "owned_field_v3_27")

    for match in _FOLLOWUP_ADDRESS_RECORD.finditer(normalized):
        for group, entity_type in (
            ("city", "ADDRESS_CITY"),
            ("street", "ADDRESS_STREET"),
            ("house", "ADDRESS_HOUSE"),
            ("flat", "ADDRESS_APARTMENT"),
        ):
            yield _entity(
                text,
                entity_type,
                match.span(group),
                "followup_address_record_v3_27",
            )


def _clause(text: str, start: int, end: int) -> str:
    left = max(text.rfind(";", 0, start), text.rfind("\n", 0, start), 0)
    stops = [
        position
        for mark in (";", "\n")
        if (position := text.find(mark, end)) >= 0
    ]
    right = min(stops) if stops else len(text)
    return text[left:right]


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    clause = _clause(text, entity.start, entity.end)
    window = text[max(0, entity.start - 170) : min(len(text), entity.end + 170)]
    personal = _PERSONAL.search(clause) is not None and _NEGATED_PERSONAL.search(clause) is None
    public = _PUBLIC.search(clause) is not None
    technical = _TECHNICAL.search(clause) is not None
    if entity.entity_type == "EMAIL":
        return _ROLE_EMAIL.search(entity.text) is not None or (public and not personal)
    if entity.entity_type in {"BANK_CARD", "CVV", "PIN"}:
        return technical
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "DRIVER_LICENSE_RF"}:
        return technical
    if entity.entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"}:
        return technical
    if entity.entity_type == "INN":
        return (public and not personal) or technical
    if entity.entity_type == "PHONE_RF" and _FOLLOWING_PUBLIC_PHONE.search(window):
        return True
    if entity.entity_type.startswith("ADDRESS_") or entity.entity_type == "PHONE_RF":
        return (public and not personal) or technical
    if entity.entity_type == "PERSON" and _TECHNICAL.search(window):
        return True
    return False


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Detect PII with owned-record grammars and clause-local suppression."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = detect_v3_26(text)
    if len(text) >= 100_000:
        return inherited
    merged = _merge([*inherited, *_extra_candidates(text)])
    return [entity for entity in merged if not _suppressed(text, entity)]
