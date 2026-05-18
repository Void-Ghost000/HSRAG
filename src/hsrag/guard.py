"""
HSRAG conservative route guard.

QSVCS scope:
- I / Intent:
  Convert CTHC scope detection into bounded retrieval decisions.
- V / Validation:
  Do not read expected_corpus, expected_jurisdiction, case_type, or answer keys.
  Only query text and available salted domain hashes may be used.
- O / Operation:
  conflict -> unsupported -> ambiguous -> routable -> no evidence
- P / Postcondition:
  A query receives one of:
  HIT, NO_EVIDENCE, AMBIGUOUS, ROUTE_CONFLICT.
- F / Feedback:
  This module is aligned with RQ5.5 conservative routing and RQ6 route statuses.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from .cthc import (
    conflict_query_signal,
    contains_unsupported_topic,
    detect_route_openers,
    generic_ambiguous_signal,
)
from .hash_router import default_cthc_code, salted_domain_hash
from .types import CTHCRoute, GateDecision


ROUTE_ROUTABLE = "ROUTABLE"
ROUTE_BLOCK_CONFLICT = "BLOCK_CONFLICT_QUERY"
ROUTE_BLOCK_UNSUPPORTED = "BLOCK_UNSUPPORTED_QUERY"
ROUTE_BLOCK_AMBIGUOUS = "BLOCK_AMBIGUOUS_QUERY"

RESULT_HIT = "HIT"
RESULT_NO_EVIDENCE = "NO_EVIDENCE"
RESULT_AMBIGUOUS = "AMBIGUOUS"
RESULT_ROUTE_CONFLICT = "ROUTE_CONFLICT"


def _domain_hash_set(
    available_domain_hashes: Collection[str] | Mapping[str, Any] | None,
) -> set[str] | None:
    """Normalize available domain hashes into a set.

    None means "do not enforce local domain availability".
    This is useful for unit tests or pure route classification.
    """

    if available_domain_hashes is None:
        return None

    if isinstance(available_domain_hashes, Mapping):
        return set(available_domain_hashes.keys())

    return set(available_domain_hashes)


def classify_query_to_cthc_route(
    query: str,
    available_domain_hashes: Collection[str] | Mapping[str, Any] | None = None,
) -> CTHCRoute:
    """Classify a query into a CTHC route.

    This function intentionally mirrors the RQ5.5 design principle:

    - stable legal identifiers may open a route
    - generic legal words cannot open a route
    - conflict-form queries are blocked before retrieval
    - unsupported topics are blocked before retrieval
    - local corpus availability is checked via salted domain hash
    """

    detected = tuple(detect_route_openers(query))
    available_hashes = _domain_hash_set(available_domain_hashes)

    if conflict_query_signal(query, detected):
        return CTHCRoute(
            status=ROUTE_BLOCK_CONFLICT,
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Conflict-form query detected before routing.",
            detected_corpus_ids=detected,
        )

    if contains_unsupported_topic(query):
        return CTHCRoute(
            status=ROUTE_BLOCK_UNSUPPORTED,
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Unsupported legal topic outside local corpus.",
            detected_corpus_ids=detected,
        )

    if not detected and generic_ambiguous_signal(query):
        return CTHCRoute(
            status=ROUTE_BLOCK_AMBIGUOUS,
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Generic legal query without stable CTHC identifier.",
            detected_corpus_ids=(),
        )

    if len(detected) == 1:
        corpus_id = detected[0]
        code = default_cthc_code(corpus_id=corpus_id)
        domain_hash = salted_domain_hash(code)

        if available_hashes is not None and domain_hash not in available_hashes:
            return CTHCRoute(
                status=ROUTE_BLOCK_UNSUPPORTED,
                code=None,
                domain_hash=None,
                confidence="HIGH",
                reason="CTHC route exists but salted domain is unavailable in local corpus.",
                detected_corpus_ids=detected,
            )

        return CTHCRoute(
            status=ROUTE_ROUTABLE,
            code=code,
            domain_hash=domain_hash,
            confidence="HIGH",
            reason="Stable CTHC legal identifier detected.",
            detected_corpus_ids=detected,
        )

    if len(detected) > 1:
        return CTHCRoute(
            status=ROUTE_BLOCK_CONFLICT,
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Multiple stable CTHC identifiers detected.",
            detected_corpus_ids=detected,
        )

    return CTHCRoute(
        status=ROUTE_BLOCK_UNSUPPORTED,
        code=None,
        domain_hash=None,
        confidence="LOW",
        reason="No stable CTHC legal identifier found.",
        detected_corpus_ids=(),
    )


def route_status_to_result_status(route_status: str) -> str:
    """Map internal route status to RQ6-compatible result status."""

    if route_status == ROUTE_ROUTABLE:
        return RESULT_HIT

    if route_status == ROUTE_BLOCK_CONFLICT:
        return RESULT_ROUTE_CONFLICT

    if route_status == ROUTE_BLOCK_AMBIGUOUS:
        return RESULT_AMBIGUOUS

    return RESULT_NO_EVIDENCE


def evaluate_gate(
    query: str,
    available_domain_hashes: Collection[str] | Mapping[str, Any] | None = None,
) -> GateDecision:
    """Evaluate a query and return a conservative retrieval gate decision."""

    route = classify_query_to_cthc_route(
        query=query,
        available_domain_hashes=available_domain_hashes,
    )

    return GateDecision(
        status=route_status_to_result_status(route.status),
        reason=route.reason,
        route=route,
    )