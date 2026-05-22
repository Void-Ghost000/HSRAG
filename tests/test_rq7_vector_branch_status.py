from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_vector_branch_status_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_vector_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["branch_scope"] == "rq7-vector-baseline"
    assert "VECTOR_GLOBAL" in summary["vector_modes"]
    assert "CTHC_PRUNED_VECTOR" in summary["vector_modes"]

    assert summary["claim_boundary"]["local_deterministic_vector_baseline"] is True
    assert summary["claim_boundary"]["external_embedding_api"] is False
    assert summary["claim_boundary"]["network_required"] is False
    assert summary["claim_boundary"]["secret_required"] is False
    assert summary["claim_boundary"]["hybrid_ranking"] is False


def test_rq7_vector_branch_status_writes_reports() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_vector_branch_status.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    status_md = ROOT / "05_reports" / "RQ7_VECTOR_BRANCH_STATUS.md"
    status_json = ROOT / "05_reports" / "RQ7_VECTOR_BRANCH_STATUS.json"

    assert status_md.exists()
    assert status_json.exists()

    text = status_md.read_text(encoding="utf-8")

    assert "# RQ7 Vector Branch Status" in text
    assert "VECTOR_GLOBAL" in text
    assert "CTHC_PRUNED_VECTOR" in text
    assert "external_embedding_api: false" in text
    assert "hybrid_ranking: false" in text
