"""Candidate v3.19: bounded ownership clauses for natural Russian documents.

The candidate extends v3.17 without changing production. Detection and the
privacy/utility decision remain separate: broad-looking values are emitted
only from a short, explicit personal clause and public/shared values are then
rejected by policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.detection.models import DetectedEntity
from proposals.detector_v3_13 import DetectionCandidate
from proposals.detector_v3_17 import detect_candidates as detect_candidates_v3_17
from proposals.detector_v3_17 import should_mask as should_mask_v3_17

_SEP = r"\s*(?:[:=№/|]|[-–—])?\s*"
_WORD = r"[А-Яа-яЁё]{2,}(?:-[А-Яа-яЁё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_MONTH = (
    r"января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря"
)
_ORDINAL_DAY = (
    r"перв(?:ого|ое)|втор(?:ого|ое)|треть(?:его|е)|четв[её]рт(?:ого|ое)|"
    r"пят(?:ого|ое)|шест(?:ого|ое)|седьм(?:ого|ое)|восьм(?:ого|ое)|"
    r"девят(?:ого|ое)|десят(?:ого|ое)|одиннадцат(?:ого|ое)|"
    r"двенадцат(?:ого|ое)|тринадцат(?:ого|ое)|четырнадцат(?:ого|ое)|"
    r"пятнадцат(?:ого|ое)|шестнадцат(?:ого|ое)|семнадцат(?:ого|ое)|"
    r"восемнадцат(?:ого|ое)|девятнадцат(?:ого|ое)|двадцат(?:ого|ое)|"
    r"двадцать\s+(?:первого|второго|третьего|четв[её]ртого|пятого|"
    r"шестого|седьмого|восьмого|девятого)|тридцат(?:ого|ое)|"
    r"тридцать\s+первого"
)

_PERSON_RE = re.compile(
    rf"\b(?:копи\w*|документ\w*)\s+(?:выдал\w*|передал\w*|вручил\w*)\s+"
    rf"(?P<value>{_NAME3})(?=\s+как\s+(?:владел|держател|заявител|получател)\w*)",
    re.IGNORECASE,
)
_PATRONYMIC = re.compile(r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ем|ом)?$", re.IGNORECASE)
_INN_RE = re.compile(
    rf"\b(?:мой|свой|личный)\s+(?:идентификатор\s+в\s+ФНС|"
    rf"налоговый\s+идентификатор|ИНН)(?:\s+\w+){{0,3}}{_SEP}"
    r"(?P<value>\d{10}|\d{12})(?!\d)",
    re.IGNORECASE,
)
_ISSUE_DATE_RE = re.compile(
    rf"\b(?:паспорт|личн\w*\s+документ)\w*[^.;\n]{{0,45}}?"
    rf"(?:оформили|выдали)(?:\s+(?:мне|ему|ей))?{_SEP}"
    rf"(?P<value>(?:{_ORDINAL_DAY})\s+(?:{_MONTH})\s+(?:19|20)\d{{2}}\s+года)",
    re.IGNORECASE,
)
_LICENSE_RE = re.compile(
    rf"\b(?:мо[и|й]|его|е[её]|личн\w*)\s+(?:водительск\w*\s+)?права\b"
    rf"[^.;\n]{{0,55}}?{_SEP}(?P<value>\d{{2}}\d{{2}}[- ]\d{{6}})(?!\d)",
    re.IGNORECASE,
)
_ISSUER_RE = re.compile(
    r"\b(?:в\s+)?личном\s+документе\s*:\s*орган\s+"
    r"(?P<value>(?:ОМВД|УМВД|УФМС|ГУ\s+МВД)[^;\n]+?)"
    r"(?=\s*[;]|$)",
    re.IGNORECASE,
)
_CVV_RE = re.compile(
    rf"\bкод\s+(?:CVV2?|CVC2?)\s+на\s+карте\s+"
    rf"(?:клиент|владел|держател)\w*\s+(?:составляет|равен){_SEP}"
    r"(?P<value>\d{3,4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER_RE = re.compile(
    rf"\b(?:CARD\s+HOLDER\s+NAME|на\s+пластике\s+(?:написано\s+)?"
    rf"имя\s+владельца){_SEP}"
    r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=\s*[.;,]|$)",
    re.IGNORECASE,
)

_COUNTRY_FIELD_RE = re.compile(
    rf"\b(?:страна\s*,?\s+где\s+постоянно\s+жив[её]т\s+(?:клиент|гражданин)|"
    rf"в\s+домашнем\s+адресе\s+(?:клиент|граждан)\w*\s+страна\s+указана\s+как)"
    rf"{_SEP}(?P<value>РФ|Россия|Российская\s+Федерация)",
    re.IGNORECASE,
)
_POSTCODE_FIELD_RE = re.compile(
    rf"\b(?:почтовый\s+индекс\s+места\s+жительства\s+(?:физлиц|граждан|клиент)\w*|"
    rf"для\s+домашн\w*\s+доставк\w*[^.;\n]{{0,35}}?индекс){_SEP}"
    r"(?P<value>\d{6})(?!\d)",
    re.IGNORECASE,
)
_CITY_FIELD_RE = re.compile(
    rf"\b(?:город\s+проживания\s+(?:владел|получател|заявител|клиент|граждан)\w*[^.;\n]{{0,35}}?"
    rf"|(?:я|он|она)\s+(?:постоянно\s+)?жив[еуё]т?\s+в){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[;,.]|\s+и\b|$)",
    re.IGNORECASE,
)
_STREET_FIELD_RE = re.compile(
    rf"\b(?:улица\s+в\s+адресе\s+(?:получател|заявител|клиент|граждан)\w*|"
    rf"мо[йя]\s+дом\s+(?:расположен|находится)\s+на\s+улице){_SEP}"
    rf"(?P<value>{_WORD})(?=\s*[;,.]|$)",
    re.IGNORECASE,
)
_HOUSE_FIELD_RE = re.compile(
    rf"\b(?:номер\s+дома\s+(?:граждан|клиент|заявител|получател)\w*|"
    rf"в\s+(?:его|е[её]|мо[её]м)\s+домашнем\s+адресе\s+указан\s+дом)"
    rf"{_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[;,.]|$)",
    re.IGNORECASE,
)
_FLAT_FIELD_RE = re.compile(
    rf"\b(?:квартира\s+(?:самого\s+)?(?:заявител|получател|клиент|граждан)\w*|"
    rf"(?:он|она|я)\s+прожива(?:ет|ю)\s+в\s+квартире){_SEP}"
    r"(?P<value>\d+)(?=\s*[;,.]|$)",
    re.IGNORECASE,
)

_ADDRESS_ANCHOR_RE = re.compile(
    r"\b(?:мой\s+адрес|домашний\s+адрес\s+(?:получател|заявител|клиент|граждан)\w*)"
    r"\s*[:—-]",
    re.IGNORECASE,
)
_RESIDENCE_RE = re.compile(r"\b(?:жив[её]т|проживает|живу)\s+в\b", re.IGNORECASE)
_PERSONAL_PRELUDE = re.compile(
    r"\b(?:получател|заявител|клиент|граждан|владел|физлиц|он|она|я)\w*\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?:РФ|Россия|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_CITY = re.compile(
    rf"(?:^|,\s*)\s*(?:\d{{6}}\s*,\s*)?(?:г\.|городе\s+)?"
    rf"(?P<value>{_WORD})(?=\s*,\s*(?:(?:на\s+)?улиц|ул\.))|"
    rf"^\s*(?:г\.|городе\s+)(?P<label>{_WORD})(?=\s*[.;,]|$)",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:на\s+)?(?:улица|улице|ул\.){_SEP}(?P<value>{_WORD})(?=\s*[,;])",
    re.IGNORECASE,
)
_HOUSE = re.compile(rf"\b(?:дом|д\.){_SEP}(?P<value>\d+[А-ЯЁ]?)(?=\s*[,;.]|$)", re.IGNORECASE)
_FLAT = re.compile(rf"\b(?:квартира|кв\.){_SEP}(?P<value>\d+)(?=\s*[,;.]|$)", re.IGNORECASE)
_BIRTHPLACE_RE = re.compile(
    rf"\bродил\w*\s+\d{{1,2}}[./-]\d{{1,2}}[./-](?:19|20)\d{{2}}\s+в\s+"
    rf"(?P<value>(?:селе|деревне|городе|пос[её]лке)\s+{_WORD}(?:\s+{_WORD}){{0,3}}\s+"
    rf"(?:области|края|республики))(?=\s+(?:и\s+)?(?:теперь|сейчас)\s+жив|[.;]|$)",
    re.IGNORECASE,
)

_PUBLIC_PHONE = re.compile(
    r"\b(?:администраци\w*\s+(?:бассейн|поликлиник|школ|театр)\w*|"
    r"отдел\w*\s+закупок|(?:звонить\s+)?в\s+отдел\w*[\s\S]{0,80}личн\w*\s+номер\w*\s+нет|"
    r"телефон\s+отдел\w*[^.;]{0,45}не\s+личн|"
    r"контакт\w*\s+галере\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL = re.compile(
    r"^(?:franchise|notifier|office-manager|gallery|gallery-office)@", re.IGNORECASE
)
_SHARED_CONTEXT = re.compile(
    r"\b(?:общ\w*|публичн\w*|служебн\w*|не\s+личн\w*|контакт\w*\s+галере\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_ADDRESS = re.compile(r"\b(?:кинотеатр|галере|музе|офис\s+компани)\w*\b", re.IGNORECASE)
_NON_PERSON_CVV = re.compile(r"\b(?:запчаст|детал|артикул|склад)\w*\b", re.IGNORECASE)
_RESIDENCE_NOT_BIRTH = re.compile(r"\b(?:теперь|сейчас)\s+жив[её]т\s+в\b", re.IGNORECASE)


def _entity(text: str, entity_type: str, span: tuple[int, int], source: str) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.99, source, 160)


def _candidate(entity: DetectedEntity, evidence: str) -> DetectionCandidate:
    return DetectionCandidate(entity, evidence, "personal")


def _valid_inn(value: str) -> bool:
    digits = [int(char) for char in value]
    if len(digits) == 10:
        return (
            sum(a * b for a, b in zip((2, 4, 10, 3, 5, 9, 4, 6, 8), digits, strict=False)) % 11 % 10
            == digits[9]
        )
    if len(digits) == 12:
        first = (
            sum(a * b for a, b in zip((7, 2, 4, 10, 3, 5, 9, 4, 6, 8), digits, strict=False))
            % 11
            % 10
        )
        second = (
            sum(a * b for a, b in zip((3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8), digits, strict=False))
            % 11
            % 10
        )
        return first == digits[10] and second == digits[11]
    return False


def _clause(text: str, entity: DetectedEntity, radius: int = 220) -> str:
    left = max(
        text.rfind(".", 0, entity.start), text.rfind(";", 0, entity.start), entity.start - radius
    )
    stops = [
        position for mark in (".", ";", "\n") if (position := text.find(mark, entity.end)) >= 0
    ]
    right = min(stops) if stops else min(len(text), entity.end + radius)
    return text[max(0, left + 1) : right]


def _window(text: str, entity: DetectedEntity, radius: int = 220) -> str:
    return text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]


def _yield_matches(
    text: str, pattern: re.Pattern[str], entity_type: str, evidence: str
) -> Iterator[DetectionCandidate]:
    for match in pattern.finditer(text):
        yield _candidate(
            _entity(text, entity_type, match.span("value"), "bounded_clause_v3_19"), evidence
        )


def _address_chain(text: str, start: int, end: int) -> Iterator[DetectionCandidate]:
    fragment = text[start:end]
    for entity_type, pattern, group in (
        ("ADDRESS_COUNTRY", _COUNTRY, None),
        ("ADDRESS_POSTAL_CODE", _POSTCODE, None),
        ("ADDRESS_CITY", _CITY, "value"),
        ("ADDRESS_STREET", _STREET, "value"),
        ("ADDRESS_HOUSE", _HOUSE, "value"),
        ("ADDRESS_APARTMENT", _FLAT, "value"),
    ):
        for match in pattern.finditer(fragment):
            selected = group
            if entity_type == "ADDRESS_CITY" and match.groupdict().get("label"):
                selected = "label"
            span = match.span(selected) if selected else match.span()
            yield _candidate(
                _entity(
                    text, entity_type, (start + span[0], start + span[1]), "address_chain_v3_19"
                ),
                "bounded_personal_address",
            )


def _new_candidates(text: str) -> Iterator[DetectionCandidate]:
    for match in _PERSON_RE.finditer(text):
        value = match.group("value")
        if any(_PATRONYMIC.search(word) for word in value.split()[1:]):
            yield _candidate(
                _entity(text, "PERSON", match.span("value"), "person_owner_v3_19"), "document_owner"
            )

    for match in _INN_RE.finditer(text):
        if _valid_inn(match.group("value")):
            yield _candidate(
                _entity(text, "INN", match.span("value"), "inn_owner_v3_19"), "personal_tax_id"
            )

    for marker, pattern, entity_type, evidence in (
        ("паспорт", _ISSUE_DATE_RE, "PASSPORT_ISSUE_DATE", "owned_document_date"),
        ("права", _LICENSE_RE, "DRIVER_LICENSE_RF", "owned_driving_licence"),
        ("личном документе", _ISSUER_RE, "PASSPORT_ISSUER", "owned_document_issuer"),
        ("cvv", _CVV_RE, "CVV", "owned_card_secret"),
        ("holder", _CARDHOLDER_RE, "CARDHOLDER_NAME", "cardholder_label"),
        ("пластике", _CARDHOLDER_RE, "CARDHOLDER_NAME", "cardholder_label"),
        ("страна", _COUNTRY_FIELD_RE, "ADDRESS_COUNTRY", "residence_country"),
        ("индекс", _POSTCODE_FIELD_RE, "ADDRESS_POSTAL_CODE", "residence_postcode"),
        ("город", _CITY_FIELD_RE, "ADDRESS_CITY", "residence_city"),
        ("жив", _CITY_FIELD_RE, "ADDRESS_CITY", "residence_city"),
        ("улиц", _STREET_FIELD_RE, "ADDRESS_STREET", "residence_street"),
        ("дом", _HOUSE_FIELD_RE, "ADDRESS_HOUSE", "residence_house"),
        ("квартир", _FLAT_FIELD_RE, "ADDRESS_APARTMENT", "residence_flat"),
        ("родил", _BIRTHPLACE_RE, "PLACE_OF_BIRTH", "birth_clause"),
    ):
        if marker in text.casefold():
            yield from _yield_matches(text, pattern, entity_type, evidence)

    for anchor in _ADDRESS_ANCHOR_RE.finditer(text):
        stop = min(
            (position for mark in (".", "\n") if (position := text.find(mark, anchor.end())) >= 0),
            default=len(text),
        )
        yield from _address_chain(text, anchor.end(), min(stop + 1, anchor.end() + 320))

    for anchor in _RESIDENCE_RE.finditer(text):
        prelude = text[max(0, anchor.start() - 150) : anchor.start()]
        if not _PERSONAL_PRELUDE.search(prelude):
            continue
        stop = min(
            (position for mark in (".", "\n") if (position := text.find(mark, anchor.end())) >= 0),
            default=len(text),
        )
        yield from _address_chain(text, anchor.end(), min(stop + 1, anchor.end() + 260))


def detect_candidates(text: str) -> list[DetectionCandidate]:
    """Return inherited and v3.19 candidates before mask policy."""

    return [*detect_candidates_v3_17(text), *_new_candidates(text)]


def should_mask(text: str, candidate: DetectionCandidate) -> bool:
    """Apply inherited policy and local public/non-person suppressions."""

    if not should_mask_v3_17(text, candidate):
        return False
    entity = candidate.entity
    clause = _clause(text, entity)
    window = _window(text, entity)
    if entity.entity_type == "PHONE_RF" and _PUBLIC_PHONE.search(window):
        return False
    if entity.entity_type == "EMAIL" and (
        _SHARED_EMAIL.search(entity.text) or _SHARED_CONTEXT.search(window)
    ):
        return False
    if entity.entity_type.startswith("ADDRESS_") and _PUBLIC_ADDRESS.search(window):
        return False
    if entity.entity_type == "CVV" and _NON_PERSON_CVV.search(clause):
        return False
    if entity.entity_type == "PLACE_OF_BIRTH" and _RESIDENCE_NOT_BIRTH.search(clause):
        return candidate.evidence == "birth_clause"
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
    return _merge(item.entity for item in detect_candidates(text) if should_mask(text, item))
