# Implementation Plan: Layered Export (per-element layers.zip)

**Branch**: `016-layered-export` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-layered-export/spec.md`

## Summary

After the operator eye-judges a generated image, an opt-in, cost-stated button exports a layered
decomposition: one gpt-image-2 edit call per deterministically enumerated design element (message
lines, fed logo, product photos) repainting ONLY that element on chroma green #00B140, keyed to a
true RGBA layer by the EXISTING `strip_chroma`; plus one background call (elements removed); all
zipped with white-bg JPG previews and an audit manifest. gpt-image-2 cannot emit layers or
transparency natively (verified 2026-07), so build-by-chroma-repaint is the route. The export
follows the 015 pre-spend contract exactly (free plan surface, state-before-spend, idempotent,
retry only from failed, gate-done precondition, disk-backed).

## Technical Context

**Language/Version**: Python 3.11 (`.venv`); frontend stays no-framework HTML + vanilla JS.

**Primary Dependencies**: stdlib + PIL; numpy/scipy arrive transitively through the reused
`strip_chroma` import (already project deps); the OpenAI client only inside the existing
`harness/generate.py` wrapper. NO new dependencies.

**Storage**: files in the run dir only: `export_state.json`, `export/<layer_id>/*`,
`export_manifest.json`, `layers.zip`. Never rewrites any pre-existing artifact.

**Testing**: `test_export_layers.py`, the project's plain-script self-test style, 7 checks, all
FREE (injected `generate_fn` stub writes synthetic chroma PNGs; the REAL `strip_chroma` runs on
synthetic fixtures). The one paid step is the SC-007 human eye-gate, never automated.

**Target Platform**: local Linux/WSL2, the existing `frontend/server.py` app.

**Project Type**: existing single repo; one new harness module + thin frontend wiring.

**Performance Goals**: N+1 paid calls per export, sequential (matches the single-flight server);
no other constraints.

**Constraints**: 015 pre-spend contract; byte-identity for unexported runs and all existing
paths; honest nulls per layer; no paid calls in tests; no em-dashes in user-facing text.

**Scale/Scope**: ~350-line new module, ~60 lines server, ~15 lines run_view, ~40 lines
index.html, 1 test file. `generate.py`, `scene_author.py` generation paths, `conductor.py`,
register engine, kit/legacy: UNTOUCHED.

## Constitution Check

*GATE: passed pre-Phase-0; re-checked post-Phase-1 (no drift).*

| Principle | Status | How the design honors it |
|---|---|---|
| I. Agent-free, not human-free | PASS | Export is an operator TASTE-gate action: opt-in click after the eye-judgment, never automatic, never bundled into generation. |
| II. Eye is ground truth | PASS | Structural tests prove zip shape/state/costs only; SC-007 (operator stacks layers in an editor) is the only pixel verdict. |
| III. Falsifiable tests | PASS | Checks assert VALUES: exact call counts, exact zip member sets, alpha at known pixels of synthetic fixtures, zero-call idempotency, tree-hash byte-identity. |
| IV. Generalize, no hand-tune | PASS | Element enumeration reads run artifacts (any brand, any brief); thresholds are keying-statistic constants, not per-image tuning. |
| V. Honest nulls | PASS | Threshold-marked null layers ship the raw output + a named note, never a fabricated cutout; background flagged model-continued. |
| VI. Reconciliation per-dimension | PASS (n/a core) | Feature is post-generation packaging; it never touches register/calibration. |
| VII. Repo durable context | PASS | Spec/plan/tasks committed; CLAUDE.md + SYSTEM_MAP updated in the same commit that stales them (T6). |
| Cost discipline | PASS | `--plan-only` + stubbed `generate_fn` are the free surfaces; exactly one paid eye-gate, human-scheduled. |

## Project Structure

### Documentation (this feature)

```text
specs/016-layered-export/
├── spec.md              # feature spec (done)
├── plan.md              # this file
├── research.md          # Phase 0: decisions + verified facts
├── data-model.md        # Phase 1: entities, state machine, file layout
├── quickstart.md        # Phase 1: free + paid validation walkthrough
├── contracts/
│   └── http-and-cli.md  # Phase 1: routes, CLI, zip/manifest contracts
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
harness/
├── export_layers.py         # NEW: the whole engine (enumerate/prompts/plan/key/orchestrate/zip/CLI)
├── closed_loop_composite.py # REUSED read-only: strip_chroma(final_png, out_dir, key_hex) at :428
├── generate.py              # REUSED read-only: generate_variant(prompt, refs, out_path, size, quality)
└── scene_author.py          # REUSED read-only: CHROMA_KEY_HEX = "#00B140" at :133

frontend/
├── server.py                # +decide_export, POST /run/<id>/export, GET .../export/plan, GET .../layers.zip
├── run_view.py              # +additive "export" stage (state + manifest + honest null)
└── index.html               # +opt-in export button, per-layer rows, download link

test_export_layers.py        # NEW: 7 free checks
```

**Structure Decision**: one new harness module (the project's per-concern pattern: conductor,
scene_author, measure, composite are all single-purpose modules), thin frontend wiring mirroring
the 015 gate seams. The exporter is CLI-first (like every harness module) so the browser is a
thin shell over it.

## Design detail (binding decisions)

### Core module `harness/export_layers.py`

Constants: `EXPORT_DIRNAME="export"`, `ZIP_NAME="layers.zip"`, `STATE_NAME="export_state.json"`,
`MANIFEST_NAME="export_manifest.json"`; honest-null thresholds `NULL_OPAQUE_MAX=0.95`
(model ignored chroma), `NULL_OPAQUE_MIN=0.001` (empty frame), `NULL_RESIDUAL_MAX=2000`
(dirty key field, on strip_chroma's `green_residual_px_in_preview`). `CHROMA_KEY_HEX` imported
from `scene_author` (single source). Per-image cost imported/mirrored from the 015 constant
(`PER_RUN_COST_USD` in `frontend/server.py`; the module takes `per_image_usd` as a parameter so
harness stays frontend-independent, the server passes its constant).

Functions (signatures fixed):
- `find_source_image(run_dir, sign_id="s1") -> Path | None`: `final.png` if present else
  `generated.png`, else None (honest null).
- `enumerate_elements(run_dir, brand_key) -> list[dict]`: PURE. One
  `{"id": "text_<i>", "kind": "text", "text": <verbatim>}` per `inputs.json signs[0].messages`
  line; `{"id": "logo", "kind": "logo", "ref": <key logo_path>}` ONLY if that path is in
  `run_manifest generation.reference_image` (verified real key: the fed list is
  [reference.png, logo, product_1.jpg]); one `{"id": "product_<i>", "kind": "product",
  "ref": <path>}` per `inputs.json product_images`. Background NOT an element.
- `isolation_prompt(element, key_hex=CHROMA_KEY_HEX) -> str` and
  `background_prompt(elements) -> str`: PURE; skeletons in research.md. Logo/product prompts
  reference "the SECOND supplied image" (the original asset).
- `export_plan(run_dir, brand_key, per_image_usd) -> dict`:
  `{elements, calls: len+1, cost_usd, source_image, size}` (size from
  `run_manifest generation.size`); raises `SystemExit` with a named reason on zero elements or
  missing source (FR-011), so plan surface and CLI share the refusal.
- `key_layer(isolated_png, layer_dir) -> dict`: wraps the REAL `strip_chroma`; applies NULL_*
  thresholds; on ok flattens `preview_white.png` to `preview.jpg` and records the opaque bbox;
  returns `{"status": "ok"|"null", "note": ..., **stats}`.
- `export_layers(run_dir, brand_key, generate_fn=None, per_image_usd=...) -> dict`: the
  orchestrator. (1) state exporting/done → no-op return (idempotent; retry accepted only from
  failed); (2) write state="exporting" + plan BEFORE any call; (3) per element:
  `generate_fn(prompt, [source] + ([ref] if logo/product), export/<id>/isolated.png, size=...)`
  then `key_layer`, APPENDING each entry to `export_manifest.json` (progressive, crash leaves a
  truthful partial); (4) background call to `export/background/background.png` (UNKEYED) +
  `background_preview.jpg`; (5) `build_zip`; state="done". Any exception: state="failed" +
  error note, fail loud. `generate_fn` defaults to `generate.generate_variant` (lazy import so
  tests never touch the OpenAI client).
- `build_zip(run_dir, manifest) -> Path`: `layers.zip` = manifest + `background.png` +
  `background_preview.jpg` + per ok-layer `<id>.png` (RGBA cutout) + `<id>_preview.jpg` + per
  null-layer `<id>_raw.png`. Null layers NEVER ship a cutout.
- `main()`: `--run-dir` (required), `--brand` (default from `run_meta.json`), `--plan-only`
  (print plan JSON, exit, ZERO paid calls: the free surface).

### Frontend seams (mirror 015)

- `frontend/server.py`: `decide_export(run_dir, per_image_usd) -> (code, payload, launch)`
  HTTP-free like `decide_confirm` (:88): 404 missing run/source; 409 unless
  `gate_state.state == "done"`; no-op 200 on exporting/done; failed → accept retry; on accept
  writes state="exporting" via the module then returns launch=True. `POST /run/<id>/export`
  takes `_inflight`, launches `.venv/bin/python harness/export_layers.py --run-dir <dir>` in the
  `_launch_async` style (subprocess isolation; crash lands in state="failed"). Free
  `GET /run/<id>/export/plan`. `GET /run/<id>/layers.zip` serves the zip (404 until done).
- `frontend/run_view.py`: additive `export` stage from `export_state.json` +
  `export_manifest.json`; absent = `present:false` + note "not exported; export is opt-in and
  paid". Never raises.
- `frontend/index.html`: post-image "Export layers (paid, ~$X for N+1 images)" button labeled
  from the plan endpoint; per-layer progress rows (ok / null + note); `layers.zip` download
  link. Requires a server restart to pick up server.py (known ops note in memory).

### Accepted v1 risks (from spec Assumptions, restated for the implementer)

Position drift: measured (bbox in manifest), judged by eye, not auto-corrected. Largest-component
keying: `stray_component_px_dropped` exposes dropped glyph clusters; keying itself UNTOUCHED.
Background hallucination: flagged `model_continued: true` in the manifest.

## Complexity Tracking

No constitution violations; table not needed.
