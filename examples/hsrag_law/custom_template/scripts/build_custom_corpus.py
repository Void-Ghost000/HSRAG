from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


BASE = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE / "input"
TEXT_DIR = INPUT_DIR / "legal_texts"
OUTPUT_DIR = BASE / "output"

DEFAULT_MANIFEST = INPUT_DIR / "manifest.example.json"
DEFAULT_SALT = "HSRAG_LAW_CUSTOM_TEMPLATE_PUBLIC_SALT_v1"

REQUIRED_MANIFEST_FIELDS = [
    "corpus_id",
    "title",
    "jurisdiction",
    "source_type",
    "language",
    "license_note",
    "cthc_domain",
    "cthc_topic",
    "text_files",
]


@dataclass
class GateCheck:
    check: str
    passed: bool
    detail: str


@dataclass
class ChunkRecord:
    chunk_id: str
    chunk_index: int
    corpus_id: str
    title: str
    jurisdiction: str
    source_type: str
    language: str
    source_url: str
    version: str
    cthc_address: str
    domain_hash: str
    chunk_hash: str
    char_len: int
    token_estimate: int
    text: str


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload_hash: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def estimate_tokens(text: str) -> int:
    # Lightweight estimate; avoids tokenizer dependency.
    return max(1, int(len(text) / 4))


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: Dict[str, Any]) -> List[GateCheck]:
    checks: List[GateCheck] = []

    for field in REQUIRED_MANIFEST_FIELDS:
        value = manifest.get(field)
        passed = value is not None and value != "" and value != []
        checks.append(
            GateCheck(
                check=f"manifest_has_{field}",
                passed=passed,
                detail=f"{field}={value!r}",
            )
        )

    text_files = manifest.get("text_files", [])
    checks.append(
        GateCheck(
            check="manifest_text_files_is_list",
            passed=isinstance(text_files, list),
            detail=f"type={type(text_files).__name__}",
        )
    )

    license_note = str(manifest.get("license_note", "")).strip()
    checks.append(
        GateCheck(
            check="license_note_present",
            passed=len(license_note) >= 10,
            detail="license_note should state that the user has the right to process the text locally.",
        )
    )

    return checks


def make_domain_hash(manifest: Dict[str, Any], salt: str) -> str:
    parts = [
        salt,
        str(manifest.get("cthc_domain", "")),
        str(manifest.get("source_type", "")),
        str(manifest.get("jurisdiction", "")),
        str(manifest.get("corpus_id", "")),
    ]
    return sha256_text("||".join(parts))


def build_cthc_base(manifest: Dict[str, Any]) -> str:
    parts = [
        str(manifest.get("cthc_domain", "LEGAL")).upper(),
        str(manifest.get("source_type", "PUBLIC_LEGAL_TEXT")).upper(),
        str(manifest.get("jurisdiction", "CUSTOM")).upper(),
        str(manifest.get("corpus_id", "CUSTOM_LAW")).upper(),
        str(manifest.get("cthc_topic", "GENERAL")).upper(),
    ]
    cleaned = []
    for part in parts:
        part = re.sub(r"[^A-Z0-9_]+", "_", part).strip("_")
        cleaned.append(part or "UNKNOWN")
    return ".".join(cleaned)


def split_into_chunks(text: str, max_chars: int = 1200, overlap: int = 120) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    # First try semantic-ish paragraph grouping.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for paragraph in paragraphs:
        p_len = len(paragraph)

        if p_len > max_chars:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_len = 0

            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + max_chars)
                chunks.append(paragraph[start:end].strip())
                if end >= len(paragraph):
                    break
                start = max(0, end - overlap)
            continue

        if current and current_len + p_len + 2 > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_len = p_len
        else:
            current.append(paragraph)
            current_len += p_len + 2

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def read_text_files(manifest: Dict[str, Any]) -> tuple[str, List[GateCheck], List[Dict[str, Any]]]:
    checks: List[GateCheck] = []
    source_records: List[Dict[str, Any]] = []
    all_text_parts: List[str] = []

    text_files = manifest.get("text_files", [])
    if not isinstance(text_files, list):
        return "", [GateCheck("text_files_invalid", False, "text_files must be a list.")], []

    for filename in text_files:
        path = TEXT_DIR / str(filename)
        exists = path.exists()
        checks.append(
            GateCheck(
                check=f"text_file_exists::{filename}",
                passed=exists,
                detail=str(path),
            )
        )

        if not exists:
            continue

        raw = path.read_text(encoding="utf-8", errors="replace")
        normalized = normalize_text(raw)

        source_records.append(
            {
                "filename": str(filename),
                "path": str(path),
                "char_len_raw": len(raw),
                "char_len_normalized": len(normalized),
                "file_hash": sha256_text(normalized),
            }
        )

        all_text_parts.append(normalized)

    combined = "\n\n".join(all_text_parts).strip()

    checks.append(
        GateCheck(
            check="combined_text_non_empty",
            passed=len(combined) > 0,
            detail=f"combined_char_len={len(combined)}",
        )
    )

    return combined, checks, source_records


