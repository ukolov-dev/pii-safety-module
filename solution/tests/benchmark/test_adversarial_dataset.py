import json
from pathlib import Path
from typing import Any, cast

from benchmark.evaluate_quality import resolve_gold

DATASET_PATH = Path(__file__).parents[2] / "benchmark" / "adversarial_dataset.json"


def _load_dataset() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(DATASET_PATH.read_text(encoding="utf-8")))


def test_adversarial_dataset_loads_and_has_unique_cases() -> None:
    dataset = _load_dataset()

    assert dataset["name"] == "ru_pii_adversarial_v1"
    assert dataset["version"] == 1
    assert 20 <= len(dataset["cases"]) <= 30
    case_ids = [case["id"] for case in dataset["cases"]]
    assert len(case_ids) == len(set(case_ids))


def test_adversarial_dataset_annotations_are_valid_exact_spans() -> None:
    dataset = _load_dataset()

    for case in dataset["cases"]:
        assert isinstance(case["text"], str) and case["text"]
        assert isinstance(case["entities"], list)
        gold = resolve_gold(case["text"], case["entities"])
        assert all(case["text"][entity.start : entity.end] == entity.text for entity in gold)


def test_adversarial_dataset_covers_required_types_and_negative_cases() -> None:
    dataset = _load_dataset()
    entity_types = {
        entity["type"]
        for case in dataset["cases"]
        for entity in case["entities"]
    }
    required_types = {
        "PERSON",
        "BIRTH_DATE",
        "PLACE_OF_BIRTH",
        "PASSPORT_RF",
        "CITIZENSHIP",
        "PASSPORT_ISSUER",
        "DIVISION_CODE",
        "PASSPORT_ISSUE_DATE",
        "DRIVER_LICENSE_RF",
        "ADDRESS_COUNTRY",
        "ADDRESS_POSTAL_CODE",
        "ADDRESS_CITY",
        "ADDRESS_STREET",
        "ADDRESS_HOUSE",
        "ADDRESS_APARTMENT",
        "EMAIL",
        "PHONE_RF",
        "INN",
        "BANK_CARD",
        "CVV",
        "PIN",
        "CARDHOLDER_NAME",
    }

    assert required_types <= entity_types
    assert sum(not case["entities"] for case in dataset["cases"]) >= 7
