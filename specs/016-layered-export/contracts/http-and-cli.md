# Contracts: Layered Export (016)

## HTTP (frontend/server.py; all handlers are thin over HTTP-free deciders, 015 style)

### GET /run/<id>/export/plan  (FREE, zero spend)
- 200: the export plan JSON (see data-model). Powers the button label.
- 404: run dir or source image missing (named reason).
- 409: `gate_state.state != "done"` (no generated image to decompose yet), or zero elements
  (named: "no enumerable elements; layered export would be a paid no-op").

### POST /run/<id>/export  (the ONLY layered-export spending route)
- Preconditions identical to the plan endpoint, evaluated by `decide_export(run_dir,
  per_image_usd)` (HTTP-free, unit-tested directly).
- On accept: writes `export_state.json` state="exporting" (BEFORE launch), acquires the
  `_inflight` single-flight lock, launches `.venv/bin/python harness/export_layers.py
  --run-dir <dir>` as a background subprocess. 202 `{"state": "exporting", "cost_stated": ...}`.
- Repeat while exporting/done: 200 `{"state": ..., "note": "already exporting/exported; no
  second spend"}`, ZERO calls.
- From failed: accepted as a fresh export (cost restated in the response).
- 503 if `_inflight` is held by a generation (one paid thing at a time).

### GET /run/<id>/layers.zip
- 200 (application/zip) when state=done; 404 otherwise.

### GET /run/<id> (existing run view)
- Gains one ADDITIVE stage `export`: `{present, content: {state, plan, layers: [manifest entries
  so far], zip_ready}, note}`. Absent state file: `present: false`, note "not exported; export
  is opt-in and paid". Pre-016 run dirs: unchanged output plus this stage only.

## CLI (harness/export_layers.py)

```
.venv/bin/python harness/export_layers.py --run-dir output/run_X [--brand CJXQ] [--plan-only]
```
- `--plan-only`: print the plan JSON, exit 0, ZERO paid calls (the free structural surface).
- Without it: run the full export against the run dir (same state machine as the route; the
  browser is a thin shell over this).
- `--brand` defaults from `run_meta.json`; the brand key loads from `answer_keys/<brand>.json`.
- Refusals (missing source, zero elements, gate not done, state exporting/done) are `SystemExit`
  with a named reason, exit code nonzero. Retry from failed allowed.

## Python (internal, test-facing)

```python
export_layers(run_dir: Path, brand_key: dict, generate_fn=None, per_image_usd=0.08) -> dict
# generate_fn(prompt: str, refs: list[str], out_path: str, size: str) -> dict
# defaults to harness/generate.generate_variant (lazy import); tests inject a stub.
```
Call contract per element: refs = `[source_image]` (text) or `[source_image, element_ref]`
(logo/product); background: `[source_image]`. size = run_manifest `generation.size`, always.