def build_chunk_records(
    manifest: Dict[str, Any],
    chunks: Sequence[str],
    domain_hash: str,
) -> List[ChunkRecord]:
    cthc_base = build_cthc_base(manifest)

    corpus_id = str(manifest.get("corpus_id", "CUSTOM_LAW_001"))
    title = str(manifest.get("title", "Custom Legal Corpus"))
    jurisdiction = str(manifest.get("jurisdiction", "CUSTOM"))
    source_type = str(manifest.get("source_type", "PUBLIC_LEGAL_TEXT"))
    language = str(manifest.get("language", "en"))
    source_url = str(manifest.get("source_url", ""))
    version = str(manifest.get("version", ""))

    records: List[ChunkRecord] = []

    for idx, chunk in enumerate(chunks, start=1):
        cthc_address = f"{cthc_base}.CHUNK_{idx:04d}"
        chunk_hash = sha256_text("||".join([domain_hash, cthc_address, chunk]))
        chunk_id = f"{corpus_id}::CHUNK_{idx:04d}"

        records.append(
            ChunkRecord(
                chunk_id=chunk_id,
                chunk_index=idx,
                corpus_id=corpus_id,
                title=title,
                jurisdiction=jurisdiction,
                source_type=source_type,
                language=language,
                source_url=source_url,
                version=version,
                cthc_address=cthc_address,
                domain_hash=domain_hash,
                chunk_hash=chunk_hash,
                char_len=len(chunk),
                token_estimate=estimate_tokens(chunk),
                text=chunk,
            )
        )

    return records


def build_audit_chain(events_payloads: Sequence[tuple[str, Dict[str, Any]]]) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous = "GENESIS"

    for index, (event_type, payload) in enumerate(events_payloads):
        payload_hash = stable_json_hash(payload)
        event_seed = {
            "index": index,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "previous_hash": previous,
        }
        event_hash = stable_json_hash(event_seed)

        event = AuditEvent(
            index=index,
            event_type=event_type,
            payload_hash=payload_hash,
            payload=payload,
            previous_hash=previous,
            event_hash=event_hash,
        )
        events.append(event)
        previous = event_hash

    return events


