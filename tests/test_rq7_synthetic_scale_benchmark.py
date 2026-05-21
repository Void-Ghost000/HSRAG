from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_synthetic_scale_benchmark_builds(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_synthetic_scale_benchmark.py"),
            "--target-sizes",
            "1000",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["target_sizes"] == [1000]
    assert summary["claim_boundary"]["synthetic_expansion"] is True
    assert summary["claim_boundary"]["synthetic_chunks_explicitly_labeled"] is True
    assert summary["claim_boundary"]["synthetic_expansion_is_not_new_legal_corpus"] is True
    assert summary["claim_boundary"]["scale_stress_only"] is True
    assert summary["claim_boundary"]["full_scale_real_corpus_benchmark"] is False

    assert (output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.json").exists()
    assert (output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.md").exists()
    assert (output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.csv").exists()

    with (output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {int(row["target_size"]) for row in rows} == {1000}
    assert {"BM25_GLOBAL", "CTHC_PRUNED_BM25", "UNIQUE_ADDRESS"}.issubset(
        {row["mode"] for row in rows}
    )


def test_rq7_synthetic_scale_benchmark_rejects_missing_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_synthetic_scale_benchmark.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
            "--output-dir",
            str(tmp_path / "reports"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
