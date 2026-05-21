from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def build_registry(output: Path, size: int = 1000) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_synthetic_expanded_registry.py"),
            "--target-size",
            str(size),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_synthetic_expanded_registry_builds_with_labels(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.synthetic_1000.json"
    summary = build_registry(output, 1000)

    assert summary["status"] == "OK"
    assert summary["target_size"] == 1000
    assert summary["chunk_count"] == 1000
    assert summary["real_chunk_count"] >= 800
    assert summary["synthetic_chunk_count"] == 1000 - summary["real_chunk_count"]
    assert summary["synthetic_expansion"] is True
    assert summary["synthetic_chunks_explicitly_labeled"] is True

    registry = json.loads(output.read_text(encoding="utf-8"))

    assert registry["schema"] == "HSRAG_RQ7_CHUNK_REGISTRY_V0_1"
    assert registry["registry_variant"] == "SYNTHETIC_EXPANDED_REGISTRY_V0_1"
    assert registry["claim_boundary"]["synthetic_expansion"] is True
    assert registry["claim_boundary"]["synthetic_expansion_is_not_new_legal_corpus"] is True
    assert registry["claim_boundary"]["full_scale_real_corpus_benchmark"] is False

    real_chunks = [chunk for chunk in registry["chunks"] if chunk["synthetic_expansion"] is False]
    synthetic_chunks = [chunk for chunk in registry["chunks"] if chunk["synthetic_expansion"] is True]

    assert len(real_chunks) == registry["real_chunk_count"]
    assert len(synthetic_chunks) == registry["synthetic_chunk_count"]

    for chunk in synthetic_chunks[:20]:
        assert chunk["source_type"] == "SYNTHETIC_SCALE_EXPANSION"
        assert chunk["official_source"] is False
        assert chunk["synthetic_source_chunk_id"]
        assert chunk["synthetic_variant_index"] >= 1
        assert "SYNTHETIC_SCALE_EXPANSION" in chunk["text"]


def test_rq7_synthetic_registry_is_deterministic(tmp_path: Path) -> None:
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"

    build_registry(output_a, 1000)
    build_registry(output_b, 1000)

    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")


def test_rq7_synthetic_registry_runs_with_rq7(tmp_path: Path) -> None:
    output = tmp_path / "chunk_registry.synthetic_1000.json"
    build_registry(output, 1000)

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
    assert summary["salted_domain_gate"] is True
    assert Path(summary["metrics_summary"]).exists()
    assert Path(summary["metrics_by_query_class"]).exists()


def test_rq7_synthetic_registry_rejects_target_below_real_count(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_synthetic_expanded_registry.py"),
            "--target-size",
            "100",
            "--output",
            str(tmp_path / "bad.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "TARGET_SIZE_BELOW_REAL_COUNT" in result.stderr or "TARGET_SIZE_BELOW_REAL_COUNT" in result.stdout
