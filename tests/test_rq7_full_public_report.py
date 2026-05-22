from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_full_public_report_builds(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_public_report.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["claim_boundary"]["diagnostic_only"] is True
    assert summary["claim_boundary"]["triage_only"] is True
    assert summary["claim_boundary"]["synthetic_expansion"] is True
    assert summary["claim_boundary"]["synthetic_expansion_is_not_new_legal_corpus"] is True
    assert summary["claim_boundary"]["full_scale_real_corpus_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False

    assert (output_dir / "RQ7_FULL_PUBLIC_REPORT.md").exists()
    assert (output_dir / "RQ7_FULL_PUBLIC_REPORT_SUMMARY.json").exists()


def test_rq7_full_public_report_contains_claim_boundaries(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_public_report.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    text = (output_dir / "RQ7_FULL_PUBLIC_REPORT.md").read_text(encoding="utf-8")

    assert "# RQ7 Full Public Report" in text
    assert "full_scale_real_corpus_benchmark: false" in text
    assert "vector_hybrid_baselines: false" in text
    assert "Synthetic chunks are explicitly labeled" in text
    assert "python -m pytest tests -k rq7" in text


def test_rq7_full_public_report_rejects_missing_reports_dir(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_public_report.py"),
            "--reports-dir",
            str(tmp_path / "missing_reports"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "MISSING_REQUIRED_REPORTS" in result.stderr or "MISSING_REQUIRED_REPORTS" in result.stdout
