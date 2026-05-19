from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_demo_script_runs_end_to_end(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "src" / "hsrag_api_sqlite" / "demo.py"
    input_path = project_root / "input" / "api_spec.example.json"
    db_path = tmp_path / "demo_api_specs.sqlite3"
    report_path = tmp_path / "demo_report.json"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--db",
            str(db_path),
            "--report",
            str(report_path),
        ],
        cwd=str(project_root),
        text=True,
        capture_output=True,
        check=True,
    )

    assert db_path.exists(), result.stdout + result.stderr
    assert report_path.exists(), result.stdout + result.stderr

    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["scope"]["local_only"] is True
    assert report["scope"]["zero_secret"] is True
    assert report["scope"]["zero_network"] is True

    assert report["steps"]["first_ingest"]["status"] == "ok"
    assert report["steps"]["second_ingest_revision"]["status"] == "ok"
    assert report["steps"]["second_ingest_revision"]["reason_code"] == "NEW_SPEC_REVISION_CREATED"

    assert report["steps"]["query_by_method_path"]["status"] == "found"
    assert report["steps"]["query_by_cthc_hash"]["status"] == "found"
    assert report["steps"]["history_by_cthc_hash"]["status"] == "found"

    assert report["steps"]["semantic_discovery"]["status"] == "found_with_warning"
    assert report["steps"]["semantic_discovery"]["reason_code"] == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION"

    history = report["steps"]["history_by_cthc_hash"]["data"]["history"]
    revisions = [
        item["spec_revision"]
        for item in history
        if item["path"] == "/users/{id}"
    ]

    assert revisions == [1, 2]
