"""Candidate v3.1: v3 recognizers plus a general false-positive suppression layer.

This module is deliberately isolated from the production detector.  Suppression is
based on semantic context classes (documentation, organisation-owned contacts,
non-personal identifiers, and cultural/bibliographic discourse), not benchmark IDs
or exact test values.
"""

from __future__ import annotations

import re

from app.detection.models import DetectedEntity
from proposals.detector_v3 import detect as detect_v3

_DOCUMENTATION_CONTEXT = re.compile(
    r"\b(?:\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\w*|\u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\w*|\u043e\u0431\u0440\u0430\u0437\u0435\u0446|\u043f\u0440\u0438\u043c\u0435\u0440(?:\u0430|\u0435|\u043e\u043c)?|\u0448\u0430\u0431\u043b\u043e\u043d|"
    r"\u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\w*|\u0444\u043e\u0440\u043c\u0430\u0442\s+(?:\u043d\u043e\u043c\u0435\u0440\u0430|\u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430)|\u0443\u0441\u043b\u043e\u0432\u043d\w*|\u0443\u0447\u0435\u0431\u043d\w*|"
    r"\u043f\u0435\u0441\u043e\u0447\u043d\u0438\w*|\u0442\u0435\u0441\u0442\u043e\u0432\w*|sandbox|fixture|placeholder|sample)\b",
    re.IGNORECASE,
)
_CODE_OR_LOG_CONTEXT = re.compile(
    r"(?:\b(?:debug|trace|insert\s+into|todo|recipient\s*=|build|artifact)\b|//|\{\{[A-Z_]+_\d+\}\})",
    re.IGNORECASE,
)
_PUBLIC_CONTACT_CONTEXT = re.compile(
    r"\b(?:\u0433\u043e\u0440\u044f\u0447\u0430\u044f\s+\u043b\u0438\u043d\u0438\u044f|\u043a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u044b\u0439\s+\u0446\u0435\u043d\u0442\u0440|\u043f\u0440\u0438[\u0435\u0451]\u043c\u043d\w*|\u0441\u043f\u0440\u0430\u0432\u043e\u0447\u043d\w*|"
    r"\u0441\u043b\u0443\u0436\u0431\u0430\s+(?:\u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438|\u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0438)|\u043e\u0442\u0434\u0435\u043b\s+(?:\u043f\u0440\u043e\u0434\u0430\u0436|\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0438)|"
    r"\u043f\u0440\u0435\u0441\u0441[- ]\u0441\u043b\u0443\u0436\u0431\w*|"
    r"\u043a\u043e\u043c\u043c\u0435\u0440\u0447\u0435\u0441\u043a\u0438\u0435\s+\u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f|"
    r"\u0440\u0435\u0437\u044e\u043c\u0435\s+\u043f\u0440\u0438\u043d\u0438\u043c\u0430\u044e\u0442\u0441\u044f|"
    r"\u0442\u0435\u043b\u0435\u0444\u043e\u043d\s+(?:\u043e\u0444\u0438\u0441\u0430|\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438|\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438)|\u043a\u043e\u043d\u0442\u0430\u043a\u0442\u044b\s+\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438)\b",
    re.IGNORECASE,
)
_ORGANISATION_CONTEXT = re.compile(
    r"\b(?:\u0431\u0430\u043d\u043a|\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\w*|\u043a\u043e\u043c\u043f\u0430\u043d\u0438\w*|\u043e\u0444\u0438\u0441|\u043e\u0442\u0434\u0435\u043b\u0435\u043d\u0438\w*|\u0444\u0438\u043b\u0438\u0430\u043b|\u043c\u0430\u0433\u0430\u0437\u0438\u043d|"
    r"\u0441\u043a\u043b\u0430\u0434|\u043c\u0443\u0437\u0435\u0439|\u0443\u043d\u0438\u0432\u0435\u0440\u0441\u0438\u0442\u0435\u0442|\u043f\u043e\u043b\u0438\u043a\u043b\u0438\u043d\u0438\u043a\u0430|\u043e\u043e\u043e|\u043f\u0430\u043e|\u0430\u043e)\b",
    re.IGNORECASE,
)
_NONPERSONAL_IDENTIFIER_CONTEXT = re.compile(
    r"\b(?:\u0437\u0430\u043a\u0430\u0437|\u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\w*|\u0442\u0438\u043a\u0435\u0442|\u0430\u0440\u0442\u0438\u043a\u0443\u043b|\u0441\u0431\u043e\u0440\u043a\w*|\u0430\u0440\u0442\u0435\u0444\u0430\u043a\u0442|\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440)\b",
    re.IGNORECASE,
)
_NONPERSONAL_PERSON_CONTEXT = re.compile(
    r"\b(?:\u043b\u0435\u043a\u0446\u0438\w*|\u0443\u0440\u043e\u043a\w*|\u043c\u0443\u0437\u0435\u0439|\u0431\u0438\u043e\u0433\u0440\u0430\u0444\u0438\w*|\u0430\u0432\u0442\u043e\u0440\s+\u043a\u043d\u0438\u0433\u0438|\u0440\u043e\u043c\u0430\u043d\w*|"
    r"\u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\w*|\u043f\u0438\u0441\u0430\u0442\u0435\u043b\w*|\u0445\u0443\u0434\u043e\u0436\u043d\u0438\u043a\w*|\u0443\u0441\u043b\u043e\u0432\u043d\w*\s+\u0433\u0435\u0440\u043e\u0439|\u0443\u0447\u0435\u0431\u043d\w*\s+\u043f\u0440\u0438\u043c\u0435\u0440)\b",
    re.IGNORECASE,
)
_PERSONAL_CONTEXT = re.compile(
    r"\b(?:\u043a\u043b\u0438\u0435\u043d\u0442\w*|\u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\w*|\u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\w*|\u0432\u043b\u0430\u0434\u0435\u043b\u044c\u0446\w*|\u0433\u0440\u0430\u0436\u0434\u0430\u043d\w*|"
    r"\u0444\u0438\u0437(?:\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e\s+\u043b\u0438\u0446\u0430|\u043b\u0438\u0446\u043e)|\u043b\u0438\u0447\u043d\w*|\u0430\u043d\u043a\u0435\u0442\w*)\b",
    re.IGNORECASE,
)

