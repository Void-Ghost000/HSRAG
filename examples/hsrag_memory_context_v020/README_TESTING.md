# README_TESTING — HSRAG Memory Context Baseline v0.2.0

## Goal

Reproduce the v0.2.0 deterministic memory-context baseline from a clean repository checkout.

## Requirements

- Python 3.10+
- PowerShell or shell equivalent
- No external API key required
- No network access required

## Verify Commands

Run from repository root:

1. Set base path: `$base = "examples/hsrag_memory_context_v020"`
2. Generate dataset: `python "$base/make_v020_dataset.py"`
3. Run baselines: `python "$base/run_v020_baselines.py"`
4. Generate interpretation: `python "$base/interpret_v020_results.py"`

## Expected Result

You should see:

- PASS_BASELINE_RUNNER
- PASS_INTERPRETATION_REPORT

Generated documentation should include:

- README.md
- V020_EVIDENCE_SUMMARY.md
- README_TESTING.md
- outputs/hsrag_memory_context_v020_final_summary.json
- outputs/hsrag_memory_context_v020_interpretation_summary.json

## Not Covered

- Real LLM answer quality.
- Real tokenizer cost.
- Real user data.
- GDPR compliance.
- Production privacy classifier.
- Production encrypted local storage.

Generated at UTC: 2026-05-26T14:23:37Z
