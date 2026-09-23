"""Candidate v3.18: clause-aware ownership and weak-type recovery over v3.13."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from .detector_v3_13 import detect as production_detect
from .models import DetectedEntity
from .overlap import merge_greedy_non_overlapping

_WORD = r"[А-ЯЁа-яё]{2,}(?:-[А-ЯЁа-яё]{2,})*"
_NAME3 = rf"{_WORD}\s+{_WORD}\s+{_WORD}"
_DATE = (
    r"(?:3[01]|[12]\d|0?[1-9])[-/.](?:1[0-2]|0?[1-9])[-/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{2}[-/.](?:1[0-2]|0?[1-9])[-/.](?:3[01]|[12]\d|0?[1-9])"
)
_END = r"(?=\s*(?:[,;.]|$))"
_PATRONYMIC = re.compile(
    r"(?:(?:ович|евич|ич)(?:а|я|у|е|ем|ом)?|"
    r"(?:овн|евн|ичн)(?:а|я|у|е|ой|ы)?)$",
    re.IGNORECASE,
)
_NAME = re.compile(rf"(?=(?<![А-ЯЁа-яё-])(?P<value>{_NAME3})(?![А-ЯЁа-яё-]))")
_PERSONAL_EVIDENCE = re.compile(
    r"\b(?:автовладел\w*|владел\w*|действует|залогодател\w*|заявител\w*|"
    r"застрахованн\w*|клиент\w*|личн\w*\s+дел\w*|обративш\w*|"
    r"от\s+имени|посылк\w*|заказ\w*|получател\w*|принадлежит|согласие|"
    r"сч[её]т|Ф\.?И\.?О\.?)\b",
    re.IGNORECASE,
)
_CULTURAL_CONTEXT = re.compile(
    r"\b(?:афиш\w*|биографи\w*|выставк\w*|книг\w*|концерт\w*|"
    r"литератур\w*|музе\w*|писател\w*|поэт\w*|пьес\w*|режисс[её]р\w*|"
    r"роман\s+(?:описывает|написан)|скульптур\w*|спектакл\w*|фильм\w*)\b",
    re.IGNORECASE,
)
_PERSON_STOPWORDS = re.compile(
    r"^(?:ПО\s+ДОГОВОРУ|ДАТА\s+РОЖДЕНИЯ|МЕСТО\s+РОЖДЕНИЯ)$", re.IGNORECASE
)

_PASSPORT_FIELDS = (
    re.compile(
        r"\b(?P<value>серия\s+паспорта\s*[:=]?\s*\d{4}\s*[/;,]\s*"
        r"номер\s*[:=]?\s*\d{6})(?!\d)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<value>серия\s*[:=]?\s*\d{4}\s+(?:и|[,;])\s*"
        r"паспортный\s+номер\s*[:=]?\s*\d{6})(?!\d)",
        re.IGNORECASE,
    ),
)
_DIVISION = re.compile(
    r"\b(?:поле\s+КП|КП|код\s+паспортного\s+подразделения|"
    r"(?:паспорт|документ)\b[^\n]{0,160}\b(?:код\s+)?подразделени[ея])"
    r"(?:\s+заполнено\s+значением)?\s*[:=—-]?\s*"
    r"(?P<value>\d{3}[- /]\d{3})(?!\d)",
    re.IGNORECASE,
)
_BIRTH_DATE = re.compile(
    rf"\b(?:рождени[ея](?:\s+(?:клиента|заявителя|за[её]мщика|физлица))?|"
    rf"д\.?\s*р\.?)\s*(?:указано|записано)?(?:\s+как)?\s*[:=—-]?\s*"
    rf"(?P<value>{_DATE})(?!\d)",
    re.IGNORECASE,
)
_BIRTHPLACE = (
    re.compile(
        rf"\bместо\s+(?:моего\s+)?рождения(?:\s+(?:заявител\w*|клиент\w*))?"
        rf"(?:\s+по\s+(?:паспорту|документу))?\s*[:—-]\s*"
        rf"(?P<value>(?:пос[её]лок|аул|хутор|станица|село|деревня|город|г\.)"
        rf"\s+{_WORD}(?:\s+{_WORD}){{0,4}}){_END}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:заявител\w*|клиент\w*|граждан\w*)\s+родом\s+из\s+"
        rf"(?P<value>(?:пос[её]лка|аула|хутора|станицы|села|деревни|города|г\.)"
        rf"\s+{_WORD}(?:\s+{_WORD}){{0,3}}){_END}",
        re.IGNORECASE,
    ),
)
_CITIZENSHIP = re.compile(
    r"\b(?:поле\s+)?гражданств\w*(?:\s+(?:лица|клиента|заявителя))?\s+"
    r"(?:написано|указано|заполнено)(?:\s+как)?\s*[:=—-]?\s*"
    r"(?P<value>РФ|Россия|Российская\s+Федерация)(?=\s*[,;.]|$)",
    re.IGNORECASE,
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
_PIN = re.compile(
    r"\b(?:PIN|ПИН)(?:[- ]код)?(?:\s*,?\s*(?:установленн\w*|выбранн\w*)\s+"
    r"(?:самим\s+)?(?:держателем|владельцем|клиентом))\s*[:=—-]?\s*"
    r"(?P<value>\d{4})(?!\d)",
    re.IGNORECASE,
)
_CARDHOLDER = re.compile(
    r"\b(?:на\s+пластике\s+(?:владельца|держателя)\s+(?:напечатано|выбито)|"
    r"имя\s+(?:владельца|держателя)\s+на\s+(?:карте|пластике))\s*[:=—-]?\s*"
    r"(?P<value>[A-Z][A-Z'’-]+(?:\s+[A-Z][A-Z'’-]+){1,3})(?=\s*[,;.]|$)",
    re.IGNORECASE,
)

_ADDRESS_EVIDENCE = re.compile(
    r"\b(?:адрес(?:ом|у)?\s+(?:для\s+моей\s+доставки|регистрации|проживания)|"
    r"(?:домашний|личный|мой|точный)\s+адрес|адрес\s+(?:физлица|за[её]мщика|"
    r"(?:самого\s+)?(?:заявителя|страхователя|клиента|получателя))|"
    r"действительно\s+живу|(?:получател\w*|клиент\w*|заявител\w*)\s+жив[её]т|"
    r"дом(?:\s+(?:заявителя|клиента|получателя))?\s+находится|"
    r"место\s+постоянного\s+проживания|мой\s+адрес|"
    r"прописан\w*|регистраци\w*\s+физлица|доставить\s+\w+\s+домой|"
    r"курьер\w*\s+нужен\s+мой\s+адрес)\b",
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
        rf"\b(?:жив[её]т|нахожусь|находится|прописан\w*)\s+(?:в|во)\s+"
        rf"(?P<value>{_WORD})(?=\s*[,;.]|\s+(?:по|на)\s+улиц)",
        re.IGNORECASE,
    ),
)
_STREET = re.compile(
    rf"\b(?:по\s+|на\s+)?(?:улиц(?:а|е)|ул\.|проспект|переулок|шоссе|набережная)"
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
_ADDRESS_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("ADDRESS_COUNTRY", (_COUNTRY,)),
    ("ADDRESS_POSTAL_CODE", (_POSTCODE,)),
    ("ADDRESS_CITY", _CITY),
    ("ADDRESS_STREET", (_STREET,)),
    ("ADDRESS_HOUSE", (_HOUSE,)),
    ("ADDRESS_APARTMENT", (_FLAT,)),
)

_PUBLIC_CONTACT = re.compile(
    r"\b(?:аэропорт\w*|автоматическ\w*|выставочн\w*\s+центр\w*|"
    r"диспетчер\w*|культурн\w*\s+центр\w*|корпоративн\w*|отдел\w*|"
    r"поддержк\w*|публичн\w*|реклам\w*|регистратур\w*|санатори\w*|"
    r"секретар\w*|служб\w*\s+отел\w*|школ\w*)\b",
    re.IGNORECASE,
)
_ROLE_EMAIL = re.compile(
    r"^(?:business|rewards?|accreditation|internship|receipt|concierge|culture|"
    r"mailer|presscenter|supportdesk|expo|service|office|team|press|support|"
    r"help|info|hr|admin|noreply)@",
    re.IGNORECASE,
)
_PERSONAL_EMAIL = re.compile(
    r"\b(?:моя|мой|собственная|личная|персональная)\s+(?:электронная\s+)?"
    r"(?:почта|email|e-mail)|\bпочта\s+(?:получателя|клиента|заявителя)\b",
    re.IGNORECASE,
)
_NONPERSON_ADDRESS = re.compile(
    r"\b(?:адрес\s+(?:администрации|магазина|организации|работодателя)|"
    r"пункт\w*\s+выдач\w*|филиал\w*|на\s+работу|администраци\w*\s+школ\w*)\b",
    re.IGNORECASE,
)
_SYNTHETIC = re.compile(
    r"\b(?:заглушк\w*|фиктивн\w*|заполнител\w*|тестов\w*|макет\w*|"
    r"пример\w*|образец\w*|подсказк\w*)\b",
    re.IGNORECASE,
)
_TECHNICAL = re.compile(
    r"\b(?:промышленн\w*|установк\w*|оборудовани\w*|прибор\w*|"
    r"устройств\w*|техническ\w*)\b",
    re.IGNORECASE,
)
_INVALID_CHECKSUM = re.compile(
    r"\b(?:неверн\w*|ошибочн\w*|не\s+проходит|невалидн\w*)"
    r"[^.;\n]{0,40}\b(?:контрольн\w*\s+сумм\w*|разряд\w*)|"
    r"\b(?:неверн\w*\s+контрольн\w*\s+сумм\w*)\b",
    re.IGNORECASE,
)


def _entity(text: str, entity_type: str, span: tuple[int, int], source: str) -> DetectedEntity:
    start, end = span
    return DetectedEntity(entity_type, start, end, text[start:end], 0.998, source, 170)


def _valid_name(value: str) -> bool:
    parts = value.split()
    return (
        len(parts) == 3
        and all(part[0].isupper() or part.isupper() for part in parts)
        and any(_PATRONYMIC.search(part) for part in parts)
    )


def _valid_date(value: str) -> bool:
    parts = [int(item) for item in re.split(r"[-/.]", value)]
    year, month, day = parts if len(str(parts[0])) == 4 else parts[::-1]
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _supplemental(text: str) -> Iterator[DetectedEntity]:
    if _PERSONAL_EVIDENCE.search(text) and not _CULTURAL_CONTEXT.search(text):
        for match in _NAME.finditer(text):
            if _valid_name(match.group("value")):
                yield _entity(text, "PERSON", match.span("value"), "person_context_v3_18")
    for patterns, entity_type, source in (
        (_PASSPORT_FIELDS, "PASSPORT_RF", "passport_fields_v3_18"),
        ((_DIVISION,), "DIVISION_CODE", "division_field_v3_18"),
        ((_BIRTH_DATE,), "BIRTH_DATE", "birth_field_v3_18"),
        (_BIRTHPLACE, "PLACE_OF_BIRTH", "birthplace_v3_18"),
        ((_CITIZENSHIP,), "CITIZENSHIP", "citizenship_v3_18"),
        ((_ISSUER,), "PASSPORT_ISSUER", "issuer_v3_18"),
        (_ISSUE_DATE, "PASSPORT_ISSUE_DATE", "issue_date_v3_18"),
        ((_PIN,), "PIN", "pin_v3_18"),
        ((_CARDHOLDER,), "CARDHOLDER_NAME", "cardholder_v3_18"),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                if entity_type in {"BIRTH_DATE", "PASSPORT_ISSUE_DATE"} and not _valid_date(
                    match.group("value")
                ):
                    continue
                yield _entity(text, entity_type, match.span("value"), source)
    if _ADDRESS_EVIDENCE.search(text) and not _NONPERSON_ADDRESS.search(text):
        for entity_type, address_patterns in _ADDRESS_PATTERNS:
            for pattern in address_patterns:
                for match in pattern.finditer(text):
                    value = match.group("value")
                    if entity_type == "ADDRESS_CITY" and not value[0].isupper():
                        continue
                    yield _entity(text, entity_type, match.span("value"), "address_v3_18")


def _valid_luhn(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    parity = len(digits) % 2
    total = 0
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return 13 <= len(digits) <= 19 and total % 10 == 0


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    if entity.entity_type == "PERSON":
        return bool(_PERSON_STOPWORDS.fullmatch(entity.text))
    if entity.entity_type == "PHONE_RF":
        return bool(_PUBLIC_CONTACT.search(text) or _SYNTHETIC.search(text))
    if entity.entity_type == "BIRTH_DATE":
        return _SYNTHETIC.search(text) is not None
    if entity.entity_type == "EMAIL":
        personal = _PERSONAL_EMAIL.search(text) is not None
        public = _PUBLIC_CONTACT.search(text) or _ROLE_EMAIL.search(entity.text)
        return bool(not personal and public)
    if entity.entity_type.startswith("ADDRESS_"):
        return _NONPERSON_ADDRESS.search(text) is not None
    if entity.entity_type == "BANK_CARD":
        return not _valid_luhn(entity.text) or _INVALID_CHECKSUM.search(text) is not None
    if entity.entity_type in {"PASSPORT_RF", "DIVISION_CODE", "CVV"}:
        return _TECHNICAL.search(text) is not None
    return False


def _merge(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    return merge_greedy_non_overlapping(entities)


def detect(text: str) -> list[DetectedEntity]:
    """Return production v3.13 plus clause-aware candidates and suppression."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    return [
        entity
        for entity in _merge([*production_detect(text), *_supplemental(text)])
        if not _suppressed(text, entity)
    ]
