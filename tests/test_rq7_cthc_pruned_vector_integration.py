from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_vector_config() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.vector.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_rq7_vector_config_contains_cthc_pruned_vector() -> None:
    config = json.loads((ROOT / "config.rq7.vector.json").read_text(encoding="utf-8"))

    assert "VECTOR_GLOBAL" in config["modes"]
    assert "CTHC_PRUNED_VECTOR" in config["modes"]
    assert config["claim_boundary"]["local_deterministic_vector_baseline"] is True
    assert config["claim_boundary"]["external_embedding_api"] is False
    assert config["claim_boundary"]["network_required"] is False
    assert config["claim_boundary"]["secret_required"] is False


def test_rq7_runner_accepts_cthc_pruned_vector_mode() -> None:
    summary = run_vector_config()

    assert summary["status"] == "OK"
    assert Path(summary["metrics_summary"]).exists()
    assert Path(summary["metrics_by_query_class"]).exists()

    rows = read_csv(Path(summary["metrics_summary"]))
    modes = {row["mode"] for row in rows}

    assert "VECTOR_GLOBAL" in modes
    assert "CTHC_PRUNED_VECTOR" in modes


def test_rq7_cthc_pruned_vector_uses_salted_boundary() -> None:
    summary = run_vector_config()

    raw_rows = [
        json.loads(line)
        for line in Path(summary["raw_results"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = [row for row in raw_rows if row["mode"] == "CTHC_PRUNED_VECTOR"]
    assert rows

    allow_rows = [row for row in rows if row["status"] == "ALLOW"]
    assert allow_rows

    for row in allow_rows:
        assert row["route_boundary"]["used_for_pruning"] is True
        assert row["route_boundary"]["domain_salt_hash"]
        assert row["metrics"]["actual_elapsed_ms"] >= 0.0
