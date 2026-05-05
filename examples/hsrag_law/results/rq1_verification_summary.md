# RQ1 Verification Summary

Core decision: `RQ1_VERIFICATION_PASS`
Audit chain complete: `1.0`

## RQ1 Purpose

RQ1 verifies the publication-grade real-corpus gate before retrieval benchmarking begins. It checks source-hash completeness, real-primary corpus status, wrong-collision absence, SC1 regression status, and auditability.

## Core Gate Summary

- passed gates: `11/11`
- real_primary_corpus_rate: `1.0`
- real_primary_chunk_rate: `1.0`
- source_hash_final_present_rate: `1.0`
- primary_real_rows: `1211`
- primary_real_target_correct_rate: `1.0`
- primary_real_wrong_collision_rate: `0.0`
- fail_count: `0`
- warn_count: `0`

## MC Scope

- decision: `MC_NOT_REQUIRED_FOR_RQ1_PASS`
- mc_cases: `None`
- reason: RQ1 is a source-integrity and publication-grade real-corpus gate, not an adversarial retrieval mutation benchmark. MC robustness is covered by RQ2/RQ3-style retrieval benchmarks.

## URL Fetch Smoke

- decision: `FETCH_SMOKE_PASS_WITH_WARN`
- fetch_count: `6`
- fetch_ok_count: `3`
- fetch_warn_count: `2`
- fetch_error_count: `1`

Fetch records are written to `rq1_url_fetch_records.csv`.

## Notes

- This verifier does not reproduce the full RQ2/RQ3 MC benchmarks.
- URL fetch smoke is intentionally not a hard gate unless `--strict-fetch` is used.
- If official sites block scripted fetching, create a dedicated RQ4 fetch reproducibility pipeline.

## Fetch Record Preview

- `EU_AI_ACT`: `FETCH_WARN_GATE_PAGE` status=`202` bytes=`2035`
- `EU_DMA`: `FETCH_WARN_GATE_PAGE` status=`202` bytes=`2035`
- `US_COPPA`: `FETCH_OK` status=`200` bytes=`1012296`
- `US_CDA230`: `FETCH_OK` status=`200` bytes=`142083`
- `US_FTC_ACT5`: `FETCH_OK` status=`200` bytes=`172748`
- `US_CCPA`: `FETCH_ERROR` status=`None` bytes=`0`
