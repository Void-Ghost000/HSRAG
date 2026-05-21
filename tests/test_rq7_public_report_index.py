from pathlib import Path


def test_rq7_public_report_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Public Report" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json" in text
    assert "verify_rq7_release.py --tiers 100,300,600,889" in text
    assert "full-scale benchmark pending" in text
    assert "unit derivation remains heuristic" in text


def test_rq7_public_report_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Public Report" in text
    assert "rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md" in text
    assert "rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json" in text
    assert "RQ4 rebuilt artifact is connected locally" in text
    assert "This is not a full-scale benchmark" in text
    assert "This is not legal advice" in text


def test_rq7_public_report_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## Published Public Report" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json" in text
    assert "scale tiers: 100 / 300 / 600 / 889" in text
    assert "actual elapsed timing" in text
    assert "verify_rq7_release.py --tiers 100,300,600,889" in text
