from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_rq4_metrics_snapshot_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "snapshot_rq7_rq4_metrics.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    snapshot = json.loads(result.stdout)

    assert snapshot["status"] == "OK"
    assert snapshot["rq4_verify"]["acceptance_passed"] is True
    assert snapshot["rq4_verify"]["latest_report_is_clean"] is True
    assert snapshot["rq4_verify"]["chunk_count"] >= 800
    assert snapshot["claim_boundary"]["rq4_rebuilt_artifact_connected"] is True
    assert snapshot["claim_boundary"]["metrics_snapshot_only"] is True
    assert snapshot["claim_boundary"]["full_scale_benchmark"] is False
    assert snapshot["claim_boundary"]["unit_derivation_is_heuristic"] is True

    assert "BM25_GLOBAL" in snapshot["modes"]
    assert "CTHC_PRUNED_BM25" in snapshot["modes"]
    assert "UNIQUE_ADDRESS" in snapshot["modes"]

    assert "exact_unit" in snapshot["query_classes"]
    assert "no_evidence" in snapshot["query_classes"]
    assert "ambiguous_cross_domain" in snapshot["query_classes"]

    assert snapshot["mode_summaries"]
    assert snapshot["query_class_summaries"]


def test_rq7_rq4_metrics_snapshot_writes_files() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "snapshot_rq7_rq4_metrics.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    snapshot = json.loads(result.stdout)
    snapshot_dir = ROOT / "04_runs" / snapshot["snapshot_id"]

    snapshot_json = snapshot_dir / "rq7_rq4_metrics_snapshot.json"
    snapshot_txt = snapshot_dir / "rq7_rq4_metrics_snapshot.txt"

    assert snapshot_json.exists()
    assert snapshot_txt.exists()

    text = snapshot_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 RQ4 metrics snapshot" in text
    assert "rq4_rebuilt_artifact_connected: true" in text
    assert "metrics_snapshot_only: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_rq4_metrics_snapshot_rejects_missing_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "snapshot_rq7_rq4_metrics.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
