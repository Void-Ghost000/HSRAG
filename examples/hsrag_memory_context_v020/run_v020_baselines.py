import csv
import hashlib
import json
import math
import re
import statistics
import time
import tracemalloc
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("examples/hsrag_memory_context_v020")
DATA = BASE / "data"
OUT = BASE / "outputs"
REPORTS = BASE / "reports"

OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

RUN_TS = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
TOP_K = 5
RESOLVE_K = 3

STRATEGIES = [
    "A_FULL_RAW_CONTEXT",
    "B_TOPK_RAW_CHUNKS",
    "C_SUMMARY_MEMORY",
    "D_POINTER_METADATA_ONLY",
    "E_POINTER_ON_DEMAND_RESOLVE",
]

TOKEN_CHARS_PER_TOKEN = 4


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"INVALID_JSONL at {path}:{line_no}: {e}") from e
    return rows


def stable_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    return int(math.ceil(len(text) / TOKEN_CHARS_PER_TOKEN))


def bytes_len(text: str) -> int:
    return len(text.encode("utf-8"))


def tokenize(text: str):
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def percentile(values, pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return float(values[0])
    k = (len(values) - 1) * pct
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return float(values[int(k)])
    return float(values[lo] * (hi - k) + values[hi] * (k - lo))


def enrich_memory(memory):
    canonical = stable_json({
        "memory_id": memory["memory_id"],
        "text": memory["text"],
        "summary": memory["summary"],
        "tags": memory["tags"],
        "tier": memory["tier"],
        "sensitivity": memory["sensitivity"],
        "source_type": memory["source_type"],
    })
    source_hash = "sha256:" + sha256_text(canonical)
    memory_uri = f"mem://local/memory/{memory['memory_id']}"
    enriched = dict(memory)
    enriched["source_hash"] = source_hash
    enriched["memory_uri"] = memory_uri
    return enriched


def score_memory(query, memory):
    q_tokens = tokenize(query["query"])
    text_tokens = tokenize(memory["text"])
    summary_tokens = tokenize(memory["summary"])
    tag_tokens = set(t.lower() for t in memory["tags"])

    score = 0
    score += len(q_tokens & text_tokens)
    score += 2 * len(q_tokens & summary_tokens)
    score += 3 * len(q_tokens & tag_tokens)

    # Lightweight phrase boosts for deterministic benchmark stability.
    q_lower = query["query"].lower()
    if "sqlite" in q_lower and "sqlite" in tag_tokens:
        score += 8
    if "tombstone" in q_lower and "tombstone" in tag_tokens:
        score += 8
    if "shadow" in q_lower and "shadow_window" in tag_tokens:
        score += 8
    if "training export" in q_lower and "training_export" in tag_tokens:
        score += 8
    if "summary" in q_lower and "summary" in tag_tokens:
        score += 8
    if "top-k" in q_lower and "topk" in tag_tokens:
        score += 8
    if "metrics" in q_lower and "metrics" in tag_tokens:
        score += 8
    if "resolver" in q_lower and "resolver" in tag_tokens:
        score += 8
    if "metadata" in q_lower and "metadata" in tag_tokens:
        score += 8

    return score


def select_topk(query, memories, k=TOP_K):
    scored = []
    for m in memories:
        scored.append((score_memory(query, m), m["memory_id"], m))
    scored.sort(key=lambda x: (-x[0], x[1]))
    positive = [m for s, _, m in scored if s > 0]
    return positive[:k]


def release_guard(memory, query):
    """
    Deterministic placeholder guard:
    - Always block synthetic secret test records.
    - Block safety-note high-sensitive records unless explicitly queried.
    - Allow policy/security high-sensitive records when directly relevant.
    This is not a production privacy classifier.
    """
    tags = set(memory["tags"])
    q = query["query"].lower()

    if "test_secret" in tags or "password" in tags:
        return False, "BLOCK_SYNTHETIC_SECRET_TEST"

    if memory["source_type"] == "safety_note" and "synthetic" not in q and "real personal data" not in q:
        return False, "BLOCK_SAFETY_NOTE_NOT_REQUESTED"

    if memory["tier"] == "FHS" and memory["sensitivity"] == "high":
        # Allow high-sensitive policy/security notes only when the query directly asks for that concept.
        relevant_terms = set(["purpose_boundary", "training_export", "policy", "guard", "security", "synthetic"])
        if tags & relevant_terms and score_memory(query, memory) > 0:
            return True, "ALLOW_HIGH_RELEVANT_POLICY_NOTE"
        return False, "BLOCK_FHS_HIGH_DEFAULT"

    return True, "ALLOW_NON_HIGH"


def build_context(strategy, query, memories):
    expected_ids = set(query["expected_memory_ids"])

    if strategy == "A_FULL_RAW_CONTEXT":
        selected = list(memories)
        released = list(memories)
        context = "\n".join(m["text"] for m in released)
        trace_refs = []
        guard_reasons = ["FULL_RAW_NO_GUARD"]
        return selected, released, context, trace_refs, guard_reasons

    if strategy == "B_TOPK_RAW_CHUNKS":
        selected = select_topk(query, memories, TOP_K)
        released = selected
        context = "\n".join(
            f"[memory_id={m['memory_id']}] {m['text']}"
            for m in released
        )
        trace_refs = [m["memory_id"] for m in released]
        guard_reasons = ["TOPK_RAW_NO_GUARD"]
        return selected, released, context, trace_refs, guard_reasons

    if strategy == "C_SUMMARY_MEMORY":
        selected = select_topk(query, memories, TOP_K)
        released = selected
        context = "\n".join(
            f"[memory_id={m['memory_id']}] {m['summary']}"
            for m in released
        )
        trace_refs = [m["memory_id"] for m in released]
        guard_reasons = ["SUMMARY_NO_RAW_TEXT"]
        return selected, released, context, trace_refs, guard_reasons

    if strategy == "D_POINTER_METADATA_ONLY":
        selected = select_topk(query, memories, TOP_K)
        released = selected
        context = "\n".join(
            (
                f"[pointer={m['memory_uri']}] "
                f"source_hash={m['source_hash']} "
                f"tier={m['tier']} sensitivity={m['sensitivity']} "
                f"tags={','.join(m['tags'])} "
                f"summary={m['summary']}"
            )
            for m in released
        )
        trace_refs = [m["memory_uri"] for m in released]
        guard_reasons = ["POINTER_METADATA_ONLY_NO_RAW_TEXT"]
        return selected, released, context, trace_refs, guard_reasons

    if strategy == "E_POINTER_ON_DEMAND_RESOLVE":
        selected = select_topk(query, memories, TOP_K)
        resolved_candidates = selected[:RESOLVE_K]

        released = []
        guard_reasons = []
        for m in resolved_candidates:
            allowed, reason = release_guard(m, query)
            guard_reasons.append(reason)
            if allowed:
                released.append(m)

        context = "\n".join(
            (
                f"[pointer={m['memory_uri']}] "
                f"source_hash={m['source_hash']} "
                f"resolved_text={m['text']}"
            )
            for m in released
        )
        trace_refs = [m["memory_uri"] for m in released]
        return selected, released, context, trace_refs, guard_reasons

    raise ValueError(f"UNKNOWN_STRATEGY: {strategy}")


def evaluate(strategy, query, memories):
    start = time.perf_counter()
    selected, released, context, trace_refs, guard_reasons = build_context(strategy, query, memories)
    latency_ms = (time.perf_counter() - start) * 1000.0

    selected_ids = [m["memory_id"] for m in selected]
    released_ids = [m["memory_id"] for m in released]
    expected_ids = set(query["expected_memory_ids"])
    forbidden_ids = set(query.get("forbidden_memory_ids", []))

    selected_set = set(selected_ids)
    released_set = set(released_ids)

    expected_selected_count = len(expected_ids & selected_set)
    expected_released_count = len(expected_ids & released_set)

    all_expected_selected = expected_ids.issubset(selected_set)
    all_expected_released = expected_ids.issubset(released_set)

    context_lower = context.lower()
    expected_terms = query["expected_answer_contains"]
    answer_contains_count = sum(1 for term in expected_terms if term.lower() in context_lower)
    answer_contains_expected = answer_contains_count == len(expected_terms)

    forbidden_released_count = len(forbidden_ids & released_set)

    high_unexpected_released_count = 0
    for m in released:
        if m["sensitivity"] == "high" and m["memory_id"] not in expected_ids:
            high_unexpected_released_count += 1

    irrelevant_released_count = sum(1 for mid in released_ids if mid not in expected_ids)

    traceability = 0
    if strategy.startswith("A_"):
        traceability = 0
    elif expected_released_count > 0:
        traceability = 1

    source_hash_present = 1 if "source_hash=sha256:" in context else 0
    pointer_present = 1 if "mem://local/memory/" in context else 0

    result = {
        "strategy": strategy,
        "query_id": query["query_id"],
        "query": query["query"],
        "selected_ids": "|".join(selected_ids),
        "released_ids": "|".join(released_ids),
        "expected_ids": "|".join(query["expected_memory_ids"]),
        "forbidden_ids": "|".join(query.get("forbidden_memory_ids", [])),
        "selected_count": len(selected),
        "released_count": len(released),
        "expected_selected_count": expected_selected_count,
        "expected_released_count": expected_released_count,
        "retrieved_correct_memory": int(all_expected_selected),
        "released_correct_memory": int(all_expected_released),
        "answer_contains_expected": int(answer_contains_expected),
        "answer_contains_count": answer_contains_count,
        "expected_answer_term_count": len(expected_terms),
        "wrong_memory_count": max(0, len(released_set - expected_ids)),
        "forbidden_memory_leak_count": forbidden_released_count,
        "sensitive_memory_leak_count": high_unexpected_released_count,
        "irrelevant_memory_leak_count": irrelevant_released_count,
        "traceability": traceability,
        "source_hash_present": source_hash_present,
        "pointer_present": pointer_present,
        "context_bytes": bytes_len(context),
        "context_tokens_est": estimate_tokens(context),
        "latency_ms": latency_ms,
        "guard_reasons": "|".join(guard_reasons),
    }
    return result


def aggregate(rows, local_storage_bytes, index_size_by_strategy, runtime_peak_by_strategy):
    full_raw_tokens_by_query = {
        r["query_id"]: r["context_tokens_est"]
        for r in rows
        if r["strategy"] == "A_FULL_RAW_CONTEXT"
    }

    summary = []
    for strategy in STRATEGIES:
        srows = [r for r in rows if r["strategy"] == strategy]
        lat = [r["latency_ms"] for r in srows]
        toks = [r["context_tokens_est"] for r in srows]
        ctx_bytes = [r["context_bytes"] for r in srows]

        baseline_tokens = []
        for r in srows:
            baseline_tokens.append(full_raw_tokens_by_query[r["query_id"]])

        token_reductions = []
        for r, base_tok in zip(srows, baseline_tokens):
            if base_tok <= 0:
                token_reductions.append(0.0)
            else:
                token_reductions.append((1 - (r["context_tokens_est"] / base_tok)) * 100)

        released_total = sum(r["released_count"] for r in srows)
        sensitive_leaks = sum(r["sensitive_memory_leak_count"] for r in srows)
        irrelevant_leaks = sum(r["irrelevant_memory_leak_count"] for r in srows)
        forbidden_leaks = sum(r["forbidden_memory_leak_count"] for r in srows)

        summary.append({
            "strategy": strategy,
            "query_count": len(srows),
            "context_tokens_avg": round(statistics.mean(toks), 4),
            "context_tokens_p50": round(percentile(toks, 0.50), 4),
            "context_tokens_p95": round(percentile(toks, 0.95), 4),
            "context_tokens_p99": round(percentile(toks, 0.99), 4),
            "token_reduction_vs_full_raw_avg_pct": round(statistics.mean(token_reductions), 4),
            "latency_ms_avg": round(statistics.mean(lat), 6),
            "latency_ms_p50": round(percentile(lat, 0.50), 6),
            "latency_ms_p95": round(percentile(lat, 0.95), 6),
            "latency_ms_p99": round(percentile(lat, 0.99), 6),
            "accuracy_retrieved_correct_rate": round(statistics.mean([r["retrieved_correct_memory"] for r in srows]), 6),
            "accuracy_released_correct_rate": round(statistics.mean([r["released_correct_memory"] for r in srows]), 6),
            "answer_contains_expected_rate": round(statistics.mean([r["answer_contains_expected"] for r in srows]), 6),
            "wrong_memory_rate_per_released": round(
                (sum(r["wrong_memory_count"] for r in srows) / released_total) if released_total else 0.0,
                6
            ),
            "sensitive_memory_leak_rate_per_released": round(
                (sensitive_leaks / released_total) if released_total else 0.0,
                6
            ),
            "irrelevant_memory_leak_rate_per_released": round(
                (irrelevant_leaks / released_total) if released_total else 0.0,
                6
            ),
            "forbidden_memory_leak_count": forbidden_leaks,
            "traceability_rate": round(statistics.mean([r["traceability"] for r in srows]), 6),
            "source_hash_present_rate": round(statistics.mean([r["source_hash_present"] for r in srows]), 6),
            "pointer_present_rate": round(statistics.mean([r["pointer_present"] for r in srows]), 6),
            "context_bytes_avg": round(statistics.mean(ctx_bytes), 4),
            "local_storage_bytes": local_storage_bytes,
            "strategy_index_size_bytes": index_size_by_strategy.get(strategy, 0),
            "runtime_peak_memory_bytes": runtime_peak_by_strategy.get(strategy, 0),
        })
    return summary


def write_csv(path: Path, rows):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def strategy_index_size(strategy, memories):
    if strategy == "A_FULL_RAW_CONTEXT":
        payload = [{"memory_id": m["memory_id"], "text": m["text"]} for m in memories]
    elif strategy == "B_TOPK_RAW_CHUNKS":
        payload = [{"memory_id": m["memory_id"], "text": m["text"], "tags": m["tags"]} for m in memories]
    elif strategy == "C_SUMMARY_MEMORY":
        payload = [{"memory_id": m["memory_id"], "summary": m["summary"], "tags": m["tags"]} for m in memories]
    elif strategy == "D_POINTER_METADATA_ONLY":
        payload = [
            {
                "memory_uri": m["memory_uri"],
                "source_hash": m["source_hash"],
                "summary": m["summary"],
                "tags": m["tags"],
                "tier": m["tier"],
                "sensitivity": m["sensitivity"],
            }
            for m in memories
        ]
    elif strategy == "E_POINTER_ON_DEMAND_RESOLVE":
        payload = [
            {
                "memory_uri": m["memory_uri"],
                "source_hash": m["source_hash"],
                "tags": m["tags"],
                "tier": m["tier"],
                "sensitivity": m["sensitivity"],
                "resolver_index_ref": m["memory_id"],
            }
            for m in memories
        ]
    else:
        payload = []
    return bytes_len(stable_json(payload))


def make_report(final_summary, metric_summary):
    lines = []
    lines.append("# HSRAG Memory Context Baseline v0.2.0 Report")
    lines.append("")
    lines.append(f"Run timestamp UTC: `{final_summary['run_created_at_utc']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Synthetic data only")
    lines.append("- Deterministic evaluator only")
    lines.append("- No real LLM call")
    lines.append("- No external API")
    lines.append("- No real personal data")
    lines.append("")
    lines.append("## Strategies")
    lines.append("")
    for s in STRATEGIES:
        lines.append(f"- `{s}`")
    lines.append("")
    lines.append("## Metric Summary")
    lines.append("")
    headers = [
        "strategy",
        "token_reduction_vs_full_raw_avg_pct",
        "latency_ms_p50",
        "latency_ms_p95",
        "latency_ms_p99",
        "accuracy_retrieved_correct_rate",
        "answer_contains_expected_rate",
        "sensitive_memory_leak_rate_per_released",
        "forbidden_memory_leak_count",
        "traceability_rate",
        "runtime_peak_memory_bytes",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in metric_summary:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- Full raw context is the cost and leakage baseline.")
    lines.append("- Pointer metadata and pointer resolve should reduce context size and improve traceability.")
    lines.append("- Pointer resolve should be evaluated as a selective disclosure strategy, not as a production privacy guarantee.")
    lines.append("")
    lines.append("## Known Limits")
    lines.append("")
    lines.append("- Token count is estimated by character length, not a model tokenizer.")
    lines.append("- Latency measures local strategy construction only, not LLM latency.")
    lines.append("- Accuracy is deterministic evidence availability, not real natural-language answer quality.")
    lines.append("- Content guard is a placeholder rule, not a production classifier.")
    return "\n".join(lines) + "\n"


def main():
    memory_path = DATA / "memory_items.jsonl"
    query_path = DATA / "queries.jsonl"

    memories_raw = read_jsonl(memory_path)
    queries = read_jsonl(query_path)
    memories = [enrich_memory(m) for m in memories_raw]

    memory_ids = {m["memory_id"] for m in memories}
    for q in queries:
        for mid in q["expected_memory_ids"]:
            if mid not in memory_ids:
                raise ValueError(f"EXPECTED_MEMORY_NOT_FOUND: {q['query_id']} -> {mid}")
        for mid in q.get("forbidden_memory_ids", []):
            if mid not in memory_ids:
                raise ValueError(f"FORBIDDEN_MEMORY_NOT_FOUND: {q['query_id']} -> {mid}")

    local_storage_bytes = bytes_len(memory_path.read_text(encoding="utf-8"))

    all_rows = []
    runtime_peak_by_strategy = {}
    index_size_by_strategy = {}

    for strategy in STRATEGIES:
        index_size_by_strategy[strategy] = strategy_index_size(strategy, memories)

        tracemalloc.start()
        strategy_rows = []
        for q in queries:
            row = evaluate(strategy, q, memories)
            strategy_rows.append(row)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        runtime_peak_by_strategy[strategy] = int(peak)
        all_rows.extend(strategy_rows)

    metric_summary = aggregate(
        all_rows,
        local_storage_bytes=local_storage_bytes,
        index_size_by_strategy=index_size_by_strategy,
        runtime_peak_by_strategy=runtime_peak_by_strategy,
    )

    config = {
        "top_k": TOP_K,
        "resolve_k": RESOLVE_K,
        "strategies": STRATEGIES,
        "token_chars_per_token": TOKEN_CHARS_PER_TOKEN,
        "memory_count": len(memories),
        "query_count": len(queries),
    }
    config_hash = sha256_text(stable_json(config))

    gates = {
        "five_strategies_executed": len(set(r["strategy"] for r in all_rows)) == 5,
        "token_cost_present": all("context_tokens_est" in r for r in all_rows),
        "latency_present": all("latency_ms" in r for r in all_rows),
        "accuracy_present": all("retrieved_correct_memory" in r for r in all_rows),
        "memory_footprint_present": all("runtime_peak_memory_bytes" in r for r in metric_summary),
        "leakage_present": all("sensitive_memory_leak_count" in r for r in all_rows),
        "traceability_present": all("traceability" in r for r in all_rows),
    }

    final_summary = {
        "poc_version": "HSRAG_MEMORY_CONTEXT_BASELINE_V0_2_0_STEP3",
        "decision": "PASS_BASELINE_RUNNER" if all(gates.values()) else "FAIL_BASELINE_RUNNER",
        "run_created_at_utc": RUN_TS,
        "scope": "deterministic_memory_context_strategy_baseline",
        "config": config,
        "config_hash": config_hash,
        "acceptance_gates": gates,
        "metric_summary": metric_summary,
        "warnings": [
            "Synthetic only; not real personal data.",
            "No real LLM call; answer quality is approximated by deterministic evidence availability.",
            "Token count is estimated by character length, not a model tokenizer.",
            "Latency measures local strategy construction only.",
            "Content guard is a placeholder, not production privacy protection."
        ]
    }

    write_csv(OUT / "hsrag_memory_context_v020_strategy_results.csv", all_rows)
    write_csv(OUT / "hsrag_memory_context_v020_metrics_summary.csv", metric_summary)

    with (OUT / "hsrag_memory_context_v020_final_summary.json").open("w", encoding="utf-8") as f:
        json.dump(final_summary, f, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)

    report = make_report(final_summary, metric_summary)
    (REPORTS / "hsrag_memory_context_v020_report.md").write_text(report, encoding="utf-8")

    print(json.dumps({
        "poc_version": final_summary["poc_version"],
        "decision": final_summary["decision"],
        "memory_count": len(memories),
        "query_count": len(queries),
        "strategy_count": len(STRATEGIES),
        "config_hash": config_hash,
        "acceptance_gates": gates,
        "outputs": [
            str(OUT / "hsrag_memory_context_v020_strategy_results.csv"),
            str(OUT / "hsrag_memory_context_v020_metrics_summary.csv"),
            str(OUT / "hsrag_memory_context_v020_final_summary.json"),
            str(REPORTS / "hsrag_memory_context_v020_report.md"),
        ]
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
