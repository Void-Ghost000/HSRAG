from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SEGMENT_RE = re.compile(r"[^A-Za-z0-9_]+")

COLUMN_ALIASES = {
    "domain": ["domain", "legal_domain"],
    "jurisdiction": ["jurisdiction", "region", "legal_jurisdiction"],
    "corpus": ["corpus", "corpus_id", "corpus_guess", "source_corpus"],
    "unit": ["unit", "unit_id", "article", "article_id", "section", "section_id"],
    "text": ["text", "chunk_text", "content", "article_text", "evidence_text"],
    "chunk_id": ["chunk_id", "id"],
    "source_hash": ["source_hash", "sha256", "content_hash"],
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split())


def safe_segment(value: str) -> str:
    cleaned = SEGMENT_RE.sub("_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("EMPTY_CTHC_SEGMENT")
    return cleaned


def load_rows(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        raise ValueError("EMPTY_CSV")

    return rows, fieldnames


def find_column(fieldnames: list[str], logical_name: str, required: bool = True) -> str | None:
    lowered = {field.lower(): field for field in fieldnames}

    for alias in COLUMN_ALIASES[logical_name]:
        if alias.lower() in lowered:
            return lowered[alias.lower()]

    if required:
        raise ValueError(f"MISSING_REQUIRED_COLUMN_FOR:{logical_name}")

    return None


def parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def build_registry(csv_path: Path) -> dict[str, Any]:
    rows, fieldnames = load_rows(csv_path)

    domain_col = find_column(fieldnames, "domain", required=False)
    jurisdiction_col = find_column(fieldnames, "jurisdiction")
    corpus_col = find_column(fieldnames, "corpus")
    unit_col = find_column(fieldnames, "unit")
    text_col = find_column(fieldnames, "text")
    chunk_id_col = find_column(fieldnames, "chunk_id", required=False)
    source_hash_col = find_column(fieldnames, "source_hash", required=False)

    chunks: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    seen_cthc_addresses: set[str] = set()

    for row_index, row in enumerate(rows, start=1):
        domain = safe_segment(str(row.get(domain_col, "LAW"))) if domain_col else "LAW"
        jurisdiction = safe_segment(str(row[jurisdiction_col]))
        corpus = safe_segment(str(row[corpus_col]))
        unit = safe_segment(str(row[unit_col]))
        text = normalize_text(str(row[text_col]))

        if not text:
            raise ValueError(f"EMPTY_TEXT:ROW_{row_index}")

        if chunk_id_col and row.get(chunk_id_col):
            chunk_id = safe_segment(str(row[chunk_id_col]))
        else:
            chunk_id = f"{corpus}_{unit}_CHUNK_{row_index:04d}"

        if chunk_id in seen_chunk_ids:
            raise ValueError(f"DUPLICATE_CHUNK_ID:{chunk_id}")

        if source_hash_col and row.get(source_hash_col):
            source_hash = str(row[source_hash_col]).strip()
            if not source_hash.startswith("sha256:"):
                raise ValueError(f"INVALID_SOURCE_HASH:{chunk_id}")
        else:
            source_hash = sha256_text(text)

        cthc_address = f"cthc://{domain}/{jurisdiction}/{corpus}/{unit}/{chunk_id}"

        if cthc_address in seen_cthc_addresses:
            raise ValueError(f"DUPLICATE_CTHC_ADDRESS:{cthc_address}")

        chunks.append(
            {
                "chunk_id": chunk_id,
                "domain": domain,
                "jurisdiction": jurisdiction,
                "corpus": corpus,
                "unit": unit,
                "cthc_address": cthc_address,
                "source_hash": source_hash,
                "source_type": str(row.get("source_type", "AUTO_CSV")).strip() or "AUTO_CSV",
                "official_source": parse_bool(row.get("official_source", False)),
                "source_path": str(csv_path.as_posix()),
                "text": text,
            }
        )

        seen_chunk_ids.add(chunk_id)
        seen_cthc_addresses.add(cthc_address)

    return {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "description": "Generated RQ7 chunk registry from auto-detected CSV artifact columns.",
        "generator": "build_chunk_registry_auto_csv.py",
        "local_only": True,
        "csv_path": str(csv_path.as_posix()),
        "csv_hash": sha256_text(csv_path.read_text(encoding="utf-8-sig")),
        "detected_columns": {
            "domain": domain_col,
            "jurisdiction": jurisdiction_col,
            "corpus": corpus_col,
            "unit": unit_col,
            "text": text_col,
            "chunk_id": chunk_id_col,
            "source_hash": source_hash_col,
        },
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()

    if not csv_path.exists():
        raise SystemExit(f"CSV_NOT_FOUND:{csv_path}")

    registry = build_registry(csv_path)
    output_path = Path(args.output)
    write_json(output_path, registry)

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "chunk_count": registry["chunk_count"],
                "csv_hash": registry["csv_hash"],
                "detected_columns": registry["detected_columns"],
                "local_only": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
