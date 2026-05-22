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


def run_hybrid() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.hybrid.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_hybrid_config_contains_cthc_pruned_hybrid() -> None:
    config = json.loads((ROOT / "config.rq7.hybrid.json").read_text(encoding="utf-8"))

    assert "HYBRID_BM25_VECTOR" in config["modes"]
    assert "CTHC_PRUNED_HYBRID" in config["modes"]
    assert config["claim_boundary"]["cthc_pruned_hybrid_available"] is True


def test_runner_accepts_cthc_pruned_hybrid() -> None:
    summary = run_hybrid()
    assert summary["status"] == "OK"

    rows = read_csv(Path(summary["metrics_summary"]))
    modes = {row["mode"] for row in rows}

    assert "HYBRID_BM25_VECTOR" in modes
    assert "CTHC_PRUNED_HYBRID" in modes


def test_cthc_pruned_hybrid_uses_salted_boundary() -> None:
    summary = run_hybrid()

    raw_rows = [
        json.loads(line)
        for line in Path(summary["raw_results"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = [row for row in raw_rows if row["mode"] == "CTHC_PRUNED_HYBRID"]
    assert rows

    allow_rows = [row for row in rows if row["status"] == "ALLOW"]
    assert allow_rows

    for row in allow_rows:
        assert row["route_boundary"]["used_for_pruning"] is True
        assert row["route_boundary"]["domain_salt_hash"]
        assert row["metrics"]["actual_elapsed_ms"] >= 0.0
