from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_release_checkpoint_publishes_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "release"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_release_checkpoint.py"),
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
    assert summary["release_checkpoint"] is True
    assert summary["claim_boundary"]["rq7_v0_1_checkpoint"] is True
    assert summary["claim_boundary"]["public_report_published"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert summary["claim_boundary"]["vector_hybrid_baselines"] is False
    assert summary["claim_boundary"]["unit_derivation_is_heuristic"] is True

    assert (output_dir / "RQ7_PUBLIC_REPORT.md").exists()
    assert (output_dir / "RQ7_PUBLIC_REPORT_SUMMARY.json").exists()
    assert (output_dir / "RQ7_RELEASE_CHECKPOINT.json").exists()
    assert (output_dir / "RQ7_RELEASE_CHECKPOINT.md").exists()


def test_rq7_release_checkpoint_contains_claim_boundary(tmp_path: Path) -> None:
    output_dir = tmp_path / "release"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_release_checkpoint.py"),
            "--tiers",
            "100",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    text = (output_dir / "RQ7_RELEASE_CHECKPOINT.md").read_text(encoding="utf-8")

    assert "# RQ7 Release Checkpoint" in text
    assert "full_scale_benchmark: false" in text
    assert "vector_hybrid_baselines: false" in text
    assert "unit_derivation_is_heuristic: true" in text
    assert "python -m pytest tests -k rq7" in text


def test_rq7_release_checkpoint_rejects_missing_rq4_csv(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_rq7_release_checkpoint.py"),
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
