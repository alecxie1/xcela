# Quickstart: Layered Export (016)

## Prerequisites
- `.venv` ready (Python 3.11); no new deps to install.
- At least one completed thin-route run dir (gate done, `sign_s1/generated.png` present), e.g.
  `output/run_CJXQ_20260708_151506`.

## 1. FREE structural validation (do this first, always)
```bash
.venv/bin/python test_export_layers.py           # all 7 checks, zero paid calls
# the no-regression sweep (unchanged suites must stay green):
.venv/bin/python test_confirm_gate.py
.venv/bin/python test_frontend_stages.py
.venv/bin/python test_product_refs.py
.venv/bin/python test_thin_route.py
```

## 2. FREE plan dry-run on a real run dir (zero spend, proves enumeration + refusals)
```bash
.venv/bin/python harness/export_layers.py \
  --run-dir output/run_CJXQ_20260708_151506 --plan-only
# expect: elements = 3 text lines + logo + product_1 (5), calls = 6, cost, size 1536x1024
```
Refusal checks (also free): point `--run-dir` at a gate-not-done run (expect a named SystemExit);
at a run with no messages/logo/products (expect the zero-element refusal).

## 3. FREE browser surface (restart the server first: server.py loads once)
```bash
.venv/bin/python frontend/server.py
```
- Open a pre-016 run: renders as before plus the "not exported" stage line.
- Open a judged run: the export button shows the exact call count + cost (from
  `GET /run/<id>/export/plan`) BEFORE any click.

## 4. The ONE PAID step: the SC-007 human eye-gate (operator-scheduled, never automated)
1. On a real judged CJXQ run, click "Export layers" (~$0.48 for 6 calls on the reference run).
2. Watch per-layer rows appear (ok / null with note); download `layers.zip` when done.
3. In an image editor: stack each `<id>.png` over `background.png`. Judge: each layer reads as
   its element; position drift acceptable for a draft decomposition; every null honest (its
   `<id>_raw.png` shows why). Check `export_manifest.json` bboxes against the original.
4. Record the verdict in SYSTEM_MAP (and tasks.md T7).

## Expected outcomes
- Zero spend anywhere except step 4, and step 4 spends exactly plan.calls images.
- Repeat clicks during/after step 4: server answers "no second spend"; `export_state.json`
  proves it.
- A run never exported stays byte-identical (tree-hash check in the test suite).
