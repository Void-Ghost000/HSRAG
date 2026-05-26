# V01X Local Repro Report — HSRAG Personal Memory Pointer

Generated at UTC: 2026-05-26T14:42:46Z

## Decision

PASS_V01X_LOCAL_REPRO_PACK

## Scale Compression at 100k

| Avg Text Chars | Compact Reduction | Ultra Reduction |
|---:|---:|---:|
| 50 | 68.34% | 87.21% |
| 300 | 82.41% | 92.89% |
| 1000 | 92.16% | 96.83% |
| 3000 | 96.97% | 98.77% |

## SQLite / Lifecycle / Replay Result

- Active after SQLite reload: 97000
- Reload attack checked: 18000
- Reload wrong resolve: 0
- Reload wrong release: 0
- Min attack reject rate: 1.0
- Min structured reason rate: 1.0
- Audit tamper detected: True

## Acceptance Gates

| Gate | Pass |
|---|---:|
| measured_max_n_100k | True |
| compact_pointer_reduction_100k_gt_60pct | True |
| ultra_pointer_reduction_100k_gt_75pct | True |
| scale_std_under_0_1pct | True |
| active_pointer_collision_zero | True |
| tombstone_missing_zero | True |
| sqlite_reload_wrong_resolve_zero | True |
| sqlite_reload_wrong_release_zero | True |
| sqlite_reload_attack_reject_rate_1 | True |
| sqlite_reload_structured_reason_rate_1 | True |
| audit_tamper_detected | True |
| sqlite_state_fingerprint_match | True |

## Known Limits

- Synthetic only.
- Not real personal data.
- Not GDPR proof.
- Benchmark HMAC key is public and deterministic; it is not a production secret.
- SQLite database is not encrypted in this PoC.
- Production needs secure key management and stronger local policy classifier.
