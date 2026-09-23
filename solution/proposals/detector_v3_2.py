"""Candidate v3.2: v3 recognizers plus ownership-aware suppression.

The filter treats a syntactically valid identifier as *potential* PII.  It is kept
unless nearby language clearly says that it belongs to an organisation, is a public
contact, or is documentation/test data.  Explicit personal ownership wins over
public-contact ambiguity, while documentation/example markers remain a hard veto.
"""

from __future__ import annotations

import re

from app.detection.models import DetectedEntity
from proposals.detector_v3 import detect as detect_v3

_PERSONAL_CUE = re.compile(
    r"\b(?:клиент\w*|заявител\w*|граждан\w*|физлиц\w*|"
    r"физическ\w*\s+лиц\w*|получател\w*|владел\w*|"
    r"личн(?:ый|ая|ое|ого)|персональн\w*|анкет\w*|"
    r"доверенност\w*\s+оформлен\w*\s+на\s+имя|"
    r"для\s+связи\s+с\s+клиент\w*)\b",
    re.IGNORECASE,
)
_DOCUMENTATION_CUE = re.compile(
    r"(?:\b(?:пример\w*|образец|шаблон\w*|инструкц\w*|"
    r"документац\w*|справк\w*|подсказк\w*|"
    r"тестов\w*|песочниц\w*|фикстур\w*|условн\w*|"
    r"маскирован\w*|токен\w*|заполнен\w*|введит\w*|вводится)\b|"
    r"\{\{[A-Z_]+_\d+}}|\b(?:TODO|DEBUG|INSERT\s+INTO|VALUES\s*\()\b|"
    r"формат\w*\s+(?:номер\w*|телефон\w*|паспорт\w*)|"
    r"адрес\w*\s+вида|//|<[^>]*пример[^>]*>)",
    re.IGNORECASE,
)
_PUBLIC_CONTACT_CUE = re.compile(
    r"\b(?:горячая\s+линия|контактн\w*\s+центр|"
    r"колл-центр|приёмн\w*|справочн\w*|служба\s+доставки|"
    r"офис\w*\s+продаж|информационн\w*\s+отдел|"
    r"отдел\s+продаж|пресс-служб\w*|контакт\w*\s+компан\w*|"
    r"резюме\s+принимаются|сообщения\s+об\s+уязвимостях|"
    r"общ\w*\s+(?:адрес|почта)|телефон\s+офис\w*)\b",
    re.IGNORECASE,
)
_ORGANISATION_CUE = re.compile(
    r"\b(?:банк\w*|организац\w*|компан\w*|офис\w*|отделен\w*|"
    r"филиал\w*|магазин\w*|склад\w*|поликлиник\w*|музе\w*|"
    r"университет\w*|юридическ\w*\s+лиц\w*|подрядчик\w*|"
    r"ооо|пао|ао)\b",
    re.IGNORECASE,
)
_NON_PERSON_IDENTIFIER_CUE = re.compile(
    r"\b(?:артефакт|идентификатор|обращение|заказ|тикет|"
    r"номер\s+сборки|журнал\w*\s+CI|код\s+склада|"
    r"счёт-фактура)\b",
    re.IGNORECASE,
)
_CULTURAL_CUE = re.compile(
    r"\b(?:автор|книг\w*|роман\w*|лекц\w*|музе\w*|биограф\w*|"
    r"поэт\w*|писател\w*|написал\w*|разработал\w*|геро\w*|"
    r"историческ\w*|картин\w*|издательств\w*|космос\w*|"
    r"перв\w*\s+человек\w*)\b",
    re.IGNORECASE,
)
_SHARED_EMAIL_LOCAL = re.compile(
    r"^(?:info|sales|press|jobs?|career|security|support|help|office|admin|"
    r"noreply|no-reply|contact|reception)(?:[+._-]|$)",
    re.IGNORECASE,
)
_INVALID_PLACE_VALUE = re.compile(
    r"^(?:указан\w*|приведен\w*|заполнен\w*|отсутствует)\b", re.IGNORECASE
)


def _window(text: str, entity: DetectedEntity, radius: int = 110) -> str:
    return text[max(0, entity.start - radius) : min(len(text), entity.end + radius)]


def _normalise_email(text: str, entity: DetectedEntity) -> DetectedEntity:
    """Exclude an adjacent ``e-mail=`` label accepted by permissive RFC characters."""

    value = entity.text
    marker = value.rfind("=")
    if marker >= 0 and re.fullmatch(r"e-?mail", value[:marker], re.IGNORECASE):
        start = entity.start + marker + 1
        return DetectedEntity(
            entity.entity_type,
            start,
            entity.end,
            text[start : entity.end],
            entity.confidence,
            "email_label_trim_v3_2",
            entity.priority,
        )
    return entity


def _keep(text: str, entity: DetectedEntity) -> bool:
    context = _window(text, entity)
    personal = _PERSONAL_CUE.search(context) is not None
    documentation = _DOCUMENTATION_CUE.search(context) is not None

    if documentation and not personal:
        return False

    if entity.entity_type == "EMAIL":
        local_part = entity.text.split("@", 1)[0]
        return personal or not (
            _SHARED_EMAIL_LOCAL.search(local_part)
            or _PUBLIC_CONTACT_CUE.search(context)
            or _ORGANISATION_CUE.search(context)
        )

    if entity.entity_type == "PHONE_RF":
        return personal or not (
            _PUBLIC_CONTACT_CUE.search(context)
            or _ORGANISATION_CUE.search(context)
            or _NON_PERSON_IDENTIFIER_CUE.search(context)
        )

    if entity.entity_type == "INN":
        return personal or not (
            _ORGANISATION_CUE.search(context) or _NON_PERSON_IDENTIFIER_CUE.search(context)
        )

    if entity.entity_type == "BANK_CARD":
        return personal or not _NON_PERSON_IDENTIFIER_CUE.search(context)

    if entity.entity_type == "PERSON":
        return personal or not _CULTURAL_CUE.search(context)

    if entity.entity_type.startswith("ADDRESS_"):
        return personal or not _ORGANISATION_CUE.search(context)

    if entity.entity_type == "PLACE_OF_BIRTH":
        return _INVALID_PLACE_VALUE.search(entity.text) is None

    return True


def detect(text: str) -> list[DetectedEntity]:
    """Run v3 and remove candidates that lack personal ownership in negative contexts."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []
    result: list[DetectedEntity] = []
    for raw_entity in detect_v3(text):
        entity = (
            _normalise_email(text, raw_entity)
            if raw_entity.entity_type == "EMAIL"
            else raw_entity
        )
        if _keep(text, entity):
            result.append(entity)
    return result