def verify_audit_chain(events: Sequence[AuditEvent]) -> bool:
    previous = "GENESIS"

    for event in events:
        if event.previous_hash != previous:
            return False

        payload_hash = stable_json_hash(event.payload)
        if payload_hash != event.payload_hash:
            return False

        event_seed = {
            "index": event.index,
            "event_type": event.event_type,
            "payload_hash": event.payload_hash,
            "previous_hash": event.previous_hash,
        }

        if stable_json_hash(event_seed) != event.event_hash:
            return False

        previous = event.event_hash

    return True


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(
    manifest: Dict[str, Any],
    source_records: List[Dict[str, Any]],
    gate_checks: List[GateCheck],
    chunk_records: List[ChunkRecord],
    domain_hash: str,
    salt: str,
) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    manifest_hash = stable_json_hash(manifest)

    audit_events = build_audit_chain(
        [
            (
                "CUSTOM_MANIFEST",
                {
                    "manifest": manifest,
                    "manifest_hash": manifest_hash,
                },
            ),
            (
                "SOURCE_FILES",
                {
                    "source_records": source_records,
                },
            ),
            (
                "DOMAIN_HASH",
                {
                    "salt": salt,
                    "domain_hash": domain_hash,
                    "cthc_base": build_cthc_base(manifest),
                },
            ),
            (
                "CHUNK_BUILD",
                {
                    "chunk_count": len(chunk_records),
                    "chunk_hashes": [record.chunk_hash for record in chunk_records],
                },
            ),
        ]
    )

    audit_ok = verify_audit_chain(audit_events)

    gate_rows = [asdict(check) for check in gate_checks]
    chunk_rows = [asdict(record) for record in chunk_records]
    source_rows = source_records

    summary = {
        "name": "HSRAG_LAW_CUSTOM_CORPUS_BUILD",
        "decision": "CUSTOM_CORPUS_BUILD_PASS"
        if all(check.passed for check in gate_checks) and len(chunk_records) > 0 and audit_ok
        else "CUSTOM_CORPUS_BUILD_FAIL",
        "generated_at_utc": now,
        "manifest_path": str(DEFAULT_MANIFEST),
        "manifest_hash": manifest_hash,
        "domain_hash": domain_hash,
        "cthc_base": build_cthc_base(manifest),
        "source_file_count": len(source_records),
        "chunk_count": len(chunk_records),
        "total_chars": sum(record.char_len for record in chunk_records),
        "total_token_estimate": sum(record.token_estimate for record in chunk_records),
        "gate_passed": all(check.passed for check in gate_checks),
        "audit_chain_complete": 1.0 if audit_ok else 0.0,
        "outputs": {
            "custom_manifest": "custom_manifest.json",
            "custom_source_records": "custom_source_records.csv",
            "custom_chunks": "custom_chunks.csv",
            "custom_gate_checks": "custom_gate_checks.csv",
            "custom_audit_chain": "custom_audit_chain.jsonl",
            "custom_build_summary": "custom_build_summary.json",
            "custom_build_summary_md": "custom_build_summary.md",
        },
    }

    custom_manifest = dict(manifest)
    custom_manifest["_hsrag_build"] = {
        "generated_at_utc": now,
        "manifest_hash": manifest_hash,
        "domain_hash": domain_hash,
        "cthc_base": build_cthc_base(manifest),
        "chunk_count": len(chunk_records),
        "audit_chain_complete": 1.0 if audit_ok else 0.0,
    }

    (OUTPUT_DIR / "custom_manifest.json").write_text(
        json.dumps(custom_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_csv(
        OUTPUT_DIR / "custom_source_records.csv",
        source_rows,
        ["filename", "path", "char_len_raw", "char_len_normalized", "file_hash"],
    )

    write_csv(
        OUTPUT_DIR / "custom_chunks.csv",
        chunk_rows,
        [
            "chunk_id",
            "chunk_index",
            "corpus_id",
            "title",
            "jurisdiction",
            "source_type",
            "language",
            "source_url",
            "version",
            "cthc_address",
            "domain_hash",
            "chunk_hash",
            "char_len",
            "token_estimate",
            "text",
        ],
    )

    write_csv(
        OUTPUT_DIR / "custom_gate_checks.csv",
        gate_rows,
        ["check", "passed", "detail"],
    )

    with (OUTPUT_DIR / "custom_audit_chain.jsonl").open("w", encoding="utf-8") as f:
        for event in audit_events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")

    (OUTPUT_DIR / "custom_build_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = [
        "# HSRAG LAW Custom Corpus Build Summary",
        "",
        f"Decision: `{summary['decision']}`",
        f"Generated at UTC: `{now}`",
        "",
        "## Metrics",
        "",
        f"- source_file_count: `{summary['source_file_count']}`",
        f"- chunk_count: `{summary['chunk_count']}`",
        f"- total_chars: `{summary['total_chars']}`",
        f"- total_token_estimate: `{summary['total_token_estimate']}`",
        f"- gate_passed: `{summary['gate_passed']}`",
        f"- audit_chain_complete: `{summary['audit_chain_complete']}`",
        "",
        "## Domain",
        "",
        f"- cthc_base: `{summary['cthc_base']}`",
        f"- domain_hash: `{summary['domain_hash']}`",
        "",
        "## Outputs",
        "",
    ]

    for key, value in summary["outputs"].items():
        md.append(f"- {key}: `{value}`")

    (OUTPUT_DIR / "custom_build_summary.md").write_text("\n".join(md), encoding="utf-8")

    return summary


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a custom HSRAG LAW corpus from clean public legal text.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to manifest JSON.")
    parser.add_argument("--salt", default=DEFAULT_SALT, help="Public reproducible benchmark salt.")
    parser.add_argument("--max-chars", type=int, default=1200, help="Maximum characters per chunk.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)

    gate_checks = validate_manifest(manifest)

    combined_text, text_checks, source_records = read_text_files(manifest)
    gate_checks.extend(text_checks)

    chunks = split_into_chunks(combined_text, max_chars=args.max_chars)
    gate_checks.append(
        GateCheck(
            check="chunk_count_positive",
            passed=len(chunks) > 0,
            detail=f"chunk_count={len(chunks)}",
        )
    )

    domain_hash = make_domain_hash(manifest, args.salt)
    chunk_records = build_chunk_records(manifest, chunks, domain_hash)

    summary = write_outputs(
        manifest=manifest,
        source_records=source_records,
        gate_checks=gate_checks,
        chunk_records=chunk_records,
        domain_hash=domain_hash,
        salt=args.salt,
    )

    print("=" * 80)
    print("HSRAG LAW — CUSTOM CORPUS BUILD")
    print("=" * 80)
    print(f"decision: {summary['decision']}")
    print(f"source_file_count: {summary['source_file_count']}")
    print(f"chunk_count: {summary['chunk_count']}")
    print(f"total_token_estimate: {summary['total_token_estimate']}")
    print(f"gate_passed: {summary['gate_passed']}")
    print(f"audit_chain_complete: {summary['audit_chain_complete']}")
    print(f"cthc_base: {summary['cthc_base']}")
    print(f"domain_hash: {summary['domain_hash']}")
    print("")
    print(f"results_dir: {OUTPUT_DIR}")
    print("=" * 80)

    return 0 if summary["decision"] == "CUSTOM_CORPUS_BUILD_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())