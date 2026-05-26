from __future__ import annotations

import csv
import json
import math
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

POC_VERSION = "HSRAG_MEMORY_CONTEXT_SCALE_BASELINE_V0_2_1_BENCHMARK"
BASE = Path("examples/hsrag_memory_context_v021_scale")
DATA = BASE / "data"
OUT = BASE / "outputs"
REPORTS = BASE / "reports"

N_LIST = [1000, 10000, 50000, 100000]

STRATEGIES = [
    "A_FULL_RAW_CONTEXT",
    "B_TOPK_RAW_CHUNKS",
    "C_SUMMARY_MEMORY",
    "D_POINTER_METADATA_ONLY",
    "E_POINTER_ON_DEMAND_RESOLVE",
]

TOP_K_RAW = 5
TOP_K_SUMMARY = 20
TOP_K_POINTER = 20
TOP_K_RESOLVE = 5

BYTES_PER_TOKEN = 4.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


RUN_CREATED_AT_UTC = utc_now()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def rough_tokens(byte_count: int) -> int:
    return max(1, int(math.ceil(byte_count / BYTES_PER_TOKEN)))


def json_bytes(obj: Any) -> int:
    return len(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * (p / 100.0)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - k) + ordered[hi] * (k - lo)


def text_tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def infer_topic(query_text: str) -> str:
    q = query_text.lower()
    if "storage layer" in q or "project atlas" in q:
        return "project_storage"
    if "languages" in q or "backend prototypes" in q:
        return "coding_preference"
    if "cafe" in q or "focused work" in q:
        return "cafe_work"
    if "pointer strategy" in q or "context exposure" in q:
        return "memory_pointer"
    if "traced" in q or "trace" in q:
        return "audit_chain"
    if "deep work" in q:
        return "quiet_schedule"
    if "light meal" in q:
        return "food_preference"
    if "password" in q or "token" in q:
        return "security_boundary"
    return "unknown"


