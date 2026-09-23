"""Efficient greedy resolution of overlapping detection candidates."""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Iterable

from .models import DetectedEntity


def spans_overlap(left: DetectedEntity, right: DetectedEntity) -> bool:
    """Return whether two non-empty half-open spans overlap."""

    return left.start < right.end and right.start < left.end


def merge_greedy_non_overlapping(
    entities: Iterable[DetectedEntity], *, entity_type_tiebreak: bool = False
) -> list[DetectedEntity]:
    """Return the exact result of the detectors' priority-first greedy merge.

    Once a candidate is accepted, overlap checks only need the maximum end of
    an accepted interval whose start is before the candidate's end.  A Fenwick
    tree over compressed start offsets answers that query and records accepted
    intervals in ``O(log n)`` time.  Ranking and final ordering deliberately
    match the legacy implementation, including its optional entity-type tie
    break.
    """

    candidates = list(entities)
    if entity_type_tiebreak:
        ranked = sorted(
            candidates,
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
            candidates,
            key=lambda item: (
                -item.priority,
                -item.confidence,
                -(item.end - item.start),
                item.start,
            ),
        )

    starts = sorted({item.start for item in ranked})
    prefix_max_tree = [-1] * (len(starts) + 1)

    def accepted_max_end_before(stop: int) -> int:
        index = bisect_left(starts, stop)
        maximum = -1
        while index:
            maximum = max(maximum, prefix_max_tree[index])
            index -= index & -index
        return maximum

    def record_accepted(item: DetectedEntity) -> None:
        index = bisect_left(starts, item.start) + 1
        while index < len(prefix_max_tree):
            prefix_max_tree[index] = max(prefix_max_tree[index], item.end)
            index += index & -index

    accepted: list[DetectedEntity] = []
    for item in ranked:
        if accepted_max_end_before(item.end) <= item.start:
            accepted.append(item)
            record_accepted(item)

    return sorted(accepted, key=lambda item: (item.start, item.end, item.entity_type))
