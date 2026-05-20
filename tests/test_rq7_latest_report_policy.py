from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_default_run_does_not_update_latest_report() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["report"]
    assert summary["latest_report"] is None

    run_report = Path(summary["report"])
    assert run_report.exists()

    report_text = run_report.read_text(encoding="utf-8")
    assert "# HSRAG RQ7 Report" in report_text
    assert "## Known Limits" in report_text


def test_rq7_write_latest_report_flag_updates_latest_report() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
            "--write-latest-report",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["report"]
    assert summary["latest_report"]

    latest_report = Path(summary["latest_report"])
    assert latest_report.exists()

    report_text = latest_report.read_text(encoding="utf-8")
    assert "# HSRAG RQ7 Report" in report_text
    assert "salted_domain_gate: True" in report_text
