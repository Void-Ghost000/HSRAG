from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_one_command_verify_generates_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["one_command_verify"] is True
    assert summary["required_artifacts_exist"] is True
    assert summary["acceptance_passed"] is True
    assert summary["latest_report_is_clean"] is True

    assert summary["claim_boundary"]["toy_retrieval"] is True
    assert summary["claim_boundary"]["salted_domain_gate"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["official_rq4_corpus_connected"] is False

    verify_dir = Path(summary["generated_registry"]).parent
    assert (verify_dir / "rq7_verify_summary.json").exists()
    assert (verify_dir / "rq7_verify_summary.txt").exists()

    runner = summary["runner"]
    assert Path(runner["raw_results"]).exists()
    assert Path(runner["metrics_summary"]).exists()
    assert Path(runner["acceptance_gates"]).exists()
    assert Path(runner["audit_chain"]).exists()
    assert Path(runner["report"]).exists()
    assert runner["latest_report"] is None


def test_rq7_one_command_verify_does_not_update_latest_report() -> None:
    latest_report = ROOT / "05_reports" / "RQ7_LATEST_REPORT.md"
    before = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    after = latest_report.read_text(encoding="utf-8") if latest_report.exists() else None

    assert before == after
