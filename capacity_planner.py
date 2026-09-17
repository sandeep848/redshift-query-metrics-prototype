"""Offline Redshift workload capacity planner.

Consumes exported query metrics and produces deployment recommendations without
requiring Kafka, AWS credentials or a running Redshift cluster.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

REQUIRED = {
    "queue_seconds", "execution_seconds", "spill_mb", "scanned_mb", "concurrency"
}


@dataclass(frozen=True)
class CapacityReport:
    samples: int
    queue_p95_seconds: float
    execution_p95_seconds: float
    spill_rate: float
    concurrency_p95: float
    pressure_score: float
    recommendation: str


def analyze(frame: pd.DataFrame) -> CapacityReport:
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError("Input contains no query samples.")

    queue_p95 = float(frame["queue_seconds"].quantile(0.95))
    execution_p95 = float(frame["execution_seconds"].quantile(0.95))
    spill_rate = float((frame["spill_mb"] > 0).mean())
    concurrency_p95 = float(frame["concurrency"].quantile(0.95))

    queue_component = min(queue_p95 / 30.0, 1.0)
    spill_component = min(spill_rate / 0.25, 1.0)
    concurrency_component = min(concurrency_p95 / 50.0, 1.0)
    score = round(
        100 * (0.45 * queue_component + 0.35 * spill_component + 0.20 * concurrency_component),
        2,
    )

    if score >= 70:
        recommendation = "Scale compute and investigate spill-heavy queries."
    elif score >= 40:
        recommendation = "Tune workload queues and review peak concurrency."
    else:
        recommendation = "Current capacity appears adequate; continue monitoring."

    return CapacityReport(
        samples=len(frame),
        queue_p95_seconds=round(queue_p95, 3),
        execution_p95_seconds=round(execution_p95, 3),
        spill_rate=round(spill_rate, 4),
        concurrency_p95=round(concurrency_p95, 2),
        pressure_score=score,
        recommendation=recommendation,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="Exported Redshift query metrics")
    parser.add_argument("--output", type=Path, default=Path("capacity_report.json"))
    args = parser.parse_args()

    report = analyze(pd.read_csv(args.csv))
    args.output.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
