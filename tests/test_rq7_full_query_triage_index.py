from pathlib import Path


def test_rq7_full_query_triage_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Triage" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.json" in text
    assert "EXPECTED_GUARD_BLOCK" in text
    assert "FALSE_ALLOW_RISK" in text
    assert "build_rq7_full_query_triage.py" in text


def test_rq7_full_query_triage_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Triage" in text
    assert "RQ7_FULL_QUERY_TRIAGE.md" in text
    assert "Triage is diagnostic-only." in text
    assert "Vector / hybrid baselines are still pending." in text
    assert "This does not provide legal advice." in text


def test_rq7_full_query_triage_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## RQ7 Full Query Triage" in text
    assert "RQ7_FULL_QUERY_TRIAGE.json" in text
    assert "Acceptance failure is allowed for diagnostics." in text
    assert "Full-scale benchmark is still pending." in text
