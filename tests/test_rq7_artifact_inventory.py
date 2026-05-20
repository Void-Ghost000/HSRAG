from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_artifact_scanner_finds_local_csv_candidates(tmp_path: Path) -> None:
    output = tmp_path / "inventory.json"
    report = tmp_path / "inventory.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scan_rq7_artifacts.py"),
            "--root",
            str(ROOT / "02_input"),
            "--output",
            str(output),
            "--report",
            str(report),
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
    assert summary["artifact_count"] >= 2
    assert summary["candidate_count"] >= 2

    inventory = json.loads(output.read_text(encoding="utf-8"))

    assert inventory["schema"] == "HSRAG_RQ7_ARTIFACT_INVENTORY_V0_1"
    assert inventory["local_only"] is True
    assert inventory["zero_network"] is True
    assert inventory["zero_secret"] is True

    filenames = {item["filename"]: item for item in inventory["artifacts"]}

    assert "rq7_csv_fixture.example.csv" in filenames
    assert "rq7_auto_csv_fixture.example.csv" in filenames

    assert filenames["rq7_csv_fixture.example.csv"]["rq7_auto_csv_candidate"] is True
    assert filenames["rq7_auto_csv_fixture.example.csv"]["rq7_auto_csv_candidate"] is True

    auto_mapping = filenames["rq7_auto_csv_fixture.example.csv"]["detected_columns"]
    assert auto_mapping["corpus"] == "corpus_guess"
    assert auto_mapping["unit"] == "unit_id"
    assert auto_mapping["text"] == "chunk_text"

    assert report.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "# RQ7 Artifact Inventory" in report_text
    assert "candidate_count" in report_text


def test_rq7_artifact_scanner_rejects_missing_root(tmp_path: Path) -> None:
    output = tmp_path / "inventory.json"
    report = tmp_path / "inventory.md"
    missing_root = tmp_path / "missing"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scan_rq7_artifacts.py"),
            "--root",
            str(missing_root),
            "--output",
            str(output),
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "SCAN_ROOT_NOT_FOUND" in result.stderr or "SCAN_ROOT_NOT_FOUND" in result.stdout
