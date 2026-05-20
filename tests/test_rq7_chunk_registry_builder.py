from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def run_builder(output_path: Path) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry.py"),
            "--manifest",
            str(ROOT / "02_input" / "real_law_manifest.example.json"),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_build_chunk_registry_from_manifest(tmp_path: Path) -> None:
    output_path = tmp_path / "chunk_registry.generated.json"
    summary = run_builder(output_path)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["chunk_count"] >= 2
    assert output_path.exists()

    registry = json.loads(output_path.read_text(encoding="utf-8"))

    assert registry["schema"] == "HSRAG_RQ7_CHUNK_REGISTRY_V0_1"
    assert registry["local_only"] is True
    assert registry["manifest_hash"].startswith("sha256:")
    assert registry["chunks"]

    for chunk in registry["chunks"]:
        assert chunk["cthc_address"].startswith("cthc://")
        assert chunk["source_hash"].startswith("sha256:")
        assert chunk["text"]


def test_rq7_build_chunk_registry_is_deterministic(tmp_path: Path) -> None:
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"

    run_builder(output_a)
    run_builder(output_b)

    registry_a = json.loads(output_a.read_text(encoding="utf-8"))
    registry_b = json.loads(output_b.read_text(encoding="utf-8"))

    assert registry_a == registry_b


def test_rq7_generated_chunk_registry_runs_with_rq7_runner(tmp_path: Path) -> None:
    output_path = tmp_path / "chunk_registry.generated.json"
    run_builder(output_path)

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

    run_manifest = json.loads((Path(summary["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["chunk_registry_path"].endswith("chunk_registry.generated.json")
    assert run_manifest["chunk_registry_hash"].startswith("sha256:")


def test_rq7_builder_rejects_path_outside_base(tmp_path: Path) -> None:
    bad_manifest = tmp_path / "bad_manifest.json"
    bad_manifest.write_text(
        json.dumps(
            {
                "schema": "HSRAG_RQ7_REAL_LAW_MANIFEST_V0_1",
                "local_only": True,
                "entries": [
                    {
                        "entry_id": "BAD",
                        "domain": "LAW",
                        "jurisdiction": "EU",
                        "corpus": "EU_AI_ACT",
                        "unit": "ARTICLE_5",
                        "path": "../../outside.txt",
                        "source_type": "LOCAL_SAMPLE_TEXT",
                        "official_source": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_chunk_registry.py"),
            "--manifest",
            str(bad_manifest),
            "--output",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
