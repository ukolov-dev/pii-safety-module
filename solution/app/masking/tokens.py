"""Deterministic typed-token masking and exact restoration."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol


class EntitySpan(Protocol):
    @property
    def entity_type(self) -> str: ...

    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...

    @property
    def text(self) -> str: ...


@dataclass(frozen=True, slots=True)
class MaskingResult:
    text: str
    mapping: dict[str, str]


_TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*_[1-9]\d*\}\}")


def mask_text(text: str, entities: Iterable[EntitySpan]) -> MaskingResult:
    """Replace non-overlapping entity spans with stable typed tokens."""

    ordered = sorted(entities, key=lambda item: (item.start, item.end))
    last_end = 0
    counters: defaultdict[str, int] = defaultdict(int)
    value_tokens: dict[tuple[str, str], str] = {}
    mapping: dict[str, str] = {}
    parts: list[str] = []

    for entity in ordered:
        if entity.start < last_end:
            raise ValueError("mask_text received overlapping entity spans")
        if text[entity.start : entity.end] != entity.text:
            raise ValueError("entity offsets do not match source text")

        parts.append(text[last_end : entity.start])
        key = (entity.entity_type, entity.text)
        token = value_tokens.get(key)
        if token is None:
            counters[entity.entity_type] += 1
            token = f"{{{{{entity.entity_type}_{counters[entity.entity_type]}}}}}"
            value_tokens[key] = token
            mapping[token] = entity.text
        parts.append(token)
        last_end = entity.end

    parts.append(text[last_end:])
    return MaskingResult(text="".join(parts), mapping=mapping)


def unmask_text(text: str, mapping: Mapping[str, str]) -> str:
    """Restore only tokens present in this payload's mapping."""

    if not mapping:
        return text

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return mapping.get(token, token)

    return _TOKEN_RE.sub(replace, text)
