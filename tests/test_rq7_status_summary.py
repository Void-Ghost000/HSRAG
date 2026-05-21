from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_status_summary_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_status_summary.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["current_maturity"] == "RQ7 v0.1 release checkpoint / Level 2B-pre"
    assert summary["claim_boundary"]["public_report_published"] is True
    assert summary["claim_boundary"]["release_checkpoint_published"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True

    assert (ROOT / "05_reports" / "RQ7_STATUS_SUMMARY.md").exists()
    assert (ROOT / "05_reports" / "RQ7_STATUS_SUMMARY.json").exists()


def test_rq7_status_summary_contains_verify_commands() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_status_summary.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    text = (ROOT / "05_reports" / "RQ7_STATUS_SUMMARY.md").read_text(encoding="utf-8")

    assert "# RQ7 Status Summary" in text
    assert "python -m pytest tests -k rq7" in text
    assert "verify_rq7_release.py --tiers 100,300,600,889" in text
    assert "full_scale_benchmark: false" in text
    assert "vector_hybrid_baselines: false" in text
    assert "unit_derivation_is_heuristic: true" in text
