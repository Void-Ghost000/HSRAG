from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_runner_accepts_external_chunk_registry_path() -> None:
    registry_path = ROOT / "02_input" / "chunk_registry.example.json"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
            "--chunk-registry",
            str(registry_path),
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

    assert "chunk_registry_path" in run_manifest
    assert run_manifest["chunk_registry_path"].endswith("chunk_registry.example.json")
    assert run_manifest["chunk_registry_hash"].startswith("sha256:")


def test_rq7_runner_rejects_invalid_chunk_registry(tmp_path: Path) -> None:
    bad_registry = tmp_path / "bad_registry.json"
    bad_registry.write_text(
        json.dumps(
            {
                "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
                "chunks": [
                    {
                        "chunk_id": "BAD_1",
                        "domain": "LAW",
                        "jurisdiction": "EU",
                        "corpus": "EU_AI_ACT",
                        "unit": "ARTICLE_5",
                        "cthc_address": "not-a-cthc-address",
                        "source_hash": "sha256:BAD",
                        "text": "bad test chunk"
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
            "--chunk-registry",
            str(bad_registry),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "INVALID_CTHC_ADDRESS" in result.stderr or "INVALID_CTHC_ADDRESS" in result.stdout
