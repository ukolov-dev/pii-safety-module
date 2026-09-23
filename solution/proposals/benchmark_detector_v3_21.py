"""Local p95 benchmark for 100,000-token v3.21 documents."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Sequence

from proposals.detector_v3_21 import detect


def _documents() -> dict[str, str]:
    sentence = "служебная запись обработана без ошибок "
    plain = (sentence * 20_000).strip()
    sparse = (
        (sentence * 10_000) + "\nФИО заявителя: Иванов Иван Иванович\n" + (sentence * 10_000)
    ).strip()
    return {"benign": plain, "sparse_pii": sparse}


def benchmark(runs: int) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for name, text in _documents().items():
        samples: list[float] = []
        for _ in range(runs):
            started = time.perf_counter()
            detect(text)
            samples.append(time.perf_counter() - started)
        samples.sort()
        p95_index = min(len(samples) - 1, max(0, int(len(samples) * 0.95)))
        result[name] = {
            "tokens": len(text.split()),
            "median_seconds": statistics.median(samples),
            "p95_seconds": samples[p95_index],
        }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be positive")
    print(json.dumps(benchmark(args.runs), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