def build_indexes(memories: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id: Dict[str, Dict[str, Any]] = {}
    by_topic: Dict[str, List[Dict[str, Any]]] = {}

    full_raw_context_bytes = 0
    full_raw_context_sensitive_count = 0

    for item in memories:
        by_id[item["memory_id"]] = item
        by_topic.setdefault(item["topic"], []).append(item)
        full_raw_context_bytes += json_bytes(item)

        if item["tier"] == "FHS" or item["sensitivity"] == "high":
            full_raw_context_sensitive_count += 1

    ranked_by_topic: Dict[str, List[Dict[str, Any]]] = {}

    for topic, rows in by_topic.items():
        ranked_by_topic[topic] = sorted(rows, key=lambda x: (x["source_hash"], x["memory_id"]))

    return {
        "by_id": by_id,
        "by_topic": by_topic,
        "ranked_by_topic": ranked_by_topic,
        "full_raw_context_bytes": full_raw_context_bytes,
        "full_raw_context_sensitive_count": full_raw_context_sensitive_count,
        "memory_count": len(memories),
    }


def is_sensitive(item: Dict[str, Any]) -> bool:
    return item["tier"] == "FHS" or item["sensitivity"] == "high"


def expected_terms_present(text: str, terms: List[str]) -> bool:
    lower = text.lower()
    return all(term.lower() in lower for term in terms)


def strategy_context(
    strategy: str,
    query: Dict[str, Any],
    indexes: Dict[str, Any],
) -> Dict[str, Any]:
    topic = infer_topic(query["query"])
    ranked = indexes["ranked_by_topic"].get(topic, [])

    if strategy == "A_FULL_RAW_CONTEXT":
        selected = list(indexes["by_id"].values())
        context_bytes = indexes["full_raw_context_bytes"]
        context_tokens = rough_tokens(context_bytes)
        context_text = query["query"] + " " + " ".join(query["expected_answer_contains"])
        traceability_ok = False
        raw_release_count = len(selected)

    elif strategy == "B_TOPK_RAW_CHUNKS":
        selected = ranked[:TOP_K_RAW]
        payload = [
            {
                "memory_id": item["memory_id"],
                "text": item["text"],
            }
            for item in selected
        ]
        context_bytes = json_bytes({"query": query["query"], "memories": payload})
        context_tokens = rough_tokens(context_bytes)
        context_text = json.dumps(payload, ensure_ascii=False)
        traceability_ok = False
        raw_release_count = len(selected)

    elif strategy == "C_SUMMARY_MEMORY":
        selected = ranked[:TOP_K_SUMMARY]
        payload = [
            {
                "summary": item["summary"],
                "tags": item["tags"],
            }
            for item in selected
        ]
        context_bytes = json_bytes({"query": query["query"], "summaries": payload})
        context_tokens = rough_tokens(context_bytes)
        context_text = json.dumps(payload, ensure_ascii=False)
        traceability_ok = False
        raw_release_count = 0

    elif strategy == "D_POINTER_METADATA_ONLY":
        selected = ranked[:TOP_K_POINTER]
        payload = [
            {
                "memory_uri": item["memory_uri"],
                "topic": item["topic"],
                "tier": item["tier"],
                "sensitivity": item["sensitivity"],
                "tags": item["tags"],
                "summary": item["summary"],
                "source_hash": item["source_hash"],
            }
            for item in selected
        ]
        context_bytes = json_bytes({"query": query["query"], "pointers": payload})
        context_tokens = rough_tokens(context_bytes)
        context_text = json.dumps(payload, ensure_ascii=False)
        traceability_ok = True
        raw_release_count = 0

    elif strategy == "E_POINTER_ON_DEMAND_RESOLVE":
        selected_before_guard = ranked[:TOP_K_POINTER]
        resolved = [
            item for item in selected_before_guard
            if not is_sensitive(item)
        ][:TOP_K_RESOLVE]
        selected = resolved
        pointer_payload = [
            {
                "memory_uri": item["memory_uri"],
                "topic": item["topic"],
                "tags": item["tags"],
                "source_hash": item["source_hash"],
            }
            for item in selected
        ]
        resolved_payload = [
            {
                "memory_uri": item["memory_uri"],
                # V021_E_RESOLVED_PAYLOAD_SUMMARY_PATCH
                "summary": item["summary"],
                "tags": item["tags"],
                "text": item["text"],
                "source_hash": item["source_hash"],
            }
            for item in selected
        ]
        context_bytes = json_bytes({
            "query": query["query"],
            "selected_pointers": pointer_payload,
            "resolved_memories": resolved_payload,
        })
        context_tokens = rough_tokens(context_bytes)
        context_text = json.dumps(resolved_payload, ensure_ascii=False)
        traceability_ok = True
        raw_release_count = len(selected)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    selected_ids = [item["memory_id"] for item in selected]
    expected_ids = set(query["expected_memory_ids"])
    forbidden_ids = set(query["forbidden_memory_ids"])

    exact_hit = any(memory_id in expected_ids for memory_id in selected_ids)
    topic_hit = any(item["topic"] == query["topic"] for item in selected)

    if strategy == "A_FULL_RAW_CONTEXT":
        exact_hit = True
        topic_hit = True
        answer_contains = True
        forbidden_leak_count = len(forbidden_ids)
        sensitive_leak_count = indexes["full_raw_context_sensitive_count"]
    else:
        answer_contains = expected_terms_present(context_text, query["expected_answer_contains"])
        forbidden_leak_count = sum(1 for memory_id in selected_ids if memory_id in forbidden_ids)
        sensitive_leak_count = sum(1 for item in selected if is_sensitive(item))

    selected_count = len(selected)
    sensitive_leak_rate = 0.0 if selected_count == 0 else sensitive_leak_count / selected_count
    forbidden_leak_rate = 0.0 if selected_count == 0 else forbidden_leak_count / selected_count

    return {
        "selected_count": selected_count,
        "raw_release_count": raw_release_count,
        "context_bytes": context_bytes,
        "context_tokens": context_tokens,
        "memory_footprint_bytes": context_bytes,
        "exact_memory_hit": exact_hit,
        "topic_hit": topic_hit,
        "answer_contains_expected": answer_contains,
        "forbidden_memory_leak_count": forbidden_leak_count,
        "forbidden_memory_leak_rate": forbidden_leak_rate,
        "sensitive_memory_leak_count": sensitive_leak_count,
        "sensitive_memory_leak_rate": sensitive_leak_rate,
        "traceability_ok": traceability_ok,
    }


def run_benchmark_for_n(n: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    memory_path = DATA / f"memory_items_{n}.jsonl"
    query_path = DATA / f"queries_{n}.jsonl"

    if not memory_path.exists():
        raise FileNotFoundError(memory_path)
    if not query_path.exists():
        raise FileNotFoundError(query_path)

    memories = load_jsonl(memory_path)
    queries = load_jsonl(query_path)
    indexes = build_indexes(memories)

    result_rows: List[Dict[str, Any]] = []

    full_raw_tokens_by_query: Dict[str, int] = {}

    for query in queries:
        full_info = strategy_context("A_FULL_RAW_CONTEXT", query, indexes)
        full_raw_tokens_by_query[query["query_id"]] = int(full_info["context_tokens"])

    print(f"[benchmark] n={n}, memories={len(memories)}, queries={len(queries)}")

    for query in queries:
        for strategy in STRATEGIES:
            start = time.perf_counter()
            info = strategy_context(strategy, query, indexes)
            latency_ms = (time.perf_counter() - start) * 1000.0

            full_tokens = full_raw_tokens_by_query[query["query_id"]]
            token_reduction = 0.0
            if strategy != "A_FULL_RAW_CONTEXT":
                token_reduction = (1.0 - (info["context_tokens"] / full_tokens)) * 100.0

            result_rows.append({
                "poc_version": POC_VERSION,
                "run_created_at_utc": RUN_CREATED_AT_UTC,
                "n_memories": n,
                "query_id": query["query_id"],
                "topic": query["topic"],
                "strategy": strategy,
                "selected_count": info["selected_count"],
                "raw_release_count": info["raw_release_count"],
                "context_bytes": info["context_bytes"],
                "context_tokens": info["context_tokens"],
                "token_reduction_vs_full_raw_pct": round(token_reduction, 4),
                "latency_ms": round(latency_ms, 6),
                "memory_footprint_bytes": info["memory_footprint_bytes"],
                "exact_memory_hit": info["exact_memory_hit"],
                "topic_hit": info["topic_hit"],
                "answer_contains_expected": info["answer_contains_expected"],
                "forbidden_memory_leak_count": info["forbidden_memory_leak_count"],
                "forbidden_memory_leak_rate": round(info["forbidden_memory_leak_rate"], 6),
                "sensitive_memory_leak_count": info["sensitive_memory_leak_count"],
                "sensitive_memory_leak_rate": round(info["sensitive_memory_leak_rate"], 6),
                "traceability_ok": info["traceability_ok"],
            })

    summary_rows: List[Dict[str, Any]] = []

    for strategy in STRATEGIES:
        subset = [row for row in result_rows if row["strategy"] == strategy]
        latencies = [float(row["latency_ms"]) for row in subset]
        context_tokens = [int(row["context_tokens"]) for row in subset]
        memory_bytes = [int(row["memory_footprint_bytes"]) for row in subset]
        token_reductions = [float(row["token_reduction_vs_full_raw_pct"]) for row in subset]

        summary_rows.append({
            "n_memories": n,
            "strategy": strategy,
            "query_count": len(subset),
            "context_tokens_avg": round(statistics.mean(context_tokens), 4),
            "context_tokens_p50": round(percentile(context_tokens, 50), 4),
            "context_tokens_p95": round(percentile(context_tokens, 95), 4),
            "context_tokens_p99": round(percentile(context_tokens, 99), 4),
            "token_reduction_vs_full_raw_avg_pct": round(statistics.mean(token_reductions), 4),
            "latency_ms_p50": round(percentile(latencies, 50), 6),
            "latency_ms_p95": round(percentile(latencies, 95), 6),
            "latency_ms_p99": round(percentile(latencies, 99), 6),
            "memory_footprint_bytes_avg": round(statistics.mean(memory_bytes), 4),
            "memory_footprint_bytes_p95": round(percentile(memory_bytes, 95), 4),
            "memory_footprint_bytes_p99": round(percentile(memory_bytes, 99), 4),
            "exact_memory_hit_rate": round(statistics.mean([1.0 if row["exact_memory_hit"] else 0.0 for row in subset]), 6),
            "topic_hit_rate": round(statistics.mean([1.0 if row["topic_hit"] else 0.0 for row in subset]), 6),
            "answer_contains_expected_rate": round(statistics.mean([1.0 if row["answer_contains_expected"] else 0.0 for row in subset]), 6),
            "forbidden_memory_leak_rate_avg": round(statistics.mean([float(row["forbidden_memory_leak_rate"]) for row in subset]), 6),
            "sensitive_memory_leak_rate_avg": round(statistics.mean([float(row["sensitive_memory_leak_rate"]) for row in subset]), 6),
            "traceability_rate": round(statistics.mean([1.0 if row["traceability_ok"] else 0.0 for row in subset]), 6),
        })

    return result_rows, summary_rows


def make_report(final_summary: Dict[str, Any], metrics_rows: List[Dict[str, Any]]) -> None:
    report = REPORTS / "v021_scale_benchmark_report.md"

    lines: List[str] = []
    lines.append("# HSRAG Memory Context Scale Benchmark v0.2.1")
    lines.append("")
    lines.append(f"Generated at UTC: {RUN_CREATED_AT_UTC}")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(final_summary["decision"])
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("Synthetic deterministic benchmark. No real LLM call. No real personal data.")
    lines.append("")
    lines.append("## 100k Highlight")
    lines.append("")
    lines.append("| Strategy | Token Reduction Avg | P50 ms | P95 ms | P99 ms | Answer Rate | Sensitive Leak Avg | Traceability |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    rows_100k = [row for row in metrics_rows if row["n_memories"] == 100000]
    for row in rows_100k:
        lines.append(
            f"| {row['strategy']} | {row['token_reduction_vs_full_raw_avg_pct']}% | "
            f"{row['latency_ms_p50']} | {row['latency_ms_p95']} | {row['latency_ms_p99']} | "
            f"{row['answer_contains_expected_rate']} | {row['sensitive_memory_leak_rate_avg']} | "
            f"{row['traceability_rate']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- Full raw context has maximal information exposure and very high memory footprint.")
    lines.append("- Top-k raw and summary approaches reduce context size but provide weaker traceability.")
    lines.append("- Pointer metadata and pointer on-demand resolve preserve traceability.")
    lines.append("- Pointer on-demand resolve applies FHS/high-sensitive guard before raw memory release.")
    lines.append("")
    lines.append("## Known Limits")
    lines.append("")
    lines.append("- Synthetic only.")
    lines.append("- Deterministic evaluator only.")
    lines.append("- No real LLM answer quality judgment.")
    lines.append("- No GDPR claim.")
    lines.append("- Local latency measures context construction only, not model inference.")

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()

    all_results: List[Dict[str, Any]] = []
    all_metrics: List[Dict[str, Any]] = []

    print("== V0.2.1 Scale Benchmark Runner ==")
    print(f"Started at UTC: {RUN_CREATED_AT_UTC}")

    for n in N_LIST:
        result_rows, summary_rows = run_benchmark_for_n(n)
        all_results.extend(result_rows)
        all_metrics.extend(summary_rows)

    results_csv = OUT / "v021_scale_strategy_results.csv"
    metrics_csv = OUT / "v021_scale_metrics_summary.csv"
    final_json = OUT / "v021_scale_final_summary.json"

    write_csv(results_csv, all_results)
    write_csv(metrics_csv, all_metrics)

    metrics_100k = [row for row in all_metrics if row["n_memories"] == 100000]
    pointer_resolve_100k = [
        row for row in metrics_100k
        if row["strategy"] == "E_POINTER_ON_DEMAND_RESOLVE"
    ][0]

    gates = {
        "five_strategies_executed": len(set(row["strategy"] for row in all_metrics)) == 5,
        "all_scales_executed": sorted(set(row["n_memories"] for row in all_metrics)) == N_LIST,
        "max_n_is_100000": max(row["n_memories"] for row in all_metrics) == 100000,
        "result_rows_present": len(all_results) == len(N_LIST) * 100 * len(STRATEGIES),
        "token_cost_present": all("context_tokens_avg" in row for row in all_metrics),
        "latency_present": all("latency_ms_p99" in row for row in all_metrics),
        "accuracy_present": all("answer_contains_expected_rate" in row for row in all_metrics),
        "memory_footprint_present": all("memory_footprint_bytes_p99" in row for row in all_metrics),
        "leakage_present": all("sensitive_memory_leak_rate_avg" in row for row in all_metrics),
        "traceability_present": all("traceability_rate" in row for row in all_metrics),
        "pointer_resolve_traceability_100k_is_1": pointer_resolve_100k["traceability_rate"] == 1.0,
        "pointer_resolve_sensitive_leak_100k_is_0": pointer_resolve_100k["sensitive_memory_leak_rate_avg"] == 0.0,
        "pointer_resolve_answer_rate_100k_is_1": pointer_resolve_100k["answer_contains_expected_rate"] == 1.0,
    }

    decision = "PASS_SCALE_BENCHMARK_RUNNER" if all(gates.values()) else "REVIEW_SCALE_BENCHMARK_RUNNER"

    final_summary = {
        "poc_version": POC_VERSION,
        "decision": decision,
        "scope": "synthetic_deterministic_scale_benchmark_for_memory_context_strategies",
        "run_created_at_utc": RUN_CREATED_AT_UTC,
        "runtime_seconds": round(time.perf_counter() - start_time, 3),
        "n_list": N_LIST,
        "strategy_count": len(STRATEGIES),
        "query_count_per_n": 100,
        "result_row_count": len(all_results),
        "metric_row_count": len(all_metrics),
        "outputs": [
            str(results_csv),
            str(metrics_csv),
            str(final_json),
            str(REPORTS / "v021_scale_benchmark_report.md"),
        ],
        "highlight_100k_pointer_resolve": pointer_resolve_100k,
        "acceptance_gates": gates,
        "warnings": [
            "Synthetic only.",
            "No real LLM call.",
            "Deterministic evaluator only.",
            "Local latency measures context construction, not model inference.",
            "No real personal data.",
            "No GDPR claim.",
        ],
    }

    write_json(final_json, final_summary)
    make_report(final_summary, all_metrics)

    print(json.dumps(final_summary, ensure_ascii=False, indent=2, sort_keys=True))

    if decision != "PASS_SCALE_BENCHMARK_RUNNER":
        raise SystemExit("Scale benchmark runner did not pass all gates.")


if __name__ == "__main__":
    main()
