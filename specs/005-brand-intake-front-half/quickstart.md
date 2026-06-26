# Quickstart: validating the Brand-intake Front-half

Free STRUCTURAL surfaces first (no model spend), then the cold-brand OCR extraction + the one paid
sign are the human's smoke / eye-gate. A green self-test proves structure, never pixels (§II).

## Prerequisites

- Python 3.11 env at `.venv`. Existing deps only: PyMuPDF (`fitz`), `rapidocr_onnxruntime`, Pillow
  (the extractors already use them). No new dependency, no paid API.
- A brand-guideline PDF on disk for the human smoke (e.g. chajiuxingqiu / mahoupao). An existing fat
  key (`answer_keys/aia.json`) for the byte-identical regression.

## Step 1 - Page-finding heuristic (free)

```
.venv/bin/python test_page_finder.py
```
Expect: over a synthetic 3-page PDF where page 1 says "color palette" (no hex) and page 2 prints
`#31B4E7`, `suggest_pages` returns page 2 (1-indexed) for `color`, NOT page 1; font-name pages are
detected; all page numbers are 1-indexed (the `render_page` footgun).

## Step 2 - Lean key: assemble, fail-loud validate, byte-identical (free)

```
.venv/bin/python test_brand_key.py
```
Expect: `validate_lean_key` RAISES with a named reason on a key missing a primary color OR a real
`logo_path`; the lean key fed to `assemble_thin_prompt` (+ `derive_register`) yields a NON-EMPTY
prompt with the primary hex present (no blank "color  stays"); a fat key (aia.json) stripped to the
lean subset yields a BYTE-IDENTICAL prompt vs the fat key (and changing a primary hex changes it);
`extract_colors.delta_e` fires `needs_review` past the reconcile threshold.

## Step 3 - Cold-brand extraction smoke (human-run, local OCR, no paid API)

```
.venv/bin/python brand_intake/intake.py --pdf <path/to/cold_brand_VI.pdf> --brand <id> --verified-by "<you>"
```
Confirm the suggested color/name pages, run the extractors, verify each lock at the gate (assign the
primary, acknowledge any `needs_review`), supply the logo. Confirm the extracted hex matches the
printed spec (e.g. chajiuxingqiu #31B4E7 / #73C900 / #94D4EB) and that a garbled read flips
`needs_review`. The key is written to `answer_keys/<id>.json` + the logo placed under `brands/<id>/`.

## Step 4 - Run the new brand through the existing back-half (the eye-gate, paid)

```
.venv/bin/python harness/conductor.py --brand <id> --thin --no-approve --inputs <single_sign>.json
```
The lean key drives the EXISTING thin route UNCHANGED. Judge the sign by eye (§II). This is the one
paid step, AFTER the build. Record the verdict in `SYSTEM_MAP.md`.

## References

- Data shapes: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Decisions + reuse map: [research.md](./research.md)
