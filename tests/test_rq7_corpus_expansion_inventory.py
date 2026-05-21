from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")


def test_rq7_corpus_expansion_inventory_builds() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_corpus_expansion_inventory.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["artifact_count"] > 0
    assert summary["claim_boundary"]["inventory_only"] is True
    assert summary["claim_boundary"]["does_not_expand_corpus"] is True
    assert summary["claim_boundary"]["full_scale_benchmark"] is False
    assert "kind_summary" in summary
    assert "text_corpus_candidate_count" in summary


def test_rq7_corpus_expansion_inventory_writes_reports() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_corpus_expansion_inventory.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output_json = ROOT / "05_reports" / "RQ7_CORPUS_EXPANSION_INVENTORY.json"
    output_md = ROOT / "05_reports" / "RQ7_CORPUS_EXPANSION_INVENTORY.md"

    assert output_json.exists()
    assert output_md.exists()

    text = output_md.read_text(encoding="utf-8")
    assert "# RQ7 Corpus Expansion Inventory" in text
    assert "inventory_only: true" in text
    assert "full_scale_benchmark: false" in text


def test_rq7_corpus_expansion_inventory_rejects_missing_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_rq7_corpus_expansion_inventory.py"),
            "--root",
            str(tmp_path / "missing"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "ROOT_NOT_FOUND" in result.stderr or "ROOT_NOT_FOUND" in result.stdout
