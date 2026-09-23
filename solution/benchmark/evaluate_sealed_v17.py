"""Evaluate immutable v17 through the repository quality evaluator."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from app.detection.detector_v3_26 import detect as detect_326
from app.detection.detector_v3_27 import detect as detect_327
from benchmark import evaluate_quality as quality

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "sealed_holdout_v17.json"
EXPECTED_SHA256 = "712f47ed951bc788d3a7000ff26586e01cf365cdc1a78698a05f82c54955024f"
TYPE_MAP = {
    "full_name": "PERSON",
    "date_of_birth": "BIRTH_DATE",
    "place_of_birth": "PLACE_OF_BIRTH",
    "passport": "PASSPORT_RF",
    "citizenship": "CITIZENSHIP",
    "passport_issuer": "PASSPORT_ISSUER",
    "department_code": "DIVISION_CODE",
    "passport_issue_date": "PASSPORT_ISSUE_DATE",
    "driver_license": "DRIVER_LICENSE_RF",
    "address": "ADDRESS",
    "country": "ADDRESS_COUNTRY",
    "postal_code": "ADDRESS_POSTAL_CODE",
    "city": "ADDRESS_CITY",
    "street": "ADDRESS_STREET",
    "house": "ADDRESS_HOUSE",
    "apartment": "ADDRESS_APARTMENT",
    "email": "EMAIL",
    "phone": "PHONE_RF",
    "inn": "INN",
    "bank_card": "BANK_CARD",
    "cvv": "CVV",
    "pin": "PIN",
    "cardholder_name": "CARDHOLDER_NAME",
}


def load_dataset():
    raw = DATASET_PATH.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"sealed dataset hash mismatch: {actual}")
    source = json.loads(raw)
    return {
        "name": "sealed_holdout_v17",
        "version": source["version"],
        "sources": source["requirements_sources"],
        "cases": [
            {
                "id": case["id"],
                "text": case["text"],
                "entities": [
                    {"type": TYPE_MAP[e["type"]], "value": e["value"]}
                    for e in case["expected_entities"]
                ],
            }
            for case in source["cases"]
        ],
    }


def run(name, detector, dataset):
    quality.detect = detector
    report = quality.evaluate_dataset(dataset)
    report["detector"] = name
    exact = sum(not c["missing"] and not c["unexpected"] for c in report["cases"])
    report["exact_case"] = {
        "passed": exact,
        "total": report["case_count"],
        "rate": exact / report["case_count"],
    }
    missing, unexpected = Counter(), Counter()
    for case in report["cases"]:
        missing.update(x[0] for x in case["missing"])
        unexpected.update(x[0] for x in case["unexpected"])
    report["top_error_categories"] = {
        "missing": missing.most_common(12),
        "unexpected": unexpected.most_common(12),
    }
    out = ROOT / "results" / f"sealed_holdout_v17_{name.replace('.', '')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    dataset = load_dataset()
    reports = [run("v3.26", detect_326, dataset), run("v3.27", detect_327, dataset)]
    summary = {
        r["detector"]: {
            k: r[k]
            for k in (
                "case_count",
                "overall",
                "exact_case",
                "mask_exact",
                "round_trip_exact",
                "top_error_categories",
            )
        }
        for r in reports
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
