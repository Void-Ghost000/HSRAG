from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


BASE = Path("examples/hsrag_law/rq7_scale")
REPORTS = BASE / "05_reports"

DESIGN = BASE / "RQ7_VECTOR_BASELINE_DESIGN.md"
VECTORIZER = BASE / "scripts" / "local_hash_vector.py"
CONFIG = BASE / "config.rq7.vector.json"
VECTOR_REPORT_MD = REPORTS / "RQ7_VECTOR_BASELINE_REPORT.md"
VECTOR_REPORT_JSON = REPORTS / "RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json"
VECTOR_REPORT_CSV = REPORTS / "RQ7_VECTOR_BASELINE_REPORT.csv"

STATUS_MD = REPORTS / "RQ7_VECTOR_BRANCH_STATUS.md"
STATUS_JSON = REPORTS / "RQ7_VECTOR_BRANCH_STATUS.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checked_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    required = [
        DESIGN,
        VECTORIZER,
        CONFIG,
        VECTOR_REPORT_MD,
        VECTOR_REPORT_JSON,
        VECTOR_REPORT_CSV,
    ]

    missing = [str(path) for path in required if not path.exists()]

    config = load_json(CONFIG) if CONFIG.exists() else {}
    report = load_json(VECTOR_REPORT_JSON) if VECTOR_REPORT_JSON.exists() else {}

    modes = config.get("modes", [])
    vector_modes = report.get("vector_modes", [])

    passed = (
        not missing
        and "VECTOR_GLOBAL" in modes
        and "CTHC_PRUNED_VECTOR" in modes
        and "VECTOR_GLOBAL" in vector_modes
        and "CTHC_PRUNED_VECTOR" in vector_modes
        and report.get("claim_boundary", {}).get("local_deterministic_vector_baseline") is True
        and report.get("claim_boundary", {}).get("external_embedding_api") is False
        and report.get("claim_boundary", {}).get("network_required") is False
        and report.get("claim_boundary", {}).get("secret_required") is False
    )

    summary = {
        "schema": "HSRAG_RQ7_VECTOR_BRANCH_STATUS_V0_1",
        "status": "OK" if passed else "FAILED",
        "checked_at_utc": checked_at_utc,
        "branch_scope": "rq7-vector-baseline",
        "missing_files": missing,
        "vector_modes": vector_modes,
        "config_modes": modes,
        "published_files": {
            "design": str(DESIGN),
            "vectorizer": str(VECTORIZER),
            "config": str(CONFIG),
            "report_md": str(VECTOR_REPORT_MD),
            "report_json": str(VECTOR_REPORT_JSON),
            "report_csv": str(VECTOR_REPORT_CSV),
        },
        "claim_boundary": {
            "local_deterministic_vector_baseline": True,
            "external_embedding_api": False,
            "network_required": False,
            "secret_required": False,
            "state_of_the_art_vector_search": False,
            "production_vector_database": False,
            "hybrid_ranking": False,
            "legal_advice": False,
        },
        "next_steps": [
            "RQ7-vector.8 final vector verify",
            "RQ7-vector.9 optional tag",
            "future branch: hybrid BM25/vector baseline",
        ],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RQ7 Vector Branch Status",
        "",
        f"- status: {summary['status']}",
        f"- checked_at_utc: {checked_at_utc}",
        "- branch_scope: rq7-vector-baseline",
        "",
        "## Current Vector Additions",
        "",
        f"- design: `{DESIGN.as_posix()}`",
        f"- vectorizer: `{VECTORIZER.as_posix()}`",
        f"- config: `{CONFIG.as_posix()}`",
        f"- report_md: `{VECTOR_REPORT_MD.as_posix()}`",
        f"- report_json: `{VECTOR_REPORT_JSON.as_posix()}`",
        f"- report_csv: `{VECTOR_REPORT_CSV.as_posix()}`",
        "",
        "## Vector Modes",
        "",
    ]

    for mode in vector_modes:
        lines.append(f"- {mode}")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- local_deterministic_vector_baseline: true",
            "- external_embedding_api: false",
            "- network_required: false",
            "- secret_required: false",
            "- state_of_the_art_vector_search: false",
            "- production_vector_database: false",
            "- hybrid_ranking: false",
            "- legal_advice: false",
            "",
            "## Next Steps",
            "",
            "- RQ7-vector.8 final vector verify",
            "- RQ7-vector.9 optional tag",
            "- future branch: hybrid BM25/vector baseline",
            "",
        ]
    )

    STATUS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
