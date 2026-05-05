# RQ4.1 Official/Public Source Fetch & Rebuild Summary

Core decision: `RQ4_SOURCE_REBUILD_PASS`
Audit chain complete: `1.0`

## Purpose

RQ4.1 tests whether HSRAG LAW can fetch official or public legal sources, normalize text, generate stable source hashes, rebuild chunks, and write an auditable source manifest. It distinguishes clean fetch success from rebuild-usable warning cases.

## Summary

- source_count: `6`
- attempt_count: `11`
- fetch_ok_count: `5`
- rebuild_ok_count: `5`
- fetch_warn_count: `0`
- fetch_error_count: `1`
- rebuilt_chunk_count: `110`
- min_ok: `2`
- strict: `False`

## Source Records

| corpus_id | jurisdiction | selected_candidate_type | fetch_decision | rebuild_usable | status | text_len | chunks |
|---|---|---|---|---:|---:|---:|---:|
| EU_AI_ACT | EU | PUBLIC_REFERENCE_AI_ACT_EXPLORER | `FETCH_OK` | `True` | 200 | 7183 | 7 |
| EU_DMA | EU | OFFICIAL_EC_PUBLIC_REFERENCE | `FETCH_OK` | `True` | 200 | 6032 | 6 |
| US_COPPA | US | OFFICIAL_US_ECFR | `FETCH_OK` | `True` | 200 | 52389 | 49 |
| US_CDA230 | US | PUBLIC_REFERENCE_CORNELL_LII_USCODE | `FETCH_OK` | `True` | 200 | 11691 | 11 |
| US_FTC_ACT5 | US | PUBLIC_REFERENCE_CORNELL_LII_USCODE | `FETCH_OK` | `True` | 200 | 39692 | 37 |
| US_CCPA | US-CA | OFFICIAL_CA_OAG_REFERENCE | `FETCH_ERROR` | `False` | None | 0 | 0 |

## Gate Checks

| gate_id | passed | expected | actual |
|---|---:|---|---|
| RQ4_REBUILD_OK_MINIMUM | `True` | `>= 2` | `5` |
| RQ4_CHUNK_COUNT_POSITIVE | `True` | `> 0` | `110` |
| RQ4_CHUNK_HASH_COMPLETENESS | `True` | `True` | `True` |
| RQ4_AUDIT_CHAIN_COMPLETE | `True` | `1.0` | `1.0` |
| RQ4_HARD_GATE_SOURCES | `True` | `0` | `0` |
| RQ4_FETCH_OK_OBSERVATION | `True` | `informational` | `5` |

## Notes

- `FETCH_OK` means clean fetch + enough text + legal signal + chunks.
- `FETCH_WARN_EXTRACTABLE` means the fetch had a warning but still produced rebuild-usable text and chunks.
- EUR-Lex may return JavaScript / robot verification pages in simple fetch clients.
- Public legal references are used as fallback candidates for reproducibility smoke testing.
- This is not yet RQ4-full. A future version can add browser automation and PDF extraction.
