from __future__ import annotations

import argparse
import hashlib
import json
import random
import sqlite3
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


def utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_cthc(service_name: str, api_version: str, method: str, path: str) -> str:
    return f"API|{service_name}|{api_version}|{method.upper()}|{path}"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * p))
    return ordered[index]


def summarize_ms(samples: list[float]) -> dict[str, float]:
    return {
        "count": len(samples),
        "p50_ms": round(percentile(samples, 0.50), 6),
        "p95_ms": round(percentile(samples, 0.95), 6),
        "p99_ms": round(percentile(samples, 0.99), 6),
        "mean_ms": round(statistics.mean(samples), 6) if samples else 0.0,
        "max_ms": round(max(samples), 6) if samples else 0.0,
    }


def setup_db(dataset_size: int) -> tuple[sqlite3.Connection, list[dict[str, Any]]]:
    conn = sqlite3.connect(":memory:")

    conn.execute(
        """
        CREATE TABLE api_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cthc_hash TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            authority_hash TEXT NOT NULL,
            service_name TEXT NOT NULL,
            api_version TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            summary TEXT NOT NULL,
            evidence_class TEXT NOT NULL,
            tacl_layer TEXT NOT NULL,
            contract_role TEXT NOT NULL,
            is_current INTEGER NOT NULL
        )
        """
    )

    conn.execute("CREATE INDEX idx_api_specs_cthc_hash ON api_specs(cthc_hash)")
    conn.execute("CREATE INDEX idx_api_specs_method_path ON api_specs(method, path)")
    conn.execute("CREATE INDEX idx_api_specs_summary ON api_specs(summary)")

    records: list[dict[str, Any]] = []

    for i in range(dataset_size):
        method = VALID_METHODS[i % len(VALID_METHODS)]
        path = f"/demo/resources/{i}"
        service_name = "demo-service"
        api_version = "v1"
        summary = f"Demo endpoint for resource {i}"

        cthc = canonical_cthc(service_name, api_version, method, path)
        cthc_hash = sha256_text(cthc)
        authority_hash = sha256_text("TACL|L0|FHS|core")

        source_payload = {
            "service_name": service_name,
            "api_version": api_version,
            "method": method,
            "path": path,
            "summary": summary,
            "evidence_class": "FHS",
            "tacl_layer": "L0",
            "contract_role": "core",
        }

        source_hash = sha256_text(
            json.dumps(
                source_payload,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

        record = {
            "cthc_hash": cthc_hash,
            "source_hash": source_hash,
            "authority_hash": authority_hash,
            "service_name": service_name,
            "api_version": api_version,
            "method": method,
            "path": path,
            "summary": summary,
        }

        records.append(record)

        conn.execute(
            """
            INSERT INTO api_specs (
                cthc_hash,
                source_hash,
                authority_hash,
                service_name,
                api_version,
                method,
                path,
                summary,
                evidence_class,
                tacl_layer,
                contract_role,
                is_current
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cthc_hash,
                source_hash,
                authority_hash,
                service_name,
                api_version,
                method,
                path,
                summary,
                "FHS",
                "L0",
                "core",
                1,
            ),
        )

    conn.commit()
    return conn, records


def time_query(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> float:
    start = time.perf_counter_ns()
    list(conn.execute(sql, params))
    end = time.perf_counter_ns()
    return (end - start) / 1_000_000


def run_benchmark(runs: int, dataset_size: int, seed: int) -> dict[str, Any]:
    random.seed(seed)
    conn, records = setup_db(dataset_size)

    cthc_hash_samples: list[float] = []
    method_path_samples: list[float] = []
    semantic_discovery_samples: list[float] = []

    for _ in range(runs):
        record = random.choice(records)

        cthc_hash_samples.append(
            time_query(
                conn,
                """
                SELECT * FROM api_specs
                WHERE cthc_hash = ?
                  AND evidence_class = ?
                  AND tacl_layer = ?
                  AND contract_role = ?
                  AND is_current = 1
                """,
                (record["cthc_hash"], "FHS", "L0", "core"),
            )
        )

        method_path_samples.append(
            time_query(
                conn,
                """
                SELECT * FROM api_specs
                WHERE service_name = ?
                  AND api_version = ?
                  AND method = ?
                  AND path = ?
                  AND is_current = 1
                """,
                (
                    record["service_name"],
                    record["api_version"],
                    record["method"],
                    record["path"],
                ),
            )
        )

        semantic_discovery_samples.append(
            time_query(
                conn,
                """
                SELECT cthc_hash, method, path, summary
                FROM api_specs
                WHERE summary LIKE ?
                LIMIT 10
                """,
                ("%resource%",),
            )
        )

    return {
        "benchmark_name": "hsrag_api_sqlite_local_lookup_v0_1",
        "generated_at_utc": utc_now_z(),
        "runs": runs,
        "dataset_size": dataset_size,
        "seed": seed,
        "scope": {
            "local_only": True,
            "zero_secret": True,
            "zero_network": True,
            "sqlite_in_memory": True,
            "note": "This benchmark measures local SQLite lookup latency only. It is not a cloud RAG or LLM billing benchmark.",
        },
        "results": {
            "cthc_hash_lookup": summarize_ms(cthc_hash_samples),
            "method_path_lookup": summarize_ms(method_path_samples),
            "semantic_discovery_like_lookup": summarize_ms(semantic_discovery_samples),
        },
        "cost_profile": {
            "api_key_required": False,
            "network_calls": 0,
            "llm_calls_required": 0,
            "tokens_sent_to_llm": 0,
            "estimated_tokens_avoided_per_lookup": "not_measured_in_v0_1",
            "note": "Token avoidance is intentionally not claimed as a measured billing result in v0.1.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local benchmark for HSRAG API SQLite pointer lookup."
    )
    parser.add_argument("--runs", type=int, default=10000)
    parser.add_argument("--dataset-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260519)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/local_lookup_report.json"),
    )

    args = parser.parse_args()

    if args.runs <= 0:
        raise SystemExit("--runs must be positive")

    if args.dataset_size <= 0:
        raise SystemExit("--dataset-size must be positive")

    report = run_benchmark(args.runs, args.dataset_size, args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nBenchmark report written to: {args.output}")


if __name__ == "__main__":
    main()
