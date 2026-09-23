"""Candidate v3.15: clause-owned PERSON/address recall over v3.13.

The candidate reuses v3.13's candidate/policy split and adds only lightweight
rules. New free-form values require a personal ownership clause; public and
organisation clauses are rejected by the policy stage. Production is unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.models import DetectedEntity
from proposals.detector_v3_13 import (
    DetectionCandidate,
)
from proposals.detector_v3_13 import (
    detect_candidates as detect_candidates_v3_13,
)
from proposals.detector_v3_13 import should_mask as should_mask_v3_13

_SEP = r"\s*(?:[:=№/|]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_END = r"(?=\s*(?:[,;.]|$))"

_PERSON_RE = re.compile(
    rf"\bсогласие\s+от{_SEP}(?P<consent>{_NAME3})\b|"
    rf"\bпосылк\w*\s+заберёт(?:\s+сам\w*)?{_SEP}(?P<parcel>{_NAME3})\b|"
    rf"\b(?:получател|получательниц)\w*(?:\s+(?:пособия|выплаты))?\s+"
    rf"(?:является|стала?){_SEP}"
    rf"(?P<recipient>{_NAME3})\b|"
    rf"\b(?:лицевой|банковский|абонентский)\s+счёт\s+оформлен\w*\s+на{_SEP}"
    rf"(?P<account>{_NAME3})\b",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$",
    re.IGNORECASE,
)

_PASSPORT_RE = re.compile(
    rf"\b(?P<value>серия\s+паспорта{_SEP}\d{{4}}\s*(?:/|и|,)\s*"
    r"номер\s*\d{6})(?!\d)",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    r"\bпаспорт\s+оформил\w*\s+"
    r"(?P<value>(?:ОМВД|УМВД|УФМС|ГУ\s+МВД)[^,;\n]*?)"
    r"(?=\s*(?:[,;]|\.\s*$|$))",
    re.IGNORECASE,
)
_ISSUE_DATE_RE = re.compile(
    rf"\bдатой\s+выдачи\s+паспорта\s+является{_SEP}"
    r"(?P<value>\d{1,2}[./-]\d{1,2}[./-](?:19|20)\d{2})(?!\d)",
    re.IGNORECASE,
)
_DIVISION_RE = re.compile(
    rf"\b(?:подразделение|код\s+подразделения){_SEP}"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_CLAUSE = re.compile(
    r"\b(?:паспорт|выдан\w*\s+(?:ОМВД|УМВД|УФМС|ГУ\s+МВД))\b",
    re.IGNORECASE,
)
_BIRTHPLACE_RE = re.compile(
    rf"\b(?:место\s+рождения(?:\s+(?:по\s+документу|заявителя|клиента))?|"
    rf"место\s+моего\s+рождения){_SEP}"
    rf"(?P<label>(?:город|г\.|(?:рабочий\s+)?посёлок|аул|хутор|село|деревня)\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,4}}){_END}|"
    rf"\b(?:заявител|клиент|гражданин)\w*\s+родом\s+из{_SEP}"
    rf"(?P<origin>(?:города|г\.|(?:рабочего\s+)?посёлка|аула|села|деревни)\s+{_WORD}){_END}",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR = re.compile(
    r"\b(?:мой\s+домашний\s+адрес|точный\s+адрес|"
    r"дом\s+(?:заявител|клиент|страховател)\w*\s+находится|"
    r"адрес\s+сам\w*\s+(?:заявител|клиент|страховател)\w*|"
    r"получател\w*\s+ответил\w*|"
    r"доставить\s+документ\w*\s+домой(?:[^.]|\.\s*){0,70}адрес|"
    r"я\s+лично\s+проживаю)\b",
    re.IGNORECASE,
)
_LIVES_CITY_RE = re.compile(
    rf"\b(?:она|он|заявитель|клиент)\w*[^.\n]{{0,45}}?\bживёт\s+во?{_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[.,;]|$)",
    re.IGNORECASE,
)
_COUNTRY_RE = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY_RE = re.compile(
    rf"(?:г\.{_SEP})?(?P<value>{_WORD})(?=\s*[,;|])|"
    rf"\bво?{_SEP}(?P<locative>{_WORD})(?=\s*,)|"
    rf"\bв\s+городе{_SEP}(?P<label>{_WORD})(?=\s*(?:и|[,;.]))",
    re.IGNORECASE,
)
_STREET_RE = re.compile(
    rf"\b(?:на\s+)?(?:улица|улице|ул\.|проспекте?|пр\.){_SEP}"
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
    r"\b(?:секретар\w*\s+подразделени\w*|фиктивн\w*\s+номер|"
    r"обратитесь\s+в\s+поддержк\w*|контакт\w*\s+выставочн\w*\s+центр\w*|"
    r"оба\s+контакта\s+корпоративн\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:mailer|presscenter|supportdesk|expo|robot|service|vendor|hall)@",
    re.IGNORECASE,
)
_SHARED_EMAIL_CONTEXT = re.compile(
    r"\b(?:рассылк\w*\s+ведёт\s+робот|подпис\w*\s+ведомств\w*|"
    r"оба\s+контакта\s+корпоративн\w*|выставочн\w*\s+центр\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(
    r"\b(?:адрес\s+(?:магазин|филиал|пункт\w*\s+выдачи)\w*|"
    r"филиал\w*\s+банк\w*[^.;]{0,55}не\s+к\s+заявител\w*|"
    r"получател\w*\s+там\s+не\s+живёт|домашний\s+адрес\s+клиента\s+неизвестен|"
    r"на\s+работу[\s\S]{0,110}адрес\s+организаци\w*)\b",
    re.IGNORECASE,
)


def _entity(
    text: str, entity_type: str, start: int, end: int, source: str, priority: int = 140
) -> DetectedEntity:
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, priority)


def _candidate(entity: DetectedEntity, evidence: str) -> DetectionCandidate:
    return DetectionCandidate(entity=entity, evidence=evidence, ownership="personal")


def _near(text: str, entity: DetectedEntity, pattern: re.Pattern[str], radius: int = 190) -> bool:
    window = text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]
    return pattern.search(window) is not None


def _new_candidates(text: str) -> Iterator[DetectionCandidate]:
    folded = text.casefold()
    person_markers = ("согласие", "посылк", "получател", "счёт оформлен")
    if any(marker in folded for marker in person_markers):
        for match in _PERSON_RE.finditer(text):
            group = next(name for name, value in match.groupdict().items() if value)
            value = match.group(group)
            if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
                yield _candidate(
                    _entity(text, "PERSON", *match.span(group), "person_clause_v3_15"),
                    "personal_role_clause",
                )

    if "паспорт" in folded:
        for match in _PASSPORT_RE.finditer(text):
            yield _candidate(
                _entity(text, "PASSPORT_RF", *match.span("value"), "passport_fields_v3_15"),
                "passport_field_clause",
            )
        for pattern, entity_type, evidence in (
            (_ISSUER_RE, "PASSPORT_ISSUER", "passport_issuer_clause"),
            (_ISSUE_DATE_RE, "PASSPORT_ISSUE_DATE", "passport_issue_date_clause"),
        ):
            for match in pattern.finditer(text):
                group = next(name for name, value in match.groupdict().items() if value)
                yield _candidate(
                    _entity(text, entity_type, *match.span(group), "document_clause_v3_15"),
                    evidence,
                )
        for match in _DIVISION_RE.finditer(text):
            window = text[max(0, match.start() - 170) : match.end()]
            if _PASSPORT_CLAUSE.search(window):
                yield _candidate(
                    _entity(text, "DIVISION_CODE", *match.span("value"), "division_v3_15"),
                    "passport_division_clause",
                )

    if "место" in folded or "родом" in folded:
        for match in _BIRTHPLACE_RE.finditer(text):
            group = next(name for name, value in match.groupdict().items() if value)
            yield _candidate(
                _entity(text, "PLACE_OF_BIRTH", *match.span(group), "document_clause_v3_15"),
                "birthplace_clause",
            )

    if "живёт" in folded:
        for match in _LIVES_CITY_RE.finditer(text):
            yield _candidate(
                _entity(text, "ADDRESS_CITY", *match.span("value"), "residence_city_v3_15"),
                "personal_residence_clause",
            )

    address_markers = ("адрес", "дом ", "доставить", "проживаю")
    if any(marker in folded for marker in address_markers):
        for anchor in _ADDRESS_ANCHOR.finditer(text):
            address = text[anchor.end() : min(len(text), anchor.end() + 400)]
            offset = anchor.end()
            for entity_type, pattern, groups in (
                ("ADDRESS_COUNTRY", _COUNTRY_RE, ()),
                ("ADDRESS_POSTAL_CODE", _POSTCODE_RE, ()),
                ("ADDRESS_STREET", _STREET_RE, ("value",)),
                ("ADDRESS_CITY", _CITY_RE, ("value", "locative", "label")),
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
                            "personal_address_v3_15",
                            139,
                        ),
                        "personal_address_clause",
                    )


def detect_candidates(text: str) -> list[DetectionCandidate]:
    """Return v3.13 and v3.15 candidates before mask policy."""

    return [*detect_candidates_v3_13(text), *_new_candidates(text)]


def should_mask(text: str, candidate: DetectionCandidate) -> bool:
    """Apply parent policy, then v3.15 public/shared clause gates."""

    if not should_mask_v3_13(text, candidate):
        return False
    entity = candidate.entity
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
    """Detect and policy-filter PII while keeping the production API."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    accepted = [item.entity for item in detect_candidates(text) if should_mask(text, item)]
    return _merge(accepted)
