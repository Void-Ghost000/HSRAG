from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_full_branch_status_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["branch_scope"] == "rq7-full-benchmark"
    assert summary["claim_boundary"]["full_query_expansion"] is True
    assert summary["claim_boundary"]["diagnostic_only"] is True
    assert summary["claim_boundary"]["triage_only"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False

    assert summary["full_query_seed"]["query_count"] is not None
    assert summary["diagnostics"]["raw_result_count"] is not None
    assert summary["triage"]["raw_result_count"] is not None


def test_rq7_full_branch_status_writes_reports() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    status_md = ROOT / "05_reports" / "RQ7_FULL_BRANCH_STATUS.md"
    status_json = ROOT / "05_reports" / "RQ7_FULL_BRANCH_STATUS.json"

    assert status_md.exists()
    assert status_json.exists()

    text = status_md.read_text(encoding="utf-8")

    assert "# RQ7 Full Branch Status" in text
    assert "rq7-full-benchmark" in text
    assert "acceptance_failure_allowed_for_diagnostics: true" in text
    assert "full_scale_benchmark: false" in text
    assert "vector_hybrid_baselines: false" in text
