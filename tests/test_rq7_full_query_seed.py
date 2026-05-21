from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_full_query_seed_builder_generates_expanded_seed() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_query_seed.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["added_query_count"] >= 18
    assert summary["query_count"] > summary["base_query_count"]
    assert summary["query_seed_path"] == "02_input/query_seed.full.example.json"

    seed = json.loads((ROOT / "02_input" / "query_seed.full.example.json").read_text(encoding="utf-8"))

    classes = {query.get("query_class") or query.get("case_type") for query in seed["queries"]}

    assert "exact_unit" in classes
    assert "no_evidence" in classes
    assert "ambiguous_cross_domain" in classes
    assert "mismatch_trap" in classes
    assert "jurisdiction_distractor" in classes
    assert "typo_abbreviation" in classes


def test_rq7_runner_accepts_full_query_seed_config() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_full_query_seed.py"),
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
            str(ROOT / "config.rq7.full_queries.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    # Full query expansion is diagnostic/stress-oriented.
    # It may surface acceptance-gate failures; this test only requires runnable artifacts.
    assert "passed" in summary
    assert summary["salted_domain_gate"] is True
    assert Path(summary["raw_results"]).exists()
    assert Path(summary["acceptance_gates"]).exists()
    assert Path(summary["metrics_summary"]).exists()
    assert Path(summary["metrics_by_query_class"]).exists()

    metrics_text = Path(summary["metrics_by_query_class"]).read_text(encoding="utf-8")

    assert "jurisdiction_distractor" in metrics_text
    assert "typo_abbreviation" in metrics_text


def test_rq7_full_query_config_uses_explicit_seed_path() -> None:
    config = json.loads((ROOT / "config.rq7.full_queries.json").read_text(encoding="utf-8"))

    assert config["query_seed_path"] == "02_input/query_seed.full.example.json"
    assert config["rq7_full_query_expansion"] is True
    assert "_rq7_base_dir" in config
