# Tasks: Layered Export (per-element layers.zip)

**Input**: Design documents from `/specs/016-layered-export/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-and-cli.md

**Tests**: REQUIRED by the constitution (falsifiable, free). One growing self-test file
`test_export_layers.py`; every check asserts a VALUE a wrong build cannot satisfy. NO paid call
anywhere in tests; the one paid step is the human eye-gate (T009).

**Organization**: grouped by user story; one task = one commit (constitution VII).

## Format: `[ID] [P?] [Story?] Description`

---

## Phase 1: Setup

**Purpose**: spec artifacts committed; the test scaffold + synthetic fixtures every later check reuses.

- [x] T001 Commit the 016 spec artifacts (spec.md, plan.md, research.md, data-model.md,
      contracts/, checklists/, this file) plus the CLAUDE.md active-feature flip; create
      `test_export_layers.py` scaffold with the shared fixture builders: `make_run_dir(tmp,
      messages=3, logo_fed=True, products=1)` writing a CJXQ-shaped `inputs.json` +
      `sign_s1/run_manifest.json` (generation.size, generation.reference_image) +
      `gate_state.json` (state=done) + a stand-in `sign_s1/generated.png`, and
      `make_chroma_png(path, w=1536, h=1024, content="rect"|"full"|"empty")` (PIL: red rect on
      flat #00B140 / full-noise no-green / pure-green). Self-check: fixtures round-trip
      (files exist, key color exact). Commit: `feat(016): spec + test scaffold (T001)`.

---

## Phase 2: Foundational (blocking)

**Purpose**: the PURE half every story needs: enumeration, prompts, plan, the free CLI surface.

- [x] T002 Create `harness/export_layers.py` pure half: constants (`EXPORT_DIRNAME`, `ZIP_NAME`,
      `STATE_NAME`, `MANIFEST_NAME`, `NULL_OPAQUE_MAX=0.95`, `NULL_OPAQUE_MIN=0.001`,
      `NULL_RESIDUAL_MAX=2000`, `CHROMA_KEY_HEX` imported from `harness/scene_author.py`);
      `find_source_image` (final.png > generated.png > None); `enumerate_elements` (per
      data-model: text per verbatim message line, logo gated on membership in run_manifest
      `generation.reference_image`, product per `inputs.json product_images`; background NOT an
      element); `isolation_prompt` + `background_prompt` (research.md D2 skeletons; logo/product
      name the SECOND supplied image); `export_plan` (calls=len+1, cost, size from run_manifest;
      SystemExit with a named reason on zero elements or missing source); CLI `main()` with
      `--run-dir`, `--brand` (default from run_meta.json), `--plan-only` (print plan JSON, exit,
      zero paid calls). Tests: check1 (enumeration: 3+logo+1 => 5 elements, deterministic ids;
      unfed logo => no logo element; plan calls=6 and cost=6*per_image) + check2 (prompts carry
      the verbatim line exactly once + literal #00B140 + identical-position/size clauses +
      exact-canvas clause; background prompt lists every element desc; zero-element plan raises
      the named SystemExit). Commit: `feat(016): enumeration + prompts + free plan surface (T002)`.

---

## Phase 3: User Story 1 - Export a judged run as layers (P1) 🎯 MVP

**Goal**: click-to-layers.zip works end to end (engine + zip), pixels judged later by eye.

**Independent Test**: with `generate_fn` stubbed, a fixture run exports to a zip with exactly
the expected members and exactly N+1 recorded calls.

- [x] T003 [US1] Add `key_layer(isolated_png, layer_dir)` to `harness/export_layers.py`:
      call the REAL `strip_chroma` (`harness/closed_loop_composite.py`, unchanged), apply the
      NULL_* thresholds, on ok flatten `preview_white.png` -> `preview.jpg` and record the
      opaque bbox; return `{"status","note",**stats,"bbox"}`. Test: check3 drives REAL keying on
      the synthetic fixtures: rect-on-green => status ok, cutout.png RGBA with alpha 0 off-rect
      and 255 on-rect (probe exact pixels), preview.jpg exists, bbox matches the rect within the
      defringe margin; full-noise => null "chroma directive ignored"; pure-green => null "empty
      frame". (Also discharges US3 acceptance 1-2.) Commit:
      `feat(016): key_layer over real strip_chroma + honest-null thresholds (T003)`.

- [x] T004 [US1] Add the orchestrator `export_layers(run_dir, brand_key, generate_fn=None,
      per_image_usd)` + `build_zip`: state written BEFORE the first call (full semantics T005);
      per element `generate_fn(prompt, [source]+([ref] if logo/product), export/<id>/isolated.png,
      size=run_manifest size)` then `key_layer`, APPENDING each layer record (with its prompt) to
      `export_manifest.json` progressively; background call (UNKEYED) + `background_preview.jpg`,
      manifest background entry `model_continued: true`; `build_zip` per data-model (ok:
      `<id>.png` + `<id>_preview.jpg`; null: `<id>_raw.png` ONLY, never a cutout); exception =>
      state failed + error, fail loud; `generate_fn` defaults to `generate.generate_variant` via
      LAZY import; wire the CLI non-plan path. Test: check4 (stub records calls: count = N+1
      exactly; refs order per contract; size threaded; manifest grows per layer with the exact
      prompt; zip member set EQUALS the expected set; a stub-forced null layer ships raw + no
      cutout + note). Commit: `feat(016): orchestrator + progressive manifest + layers.zip (T004)`.

**Checkpoint**: MVP engine complete; `--plan-only` free; full export runs via CLI (stub or paid).

---

## Phase 4: User Story 2 - Spend only on an explicit, informed click (P2)

**Goal**: the 015 pre-spend contract holds for export end to end (state machine + routes + UI).

**Independent Test**: all free: plan endpoint spends nothing; repeats make zero calls; retry
only from failed; 409 while the gate is not done; disk-backed rendering.

- [x] T005 [US2] Finish the state machine in `harness/export_layers.py` (exporting/done no-op
      return with zero calls; failed accepts retry; refuse unless `gate_state.state == "done"`)
      and add to `frontend/server.py`: `decide_export(run_dir, per_image_usd)` (HTTP-free,
      mirrors `decide_confirm`: 404 missing run/source, 409 gate-not-done or zero elements,
      no-op 200 exporting/done with "no second spend", accept from absent/failed writing
      state="exporting" BEFORE launch), `POST /run/<id>/export` (single-flight `_inflight`,
      background subprocess `.venv/bin/python harness/export_layers.py --run-dir <dir>`), free
      `GET /run/<id>/export/plan`, `GET /run/<id>/layers.zip` (404 until done); and the additive
      `export` stage in `frontend/run_view.py` (state + manifest-so-far + zip_ready; absent =
      present:false + "not exported; export is opt-in and paid"; never raises). Tests: check5
      (state on disk before the first stub call; second invocation ZERO generate calls; retry
      from failed accepted, from done refused) + check7 (decide_export + plan endpoint semantics
      HTTP-free: each code/payload/launch triple asserted, incl. 409 on an awaiting gate and
      no-op payload wording). Commit: `feat(016): pre-spend state machine + export routes + stage (T005)`.

- [x] T006 [US2] `frontend/index.html`: after the image stage, an "Export layers" button labeled
      from `GET /run/<id>/export/plan` ("paid, ~$X for N images"), never automatic or
      pre-selected; click POSTs `/run/<id>/export` then polls the run view; render per-layer
      progress rows (ok / null + note) from the export stage; `layers.zip` download link when
      done; failures surfaced. Test: check6a form greps (falsifiable: the button markup exists,
      is type=button not auto-submit, the label templates cost from the plan payload, the zip
      href present) per the project's existing form-grep pattern. NOTE for the operator: restart
      `frontend/server.py` after this lands (server code loads once). Commit:
      `feat(016): export button + per-layer progress + download (T006)`.

**Checkpoint**: browser flow complete; spend guarded exactly like generation.

---

## Phase 5: User Story 3 - Honest per-layer nulls and audit trail (P3)

**Goal**: the manifest is a complete audit record; nothing fabricated anywhere.

**Independent Test**: manifest field-completeness asserted per layer against the data model.

- [x] T007 [US3] Harden the audit surface in `harness/export_layers.py`: every layer record
      carries id/kind/prompt/status/note/opaque_frac/stray_component_px_dropped/despilled_px/
      green_residual_px_in_preview/bbox/files exactly per data-model.md; manifest root carries
      source_image + size + the flagged background entry; `export_state.json` carries plan +
      cost_stated + timestamps (+ error when failed). Test: extend check4 into check4b asserting
      the FULL record schema on ok AND null layers (missing-field = fail; a wrong build that
      drops stats cannot pass) and that the background entry is `model_continued: true`.
      Commit: `feat(016): complete audit manifest (T007)`.

---

## Phase 6: Polish & Cross-Cutting

- [x] T008 Byte-identity + no-regression + docs currency: check8 tree-hashes an unexported
      fixture run dir before/after module import AND run_view render (identical); a pre-016 run
      dir renders exactly as before plus the honest-null export stage (compare against a pinned
      pre-016 render literal); run the FULL prior self-test sweep unchanged (conductor,
      confirm_gate, render_and_scrub, render_modes, register_render_aware, product_refs,
      frontend suites, thin_route et al.); update CLAUDE.md (active-feature block: BUILT +
      structurally green) + SYSTEM_MAP (016 build-status block) in this same commit.
      Commit: `test(016): byte-identity + full sweep + docs currency (T008)`.

- [ ] T009 HUMAN EYE-GATE (SC-007, quickstart §4; the ONE paid step, operator-scheduled, never
      automated): on a real judged CJXQ run, click Export (cost as stated), download layers.zip,
      stack each `<id>.png` over `background.png` in an image editor; judge: each layer reads as
      its element, position drift acceptable for a draft decomposition, nulls honest (raw shows
      why). Record the verdict + run id in SYSTEM_MAP and here.

---

## Dependencies & Execution Order

- **T001 -> T002** (fixtures before the pure half's tests).
- **T002 blocks everything downstream** (enumeration/prompts/plan are the shared foundation).
- **US1**: T003 -> T004 (orchestrator calls key_layer).
- **US2**: T005 needs T004 (it wraps the orchestrator); T006 needs T005 (button hits the routes).
- **US3**: T007 needs T004 (extends the manifest the orchestrator writes).
- **Polish**: T008 after all code tasks; T009 after T008 and human-scheduled.
- Parallel opportunities are limited by the one-file test convention and the module being one
  file: the real sequence is linear T001..T008. [P] deliberately not used.

## Implementation Strategy

MVP = Phase 1-3 (T001-T004): a CLI-driven export engine, fully testable free with a stub and
usable paid from the command line. Phases 4-5 make it a guarded browser feature; Phase 6 proves
the world unchanged and hands the pixels to the eye. Stop-and-validate at every checkpoint:
`.venv/bin/python test_export_layers.py` stays green cumulatively.
