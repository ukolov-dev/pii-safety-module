import json
from pathlib import Path

import pytest

from benchmarks.large_payload import (
    PII_BY_POSITION,
    benchmark_case,
    generate_payload,
    main,
)


def test_generator_has_exact_size_and_pii_at_all_anchors() -> None:
    generated = generate_payload(11)
    tokens = generated.text.split()

    assert generated.token_count == 11
    assert len(tokens) == 11
    assert generated.pii_token_indices == {"start": 0, "middle": 5, "end": 10}
    assert tokens[0] == PII_BY_POSITION["start"]
    assert tokens[5] == PII_BY_POSITION["middle"]
    assert tokens[10] == PII_BY_POSITION["end"]


def test_generator_rejects_payload_too_small() -> None:
    with pytest.raises(ValueError, match="at least 3"):
        generate_payload(2)


def test_small_benchmark_detects_anchors_and_round_trips() -> None:
    result = benchmark_case(20, iterations=2, warmups=0)

    assert result.actual_tokens == 20
    assert result.detected_entities == 3
    assert result.mapping_entries == 3
    assert result.exact_round_trip is True
    assert result.mask_ms_min >= 0
    assert result.unmask_ms_min >= 0
    assert result.payload_utf8_bytes > 0
    assert result.tracemalloc_peak_bytes > 0
    assert result.process_peak_rss_bytes > 0


def test_cli_writes_json_and_markdown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--sizes",
            "12,24",
            "--iterations",
            "1",
            "--warmups",
            "0",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    data = json.loads((tmp_path / "large-payload-benchmark.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "large-payload-benchmark.md").read_text(encoding="utf-8")
    assert [case["actual_tokens"] for case in data["cases"]] == [12, 24]
    assert all(case["exact_round_trip"] for case in data["cases"])
    assert "| Tokens |" in markdown
    assert "JSON:" in capsys.readouterr().out
