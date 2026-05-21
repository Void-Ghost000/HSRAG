from pathlib import Path


def test_rq7_release_checkpoint_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Release Checkpoint" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.json" in text
    assert "Full-scale benchmark pending" in text
    assert "Unit derivation remains heuristic" in text


def test_rq7_release_checkpoint_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Release Checkpoint" in text
    assert "RQ7_RELEASE_CHECKPOINT.md" in text
    assert "RQ7_PUBLIC_REPORT.md" in text
    assert "Vector / hybrid baselines pending" in text
    assert "Not legal advice" in text


def test_rq7_release_checkpoint_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## RQ7 Release Checkpoint" in text
    assert "RQ7_RELEASE_CHECKPOINT.md" in text
    assert "RQ7_RELEASE_CHECKPOINT.json" in text
    assert "RQ4 rebuilt 889-chunk artifact connected" in text
    assert "Actual elapsed timing available" in text
