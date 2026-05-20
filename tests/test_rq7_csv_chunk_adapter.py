from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def run_csv_builder(output_path: Path) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_csv.py"),
            "--csv",
            str(ROOT / "02_input" / "rq7_csv_fixture.example.csv"),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_build_chunk_registry_from_csv(tmp_path: Path) -> None:
    output_path = tmp_path / "chunk_registry.from_csv.json"
    summary = run_csv_builder(output_path)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["chunk_count"] >= 3
    assert output_path.exists()

    registry = json.loads(output_path.read_text(encoding="utf-8"))

    assert registry["schema"] == "HSRAG_RQ7_CHUNK_REGISTRY_V0_1"
    assert registry["local_only"] is True
    assert registry["csv_hash"].startswith("sha256:")
    assert registry["chunks"]

    for chunk in registry["chunks"]:
        assert chunk["cthc_address"].startswith("cthc://")
        assert chunk["source_hash"].startswith("sha256:")
        assert chunk["text"]


def test_rq7_csv_registry_is_deterministic(tmp_path: Path) -> None:
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"

    run_csv_builder(output_a)
    run_csv_builder(output_b)

    registry_a = json.loads(output_a.read_text(encoding="utf-8"))
    registry_b = json.loads(output_b.read_text(encoding="utf-8"))

    assert registry_a == registry_b


def test_rq7_generated_csv_registry_runs_with_rq7_runner(tmp_path: Path) -> None:
    output_path = tmp_path / "chunk_registry.from_csv.json"
    run_csv_builder(output_path)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
            "--chunk-registry",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert summary["toy_retrieval"] is True
    assert summary["salted_domain_gate"] is True


def test_rq7_csv_builder_rejects_missing_text_column(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "domain,jurisdiction,corpus,unit\nLAW,EU,EU_AI_ACT,ARTICLE_5\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_csv.py"),
            "--csv",
            str(bad_csv),
            "--output",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "MISSING_COLUMN:text" in result.stderr or "MISSING_COLUMN:text" in result.stdout
