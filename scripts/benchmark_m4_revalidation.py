"""Measure current deterministic M4 replay latency without altering its frozen archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_m4_revalidation import build


def benchmark(rounds: int) -> dict:
    if rounds < 1:
        raise ValueError("rounds must be positive")
    build()  # warm-up is intentionally excluded
    samples = []
    for _ in range(rounds):
        started = perf_counter()
        result = build()
        elapsed = (perf_counter() - started) * 1000
        if result["metrics"]["accepted_count"] != 11:
            raise RuntimeError("benchmark replay did not accept all 11 frozen witnesses")
        samples.append(elapsed)
    ordered = sorted(samples)
    p95_index = max(0, min(len(ordered) - 1, int(0.95 * len(ordered) + 0.999999) - 1))
    return {
        "schema_version": "m4-latency-benchmark-1.0",
        "scope": "current_machine_non_publication_operational_measurement",
        "rounds": rounds,
        "warmup_rounds": 1,
        "global_counterexamples_per_round": 11,
        "negative_controls_per_round": 2,
        "latency_ms": {
            "min": min(samples),
            "median": statistics.median(samples),
            "mean": statistics.fmean(samples),
            "p95": ordered[p95_index],
            "max": max(samples),
        },
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "external_tool_calls_per_round": 0,
        "external_cost_usd_per_round": 0.0,
        "limitations": [
            "Wall-clock results are machine-specific and are not a deterministic scientific benchmark.",
            "This measures replay and exact verification, not candidate generation latency."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=50)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = benchmark(args.rounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"M4 replay latency median={report['latency_ms']['median']:.3f} ms over {args.rounds} rounds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
