from pathlib import Path


def test_rq7_evidence_summary_mentions_rq4_snapshot_and_boundaries() -> None:
    path = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md")
    text = path.read_text(encoding="utf-8")

    assert "# RQ7 Evidence Summary" in text
    assert "Level 2B-pre" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py" in text
    assert "RQ4 rebuilt artifact verify: available" in text
    assert "RQ4 metrics snapshot: available" in text
    assert "examples/hsrag_law/results/rq4_rebuilt_chunks.csv" in text
    assert "Unit derivation is heuristic" in text
    assert "full-scale RQ7 benchmark completion" in text
    assert "Local deterministic vector and hybrid baselines are implemented" in text
    assert "external embedding APIs and production vector database benchmarks are not implemented" in text
    assert "RQ7.14 — Real Scale Tier Runner" in text

