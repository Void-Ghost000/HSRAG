from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def run_rq7() -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def read_rows(summary: dict) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(summary["raw_results"]).read_text(encoding="utf-8").splitlines()
    ]


def test_rq7_salted_domain_gate_is_enabled() -> None:
    summary = run_rq7()

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert summary["synthetic_dry_run"] is False
    assert summary["toy_retrieval"] is True
    assert summary["salted_domain_gate"] is True

    manifest = json.loads((Path(summary["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["salted_domain_gate"] is True
    assert manifest["domain_salt_id"] == "HSRAG_RQ7_PUBLIC_REPRODUCIBLE_SALT_v1"


def test_rq7_domain_salt_hash_is_deterministic_per_domain() -> None:
    summary = run_rq7()
    rows = read_rows(summary)

    eu_rows = [
        row for row in rows
        if row["result"]
        and row["result"]["corpus"] == "EU_AI_ACT"
    ]

    assert eu_rows

    hashes = {row["result"]["domain_salt_hash"] for row in eu_rows}
    assert len(hashes) == 1

    address_hashes = {row["result"]["cthc_address_hash"] for row in eu_rows}
    assert len(address_hashes) == 1


def test_rq7_global_search_does_not_use_salt_for_pruning() -> None:
    summary = run_rq7()
    rows = read_rows(summary)

    global_rows = [
        row for row in rows
        if row["mode"] == "BM25_GLOBAL"
    ]

    assert global_rows

    for row in global_rows:
        assert row["route_boundary"]["used_for_pruning"] is False
        assert row["route_boundary"]["domain_salt_hash"] is None
        assert row["metrics"]["candidate_count_before"] == row["metrics"]["candidate_count_after"]


def test_rq7_cthc_pruned_uses_salted_domain_boundary() -> None:
    summary = run_rq7()
    rows = read_rows(summary)

    cthc_allow_rows = [
        row for row in rows
        if row["mode"] == "CTHC_PRUNED_BM25"
        and row["status"] == "ALLOW"
    ]

    assert cthc_allow_rows

    for row in cthc_allow_rows:
        assert row["route_boundary"]["used_for_pruning"] is True
        assert row["route_boundary"]["domain_salt_hash"].startswith("sha256:")
        assert row["metrics"]["candidate_count_after"] < row["metrics"]["candidate_count_before"]


def test_rq7_unique_address_returns_cthc_address_hash() -> None:
    summary = run_rq7()
    rows = read_rows(summary)

    unique_rows = [
        row for row in rows
        if row["mode"] == "UNIQUE_ADDRESS"
        and row["query_id"] == "Q_EXACT_UNIT_0001"
        and row["status"] == "ALLOW"
    ]

    assert unique_rows

    for row in unique_rows:
        assert row["route_boundary"]["used_for_unique_address"] is True
        assert row["result"]["domain_salt_hash"].startswith("sha256:")
        assert row["result"]["cthc_address_hash"].startswith("sha256:")
        assert row["metrics"]["returned_domain_salt_valid"] is True


def test_rq7_acceptance_gates_include_salted_domain_checks() -> None:
    summary = run_rq7()
    gates = json.loads(Path(summary["acceptance_gates"]).read_text(encoding="utf-8"))

    assert gates["passed"] is True
    assert gates["gate_results"]["returned_domain_salt_valid_rate_reported"] is True
    assert gates["gate_results"]["global_search_does_not_use_salt_for_pruning"] is True
    assert gates["gate_results"]["cthc_pruned_uses_salted_domain_boundary"] is True
