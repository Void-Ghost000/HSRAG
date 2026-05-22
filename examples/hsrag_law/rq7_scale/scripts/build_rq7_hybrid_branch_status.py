from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


BASE = Path("examples/hsrag_law/rq7_scale")
REPORTS = BASE / "05_reports"

DESIGN = BASE / "RQ7_HYBRID_BASELINE_DESIGN.md"
SCORER = BASE / "scripts" / "local_hybrid_scorer.py"
CONFIG = BASE / "config.rq7.hybrid.json"

HYBRID_REPORT_MD = REPORTS / "RQ7_HYBRID_BASELINE_REPORT.md"
HYBRID_REPORT_JSON = REPORTS / "RQ7_HYBRID_BASELINE_REPORT_SUMMARY.json"
HYBRID_REPORT_CSV = REPORTS / "RQ7_HYBRID_BASELINE_REPORT.csv"

STATUS_MD = REPORTS / "RQ7_HYBRID_BRANCH_STATUS.md"
STATUS_JSON = REPORTS / "RQ7_HYBRID_BRANCH_STATUS.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checked_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    required = [
        DESIGN,
        SCORER,
        CONFIG,
        HYBRID_REPORT_MD,
        HYBRID_REPORT_JSON,
        HYBRID_REPORT_CSV,
    ]

    missing = [str(path) for path in required if not path.exists()]

    config = load_json(CONFIG) if CONFIG.exists() else {}
    report = load_json(HYBRID_REPORT_JSON) if HYBRID_REPORT_JSON.exists() else {}

    modes = config.get("modes", [])
    hybrid_modes = report.get("hybrid_modes", [])

    passed = (
        not missing
        and "HYBRID_BM25_VECTOR" in modes
        and "CTHC_PRUNED_HYBRID" in modes
        and "HYBRID_BM25_VECTOR" in hybrid_modes
        and "CTHC_PRUNED_HYBRID" in hybrid_modes
        and report.get("claim_boundary", {}).get("local_deterministic_hybrid_baseline") is True
        and report.get("claim_boundary", {}).get("external_embedding_api") is False
        and report.get("claim_boundary", {}).get("network_required") is False
        and report.get("claim_boundary", {}).get("secret_required") is False
    )

    summary = {
        "schema": "HSRAG_RQ7_HYBRID_BRANCH_STATUS_V0_1",
        "status": "OK" if passed else "FAILED",
        "checked_at_utc": checked_at_utc,
        "branch_scope": "rq7-hybrid-baseline",
        "missing_files": missing,
        "config_modes": modes,
        "hybrid_modes": hybrid_modes,
        "published_files": {
            "design": str(DESIGN),
            "scorer": str(SCORER),
            "config": str(CONFIG),
            "report_md": str(HYBRID_REPORT_MD),
            "report_json": str(HYBRID_REPORT_JSON),
            "report_csv": str(HYBRID_REPORT_CSV),
        },
        "claim_boundary": {
            "local_deterministic_hybrid_baseline": True,
            "external_embedding_api": False,
            "network_required": False,
            "secret_required": False,
            "state_of_the_art_hybrid_search": False,
            "production_vector_database": False,
            "legal_advice": False,
        },
        "final_checkpoint_ready": passed,
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RQ7 Hybrid Branch Status",
        "",
        f"- status: {summary['status']}",
        f"- checked_at_utc: {checked_at_utc}",
        "- branch_scope: rq7-hybrid-baseline",
        f"- final_checkpoint_ready: {str(passed).lower()}",
        "",
        "## Hybrid Modes",
        "",
    ]

    for mode in hybrid_modes:
        lines.append(f"- {mode}")

    lines.extend([
        "",
        "## Published Files",
        "",
        f"- `{DESIGN.as_posix()}`",
        f"- `{SCORER.as_posix()}`",
        f"- `{CONFIG.as_posix()}`",
        f"- `{HYBRID_REPORT_MD.as_posix()}`",
        f"- `{HYBRID_REPORT_JSON.as_posix()}`",
        f"- `{HYBRID_REPORT_CSV.as_posix()}`",
        f"- `{STATUS_JSON.as_posix()}`",
        "",
        "## Claim Boundary",
        "",
        "- local_deterministic_hybrid_baseline: true",
        "- external_embedding_api: false",
        "- network_required: false",
        "- secret_required: false",
        "- state_of_the_art_hybrid_search: false",
        "- production_vector_database: false",
        "- legal_advice: false",
        "",
        "## Verify",
        "",
        "    python -m pytest tests -k rq7",
        "    python examples/hsrag_law/rq7_scale/scripts/build_rq7_hybrid_branch_status.py",
        "",
    ])

    STATUS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
