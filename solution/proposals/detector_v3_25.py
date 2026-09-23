"""Candidate v3.25: reversible normalization and field-state parsing.

Pipeline: Unicode/OCR normalization with source-offset mapping, tokenization,
field-family state machine, shape/checksum validation, then an independent
ownership/public policy. Production is not modified.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.detection.models import DetectedEntity
from proposals.detector_v3_23 import detect as detect_v3_23


class Family(StrEnum):
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE_RF"
    INN = "INN"
    CARD = "BANK_CARD"
    PASSPORT = "PASSPORT_RF"
    DIVISION = "DIVISION_CODE"
    BIRTH_DATE = "BIRTH_DATE"
    BIRTHPLACE = "PLACE_OF_BIRTH"
    CITIZENSHIP = "CITIZENSHIP"
    ISSUER = "PASSPORT_ISSUER"
    ISSUE_DATE = "PASSPORT_ISSUE_DATE"
    LICENSE = "DRIVER_LICENSE_RF"
    COUNTRY = "ADDRESS_COUNTRY"
    POSTCODE = "ADDRESS_POSTAL_CODE"
    CITY = "ADDRESS_CITY"
    STREET = "ADDRESS_STREET"
    HOUSE = "ADDRESS_HOUSE"
    FLAT = "ADDRESS_APARTMENT"
    CVV = "CVV"
    PIN = "PIN"
    CARDHOLDER = "CARDHOLDER_NAME"


@dataclass(frozen=True, slots=True)
class NormalizedText:
    source: str
    text: str
    offsets: tuple[int, ...]

    @classmethod
    def build(cls, source: str) -> NormalizedText:
        chars: list[str] = []
        offsets: list[int] = []
        ocr_space = ">[]=:\t"
        for source_index, char in enumerate(source):
            normalized = unicodedata.normalize("NFKC", char).casefold().replace("ё", "е")
            if char in ocr_space:
                normalized = " " * max(1, len(normalized))
            elif char == "·":
                normalized = "."
            for output in normalized:
                chars.append(output)
                offsets.append(source_index)
        offsets.append(len(source))
        return cls(source, "".join(chars), tuple(offsets))

    def source_span(self, start: int, end: int) -> tuple[int, int]:
        return self.offsets[start], self.offsets[end - 1] + 1


@dataclass(frozen=True, slots=True)
class Token:
    value: str
    start: int
    end: int
    record: int


_TOKEN_RE = re.compile(
    r"[a-zа-я]+(?:-[a-zа-я]+)*|\d+|@[a-z0-9.-]+|[./+@-]|[,;\n]",
    re.IGNORECASE,
)


def tokenize(document: NormalizedText) -> list[Token]:
    tokens: list[Token] = []
    record = 0
    for match in _TOKEN_RE.finditer(document.text):
        value = match.group()
        tokens.append(Token(value, match.start(), match.end(), record))
        if value in {";", "\n"}:
            record += 1
    return tokens


@dataclass(frozen=True, slots=True)
class Candidate:
    entity: DetectedEntity
    family: Family
    record: int
    evidence: str


_WORD = r"[а-я]{2,}(?:-[а-я]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_EMAIL = r"[a-z0-9][a-z0-9.!#$%&'*+/=?^_`{|}~-]*@[a-z0-9.-]+\.[a-z]{2,}"
_PHONE = r"(?:\+7|8)[| ()\d-]{10,20}\d"
_DATE = r"(?:3[01]|[12]\d|0?[1-9])[./-](?:1[0-2]|0?[1-9])[./-](?:19|20)\d{2}"
_LATIN_NAME = r"[a-z][a-z'’-]+(?:\s+[a-z][a-z'’-]+){1,3}"
_ORG = r"(?:(?:гу|отдел\w*)\s+(?:мвд|уфмс)|умвд|омвд|уфмс)\b[^;\n\d]*?"
_FIELD_GAP = r"[\s./—–-]{0,55}?"

_LABELS: tuple[tuple[Family, re.Pattern[str]], ...] = (
    (Family.PERSON, re.compile(r"\b(?:ф\s*и\s*о|фио)\b")),
    (Family.EMAIL, re.compile(r"\b(?:e-?mail|электронн\w*\s+почт\w*|почт\w*)\b")),
    (Family.PHONE, re.compile(r"\b(?:телефон|тел|мобильн\w*|контакт)\w*\b")),
    (Family.INN, re.compile(r"\bинн\b|налогов\w*\s+(?:номер|идентификатор)")),
    (Family.PASSPORT, re.compile(r"\bпаспорт\w*\b|серия\s*(?:и|/)\s*номер")),
    (Family.DIVISION, re.compile(r"\b(?:код[\s_]+подразделени\w*|к\s*п)\b")),
    (
        Family.BIRTH_DATE,
        re.compile(r"\b(?:дата|день)[\s_]+рожд\w*|\bдр\b|\bродил\w*"),
    ),
    (
        Family.BIRTHPLACE,
        re.compile(r"\bмест\w*[\s_]+рожд\w*|\b(?:родом|родил\w*)\b"),
    ),
    (Family.CITIZENSHIP, re.compile(r"\bгражданств\w*\b")),
    (Family.ISSUER, re.compile(r"\b(?:кем\s+выд\w*|орган\s+выдач\w*|выдан\w*)\b")),
    (
        Family.ISSUE_DATE,
        re.compile(r"\b(?:дата[\s_]+выдач\w*|когда\s+выдан\w*)\b"),
    ),
    (Family.LICENSE, re.compile(r"\b(?:ву|водительск\w*\s+(?:права|удостоверени\w*))\b")),
    (Family.COUNTRY, re.compile(r"\b(?:стран\w*|государств\w*)\b")),
    (Family.POSTCODE, re.compile(r"\b(?:индекс|почтов\w*\s+код)\b")),
    (Family.CITY, re.compile(r"\b(?:город|населенн\w*\s+пункт)\b")),
    (Family.STREET, re.compile(r"\b(?:улиц\w*|ул)\b")),
    (Family.HOUSE, re.compile(r"\b(?:дом|д)\b")),
    (Family.FLAT, re.compile(r"\b(?:квартир\w*|кв)\b")),
    (Family.CVV, re.compile(r"\b(?:cvv2?|cvc2?|код\s+на\s+обороте)\b")),
    (Family.PIN, re.compile(r"\b(?:pin|пин)(?:\s*код)?\b")),
    (
        Family.CARDHOLDER,
        re.compile(r"\b(?:cardholder(?:_?name)?|holder|держател\w*|имя\s+на\s+карт\w*)\b"),
    ),
)

_VALUE_PATTERNS: dict[Family, re.Pattern[str]] = {
    Family.PERSON: re.compile(rf"\b(?P<value>{_NAME3})\b", re.I),
    Family.EMAIL: re.compile(rf"\b(?P<value>{_EMAIL})\b", re.I),
    Family.PHONE: re.compile(rf"(?P<value>{_PHONE})"),
    Family.INN: re.compile(r"(?<!\d)(?P<value>\d{10}|\d{12})(?!\d)"),
    Family.CARD: re.compile(r"(?<!\d)(?P<value>(?:\d[ /-]?){15}\d)(?!\d)"),
    Family.PASSPORT: re.compile(r"(?<!\d)(?P<value>\d{2}[- ]?\d{2}\s*\|?\s*\d{6})(?!\d)"),
    Family.DIVISION: re.compile(r"(?<!\d)(?P<value>\d{3}[- /]\d{3})(?!\d)"),
    Family.BIRTH_DATE: re.compile(rf"(?<!\d)(?P<value>{_DATE})(?!\d)"),
    Family.ISSUE_DATE: re.compile(rf"(?<!\d)(?P<value>{_DATE})(?!\d)"),
    Family.LICENSE: re.compile(r"(?<!\d)(?P<value>\d{2}[- ]?\d{2}[- ]\d{6})(?!\d)"),
    Family.COUNTRY: re.compile(r"\b(?P<value>российская\s+федерация|россия|рф)\b"),
    Family.POSTCODE: re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)"),
    Family.CITY: re.compile(rf"\b(?P<value>{_WORD})\b", re.I),
    Family.STREET: re.compile(rf"\b(?P<value>{_WORD})\b", re.I),
    Family.HOUSE: re.compile(r"(?<!\d)(?P<value>\d{1,4}[а-яa-z]?)(?!\d)", re.I),
    Family.FLAT: re.compile(r"(?<!\d)(?P<value>\d+)(?!\d)"),
    Family.CVV: re.compile(r"(?<!\d)(?P<value>\d{3,4})(?!\d)"),
    Family.PIN: re.compile(r"(?<!\d)(?P<value>\d{4})(?!\d)"),
    Family.CARDHOLDER: re.compile(rf"\b(?P<value>{_LATIN_NAME})\b", re.I),
}

_BIRTHPLACE_VALUE = re.compile(
    rf"\b(?P<value>(?:г\.|городе?|с\.|селе|деревне|поселке)\s*{_WORD}"
    rf"(?:\s+{_WORD}){{0,4}})(?=\s*(?:[,;.\n]|$|\s+и\b))",
    re.I,
)
_CITIZENSHIP_VALUE = re.compile(
    rf"\b(?P<value>российская\s+федерация|россия|рф|республик\w*\s+{_WORD})\b",
    re.I,
)
_ISSUER_VALUE = re.compile(rf"\b(?P<value>{_ORG})(?=\s*(?:[,;\n]|$|котор\w*)|\.\s*$)", re.I)


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[./-]", value)]
    try:
        date(parts[2], parts[1], parts[0])
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
        first = (
            sum(a * b for a, b in zip(digits[:10], (7, 2, 4, 10, 3, 5, 9, 4, 6, 8), strict=True))
            % 11
            % 10
        )
        second = (
            sum(a * b for a, b in zip(digits[:11], (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8), strict=True))
            % 11
            % 10
        )
        return (first, second) == (digits[10], digits[11])
    return False


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


def _entity(
    document: NormalizedText, family: Family, span: tuple[int, int], source: str
) -> DetectedEntity:
    start, end = document.source_span(*span)
    return DetectedEntity(family.value, start, end, document.source[start:end], 0.999, source, 250)


class FieldStateMachine:
    """Bind a normalized field family to a nearby value in the same record."""

    def __init__(self, document: NormalizedText, tokens: list[Token]) -> None:
        self.document = document
        self.tokens = tokens

    def candidates(self) -> Iterator[Candidate]:
        for family, label in _LABELS:
            for field in label.finditer(self.document.text):
                record = self._record_for(field.start())
                limit = self._record_limit(field.end(), 150)
                value_pattern = self._value_pattern(family)
                value = value_pattern.search(self.document.text, field.end(), limit)
                if value is None:
                    continue
                raw = value.group("value")
                if not self._valid(family, raw):
                    continue
                yield Candidate(
                    _entity(self.document, family, value.span("value"), "field_state_v3_25"),
                    family,
                    record,
                    self.document.text[field.start() : value.end()],
                )

    def _record_for(self, offset: int) -> int:
        return sum(1 for token in self.tokens if token.end <= offset and token.value in {";", "\n"})

    def _record_limit(self, start: int, distance: int) -> int:
        hard = min(len(self.document.text), start + distance)
        positions = [
            position
            for mark in (";", "\n")
            if (position := self.document.text.find(mark, start, hard)) >= 0
        ]
        return min(positions) if positions else hard

    @staticmethod
    def _value_pattern(family: Family) -> re.Pattern[str]:
        if family is Family.BIRTHPLACE:
            return _BIRTHPLACE_VALUE
        if family is Family.CITIZENSHIP:
            return _CITIZENSHIP_VALUE
        if family is Family.ISSUER:
            return _ISSUER_VALUE
        return _VALUE_PATTERNS[family]

    @staticmethod
    def _valid(family: Family, value: str) -> bool:
        if family in {Family.BIRTH_DATE, Family.ISSUE_DATE}:
            return _valid_date(value)
        if family is Family.INN:
            return _valid_inn(value)
        if family is Family.CARD:
            return _valid_luhn(value)
        if family is Family.PERSON:
            words = value.split()
            return len(words) == 3 and any(
                re.search(r"(?:ович|евич|ич|овн|евн|ичн)(?:а|я|у|е|ой|ы|ом)?$", word)
                for word in words[1:]
            )
        if family is Family.CITY:
            return value not in {
                "город",
                "деревня",
                "поселок",
                "проживания",
                "стране",
                "место",
                "село",
                "хутор",
            }
        if family is Family.STREET:
            return value not in {"улица", "адрес", "проживания"}
        return True


_PERSON_ROLE = re.compile(
    rf"\b(?:причита\w*|адресован\w*(?:\s+граждан\w*)?|договор\s+с|"
    rf"запис\w*\s+(?:собственник|владел))"
    rf"{_FIELD_GAP}(?P<value>{_NAME3})\b",
    re.I,
)
_PASSPORT_REVERSED = re.compile(
    r"(?P<value>(?:номер\s+\d{6}[^;\n]{0,45}?серия\s+(?:паспорта\s+)?\d{4}|"
    r"\d{6}\s+[^;\n]{0,25}?номер\s+паспорта[^;\n]{0,25}?\d{4}\s+[^;\n]{0,20}?серия))",
    re.I,
)
_ADDRESS_OWNER = re.compile(
    r"\b(?:дом\s+человек\w*|доставк\w*\s+(?:получ|человек|физлиц)\w*|"
    r"сведени\w*\s+о\s+доставк\w*|выписк\w*|домашн\w*\s+адрес\w*)\b",
    re.I,
)
_ADDRESS_PARTS: tuple[tuple[Family, re.Pattern[str]], ...] = (
    (Family.COUNTRY, re.compile(r"\b(?P<value>россия|рф|российская\s+федерация)\b", re.I)),
    (Family.POSTCODE, re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")),
    (
        Family.CITY,
        re.compile(
            rf"(?:^|[,\n]\s*)(?:россия|рф)?\s*,?\s*(?:\d{{6}}\s*,\s*)?"
            rf"(?P<value>{_WORD})(?=\s*(?:,|\n)\s*(?:ул\.?|улиц))",
            re.I,
        ),
    ),
    (Family.STREET, re.compile(rf"\b(?:улиц\w*|ул\.?)\s*(?P<value>{_WORD}(?:\s+{_WORD})?)", re.I)),
    (Family.HOUSE, re.compile(r"\b(?:д\.?|дом)\s*(?P<value>\d+[а-яa-z]?)(?!\d)", re.I)),
    (Family.FLAT, re.compile(r"\b(?:кв\.?|квартир\w*)\s*(?P<value>\d+)(?!\d)", re.I)),
)


def _prose_candidates(document: NormalizedText) -> Iterator[Candidate]:
    for pattern, family, evidence in (
        (_PERSON_ROLE, Family.PERSON, "owned_person"),
        (_PASSPORT_REVERSED, Family.PASSPORT, "passport_fields_reordered"),
    ):
        for match in pattern.finditer(document.text):
            if family is Family.PERSON and not FieldStateMachine._valid(
                family, match.group("value")
            ):
                continue
            yield Candidate(
                _entity(document, family, match.span("value"), "prose_state_v3_25"),
                family,
                0,
                evidence,
            )
    for anchor in _ADDRESS_OWNER.finditer(document.text):
        end = min(len(document.text), anchor.end() + 320)
        fragment = document.text[anchor.end() : end]
        for family, pattern in _ADDRESS_PARTS:
            for match in pattern.finditer(fragment):
                span = match.span("value")
                absolute = (anchor.end() + span[0], anchor.end() + span[1])
                yield Candidate(
                    _entity(document, family, absolute, "address_state_v3_25"),
                    family,
                    0,
                    "owned_address_record",
                )


_PERSONAL = re.compile(
    r"\b(?:я|человек\w*|физлиц\w*|клиент\w*|граждан\w*|заявител\w*|"
    r"получател\w*|владел\w*|сам(?:а|о|у|ой|ого|ому|им|ими)?|"
    r"собственн\w*|личн\w*|домашн\w*|"
    r"персональн\w*|сво(?:й|я|е|е|и|ю|его|ей|их))\b",
    re.I,
)
_PUBLIC = re.compile(
    r"\b(?:public_address|org_email|администраци\w*|аквапарк\w*|архив\w*|"
    r"агрегат\w*|банк\w*|"
    r"выставк\w*|гостиниц\w*|завод\w*|зал\w*|компани\w*|контрагент\w*|"
    r"магазин\w*|музе\w*|общежити\w*|поликлиник\w*|ресторан\w*|фонд\w*|"
    r"мониторинг\w*|организаци\w*|отдел\w*|отделени\w*|офис\w*|"
    r"постамат\w*|пункт\w*\s+(?:выдач\w*|самовывоз\w*)|публичн\w*|"
    r"редакци\w*|"
    r"ресепшен\w*|руководств\w*|сайт\w*|семинар\w*|склад\w*|"
    r"снабжени\w*|справочн\w*|служебн\w*|фирм\w*|центр\w*|школ\w*|"
    r"юридическ\w*\s+адрес|юрлиц\w*|"
    r"не\s+(?:домашн\w*|физлиц\w*|личн\w*))\b",
    re.I,
)
_TECHNICAL = re.compile(
    r"\b(?:sdk\w*|model\w*|public_test\w*|агрегат\w*|датчик\w*|двигател\w*|"
    r"издели\w*|качеств\w*|механизм\w*|оборудовани\w*|прибор\w*|"
    r"промышленн\w*|стан(?:ок|ка|\w*)|установк\w*|техническ\w*|"
    r"публичн\w*\s+руководств\w*|"
    r"спецификаци\w*|ящик\w*|"
    r"пример\w*|макет\w*|подсказк\w*|формат\w*|инструкци\w*|"
    r"заполнител\w*|условн\w*|insert\s+into|тест\w*|не\s+учитывать)\b",
    re.I,
)
_ROLE_EMAIL = re.compile(
    r"^(?:archive|booking|metrics|office|info|support|sales|admin|noreply)@",
    re.I,
)
_STRONG_PUBLIC = re.compile(
    r"\b(?:на\s+работу|адрес\w*\s+организаци\w*|публичн\w*\s+адрес|"
    r"юридическ\w*\s+адрес|постамат\w*|"
    r"пункт\w*\s+(?:выдач\w*|самовывоз\w*))\b",
    re.I,
)
_NEGATED_PERSONAL = re.compile(
    r"\b(?:не\s+(?:домашн\w*|физлиц\w*|клиент\w*|личн\w*|заявител\w*|сво[йяеё])|"
    r"вместо\s+личн\w*|"
    r"(?:не\s+является|не\s+принадлежит)\s+(?:домашн\w*|физлиц\w*|личн\w*))\b",
    re.I,
)


def should_mask(text: str, candidate: Candidate) -> bool:
    entity = candidate.entity
    left = max(0, entity.start - 190)
    right = min(len(text), entity.end + 190)
    window = text[left:right]
    delimiter = max(
        text.rfind(".", 0, entity.start),
        text.rfind(";", 0, entity.start),
        text.rfind("\n", 0, entity.start),
    )
    clause_start = max(left, delimiter + 1)
    stops = [
        position
        for mark in (".", ";", "\n")
        if (position := text.find(mark, entity.end, right)) >= 0
    ]
    clause_right = min(stops) if stops else right
    clause = text[clause_start:clause_right]
    before_value = text[clause_start : entity.start]
    personal = (
        _PERSONAL.search(before_value) is not None and _NEGATED_PERSONAL.search(clause) is None
    )
    public = _PUBLIC.search(window) is not None
    strong_public = _STRONG_PUBLIC.search(window) is not None
    technical = _TECHNICAL.search(window) is not None
    if candidate.entity.source == "field_state_v3_25":
        structured = re.search(r"[_|>\[\]\t]", window) is not None
        record_context = (
            re.search(
                r"\b(?:анкет\w*|выписк\w*|документ\w*|реестр\w*|паспорт\w*)\b",
                before_value,
                re.I,
            )
            is not None
        )
        if not (personal or structured or record_context):
            return False
    if entity.entity_type == "EMAIL":
        return not (_ROLE_EMAIL.search(entity.text) or (public and not personal))
    if entity.entity_type == "PHONE_RF":
        digits = re.sub(r"\D", "", entity.text)
        invalid_prefix = len(digits) >= 4 and digits[1:4] == "000"
        return not (strong_public or (public and not personal) or technical or invalid_prefix)
    if entity.entity_type.startswith("ADDRESS_"):
        if entity.entity_type == "ADDRESS_CITY" and entity.text.casefold() in {
            "город",
            "стране",
            "проживания",
        }:
            return False
        return not (strong_public or (public and not personal))
    if entity.entity_type == "INN":
        return not (public and not personal) and _valid_inn(entity.text)
    if entity.entity_type == "BANK_CARD":
        return not technical and _valid_luhn(entity.text)
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "CVV", "PIN"}:
        return not technical
    if entity.entity_type == "BIRTH_DATE":
        return not (
            re.search(r"\b(?:договор|событи|архив|срок)\w*\b", clause, re.I)
            and re.search(r"\bрожд\w*\b", clause, re.I) is None
        )
    return True


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


def _parse(text: str) -> list[Candidate]:
    document = NormalizedText.build(text)
    tokens = tokenize(document)
    return [*FieldStateMachine(document, tokens).candidates(), *_prose_candidates(document)]


def detect(text: str) -> list[DetectedEntity]:
    """Detect with production-compatible output and reversible source spans."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    inherited = detect_v3_23(text)
    if len(text) >= 100_000:
        # v3.23 already provides bounded trigger-region scanning for large text.
        return inherited
    candidates = _parse(text)
    added = [item.entity for item in candidates if should_mask(text, item)]
    merged = _merge([*inherited, *added])
    accepted: list[DetectedEntity] = []
    for entity in merged:
        try:
            family = Family(entity.entity_type)
        except ValueError:
            accepted.append(entity)
            continue
        if should_mask(text, Candidate(entity, family, 0, "merged_policy")):
            accepted.append(entity)
    return accepted
