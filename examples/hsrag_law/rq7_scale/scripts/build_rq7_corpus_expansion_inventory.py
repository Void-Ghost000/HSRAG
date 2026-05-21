from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_COLUMNS = {"text", "chunk_text", "content", "article_text", "evidence_text", "normalized_text"}
CORPUS_COLUMNS = {"corpus", "corpus_id", "corpus_guess", "source_corpus"}
JURISDICTION_COLUMNS = {"jurisdiction", "region", "legal_jurisdiction"}
RESULT_HINT_COLUMNS = {"mode", "status", "reason_code", "target_correct", "query_class", "case_type"}
METRIC_HINT_COLUMNS = {"p95", "p99", "latency", "esi", "token", "cost", "accuracy"}


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "04_runs", "06_audit"}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_csv_header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = sum(1 for _ in reader)
        return list(reader.fieldnames or []), rows


def iter_csv_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.csv"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def classify_artifact(columns: list[str]) -> dict[str, Any]:
    lower = {column.lower() for column in columns}

    has_text = bool(lower & TEXT_COLUMNS)
    has_corpus = bool(lower & CORPUS_COLUMNS)
    has_jurisdiction = bool(lower & JURISDICTION_COLUMNS)
    has_result_hint = bool(lower & RESULT_HINT_COLUMNS)
    has_metric_hint = any(any(hint in column for hint in METRIC_HINT_COLUMNS) for column in lower)

    if has_text and has_corpus and has_jurisdiction:
        kind = "TEXT_CORPUS_CANDIDATE"
    elif has_result_hint:
        kind = "RESULT_LOG"
    elif has_metric_hint:
        kind = "METRICS_OR_SUMMARY"
    elif has_text:
        kind = "TEXT_BUT_INCOMPLETE_METADATA"
    else:
        kind = "NON_CORPUS_ARTIFACT"

    return {
        "kind": kind,
        "has_text": has_text,
        "has_corpus": has_corpus,
        "has_jurisdiction": has_jurisdiction,
        "has_result_hint": has_result_hint,
        "has_metric_hint": has_metric_hint,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="examples/hsrag_law")
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    root = Path(args.root)
    output_dir = Path(args.output_dir)

    if not root.exists():
        raise SystemExit(f"ROOT_NOT_FOUND:{root}")

    scanned_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    artifacts = []
    kind_counter: Counter[str] = Counter()

    for csv_path in iter_csv_files(root):
        try:
            columns, row_count = read_csv_header_and_count(csv_path)
            classification = classify_artifact(columns)
            kind_counter[classification["kind"]] += 1

            artifacts.append(
                {
                    "path": str(csv_path.as_posix()),
                    "filename": csv_path.name,
                    "row_count": row_count,
                    "sha256": sha256_bytes(csv_path.read_bytes()),
                    "columns": columns,
                    "classification": classification,
                }
            )
        except Exception as exc:
            kind_counter["READ_ERROR"] += 1
            artifacts.append(
                {
                    "path": str(csv_path.as_posix()),
                    "filename": csv_path.name,
                    "row_count": None,
                    "sha256": None,
                    "columns": [],
                    "classification": {
                        "kind": "READ_ERROR",
                        "error": f"{type(exc).__name__}:{exc}",
                    },
                }
            )

    text_candidates = [
        item for item in artifacts
        if item["classification"]["kind"] == "TEXT_CORPUS_CANDIDATE"
    ]

    summary = {
        "schema": "HSRAG_RQ7_CORPUS_EXPANSION_INVENTORY_V0_1",
        "status": "OK",
        "scanned_at_utc": scanned_at_utc,
        "root": str(root.as_posix()),
        "artifact_count": len(artifacts),
        "kind_summary": dict(kind_counter),
        "text_corpus_candidate_count": len(text_candidates),
        "text_corpus_candidates": text_candidates,
        "artifacts": artifacts,
        "claim_boundary": {
            "inventory_only": True,
            "does_not_expand_corpus": True,
            "does_not_run_benchmark": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "RQ7_CORPUS_EXPANSION_INVENTORY.json"
    output_md = output_dir / "RQ7_CORPUS_EXPANSION_INVENTORY.md"

    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RQ7 Corpus Expansion Inventory",
        "",
        f"- status: {summary['status']}",
        f"- scanned_at_utc: {scanned_at_utc}",
        f"- artifact_count: {summary['artifact_count']}",
        f"- text_corpus_candidate_count: {summary['text_corpus_candidate_count']}",
        "",
        "## Kind Summary",
        "",
    ]

    for kind, count in sorted(kind_counter.items()):
        lines.append(f"- {kind}: {count}")

    lines.extend(["", "## Text Corpus Candidates", ""])

    for item in text_candidates:
        lines.append(f"- `{item['path']}` rows={item['row_count']}")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- inventory_only: true",
            "- does_not_expand_corpus: true",
            "- does_not_run_benchmark: true",
            "- full_scale_benchmark: false",
            "- vector_hybrid_baselines: false",
            "- legal_advice: false",
            "",
        ]
    )

    output_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
