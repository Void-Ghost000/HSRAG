from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path("examples/hsrag_law/rq7_scale")


@pytest.fixture(scope="module")
def master_verify_result() -> dict:
    latest_report = ROOT / "05_reports" / "RQ7_LATEST_REPORT.md"
    before = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_all.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    after = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None

    return {
        "summary": json.loads(result.stdout),
        "latest_before": before,
        "latest_after": after,
    }


def test_rq7_master_verify_passes_with_rq4_metrics_snapshot(master_verify_result: dict) -> None:
    summary = master_verify_result["summary"]

    assert summary["schema"] == "HSRAG_RQ7_ALL_VERIFY_SUMMARY_V0_3"
    assert summary["status"] == "OK"
    assert summary["all_passed"] is True
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["latest_report_is_clean"] is True

    assert summary["inventory"]["status"] == "OK"
    assert summary["core_verify"]["status"] == "OK"
    assert summary["adapter_matrix"]["status"] == "OK"
    assert summary["adapter_matrix"]["all_passed"] is True
    assert summary["candidate_run"]["status"] == "OK"
    assert summary["candidate_run"]["acceptance_passed"] is True

    assert summary["rq4_metrics_snapshot"]["status"] == "OK"
    assert summary["rq4_verify"]["acceptance_passed"] is True
    assert summary["rq4_verify"]["chunk_count"] >= 800
    assert summary["rq4_verify"]["unit_derivation_is_heuristic"] is True

    assert summary["claim_boundary"]["master_verify_only"] is True
    assert summary["claim_boundary"]["rq4_rebuilt_artifact_connected"] is True
    assert summary["claim_boundary"]["rq4_metrics_snapshot_available"] is True
    assert summary["claim_boundary"]["official_rq4_corpus_connected"] is True
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False


def test_rq7_master_verify_writes_summary_files_with_snapshot(master_verify_result: dict) -> None:
    summary = master_verify_result["summary"]
    verify_dir = ROOT / "04_runs" / summary["verify_id"]

    summary_json = verify_dir / "rq7_all_verify_summary.json"
    summary_txt = verify_dir / "rq7_all_verify_summary.txt"

    assert summary_json.exists()
    assert summary_txt.exists()

    text = summary_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 master verify" in text
    assert "rq4_metrics_snapshot_status: OK" in text
    assert "rq4_rebuilt_artifact_connected: true" in text
    assert "rq4_metrics_snapshot_available: true" in text
    assert "unit_derivation_is_heuristic: true" in text
    assert "full_scale_benchmark: false" in text
    assert "all_passed: True" in text


def test_rq7_master_verify_does_not_update_latest_report(master_verify_result: dict) -> None:
    assert master_verify_result["latest_before"] == master_verify_result["latest_after"]
