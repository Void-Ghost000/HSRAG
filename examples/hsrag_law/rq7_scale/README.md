# HSRAG RQ7 Scale Benchmark


## Directory Map

This benchmark keeps the QSVCS-CSP design files inside the experiment folder.

These files are not runtime dependencies. They are pre-benchmark governance documents used to make the experiment reviewable before execution.

Directory purpose:

- `00_qoim/`
  - Defines the experiment intent, scope, forbidden zones, invariants, risk class, and delivery level.
  - In short: why this benchmark exists and what it must not claim.

- `01_csp/`
  - Defines the causal skeleton, gates, state transitions, side-effect boundaries, failure reasons, tests, and acceptance criteria.
  - In short: how the benchmark is allowed to run and what must be validated.

- `02_input/`
  - Contains toy corpus registry, query seeds, and mutation policy.

- `03_schema/`
  - Contains the result contract schema.

- `04_runs/`
  - Stores generated run artifacts.

- `05_reports/`
  - Stores the latest human-readable RQ7 report.

- `06_audit/`
  - Stores copied audit-chain artifacts.

- `scripts/`
  - Contains the executable benchmark runner.

Why keep `00_qoim` and `01_csp`?

RQ7 is not only a benchmark. It is also a reproducibility and claim-boundary test.

The design files make clear that:

- HSRAG is not claimed to replace all RAG systems.
- Unique address lookup is only valid for stable CTHC identifiers.
- CTHC-pruned search may use salted domain boundaries.
- Global search must not use domain salt for pruning.
- Reported results must preserve claim boundaries and known limits.

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- Full-scale RQ7 benchmark: not implemented yet.
- Official RQ4 corpus loader: not connected yet.
- Vector / hybrid baselines: not implemented yet.

