from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REPORTS = Path("examples/hsrag_law/rq7_scale/05_reports")

PUBLIC_REPORT = REPORTS / "RQ7_PUBLIC_REPORT.md"
PUBLIC_SUMMARY = REPORTS / "RQ7_PUBLIC_REPORT_SUMMARY.json"
RELEASE_CHECKPOINT_MD = REPORTS / "RQ7_RELEASE_CHECKPOINT.md"
RELEASE_CHECKPOINT_JSON = REPORTS / "RQ7_RELEASE_CHECKPOINT.json"
STATUS_MD = REPORTS / "RQ7_STATUS_SUMMARY.md"
STATUS_JSON = REPORTS / "RQ7_STATUS_SUMMARY.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    required = [
        PUBLIC_REPORT,
        PUBLIC_SUMMARY,
        RELEASE_CHECKPOINT_MD,
        RELEASE_CHECKPOINT_JSON,
    ]

    missing = [str(path) for path in required if not path.exists()]

    public_summary = load_json(PUBLIC_SUMMARY) if PUBLIC_SUMMARY.exists() else {}
    release_checkpoint = load_json(RELEASE_CHECKPOINT_JSON) if RELEASE_CHECKPOINT_JSON.exists() else {}

    checked_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    passed = (
        not missing
        and public_summary.get("status") == "OK"
        and release_checkpoint.get("status") == "OK"
        and release_checkpoint.get("claim_boundary", {}).get("rq7_v0_1_checkpoint") is True
        and release_checkpoint.get("claim_boundary", {}).get("full_scale_benchmark") is False
        and release_checkpoint.get("claim_boundary", {}).get("vector_hybrid_baselines") is False
        and release_checkpoint.get("claim_boundary", {}).get("unit_derivation_is_heuristic") is True
    )

    summary = {
        "schema": "HSRAG_RQ7_STATUS_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "checked_at_utc": checked_at_utc,
        "missing_files": missing,
        "published_files": {
            "public_report": str(PUBLIC_REPORT),
            "public_summary": str(PUBLIC_SUMMARY),
            "release_checkpoint_md": str(RELEASE_CHECKPOINT_MD),
            "release_checkpoint_json": str(RELEASE_CHECKPOINT_JSON),
        },
        "current_maturity": "RQ7 v0.1 release checkpoint / Level 2B-pre",
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "rq4_metrics_snapshot_available": True,
            "rq4_scale_tiers_available": True,
            "actual_elapsed_timing_available": True,
            "public_report_published": True,
            "release_checkpoint_published": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
        "recommended_verify_commands": [
            "python -m pytest tests -k rq7",
            "python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889",
            "python examples/hsrag_law/rq7_scale/scripts/publish_rq7_release_checkpoint.py --tiers 100,300,600,889",
        ],
    }

    STATUS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RQ7 Status Summary",
        "",
        f"- status: {summary['status']}",
        f"- checked_at_utc: {checked_at_utc}",
        "- maturity: RQ7 v0.1 release checkpoint / Level 2B-pre",
        "",
        "## Published Files",
        "",
        f"- `{PUBLIC_REPORT.as_posix()}`",
        f"- `{PUBLIC_SUMMARY.as_posix()}`",
        f"- `{RELEASE_CHECKPOINT_MD.as_posix()}`",
        f"- `{RELEASE_CHECKPOINT_JSON.as_posix()}`",
        f"- `{STATUS_JSON.as_posix()}`",
        "",
        "## Claim Boundary",
        "",
        "- rq4_rebuilt_artifact_connected: true",
        "- rq4_metrics_snapshot_available: true",
        "- rq4_scale_tiers_available: true",
        "- actual_elapsed_timing_available: true",
        "- public_report_published: true",
        "- release_checkpoint_published: true",
        "- full_scale_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- unit_derivation_is_heuristic: true",
        "- legal_advice: false",
        "",
        "## Verify Commands",
        "",
        "    python -m pytest tests -k rq7",
        "    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889",
        "    python examples/hsrag_law/rq7_scale/scripts/publish_rq7_release_checkpoint.py --tiers 100,300,600,889",
        "",
        "## Next Branches",
        "",
        "- RQ7 full-scale benchmark branch",
        "- expanded query set branch",
        "- vector / hybrid baseline branch",
        "- multi-corpus scale branch",
        "",
    ]

    STATUS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
