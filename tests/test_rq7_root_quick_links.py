from pathlib import Path


def test_root_readme_has_rq7_quick_links() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "[RQ7 Key Findings and Metrics](examples/hsrag_law/rq7_scale/RQ7_KEY_FINDINGS_AND_METRICS.md)" in text
    assert "[RQ7 Evidence Summary](examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md)" in text
    assert "LLM boundary" in text
    assert "RQ7 artifact map" in text
