from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_hybrid_branch_status_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_hybrid_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["branch_scope"] == "rq7-hybrid-baseline"
    assert summary["final_checkpoint_ready"] is True
    assert "HYBRID_BM25_VECTOR" in summary["hybrid_modes"]
    assert "CTHC_PRUNED_HYBRID" in summary["hybrid_modes"]
    assert summary["claim_boundary"]["external_embedding_api"] is False
    assert summary["claim_boundary"]["network_required"] is False
    assert summary["claim_boundary"]["secret_required"] is False


def test_rq7_hybrid_branch_status_writes_reports() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_hybrid_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    md = ROOT / "05_reports" / "RQ7_HYBRID_BRANCH_STATUS.md"
    js = ROOT / "05_reports" / "RQ7_HYBRID_BRANCH_STATUS.json"

    assert md.exists()
    assert js.exists()

    text = md.read_text(encoding="utf-8")

    assert "# RQ7 Hybrid Branch Status" in text
    assert "HYBRID_BM25_VECTOR" in text
    assert "CTHC_PRUNED_HYBRID" in text
    assert "final_checkpoint_ready: true" in text
    assert "external_embedding_api: false" in text
