"""Benchmark masking and restoration of large, deterministic payloads.

Run from the ``solution`` directory::

    python -m benchmarks.large_payload --output-dir benchmark-results
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import resource
import statistics
import sys
import time
import tracemalloc
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from app.detection import detect
from app.masking import mask_text, unmask_text

DEFAULT_SIZES = (1_000, 10_000, 100_000)
PII_BY_POSITION = {
    "start": "start.person@example.ru",
    "middle": "+79991234567",
    "end": "7707083893",
}
_FILLER_WORDS = (
    "договор",
    "обработка",
    "запрос",
    "система",
    "документ",
    "проверка",
    "данные",
    "операция",
)


@dataclass(frozen=True, slots=True)
class GeneratedPayload:
    """A deterministic payload and the token indices containing PII."""

    text: str
    token_count: int
    pii_token_indices: dict[str, int]


@dataclass(frozen=True, slots=True)
class CaseResult:
    target_tokens: int
    actual_tokens: int
    payload_utf8_bytes: int
    masked_utf8_bytes: int
    detected_entities: int
    mapping_entries: int
    iterations: int
    mask_ms_min: float
    mask_ms_median: float
    mask_ms_p95: float
    mask_ms_max: float
    unmask_ms_min: float
    unmask_ms_median: float
    unmask_ms_p95: float
    unmask_ms_max: float
    tracemalloc_peak_bytes: int
    process_peak_rss_bytes: int
    exact_round_trip: bool
    pii_positions: dict[str, int]


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    schema_version: int
    python_version: str
    warmups: int
    cases: list[CaseResult]


def generate_payload(token_count: int) -> GeneratedPayload:
    """Generate exactly ``token_count`` whitespace tokens with PII at 3 anchors."""

    if token_count < 3:
        raise ValueError("token_count must be at least 3")

    words = [_FILLER_WORDS[index % len(_FILLER_WORDS)] for index in range(token_count)]
    positions = {"start": 0, "middle": token_count // 2, "end": token_count - 1}
    for name, index in positions.items():
        words[index] = PII_BY_POSITION[name]
    text = " ".join(words)
    return GeneratedPayload(text=text, token_count=len(words), pii_token_indices=positions)


def _percentile_95(values: Sequence[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _latency_stats(values: Sequence[float]) -> tuple[float, float, float, float]:
    return min(values), statistics.median(values), _percentile_95(values), max(values)


def _peak_rss_bytes() -> int:
    """Normalize ``ru_maxrss`` to bytes (bytes on macOS, KiB elsewhere)."""

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _run_once(payload: str) -> tuple[float, float, int, int, int, bool]:
    gc.collect()
    tracemalloc.start()
    try:
        mask_started = time.perf_counter_ns()
        entities = detect(payload)
        masked = mask_text(payload, entities)
        mask_ms = (time.perf_counter_ns() - mask_started) / 1_000_000

        unmask_started = time.perf_counter_ns()
        restored = unmask_text(masked.text, masked.mapping)
        unmask_ms = (time.perf_counter_ns() - unmask_started) / 1_000_000
        _, traced_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return (
        mask_ms,
        unmask_ms,
        len(entities),
        len(masked.mapping),
        traced_peak,
        restored == payload,
    )


def benchmark_case(token_count: int, *, iterations: int, warmups: int) -> CaseResult:
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if warmups < 0:
        raise ValueError("warmups must not be negative")

    generated = generate_payload(token_count)
    for _ in range(warmups):
        _run_once(generated.text)

    mask_samples: list[float] = []
    unmask_samples: list[float] = []
    traced_peaks: list[int] = []
    entity_count = 0
    mapping_entries = 0
    exact_round_trip = True
    masked_size = 0

    for _ in range(iterations):
        mask_ms, unmask_ms, entity_count, mapping_entries, traced_peak, exact = _run_once(
            generated.text
        )
        mask_samples.append(mask_ms)
        unmask_samples.append(unmask_ms)
        traced_peaks.append(traced_peak)
        exact_round_trip = exact_round_trip and exact

        # Rebuild only to capture the representative serialized output size.
        # It is intentionally outside the timed samples.
        masked_size = len(mask_text(generated.text, detect(generated.text)).text.encode("utf-8"))

    mask_min, mask_median, mask_p95, mask_max = _latency_stats(mask_samples)
    unmask_min, unmask_median, unmask_p95, unmask_max = _latency_stats(unmask_samples)
    return CaseResult(
        target_tokens=token_count,
        actual_tokens=generated.token_count,
        payload_utf8_bytes=len(generated.text.encode("utf-8")),
        masked_utf8_bytes=masked_size,
        detected_entities=entity_count,
        mapping_entries=mapping_entries,
        iterations=iterations,
        mask_ms_min=mask_min,
        mask_ms_median=mask_median,
        mask_ms_p95=mask_p95,
        mask_ms_max=mask_max,
        unmask_ms_min=unmask_min,
        unmask_ms_median=unmask_median,
        unmask_ms_p95=unmask_p95,
        unmask_ms_max=unmask_max,
        tracemalloc_peak_bytes=max(traced_peaks),
        process_peak_rss_bytes=_peak_rss_bytes(),
        exact_round_trip=exact_round_trip,
        pii_positions=generated.pii_token_indices,
    )


def run_benchmark(
    sizes: Sequence[int], *, iterations: int = 3, warmups: int = 1
) -> BenchmarkReport:
    cases = [
        benchmark_case(size, iterations=iterations, warmups=warmups)
        for size in sizes
    ]
    return BenchmarkReport(
        schema_version=1,
        python_version=sys.version.split()[0],
        warmups=warmups,
        cases=cases,
    )


def render_markdown(report: BenchmarkReport) -> str:
    lines = [
        "# Large payload benchmark",
        "",
        f"Python: `{report.python_version}`. Warm-up runs per size: {report.warmups}.",
        "",
        "| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | "
        "Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for case in report.cases:
        lines.append(
            f"| {case.actual_tokens:,} | {case.payload_utf8_bytes / 1_048_576:.3f} | "
            f"{case.detected_entities} | {case.mask_ms_median:.3f} | {case.mask_ms_p95:.3f} | "
            f"{case.unmask_ms_median:.3f} | {case.unmask_ms_p95:.3f} | "
            f"{case.tracemalloc_peak_bytes / 1_048_576:.3f} | "
            f"{case.process_peak_rss_bytes / 1_048_576:.3f} | "
            f"{'yes' if case.exact_round_trip else 'NO'} |"
        )
    lines.extend(
        [
            "",
            "`Mask` includes entity detection and token substitution. `Unmask` measures "
            "exact token restoration. RSS is the process-wide peak reported by the operating "
            "system; trace peak is Python allocation memory measured separately for each "
            "iteration.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: BenchmarkReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "large-payload-benchmark.json"
    markdown_path = output_dir / "large-payload-benchmark.md"
    json_path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _parse_sizes(raw: str) -> list[int]:
    try:
        sizes = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers") from error
    if not sizes or any(size < 3 for size in sizes):
        raise argparse.ArgumentTypeError("every size must be at least 3")
    return sizes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=list(DEFAULT_SIZES),
        help="comma-separated whitespace-token counts (default: 1000,10000,100000)",
    )
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark-results"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")
    if args.warmups < 0:
        raise SystemExit("--warmups must not be negative")
    report = run_benchmark(args.sizes, iterations=args.iterations, warmups=args.warmups)
    json_path, markdown_path = write_report(report, args.output_dir)
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0 if all(case.exact_round_trip for case in report.cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
