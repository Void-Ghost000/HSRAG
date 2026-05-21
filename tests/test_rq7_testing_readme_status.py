from pathlib import Path


def test_rq7_testing_readme_mentions_rq4_snapshot_and_master_verify() -> None:
    path = Path("examples/hsrag_law/rq7_scale/README_TESTING.md")
    text = path.read_text(encoding="utf-8")

    assert "Master verify command:" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py" in text
    assert "RQ4 metrics snapshot command:" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/snapshot_rq7_rq4_metrics.py" in text
    assert "rq4_metrics_snapshot_available: true" in text
    assert "unit_derivation_is_heuristic: true" in text
    assert "Full-scale RQ7 benchmark: not implemented yet." in text
