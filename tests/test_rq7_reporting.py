from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_reporting_layer_generates_markdown_report() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7.py"),
            "--config",
            str(ROOT / "config.rq7.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["passed"] is True
    assert summary["toy_retrieval"] is True
    assert summary["salted_domain_gate"] is True

    run_report = Path(summary["report"])

    assert run_report.exists()
    assert summary["latest_report"] is None

    report_text = run_report.read_text(encoding="utf-8")

    assert "# HSRAG RQ7 Report" in report_text
    assert "## Metrics Summary" in report_text
    assert "latency" not in report_text.lower() or "p99_ms" in report_text
    assert "esi" in report_text.lower()
    assert "token_cost_per_1k" in report_text
    assert "salted_domain_gate: True" in report_text
    assert "## Acceptance Gates" in report_text
    assert "## Known Limits" in report_text
    assert "This is toy-real retrieval" in report_text

    run_manifest = json.loads((Path(summary["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["salted_domain_gate"] is True

    audit_events = [
        json.loads(line)
        for line in Path(summary["audit_chain"]).read_text(encoding="utf-8").splitlines()
    ]
    assert any(event["event_type"] == "REPORT_WRITTEN" for event in audit_events)
