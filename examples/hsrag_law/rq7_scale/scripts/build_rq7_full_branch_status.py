from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REPORTS = Path("examples/hsrag_law/rq7_scale/05_reports")
INPUT = Path("examples/hsrag_law/rq7_scale/02_input")
CONFIG = Path("examples/hsrag_law/rq7_scale")

FULL_QUERY_SEED = INPUT / "query_seed.full.example.json"
FULL_QUERY_CONFIG = CONFIG / "config.rq7.full_queries.json"

DIAG_MD = REPORTS / "RQ7_FULL_QUERY_DIAGNOSTICS.md"
DIAG_JSON = REPORTS / "RQ7_FULL_QUERY_DIAGNOSTICS.json"
DIAG_SUMMARY = REPORTS / "RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json"

TRIAGE_MD = REPORTS / "RQ7_FULL_QUERY_TRIAGE.md"
TRIAGE_JSON = REPORTS / "RQ7_FULL_QUERY_TRIAGE.json"

STATUS_MD = REPORTS / "RQ7_FULL_BRANCH_STATUS.md"
STATUS_JSON = REPORTS / "RQ7_FULL_BRANCH_STATUS.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checked_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    required_files = [
        FULL_QUERY_SEED,
        FULL_QUERY_CONFIG,
        DIAG_MD,
        DIAG_JSON,
        DIAG_SUMMARY,
        TRIAGE_MD,
        TRIAGE_JSON,
    ]

    missing = [str(path) for path in required_files if not path.exists()]

    seed = load_json(FULL_QUERY_SEED) if FULL_QUERY_SEED.exists() else {}
    diagnostics = load_json(DIAG_JSON) if DIAG_JSON.exists() else {}
    triage = load_json(TRIAGE_JSON) if TRIAGE_JSON.exists() else {}

    passed = (
        not missing
        and seed.get("claim_boundary", {}).get("query_expansion_only") is True
        and diagnostics.get("claim_boundary", {}).get("diagnostic_only") is True
        and diagnostics.get("claim_boundary", {}).get("acceptance_failure_allowed_for_diagnostics") is True
        and triage.get("claim_boundary", {}).get("triage_only") is True
        and triage.get("claim_boundary", {}).get("acceptance_failure_allowed_for_diagnostics") is True
    )

    summary = {
        "schema": "HSRAG_RQ7_FULL_BRANCH_STATUS_V0_1",
        "status": "OK" if passed else "FAILED",
        "checked_at_utc": checked_at_utc,
        "branch_scope": "rq7-full-benchmark",
        "missing_files": missing,
        "full_query_seed": {
            "path": str(FULL_QUERY_SEED),
            "query_count": seed.get("query_count"),
            "added_query_count": seed.get("added_query_count"),
        },
        "diagnostics": {
            "path_md": str(DIAG_MD),
            "path_json": str(DIAG_JSON),
            "diagnostic_status": diagnostics.get("diagnostic_status"),
            "acceptance_passed": diagnostics.get("acceptance_passed"),
            "raw_result_count": diagnostics.get("raw_result_count"),
            "query_class_count": diagnostics.get("query_class_count"),
        },
        "triage": {
            "path_md": str(TRIAGE_MD),
            "path_json": str(TRIAGE_JSON),
            "raw_result_count": triage.get("raw_result_count"),
            "triage_summary": triage.get("triage_summary", {}),
        },
        "claim_boundary": {
            "full_query_expansion": True,
            "diagnostic_only": True,
            "triage_only": True,
            "acceptance_failure_allowed_for_diagnostics": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
        "next_branches": [
            "expanded real corpus",
            "1k/5k/10k scale after corpus expansion",
            "vector baseline",
            "hybrid baseline",
            "paper-grade report",
        ],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RQ7 Full Branch Status",
        "",
        f"- status: {summary['status']}",
        f"- checked_at_utc: {checked_at_utc}",
        "- branch_scope: rq7-full-benchmark",
        "",
        "## Current Full-Branch Additions",
        "",
        f"- full_query_seed: `{FULL_QUERY_SEED.as_posix()}`",
        f"- full_query_config: `{FULL_QUERY_CONFIG.as_posix()}`",
        f"- diagnostics_md: `{DIAG_MD.as_posix()}`",
        f"- diagnostics_json: `{DIAG_JSON.as_posix()}`",
        f"- diagnostics_summary: `{DIAG_SUMMARY.as_posix()}`",
        f"- triage_md: `{TRIAGE_MD.as_posix()}`",
        f"- triage_json: `{TRIAGE_JSON.as_posix()}`",
        "",
        "## Metrics",
        "",
        f"- query_count: {summary['full_query_seed']['query_count']}",
        f"- added_query_count: {summary['full_query_seed']['added_query_count']}",
        f"- diagnostic_status: {summary['diagnostics']['diagnostic_status']}",
        f"- acceptance_passed: {summary['diagnostics']['acceptance_passed']}",
        f"- raw_result_count: {summary['diagnostics']['raw_result_count']}",
        f"- query_class_count: {summary['diagnostics']['query_class_count']}",
        "",
        "## Claim Boundary",
        "",
        "- full_query_expansion: true",
        "- diagnostic_only: true",
        "- triage_only: true",
        "- acceptance_failure_allowed_for_diagnostics: true",
        "- full_scale_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- legal_advice: false",
        "",
        "## Next Branches",
        "",
        "- expanded real corpus",
        "- 1k / 5k / 10k scale after corpus expansion",
        "- vector baseline",
        "- hybrid baseline",
        "- paper-grade report",
        "",
    ]

    STATUS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
