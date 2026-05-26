import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("examples/hsrag_memory_context_v020")
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)

RUN_TS = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

memories = [
    {
        "memory_id": "m001",
        "text": "Project Atlas uses SQLite as its local storage layer for the memory pointer resolver demo.",
        "summary": "Project Atlas uses SQLite for local resolver storage.",
        "tags": ["project", "sqlite", "architecture"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "project_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m002",
        "text": "Alice prefers Python for backend prototypes and TypeScript for user interface work.",
        "summary": "Alice prefers Python for backend prototypes and TypeScript for UI.",
        "tags": ["coding", "preference", "python", "typescript"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "preference_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m003",
        "text": "The user wants quiet cafes with power outlets when doing focused work outside.",
        "summary": "The user prefers quiet cafes with power outlets for focused work.",
        "tags": ["cafe", "work", "preference"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "preference_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m004",
        "text": "The demo should not expose high-sensitivity memories to the language model unless the release guard explicitly allows it.",
        "summary": "High-sensitivity memories require explicit release guard approval.",
        "tags": ["security", "guard", "privacy"],
        "tier": "FHS",
        "sensitivity": "high",
        "source_type": "security_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m005",
        "text": "The memory pointer system should preserve tombstones after deletion so stale pointers cannot resurrect deleted memories.",
        "summary": "Tombstones prevent stale pointers from resurrecting deleted memories.",
        "tags": ["tombstone", "revocation", "lifecycle"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "architecture_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m006",
        "text": "For travel booking, the user prefers quiet rooms, free cancellation, and locations near public transit.",
        "summary": "Travel booking preference: quiet rooms, free cancellation, near transit.",
        "tags": ["travel", "hotel", "preference"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "preference_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m007",
        "text": "A fake password example appears here only for testing: demo_password_123 should never be released to an LLM.",
        "summary": "Contains a fake password-like string used for testing release blocking.",
        "tags": ["security", "password", "test_secret"],
        "tier": "FHS",
        "sensitivity": "high",
        "source_type": "synthetic_secret_test",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m008",
        "text": "The agent shadow window should show which memory pointers were resolved, released, blocked, revoked, or tombstoned.",
        "summary": "Agent shadow window shows resolved, released, blocked, revoked, or tombstoned pointers.",
        "tags": ["agent", "shadow_window", "audit"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "product_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m009",
        "text": "The benchmark should compare full raw context, top-k raw chunks, summary memory, pointer metadata only, and pointer on-demand resolve.",
        "summary": "Benchmark compares five memory context injection strategies.",
        "tags": ["benchmark", "baseline", "context"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "benchmark_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m010",
        "text": "The v0.2.0 benchmark must report token cost, latency p50 p95 p99, accuracy, memory footprint, leakage, and traceability.",
        "summary": "v0.2.0 reports token cost, latency percentiles, accuracy, memory, leakage, and traceability.",
        "tags": ["metrics", "benchmark", "latency"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "benchmark_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m011",
        "text": "EHS memories are low-priority scratch notes and should not override CHS or FHS records.",
        "summary": "EHS scratch notes must not override CHS or FHS records.",
        "tags": ["ehs", "tier", "scratch"],
        "tier": "EHS",
        "sensitivity": "low",
        "source_type": "scratch_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m012",
        "text": "The release policy should block cross-purpose reuse, such as using recommendation-only memory for training export.",
        "summary": "Release policy blocks cross-purpose reuse such as training export.",
        "tags": ["purpose_boundary", "training_export", "policy"],
        "tier": "FHS",
        "sensitivity": "high",
        "source_type": "policy_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m013",
        "text": "For food recommendations, Alice prefers noodles, light soups, and low-noise restaurants.",
        "summary": "Alice prefers noodles, light soups, and quiet restaurants.",
        "tags": ["food", "preference", "restaurant"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "preference_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m014",
        "text": "The local resolver must return structured reason codes instead of silent failures.",
        "summary": "Resolver must return structured reason codes.",
        "tags": ["resolver", "reason_code", "reliability"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "architecture_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m015",
        "text": "A deleted memory should leave a tombstone record containing the old pointer hash and deletion event hash.",
        "summary": "Deleted memory leaves tombstone with old pointer hash and deletion event hash.",
        "tags": ["delete", "tombstone", "audit"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "architecture_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m016",
        "text": "The benchmark should avoid real personal data and use synthetic records only.",
        "summary": "Benchmark uses synthetic data only.",
        "tags": ["synthetic", "privacy", "benchmark"],
        "tier": "FHS",
        "sensitivity": "high",
        "source_type": "safety_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m017",
        "text": "Pointer metadata can include memory_uri, source_hash, tags, tier, sensitivity, and short summary.",
        "summary": "Pointer metadata includes URI, source hash, tags, tier, sensitivity, and summary.",
        "tags": ["pointer", "metadata", "source_hash"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "architecture_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m018",
        "text": "The answer should cite memory_id or memory_uri when traceability is available.",
        "summary": "Answers should cite memory_id or memory_uri when traceability is available.",
        "tags": ["traceability", "citation", "memory_uri"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "benchmark_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m019",
        "text": "Top-k raw chunk retrieval can reduce token cost but may still leak irrelevant or sensitive memories.",
        "summary": "Top-k raw retrieval saves tokens but may leak irrelevant or sensitive memories.",
        "tags": ["topk", "raw_context", "leakage"],
        "tier": "CHS",
        "sensitivity": "medium",
        "source_type": "benchmark_note",
        "created_at_utc": RUN_TS
    },
    {
        "memory_id": "m020",
        "text": "Summary memory saves tokens but can lose details and weaken source traceability.",
        "summary": "Summary memory saves tokens but weakens detail and source traceability.",
        "tags": ["summary", "traceability", "compression"],
        "tier": "CHS",
        "sensitivity": "low",
        "source_type": "benchmark_note",
        "created_at_utc": RUN_TS
    }
]

queries = [
    {
        "query_id": "q001",
        "query": "What storage layer does Project Atlas use for the memory pointer resolver demo?",
        "expected_memory_ids": ["m001"],
        "expected_answer_contains": ["SQLite", "local storage"],
        "forbidden_memory_ids": ["m007", "m012", "m016"]
    },
    {
        "query_id": "q002",
        "query": "Which languages does Alice prefer for backend prototypes and UI work?",
        "expected_memory_ids": ["m002"],
        "expected_answer_contains": ["Python", "TypeScript"],
        "forbidden_memory_ids": ["m007", "m012", "m016"]
    },
    {
        "query_id": "q003",
        "query": "What cafe environment is preferred for focused work?",
        "expected_memory_ids": ["m003"],
        "expected_answer_contains": ["quiet", "power outlets"],
        "forbidden_memory_ids": ["m007", "m012", "m016"]
    },
    {
        "query_id": "q004",
        "query": "Why are tombstones needed in the memory pointer lifecycle?",
        "expected_memory_ids": ["m005", "m015"],
        "expected_answer_contains": ["stale pointers", "deleted memories", "tombstone"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q005",
        "query": "What should the agent shadow window display?",
        "expected_memory_ids": ["m008"],
        "expected_answer_contains": ["resolved", "released", "blocked", "revoked", "tombstoned"],
        "forbidden_memory_ids": ["m007", "m012", "m016"]
    },
    {
        "query_id": "q006",
        "query": "What five context strategies should the benchmark compare?",
        "expected_memory_ids": ["m009"],
        "expected_answer_contains": ["full raw", "top-k", "summary", "pointer metadata", "on-demand resolve"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q007",
        "query": "Which metrics must v0.2.0 report?",
        "expected_memory_ids": ["m010"],
        "expected_answer_contains": ["token cost", "latency", "accuracy", "memory", "leakage", "traceability"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q008",
        "query": "What should happen if recommendation-only memory is reused for training export?",
        "expected_memory_ids": ["m012"],
        "expected_answer_contains": ["cross-purpose", "training export", "block"],
        "forbidden_memory_ids": ["m007"]
    },
    {
        "query_id": "q009",
        "query": "What should the resolver return instead of silent failure?",
        "expected_memory_ids": ["m014"],
        "expected_answer_contains": ["structured reason codes"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q010",
        "query": "What metadata can a pointer carry?",
        "expected_memory_ids": ["m017"],
        "expected_answer_contains": ["memory_uri", "source_hash", "tags", "tier", "sensitivity"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q011",
        "query": "What weakness does summary memory have?",
        "expected_memory_ids": ["m020"],
        "expected_answer_contains": ["lose details", "traceability"],
        "forbidden_memory_ids": ["m007", "m012"]
    },
    {
        "query_id": "q012",
        "query": "What risk remains in top-k raw chunk retrieval?",
        "expected_memory_ids": ["m019"],
        "expected_answer_contains": ["leak", "irrelevant", "sensitive"],
        "forbidden_memory_ids": ["m007", "m012"]
    }
]

def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

write_jsonl(DATA / "memory_items.jsonl", memories)
write_jsonl(DATA / "queries.jsonl", queries)

# Basic deterministic validation
memory_ids = {m["memory_id"] for m in memories}
errors = []

for q in queries:
    for mid in q["expected_memory_ids"]:
        if mid not in memory_ids:
            errors.append(f"{q['query_id']} expected_memory_id not found: {mid}")
    for mid in q.get("forbidden_memory_ids", []):
        if mid not in memory_ids:
            errors.append(f"{q['query_id']} forbidden_memory_id not found: {mid}")

if errors:
    raise SystemExit("\n".join(errors))

summary = {
    "poc_version": "HSRAG_MEMORY_CONTEXT_BASELINE_V0_2_0_DATASET_STEP2",
    "run_created_at_utc": RUN_TS,
    "memory_count": len(memories),
    "query_count": len(queries),
    "tiers": sorted(set(m["tier"] for m in memories)),
    "sensitivities": sorted(set(m["sensitivity"] for m in memories)),
    "validation": "PASS"
}

with (DATA / "dataset_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2, sort_keys=True)

print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
