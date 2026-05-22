from pathlib import Path


def test_rq7_vector_baseline_report_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Vector Baseline Report" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.csv" in text
    assert "VECTOR_GLOBAL" in text
    assert "CTHC_PRUNED_VECTOR" in text


def test_rq7_vector_baseline_report_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Vector Baseline Report" in text
    assert "RQ7_VECTOR_BASELINE_REPORT.md" in text
    assert "Local deterministic vector-style baseline only." in text
    assert "No external embedding API." in text
    assert "Hybrid ranking is not included yet." in text


def test_rq7_vector_baseline_report_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## RQ7 Vector Baseline Report" in text
    assert "RQ7_VECTOR_BASELINE_REPORT.csv" in text
    assert "Not a state-of-the-art vector search engine." in text
    assert "Not a production vector database benchmark." in text
    assert "build_rq7_vector_baseline_report.py" in text
