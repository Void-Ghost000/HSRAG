from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_full_query_triage_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_query_triage.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["raw_result_count"] > 0
    assert summary["claim_boundary"]["triage_only"] is True
    assert summary["claim_boundary"]["acceptance_failure_allowed_for_diagnostics"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False

    assert summary["triage_summary"]
    assert "EXPECTED_GUARD_BLOCK" in summary["triage_summary"] or "TARGET_BLOCKED" in summary["triage_summary"]


def test_rq7_full_query_triage_writes_reports() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_query_triage.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output_json = ROOT / "05_reports" / "RQ7_FULL_QUERY_TRIAGE.json"
    output_md = ROOT / "05_reports" / "RQ7_FULL_QUERY_TRIAGE.md"

    assert output_json.exists()
    assert output_md.exists()

    text = output_md.read_text(encoding="utf-8")
    assert "# RQ7 Full Query Triage" in text
    assert "acceptance_failure_allowed_for_diagnostics: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_full_query_triage_rejects_missing_config(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_query_triage.py"),
            "--config",
            str(tmp_path / "missing.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "CONFIG_NOT_FOUND" in result.stderr or "CONFIG_NOT_FOUND" in result.stdout
