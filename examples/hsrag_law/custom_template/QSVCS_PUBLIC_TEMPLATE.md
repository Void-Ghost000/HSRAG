# QSVCS Public Template for HSRAG LAW Custom Corpus

This public template helps users prepare clean legal text inputs for HSRAG LAW.

It exposes only the public structure:

- QOIM V1: intent, boundary, invariants, success criteria
- SGF: Input / Process / Verify / Output / Feedback
- VPSM: primary-state stability rules
- CTHC: typed legal corpus addressing
- HSRAG Audit: reproducible hash-chain outputs

It does not expose private QOIM extensions or internal QSVCS reasoning protocols.

---

## QOIM V1 Intent Block

Purpose:

Run a local HSRAG routing benchmark over clean public legal text.

Allowed input:

- clean public legal text
- manually provided source metadata
- jurisdiction and corpus identifier

Disallowed input:

- private legal documents
- confidential contracts
- copyrighted text without permission
- unclear source provenance

Success criteria:

- corpus chunks are generated
- each chunk receives a CTHC typed address
- each domain receives a salted domain hash
- unsupported / ambiguous / conflict-form queries are rejected
- audit outputs are produced

---

## SGF Checklist

Input:

- Provide clean legal text files.
- Provide manifest metadata.

Process:

- Normalize text.
- Split into chunks.
- Assign CTHC typed addresses.
- Generate salted domain hashes.

Verify:

- Check manifest completeness.
- Check chunk count.
- Check domain hash count.
- Check routing behavior.

Output:

- custom_chunks.csv
- custom_manifest.json
- custom_benchmark_summary.json
- custom_benchmark_summary.md
- custom_gate_checks.csv
- custom_audit_chain.jsonl

Feedback:

- Review false allow, misrouting, and missing metadata.
- Adjust manifest or chunking rules if needed.

---

## CTHC Manifest Fields

Required fields:

- corpus_id
- title
- jurisdiction
- source_type
- language
- license_note
- cthc_domain
- cthc_topic

Recommended fields:

- source_url
- version
- retrieved_at
