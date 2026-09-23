"""Regression tests for the shared overlap resolver."""

from __future__ import annotations

import random
import time
from collections.abc import Iterable

import pytest

from app.detection.models import DetectedEntity
from app.detection.overlap import merge_greedy_non_overlapping


def _legacy_merge(
    entities: Iterable[DetectedEntity], *, entity_type_tiebreak: bool
) -> list[DetectedEntity]:
    if entity_type_tiebreak:
        ranked = sorted(
            entities,
            key=lambda item: (
                -item.priority,
                -item.confidence,
                -(item.end - item.start),
                item.start,
                item.entity_type,
            ),
        )
    else:
        ranked = sorted(
            entities,
            key=lambda item: (
                -item.priority,
                -item.confidence,
                -(item.end - item.start),
                item.start,
            ),
        )

    accepted: list[DetectedEntity] = []
    for candidate in ranked:
        if not any(
            candidate.start < current.end and current.start < candidate.end
            for current in accepted
        ):
            accepted.append(candidate)
    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))


def _entity(
    *, start: int, end: int, index: int, priority: int, confidence: float
) -> DetectedEntity:
    return DetectedEntity(
        entity_type=("EMAIL", "PHONE", "PASSPORT_RF")[index % 3],
        start=start,
        end=end,
        text="x" * (end - start),
        confidence=confidence,
        source=f"random-{index}",
        priority=priority,
    )


@pytest.mark.parametrize("entity_type_tiebreak", [False, True])
def test_matches_legacy_greedy_result_on_randomized_intervals(
    entity_type_tiebreak: bool,
) -> None:
    randomizer = random.Random(0xA1FA)
    for _ in range(500):
        entities = []
        for index in range(randomizer.randrange(0, 120)):
            start = randomizer.randrange(0, 250)
            end = start + randomizer.randrange(1, 50)
            entities.append(
                _entity(
                    start=start,
                    end=end,
                    index=index,
                    priority=randomizer.randrange(0, 5),
                    confidence=randomizer.choice((0.5, 0.75, 0.9, 0.99)),
                )
            )
        randomizer.shuffle(entities)

        expected = _legacy_merge(
            entities,
            entity_type_tiebreak=entity_type_tiebreak,
        )
        actual = merge_greedy_non_overlapping(
            (entity for entity in entities),
            entity_type_tiebreak=entity_type_tiebreak,
        )

        assert actual == expected


def test_thousands_of_disjoint_entities_do_not_regress_quadratically() -> None:
    entities = [
        _entity(
            start=index * 3,
            end=index * 3 + 1,
            index=index,
            priority=index % 7,
            confidence=0.9,
        )
        for index in range(20_000)
    ]

    started = time.perf_counter()
    actual = merge_greedy_non_overlapping(entities)
    elapsed = time.perf_counter() - started

    assert actual == sorted(entities, key=lambda item: (item.start, item.end, item.entity_type))
    assert elapsed < 1.0
