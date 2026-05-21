from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path("examples/hsrag_law/rq7_scale")


@pytest.fixture(scope="module")
def release_verify_result() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_release.py"),
            "--tiers",
            "100",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_release_verify_passes(release_verify_result: dict) -> None:
    summary = release_verify_result

    assert summary["status"] == "OK"
    assert summary["release_checkpoint"] is True
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["claim_boundary_ok"] is True

    assert summary["master_verify"]["status"] == "OK"
    assert summary["master_verify"]["all_passed"] is True
    assert summary["master_verify"]["latest_report_is_clean"] is True

    assert summary["public_report"]["status"] == "OK"
    assert summary["public_report"]["rq4_chunk_count"] >= 800
    assert summary["public_report"]["actual_elapsed_timing_available"] is True

    assert summary["claim_boundary"]["public_report_available"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True


def test_rq7_release_verify_writes_summary_files(release_verify_result: dict) -> None:
    verify_dir = ROOT / "04_runs" / release_verify_result["release_id"]

    summary_json = verify_dir / "rq7_release_verify_summary.json"
    summary_txt = verify_dir / "rq7_release_verify_summary.txt"

    assert summary_json.exists()
    assert summary_txt.exists()

    text = summary_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 release verify" in text
    assert "full_scale_benchmark: false" in text
    assert "vector_hybrid_baselines: false" in text
    assert "unit_derivation_is_heuristic: true" in text


def test_rq7_release_verify_rejects_missing_rq4_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_release.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
