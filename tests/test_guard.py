"""
Tests for HSRAG conservative route guard.

These tests align with RQ5.5 / RQ6:
- no expected labels are needed
- stable identifiers may route
- unavailable domains are blocked
- ambiguous generic queries are not allowed
- conflict-form cross-corpus queries are blocked
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hsrag.guard import (
    RESULT_AMBIGUOUS,
    RESULT_HIT,
    RESULT_NO_EVIDENCE,
    RESULT_ROUTE_CONFLICT,
    ROUTE_BLOCK_AMBIGUOUS,
    ROUTE_BLOCK_CONFLICT,
    ROUTE_BLOCK_UNSUPPORTED,
    ROUTE_ROUTABLE,
    classify_query_to_cthc_route,
    evaluate_gate,
)
from hsrag.hash_router import route_key_for_corpus


def test_single_stable_identifier_routes_when_domain_available() -> None:
    available = {route_key_for_corpus(corpus_id="EU_AI_ACT")}

    decision = evaluate_gate(
        "Find EU AI Act Article 5 prohibited AI practices.",
        available_domain_hashes=available,
    )

    assert decision.status == RESULT_HIT
    assert decision.route is not None
    assert decision.route.status == ROUTE_ROUTABLE
    assert decision.route.code is not None
    assert decision.route.code.corpus_id == "EU_AI_ACT"


def test_stable_identifier_blocks_when_domain_unavailable() -> None:
    available = {route_key_for_corpus(corpus_id="EU_DMA")}

    decision = evaluate_gate(
        "Find EU AI Act Article 5 prohibited AI practices.",
        available_domain_hashes=available,
    )

    assert decision.status == RESULT_NO_EVIDENCE
    assert decision.route is not None
    assert decision.route.status == ROUTE_BLOCK_UNSUPPORTED


def test_generic_ambiguous_query_is_not_allowed() -> None:
    decision = evaluate_gate(
        "What does the platform law say about online services and providers?",
        available_domain_hashes=set(),
    )

    assert decision.status == RESULT_AMBIGUOUS
    assert decision.route is not None
    assert decision.route.status == ROUTE_BLOCK_AMBIGUOUS


def test_conflict_query_is_route_conflict() -> None:
    available = {
        route_key_for_corpus(corpus_id="EU_AI_ACT"),
        route_key_for_corpus(corpus_id="US_FTC_ACT5"),
    }

    decision = evaluate_gate(
        "Compare EU AI Act Article 5 with U.S. FTC Act Section 5.",
        available_domain_hashes=available,
    )

    assert decision.status == RESULT_ROUTE_CONFLICT
    assert decision.route is not None
    assert decision.route.status == ROUTE_BLOCK_CONFLICT
    assert "EU_AI_ACT" in decision.route.detected_corpus_ids
    assert "US_FTC_ACT5" in decision.route.detected_corpus_ids


def test_unsupported_topic_is_no_evidence() -> None:
    decision = evaluate_gate(
        "What does Canada's PIPEDA require for private-sector privacy breach reporting?",
        available_domain_hashes=set(),
    )

    assert decision.status == RESULT_NO_EVIDENCE
    assert decision.route is not None
    assert decision.route.status == ROUTE_BLOCK_UNSUPPORTED


def test_route_classification_can_run_without_availability_gate() -> None:
    route = classify_query_to_cthc_route(
        "Under 47 U.S.C. 230, what rule is described?",
        available_domain_hashes=None,
    )

    assert route.status == ROUTE_ROUTABLE
    assert route.code is not None
    assert route.code.corpus_id == "US_CDA230"
    assert route.domain_hash is not None