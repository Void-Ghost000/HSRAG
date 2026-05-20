from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_adapter_verify_matrix_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_adapters.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["all_passed"] is True
    assert summary["adapter_count"] == 3
    assert summary["claim_boundary"]["local_adapter_matrix_only"] is True
    assert summary["claim_boundary"]["official_rq4_corpus_connected"] is False

    adapters = {item["adapter"]: item for item in summary["adapter_results"]}

    assert set(adapters) == {"txt_manifest", "fixed_csv", "auto_csv"}

    for adapter_name, result_item in adapters.items():
        assert result_item["passed"] is True
        assert result_item["required_artifacts_exist"] is True
        assert result_item["acceptance_passed"] is True
        assert result_item["latest_report_is_clean"] is True
        assert Path(result_item["registry"]).exists()

        runner = result_item["runner"]
        assert runner["status"] == "OK"
        assert runner["passed"] is True
        assert runner["salted_domain_gate"] is True
        assert runner["latest_report"] is None
        assert Path(runner["metrics_by_query_class"]).exists()


def test_rq7_adapter_verify_writes_summary_files() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_rq7_adapters.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    verify_id = summary["verify_id"]
    verify_dir = ROOT / "04_runs" / verify_id

    summary_json = verify_dir / "rq7_adapter_verify_summary.json"
    summary_txt = verify_dir / "rq7_adapter_verify_summary.txt"

    assert summary_json.exists()
    assert summary_txt.exists()

    text = summary_txt.read_text(encoding="utf-8")
    assert "txt_manifest: PASS" in text
    assert "fixed_csv: PASS" in text
    assert "auto_csv: PASS" in text
    assert "official_rq4_corpus_connected: false" in text
