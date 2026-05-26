from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

POC_VERSION = "HSRAG_MEMORY_CONTEXT_SCALE_BASELINE_V0_2_1_DATASET"
BASE = Path("examples/hsrag_memory_context_v021_scale")
DATA = BASE / "data"
OUT = BASE / "outputs"

N_LIST = [1000, 10000, 50000, 100000]
QUERY_COUNT_PER_N = 100

TIERS = ["FHS", "CHS", "EHS"]
SENSITIVITIES = ["high", "medium", "low"]

TOPICS = [
    {
        "topic": "project_storage",
        "tags": ["project", "sqlite", "architecture"],
        "answer_terms": ["SQLite", "local storage"],
        "query_template": "What storage layer does Project Atlas use for the memory pointer resolver demo?",
        "text_template": "Project Atlas uses SQLite as its local storage layer for the memory pointer resolver demo. Record {i}.",
        "summary_template": "Project Atlas uses SQLite for local resolver storage. Record {i}."
    },
    {
        "topic": "coding_preference",
        "tags": ["coding", "preference", "python", "typescript"],
        "answer_terms": ["Python", "TypeScript"],
        "query_template": "Which languages does Alice prefer for backend prototypes and UI work?",
        "text_template": "Alice prefers Python for backend prototypes and TypeScript for user interface work. Record {i}.",
        "summary_template": "Alice prefers Python for backend prototypes and TypeScript for UI. Record {i}."
    },
    {
        "topic": "cafe_work",
        "tags": ["cafe", "work", "preference"],
        "answer_terms": ["quiet", "power outlets"],
        "query_template": "What cafe environment is preferred for focused work?",
        "text_template": "The user wants quiet cafes with power outlets when doing focused work outside. Record {i}.",
        "summary_template": "The user prefers quiet cafes with power outlets for focused work. Record {i}."
    },
    {
        "topic": "memory_pointer",
        "tags": ["memory", "pointer", "hash", "resolver"],
        "answer_terms": ["hash pointer", "on-demand resolve"],
        "query_template": "How does the memory pointer strategy reduce context exposure?",
        "text_template": "The memory pointer strategy uses hash pointers and on-demand resolve to avoid sending all raw memories into context. Record {i}.",
        "summary_template": "Hash pointer with on-demand resolve reduces raw context exposure. Record {i}."
    },
    {
        "topic": "audit_chain",
        "tags": ["audit", "hash-chain", "traceability"],
        "answer_terms": ["audit chain", "traceability"],
        "query_template": "How are memory-context decisions traced?",
        "text_template": "Memory-context decisions are traced with an audit chain and pointer-level source references. Record {i}.",
        "summary_template": "Audit chain and pointer references provide traceability. Record {i}."
    },
    {
        "topic": "quiet_schedule",
        "tags": ["schedule", "deep-work", "routine"],
        "answer_terms": ["deep work", "morning"],
        "query_template": "When is deep work preferred?",
        "text_template": "The user prefers morning deep work blocks for difficult architecture tasks. Record {i}.",
        "summary_template": "Morning deep work is preferred for difficult architecture work. Record {i}."
    },
    {
        "topic": "food_preference",
        "tags": ["food", "preference", "light-meal"],
        "answer_terms": ["light meal", "tea"],
        "query_template": "What light meal pattern is preferred during long work sessions?",
        "text_template": "During long work sessions, the user prefers a light meal with tea instead of heavy food. Record {i}.",
        "summary_template": "The user prefers light meals and tea during long work sessions. Record {i}."
    },
    {
        "topic": "security_boundary",
        "tags": ["security", "boundary", "token"],
        "answer_terms": ["token", "boundary"],
        "query_template": "What should happen to password or token-like memory?",
        "text_template": "Password-like and token-like memory should be treated as high sensitivity and blocked from raw context release. Record {i}.",
        "summary_template": "Token-like memory should be blocked from raw context release. Record {i}."
    }
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


RUN_CREATED_AT_UTC = utc_now()


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tier_for(i: int, topic: str) -> str:
    if topic == "security_boundary":
        return "FHS"
    if i % 10 == 0:
        return "FHS"
    if i % 3 == 0:
        return "EHS"
    return "CHS"


def sensitivity_for(tier: str, topic: str, i: int) -> str:
    if tier == "FHS" or topic == "security_boundary":
        return "high"
    if i % 7 == 0:
        return "medium"
    return "low"


def make_memory_uri(n: int, memory_id: str, topic: str) -> str:
    digest = sha256_hex(f"{n}|{memory_id}|{topic}")[:16]
    return f"mem://local/v021/n{n}/{topic}/{memory_id}?h={digest}"


def make_memory_item(n: int, i: int) -> Dict[str, Any]:
    topic_info = TOPICS[i % len(TOPICS)]
    topic = topic_info["topic"]
    tier = tier_for(i, topic)
    sensitivity = sensitivity_for(tier, topic, i)

    memory_id = f"n{n}_m{i:06d}"
    text = topic_info["text_template"].format(i=i)
    summary = topic_info["summary_template"].format(i=i)
    memory_uri = make_memory_uri(n, memory_id, topic)

    return {
        "memory_id": memory_id,
        "memory_uri": memory_uri,
        "topic": topic,
        "tier": tier,
        "sensitivity": sensitivity,
        "source_type": "synthetic_memory",
        "tags": topic_info["tags"],
        "summary": summary,
        "text": text,
        "source_hash": "sha256:" + sha256_hex(text),
        "created_at_utc": RUN_CREATED_AT_UTC
    }


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def make_queries_for_n(n: int, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_topic: Dict[str, List[Dict[str, Any]]] = {}

    for item in memories:
        by_topic.setdefault(item["topic"], []).append(item)

    queries: List[Dict[str, Any]] = []
    q_index = 0

    for topic_info in TOPICS:
        topic = topic_info["topic"]
        candidates = by_topic.get(topic, [])
        releasable = [
            item for item in candidates
            if item["tier"] != "FHS" and item["sensitivity"] != "high"
        ]

        high_or_fhs = [
            item for item in candidates
            if item["tier"] == "FHS" or item["sensitivity"] == "high"
        ]

        if not releasable:
            continue

        repeat = max(1, QUERY_COUNT_PER_N // len(TOPICS))

        for r in range(repeat):
            expected = releasable[(r * 17) % len(releasable)]
            forbidden = [item["memory_id"] for item in high_or_fhs[:5]]

            queries.append({
                "query_id": f"n{n}_q{q_index:04d}",
                "n_memories": n,
                "topic": topic,
                "query": topic_info["query_template"],
                "expected_memory_ids": [expected["memory_id"]],
                "expected_answer_contains": topic_info["answer_terms"],
                "forbidden_memory_ids": forbidden,
                "expected_memory_uri_prefix": expected["memory_uri"].split("?")[0]
            })

            q_index += 1

    while len(queries) < QUERY_COUNT_PER_N:
        topic_info = TOPICS[len(queries) % len(TOPICS)]
        topic = topic_info["topic"]
        candidates = [
            item for item in by_topic.get(topic, [])
            if item["tier"] != "FHS" and item["sensitivity"] != "high"
        ]

        if not candidates:
            break

        expected = candidates[(len(queries) * 19) % len(candidates)]
        queries.append({
            "query_id": f"n{n}_q{q_index:04d}",
            "n_memories": n,
            "topic": topic,
            "query": topic_info["query_template"],
            "expected_memory_ids": [expected["memory_id"]],
            "expected_answer_contains": topic_info["answer_terms"],
            "forbidden_memory_ids": [],
            "expected_memory_uri_prefix": expected["memory_uri"].split("?")[0]
        })
        q_index += 1

    # V021_QUERY_FILL_FALLBACK_PATCH
    fill_cursor = 0
    fill_attempts = 0
    max_fill_attempts = QUERY_COUNT_PER_N * len(TOPICS) * 8
    while len(queries) < QUERY_COUNT_PER_N and fill_attempts < max_fill_attempts:
        topic_info = TOPICS[fill_cursor % len(TOPICS)]
        fill_cursor += 1
        fill_attempts += 1
        topic = topic_info["topic"]
        candidates = [
            item for item in by_topic.get(topic, [])
            if item["tier"] != "FHS" and item["sensitivity"] != "high"
        ]
        if not candidates:
            continue
        expected = candidates[(len(queries) * 19) % len(candidates)]
        high_or_fhs = [
            item for item in by_topic.get(topic, [])
            if item["tier"] == "FHS" or item["sensitivity"] == "high"
        ]
        queries.append({
            "query_id": f"n{n}_q{q_index:04d}",
            "n_memories": n,
            "topic": topic,
            "query": topic_info["query_template"],
            "expected_memory_ids": [expected["memory_id"]],
            "expected_answer_contains": topic_info["answer_terms"],
            "forbidden_memory_ids": [item["memory_id"] for item in high_or_fhs[:5]],
            "expected_memory_uri_prefix": expected["memory_uri"].split("?")[0]
        })
        q_index += 1

    return queries[:QUERY_COUNT_PER_N]


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    dataset_summaries = []
    all_queries = []

    print("== V0.2.1 Scale Dataset Generator ==")

    for n in N_LIST:
        print(f"[dataset] generating n={n} ...")

        memories = [make_memory_item(n, i) for i in range(n)]
        queries = make_queries_for_n(n, memories)

        memory_path = DATA / f"memory_items_{n}.jsonl"
        query_path = DATA / f"queries_{n}.jsonl"

        write_jsonl(memory_path, memories)
        write_jsonl(query_path, queries)

        all_queries.extend(queries)

        tier_counts: Dict[str, int] = {}
        sensitivity_counts: Dict[str, int] = {}
        topic_counts: Dict[str, int] = {}

        for item in memories:
            tier_counts[item["tier"]] = tier_counts.get(item["tier"], 0) + 1
            sensitivity_counts[item["sensitivity"]] = sensitivity_counts.get(item["sensitivity"], 0) + 1
            topic_counts[item["topic"]] = topic_counts.get(item["topic"], 0) + 1

        dataset_summaries.append({
            "n_memories": n,
            "memory_file": str(memory_path),
            "query_file": str(query_path),
            "memory_count": len(memories),
            "query_count": len(queries),
            "tier_counts": tier_counts,
            "sensitivity_counts": sensitivity_counts,
            "topic_counts": topic_counts,
            "memory_file_bytes": memory_path.stat().st_size,
            "query_file_bytes": query_path.stat().st_size
        })

    write_jsonl(DATA / "queries_all.jsonl", all_queries)

    final_summary = {
        "poc_version": POC_VERSION,
        "decision": "PASS_SCALE_DATASET_GENERATED",
        "scope": "synthetic_scale_dataset_generation_only",
        "run_created_at_utc": RUN_CREATED_AT_UTC,
        "n_list": N_LIST,
        "query_count_per_n": QUERY_COUNT_PER_N,
        "total_query_count": len(all_queries),
        "datasets": dataset_summaries,
        "acceptance_gates": {
            "all_memory_files_created": all((DATA / f"memory_items_{n}.jsonl").exists() for n in N_LIST),
            "all_query_files_created": all((DATA / f"queries_{n}.jsonl").exists() for n in N_LIST),
            "queries_all_created": (DATA / "queries_all.jsonl").exists(),
            "max_n_is_100000": max(N_LIST) == 100000,
            "query_count_per_n_ok": all(row["query_count"] == QUERY_COUNT_PER_N for row in dataset_summaries),
            "tiers_present": all(len(row["tier_counts"]) == 3 for row in dataset_summaries),
            "sensitivities_present": all(len(row["sensitivity_counts"]) == 3 for row in dataset_summaries)
        },
        "warnings": [
            "Synthetic only.",
            "No benchmark executed yet.",
            "No real LLM call.",
            "No real personal data.",
            "Token, latency, accuracy, leakage metrics will be produced in Step 9."
        ]
    }

    if not all(final_summary["acceptance_gates"].values()):
        final_summary["decision"] = "REVIEW_SCALE_DATASET_GENERATION"

    write_json(OUT / "v021_dataset_summary.json", final_summary)

    print(json.dumps(final_summary, ensure_ascii=False, indent=2, sort_keys=True))

    if final_summary["decision"] != "PASS_SCALE_DATASET_GENERATED":
        raise SystemExit("Dataset generation did not pass all gates.")


if __name__ == "__main__":
    main()
