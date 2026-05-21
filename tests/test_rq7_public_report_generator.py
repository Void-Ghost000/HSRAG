from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path("examples/hsrag_law/rq7_scale")


@pytest.fixture(scope="module")
def public_report_result() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_public_report.py"),
            "--tiers",
            "100",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_public_report_generator_passes(public_report_result: dict) -> None:
    summary = public_report_result

    assert summary["status"] == "OK"
    assert summary["actual_elapsed_timing_available"] is True
    assert summary["rq4_chunk_count"] >= 800
    assert summary["executed_tiers"] == [100]

    assert summary["claim_boundary"]["rq4_rebuilt_artifact_connected"] is True
    assert summary["claim_boundary"]["public_report_only"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False


def test_rq7_public_report_file_contains_claim_boundaries(public_report_result: dict) -> None:
    report_path = Path(public_report_result["report"])
    assert report_path.exists()

    text = report_path.read_text(encoding="utf-8")

    assert "# HSRAG RQ7 Public Report" in text
    assert "This report does not claim full-scale benchmark completion." in text
    assert "This report does not include vector or hybrid baselines." in text
    assert "The current RQ4 unit derivation is heuristic." in text
    assert "actual_elapsed_p99_ms" in text
    assert "python -m pytest tests -k rq7" in text


def test_rq7_public_report_rejects_missing_rq4_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_public_report.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
