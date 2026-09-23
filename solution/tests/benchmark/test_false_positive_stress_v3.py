import json
from pathlib import Path

from benchmark.evaluate_quality import resolve_gold

DATASET_PATH = (
    Path(__file__).parents[2] / "benchmark" / "false_positive_stress_v3.json"
)


def _load() -> dict[str, object]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_false_positive_stress_dataset_shape_and_unique_ids() -> None:
    dataset = _load()
    cases = dataset["cases"]
    assert isinstance(cases, list)
    assert dataset["name"] == "ru_pii_false_positive_stress_v3"
    assert dataset["version"] == 3
    assert len(cases) >= 50
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))


def test_false_positive_stress_is_predominantly_negative() -> None:
    cases = _load()["cases"]
    negative_count = sum(not case["entities"] for case in cases)
    assert negative_count >= 50
    assert negative_count / len(cases) >= 0.80


def test_false_positive_stress_annotations_are_valid_exact_spans() -> None:
    for case in _load()["cases"]:
        resolved = resolve_gold(case["text"], case["entities"])
        assert all(case["text"][item.start : item.end] == item.text for item in resolved)


def test_false_positive_stress_covers_requested_negative_families() -> None:
    ids = {case["id"] for case in _load()["cases"] if not case["entities"]}
    required_prefixes = {
        "neg-public-phone",
        "neg-public-email",
        "neg-org-",
        "neg-order-",
        "neg-famous-",
        "neg-organization-address",
        "neg-doc-",
        "neg-placeholder-",
    }
    assert all(any(case_id.startswith(prefix) for case_id in ids) for prefix in required_prefixes)
