from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_rq4_verify_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_rq4.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["acceptance_passed"] is True
    assert summary["latest_report_is_clean"] is True

    assert summary["claim_boundary"]["rq4_rebuilt_artifact_connected"] is True
    assert summary["claim_boundary"]["official_rq4_corpus_connected"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True

    assert summary["registry"]["chunk_count"] >= 800
    assert "EU_AI_ACT" in summary["registry"]["corpora"]

    runner = summary["runner"]
    assert runner["status"] == "OK"
    assert runner["passed"] is True
    assert runner["salted_domain_gate"] is True
    assert runner["latest_report"] is None
    assert Path(runner["metrics_by_query_class"]).exists()


def test_rq7_rq4_verify_writes_summary_files() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_rq4.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)
    verify_dir = ROOT / "04_runs" / summary["verify_id"]

    summary_json = verify_dir / "rq7_rq4_verify_summary.json"
    summary_txt = verify_dir / "rq7_rq4_verify_summary.txt"

    assert summary_json.exists()
    assert summary_txt.exists()

    text = summary_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 RQ4 rebuilt artifact verify" in text
    assert "rq4_rebuilt_artifact_connected: true" in text
    assert "unit_derivation_is_heuristic: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_rq4_verify_rejects_missing_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_rq4.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
