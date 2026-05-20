from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_candidate_select_and_run_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_candidate.py"),
            "--root",
            str(ROOT / "02_input"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["acceptance_passed"] is True
    assert summary["latest_report_is_clean"] is True

    assert summary["selected_candidate"]["filename"] in {
        "rq7_auto_csv_fixture.example.csv",
        "rq7_csv_fixture.example.csv",
    }

    runner = summary["runner"]
    assert runner["status"] == "OK"
    assert runner["passed"] is True
    assert runner["salted_domain_gate"] is True
    assert runner["latest_report"] is None
    assert Path(runner["metrics_by_query_class"]).exists()


def test_rq7_candidate_select_supports_prefer_auto_csv() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_candidate.py"),
            "--root",
            str(ROOT / "02_input"),
            "--prefer",
            "auto",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["selected_candidate"]["filename"] == "rq7_auto_csv_fixture.example.csv"
    assert summary["selected_candidate"]["detected_columns"]["corpus"] == "corpus_guess"
    assert summary["selected_candidate"]["detected_columns"]["unit"] == "unit_id"
    assert summary["selected_candidate"]["detected_columns"]["text"] == "chunk_text"


def test_rq7_candidate_select_fails_when_preferred_candidate_missing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_rq7_candidate.py"),
            "--root",
            str(ROOT / "02_input"),
            "--prefer",
            "definitely_missing_candidate",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "PREFERRED_CANDIDATE_NOT_FOUND" in result.stderr or "PREFERRED_CANDIDATE_NOT_FOUND" in result.stdout
