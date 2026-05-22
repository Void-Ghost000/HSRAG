from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_vector_baseline_report_builds(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_vector_baseline_report.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert "VECTOR_GLOBAL" in summary["vector_modes"]
    assert "CTHC_PRUNED_VECTOR" in summary["vector_modes"]
    assert summary["claim_boundary"]["local_deterministic_vector_baseline"] is True
    assert summary["claim_boundary"]["external_embedding_api"] is False
    assert summary["claim_boundary"]["network_required"] is False
    assert summary["claim_boundary"]["secret_required"] is False
    assert summary["claim_boundary"]["state_of_the_art_vector_search"] is False

    assert (output_dir / "RQ7_VECTOR_BASELINE_REPORT.md").exists()
    assert (output_dir / "RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json").exists()
    assert (output_dir / "RQ7_VECTOR_BASELINE_REPORT.csv").exists()


def test_rq7_vector_baseline_report_csv_contains_vector_modes(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_vector_baseline_report.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    csv_path = output_dir / "RQ7_VECTOR_BASELINE_REPORT.csv"

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    modes = {row["mode"] for row in rows}

    assert "VECTOR_GLOBAL" in modes
    assert "CTHC_PRUNED_VECTOR" in modes


def test_rq7_vector_baseline_report_contains_claim_boundary(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_vector_baseline_report.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    text = (output_dir / "RQ7_VECTOR_BASELINE_REPORT.md").read_text(encoding="utf-8")

    assert "# RQ7 Vector Baseline Report" in text
    assert "external_embedding_api: false" in text
    assert "network_required: false" in text
    assert "secret_required: false" in text
    assert "state_of_the_art_vector_search: false" in text
    assert "Hybrid ranking is not included yet." in text
