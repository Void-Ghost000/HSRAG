from __future__ import annotations

import csv
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


def test_rq7_runner_generates_toy_retrieval_outputs() -> None:
    summary = run_rq7()

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert summary["synthetic_dry_run"] is False
    assert summary["toy_retrieval"] is True

    run_dir = Path(summary["run_dir"])
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "raw_results.jsonl").exists()
    assert (run_dir / "metrics_summary.csv").exists()
    assert (run_dir / "acceptance_gates.json").exists()
    assert (run_dir / "audit_chain.jsonl").exists()


def test_rq7_raw_results_follow_result_contract() -> None:
    summary = run_rq7()
    raw_path = Path(summary["raw_results"])
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]

    assert rows

    required_fields = {
        "status",
        "reason_code",
        "retryable",
        "mode",
        "query_id",
        "query_class",
        "corpus_size",
        "target",
        "result",
        "metrics",
        "hashes",
    }

    required_hashes = {
        "query_hash",
        "source_hash",
        "evidence_hash",
        "decision_hash",
        "run_hash",
    }

    for row in rows:
        assert required_fields.issubset(row.keys())
        assert required_hashes.issubset(row["hashes"].keys())
        assert "latency_ms" in row["metrics"]
        assert "retrieved_token_count" in row["metrics"]
        assert "esi" in row["metrics"]
        assert "candidate_count_before" in row["metrics"]
        assert "candidate_count_after" in row["metrics"]


def test_rq7_metrics_include_p99_esi_and_token_cost() -> None:
    summary = run_rq7()
    metrics_path = Path(summary["metrics_summary"])

    with metrics_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows
    assert "latency_p99_ms" in reader.fieldnames
    assert "esi_mean" in reader.fieldnames
    assert "estimated_token_cost_usd_per_1k_queries" in reader.fieldnames
    assert "token_reduction_ratio" in reader.fieldnames


def test_rq7_acceptance_gates_pass_for_toy_retrieval_contract() -> None:
    summary = run_rq7()
    gates = json.loads(Path(summary["acceptance_gates"]).read_text(encoding="utf-8"))

    assert gates["passed"] is True
    assert gates["gate_results"]["audit_hash_complete_rate_min_1_0"] is True
    assert gates["gate_results"]["route_determinism_rate_min_1_0"] is True
    assert gates["gate_results"]["p99_required_for_every_mode"] is True
    assert gates["gate_results"]["token_cost_required_for_every_mode"] is True
    assert gates["gate_results"]["esi_required_for_every_mode"] is True


def test_rq7_audit_chain_is_hash_linked() -> None:
    summary = run_rq7()
    events = [
        json.loads(line)
        for line in Path(summary["audit_chain"]).read_text(encoding="utf-8").splitlines()
    ]

    assert len(events) >= 4
    assert events[0]["previous_event_hash"] is None

    for previous, current in zip(events, events[1:]):
        assert current["previous_event_hash"] == previous["event_hash"]

    timestamps = {event["event_time_utc"] for event in events}
    assert len(timestamps) == 1
    assert next(iter(timestamps)).endswith("Z")


def test_rq7_toy_retrieval_exact_unit_finds_eu_ai_act_article_5() -> None:
    summary = run_rq7()
    rows = [
        json.loads(line)
        for line in Path(summary["raw_results"]).read_text(encoding="utf-8").splitlines()
    ]

    exact_rows = [
        row for row in rows
        if row["query_id"] == "Q_EXACT_UNIT_0001"
        and row["mode"] in {"BM25_GLOBAL", "CTHC_PRUNED_BM25", "UNIQUE_ADDRESS"}
        and row["corpus_size"] == 1000
    ]

    assert exact_rows

    for row in exact_rows:
        assert row["status"] == "ALLOW"
        assert row["result"]["corpus"] == "EU_AI_ACT"
        assert row["result"]["unit"] == "ARTICLE_5"


def test_rq7_hsrag_modes_block_no_evidence() -> None:
    summary = run_rq7()
    rows = [
        json.loads(line)
        for line in Path(summary["raw_results"]).read_text(encoding="utf-8").splitlines()
    ]

    hsrag_rows = [
        row for row in rows
        if row["query_id"] == "Q_NO_EVIDENCE_0001"
        and row["mode"] in {"CTHC_PRUNED_BM25", "CTHC_PRUNED_TFIDF", "UNIQUE_ADDRESS"}
    ]

    assert hsrag_rows

    for row in hsrag_rows:
        assert row["status"] == "BLOCK"
        assert row["reason_code"] in {"NO_EVIDENCE", "UNIQUE_ADDRESS_NOT_FOUND"}