_DOCUMENT_SENSITIVE_TYPES = {
    "BANK_CARD",
    "BIRTH_DATE",
    "CVV",
    "DIVISION_CODE",
    "DRIVER_LICENSE_RF",
    "EMAIL",
    "PASSPORT_ISSUE_DATE",
    "PASSPORT_RF",
    "PHONE_RF",
    "PIN",
}
_IDENTIFIER_TYPES = {"BANK_CARD", "INN", "PHONE_RF"}
_ADDRESS_TYPES = {
    "ADDRESS_APARTMENT",
    "ADDRESS_CITY",
    "ADDRESS_COUNTRY",
    "ADDRESS_HOUSE",
    "ADDRESS_POSTAL_CODE",
    "ADDRESS_STREET",
}


def _sentence(text: str, start: int, end: int) -> str:
    """Return bounded local discourse without coupling suppression to full payloads."""

    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start), text.rfind(";", 0, start))
    stops = [position for marker in (".", "\n", ";") if (position := text.find(marker, end)) >= 0]
    right = min(stops) if stops else len(text)
    return text[left + 1 : right]


def _normalize_email(text: str, entity: DetectedEntity) -> DetectedEntity:
    """Remove an unquoted field assignment accidentally consumed as local-part text."""

    value = entity.text
    at = value.rfind("@")
    equals = value.rfind("=", 0, at)
    trim = equals + 1 if equals >= 0 else 0
    while trim < len(value) and value[trim] in "<'\"([{":
        trim += 1
    if trim == 0:
        return entity
    start = entity.start + trim
    return DetectedEntity(
        entity.entity_type,
        start,
        entity.end,
        text[start : entity.end],
        entity.confidence,
        f"{entity.source}+boundary_v3_1",
        entity.priority,
    )


def _suppressed(text: str, entity: DetectedEntity) -> bool:
    context = _sentence(text, entity.start, entity.end)
    personal = _PERSONAL_CONTEXT.search(context) is not None

    if entity.entity_type in _DOCUMENT_SENSITIVE_TYPES and (
        _DOCUMENTATION_CONTEXT.search(context) or _CODE_OR_LOG_CONTEXT.search(context)
    ):
        return True
    if entity.entity_type in {"EMAIL", "PHONE_RF"} and not personal:
        if _PUBLIC_CONTACT_CONTEXT.search(context) or _ORGANISATION_CONTEXT.search(context):
            return True
    if entity.entity_type in _IDENTIFIER_TYPES and not personal:
        if _NONPERSONAL_IDENTIFIER_CONTEXT.search(context):
            return True
    if entity.entity_type == "INN" and not personal:
        if _ORGANISATION_CONTEXT.search(context) or "\u0438\u043d\u043d" not in context.lower():
            return True
    if entity.entity_type == "PERSON" and _NONPERSONAL_PERSON_CONTEXT.search(context):
        return True
    if entity.entity_type in _ADDRESS_TYPES and _ORGANISATION_CONTEXT.search(context):
        return True
    return False


def detect(text: str) -> list[DetectedEntity]:
    """Run unchanged v3 recognizers, normalize spans, then suppress contextual FP."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    entities: list[DetectedEntity] = []
    for raw in detect_v3(text):
        entity = _normalize_email(text, raw) if raw.entity_type == "EMAIL" else raw
        if not _suppressed(text, entity):
            entities.append(entity)
    return entities
