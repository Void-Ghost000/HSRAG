from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def run_auto_builder(output_path: Path) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_auto_csv.py"),
            "--csv",
            str(ROOT / "02_input" / "rq7_auto_csv_fixture.example.csv"),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_auto_csv_builder_detects_columns(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.auto.json"
    summary = run_auto_builder(output)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["chunk_count"] >= 3
    assert summary["detected_columns"]["corpus"] == "corpus_guess"
    assert summary["detected_columns"]["unit"] == "unit_id"
    assert summary["detected_columns"]["text"] == "chunk_text"

    registry = json.loads(output.read_text(encoding="utf-8"))

    assert registry["schema"] == "HSRAG_RQ7_CHUNK_REGISTRY_V0_1"
    assert registry["generator"] == "build_chunk_registry_auto_csv.py"
    assert registry["chunks"]

    for chunk in registry["chunks"]:
        assert chunk["cthc_address"].startswith("cthc://")
        assert chunk["source_hash"].startswith("sha256:")
        assert chunk["text"]


def test_rq7_auto_csv_registry_runs_with_runner(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.auto.json"
    run_auto_builder(output)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
            "--chunk-registry",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert summary["salted_domain_gate"] is True
    assert Path(summary["metrics_by_query_class"]).exists()


def test_rq7_auto_csv_builder_rejects_missing_text_alias(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "jurisdiction,corpus_guess,unit_id\nEU,EU_AI_ACT,ARTICLE_5\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_auto_csv.py"),
            "--csv",
            str(bad_csv),
            "--output",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "MISSING_REQUIRED_COLUMN_FOR:text" in result.stderr or "MISSING_REQUIRED_COLUMN_FOR:text" in result.stdout
