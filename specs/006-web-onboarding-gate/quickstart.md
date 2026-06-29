# Quickstart: validating the Web Onboarding Gate

Free STRUCTURAL surfaces first (no model spend), then the human browser smoke + the back-half eye-gate.
A green self-test proves structure, never pixels (constitution §II).

## Prerequisites

- Python 3.11 env at `.venv`. Existing deps only (PyMuPDF, rapidocr, Pillow); no new dependency.
- The synthetic-PDF fixture (`tests_support/make_pdf`) for the free tests; a real brand PDF + logo for
  the human smoke; an existing key (e.g. `answer_keys/aia.json`) for the id-collision test.

## Step 1 - Multipart parser (free)

```
.venv/bin/python test_multipart.py
```
Expect: a synthetic multipart body with one text field + one file part round-trips -- the field value
and the file's filename + EXACT bytes come back intact; binary bytes (a PDF/PNG) survive byte-for-byte.

## Step 2 - The wizard flow + persist, over the synthetic fixture (free)

```
.venv/bin/python test_onboard.py
```
Expect: `start_draft(pdf_bytes)` returns a draft_id + suggestions whose `color` is the hex-token page
(1-indexed, not the color-mention page); `extract_draft` returns colors with hex + needs_review, and a
zero-color page set returns a BLOCK; `save_draft` with a primary + real logo + acknowledged flags writes
an `answer_keys/<brand>.json` that passes `validate_lean_key` and yields a non-empty thin prompt with
the primary hex; save FAILS LOUD (no file) on missing primary / logo, an unacknowledged flag, and an
existing brand id; the draft dir is gone after save; the saved brand appears in
`frontend.server._brands()`. (Uses a throwaway brand id; cleans up.)

## Step 3 - Standalone CLI intact + server GET smoke (free)

```
.venv/bin/python tests_support/verify_reuse.py     # 005 reuse surface still green
.venv/bin/python brand_intake/intake.py --pdf <synthetic-or-real>.pdf --brand _smoke --no-gate --logo <png>
# (the CLI now calls the shared persist.* and still runs end-to-end; clean up _smoke after)
```
Then start the server and fetch the onboarding screen with NO upload:
```
.venv/bin/python frontend/server.py <port>     # GET /onboard serves the wizard; GET /brands lists keys
```

## Step 4 - The human browser smoke + the paid eye-gate (after the build)

Open `http://localhost:<port>/onboard`, upload a real cold-brand PDF, confirm the suggested pages,
verify the locks (assign the primary, acknowledge flags, confirm names), upload the logo, and save.
Confirm the saved key matches the printed spec and appears in the live-runner dropdown; then generate a
sign for it (the one paid step) and judge by eye (§II). Record the verdict in `SYSTEM_MAP.md`.

## References

- Data shapes: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Decisions + reuse map: [research.md](./research.md)
