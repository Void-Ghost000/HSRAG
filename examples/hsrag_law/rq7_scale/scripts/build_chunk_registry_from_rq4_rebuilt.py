from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SEGMENT_RE = re.compile(r"[^A-Za-z0-9_]+")


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


def normalize_source_hash(value: str, fallback_text: str) -> str:
    text = str(value or "").strip()

    if text.startswith("sha256:"):
        return text

    if re.fullmatch(r"[a-fA-F0-9]{64}", text):
        return "sha256:" + text.lower()

    return sha256_text(fallback_text)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("EMPTY_RQ4_REBUILT_CSV")

    return rows


def require(row: dict[str, str], column: str, row_index: int) -> str:
    if column not in row:
        raise ValueError(f"MISSING_COLUMN:{column}")

    value = str(row[column]).strip()

    if not value:
        raise ValueError(f"EMPTY_COLUMN:{column}:ROW_{row_index}")

    return value


def short_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length].upper()


def derive_unit(corpus_id: str, source_title: str, source_url: str, text: str) -> str:
    corpus = corpus_id.upper()
    haystack = " ".join([source_title, source_url, text]).lower()

    if corpus == "EU_AI_ACT":
        if "article 5" in haystack or "prohibited ai" in haystack or "prohibited artificial intelligence" in haystack:
            return "ARTICLE_5"
        if "article 6" in haystack or "high-risk ai" in haystack or "high risk ai" in haystack:
            return "ARTICLE_6"

    if corpus == "US_CDA230":
        if "section 230" in haystack or "47 u.s.c" in haystack or "47 usc" in haystack or "interactive computer service" in haystack:
            return "SECTION_230"

    if corpus == "US_COPPA":
        if "children" in haystack or "coppa" in haystack:
            return "CHILDREN_PRIVACY"

    fallback_key = "|".join([corpus_id, source_title, source_url])
    return "SOURCE_" + short_hash(fallback_key)


def build_registry(csv_path: Path) -> dict[str, Any]:
    rows = read_csv(csv_path)
    chunks: list[dict[str, Any]] = []

    required_columns = {
        "chunk_id",
        "corpus_id",
        "jurisdiction",
        "source_title",
        "source_url",
        "candidate_type",
        "source_hash",
        "chunk_index",
        "chunk_hash",
        "text",
    }

    missing_columns = sorted(required_columns - set(rows[0].keys()))
    if missing_columns:
        raise ValueError("MISSING_REQUIRED_COLUMNS:" + ",".join(missing_columns))

    seen_chunk_ids: set[str] = set()
    seen_cthc_addresses: set[str] = set()

    for row_index, row in enumerate(rows, start=1):
        raw_chunk_id = require(row, "chunk_id", row_index)
        corpus_id = safe_segment(require(row, "corpus_id", row_index))
        jurisdiction = safe_segment(require(row, "jurisdiction", row_index))
        source_title = str(row.get("source_title", "")).strip()
        source_url = str(row.get("source_url", "")).strip()
        candidate_type = str(row.get("candidate_type", "RQ4_REBUILT")).strip() or "RQ4_REBUILT"
        text = normalize_text(require(row, "text", row_index))

        chunk_id = safe_segment(raw_chunk_id)

        if chunk_id in seen_chunk_ids:
            raise ValueError(f"DUPLICATE_CHUNK_ID:{chunk_id}")

        unit = safe_segment(derive_unit(corpus_id, source_title, source_url, text))
        source_hash = normalize_source_hash(str(row.get("source_hash", "")), text)

        cthc_address = f"cthc://LAW/{jurisdiction}/{corpus_id}/{unit}/{chunk_id}"

        if cthc_address in seen_cthc_addresses:
            raise ValueError(f"DUPLICATE_CTHC_ADDRESS:{cthc_address}")

        chunks.append(
            {
                "chunk_id": chunk_id,
                "domain": "LAW",
                "jurisdiction": jurisdiction,
                "corpus": corpus_id,
                "unit": unit,
                "cthc_address": cthc_address,
                "source_hash": source_hash,
                "source_type": candidate_type,
                "official_source": "OFFICIAL" in candidate_type.upper(),
                "source_title": source_title,
                "source_url": source_url,
                "source_path": str(csv_path.as_posix()),
                "chunk_index": str(row.get("chunk_index", "")),
                "chunk_hash": str(row.get("chunk_hash", "")),
                "text": text,
            }
        )

        seen_chunk_ids.add(chunk_id)
        seen_cthc_addresses.add(cthc_address)

    return {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "description": "Generated RQ7 chunk registry from RQ4 rebuilt chunks artifact.",
        "generator": "build_chunk_registry_from_rq4_rebuilt.py",
        "local_only": True,
        "source_artifact": str(csv_path.as_posix()),
        "source_artifact_hash": sha256_text(csv_path.read_text(encoding="utf-8-sig")),
        "chunk_count": len(chunks),
        "chunks": chunks,
        "claim_boundary": {
            "rq4_rebuilt_artifact_adapter": True,
            "official_rq4_corpus_connected": True,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()

    if not csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{csv_path}")

    registry = build_registry(csv_path)
    output_path = Path(args.output)
    write_json(output_path, registry)

    units = sorted({chunk["unit"] for chunk in registry["chunks"]})
    corpora = sorted({chunk["corpus"] for chunk in registry["chunks"]})

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "chunk_count": registry["chunk_count"],
                "source_artifact_hash": registry["source_artifact_hash"],
                "corpora": corpora,
                "unit_count": len(units),
                "sample_units": units[:20],
                "local_only": True,
                "rq4_rebuilt_artifact_adapter": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
