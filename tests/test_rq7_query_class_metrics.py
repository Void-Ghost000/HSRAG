from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_generates_metrics_by_query_class() -> None:
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

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert "metrics_by_query_class" in summary

    metrics_path = Path(summary["metrics_by_query_class"])
    assert metrics_path.exists()

    with metrics_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows
    assert "query_class" in reader.fieldnames
    assert "latency_p99_ms" in reader.fieldnames
    assert "esi_mean" in reader.fieldnames
    assert "estimated_token_cost_usd_per_1k_queries" in reader.fieldnames
    assert "false_allow_rate" in reader.fieldnames
    assert "candidate_reduction_ratio" in reader.fieldnames

    query_classes = {row["query_class"] for row in rows}
    assert "exact_unit" in query_classes
    assert "no_evidence" in query_classes
    assert "ambiguous_cross_domain" in query_classes


def test_rq7_query_class_no_evidence_hsrag_false_allow_zero() -> None:
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

    summary = json.loads(result.stdout)
    metrics_path = Path(summary["metrics_by_query_class"])

    with metrics_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    hsrag_no_evidence = [
        row for row in rows
        if row["query_class"] == "no_evidence"
        and row["mode"] in {"CTHC_PRUNED_BM25", "CTHC_PRUNED_TFIDF", "UNIQUE_ADDRESS"}
    ]

    assert hsrag_no_evidence

    for row in hsrag_no_evidence:
        assert float(row["false_allow_rate"]) == 0.0


def test_rq7_verify_requires_metrics_by_query_class_artifact() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["required_artifacts_exist"] is True

    runner = summary["runner"]
    assert "metrics_by_query_class" in runner
    assert Path(runner["metrics_by_query_class"]).exists()
