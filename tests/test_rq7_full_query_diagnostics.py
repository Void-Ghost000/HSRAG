from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_full_query_diagnostics_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_rq7_full_query_diagnostics.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["diagnostic_status"] in {"PASS", "DIAGNOSTIC_WARN"}
    assert summary["claim_boundary"]["diagnostic_only"] is True
    assert summary["claim_boundary"]["acceptance_failure_allowed_for_diagnostics"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False

    assert summary["raw_result_count"] > 0
    assert summary["query_class_count"] >= 4
    assert "jurisdiction_distractor" in summary["query_class_summary"]
    assert "typo_abbreviation" in summary["query_class_summary"]
    assert summary["reason_code_summary"]


def test_rq7_full_query_diagnostics_writes_files() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_rq7_full_query_diagnostics.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)
    diagnostic_dir = ROOT / "04_runs" / summary["diagnostic_id"]

    summary_json = diagnostic_dir / "rq7_full_query_diagnostics.json"
    summary_md = diagnostic_dir / "rq7_full_query_diagnostics.md"

    assert summary_json.exists()
    assert summary_md.exists()

    text = summary_md.read_text(encoding="utf-8")
    assert "# RQ7 Full Query Diagnostics" in text
    assert "acceptance_failure_allowed_for_diagnostics: true" in text
    assert "full_scale_benchmark: false" in text
