from __future__ import annotations

import csv
import hashlib
import hmac
import json
import re
import sqlite3
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

POC_VERSION = "HSRAG_PERSONAL_MEMORY_POINTER_V01X_LOCAL_REPRO_PACK"

BASE = Path("examples/hsrag_memory_pointer_v01x")
OUT = BASE / "outputs"
REPORT = BASE / "V01X_LOCAL_REPRO_REPORT.md"
README = BASE / "README.md"
README_TESTING = BASE / "README_TESTING.md"
ROOT_README = Path("README.md")
DB_PATH = OUT / "v01x_local_repro.sqlite3"

N_LIST = [1000, 10000, 50000, 100000]
TEXT_LEN_LIST = [50, 300, 1000, 3000]

N_INITIAL = 100000
N_UPDATE = 5000
N_DELETE = 3000
N_CHECK = 3000
BUCKET_COUNT = 192
PURPOSE = "recommendation"

# Public deterministic benchmark key.
# This is NOT a production secret.
BENCHMARK_KEY = b"HSRAG_V01X_PUBLIC_REPRO_BENCHMARK_KEY_NOT_SECRET"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


RUN_CREATED_AT_UTC = utc_now()


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hmac_hex(s: str, n: int = 32) -> str:
    return hmac.new(BENCHMARK_KEY, s.encode("utf-8"), hashlib.sha256).hexdigest()[:n]


