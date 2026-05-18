"""
Tests for HSRAG audit-chain primitives.

These tests align with the RQ1-RQ6 audit-chain pattern:
GENESIS -> event hash -> next event hash.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hsrag.audit_chain import build_audit_chain, verify_audit_chain
from hsrag.types import AuditEvent


def test_audit_chain_verifies_complete_chain() -> None:
    events = build_audit_chain(
        [
            ("CONFIG", {"rq": "RQ6", "seed": 20260517}),
            ("RESULT", {"decision": "PASS"}),
        ]
    )

    assert len(events) == 2
    assert verify_audit_chain(events) is True


def test_audit_chain_detects_payload_tampering() -> None:
    events = build_audit_chain(
        [
            ("CONFIG", {"rq": "RQ6", "seed": 20260517}),
            ("RESULT", {"decision": "PASS"}),
        ]
    )

    tampered = [
        events[0],
        AuditEvent(
            index=events[1].index,
            event_type=events[1].event_type,
            payload={"decision": "FAIL"},
            previous_hash=events[1].previous_hash,
            event_hash=events[1].event_hash,
        ),
    ]

    assert verify_audit_chain(tampered) is False


def test_audit_chain_detects_previous_hash_tampering() -> None:
    events = build_audit_chain(
        [
            ("CONFIG", {"rq": "RQ6"}),
            ("RESULT", {"decision": "PASS"}),
        ]
    )

    tampered = [
        events[0],
        AuditEvent(
            index=events[1].index,
            event_type=events[1].event_type,
            payload=events[1].payload,
            previous_hash="WRONG_PREVIOUS_HASH",
            event_hash=events[1].event_hash,
        ),
    ]

    assert verify_audit_chain(tampered) is False