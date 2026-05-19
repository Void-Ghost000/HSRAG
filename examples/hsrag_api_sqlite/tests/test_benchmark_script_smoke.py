from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_benchmark_script_smoke(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "scripts" / "benchmark_local_lookup.py"
    output = tmp_path / "local_lookup_report.json"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--runs",
            "20",
            "--dataset-size",
            "10",
            "--output",
            str(output),
        ],
        cwd=str(project_root),
        text=True,
        capture_output=True,
        check=True,
    )

    assert output.exists(), result.stdout + result.stderr

    report = json.loads(output.read_text(encoding="utf-8"))

    assert report["scope"]["local_only"] is True
    assert report["scope"]["zero_secret"] is True
    assert report["scope"]["zero_network"] is True

    assert report["cost_profile"]["api_key_required"] is False
    assert report["cost_profile"]["network_calls"] == 0
    assert report["cost_profile"]["llm_calls_required"] == 0

    assert "cthc_hash_lookup" in report["results"]
    assert "method_path_lookup" in report["results"]
    assert "semantic_discovery_like_lookup" in report["results"]

    assert "p99_ms" in report["results"]["cthc_hash_lookup"]