def json_len(obj: Dict[str, Any]) -> int:
    return len(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def bucket_for(memory_id: str) -> int:
    return int(hashlib.sha256(memory_id.encode("utf-8")).hexdigest()[:8], 16) % BUCKET_COUNT


def tier_for(i: int) -> str:
    if i % 10 == 0:
        return "FHS"
    if i % 3 == 0:
        return "EHS"
    return "CHS"


def sensitivity_for(tier: str, i: int) -> str:
    if tier == "FHS":
        return "high"
    if tier == "CHS" and i % 7 == 0:
        return "medium"
    return "low"


def make_pointer(
    user_id: str,
    memory_id: str,
    tier: str,
    bucket: int,
    epoch: int,
    version: int,
    purpose: str,
) -> Tuple[str, str]:
    material = (
        f"user={user_id}|mem={memory_id}|tier={tier}|bucket={bucket}|"
        f"epoch={epoch}|version={version}|purpose={purpose}"
    )
    digest = hmac_hex(material, 32)
    uri = f"pmem://{user_id}/b{bucket:03d}/{memory_id}/v{version}/e{epoch}/{purpose}"
    return uri, digest


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def distribution_counts(n: int) -> Dict[Tuple[str, str], int]:
    counts: Dict[Tuple[str, str], int] = {}
    for i in range(n):
        tier = tier_for(i)
        sensitivity = sensitivity_for(tier, i)
        key = (tier, sensitivity)
        counts[key] = counts.get(key, 0) + 1
    return counts


def size_templates(text_len: int) -> Dict[Tuple[str, str], Dict[str, int]]:
    mid = "m000000"
    pointer_uri = "pmem://u/b000/m000000/v1/e1/recommendation"
    digest = "a" * 32

    templates: Dict[Tuple[str, str], Dict[str, int]] = {}

    for tier in ["FHS", "CHS", "EHS"]:
        for sensitivity in ["high", "medium", "low"]:
            full = {
                "memory_id": mid,
                "tier": tier,
                "sensitivity": sensitivity,
                "tags": ["synthetic", tier.lower(), sensitivity],
                "source_type": "synthetic_personal_memory",
                "source_hash": "s" * 64,
                "created_at_utc": "2026-05-21T00:00:00Z",
                "text": "",
            }
            verbose = {
                "pointer": pointer_uri,
                "pointer_hmac": digest,
                "tier": tier,
                "sensitivity": sensitivity,
                "scope": "recommendation_only",
                "bucket": 0,
                "epoch": 1,
            }
            compact = {
                "p": pointer_uri,
                "h": digest,
                "t": tier,
            }
            ultra = {
                "h": digest,
            }

            templates[(tier, sensitivity)] = {
                "FULL_TEXT": json_len(full) + text_len,
                "VERBOSE_POINTER": json_len(verbose),
                "COMPACT_POINTER": json_len(compact),
                "ULTRA_POINTER": json_len(ultra),
            }

    return templates


def run_scale_compression() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    stability_rows: List[Dict[str, Any]] = []

    for text_len in TEXT_LEN_LIST:
        templates = size_templates(text_len)

        for n in N_LIST:
            counts = distribution_counts(n)
            totals = {
                "FULL_TEXT": 0,
                "VERBOSE_POINTER": 0,
                "COMPACT_POINTER": 0,
                "ULTRA_POINTER": 0,
            }
            high_sensitive_count = 0

            for key, count in counts.items():
                if key[1] == "high":
                    high_sensitive_count += count
                for mode in totals:
                    totals[mode] += templates[key][mode] * count

            full_size = totals["FULL_TEXT"]

            for mode, size in totals.items():
                reduction = 0.0 if mode == "FULL_TEXT" else round((1.0 - size / full_size) * 100.0, 4)
                rows.append(
                    {
                        "n_memories": n,
                        "avg_text_chars": text_len,
                        "mode": mode,
                        "edge_storage_bytes": size,
                        "bytes_per_memory": round(size / n, 4),
                        "reduction_vs_full_pct": reduction,
                        "high_sensitive_count": high_sensitive_count,
                    }
                )

    for text_len in TEXT_LEN_LIST:
        for mode in ["VERBOSE_POINTER", "COMPACT_POINTER", "ULTRA_POINTER"]:
            values = [
                float(r["reduction_vs_full_pct"])
                for r in rows
                if r["avg_text_chars"] == text_len and r["mode"] == mode
            ]
            stability_rows.append(
                {
                    "avg_text_chars": text_len,
                    "mode": mode,
                    "reduction_mean_pct": round(statistics.mean(values), 4),
                    "reduction_std_pct": round(statistics.pstdev(values), 6),
                    "reduction_min_pct": round(min(values), 4),
                    "reduction_max_pct": round(max(values), 4),
                    "strict_scale_stability_pass": statistics.pstdev(values) < 0.1,
                }
            )

    return rows, stability_rows


class AuditChain:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        self.prev_hash = "GENESIS"

    def append(self, event_type: str, payload: Dict[str, Any]) -> None:
        seq = len(self.events)
        event_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        event_hash = sha256_hex(f"{seq}|{self.prev_hash}|{event_type}|{event_json}")
        self.events.append(
            {
                "seq": seq,
                "event_type": event_type,
                "event_json": event_json,
                "prev_hash": self.prev_hash,
                "event_hash": event_hash,
            }
        )
        self.prev_hash = event_hash

    @staticmethod
    def verify(events: List[Dict[str, Any]]) -> Tuple[bool, str | None]:
        prev_hash = "GENESIS"
        for event in events:
            expected = sha256_hex(
                f"{event['seq']}|{prev_hash}|{event['event_type']}|{event['event_json']}"
            )
            if expected != event["event_hash"]:
                return False, "EVENT_HASH_MISMATCH"
            prev_hash = event["event_hash"]
        return True, None


def init_db() -> sqlite3.Connection:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")

    conn.executescript(
        """
        CREATE TABLE memories(
            memory_id TEXT PRIMARY KEY,
            tier TEXT NOT NULL,
            sensitivity TEXT NOT NULL,
            bucket INTEGER NOT NULL,
            epoch INTEGER NOT NULL,
            version INTEGER NOT NULL,
            active INTEGER NOT NULL,
            text_len INTEGER NOT NULL,
            updated_at_utc TEXT NOT NULL
        );

        CREATE TABLE pointer_index(
            pointer_hmac TEXT PRIMARY KEY,
            pointer_uri TEXT NOT NULL,
            memory_id TEXT NOT NULL,
            tier TEXT NOT NULL,
            purpose TEXT NOT NULL,
            bucket INTEGER NOT NULL,
            epoch INTEGER NOT NULL,
            version INTEGER NOT NULL
        );

        CREATE TABLE revoked_pointers(
            pointer_hmac TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            revoked_at_utc TEXT NOT NULL
        );

        CREATE TABLE tombstones(
            memory_id TEXT PRIMARY KEY,
            deleted_at_utc TEXT NOT NULL,
            reason TEXT NOT NULL
        );

        CREATE TABLE bucket_epochs(
            bucket INTEGER PRIMARY KEY,
            epoch INTEGER NOT NULL
        );

        CREATE TABLE test_vectors(
            name TEXT PRIMARY KEY,
            pointer_hmac TEXT NOT NULL,
            expected_reason TEXT NOT NULL
        );

        CREATE TABLE audit_chain(
            seq INTEGER PRIMARY KEY,
            event_type TEXT NOT NULL,
            event_json TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            event_hash TEXT NOT NULL
        );
        """
    )

    return conn


def state_fingerprint(conn: sqlite3.Connection) -> str:
    counts = {}

    for table in [
        "memories",
        "pointer_index",
        "revoked_pointers",
        "tombstones",
        "bucket_epochs",
        "test_vectors",
        "audit_chain",
    ]:
        counts[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]

    counts["active_memories"] = conn.execute(
        "SELECT COUNT(*) AS c FROM memories WHERE active=1"
    ).fetchone()["c"]

    return sha256_hex(json.dumps(counts, sort_keys=True))


def resolve(
    conn: sqlite3.Connection,
    pointer_hmac: str,
    requested_purpose: str = PURPOSE,
    claimed_tier: str | None = None,
) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM pointer_index WHERE pointer_hmac=?",
        (pointer_hmac,),
    ).fetchone()

    if row:
        if requested_purpose != row["purpose"]:
            return {
                "status": "DENY",
                "reason_code": "PURPOSE_MISMATCH",
                "retryable": False,
                "data": None,
                "errors": [],
                "warnings": [],
            }

        if claimed_tier is not None and claimed_tier != row["tier"]:
            return {
                "status": "DENY",
                "reason_code": "TIER_MISMATCH",
                "retryable": False,
                "data": None,
                "errors": [],
                "warnings": [],
            }

        return {
            "status": "ALLOW",
            "reason_code": "CURRENT_ACTIVE_POINTER",
            "retryable": False,
            "data": dict(row),
            "errors": [],
            "warnings": [],
        }

    revoked = conn.execute(
        "SELECT reason FROM revoked_pointers WHERE pointer_hmac=?",
        (pointer_hmac,),
    ).fetchone()

    if revoked:
        return {
            "status": "DENY",
            "reason_code": revoked["reason"],
            "retryable": False,
            "data": None,
            "errors": [],
            "warnings": [],
        }

    return {
        "status": "DENY",
        "reason_code": "UNKNOWN_POINTER",
        "retryable": False,
        "data": None,
        "errors": [],
        "warnings": [],
    }


