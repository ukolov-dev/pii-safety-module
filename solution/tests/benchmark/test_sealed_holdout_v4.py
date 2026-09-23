import json
from pathlib import Path
from typing import Any, cast

from benchmark.evaluate_quality import resolve_gold

DATASET_PATH = Path(__file__).parents[2] / "benchmark" / "sealed_holdout_v4.json"


def _load() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(DATASET_PATH.read_text(encoding="utf-8")))


def test_sealed_holdout_v4_is_structurally_valid() -> None:
    dataset = _load()
    cases = dataset["cases"]
    case_ids = [case["id"] for case in cases]

    assert dataset["name"] == "ru_pii_sealed_holdout_v4"
    assert dataset["version"] == 4
    assert 50 <= len(cases) <= 70
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        gold = resolve_gold(case["text"], case["entities"])
        assert len(gold) == len(case["entities"]), case["id"]
        assert all(entity.text == case["text"][entity.start : entity.end] for entity in gold)
