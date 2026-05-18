"""
HSRAG audit-chain helpers.

QSVCS scope:
- I / Intent:
  Build and verify append-only audit chains for retrieval and benchmark events.
- V / Validation:
  Tampering with event payload or previous_hash must fail verification.
- O / Operation:
  Each event hash is computed from index, event_type, payload, previous_hash.
- P / Postcondition:
  verify_audit_chain(events) returns True only for a complete chain.
- F / Feedback:
  Keep this small and deterministic; benchmark scripts can build richer payloads.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, List

from .hashing import hash_json
from .types import AuditEvent


GENESIS_HASH = "GENESIS"


def make_audit_event(
    *,
    index: int,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str,
) -> AuditEvent:
    """Create one deterministic audit event."""

    event_payload = {
        "index": index,
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
    }

    return AuditEvent(
        index=index,
        event_type=event_type,
        payload=payload,
        previous_hash=previous_hash,
        event_hash=hash_json(event_payload),
    )


def build_audit_chain(events: Iterable[tuple[str, dict[str, Any]]]) -> List[AuditEvent]:
    """Build an append-only audit chain from event payloads."""

    out: List[AuditEvent] = []
    previous = GENESIS_HASH

    for index, (event_type, payload) in enumerate(events):
        event = make_audit_event(
            index=index,
            event_type=event_type,
            payload=payload,
            previous_hash=previous,
        )
        out.append(event)
        previous = event.event_hash

    return out


def verify_audit_chain(events: Iterable[AuditEvent]) -> bool:
    """Verify event order, previous hash linkage, and event hash integrity."""

    previous = GENESIS_HASH

    for event in events:
        if event.previous_hash != previous:
            return False

        expected = make_audit_event(
            index=event.index,
            event_type=event.event_type,
            payload=event.payload,
            previous_hash=event.previous_hash,
        )

        if expected.event_hash != event.event_hash:
            return False

        previous = event.event_hash

    return True


def audit_events_as_dicts(events: Iterable[AuditEvent]) -> list[dict[str, Any]]:
    """Serialize audit events for JSON / JSONL output."""

    return [asdict(event) for event in events]