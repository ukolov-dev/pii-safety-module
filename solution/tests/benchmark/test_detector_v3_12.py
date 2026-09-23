import json
from pathlib import Path

from app.masking import mask_text, unmask_text
from proposals.compare_detector_v3_12 import DATASETS, compare_all
from proposals.detector_v3_12 import detect

BENCHMARK_ROOT = Path(__file__).parents[2] / "benchmark"


def test_v3_12_uses_only_disclosed_datasets() -> None:
    assert DATASETS[-1] == "sealed_holdout_v8.json"
    assert all("v9" not in filename for filename in DATASETS)


def test_v3_12_disclosed_gates() -> None:
    report = compare_all(BENCHMARK_ROOT)
    v8 = report["sealed_holdout_v8.json"]
    assert v8["candidate_v3_12"]["f1"] >= v8["production_v3_3"]["f1"] + 0.10
    for comparison in report.values():
        assert (
            comparison["candidate_v3_12"]["precision"]
            >= comparison["production_v3_3"]["precision"]
        )


def test_v3_12_round_trip_on_every_disclosed_case() -> None:
    for filename in DATASETS:
        dataset = json.loads((BENCHMARK_ROOT / filename).read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            text = case["text"]
            masked = mask_text(text, detect(text))
            assert unmask_text(masked.text, masked.mapping) == text


def test_v3_12_semantic_ownership_examples() -> None:
    personal = "Претензия составлена Орловой Еленой Павловной."
    dot_card = "Персональный платёжный PAN: 5555.5555.5555.4444."
    public = "Номер отдела доставки +7 495 123-45-67, не личный."
    technical = "Технический паспорт прибора содержит номер 45 08 123456."

    assert [(item.entity_type, item.text) for item in detect(personal)] == [
        ("PERSON", "Орловой Еленой Павловной")
    ]
    assert [(item.entity_type, item.text) for item in detect(dot_card)] == [
        ("BANK_CARD", "5555.5555.5555.4444")
    ]
    assert detect(public) == []
    assert detect(technical) == []
