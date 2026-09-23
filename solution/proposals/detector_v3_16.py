"""Candidate v3.16: precision-gated semantic extensions over production v3.13."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date

from app.detection.detector_v3_13 import detect as production_detect
from app.detection.models import DetectedEntity

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"
_DATE = (
    r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{2}[-/.](?:1[0-2]|0?[1-9])[-/.](?:3[01]|[12]\d|0?[1-9])"
)
_PATRONYMIC = re.compile(
    r"(?:(?:ович|евич|ич)(?:а|я|у|е|ем|ом)?|"
    r"(?:овн|евн|ичн)(?:а|я|у|е|ой|ы)?)$",
    re.IGNORECASE,
)

_PERSON = (
    re.compile(
        rf"\b(?:получил\w*|дали|взяли|запросили)\s+согласие\s+от\s+"
        rf"(?P<value>{_NAME3})\b(?=[^.;\n]{{0,45}}\b(?:данн\w*|обработк\w*))",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:посылк\w*|заказ\w*|документ\w*)\s+"
        rf"(?:забер[её]т|получит)\s+(?:сам(?:а|остоятельно)?\s+)?(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:получател\w*|представител\w*|доверител\w*|страховател\w*)"
        rf"(?:\s+\w+){{0,2}}\s+(?:является|стал\w*|назначен\w*)\s+"
        rf"(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:лицевой\s+сч[её]т|договор|полис|сертификат)\s+"
        rf"(?:оформлен|зарегистрирован)\s+на\s+(?P<value>{_NAME3})\b",
        re.IGNORECASE,
    ),
)

_PASSPORT_FIELDS = re.compile(
    r"\b(?P<value>серия\s+паспорта\s*[:=]?\s*\d{4}\s*[/;,]\s*"
    r"номер\s*[:=]?\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_BIRTH_DATE = re.compile(
    rf"\b(?:рождени[ея](?:\s+(?:клиента|заявителя|физлица))?\s+"
    rf"(?:указано|записано)(?:\s+как)?|д\.?\s*р\.?)\s*[:=—-]?\s*"
    rf"(?P<value>{_DATE})(?!\d)",
    re.IGNORECASE,
)
_BIRTHPLACE = (
    re.compile(
        rf"\bместо\s+(?:моего\s+)?рождения(?:\s+по\s+(?:паспорту|документу))?"
        rf"\s*[:—-]\s*(?P<value>(?:пос[её]лок|аул|хутор|станица|село|"
        rf"деревня|город|г\.)\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:заявител\w*|клиент\w*|граждан\w*)\s+родом\s+из\s+"
        rf"(?P<value>(?:пос[её]лка|аула|хутора|станицы|села|деревни|города|г\.)"
        rf"\s+{_WORD}(?:\s+{_WORD}){{0,3}}){_END}",
        re.IGNORECASE,
    ),
)
_ISSUER = re.compile(
    r"\b(?:паспорт|документ)\s+(?:оформил\w*|выдал\w*)\s+"
    r"(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС|ОТДЕЛ\s+(?:МВД|УФМС))\b[^,;\n]*?)"
    r"(?=\s*[,;]|\.\s*$|$)",
    re.IGNORECASE,
)
_ISSUE_DATE = (
    re.compile(
        rf"\bдат(?:а|ой)\s+выдачи\s+(?:паспорта|документа)\s+"
        rf"(?:является|считается)?\s*[:=—-]?\s*(?P<value>{_DATE})(?!\d)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:паспорт|документ)\b[^;\n]{{0,35}}\bвыдан\b[^;\n]{{0,80}}?\s"
        rf"(?P<value>{_DATE})(?=\s*[,;.]|$)",
        re.IGNORECASE,
    ),
)
_DIVISION = re.compile(
    r"\b(?:паспорт|документ)\b[^\n]{0,160}\b(?:код\s+)?подразделени[ея]\s*"
    r"[:=—-]?\s*(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:домашн\w*\s+адрес|точн\w*\s+адрес|адрес\s+(?:самого\s+)?"
    r"(?:заявителя|страхователя|клиента|получателя)|дом\s+заявителя|"
    r"доставить\s+\w+\s+домой|жив[её]т\s+в|адрес:\s*\d{6})\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b", re.I)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = (
    re.compile(
        rf"(?<![А-ЯЁа-яё])(?P<value>{_WORD})(?=\s*[,;|/]\s*(?:улица|ул\.|"
        rf"проспект|переулок|шоссе|набережная))",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:жив[её]т|находится)\s+(?:в|во)\s+(?P<value>{_WORD})(?=\s*[,;.])",
        re.IGNORECASE,
    ),
)
_STREET = re.compile(
    rf"\b(?:на\s+)?(?:улиц(?:а|е)|ул\.|проспект|переулок|шоссе|набережная)"
    rf"\s+(?P<value>{_WORD})(?=\s*[,;|/])",
    re.IGNORECASE,
)
_HOUSE = re.compile(
    r"\b(?:в\s+)?(?:дом(?:е)?|д\.)\s*(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;|/])",
    re.IGNORECASE,
)
_FLAT = re.compile(
    r"\b(?:в\s+)?(?:квартир(?:а|е)|кв\.)\s*(?P<value>\d+)(?=\s*[,;|/.]|$)",
    re.IGNORECASE,
)

_PUBLIC_CONTACT = re.compile(
    r"\b(?:выставочн\w*\s+центр\w*|корпоративн\w*\s+контакт|поддержк\w*|"
    r"секретар\w*\s+подразделени\w*|служебн\w*|робот\w*|ведомств\w*)\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:mailer|presscenter|supportdesk|expo|service|office|team|press|"
    r"support|help|info|hr|admin|noreply)@",
    re.IGNORECASE,
)
_NONPERSON_ADDRESS = re.compile(
    r"\b(?:адрес\s+(?:магазина|организации|работодателя)|пункт\w*\s+выдач\w*|"
    r"филиал\w*\s+банка|на\s+работу|получател\w*\s+там\s+не\s+жив[её]т|"
    r"домашн\w*\s+адрес\s+клиента\s+неизвестен)\b",
    re.IGNORECASE,
)
_SYNTHETIC = re.compile(
    r"\b(?:фиктивн\w*|заполнител\w*|тестов\w*|демонстрационн\w*|"
    r"макет\w*|пример\w*|образец\w*)\b",
    re.IGNORECASE,
)
_ADDRESS_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("ADDRESS_COUNTRY", (_COUNTRY,)),
    ("ADDRESS_POSTAL_CODE", (_POSTCODE,)),
    ("ADDRESS_CITY", _CITY),
    ("ADDRESS_STREET", (_STREET,)),
    ("ADDRESS_HOUSE", (_HOUSE,)),
    ("ADDRESS_APARTMENT", (_FLAT,)),
)


@dataclass(frozen=True, slots=True)
class NERSpan:
    label: str
    start: int
    end: int
    score: float


def _entity(
    text: str,
    entity_type: str,
    span: tuple[int, int],
    source: str,
    confidence: float = 0.998,
) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], confidence, source, 160)


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[-/.]", value)]
    year, month, day = parts if len(str(parts[0])) == 4 else parts[::-1]
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _valid_name(value: str) -> bool:
    parts = value.split()
    return len(parts) == 3 and any(_PATRONYMIC.search(item) for item in parts)


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    for pattern in _PERSON:
        for match in pattern.finditer(text):
            if _valid_name(match.group("value")):
                yield _entity(text, "PERSON", match.span("value"), "person_semantic_v3_16")
    for pattern, entity_type, source in (
        (_PASSPORT_FIELDS, "PASSPORT_RF", "passport_fields_v3_16"),
        (_BIRTH_DATE, "BIRTH_DATE", "birth_field_v3_16"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_action_v3_16"),
        (_DIVISION, "DIVISION_CODE", "division_context_v3_16"),
    ):
        for match in pattern.finditer(text):
            if entity_type == "BIRTH_DATE" and not _valid_date(match.group("value")):
                continue
            yield _entity(text, entity_type, match.span("value"), source)
    for patterns, entity_type, source in (
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_v3_16"),
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_v3_16"),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                if entity_type == "PASSPORT_ISSUE_DATE" and not _valid_date(
                    match.group("value")
                ):
                    continue
                yield _entity(text, entity_type, match.span("value"), source)
    if _ADDRESS_ANCHOR.search(text):
        for entity_type, address_patterns in _ADDRESS_PATTERNS:
            for pattern in address_patterns:
                for match in pattern.finditer(text):
                    value = match.group("value")
                    if entity_type == "ADDRESS_CITY" and not value[0].isupper():
                        continue
                    yield _entity(text, entity_type, match.span("value"), "address_v3_16")


def _ner_entities(text: str, spans: Sequence[NERSpan]) -> Iterator[DetectedEntity]:
    """Map optional model spans only when deterministic ownership evidence exists."""

    personal = _ADDRESS_ANCHOR.search(text) is not None
    mapping = {
        "PERSON": "PERSON",
        "CITY": "ADDRESS_CITY",
        "STREET": "ADDRESS_STREET",
        "HOUSE": "ADDRESS_HOUSE",
    }
    for span in spans:
        entity_type = mapping.get(span.label.upper())
        valid = 0 <= span.start < span.end <= len(text)
        if entity_type is None or span.score < 0.94 or not valid:
            continue
        value = text[span.start : span.end]
        if entity_type == "PERSON" and _valid_name(value):
            yield _entity(text, entity_type, (span.start, span.end), "ner_gated_v3_16", span.score)
        elif entity_type != "PERSON" and personal:
            yield _entity(text, entity_type, (span.start, span.end), "ner_gated_v3_16", span.score)


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


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    public = _PUBLIC_CONTACT.search(text) is not None
    if entity.entity_type == "PHONE_RF":
        return public or _SYNTHETIC.search(text) is not None
    if entity.entity_type == "EMAIL":
        return public or _ROLE_EMAIL.search(entity.text) is not None
    if entity.entity_type.startswith("ADDRESS_"):
        return _NONPERSON_ADDRESS.search(text) is not None
    return False


def detect(text: str, ner_spans: Sequence[NERSpan] = ()) -> list[DetectedEntity]:
    """Return production v3.13 plus gated semantic and optional NER candidates."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge(
            [*production_detect(text), *_supplemental(text), *_ner_entities(text, ner_spans)]
        )
        if not _suppressed(text, entity)
    ]
