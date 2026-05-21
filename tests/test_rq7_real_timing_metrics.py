from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def run_rq7() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_rq7_raw_results_include_actual_elapsed_ms() -> None:
    summary = run_rq7()

    raw_results = Path(summary["raw_results"])
    rows = [
        json.loads(line)
        for line in raw_results.read_text(encoding="utf-8").splitlines()
    ]

    assert rows

    for row in rows:
        assert "actual_elapsed_ms" in row["metrics"]
        assert isinstance(row["metrics"]["actual_elapsed_ms"], float)
        assert row["metrics"]["actual_elapsed_ms"] >= 0.0


def test_rq7_metrics_summary_include_actual_elapsed_percentiles() -> None:
    summary = run_rq7()

    metrics_rows = read_csv(Path(summary["metrics_summary"]))
    query_class_rows = read_csv(Path(summary["metrics_by_query_class"]))

    assert metrics_rows
    assert query_class_rows

    for row in metrics_rows:
        assert "actual_elapsed_p50_ms" in row
        assert "actual_elapsed_p95_ms" in row
        assert "actual_elapsed_p99_ms" in row
        assert float(row["actual_elapsed_p50_ms"]) >= 0.0
        assert float(row["actual_elapsed_p95_ms"]) >= 0.0
        assert float(row["actual_elapsed_p99_ms"]) >= 0.0

    for row in query_class_rows:
        assert "actual_elapsed_p50_ms" in row
        assert "actual_elapsed_p95_ms" in row
        assert "actual_elapsed_p99_ms" in row
        assert float(row["actual_elapsed_p50_ms"]) >= 0.0
        assert float(row["actual_elapsed_p95_ms"]) >= 0.0
        assert float(row["actual_elapsed_p99_ms"]) >= 0.0


def test_rq7_acceptance_gates_include_real_timing_contract() -> None:
    summary = run_rq7()
    gates = json.loads(Path(summary["acceptance_gates"]).read_text(encoding="utf-8"))

    assert gates["passed"] is True
    assert gates["gate_results"]["actual_elapsed_ms_reported_for_every_row"] is True
    assert gates["gate_results"]["actual_elapsed_p99_reported_for_every_mode"] is True
