"""Candidate v3.14: model-ready hybrid with a lightweight local fallback.

The default path has no ML dependency. Optional NER spans can be supplied by a
separately deployed token-classification model; contextual ownership gates keep
public names and locations out. Production remains unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass

from app.detection.models import DetectedEntity
from proposals.detector_v3_12 import detect as detect_v3_12

_WORD = r"[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)*"
_UPPER_WORD = r"[А-ЯЁ]{2,}(?:-[А-ЯЁ]{2,})*"
_NAME3 = rf"(?:{_WORD}\s+{_WORD}\s+{_WORD}|{_UPPER_WORD}\s+{_UPPER_WORD}\s+{_UPPER_WORD})"
_PATRONYMIC = re.compile(
    r"(?:ович|евич|ич|овна|евна|ична|инична)$",
    re.IGNORECASE,
)
_PERSON_ROLE = (
    r"абонент\w*|автор\w*|бенефициар\w*|вкладчик\w*|владел\w*|водител\w*|"
    r"доверител\w*|за[её]мщик\w*|заявител\w*|застрахованн\w*|клиент\w*|"
    r"пациент\w*|плательщик\w*|получател\w*|покупател\w*|представител\w*|"
    r"пользовател\w*|страховател\w*"
)
_PERSON_FALLBACK = re.compile(
    rf"\b(?:{_PERSON_ROLE})(?:\s+[А-ЯЁа-яё-]+){{0,3}}?\s*[:=/—-]?\s+"
    rf"(?P<value>{_NAME3})\b",
    re.IGNORECASE,
)
_PERSON_ACTION = re.compile(
    rf"\b(?:анкет\w*|договор\w*|жалоб\w*|заявлени\w*|обращени\w*|"
    rf"претензи\w*)\s+(?:заполнен\w*|заключ[её]н\w*|написан\w*|"
    rf"подписан\w*|подан\w*|составлен\w*)\s+(?P<value>{_NAME3})\b",
    re.IGNORECASE,
)
_PERSON_APPOINTED = re.compile(
    rf"\b(?:{_PERSON_ROLE})\s+(?:[А-ЯЁа-яё-]+\s+)?"
    rf"(?:назначен\w*|стал\w*|выбран\w*)\s+(?P<value>{_NAME3})\b",
    re.IGNORECASE,
)
_FIO_LABEL = re.compile(
    rf"\bФ\.?\s*И\.?\s*О\.?(?:\s+(?:{_PERSON_ROLE}))?\s*[:=/—-]\s*"
    rf"(?P<value>{_NAME3})\b",
    re.IGNORECASE,
)
_PERSONAL_CONTEXT = re.compile(
    rf"\b(?:{_PERSON_ROLE}|Ф\.?\s*И\.?\s*О\.?|мой|моя|мо[её]|мне|меня|"
    r"личн\w*|персональн\w*)\b",
    re.IGNORECASE,
)
_PERSONAL_ADDRESS = re.compile(
    rf"\b(?:адрес(?:ом|у)?\s+(?:регистрации|проживания|доставки)|"
    rf"(?:домашний|личный|почтовый)\s+адрес|адрес\s+(?:{_PERSON_ROLE})|"
    r"прописан\w*\s+по\s+адресу|зарегистрирован\w*\s+по\s+адресу|"
    r"(?:я\s+(?:лично\s+)?|фактически\s+)?живу|(?:я\s+(?:лично\s+)?)?прожива\w*|"
    r"(?:мне\s+домой|посылк\w*\s+для\s+меня|достав(?:ить|ка)\s+(?:мне|клиенту)))\b",
    re.IGNORECASE,
)
_PUBLIC_CONTEXT = re.compile(
    r"\b(?:афиш\w*|биографи\w*|выставк\w*|газет\w*|историк\w*|книг\w*|"
    r"концерт\w*|литератур\w*|музе\w*|писател\w*|поэзи\w*|пьес\w*|"
    r"режисс[её]р\w*|скульптур\w*|спектакл\w*|стать\w*|фильм\w*)\b",
    re.IGNORECASE,
)
_PUBLIC_CONTACT = re.compile(
    r"\b(?:аварийн\w*\s+бригад\w*|боулинг\w*|волонт[её]р\w*|инвестор\w*|"
    r"олимпиад\w*|работодател\w*|регистратур\w*|ресторан\w*|служебн\w*|"
    r"филиал\w*|школ\w*|холдинг\w*|пункт\w*\s+выдач\w*|общ\w*|"
    r"единая\s+почта)\b",
    re.IGNORECASE,
)
_NEGATED_OWNER = re.compile(
    r"\b(?:не\s+(?:свой|личн\w*|принадлежит\s+физлицу)|а\s+не\s+свой|"
    r"не\s+принадлежит\s+(?:клиенту|заявителю|физлицу)|"
    r"не\s+адрес\s+(?:получателя|клиента|заявителя))\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:ir|branch|contest|volunteers?|booking|registry|office|team|press|"
    r"sales|support|help|info|hr)@",
    re.IGNORECASE,
)

_COUNTRY = re.compile(r"\b(?P<value>Россия|РФ|Российская\s+Федерация)\b", re.IGNORECASE)
_POSTCODE = re.compile(r"(?<!\d)(?P<value>\d{6})(?!\d)")
_CITY = re.compile(
    rf"(?:\b(?:г\.|город|прожива\w*\s+(?:в|во))\s*(?P<labelled>{_WORD})|"
    rf"(?<![А-ЯЁа-яё])(?P<bare>{_WORD})(?=\s*[,;|/]\s*(?:улица|ул\.|"
    rf"проспект|переулок|шоссе|набережная|на\s+улице))|"
    rf"\b(?:в|во)\s+городе\s+(?P<locative>{_WORD}))",
    re.IGNORECASE,
)
_STREET = re.compile(
    rf"\b(?:на\s+)?(?:улиц(?:а|е)|ул\.|проспект|переулок|шоссе|набережная)\s+"
    rf"(?P<value>{_WORD})(?=\s*[,;|/])",
    re.IGNORECASE,
)
_HOUSE = re.compile(r"\b(?:дом|д\.)\s*(?P<value>\d+[А-ЯЁA-Z]?)(?=\s*[,;|/])", re.IGNORECASE)
_FLAT = re.compile(
    r"\b(?:квартира|кв\.)\s*(?P<value>\d+)(?=\s*[,;|/.]|\s+в\s+городе|$)",
    re.IGNORECASE,
)

_CARDHOLDER = re.compile(
    r"\b(?:надпись\s+на\s+карте|имя\s+владельца\s+на\s+пластике|HOLDER)"
    r"\s*[:—-]?\s*(?P<value>[A-Z][A-Z'’-]+\s+[A-Z][A-Z'’-]+)(?=\s*[,;|.]|$)",
    re.IGNORECASE,
)
_OWNED_CVV = re.compile(
    r"\b(?:защитный\s+код|тр[её]хзначный\s+(?:CVV|CVC)(?:2?)\s+карты\s+физлица)"
    r"(?:\s+(?:карты|карточки))?\s*(?:равен)?\s*[:=—-]?\s*(?P<value>\d{3})(?!\d)",
    re.IGNORECASE,
)
_CITIZENSHIP = re.compile(
    r"\bгражданство\s+(?:лица|клиента|заявителя|гражданина)\s+"
    r"(?:указано|записано)(?:\s+как)?\s*[:=—-]?\s*"
    r"(?P<value>РФ|Россия|Российская\s+Федерация)(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_LICENSE = re.compile(
    r"\b(?:для\s+проверки\s+(?:водителя|клиента)[^.;\n]{0,25}|"
    r"(?:арендатор|водитель|автомобилист)[^.;\n]{0,45})\b(?:права|ВУ)\s*"
    r"(?P<value>\d{2}[ -]\d{2}[ -]\d{6})(?!\d)",
    re.IGNORECASE,
)
_PASSPORT_LABEL = re.compile(
    r"\b(?:паспортн\w*\s+(?:данн\w*|реквизит\w*))[^.;\n]{0,20}?"
    r"(?P<value>серия\s*[:=]?\s*\d{4}\s+(?:и|[,;])\s*номер\s*[:=]?\s*\d{6})",
    re.IGNORECASE,
)
_PASSPORT_COMPACT = re.compile(
    r"\b(?:паспорт(?:у|ом)?(?:\s*№)?\s*|паспорт\w*[^.;\n]{0,20})"
    r"(?P<value>\d{10})(?!\d)(?=[^.;\n]{0,25}\b(?:заявител|клиент|граждан))",
    re.IGNORECASE,
)
_DIVISION = re.compile(
    r"\b(?:код\s+паспортного\s+подразделения|(?:паспорт|документ)\b[^\n]{0,140}\bкод)"
    r"\s*[:=—-]?\s*(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_ISSUER = re.compile(
    r"\b(?:кем\s+выдано\s+(?:удостоверение|документ)|(?:паспорт|документ)\b[^;\n]{0,20}"
    r"оформлен|оформлен)\s*[:=—-]?\s*(?P<value>(?:ГУ\s+МВД|УМВД|ОМВД|УФМС)\b[^,;\n]*?)"
    r"(?=\s*[,;]|\.\s*$|$)",
    re.IGNORECASE,
)
_ISSUE_DATE = re.compile(
    r"\bдата\s+(?:фактической\s+)?выдачи\s+(?:паспорта|документа)\s*[:=—-]?\s*"
    r"(?P<value>(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2})",
    re.IGNORECASE,
)
_BIRTH_NUMERIC = re.compile(
    r"\b(?:появил(?:ся|ась)\s+на\s+свет|рожд[её]н(?:а)?)\s+"
    r"(?P<value>(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2})",
    re.IGNORECASE,
)
_BIRTHPLACE = re.compile(
    rf"\b(?:место\s+рождения[»\"']?\s+(?:написано|указано)|родил(?:ся|ась)|"
    rf"появил(?:ся|ась)\s+на\s+свет[^.;\n]{{0,25}})\s*[:=—-]?\s*"
    rf"(?P<value>(?:аул|хутор|станица|г\.|городе?)\s+{_WORD}(?:\s+{_WORD}){{0,4}})"
    rf"(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_BIRTHPLACE_AFTER_DATE = re.compile(
    rf"\b(?:родил(?:ся|ась)|появил(?:ся|ась)\s+на\s+свет)\b[^;\n]{{0,50}}?\sв\s+"
    rf"(?P<value>(?:аул|хутор|станица|г\.|городе?)\s+{_WORD}(?:\s+{_WORD}){{0,3}})"
    rf"(?=\s*[,;.]|$)",
    re.IGNORECASE,
)
_BIRTH_WORDS = re.compile(
    r"\bдата\s+рождения\s+(?:клиента|заявителя|граждан\w*|физлица)\s*[:=—-]?\s*"
    r"(?P<value>(?:(?:двадцать\s+)?(?:первое|второе|третье|четв[её]ртое|пятое|"
    r"шестое|седьмое|восьмое|девятое)|десятое|одиннадцатое|двенадцатое|"
    r"тринадцатое|четырнадцатое|пятнадцатое|шестнадцатое|семнадцатое|"
    r"восемнадцатое|девятнадцатое|тридцатое|тридцать\s+первое)\s+"
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|"
    r"октября|ноября|декабря)\s+(?:19|20)\d{2}\s+года)",
    re.IGNORECASE,
)
_TECHNICAL_CONTEXT = re.compile(
    r"\b(?:упаковк\w*|оборудовани\w*|прибор\w*|устройств\w*|партии|"
    r"техническ\w*|макет\w*|пример\w*|образец\w*|тестов\w*)\b",
    re.IGNORECASE,
)
_SLASH_PHONE = re.compile(r"(?<!\d)(?P<value>\+7/\d{3}/\d{3}/\d{2}/\d{2})(?!\d)", re.IGNORECASE)
_PIN = re.compile(
    r"\b(?:секретный|личный|персональный)\s+(?:PIN|ПИН)(?:[- ]код)?\s+"
    r"(?:самого\s+)?(?:владельца|держателя|клиента)\s*[:=—-]?\s*(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class NERSpan:
    """Normalized output contract for an optional external NER worker."""

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
    return DetectedEntity(entity_type, start, end, text[start:end], confidence, source, 150)


def _looks_like_name(value: str) -> bool:
    parts = value.split()
    return (
        len(parts) == 3
        and all(part[0].isupper() for part in parts)
        and any(_PATRONYMIC.search(part) for part in parts)
    )


def _looks_like_fio_field(value: str) -> bool:
    parts = value.split()
    return len(parts) == 3 and any(_PATRONYMIC.search(part) for part in parts)


def _rule_fallback(text: str) -> Iterator[DetectedEntity]:
    if not _PUBLIC_CONTEXT.search(text):
        for pattern in (_PERSON_FALLBACK, _PERSON_ACTION, _PERSON_APPOINTED, _FIO_LABEL):
            for match in pattern.finditer(text):
                value = match.group("value")
                valid = (
                    _looks_like_fio_field(value)
                    if pattern is _FIO_LABEL
                    else _looks_like_name(value)
                )
                if valid:
                    yield _entity(text, "PERSON", match.span("value"), "person_fallback_v3_14")
    for pattern, entity_type, source in (
        (_CARDHOLDER, "CARDHOLDER_NAME", "cardholder_fallback_v3_14"),
        (_OWNED_CVV, "CVV", "cvv_owned_v3_14"),
        (_CITIZENSHIP, "CITIZENSHIP", "citizenship_fallback_v3_14"),
        (_LICENSE, "DRIVER_LICENSE_RF", "license_fallback_v3_14"),
        (_PASSPORT_LABEL, "PASSPORT_RF", "passport_label_v3_14"),
        (_PASSPORT_COMPACT, "PASSPORT_RF", "passport_owned_v3_14"),
        (_DIVISION, "DIVISION_CODE", "division_fallback_v3_14"),
        (_ISSUER, "PASSPORT_ISSUER", "issuer_fallback_v3_14"),
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_v3_14"),
        (_BIRTH_NUMERIC, "BIRTH_DATE", "birth_numeric_v3_14"),
        (_BIRTH_WORDS, "BIRTH_DATE", "birth_words_v3_14"),
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_fallback_v3_14"),
        (_BIRTHPLACE_AFTER_DATE, "PLACE_OF_BIRTH", "birthplace_after_date_v3_14"),
        (_SLASH_PHONE, "PHONE_RF", "phone_slash_v3_14"),
        (_PIN, "PIN", "pin_fallback_v3_14"),
    ):
        for match in pattern.finditer(text):
            yield _entity(text, entity_type, match.span("value"), source)
    if _PERSONAL_ADDRESS.search(text):
        for entity_type, pattern in (
            ("ADDRESS_COUNTRY", _COUNTRY),
            ("ADDRESS_POSTAL_CODE", _POSTCODE),
            ("ADDRESS_CITY", _CITY),
            ("ADDRESS_STREET", _STREET),
            ("ADDRESS_HOUSE", _HOUSE),
            ("ADDRESS_APARTMENT", _FLAT),
        ):
            for match in pattern.finditer(text):
                groups = match.groupdict()
                group = "value"
                if groups.get("labelled") is not None:
                    group = "labelled"
                elif groups.get("bare") is not None:
                    group = "bare"
                elif groups.get("locative") is not None:
                    group = "locative"
                value = match.group(group)
                if entity_type == "ADDRESS_CITY" and not value[0].isupper():
                    continue
                yield _entity(text, entity_type, match.span(group), "address_fallback_v3_14")


def _ner_fallback(text: str, spans: Sequence[NERSpan]) -> Iterator[DetectedEntity]:
    """Accept model proposals only behind high-precision local ownership gates."""

    if _PUBLIC_CONTEXT.search(text):
        return
    personal = _PERSONAL_CONTEXT.search(text) is not None
    personal_address = _PERSONAL_ADDRESS.search(text) is not None
    label_map = {
        "PERSON": "PERSON",
        "CITY": "ADDRESS_CITY",
        "STREET": "ADDRESS_STREET",
        "HOUSE": "ADDRESS_HOUSE",
        "POSTAL_CODE": "ADDRESS_POSTAL_CODE",
        "COUNTRY": "ADDRESS_COUNTRY",
    }
    for span in spans:
        entity_type = label_map.get(span.label.upper())
        valid_bounds = 0 <= span.start < span.end <= len(text)
        if entity_type is None or span.score < 0.92 or not valid_bounds:
            continue
        if entity_type == "PERSON":
            if personal and _looks_like_name(text[span.start : span.end]):
                yield _entity(
                    text,
                    entity_type,
                    (span.start, span.end),
                    "ner_gated_v3_14",
                    span.score,
                )
        elif personal_address:
            yield _entity(text, entity_type, (span.start, span.end), "ner_gated_v3_14", span.score)


def _overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    return left.start < right.end and right.start < left.end


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ranked = sorted(
        entities,
        key=lambda item: (-item.priority, -item.confidence, -(item.end - item.start), item.start),
    )
    accepted: list[DetectedEntity] = []
    for entity in ranked:
        if not any(_overlap(entity, existing) for existing in accepted):
            accepted.append(entity)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    public = _PUBLIC_CONTACT.search(text) is not None
    negated = _NEGATED_OWNER.search(text) is not None
    if entity.entity_type == "PHONE_RF":
        return public and (negated or _PERSONAL_CONTEXT.search(text) is None)
    if entity.entity_type == "EMAIL":
        return bool(
            (_ROLE_EMAIL.search(entity.text) and (public or negated))
            or (public and _PERSONAL_CONTEXT.search(text) is None)
        )
    if entity.entity_type.startswith("ADDRESS_"):
        employer = re.search(r"\bадрес\s+работодателя\b", text, re.IGNORECASE)
        return bool(employer or (public and negated))
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "CVV"}:
        return _TECHNICAL_CONTEXT.search(text) is not None
    return False


def detect(text: str, ner_spans: Sequence[NERSpan] = ()) -> list[DetectedEntity]:
    """Detect PII with rules and optional precomputed NER proposals."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge(
            [*detect_v3_12(text), *_rule_fallback(text), *_ner_fallback(text, ner_spans)]
        )
        if not _suppressed(text, entity)
    ]
