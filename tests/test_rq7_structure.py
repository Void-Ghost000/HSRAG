from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("examples/hsrag_law/rq7_scale")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_rq7_template_directories_exist() -> None:
    required_dirs = [
        "00_qoim",
        "01_csp",
        "02_input",
        "03_schema",
        "04_runs",
        "05_reports",
        "06_audit",
        "scripts",
    ]

    for name in required_dirs:
        assert (ROOT / name).exists(), name


def test_rq7_template_files_exist() -> None:
    required_files = [
        "00_qoim/QOIM_REVIEW.md",
        "01_csp/CSP_V0_2_SKELETON.md",
        "config.rq7.json",
        "02_input/corpus_manifest.example.json",
        "02_input/query_seed.example.json",
        "02_input/mutation_policy.example.json",
        "03_schema/result_contract.schema.json",
        "CLAIM_BOUNDARY.md",
        "scripts/run_rq7.py",
    ]

    for name in required_files:
        assert (ROOT / name).exists(), name


def test_rq7_config_contains_core_modes_and_metrics() -> None:
    config = load_json(ROOT / "config.rq7.json")

    assert "BM25_GLOBAL" in config["modes"]
    assert "CTHC_PRUNED_BM25" in config["modes"]
    assert "UNIQUE_ADDRESS" in config["modes"]

    metrics = set(config["required_metrics"])
    assert "latency_p99_ms" in metrics
    assert "esi_mean" in metrics
    assert "estimated_token_cost_usd_per_1k_queries" in metrics
    assert "token_reduction_ratio" in metrics
    assert "audit_hash_complete_rate" in metrics
    assert "route_determinism_rate" in metrics


def test_rq7_query_seed_contains_boundary_cases() -> None:
    seed = load_json(ROOT / "02_input/query_seed.example.json")
    query_classes = {q["query_class"] for q in seed["queries"]}

    assert "exact_unit" in query_classes
    assert "no_evidence" in query_classes
    assert "ambiguous_cross_domain" in query_classes


def test_rq7_result_contract_requires_audit_hashes() -> None:
    schema = load_json(ROOT / "03_schema/result_contract.schema.json")
    required_hashes = set(schema["required_hashes"])

    assert "query_hash" in required_hashes
    assert "source_hash" in required_hashes
    assert "evidence_hash" in required_hashes
    assert "decision_hash" in required_hashes
    assert "run_hash" in required_hashes
