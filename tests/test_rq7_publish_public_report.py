from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_publish_public_report_writes_report_and_summary(tmp_path: Path) -> None:
    output_dir = tmp_path / "published"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_public_report.py"),
            "--tiers",
            "100",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["claim_boundary"]["public_report_published"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True

    report = output_dir / "RQ7_PUBLIC_REPORT.md"
    report_summary = output_dir / "RQ7_PUBLIC_REPORT_SUMMARY.json"

    assert report.exists()
    assert report_summary.exists()

    text = report.read_text(encoding="utf-8")
    assert "# HSRAG RQ7 Public Report" in text
    assert "This report does not claim full-scale benchmark completion." in text
    assert "actual_elapsed_p99_ms" in text
    assert "python -m pytest tests -k rq7" in text


def test_rq7_publish_public_report_rejects_missing_rq4_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_public_report.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
