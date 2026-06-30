# Quickstart: Reference-image Upload in the Live-runner

Free structural validation first (constitution: build + verify on the free surfaces before any paid
call), then the one human browser smoke + the paid sign (folded into 004's pending T016).

## Prerequisites

- Python 3.11 `.venv` (run everything as `.venv/bin/python`).
- A brand already onboarded (an `answer_keys/<brand>.json`), e.g. `aia` or `chajiuxingqiu`.
- A reference image file on disk to pick in the browser.

## 1. Free structural self-tests (NO paid calls)

```bash
# the new feature test (save-upload + multipart /run assembly + fail-loud + verbatim + CLI + grep)
.venv/bin/python test_reference_upload.py

# regression: the upload parser and the prior frontend suites still green
.venv/bin/python test_multipart.py
.venv/bin/python test_frontend_intake.py
.venv/bin/python test_onboard.py        # 006 logo-save now goes through save_upload; must stay green
.venv/bin/python test_thin_route.py     # the unchanged input contract
```

Expected: each prints `RESULT: N/N checks passed` and exits 0. The new test asserts (each a VALUE a wrong
build cannot satisfy):
- `save_upload(("ref.png", BYTES), tmp)` writes a real file whose bytes EQUAL `BYTES` and returns its path.
- a synthetic multipart `/run`-style body -> the assembled inputs JSON's `reference_image` points at a
  file that EXISTS in the run dir (file-on-disk + path-in-JSON), with NO generation launched.
- a body with NO reference file fails loud (raises / 4xx), no run launched.
- messages / mandatory_elements pass through `inputs_writer` verbatim (002 invariant).
- `conductor --thin --inputs <json>` with a `reference_image` path still runs with the frontend absent.
- the served `index.html` uses a file input for the reference (structural grep), not a typed-path field.

## 2. Standalone CLI regression (no frontend, no paid call beyond the usual one)

```bash
# the input contract is unchanged: a hand-written inputs JSON with a reference_image PATH still drives
# the thin route with the frontend absent (dry-run / structural surface)
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/dry --dry-run --no-approve
```

Expected: plans without error; `reference_image` is read as a path exactly as before 007.

## 3. Human browser smoke + the one paid sign (folds into 004 T016)

```bash
.venv/bin/python frontend/server.py      # http://localhost:8765
```

In the browser:
1. Open `/`. Confirm the reference field is a FILE PICKER, with no typed-path text input anywhere.
2. Fill a single-sign brief, PICK a reference image from disk, click Run (paid, about $0.08).
3. Confirm the run launches, the reference is saved into `output/run_*/` (e.g. `reference.png`), and the
   sign generates from it. Judge `output/run_*/sign_*/final.png` with the HUMAN EYE (constitution §II;
   no VLM self-score counts).
4. Confirm a Run with NO file picked is rejected in-browser (fail loud), with no run launched.

This paid sign is the SAME one 004 T016 still owes; 007 ships no separate paid run.
