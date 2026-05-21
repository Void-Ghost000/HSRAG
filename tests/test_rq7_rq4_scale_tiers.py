from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path("examples/hsrag_law/rq7_scale")


@pytest.fixture(scope="module")
def scale_tier_result() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_rq4_scale_tiers.py"),
            "--tiers",
            "100,300,600,889",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_rq4_scale_tier_runner_passes(scale_tier_result: dict) -> None:
    summary = scale_tier_result

    assert summary["status"] == "OK"
    assert summary["all_passed"] is True
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["full_chunk_count"] >= 800
    assert summary["executed_tiers"] == [100, 300, 600, 889]

    assert summary["claim_boundary"]["rq4_rebuilt_artifact_connected"] is True
    assert summary["claim_boundary"]["scale_tier_runner"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True


def test_rq7_rq4_scale_tier_each_tier_has_artifacts(scale_tier_result: dict) -> None:
    for tier in scale_tier_result["tier_results"]:
        assert tier["passed"] is True
        assert tier["acceptance_passed"] is True
        assert tier["missing_artifacts"] == []

        runner = tier["runner"]
        assert runner["status"] == "OK"
        assert runner["passed"] is True
        assert runner["salted_domain_gate"] is True
        assert runner["latest_report"] is None
        assert Path(runner["metrics_summary"]).exists()
        assert Path(runner["metrics_by_query_class"]).exists()
        assert Path(runner["raw_results"]).exists()


def test_rq7_rq4_scale_tier_writes_summary_files(scale_tier_result: dict) -> None:
    verify_dir = ROOT / "04_runs" / scale_tier_result["verify_id"]

    summary_json = verify_dir / "rq7_rq4_scale_tier_summary.json"
    summary_csv = verify_dir / "rq7_rq4_scale_tier_summary.csv"
    summary_txt = verify_dir / "rq7_rq4_scale_tier_summary.txt"

    assert summary_json.exists()
    assert summary_csv.exists()
    assert summary_txt.exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {int(row["tier_size"]) for row in rows} == {100, 300, 600, 889}
    assert {"BM25_GLOBAL", "CTHC_PRUNED_BM25", "UNIQUE_ADDRESS"}.issubset(
        {row["mode"] for row in rows}
    )

    text = summary_txt.read_text(encoding="utf-8")
    assert "HSRAG RQ7 RQ4 scale tier runner" in text
    assert "scale_tier_runner: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_rq4_scale_tier_rejects_missing_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_rq4_scale_tiers.py"),
            "--rq4-csv",
            str(tmp_path / "missing.csv"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