def release_allowed(conn: sqlite3.Connection, memory_id: str) -> bool:
    row = conn.execute(
        "SELECT tier,sensitivity,active FROM memories WHERE memory_id=?",
        (memory_id,),
    ).fetchone()

    if not row or row["active"] != 1:
        return False

    if row["tier"] == "FHS" or row["sensitivity"] == "high":
        return False

    return True


def run_sqlite_lifecycle_repro() -> Dict[str, Any]:
    conn = init_db()
    audit = AuditChain()

    ts = RUN_CREATED_AT_UTC
    user_id = "demo_user"

    old_update_pointers: List[str] = []
    deleted_pointers: List[str] = []

    with conn:
        conn.executemany(
            "INSERT INTO bucket_epochs(bucket,epoch) VALUES (?,?)",
            [(b, 1) for b in range(BUCKET_COUNT)],
        )

        memory_rows = []
        pointer_rows = []

        for i in range(N_INITIAL):
            memory_id = f"m{i:06d}"
            tier = tier_for(i)
            sensitivity = sensitivity_for(tier, i)
            bucket = bucket_for(memory_id)
            uri, pointer_hmac = make_pointer(user_id, memory_id, tier, bucket, 1, 1, PURPOSE)

            memory_rows.append((memory_id, tier, sensitivity, bucket, 1, 1, 1, 300, ts))
            pointer_rows.append((pointer_hmac, uri, memory_id, tier, PURPOSE, bucket, 1, 1))

        conn.executemany(
            "INSERT INTO memories(memory_id,tier,sensitivity,bucket,epoch,version,active,text_len,updated_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
            memory_rows,
        )

        conn.executemany(
            "INSERT INTO pointer_index(pointer_hmac,pointer_uri,memory_id,tier,purpose,bucket,epoch,version) VALUES (?,?,?,?,?,?,?,?)",
            pointer_rows,
        )

        audit.append("INIT", {"n_initial": N_INITIAL, "bucket_count": BUCKET_COUNT})

        update_revokes = []
        update_deletes = []
        update_new_pointers = []
        update_memory_rows = []

        for i in range(N_UPDATE):
            memory_id = f"m{i:06d}"
            tier = tier_for(i)
            bucket = bucket_for(memory_id)

            _, old_hmac = make_pointer(user_id, memory_id, tier, bucket, 1, 1, PURPOSE)
            new_uri, new_hmac = make_pointer(user_id, memory_id, tier, bucket, 1, 2, PURPOSE)

            old_update_pointers.append(old_hmac)
            update_revokes.append((old_hmac, memory_id, "REVOKED_BY_UPDATE", ts))
            update_deletes.append((old_hmac,))
            update_new_pointers.append((new_hmac, new_uri, memory_id, tier, PURPOSE, bucket, 1, 2))
            update_memory_rows.append((2, ts, memory_id))

        conn.executemany(
            "INSERT OR IGNORE INTO revoked_pointers(pointer_hmac,memory_id,reason,revoked_at_utc) VALUES (?,?,?,?)",
            update_revokes,
        )
        conn.executemany("DELETE FROM pointer_index WHERE pointer_hmac=?", update_deletes)
        conn.executemany(
            "INSERT INTO pointer_index(pointer_hmac,pointer_uri,memory_id,tier,purpose,bucket,epoch,version) VALUES (?,?,?,?,?,?,?,?)",
            update_new_pointers,
        )
        conn.executemany(
            "UPDATE memories SET version=?,updated_at_utc=? WHERE memory_id=?",
            update_memory_rows,
        )

        audit.append("UPDATE", {"updated_count": N_UPDATE})

        delete_revokes = []
        delete_index_rows = []
        delete_memory_rows = []
        tombstone_rows = []

        for i in range(N_UPDATE, N_UPDATE + N_DELETE):
            memory_id = f"m{i:06d}"
            tier = tier_for(i)
            bucket = bucket_for(memory_id)

            _, old_hmac = make_pointer(user_id, memory_id, tier, bucket, 1, 1, PURPOSE)

            deleted_pointers.append(old_hmac)
            delete_revokes.append((old_hmac, memory_id, "REVOKED_BY_DELETE", ts))
            delete_index_rows.append((old_hmac,))
            delete_memory_rows.append((ts, memory_id))
            tombstone_rows.append((memory_id, ts, "USER_DELETE"))

        conn.executemany(
            "INSERT OR IGNORE INTO revoked_pointers(pointer_hmac,memory_id,reason,revoked_at_utc) VALUES (?,?,?,?)",
            delete_revokes,
        )
        conn.executemany("DELETE FROM pointer_index WHERE pointer_hmac=?", delete_index_rows)
        conn.executemany(
            "UPDATE memories SET active=0,updated_at_utc=? WHERE memory_id=?",
            delete_memory_rows,
        )
        conn.executemany(
            "INSERT INTO tombstones(memory_id,deleted_at_utc,reason) VALUES (?,?,?)",
            tombstone_rows,
        )

        audit.append("DELETE", {"deleted_count": N_DELETE})

        conn.execute("UPDATE bucket_epochs SET epoch=epoch+1")

        current_rows = conn.execute("SELECT * FROM pointer_index").fetchall()
        pre_rotation_pointers = [row["pointer_hmac"] for row in current_rows]

        rotation_revokes = []
        rotation_new_pointers = []
        rotation_memory_rows = []

        for row in current_rows:
            memory_id = row["memory_id"]
            tier = row["tier"]
            bucket = row["bucket"]
            version = row["version"]

            new_uri, new_hmac = make_pointer(user_id, memory_id, tier, bucket, 2, version, PURPOSE)

            rotation_revokes.append(
                (row["pointer_hmac"], memory_id, "REVOKED_BY_BUCKET_ROTATION", ts)
            )
            rotation_new_pointers.append(
                (new_hmac, new_uri, memory_id, tier, PURPOSE, bucket, 2, version)
            )
            rotation_memory_rows.append((2, ts, memory_id))

        conn.executemany(
            "INSERT OR IGNORE INTO revoked_pointers(pointer_hmac,memory_id,reason,revoked_at_utc) VALUES (?,?,?,?)",
            rotation_revokes,
        )
        conn.execute("DELETE FROM pointer_index")
        conn.executemany(
            "INSERT INTO pointer_index(pointer_hmac,pointer_uri,memory_id,tier,purpose,bucket,epoch,version) VALUES (?,?,?,?,?,?,?,?)",
            rotation_new_pointers,
        )
        conn.executemany(
            "UPDATE memories SET epoch=?,updated_at_utc=? WHERE memory_id=?",
            rotation_memory_rows,
        )

        audit.append("BUCKET_ROTATION", {"rotated_bucket_count": BUCKET_COUNT, "new_epoch": 2})

        active_current = [
            row["pointer_hmac"]
            for row in conn.execute(
                "SELECT pointer_hmac FROM pointer_index ORDER BY memory_id LIMIT ?",
                (N_CHECK,),
            ).fetchall()
        ]

        test_vectors = [
            ("current_valid_pointer_control", active_current[0], "CURRENT_ACTIVE_POINTER"),
            ("replay_updated_old_pointer", old_update_pointers[0], "REVOKED_BY_UPDATE"),
            ("replay_deleted_pointer", deleted_pointers[0], "REVOKED_BY_DELETE"),
            ("replay_pre_rotation_pointer", pre_rotation_pointers[0], "REVOKED_BY_BUCKET_ROTATION"),
            ("cross_purpose_training_export", active_current[1], "PURPOSE_MISMATCH"),
            ("forged_pointer_lookup", hmac_hex("forged-pointer-sample"), "UNKNOWN_POINTER"),
            ("tier_confusion_attempt", active_current[2], "TIER_MISMATCH"),
        ]

        conn.executemany(
            "INSERT INTO test_vectors(name,pointer_hmac,expected_reason) VALUES (?,?,?)",
            test_vectors,
        )

        audit.append("TEST_VECTORS", {"test_vector_count": len(test_vectors)})

        conn.executemany(
            "INSERT INTO audit_chain(seq,event_type,event_json,prev_hash,event_hash) VALUES (?,?,?,?,?)",
            [
                (
                    event["seq"],
                    event["event_type"],
                    event["event_json"],
                    event["prev_hash"],
                    event["event_hash"],
                )
                for event in audit.events
            ],
        )

    before_fingerprint = state_fingerprint(conn)

    audit_rows = [
        dict(row)
        for row in conn.execute("SELECT * FROM audit_chain ORDER BY seq").fetchall()
    ]

    audit_ok, _ = AuditChain.verify(audit_rows)

    tampered_rows = [dict(row) for row in audit_rows]
    tampered_rows[2]["event_json"] = tampered_rows[2]["event_json"] + "_tamper"
    tamper_ok, tamper_reason = AuditChain.verify(tampered_rows)

    conn.close()

    reload_conn = sqlite3.connect(DB_PATH)
    reload_conn.row_factory = sqlite3.Row

    after_fingerprint = state_fingerprint(reload_conn)

    current_samples = [
        row["pointer_hmac"]
        for row in reload_conn.execute(
            "SELECT pointer_hmac FROM pointer_index ORDER BY memory_id LIMIT ?",
            (N_CHECK,),
        ).fetchall()
    ]

    forged_samples = [hmac_hex(f"forged-{i}") for i in range(N_CHECK)]

    def eval_case(
        name: str,
        samples: List[str],
        expect_resolve: bool,
        purpose: str = PURPOSE,
        tier_mode: str | None = None,
    ) -> Dict[str, Any]:
        wrong_resolve = 0
        wrong_release = 0
        content_guard_blocked = 0
        structured = 0
        reasons: Dict[str, int] = {}

        for pointer_hmac in samples:
            claimed_tier = None

            if tier_mode == "wrong":
                row = reload_conn.execute(
                    "SELECT tier FROM pointer_index WHERE pointer_hmac=?",
                    (pointer_hmac,),
                ).fetchone()
                claimed_tier = "CHS" if row and row["tier"] != "CHS" else "FHS"

            result = resolve(reload_conn, pointer_hmac, purpose, claimed_tier)

            if result.get("reason_code"):
                structured += 1
                reasons[result["reason_code"]] = reasons.get(result["reason_code"], 0) + 1

            resolved = result["status"] == "ALLOW"

            if expect_resolve and not resolved:
                wrong_resolve += 1

            if (not expect_resolve) and resolved:
                wrong_resolve += 1

            if resolved and result["data"]:
                allowed = release_allowed(reload_conn, result["data"]["memory_id"])

                if expect_resolve and not allowed:
                    content_guard_blocked += 1

                if (not expect_resolve) and allowed:
                    wrong_release += 1

        checked = len(samples)

        return {
            "case": name,
            "checked": checked,
            "expect_resolve": expect_resolve,
            "wrong_resolve_count": wrong_resolve,
            "wrong_release_count": wrong_release,
            "content_guard_blocked_count": content_guard_blocked if expect_resolve else None,
            "reject_rate": None if expect_resolve else round(1.0 - wrong_resolve / checked, 6),
            "resolve_pass_rate": round(1.0 - wrong_resolve / checked, 6) if expect_resolve else None,
            "structured_reason_rate": round(structured / checked, 6),
            "top_reasons": json.dumps(reasons, sort_keys=True),
        }

    case_results = [
        eval_case("current_valid_pointer_control", current_samples, True),
        eval_case("replay_updated_old_pointer", old_update_pointers[:N_CHECK], False),
        eval_case("replay_deleted_pointer", deleted_pointers[:N_CHECK], False),
        eval_case("replay_pre_rotation_pointer", pre_rotation_pointers[:N_CHECK], False),
        eval_case("cross_purpose_training_export", current_samples, False, purpose="training_export"),
        eval_case("forged_pointer_lookup", forged_samples, False),
        eval_case("tier_confusion_attempt", current_samples, False, tier_mode="wrong"),
    ]

    attack_cases = [
        row for row in case_results if row["case"] != "current_valid_pointer_control"
    ]

    table_counts = {}

    for table in [
        "memories",
        "pointer_index",
        "revoked_pointers",
        "tombstones",
        "bucket_epochs",
        "test_vectors",
        "audit_chain",
    ]:
        table_counts[table] = reload_conn.execute(
            f"SELECT COUNT(*) AS c FROM {table}"
        ).fetchone()["c"]

    active_after_reload = reload_conn.execute(
        "SELECT COUNT(*) AS c FROM memories WHERE active=1"
    ).fetchone()["c"]

    pointer_count = table_counts["pointer_index"]

    distinct_pointer_count = reload_conn.execute(
        "SELECT COUNT(DISTINCT pointer_hmac) AS c FROM pointer_index"
    ).fetchone()["c"]

    reload_conn.close()

    summary = {
        "active_after_sqlite_reload": active_after_reload,
        "rotated_bucket_count": BUCKET_COUNT,
        "current_collision_count": pointer_count - distinct_pointer_count,
        "sqlite_state_fingerprint_before": before_fingerprint,
        "sqlite_state_fingerprint_loaded": after_fingerprint,
        "sqlite_state_fingerprint_match": before_fingerprint == after_fingerprint,
        "sqlite_table_counts": table_counts,
        "sqlite_reload_tombstone_missing": N_DELETE - table_counts["tombstones"],
        "total_sqlite_reload_attack_checked": sum(row["checked"] for row in attack_cases),
        "total_sqlite_reload_wrong_resolve": sum(row["wrong_resolve_count"] for row in attack_cases),
        "total_sqlite_reload_wrong_release": sum(row["wrong_release_count"] for row in attack_cases),
        "min_sqlite_reload_attack_reject_rate": min(
            float(row["reject_rate"])
            for row in attack_cases
            if row["reject_rate"] is not None
        ),
        "min_sqlite_reload_structured_reason_rate": min(
            float(row["structured_reason_rate"]) for row in case_results
        ),
        "audit_chain_valid_after_sqlite_reload": audit_ok,
        "audit_tamper_detected": not tamper_ok,
        "tamper_reason": tamper_reason,
        "sqlite_db_path": str(DB_PATH),
        "sqlite_db_size_bytes": DB_PATH.stat().st_size,
    }

    return {
        "summary": summary,
        "case_results": case_results,
    }


