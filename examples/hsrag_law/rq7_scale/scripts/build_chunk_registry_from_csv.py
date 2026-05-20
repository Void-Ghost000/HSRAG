from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SEGMENT_RE = re.compile(r"[^A-Za-z0-9_]+")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split())


def safe_segment(value: str) -> str:
    cleaned = SEGMENT_RE.sub("_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("EMPTY_CTHC_SEGMENT")
    return cleaned


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("EMPTY_CSV")

    return rows


def require_column(row: dict[str, str], column: str, row_index: int) -> str:
    if column not in row:
        raise ValueError(f"MISSING_COLUMN:{column}")

    value = str(row[column]).strip()

    if not value:
        raise ValueError(f"EMPTY_COLUMN:{column}:ROW_{row_index}")

    return value


def build_registry_from_csv(
    csv_path: Path,
    domain_column: str,
    jurisdiction_column: str,
    corpus_column: str,
    unit_column: str,
    text_column: str,
    chunk_id_column: str | None,
    source_hash_column: str | None,
) -> dict[str, Any]:
    rows = load_csv_rows(csv_path)
    chunks: list[dict[str, Any]] = []

    seen_chunk_ids: set[str] = set()
    seen_cthc_addresses: set[str] = set()

    for row_index, row in enumerate(rows, start=1):
        domain = safe_segment(require_column(row, domain_column, row_index))
        jurisdiction = safe_segment(require_column(row, jurisdiction_column, row_index))
        corpus = safe_segment(require_column(row, corpus_column, row_index))
        unit = safe_segment(require_column(row, unit_column, row_index))
        text = normalize_text(require_column(row, text_column, row_index))

        if chunk_id_column and chunk_id_column in row and str(row[chunk_id_column]).strip():
            chunk_id = safe_segment(str(row[chunk_id_column]).strip())
        else:
            chunk_id = f"{corpus}_{unit}_CHUNK_{row_index:04d}"

        if chunk_id in seen_chunk_ids:
            raise ValueError(f"DUPLICATE_CHUNK_ID:{chunk_id}")

        if source_hash_column and source_hash_column in row and str(row[source_hash_column]).strip():
            source_hash = str(row[source_hash_column]).strip()
            if not source_hash.startswith("sha256:"):
                raise ValueError(f"INVALID_SOURCE_HASH:{chunk_id}")
        else:
            source_hash = sha256_text(text)

        cthc_address = f"cthc://{domain}/{jurisdiction}/{corpus}/{unit}/{chunk_id}"

        if cthc_address in seen_cthc_addresses:
            raise ValueError(f"DUPLICATE_CTHC_ADDRESS:{cthc_address}")

        source_type = str(row.get("source_type", "LOCAL_CSV")).strip() or "LOCAL_CSV"
        official_source = parse_bool(row.get("official_source", False))

        chunks.append(
            {
                "chunk_id": chunk_id,
                "domain": domain,
                "jurisdiction": jurisdiction,
                "corpus": corpus,
                "unit": unit,
                "cthc_address": cthc_address,
                "source_hash": source_hash,
                "source_type": source_type,
                "official_source": official_source,
                "source_path": str(csv_path.as_posix()),
                "text": text,
            }
        )

        seen_chunk_ids.add(chunk_id)
        seen_cthc_addresses.add(cthc_address)

    return {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "description": "Generated local RQ7 chunk registry from CSV chunk artifact.",
        "generator": "build_chunk_registry_from_csv.py",
        "local_only": True,
        "csv_path": str(csv_path.as_posix()),
        "csv_hash": sha256_text(csv_path.read_text(encoding="utf-8-sig")),
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
    parser.add_argument("--domain-column", default="domain")
    parser.add_argument("--jurisdiction-column", default="jurisdiction")
    parser.add_argument("--corpus-column", default="corpus")
    parser.add_argument("--unit-column", default="unit")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--chunk-id-column", default="")
    parser.add_argument("--source-hash-column", default="")
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()

    if not csv_path.exists():
        raise SystemExit(f"CSV_NOT_FOUND:{csv_path}")

    registry = build_registry_from_csv(
        csv_path=csv_path,
        domain_column=args.domain_column,
        jurisdiction_column=args.jurisdiction_column,
        corpus_column=args.corpus_column,
        unit_column=args.unit_column,
        text_column=args.text_column,
        chunk_id_column=args.chunk_id_column or None,
        source_hash_column=args.source_hash_column or None,
    )

    output_path = Path(args.output)
    write_json(output_path, registry)

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "chunk_count": registry["chunk_count"],
                "csv_hash": registry["csv_hash"],
                "local_only": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
