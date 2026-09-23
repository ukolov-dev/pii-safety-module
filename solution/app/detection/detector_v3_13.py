"""Production detector v3.13: lightweight candidate detection plus mask policy.

`detect_candidates` discovers structured or strongly labelled values.
`should_mask` independently applies privacy/utility ownership gates. This keeps
the masking decision auditable and leaves a small interface for a future local
NER candidate source without adding a model or changing the masking API.

"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime

from .detector_v3_3 import detect as detect_v3_3
from .detector_v3_11 import detect as detect_v3_11
from .models import DetectedEntity

_SEP = r"\s*(?:[:=№/|]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"
_MONTH = (
    r"января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|"
    r"январь|февраль|март|апрель|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь"
)
_ADVANCED_TRIGGER_WORDS = (
    "представител", "застрахован", "получател", "подписант", "автор", "водител",
    "клиент", "заявител", "паспорт", "подразделени", "выдан", "рожд", "гражданств",
    "удостоверени", "права", "cvv", "cvc", "pin", "пин", "держател", "card holder",
    "владелец", "адрес", "прожива", "регистрац", "индекс", "город", "г.", "улиц",
    "ул.", "дом", "квартир",
)


@dataclass(frozen=True, slots=True)
class DetectionCandidate:
    """A detector proposal before the independent mask-policy decision."""

    entity: DetectedEntity
    evidence: str
    ownership: str


_PERSON_RE = re.compile(
    rf"\bпредставител\w*\s+назначен\w*{_SEP}"
    rf"(?P<representative>{_NAME3})\b|"
    rf"\bзастрахованн\w*{_SEP}(?P<insured>{_NAME3})\b|"
    rf"\bполучател\w*(?:\s+пособия|выплаты)?\s+"
    rf"(?:стала?|является){_SEP}(?P<recipient>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)
_PASSPORT_RE = re.compile(
    rf"\bпаспортные\s+данные(?:\s+(?:клиент|граждан)\w*)?{_SEP}"
    r"(?P<value>серия\s+\d{4}\s+(?:и\s+)?номер\s+\d{6})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\b(?:код\s+паспортного\s+подразделения|код){_SEP}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_CONTEXT = re.compile(
    r"\b(?:паспортн\w*|паспорт|документ\s+выдан|выдавший\s+орган|"
    r"кем\s+выдан|код\s+подразделения)\b",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    r"\b(?:кем\s+выдано?\s+(?:удостоверение|паспорт)|"
    r"документ\s+выдан|оформлен)\s*[:—-]?\s*"
    r"(?P<value>(?:ОМВД|УМВД|УФМС|ГУ\s+МВД)[^,;\n]*?)"
    r"(?=\s*(?:[,;]|(?:\d{2}[./-]\d{2}[./-]\d{4})|\.\s*$|$))",
    re.IGNORECASE,
)
_ISSUE_DATE_RE = re.compile(
    rf"\bдата\s+(?:фактической\s+)?выдачи\s+паспорта{_SEP}"
    r"(?P<value>\d{1,2}[./-]\d{1,2}[./-](?:19|20)\d{2})(?!\d)",
    re.IGNORECASE,
)
_BIRTH_NUMERIC_RE = re.compile(
    r"(?<!\d)(?P<value>(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:19|20)\d{2})(?!\d)"
)
_BIRTH_CONTEXT = re.compile(
    r"\b(?:дата|дате|дату)\s+рождения\b|\bрождён\b|\bродил\w*\b",
    re.IGNORECASE,
)
_BIRTH_TEXT_RE = re.compile(
    rf"\b(?:дата|дате|дату)\s+рождения(?:\s+\w+)?{_SEP}"
    rf"(?P<value>{_WORD}(?:\s+{_WORD})?\s+(?:{_MONTH})\s+(?:19|20)\d{{2}}\s+года){_END}",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\b(?:в\s+строке\s+[«\"]?место\s+рождения[»\"]?\s+написано|"
    rf"место\s+рождения\s+записано){_SEP}"
    rf"(?P<field>(?:аул|хутор|село|деревня|г\.)\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}|"
    rf"\b(?:появился|появилась)\s+на\s+свет[^;]{{0,55}}?\s+в{_SEP}"
    rf"(?P<prose>(?:г\.|городе|селе|деревне)\s+{_WORD}){_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\b(?:в\s+миграционной\s+анкете\s+)?гражданство(?:\s+лица)?"
    rf"(?:\s+указано\s+как)?{_SEP}(?P<value>РФ|Россия|Российская\s+Федерация){_END}",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\b(?:для\s+проверки\s+водителя\s+загружены\s+права|"
    rf"права){_SEP}(?P<value>\d{{2}}[ -]?\d{{2}}[- ]?\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(r"(?<!\d)(?P<value>\+7/\d{3}/\d{3}/\d{2}/\d{2})(?!\d)")
_CVV_RE = re.compile(
    rf"\b(?:(?:защитный|секретный|трёхзначный)\s+(?:код|CVV2?|CVC2?)|"
    rf"(?:CVV2?|CVC2?))(?:\s+карт\w*(?:\s+физлиц\w*)?)?"
    rf"(?:\s+равен)?{_SEP}"
    r"(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:надпись\s+на\s+карте|имя\s+владельца\s+на\s+пластике|"
    rf"HOLDER){_SEP}(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){{1,3}})(?=\s*[,;.|]|$)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    rf"\bсекретн\w*\s+(?:PIN|ПИН)(?:-код)?(?:\s+самого\s+держателя)?{_SEP}"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:мне\s+домой|фактически\s+живу|"
    r"посылка\s+для\s+меня\s+по\s+адресу|я\s+лично\s+проживаю)\b",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_COUNTRY_RESIDENCE_RE = re.compile(
    rf"\bстрана\s+проживания(?:\s+физлиц\w*)?{_SEP}"
    r"(?P<value>РФ|Россия|Российская\s+Федерация)(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"(?P<value>{_WORD})(?=\s*[,/|])|"
    rf"\bв\s+городе{_SEP}(?P<label>{_WORD})(?=\s*(?:и|[,;.]))",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:на\s+)?(?:улица|улице|ул\.|проспекте?|пр\.){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[,/|])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;/|.]|$)", re.IGNORECASE)
_FLAT_RE = re.compile(
    rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)"
    r"(?=\s*(?:[,;/|.]|$)|\s+в\s+городе)",
    re.IGNORECASE,
)

_PUBLIC_PHONE = re.compile(
    r"\b(?:служебн\w*\s+номер\s+аварийн\w*\s+бригад\w*|"
    r"телефон\s+ресторан\w*[^.;]{0,40}не\s+свой|общ\w*\s+регистратур\w*|"
    r"телефонн\w*\s+макет\w*|контакт\w*\s+боулинг\w*|"
    r"рабоч\w*\s+телефон\s+отдел\w*[^.;]{0,60}вместо\s+номера\s+сотрудник\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:ir|branch|contest|volunteers?|booking|investors?|school|charity|"
    r"department|office|team|support|info|sales|press|admin|noreply)@",
    re.IGNORECASE,
)
_SHARED_EMAIL_CONTEXT = re.compile(
    r"\b(?:обращени\w*\s+инвестор\w*|един\w*\s+почт\w*\s+филиал\w*|"
    r"вопрос\w*\s+к\s+олимпиад\w*|заявк\w*\s+волонтёр\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\bадрес\s+работодател\w*\b",
    re.IGNORECASE,
)
_NON_PERSON = re.compile(
    r"\b(?:макет\w*|шаблон\w*|учебн\w*|пример\w*|каталог\w*|"
    r"документаци\w*|тестов\w*|подсказк\w*\s+форм\w*|"
    r"датчик\w*|детал\w*|компонент\w*|издели\w*|спецификаци\w*|"
    r"прайс-лист\w*|коробк\w*|маркировк\w*|классификатор\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int = 130
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _candidate(
    entity: DetectedEntity, evidence: str, ownership: str = "personal"
) -> DetectionCandidate:
    return DetectionCandidate(entity=entity, evidence=evidence, ownership=ownership)


def _near(text: str, entity: DetectedEntity, pattern: re.Pattern[str], radius: int = 170) -> bool:
    window = text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]
    return pattern.search(window) is not None


def _same_clause(text: str, entity: DetectedEntity, pattern: re.Pattern[str]) -> bool:
    """Keep semantic evidence inside the entity's sentence or clause."""

    left = 0
    for boundary in re.finditer(r"(?:[;!?]|\.(?=\s+[А-ЯЁA-Z]))\s*", text[: entity.start]):
        left = boundary.end()
    right_match = re.search(r"(?:[;!?]|\.(?=\s+[А-ЯЁA-Z]))", text[entity.end :])
    right = entity.end + right_match.start() if right_match else len(text)
    return pattern.search(text[left:right]) is not None


