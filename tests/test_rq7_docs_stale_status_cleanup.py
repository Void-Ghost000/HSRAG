from pathlib import Path


DOCS = [
    Path("README.md"),
    Path("examples/hsrag_law/README.md"),
    Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md"),
]


def test_rq7_readmes_do_not_claim_vector_hybrid_pending_anymore() -> None:
    stale_phrases = [
        "vector / hybrid baselines pending",
        "Vector / hybrid baselines pending",
        "Vector / hybrid baselines are still pending.",
        "Hybrid ranking is not included yet.",
    ]

    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for phrase in stale_phrases:
            assert phrase not in text, f"{path} still contains stale phrase: {phrase}"


def test_rq7_readmes_state_current_baseline_status() -> None:
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        has_current_baseline_status = (
            "local deterministic vector / hybrid baselines" in text
            or "Local deterministic vector and hybrid baselines are implemented" in text
        )

        assert has_current_baseline_status
        assert "production embedding / vector database" in text


def test_rq7_key_findings_markdown_scope_is_clean() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_KEY_FINDINGS_AND_METRICS.md").read_text(encoding="utf-8")

    assert "# RQ7 Key Findings and Metrics" in text
    assert "RQ7 does **not** call an LLM." in text
    assert "RQ7 does **not** evaluate LLM reasoning." in text
    assert "RQ7 does **not** evaluate generated answer quality." in text
    assert "Hash-Structured RAG with deterministic addressing" in text

