from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_publish_full_query_diagnostics_writes_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_full_query_diagnostics.py"),
            "--output-dir",
            str(output_dir),
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

    assert (output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.json").exists()
    assert (output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.md").exists()
    assert (output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json").exists()

    text = (output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.md").read_text(encoding="utf-8")
    assert "# RQ7 Full Query Diagnostics" in text
    assert "acceptance_failure_allowed_for_diagnostics: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_publish_full_query_diagnostics_rejects_missing_config(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_full_query_diagnostics.py"),
            "--config",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(tmp_path / "reports"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "CONFIG_NOT_FOUND" in result.stderr or "CONFIG_NOT_FOUND" in result.stdout
