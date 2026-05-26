# HSRAG Memory Context Baseline v0.2.1 — Public Summary

This benchmark compares five ways to build memory context for an AI assistant, from full raw context stuffing to pointer-based on-demand resolve.

The main question is simple:

> Can a pointer-based memory context strategy remain small, fast, traceable, and safe at 100k synthetic memories?

## Result

At 100k synthetic memories, `E_POINTER_ON_DEMAND_RESOLVE` achieved:

- 99.9941% token reduction vs full raw context
- P99 local context construction latency of 0.20809 ms
- answer coverage of 1.0
- sensitive memory leak rate of 0.0
- traceability rate of 1.0

## What this does not claim

- It does not call a real LLM.
- It does not use real personal data.
- It does not prove legal or GDPR compliance.
- It measures local context construction, not model inference.

## Why it matters

The result suggests that memory systems can separate addressing, traceability, and selective disclosure instead of always stuffing raw memory into the model context.
