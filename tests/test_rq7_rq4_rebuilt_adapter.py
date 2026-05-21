from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")
RQ4_CSV = Path("examples/hsrag_law/results/rq4_rebuilt_chunks.csv")


def test_rq7_rq4_rebuilt_builder_generates_registry(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.rq4_rebuilt.json"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(RQ4_CSV),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["rq4_rebuilt_artifact_adapter"] is True
    assert summary["chunk_count"] >= 800
    assert output.exists()

    registry = json.loads(output.read_text(encoding="utf-8"))

    assert registry["schema"] == "HSRAG_RQ7_CHUNK_REGISTRY_V0_1"
    assert registry["generator"] == "build_chunk_registry_from_rq4_rebuilt.py"
    assert registry["chunk_count"] == summary["chunk_count"]
    assert registry["claim_boundary"]["unit_derivation_is_heuristic"] is True

    chunks = registry["chunks"]
    assert chunks

    for chunk in chunks[:20]:
        assert chunk["domain"] == "LAW"
        assert chunk["chunk_id"]
        assert chunk["jurisdiction"]
        assert chunk["corpus"]
        assert chunk["unit"]
        assert chunk["cthc_address"].startswith("cthc://LAW/")
        assert chunk["source_hash"].startswith("sha256:")
        assert chunk["text"]


def test_rq7_rq4_rebuilt_builder_derives_core_units(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.rq4_rebuilt.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(RQ4_CSV),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    registry = json.loads(output.read_text(encoding="utf-8"))
    units_by_corpus = {}

    for chunk in registry["chunks"]:
        units_by_corpus.setdefault(chunk["corpus"], set()).add(chunk["unit"])

    assert "EU_AI_ACT" in units_by_corpus
    assert "ARTICLE_5" in units_by_corpus["EU_AI_ACT"]


def test_rq7_rq4_rebuilt_registry_runs_with_rq7(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.rq4_rebuilt.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(RQ4_CSV),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

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
    assert summary["synthetic_dry_run"] is False
    assert summary["toy_retrieval"] is True
    assert summary["salted_domain_gate"] is True
    assert Path(summary["metrics_by_query_class"]).exists()


def test_rq7_rq4_rebuilt_builder_rejects_missing_csv(tmp_path: Path) -> None:
    output = tmp_path / "out.json"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(tmp_path / "missing.csv"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "RQ4_REBUILT_CSV_NOT_FOUND" in result.stderr or "RQ4_REBUILT_CSV_NOT_FOUND" in result.stdout