def _valid_date(value: str) -> bool:
    parts = [int(part) for part in re.split(r"[./-]", value)]
    try:
        datetime(parts[2], parts[1], parts[0])
    except ValueError:
        return False
    return True


def _new_candidates(text: str) -> Iterator[DetectionCandidate]:
    for match in _PERSON_RE.finditer(text):
        group = next(name for name, value in match.groupdict().items() if value)
        value = match.group(group)
        if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
            yield _candidate(
                _entity(text, "PERSON", *match.span(group), "person_role_v3_13"),
                "explicit_person_role",
            )

    for pattern, entity_type, evidence in (
        (_PASSPORT_RE, "PASSPORT_RF", "passport_fields"),
        (_ISSUER_RE, "PASSPORT_ISSUER", "issuing_authority"),
        (_ISSUE_DATE_RE, "PASSPORT_ISSUE_DATE", "passport_issue_date"),
        (_BIRTH_TEXT_RE, "BIRTH_DATE", "birth_label"),
        (_BIRTHPLACE_RE, "PLACE_OF_BIRTH", "birthplace_label"),
        (_CITIZENSHIP_RE, "CITIZENSHIP", "citizenship_label"),
        (_LICENSE_RE, "DRIVER_LICENSE_RF", "driver_license_label"),
        (_PHONE_RE, "PHONE_RF", "subscriber_phone_label"),
        (_CVV_RE, "CVV", "card_secret_label"),
        (_CARDHOLDER_RE, "CARDHOLDER_NAME", "cardholder_label"),
        (_PIN_RE, "PIN", "pin_holder_label"),
        (_COUNTRY_RESIDENCE_RE, "ADDRESS_COUNTRY", "personal_residence_country"),
    ):
        for match in pattern.finditer(text):
            group = next(name for name, value in match.groupdict().items() if value)
            yield _candidate(
                _entity(text, entity_type, *match.span(group), "semantic_field_v3_13"),
                evidence,
            )

    for match in _DIVISION_RE.finditer(text):
        window = text[max(0, match.start() - 170) : match.end()]
        if _PASSPORT_CONTEXT.search(window):
            yield _candidate(
                _entity(text, "DIVISION_CODE", *match.span("value"), "division_v3_13"),
                "passport_division_context",
            )

    for match in _BIRTH_NUMERIC_RE.finditer(text):
        window = text[max(0, match.start() - 100) : match.end()]
        value = match.group("value")
        if _valid_date(value) and _BIRTH_CONTEXT.search(window):
            yield _candidate(
                _entity(text, "BIRTH_DATE", *match.span("value"), "birth_context_v3_13"),
                "birth_date_context",
            )

    for anchor in _ADDRESS_ANCHOR.finditer(text):
        address = text[anchor.end() :]
        offset = anchor.end()
        for entity_type, pattern, groups in (
            ("ADDRESS_COUNTRY", _COUNTRY_RE, ()),
            ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, ()),
            ("ADDRESS_STREET", _STREET_RE, ("value",)),
            ("ADDRESS_CITY", _CITY_RE, ("value", "label")),
            ("ADDRESS_HOUSE", _HOUSE_RE, ("value",)),
            ("ADDRESS_APARTMENT", _FLAT_RE, ("value",)),
        ):
            for match in pattern.finditer(address):
                selected = next((name for name in groups if match.group(name)), None)
                start, end = match.span(selected) if selected else match.span()
                yield _candidate(
                    _entity(
                        text,
                        entity_type,
                        offset + start,
                        offset + end,
                        "personal_address_v3_13",
                        129,
                    ),
                    "personal_address_anchor",
                )


