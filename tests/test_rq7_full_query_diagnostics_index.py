from pathlib import Path


def test_rq7_full_query_diagnostics_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Diagnostics" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.json" in text
    assert "Acceptance failure is allowed for diagnostics." in text
    assert "publish_rq7_full_query_diagnostics.py" in text


def test_rq7_full_query_diagnostics_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Diagnostics" in text
    assert "RQ7_FULL_QUERY_DIAGNOSTICS.md" in text
    assert "Full query expansion is diagnostic-only." in text
    assert "Vector / hybrid baselines are still pending." in text


def test_rq7_full_query_diagnostics_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Diagnostics" in text
    assert "RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json" in text
    assert "Full-scale benchmark is still pending." in text
    assert "analyze_rq7_full_query_diagnostics.py" in text
