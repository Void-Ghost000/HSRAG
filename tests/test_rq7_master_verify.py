from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_master_verify_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_all.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

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

    assert summary["claim_boundary"]["master_verify_only"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["official_rq4_corpus_connected"] is False


def test_rq7_master_verify_writes_summary_files() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_all.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)
    verify_dir = ROOT / "04_runs" / summary["verify_id"]

    summary_json = verify_dir / "rq7_all_verify_summary.json"
    summary_txt = verify_dir / "rq7_all_verify_summary.txt"

    assert summary_json.exists()
    assert summary_txt.exists()

    text = summary_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 master verify" in text
    assert "full_scale_benchmark: false" in text
    assert "official_rq4_corpus_connected: false" in text
    assert "all_passed: True" in text


def test_rq7_master_verify_does_not_update_latest_report() -> None:
    latest_report = ROOT / "05_reports" / "RQ7_LATEST_REPORT.md"
    before = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_all.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    after = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None
    assert before == after