def detect_candidates(text: str) -> list[DetectionCandidate]:
    """Return candidates before applying the independent mask policy."""

    inherited = [
        _candidate(entity, "inherited_v3_11", "unknown") for entity in detect_v3_11(text)
    ]
    return [*inherited, *_new_candidates(text)]


def should_mask(text: str, candidate: DetectionCandidate) -> bool:
    """Apply privacy/utility ownership policy to a discovered candidate."""

    entity = candidate.entity
    if _near(text, entity, _NON_PERSON):
        return False
    if entity.entity_type == "BIRTH_DATE":
        return _same_clause(text, entity, _BIRTH_CONTEXT)
    if entity.entity_type == "PHONE_RF":
        return not _near(text, entity, _PUBLIC_PHONE)
    if entity.entity_type == "EMAIL":
        return not (
            _SHARED_EMAIL.search(entity.text) or _near(text, entity, _SHARED_EMAIL_CONTEXT)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not _near(text, entity, _PUBLIC_ADDRESS)
    return candidate.ownership in {"personal", "unknown"}


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
    """Detect and policy-filter PII while preserving the existing detector API."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    if len(text) >= 100_000:
        lowered = text.casefold()
        if not any(marker in lowered for marker in _ADVANCED_TRIGGER_WORDS):
            return detect_v3_3(text)
    accepted = [item.entity for item in detect_candidates(text) if should_mask(text, item)]
    return _merge(accepted)
