from benchmark.evaluate_quality import Counts, evaluate_dataset, render_markdown, resolve_gold


def test_resolve_gold_handles_repeated_values() -> None:
    text = "user@example.org and user@example.org"
    gold = resolve_gold(
        text,
        [
            {"type": "EMAIL", "value": "user@example.org", "occurrence": 0},
            {"type": "EMAIL", "value": "user@example.org", "occurrence": 1},
        ],
    )

    assert [(entity.start, entity.end) for entity in gold] == [(0, 16), (21, 37)]


def test_counts_calculates_metrics() -> None:
    counts = Counts(true_positive=3, false_positive=1, false_negative=2)

    assert counts.precision == 0.75
    assert counts.recall == 0.6
    assert counts.f1 == 2 / 3


def test_evaluate_dataset_reports_detection_mask_and_round_trip() -> None:
    dataset = {
        "name": "fixture",
        "version": 1,
        "sources": ["source.md"],
        "cases": [
            {
                "id": "detected",
                "text": "Email: user@example.org",
                "entities": [{"type": "EMAIL", "value": "user@example.org"}],
            },
            {
                "id": "missed",
                "text": "Личный код: AB-42",
                "entities": [{"type": "CUSTOM", "value": "AB-42"}],
            },
        ],
    }

    report = evaluate_dataset(dataset)

    assert report["overall"]["true_positive"] == 1
    assert report["overall"]["false_negative"] == 1
    assert report["overall"]["recall"] == 0.5
    assert report["mask_exact"] == {"passed": 1, "total": 2, "rate": 0.5}
    assert report["round_trip_exact"] == {"passed": 2, "total": 2, "rate": 1.0}


def test_render_markdown_contains_overall_and_type_metrics() -> None:
    report = evaluate_dataset(
        {
            "name": "fixture",
            "version": 1,
            "sources": [],
            "cases": [
                {
                    "id": "email",
                    "text": "user@example.org",
                    "entities": [{"type": "EMAIL", "value": "user@example.org"}],
                }
            ],
        }
    )

    markdown = render_markdown(report)

    assert "| Precision | 100.00% |" in markdown
    assert "| EMAIL | 1 | 0 | 0 |" in markdown
