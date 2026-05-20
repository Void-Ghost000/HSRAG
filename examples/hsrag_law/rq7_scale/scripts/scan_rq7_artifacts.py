from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COLUMN_ALIASES = {
    "domain": ["domain", "legal_domain"],
    "jurisdiction": ["jurisdiction", "region", "legal_jurisdiction"],
    "corpus": ["corpus", "corpus_id", "corpus_guess", "source_corpus"],
    "unit": ["unit", "unit_id", "article", "article_id", "section", "section_id"],
    "text": ["text", "chunk_text", "content", "article_text", "evidence_text"],
    "chunk_id": ["chunk_id", "id"],
    "source_hash": ["source_hash", "sha256", "content_hash"],
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "04_runs",
    "06_audit",
}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def find_column(fieldnames: list[str], logical_name: str) -> str | None:
    lowered = {field.lower(): field for field in fieldnames}

    for alias in COLUMN_ALIASES[logical_name]:
        if alias.lower() in lowered:
            return lowered[alias.lower()]

    return None


def detect_columns(fieldnames: list[str]) -> dict[str, str | None]:
    return {
        name: find_column(fieldnames, name)
        for name in COLUMN_ALIASES
    }


def is_candidate(mapping: dict[str, str | None]) -> bool:
    required = ["jurisdiction", "corpus", "unit", "text"]
    return all(mapping.get(name) for name in required)


def count_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def read_fieldnames(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def iter_csv_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for path in root.rglob("*.csv"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        files.append(path)

    return sorted(files)


def build_inventory(root: Path) -> dict[str, Any]:
    if not root.exists():
        raise FileNotFoundError(f"SCAN_ROOT_NOT_FOUND:{root}")

    if not root.is_dir():
        raise ValueError(f"SCAN_ROOT_NOT_DIRECTORY:{root}")

    scanned_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    artifacts: list[dict[str, Any]] = []

    for csv_path in iter_csv_files(root):
        try:
            fieldnames = read_fieldnames(csv_path)
            mapping = detect_columns(fieldnames)
            candidate = is_candidate(mapping)
            row_count = count_rows(csv_path)
            data = csv_path.read_bytes()

            artifacts.append(
                {
                    "path": str(csv_path.as_posix()),
                    "filename": csv_path.name,
                    "sha256": sha256_bytes(data),
                    "row_count": row_count,
                    "columns": fieldnames,
                    "detected_columns": mapping,
                    "rq7_auto_csv_candidate": candidate,
                    "reason": "OK" if candidate else "MISSING_REQUIRED_COLUMNS",
                }
            )
        except Exception as exc:
            artifacts.append(
                {
                    "path": str(csv_path.as_posix()),
                    "filename": csv_path.name,
                    "sha256": None,
                    "row_count": None,
                    "columns": [],
                    "detected_columns": {},
                    "rq7_auto_csv_candidate": False,
                    "reason": f"READ_ERROR:{type(exc).__name__}:{exc}",
                }
            )

    candidate_count = sum(1 for item in artifacts if item["rq7_auto_csv_candidate"])

    return {
        "schema": "HSRAG_RQ7_ARTIFACT_INVENTORY_V0_1",
        "scan_root": str(root.as_posix()),
        "scanned_at_utc": scanned_at_utc,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "artifact_count": len(artifacts),
        "candidate_count": candidate_count,
        "artifacts": artifacts,
        "claim_boundary": {
            "inventory_only": True,
            "does_not_run_benchmark": True,
            "official_rq4_corpus_connected": False,
        },
    }


def build_markdown_report(inventory: dict[str, Any]) -> str:
    lines = [
        "# RQ7 Artifact Inventory",
        "",
        "## Status",
        "",
        f"- local_only: {inventory['local_only']}",
        f"- zero_network: {inventory['zero_network']}",
        f"- zero_secret: {inventory['zero_secret']}",
        f"- artifact_count: {inventory['artifact_count']}",
        f"- candidate_count: {inventory['candidate_count']}",
        "",
        "## Claim Boundary",
        "",
        "This inventory only scans local CSV artifacts and detects whether they look compatible with the RQ7 auto CSV adapter.",
        "",
        "It does not run the full RQ7 benchmark.",
        "It does not connect official RQ4 corpus automatically.",
        "It does not provide legal advice.",
        "",
        "## Artifacts",
        "",
        "| candidate | rows | file | reason |",
        "|---:|---:|---|---|",
    ]

    for item in inventory["artifacts"]:
        lines.append(
            "| {candidate} | {rows} | {file} | {reason} |".format(
                candidate="yes" if item["rq7_auto_csv_candidate"] else "no",
                rows=item["row_count"] if item["row_count"] is not None else "NA",
                file=item["path"],
                reason=item["reason"],
            )
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="examples/hsrag_law")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    inventory = build_inventory(root)

    output_path = Path(args.output)
    report_path = Path(args.report)

    write_json(output_path, inventory)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_markdown_report(inventory), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "report": str(report_path),
                "artifact_count": inventory["artifact_count"],
                "candidate_count": inventory["candidate_count"],
                "local_only": True,
                "zero_network": True,
                "zero_secret": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
