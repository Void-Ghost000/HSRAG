from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def split_paragraph_chunks(text: str, max_tokens: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = len(tokenize(paragraph))

        if current and current_tokens + paragraph_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_tokens = paragraph_tokens
        else:
            current.append(paragraph)
            current_tokens += paragraph_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def safe_resolve_under_base(base_dir: Path, relative_path: str) -> Path:
    candidate = (base_dir / relative_path).resolve()
    resolved_base = base_dir.resolve()

    try:
        candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"PATH_OUTSIDE_RQ7_BASE:{relative_path}") from exc

    return candidate


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != "HSRAG_RQ7_REAL_LAW_MANIFEST_V0_1":
        raise ValueError("INVALID_REAL_LAW_MANIFEST_SCHEMA")

    if manifest.get("local_only") is not True:
        raise ValueError("MANIFEST_MUST_BE_LOCAL_ONLY")

    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("EMPTY_REAL_LAW_MANIFEST")

    required = {"entry_id", "domain", "jurisdiction", "corpus", "unit", "path", "source_type", "official_source"}

    seen_entry_ids: set[str] = set()

    for index, entry in enumerate(entries):
        missing = [field for field in required if field not in entry or entry[field] in (None, "")]
        if missing:
            raise ValueError(f"INVALID_ENTRY_{index}_MISSING_{','.join(missing)}")

        entry_id = str(entry["entry_id"])
        if entry_id in seen_entry_ids:
            raise ValueError(f"DUPLICATE_ENTRY_ID:{entry_id}")
        seen_entry_ids.add(entry_id)


def build_registry(base_dir: Path, manifest_path: Path, max_tokens: int) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    validate_manifest(manifest)

    chunks: list[dict[str, Any]] = []

    for entry in manifest["entries"]:
        file_path = safe_resolve_under_base(base_dir, str(entry["path"]))

        if not file_path.exists():
            raise FileNotFoundError(f"TEXT_FILE_NOT_FOUND:{file_path}")

        raw_text = file_path.read_text(encoding="utf-8")
        normalized = normalize_text(raw_text)

        if not normalized:
            raise ValueError(f"EMPTY_TEXT_FILE:{file_path}")

        source_hash = sha256_text(normalized)
        text_chunks = split_paragraph_chunks(normalized, max_tokens=max_tokens)

        for index, chunk_text in enumerate(text_chunks, start=1):
            chunk_suffix = f"CHUNK_{index:04d}"
            chunk_id = f"{entry['corpus']}_{entry['unit']}_{chunk_suffix}"
            cthc_address = "cthc://{domain}/{jurisdiction}/{corpus}/{unit}/{chunk}".format(
                domain=entry["domain"],
                jurisdiction=entry["jurisdiction"],
                corpus=entry["corpus"],
                unit=entry["unit"],
                chunk=chunk_suffix,
            )

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "domain": entry["domain"],
                    "jurisdiction": entry["jurisdiction"],
                    "corpus": entry["corpus"],
                    "unit": entry["unit"],
                    "cthc_address": cthc_address,
                    "source_hash": source_hash,
                    "source_type": entry["source_type"],
                    "official_source": bool(entry["official_source"]),
                    "source_path": str(Path(entry["path"]).as_posix()),
                    "text": chunk_text,
                }
            )

    registry = {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "description": "Generated local RQ7 chunk registry from plaintext legal files.",
        "generator": "build_chunk_registry.py",
        "local_only": True,
        "manifest_hash": sha256_json(manifest),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    return registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-tokens", type=int, default=220)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    base_dir = manifest_path.parent.parent

    registry = build_registry(
        base_dir=base_dir,
        manifest_path=manifest_path,
        max_tokens=args.max_tokens,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, registry)

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "chunk_count": registry["chunk_count"],
                "manifest_hash": registry["manifest_hash"],
                "local_only": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
