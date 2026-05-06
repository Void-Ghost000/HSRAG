# HSRAG LAW Custom Corpus Template

This template lets users test clean, legally usable public legal text with a local HSRAG LAW routing benchmark.

It is designed for plaintext / markdown legal text first.

This template does not claim to support every legal source format. PDF extraction, browser automation, and official bulk dataset ingestion should be handled by separate ingestion tools.

---

## Basic workflow

1. Put clean public legal text into:

    input/legal_texts/

2. Fill in:

    input/manifest.example.json

3. Build a custom corpus:

    python .\examples\hsrag_law\custom_template\scripts\build_custom_corpus.py

4. Run a local routing benchmark:

    python .\examples\hsrag_law\custom_template\scripts\run_custom_benchmark.py

5. Review outputs in:

    output/

---

## Safety note

Use only legal text that you are allowed to process locally.

Do not put confidential, private, or copyrighted text into this template unless you have the right to do so.

This is a retrieval benchmark template, not legal advice.
