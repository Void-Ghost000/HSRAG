from pathlib import Path


KEY_FINDINGS = Path("examples/hsrag_law/rq7_scale/RQ7_KEY_FINDINGS_AND_METRICS.md")


def test_rq7_key_findings_doc_exists_and_has_scope() -> None:
    text = KEY_FINDINGS.read_text(encoding="utf-8")

    assert "# RQ7 Key Findings and Metrics" in text
    assert "Hash-Structured RAG with deterministic addressing" in text
    assert "RQ7 does **not** call an LLM." in text
    assert "does **not** evaluate LLM reasoning" in text
    assert "does **not** evaluate generated answer quality" in text
    assert "candidate_reduction_ratio" in text
    assert "actual_elapsed_p99_ms" in text
    assert "estimated_token_cost_usd_per_1k_queries" in text
    assert "ESI means Evidence Support Index" in text
    assert "Synthetic 10k scale equals real-law 10k corpus scale" in text


def test_rq7_scope_and_key_findings_indexed() -> None:
    for path in [
        Path("README.md"),
        Path("examples/hsrag_law/README.md"),
        Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md"),
    ]:
        text = path.read_text(encoding="utf-8")

        assert "## RQ7 Scope and Key Findings" in text
        assert "Hash-Structured RAG with deterministic addressing" in text
        assert "does **not** call an LLM" in text
        assert "RQ7_KEY_FINDINGS_AND_METRICS.md" in text


def test_rq7_evidence_summary_no_longer_claims_vector_hybrid_missing() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "Local deterministic vector and hybrid baselines are implemented" in text
    assert "external embedding APIs and production vector database benchmarks are not implemented" in text
    assert "Real-law full-scale RQ7 benchmark is pending; synthetic scale-stress benchmark is available." in text
