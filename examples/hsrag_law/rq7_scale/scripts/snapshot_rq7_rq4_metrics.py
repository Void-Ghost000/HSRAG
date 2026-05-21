from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def index_by_mode(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["mode"], []).append(row)
    return grouped


def summarize_mode_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for row in rows:
        summaries.append(
            {
                "mode": row["mode"],
                "corpus_size": int(float(row["corpus_size"])),
                "target_correct_rate": float(row["target_correct_rate"]),
                "candidate_reduction_ratio": float(row["candidate_reduction_ratio"]),
                "retrieved_token_count_mean": float(row["retrieved_token_count_mean"]),
                "estimated_token_cost_usd_per_1k_queries": float(row["estimated_token_cost_usd_per_1k_queries"]),
                "latency_p99_ms": float(row["latency_p99_ms"]),
                "actual_elapsed_p50_ms": float(row.get("actual_elapsed_p50_ms", 0.0)),
                "actual_elapsed_p95_ms": float(row.get("actual_elapsed_p95_ms", 0.0)),
                "actual_elapsed_p99_ms": float(row.get("actual_elapsed_p99_ms", 0.0)),
                "esi_mean": float(row["esi_mean"]),
                "returned_domain_salt_valid_rate": float(row.get("returned_domain_salt_valid_rate", 0.0)),
            }
        )

    return summaries


def summarize_query_class_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for row in rows:
        summaries.append(
            {
                "mode": row["mode"],
                "corpus_size": int(float(row["corpus_size"])),
                "query_class": row["query_class"],
                "target_correct_rate": float(row["target_correct_rate"]),
                "false_allow_rate": float(row["false_allow_rate"]),
                "correct_block_rate": float(row["correct_block_rate"]),
                "candidate_reduction_ratio": float(row["candidate_reduction_ratio"]),
                "latency_p99_ms": float(row["latency_p99_ms"]),
                "actual_elapsed_p50_ms": float(row.get("actual_elapsed_p50_ms", 0.0)),
                "actual_elapsed_p95_ms": float(row.get("actual_elapsed_p95_ms", 0.0)),
                "actual_elapsed_p99_ms": float(row.get("actual_elapsed_p99_ms", 0.0)),
                "esi_mean": float(row["esi_mean"]),
            }
        )

    return summaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = "rq7_rq4_metrics_snapshot_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    snapshot_dir = base_dir / "04_runs" / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    verify_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "verify_rq7_rq4.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
        ]
    )

    runner = verify_summary["runner"]
    metrics_summary_path = Path(runner["metrics_summary"])
    metrics_by_query_class_path = Path(runner["metrics_by_query_class"])

    if not metrics_summary_path.exists():
        raise SystemExit(f"METRICS_SUMMARY_NOT_FOUND:{metrics_summary_path}")

    if not metrics_by_query_class_path.exists():
        raise SystemExit(f"METRICS_BY_QUERY_CLASS_NOT_FOUND:{metrics_by_query_class_path}")

    metrics_rows = read_csv_rows(metrics_summary_path)
    query_class_rows = read_csv_rows(metrics_by_query_class_path)

    mode_summaries = summarize_mode_rows(metrics_rows)
    query_class_summaries = summarize_query_class_rows(query_class_rows)

    modes = sorted({row["mode"] for row in mode_summaries})
    query_classes = sorted({row["query_class"] for row in query_class_summaries})

    required_modes = {
        "BM25_GLOBAL",
        "TFIDF_GLOBAL",
        "CTHC_PRUNED_BM25",
        "CTHC_PRUNED_TFIDF",
        "UNIQUE_ADDRESS",
    }

    passed = (
        verify_summary.get("status") == "OK"
        and verify_summary.get("acceptance_passed") is True
        and verify_summary.get("latest_report_is_clean") is True
        and verify_summary.get("registry", {}).get("chunk_count", 0) >= 800
        and required_modes.issubset(set(modes))
        and "exact_unit" in query_classes
        and "no_evidence" in query_classes
        and "ambiguous_cross_domain" in query_classes
    )

    snapshot = {
        "schema": "HSRAG_RQ7_RQ4_METRICS_SNAPSHOT_V0_1",
        "status": "OK" if passed else "FAILED",
        "snapshot_id": snapshot_id,
        "run_started_at_utc": run_started_at_utc,
        "rq4_csv": str(rq4_csv_path),
        "rq4_verify": {
            "status": verify_summary.get("status"),
            "verify_id": verify_summary.get("verify_id"),
            "acceptance_passed": verify_summary.get("acceptance_passed"),
            "latest_report_is_clean": verify_summary.get("latest_report_is_clean"),
            "chunk_count": verify_summary.get("registry", {}).get("chunk_count"),
            "corpora": verify_summary.get("registry", {}).get("corpora"),
            "unit_count": verify_summary.get("registry", {}).get("unit_count"),
            "unit_derivation_is_heuristic": verify_summary.get("claim_boundary", {}).get("unit_derivation_is_heuristic"),
        },
        "metrics_summary_path": str(metrics_summary_path),
        "metrics_by_query_class_path": str(metrics_by_query_class_path),
        "mode_count": len(modes),
        "modes": modes,
        "query_class_count": len(query_classes),
        "query_classes": query_classes,
        "mode_summaries": mode_summaries,
        "query_class_summaries": query_class_summaries,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "metrics_snapshot_only": True,
            "full_scale_benchmark": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    snapshot_json = snapshot_dir / "rq7_rq4_metrics_snapshot.json"
    snapshot_txt = snapshot_dir / "rq7_rq4_metrics_snapshot.txt"

    write_json(snapshot_json, snapshot)

    lines = [
        "HSRAG RQ7 RQ4 metrics snapshot",
        "",
        f"status: {snapshot['status']}",
        f"snapshot_id: {snapshot_id}",
        f"rq4_csv: {rq4_csv_path}",
        f"chunk_count: {snapshot['rq4_verify']['chunk_count']}",
        f"mode_count: {snapshot['mode_count']}",
        f"query_class_count: {snapshot['query_class_count']}",
        f"acceptance_passed: {snapshot['rq4_verify']['acceptance_passed']}",
        f"latest_report_is_clean: {snapshot['rq4_verify']['latest_report_is_clean']}",
        "",
        "modes:",
    ]

    for mode in modes:
        lines.append(f"- {mode}")

    lines.extend(
        [
            "",
            "query_classes:",
        ]
    )

    for query_class in query_classes:
        lines.append(f"- {query_class}")

    lines.extend(
        [
            "",
            "claim_boundary:",
            "- rq4_rebuilt_artifact_connected: true",
            "- metrics_snapshot_only: true",
            "- full_scale_benchmark: false",
            "- unit_derivation_is_heuristic: true",
            "- legal_advice: false",
            "",
            f"snapshot_json: {snapshot_json}",
        ]
    )

    snapshot_txt.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
