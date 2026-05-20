from pathlib import Path


def test_rq7_evidence_summary_exists_and_states_current_boundary() -> None:
    path = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md")
    text = path.read_text(encoding="utf-8")

    assert "# RQ7 Evidence Summary" in text
    assert "Level 2A+" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py" in text
    assert "python -m pytest tests -k rq7" in text
    assert "salted-domain gate: verified" in text
    assert "query-class metrics: available" in text
    assert "one-command verify: available" in text
    assert "full-scale RQ7 benchmark completion" in text
    assert "Official RQ4 corpus is not connected yet" in text
    assert "RQ7.3 — Real Corpus Connection" in text