def make_report(
    final_summary: Dict[str, Any],
    scale_rows: List[Dict[str, Any]],
) -> None:
    def scale_row(text_len: int, mode: str) -> Dict[str, Any]:
        for row in scale_rows:
            if (
                row["avg_text_chars"] == text_len
                and row["mode"] == mode
                and row["n_memories"] == 100000
            ):
                return row
        raise KeyError((text_len, mode))

    lines = [
        "# V01X Local Repro Report — HSRAG Personal Memory Pointer",
        "",
        f"Generated at UTC: {RUN_CREATED_AT_UTC}",
        "",
        "## Decision",
        "",
        final_summary["decision"],
        "",
        "## Scale Compression at 100k",
        "",
        "| Avg Text Chars | Compact Reduction | Ultra Reduction |",
        "|---:|---:|---:|",
    ]

    for text_len in TEXT_LEN_LIST:
        compact = scale_row(text_len, "COMPACT_POINTER")["reduction_vs_full_pct"]
        ultra = scale_row(text_len, "ULTRA_POINTER")["reduction_vs_full_pct"]
        lines.append(f"| {text_len} | {compact:.2f}% | {ultra:.2f}% |")

    sqlite_summary = final_summary["sqlite_repro"]

    lines += [
        "",
        "## SQLite / Lifecycle / Replay Result",
        "",
        f"- Active after SQLite reload: {sqlite_summary['active_after_sqlite_reload']}",
        f"- Reload attack checked: {sqlite_summary['total_sqlite_reload_attack_checked']}",
        f"- Reload wrong resolve: {sqlite_summary['total_sqlite_reload_wrong_resolve']}",
        f"- Reload wrong release: {sqlite_summary['total_sqlite_reload_wrong_release']}",
        f"- Min attack reject rate: {sqlite_summary['min_sqlite_reload_attack_reject_rate']}",
        f"- Min structured reason rate: {sqlite_summary['min_sqlite_reload_structured_reason_rate']}",
        f"- Audit tamper detected: {sqlite_summary['audit_tamper_detected']}",
        "",
        "## Acceptance Gates",
        "",
        "| Gate | Pass |",
        "|---|---:|",
    ]

    for gate, passed in final_summary["acceptance_gates"].items():
        lines.append(f"| {gate} | {passed} |")

    lines += [
        "",
        "## Known Limits",
        "",
        "- Synthetic only.",
        "- Not real personal data.",
        "- Not GDPR proof.",
        "- Benchmark HMAC key is public and deterministic; it is not a production secret.",
        "- SQLite database is not encrypted in this PoC.",
        "- Production needs secure key management and stronger local policy classifier.",
    ]

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_docs(final_summary: Dict[str, Any]) -> None:
    README.write_text(
        f"""# HSRAG Personal Memory Pointer v0.1.x Local Repro Pack

Current decision: {final_summary['decision']}

Run from repository root:

`python examples/hsrag_memory_pointer_v01x/run_v01x_local_repro.py`

## Outputs

- outputs/v01x_scale_compression_results.csv
- outputs/v01x_scale_stability.csv
- outputs/v01x_sqlite_attack_results.csv
- outputs/v01x_sqlite_lifecycle_summary.csv
- outputs/v01x_final_summary.json
- outputs/v01x_local_repro.sqlite3
- V01X_LOCAL_REPRO_REPORT.md
""",
        encoding="utf-8",
    )

    README_TESTING.write_text(
        """# README_TESTING — V01X Local Repro Pack

Run:

`python examples/hsrag_memory_pointer_v01x/run_v01x_local_repro.py`

Expected:

- decision = PASS_V01X_LOCAL_REPRO_PACK
- measured_max_n = 100000
- total_sqlite_reload_wrong_resolve = 0
- total_sqlite_reload_wrong_release = 0
- audit_tamper_detected = true
""",
        encoding="utf-8",
    )

    start = "<!-- HSRAG_MEMORY_POINTER_V01X_START -->"
    end = "<!-- HSRAG_MEMORY_POINTER_V01X_END -->"

    block = f"""{start}
## HSRAG Personal Memory Pointer v0.1.x Local Repro Pack

Current decision: {final_summary['decision']}.

Key result: the local repro pack measures 100k-scale pointer compression and verifies SQLite reload safety, tombstones, stale pointer rejection, purpose-boundary rejection, and audit-chain tamper detection.

Artifacts:

- examples/hsrag_memory_pointer_v01x/README.md
- examples/hsrag_memory_pointer_v01x/README_TESTING.md
- examples/hsrag_memory_pointer_v01x/V01X_LOCAL_REPRO_REPORT.md
- examples/hsrag_memory_pointer_v01x/outputs/v01x_final_summary.json

Boundary: synthetic local repro benchmark only; not real personal data and not GDPR proof.
{end}
"""

    if ROOT_README.exists():
        root_text = ROOT_README.read_text(encoding="utf-8")
    else:
        root_text = "# HSRAG\n"

    pattern = re.escape(start) + r".*?" + re.escape(end)

    if start in root_text and end in root_text:
        root_text = re.sub(pattern, block, root_text, flags=re.DOTALL)
    else:
        root_text = root_text.rstrip() + "\n\n" + block

    ROOT_README.write_text(root_text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()

    print("== V01X Local Repro Pack ==")
    print(f"Started at UTC: {RUN_CREATED_AT_UTC}")

    print("[1/3] Running scale compression repro...")
    scale_rows, stability_rows = run_scale_compression()

    write_csv(OUT / "v01x_scale_compression_results.csv", scale_rows)
    write_csv(OUT / "v01x_scale_stability.csv", stability_rows)

    print("[2/3] Running SQLite lifecycle/reload/replay repro...")
    sqlite_result = run_sqlite_lifecycle_repro()

    sqlite_summary = sqlite_result["summary"]
    attack_rows = sqlite_result["case_results"]

    write_csv(OUT / "v01x_sqlite_attack_results.csv", attack_rows)
    write_csv(OUT / "v01x_sqlite_lifecycle_summary.csv", [sqlite_summary])

    def find_scale_row(text_len: int, mode: str) -> Dict[str, Any]:
        for row in scale_rows:
            if (
                row["avg_text_chars"] == text_len
                and row["mode"] == mode
                and row["n_memories"] == 100000
            ):
                return row
        raise KeyError((text_len, mode))

    compact_50 = float(find_scale_row(50, "COMPACT_POINTER")["reduction_vs_full_pct"])
    ultra_50 = float(find_scale_row(50, "ULTRA_POINTER")["reduction_vs_full_pct"])

    max_scale_std = max(
        float(row["reduction_std_pct"])
        for row in stability_rows
        if row["mode"] in ["COMPACT_POINTER", "ULTRA_POINTER"]
    )

    gates = {
        "measured_max_n_100k": max(N_LIST) == 100000,
        "compact_pointer_reduction_100k_gt_60pct": compact_50 > 60.0,
        "ultra_pointer_reduction_100k_gt_75pct": ultra_50 > 75.0,
        "scale_std_under_0_1pct": max_scale_std < 0.1,
        "active_pointer_collision_zero": sqlite_summary["current_collision_count"] == 0,
        "tombstone_missing_zero": sqlite_summary["sqlite_reload_tombstone_missing"] == 0,
        "sqlite_reload_wrong_resolve_zero": sqlite_summary["total_sqlite_reload_wrong_resolve"] == 0,
        "sqlite_reload_wrong_release_zero": sqlite_summary["total_sqlite_reload_wrong_release"] == 0,
        "sqlite_reload_attack_reject_rate_1": sqlite_summary["min_sqlite_reload_attack_reject_rate"] == 1.0,
        "sqlite_reload_structured_reason_rate_1": sqlite_summary["min_sqlite_reload_structured_reason_rate"] == 1.0,
        "audit_tamper_detected": sqlite_summary["audit_tamper_detected"] is True,
        "sqlite_state_fingerprint_match": sqlite_summary["sqlite_state_fingerprint_match"] is True,
    }

    decision = "PASS_V01X_LOCAL_REPRO_PACK" if all(gates.values()) else "REVIEW_V01X_LOCAL_REPRO_PACK"

    final_summary = {
        "poc_version": POC_VERSION,
        "decision": decision,
        "generated_at_utc": RUN_CREATED_AT_UTC,
        "runtime_seconds": round(time.perf_counter() - start_time, 3),
        "scope": "local_repro_pack_for_core_v01x_personal_memory_pointer_claims",
        "measured_max_n": max(N_LIST),
        "scale_repro": {
            "compact_pointer_100k_50_chars_reduction_pct": compact_50,
            "ultra_pointer_100k_50_chars_reduction_pct": ultra_50,
            "max_scale_std_pct_compact_ultra": max_scale_std,
        },
        "sqlite_repro": sqlite_summary,
        "acceptance_gates": gates,
        "warnings": [
            "Synthetic only; not real personal data.",
            "Not GDPR proof.",
            "Benchmark HMAC key is public and deterministic; not a production secret.",
            "SQLite database is not encrypted in this PoC.",
            "Production needs secure key management and stronger local policy classifier.",
        ],
    }

    write_json(OUT / "v01x_final_summary.json", final_summary)

    print("[3/3] Writing report and README files...")
    make_report(final_summary, scale_rows)
    write_docs(final_summary)

    print(json.dumps(final_summary, ensure_ascii=False, indent=2, sort_keys=True))

    if decision != "PASS_V01X_LOCAL_REPRO_PACK":
        raise SystemExit("V01X local repro did not pass all gates.")


if __name__ == "__main__":
    main()
