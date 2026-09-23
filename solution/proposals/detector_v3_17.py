"""Candidate v3.17: semantic role families with bounded clause scans.

The proposal composes v3.15's candidate/policy architecture. Free-form values
are accepted only through explicit person, residence, document, or payment-owner
clauses. Public/shared and non-person clauses are rejected independently.
Production remains unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.models import DetectedEntity
from proposals.detector_v3_13 import DetectionCandidate
from proposals.detector_v3_15 import (
    detect_candidates as detect_candidates_v3_15,
)
from proposals.detector_v3_15 import should_mask as should_mask_v3_15

_SEP = r"\s*(?:[:=№/|]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"

_PERSON_RE = re.compile(
    rf"\b(?:беседовал|общался|говорил)\w*\s+с{_SEP}"
    rf"(?P<interview>{_NAME3})(?=\s+как\s+с\s+(?:заявител|клиент|граждан)\w*)|"
    rf"\bф\.?\s*и\.?\s*о\.?(?:\s+(?:получател|заявител|клиент)\w*)?"
    rf"(?:\s+по\s+(?:договору|заявке|анкете))?{_SEP}(?P<fio>{_NAME3})\b|"
    rf"\bот\s+имени\s+(?:ребёнка|несовершеннолетнего|доверителя)\s+"
    rf"действует{_SEP}(?P<representative>{_NAME3})\b|"
    rf"\b(?:счёт|договор|полис|актив)\s+принадлежит{_SEP}"
    rf"(?P<owner>{_NAME3})\b|"
    rf"\bобративш\w*\s+зовут{_SEP}(?P<caller>{_NAME3})\b|"
    rf"\b(?:в\s+)?личном\s+деле\s+указан\w*{_SEP}(?P<file>{_NAME3})\b|"
    rf"\b(?:залогодател|автовладелец|арендатор|ссудополучатель)\w*{_SEP}"
    rf"(?P<role>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)

_PASSPORT_RE = re.compile(
    rf"\b(?P<value>серия{_SEP}\d{{4}}\s+(?:и|/)\s+паспортный\s+номер{_SEP}\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\b(?:поле\s+)?КП(?:\s+паспорта)?(?:\s+заполнено\s+значением)?{_SEP}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\bместо\s+рождения(?:\s+(?:заявител|клиент|граждан)\w*)?{_SEP}"
    rf"(?P<value>(?:г\.|(?:рабочий\s+)?посёлок|город|село|деревня|аул|хутор)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
    re.IGNORECASE,
)
_CITIZENSHIP_RE = re.compile(
    rf"\b(?:в\s+)?поле\s+гражданства(?:\s+(?:написано|указано))?{_SEP}"
    r"(?P<value>РФ|Россия|Российская\s+Федерация)(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    rf"\b(?:PIN|ПИН)(?:-код)?\s*,?\s*(?:установленн\w*|заданн\w*)\s+"
    rf"сам\w*\s+(?:держател\w*|владелец|владельц\w*|клиент\w*){_SEP}"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\bна\s+пластике\s+владельц\w*\s+(?:напечатано|выбито|указано){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:адрес\s*,?\s+где\s+я\s+(?:действительно\s+)?живу|"
    r"регистрация\s+физлиц\w*|дом\s+находится|"
    r"я\s+прописан\w*|место\s+постоянного\s+проживания\s+(?:заёмщик|клиент|граждан)\w*|"
    r"получател\w*\s+живёт|"
    r"курьер\w*\s+нужен\w*\s+мой\s+адрес[\s\S]{0,70}сообщаю|"
    r"адрес\s+для\s+моей\s+доставки)\b",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"(?:г\.{_SEP})?(?P<value>{_WORD})(?=\s*[,;|])|"
    rf"\bво?{_SEP}(?P<locative>{_WORD})(?=\s*(?:[,.;]|по\s+улице))",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:по|(?:на\s+)?)?(?:улица|улице|ул\.|проспекте?|пр\.){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[,;|])",
    re.IGNORECASE,
)
_HOUSE_RE = re.compile(
    rf"\b(?:в\s+)?(?:дом|доме|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;|.]|$)",
    re.IGNORECASE,
)
_FLAT_RE = re.compile(
    rf"\b(?:в\s+)?(?:квартира|квартире|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;|.]|$)",
    re.IGNORECASE,
)

_PUBLIC_PHONE = re.compile(
    r"\b(?:контакт\s+диспетчер\w*\s+аэропорт\w*|телефон\s+отдел\w*\s+реклам\w*|"
    r"регистратур\w*\s+санатори\w*|заглушк\w*|контакт\w*\s+культурн\w*\s+центр\w*|"
    r"размещён\w*\s+публичн\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:business|rewards?|accreditation|internship|receipt|concierge|culture|"
    r"commercial|loyalty|media|practice|payments?|hotel|center)@",
    re.IGNORECASE,
)
_SHARED_EMAIL_CONTEXT = re.compile(
    r"\b(?:коммерческ\w*\s+запрос\w*|программ\w*\s+лояльност\w*|"
    r"аккредитаци\w*\s+СМИ|заявк\w*\s+на\s+практик\w*|автоматическ\w*\s+чек\w*|"
    r"служб\w*\s+отел\w*|культурн\w*\s+центр\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\bадрес\s+администраци\w*\s+школ\w*\b",
    re.IGNORECASE,
)
_NON_PERSON_DOCUMENT = re.compile(
    r"\b(?:промышленн\w*\s+установк\w*|оборудовани\w*|техническ\w*\s+паспорт)\b",
    re.IGNORECASE,
)
_INVALID_CARD_CONTEXT = re.compile(
    r"\b(?:неверн\w*|некорректн\w*)\s+контрольн\w*\s+сумм\w*\b",
    re.IGNORECASE,
)
_PERSON_NOISE = re.compile(
    r"\b(?:по|договору|анкете|заявке|получателя|клиента|гражданина)\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int = 150
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _candidate(entity: DetectedEntity, evidence: str) -> DetectionCandidate:
    return DetectionCandidate(entity=entity, evidence=evidence, ownership="personal")


def _near(text: str, entity: DetectedEntity, pattern: re.Pattern[str], radius: int = 200) -> bool:
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


def _new_candidates(text: str) -> Iterator[DetectionCandidate]:
    folded = text.casefold()
    person_markers = (
        "беседовал",
        "фио",
        "от имени",
        "принадлежит",
        "зовут",
        "личном деле",
        "залогодател",
        "автовладелец",
    )
    if any(marker in folded for marker in person_markers):
        for match in _PERSON_RE.finditer(text):
            group = next(name for name, value in match.groupdict().items() if value)
            value = match.group(group)
            if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
                yield _candidate(
                    _entity(text, "PERSON", *match.span(group), "person_semantics_v3_17"),
                    "explicit_person_semantic_family",
                )

    if "серия" in folded and "паспорт" in folded:
        for match in _PASSPORT_RE.finditer(text):
            yield _candidate(
                _entity(text, "PASSPORT_RF", *match.span("value"), "passport_fields_v3_17"),
                "passport_field_family",
            )
    if "кп" in folded:
        for match in _DIVISION_RE.finditer(text):
            yield _candidate(
                _entity(text, "DIVISION_CODE", *match.span("value"), "division_field_v3_17"),
                "passport_division_field",
            )

    for marker, pattern, entity_type, evidence in (
        ("место рождения", _BIRTHPLACE_RE, "PLACE_OF_BIRTH", "birthplace_owner"),
        ("поле гражданства", _CITIZENSHIP_RE, "CITIZENSHIP", "citizenship_field"),
        ("пин", _PIN_RE, "PIN", "holder_pin"),
        ("на пластике", _CARDHOLDER_RE, "CARDHOLDER_NAME", "cardholder_field"),
    ):
        if marker in folded:
            for match in pattern.finditer(text):
                yield _candidate(
                    _entity(text, entity_type, *match.span("value"), "owned_field_v3_17"),
                    evidence,
                )

    address_markers = (
        "где я",
        "регистрация физлиц",
        "дом находится",
        "я прописан",
        "постоянного проживания",
        "живёт",
        "нужен мой адрес",
        "моей доставки",
    )
    if any(marker in folded for marker in address_markers):
        for anchor in _ADDRESS_ANCHOR.finditer(text):
            address = text[anchor.end() : min(len(text), anchor.end() + 400)]
            offset = anchor.end()
            for entity_type, pattern, groups in (
                ("ADDRESS_COUNTRY", _COUNTRY_RE, ()),
                ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, ()),
                ("ADDRESS_STREET", _STREET_RE, ("value",)),
                ("ADDRESS_CITY", _CITY_RE, ("value", "locative")),
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
                            "personal_address_v3_17",
                            149,
                        ),
                        "personal_address_semantic_family",
                    )


def detect_candidates(text: str) -> list[DetectionCandidate]:
    """Return v3.15 and v3.17 candidates before the mask policy."""

    return [*detect_candidates_v3_15(text), *_new_candidates(text)]


def should_mask(text: str, candidate: DetectionCandidate) -> bool:
    """Apply parent policy and v3.17 semantic ownership gates."""

    if not should_mask_v3_15(text, candidate):
        return False
    entity = candidate.entity
    if entity.entity_type == "PERSON":
        words = entity.text.split()
        return len(words) >= 2 and not _PERSON_NOISE.search(entity.text)
    if entity.entity_type == "BANK_CARD":
        return _valid_luhn(entity.text) and not _near(text, entity, _INVALID_CARD_CONTEXT)
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE"}:
        return not _near(text, entity, _NON_PERSON_DOCUMENT)
    if entity.entity_type == "PHONE_RF":
        return not _near(text, entity, _PUBLIC_PHONE)
    if entity.entity_type == "EMAIL":
        return not (
            _SHARED_EMAIL.search(entity.text) or _near(text, entity, _SHARED_EMAIL_CONTEXT)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        return not _near(text, entity, _PUBLIC_ADDRESS)
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
    """Detect and policy-filter PII while preserving the production API."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    accepted = [item.entity for item in detect_candidates(text) if should_mask(text, item)]
    return _merge(accepted)
