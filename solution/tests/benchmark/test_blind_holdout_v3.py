import json
from pathlib import Path
from typing import Any, cast

from benchmark.evaluate_quality import resolve_gold

DATASET_PATH = Path(__file__).parents[2] / "benchmark" / "blind_holdout_v3.json"


REQUIRED_TYPES = {
    "PERSON",
    "EMAIL",
    "PHONE_RF",
    "INN",
    "BANK_CARD",
    "PASSPORT_RF",
    "DIVISION_CODE",
    "BIRTH_DATE",
    "PLACE_OF_BIRTH",
    "CITIZENSHIP",
    "PASSPORT_ISSUER",
    "PASSPORT_ISSUE_DATE",
    "DRIVER_LICENSE_RF",
    "ADDRESS_COUNTRY",
    "ADDRESS_POSTAL_CODE",
    "ADDRESS_CITY",
    "ADDRESS_STREET",
    "ADDRESS_HOUSE",
    "ADDRESS_APARTMENT",
    "CVV",
    "PIN",
    "CARDHOLDER_NAME",
}


def _load() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(DATASET_PATH.read_text(encoding="utf-8")))


def test_blind_holdout_v3_loads_and_has_unique_bounded_cases() -> None:
    dataset = _load()
    cases = dataset["cases"]
    ids = [case["id"] for case in cases]

    assert dataset["name"] == "ru_pii_blind_holdout_v3"
    assert dataset["version"] == 3
    assert 50 <= len(cases) <= 80
    assert len(ids) == len(set(ids))


def test_blind_holdout_v3_annotations_resolve_to_valid_nonoverlapping_spans() -> None:
    for case in _load()["cases"]:
        gold = resolve_gold(case["text"], case["entities"])
        assert len(gold) == len(case["entities"]), case["id"]
        assert all(entity.text == case["text"][entity.start : entity.end] for entity in gold)


def test_blind_holdout_v3_covers_types_dimensions_and_hard_negatives() -> None:
    cases = _load()["cases"]
    covered_types = {entity["type"] for case in cases for entity in case["entities"]}
    dimensions = {dimension for case in cases for dimension in case["dimensions"]}
    negatives = [case for case in cases if not case["entities"]]

    assert covered_types == REQUIRED_TYPES
    assert {"case", "label", "format", "punctuation", "mixed_case", "multiple"} <= dimensions
    assert {"corporate_contact", "public_contact", "checksum", "address_one_line"} <= dimensions
    assert len(negatives) >= 15
