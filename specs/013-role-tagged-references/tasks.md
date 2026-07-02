# Tasks: Role-Tagged References (Style + Product)

**Input**: Design documents from `/specs/013-role-tagged-references/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/product_refs_contract.md, quickstart.md

**Tests**: Included inside every implementation task (constitution III; one task, one module,
one falsifiable test, one commit; the test lands in the SAME commit as the code it gates). All
tests FREE. Contract rows refer to
[contracts/product_refs_contract.md](contracts/product_refs_contract.md).

**Organization**: grouped by user story. Engine assertions are VALUES; form checks are greps
(the weakest gate, declared per the 010 precedent).

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Repo root, flat layout: engine `harness/scene_author.py`, orchestrator `harness/conductor.py`,
generation wrapper `harness/generate.py` (NOT touched), form `frontend/index.html`, server
`frontend/server.py`, writer `frontend/inputs_writer.py`, self-tests `test_*.py` in root.

---

## Phase 1: Setup

**Purpose**: baseline green + the two byte-identity references (prompt AND refs list).

- [X] T001 Run the 6 existing free suites and record them green BEFORE any edit
      (`test_conductor.py`, `test_render_and_scrub.py`, `test_render_modes.py`,
      `test_register_render_aware.py`, `test_frontend_nav.py`, `test_lossless_brief.py`).
      Capture TWO pre-013 baselines to the session scratchpad, both reused as inlined literals
      in `test_product_refs.py`: (a) the `assemble_thin_prompt` output for the SAME fixture
      test_lossless_brief uses (minimal inline brand key, one message, marketing register,
      photo profile, has_reference=True, no notes), as `EXPECTED_PREFEATURE_PROMPT`; (b) the
      thin-route refs-list construction shape `[style_ref, logo]` noted from
      `harness/scene_author.py` ~1055-1063 (the T004 test asserts list equality directly, no
      dump needed; record the line region). No repo file changes; if anything is red, STOP and
      report (honest nulls).

---

## Phase 2: Foundational (Blocking Prerequisites)

None. The slices layer outward from the engine (US1) to the form (US3); no shared new
infrastructure beyond the T001 baselines.

---

## Phase 3: User Story 1 - Real product shots appear in the composition (Priority: P1) 🎯 MVP

**Goal**: product image paths flow from the brief through the conductor into scene_author, into
the PRODUCT FIDELITY prompt section and the generation refs list, and into the manifests;
calibration provably never sees them.

**Independent Test**: brief with `product_images` -> both call sites' argv carry repeatable
`--product-image` in order; the prompt carries the fidelity section; refs == [style, logo] +
products; calibrate argv identical with/without products.

- [X] T002 [US1] Engine half in `harness/scene_author.py`: argparse gains `--product-image`
      with `action="append"` (default None; ordered list); `assemble_thin_prompt` gains
      `product_images=None` and emits the PRODUCT FIDELITY section (research D3 wording: the N
      additional supplied image(s) are the brand's REAL products; carry exactly: same shapes,
      same printed branding and label text, same colors; do NOT redraw as generic products;
      only their backgrounds may be discarded) placed with the reference-exemplar note block;
      absent/empty = NO section. The thin refs construction (~line 1055) APPENDS the product
      paths after the existing [style_ref, logo] (research D2: prefix byte-stable); the thin
      run manifest gains `product_images`. Create `test_product_refs.py` (repo test style)
      covering contract rows 1-2 (section values verbatim + no-products prompt byte-identical
      to the inlined `EXPECTED_PREFEATURE_PROMPT`), row 4 (argparse append order), rows 6-7
      (refs list equality: [style, logo] + products with products, exactly [style, logo]
      without; assert by calling the refs-building logic or monkeypatching generate_variant to
      capture its argument, NO paid call), and row 12 (no em-dash in the new section).
      Commit: `feat(013): product fidelity section + generation feed in scene_author (T002)`.

- [X] T003 [US1] Conductor half in `harness/conductor.py`: module constant
      `MAX_PRODUCT_IMAGES = 6`; `validate_inputs` fail-louds (named error, no launch) on
      >6 `product_images` entries or a listed file missing on disk (contract row 5);
      `_scene_author_thin_argv` gains `product_images=None` appending one `--product-image
      <path>` per entry in order; BOTH call sites (build_plan thin loop AND execute thin loop)
      pass `inputs.get("product_images")` (the twice-caught drift lesson);
      `conductor_manifest` records `product_images` (FR-006). Tests in `test_product_refs.py`:
      contract row 3 (carried in order at BOTH sites via the stubbed-`run_step` execute
      pattern; absent entirely when the brief lacks the key), row 5 (over-cap + missing-file
      fail loud), row 8 (the calibrate step argv is IDENTICAL for the same brief with and
      without product_images: calibration isolation, SC-003), row 14 (a legacy brief without
      the key plans byte-identically).
      Commit: `feat(013): thread product_images at BOTH call sites + cap + isolation (T003)`.

**Checkpoint**: the engine path is complete: a CLI brief with product_images reaches generation
with the images and the instruction. MVP for CLI users.

---

## Phase 4: User Story 2 - Style-only briefs behave exactly as today (Priority: P1)

**Goal**: the shipped single-reference flow is provably untouched, end to end.

**Independent Test**: no-products prompt byte-identical (already pinned in T002); the full
existing suite sweep passes; a pre-013 inputs JSON produces an identical plan.

- [X] T004 [US2] No-regression proof in `test_product_refs.py` (contract rows 7, 13, 14
      consolidation): assert the zero-products refs list equals exactly [style_ref, logo]
      (pre-feature equality); assert a verbatim pre-013 thin inputs dict (the
      test_lossless_brief fixture shape) produces a build_plan whose scene_author argv contains
      NO `--product-image` and whose calibrate argv is unchanged; run and record the 6-suite
      sweep green (SC-005). Test-only change.
      Commit: `test(013): style-only path byte-identical end to end (T004)`.

**Checkpoint**: both P1 stories done; every existing brief provably unaffected.

---

## Phase 5: User Story 3 - The form captures roles (Priority: P2)

**Goal**: the browser can supply product shots: multipart capture -> shared save_upload ->
`form["product_images"]` -> the T003 threading; the old flow untouched when the control is
left empty.

**Independent Test**: parse_run_form handles 0/2/7 product parts (7 rejects naming the cap);
write_run_inputs saves `product_<i>.<ext>` via the shared home and injects the paths; the
served form has the relabeled style upload + the optional multi-file control with distinct
part naming.

- [X] T005 [US3] Server half in `frontend/server.py` + `frontend/inputs_writer.py`:
      `parse_run_form` also collects file parts named `product_*` (sorted by their numeric
      suffix), raises ValueError naming the cap of 6 when exceeded (visible form error, no
      launch, contract row 9); `write_run_inputs` saves each via the shared
      `uploads.save_upload(name=f"product_{i}{ext}")` into the run dir and injects
      `form["product_images"]` (saved paths, in order); `inputs_writer.to_inputs` passes
      `product_images` through verbatim when present, key ABSENT when not (byte-compat).
      Tests: contract rows 9-10 (0/2/7-part parse cases; saved names + injected paths; the
      0-part case byte-identical to today's parse result).
      Commit: `feat(013): multipart product uploads through the shared save_upload home (T005)`.

- [X] T006 [US3] Form half in `frontend/index.html`: relabel the existing reference upload
      "Style reference (how the asset should feel; required)"; add an optional
      `<input type="file" id="product_images" multiple>` labeled "Product shots (optional,
      up to 6): photos of the real products that must appear in the design"; `startRun`
      appends each selected file as a DISTINCT part `product_1`..`product_N` (research D5:
      the multipart parser is last-wins per name) and client-side rejects >6 with a visible
      message before submitting. Tests: contract row 11 greps (style-reference label, the
      multiple-file control, the distinct part-name loop in the JS) + row 12 (no em-dash in
      the new labels).
      Commit: `feat(013): style + product upload controls on the run form (T006)`.

**Checkpoint**: full browser flow: upload cups, run, audit the manifest.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T007 Full validation per quickstart §1-3: `test_product_refs.py` + the 6-suite sweep,
      the dry-run plumbing check (plan.json argv carries ordered `--product-image`, calibrate
      argv unchanged), and a served-page eyeball of the two upload controls. Fix anything red;
      commit only if fixes were needed.

- [X] T008 Repo currency in the closing commit (constitution VII): `CLAUDE.md` (active feature
      012 -> prior, 013 built + structurally green, eye-gate pending; note the brand-level
      product-library deferral to 015) and `SYSTEM_MAP.md` (013 build-status block: the role
      seam, the two asset homes, the cap, the test surface). No em-dashes in new text.
      Commit: `docs(013): CLAUDE.md + SYSTEM_MAP currency (T008)`.

- [ ] T009 DEFERRED HUMAN EYE-GATE (SC-006, quickstart §4): ONE paid rerun of the CJXQ
      watermelon brief WITH the branded cup shots uploaded as product references, judged by
      the operator against `run_CJXQ_20260701_164912`: the actual 茶救星球 JO'S CHA cups
      (printed logos visible) appear instead of generic look-alikes; the 012 run's style/scene
      quality retained; no new text leakage. Never run inside automation. Record the verdict
      in SYSTEM_MAP.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: first, must be green.
- **US1 (T002 → T003)**: T002 creates the flags + test file; T003's threading depends on
  T002's flags existing. Same test file, sequential.
- **US2 (T004)**: needs T002+T003 (asserts against their surfaces). Test-only.
- **US3 (T005 → T006)**: T005 (server/writer) is independent of T004 and could start after
  T003; T006 (form) last so the client cap message matches the server's. Sequential on the
  shared test file.
- **Polish (T007 → T008 → T009)**: after all code tasks; T009 is human-scheduled.

### Parallel Opportunities

- T005 (frontend/server.py + inputs_writer.py) ∥ T004 (test-only) after T003, if desired; they
  share `test_product_refs.py`, so the linear order is the low-friction default. Everything
  else serializes on the engine files or the shared test file.

---

## Implementation Strategy

**MVP = Phase 1 + Phase 3 (US1)**: after T003 a CLI brief carries product truth end to end,
which already unblocks the eye-gate scenario by hand-editing an inputs JSON. Phase 4 locks the
no-regression proof before the UI grows. Phase 5 makes it a browser feature. T009 (the paid
branded-cups rerun) runs once at the end: whether SUPPLYING the product wins on pixels is the
question only the eye can answer.
