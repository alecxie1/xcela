# Tasks: Lossless Brief (Field Honesty on the Thin Route)

**Input**: Design documents from `/specs/012-lossless-brief/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/lossless_brief_contract.md, quickstart.md

**Tests**: Included inside every implementation task (constitution III: falsifiable tests are
mandatory; one task, one module, one falsifiable test, one commit; the test lands in the SAME
commit as the code it gates). All tests FREE. Contract row numbers refer to
[contracts/lossless_brief_contract.md](contracts/lossless_brief_contract.md).

**Organization**: grouped by user story. Form-surface assertions are greps (the weakest gate,
declared per the 010 precedent); everything engine-side asserts VALUES.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Repo root, flat layout: engine `harness/scene_author.py`, orchestrator `harness/conductor.py`,
form `frontend/index.html`, writer `frontend/inputs_writer.py`, self-tests `test_*.py` in root.

---

## Phase 1: Setup

**Purpose**: baseline green + the byte-identity reference for FR-003.

- [X] T001 Run the 5 existing free suites and record them green BEFORE any edit
      (`test_conductor.py`, `test_render_and_scrub.py`, `test_render_modes.py`,
      `test_register_render_aware.py`, `test_frontend_nav.py`). Capture the FR-003 baseline:
      import `scene_author` and dump `assemble_thin_prompt` output for ONE fixed fixture
      (minimal inline brand_key with 1 primary color, one message, a marketing register_profile
      dict, `asset_profile="photo"`, `has_reference=True`, no style_notes) to the session
      scratchpad; T002 inlines it as the `EXPECTED_PREFEATURE_PROMPT` literal in
      `test_lossless_brief.py`. The exact fixture is reused verbatim in T002. No repo file
      changes; if anything is already red, STOP and report (honest nulls).

---

## Phase 2: Foundational (Blocking Prerequisites)

None. The five deltas are independent slices over existing plumbing; no shared infrastructure is
needed beyond the T001 baseline. User story phases start directly.

---

## Phase 3: User Story 1 - Asset description and occasion reach the image (Priority: P1) 🎯 MVP

**Goal**: `asset_type` + `occasion` flow verbatim from the brief into the thin prompt as a
SCENE/SUBJECT context section; blank fields leave the prompt byte-identical.

**Independent Test**: assemble the thin prompt with distinctive values; both appear verbatim with
context-not-text framing; the both-blank case equals the pre-feature baseline byte for byte.

- [X] T002 [US1] Scene section in `harness/scene_author.py`: `assemble_thin_prompt` gains
      `asset_type=None, occasion=None`; emit the SCENE/SUBJECT section (research D2 wording:
      "compositional context ONLY, not text: no words from this section may be painted anywhere
      on the asset") immediately after the opener and before the HEADLINE block; render an
      `Asset:` line and/or `Occasion:` line only for non-empty values, NO section when both are
      empty; add CLI flags `--asset-type` / `--occasion` (default "") and pass them in the thin
      path. Create `test_lossless_brief.py` (repo test style) with contract rows 1-3: both
      values verbatim + framing line present + HEADLINE guard byte-unchanged (row 1); Asset line
      only, no empty Occasion scaffolding (row 2); both-blank output equals the
      `EXPECTED_PREFEATURE_PROMPT` literal from T001 byte for byte (row 3). No em-dash in the
      new section header (contract row 12).
      Commit: `feat(012): scene/subject section in the thin prompt (T002)`.

- [X] T003 [US1] Conductor threading in `harness/conductor.py`: `_scene_author_thin_argv` gains
      `asset_type=None, occasion=None` and appends `--asset-type` / `--occasion` exactly when
      non-empty; BOTH call sites pass them from the brief: build_plan's thin loop (~line 372)
      AND execute's thin loop (~line 880), applying the 009 drift lesson. Tests (contract row
      4): build_plan thin argv carries both flags verbatim for a brief that sets them and omits
      them for one that does not; the EXECUTE path asserted with the stubbed-`run_step` pattern
      (reuse the render_modes check-5 approach: capture the argv `execute()` constructs, no
      subprocess, no paid calls).
      Commit: `feat(012): thread asset_type + occasion at BOTH conductor call sites (T003)`.

**Checkpoint**: the reported defect (CJXQ asset description reaching nothing) is fixed end to end.

---

## Phase 4: User Story 2 - Design notes on the first run (Priority: P1)

**Goal**: a design-notes field on the form feeds the existing binding design-rules block on the
FIRST run; nudges append via the channel's ";"-join contract. Frontend-only (research D3).

**Independent Test**: form carries the field; the submitted `style_notes` string is the ";"-join
of notes + nudge; the split channel renders both as binding rules.

- [X] T004 [US2] Design notes in `frontend/index.html`: add a `design_notes` textarea (with a
      plain-language label: binding instructions the design must obey); compose the submitted
      form JSON's `style_notes` as the ";"-join of the non-empty `design_notes` value and any
      nudge text in `startRun` (first run: notes only; nudge re-run: notes + nudge, so the
      nudge APPENDS, contract row 6); server/runner/conductor untouched. Tests in
      `test_lossless_brief.py`: channel semantics rows 5-7 via the Python side
      (`assemble_thin_prompt` with the ";"-split of a joined string renders BOTH notes verbatim
      in the binding block; empty notes add no block, byte-identical); form greps row 10
      (`id="design_notes"` present; the join expression present in the page JS). No em-dash in
      the new label.
      Commit: `feat(012): design notes on the first-run form, nudges append (T004)`.

**Checkpoint**: MVP complete (US1 + US2): the two P1 stories deliver the lossless brief core.

---

## Phase 5: User Story 3 - No dead controls (Priority: P2)

**Goal**: audience + warmth controls gone from the form; legacy briefs keep working verbatim.

**Independent Test**: served page has neither control; a legacy form state carrying the fields
still lands in `context` unchanged.

- [X] T005 [US3] Remove the audience input and warmth slider (and their JS reads/label wiring)
      from `frontend/index.html`; `frontend/inputs_writer.py` stays tolerant (absent keys
      produce today's empty/None values; present keys pass through verbatim; hero_icon already
      has no control, writer tolerance only, research D4). Tests: contract row 8 greps (no
      `id="audience"`, no `id="warmth"`); row 13 back-compat (writer with legacy keys lands
      them in context verbatim; writer without them still produces a valid brief with the same
      shape as today).
      Commit: `feat(012): retire inert audience + warmth form controls (T005)`.

---

## Phase 6: User Story 4 - Reference relationship is a choice (Priority: P2)

**Goal**: the dial is captured as one of exactly 3 described options; the form can no longer
produce lossy prose. Engine untouched.

**Independent Test**: the select offers exactly `extend` / `match style` / `mood`; each maps 1:1
onto the engine lane; free-text legacy JSON still normalizes.

- [X] T006 [US4] Replace the `reference_relationship` free-text input in `frontend/index.html`
      with a `<select>` of exactly three options (values `extend`, `match style`, `mood`) whose
      labels describe each lane in plain language (research D5), e.g. keep-the-look /
      match-style-fresh-layout / loose-mood-cue. Tests: contract row 9 greps (select present,
      exactly those 3 option values, no free-text input for the field); row 14 VALUE mapping
      (`conductor.normalize_dial` maps the three submitted values to `extend` / `match_style` /
      `mood` respectively, and a legacy free-text phrase still normalizes through the keyword
      fallback unchanged).
      Commit: `feat(012): reference relationship becomes a 3-lane choice (T006)`.

---

## Phase 7: User Story 5 - The message field says what it is (Priority: P3)

**Goal**: no sign-era wording on the message field; the label states the verbatim-text contract.

**Independent Test**: served page contains no "Sign message" label; the new label says the text
is rendered verbatim and is the only words allowed.

- [X] T007 [US5] Rename the message label in `frontend/index.html` (currently "Sign message
      line(s) (one per line, verbatim)") to asset-generic verbatim-contract wording, e.g.
      "Text on the asset (one per line, rendered exactly as written: the only words that will
      appear)". Tests: contract row 11 (grep: "Sign message" absent; the new wording present)
      and row 12 (no em-dash in the new label).
      Commit: `feat(012): message label states the verbatim-text contract (T007)`.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T008 Full validation sweep per quickstart §1-3: `test_lossless_brief.py` + the 5 prior
      suites (SC-006), then the dry-run plumbing check (plan.json argv carries `--asset-type` /
      `--occasion`) and a served-page eyeball of the form deltas. Fix anything red; commit only
      if fixes were needed.

- [X] T009 Repo currency in the closing commit (constitution VII): `CLAUDE.md` (active feature
      becomes 012 built + structurally green, 011 moves to prior features) and `SYSTEM_MAP.md`
      (012 build-status block; date bump). No em-dashes in new text.
      Commit: `docs(012): CLAUDE.md + SYSTEM_MAP currency (T009)`.

- [ ] T010 DEFERRED HUMAN EYE-GATE (SC-007, quickstart §4): ONE paid re-brief of the CJXQ
      watermelon post through the form (photographic, asset_type + occasion filled, optional
      design note), judged by the operator against `output/run_CJXQ_20260701_154416`: subject
      fidelity improved AND zero scene/occasion words painted on the asset (the slogan-lesson
      leakage check) AND the design note visibly obeyed. Never run inside automation. Record
      the verdict in SYSTEM_MAP.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: first, must be green.
- **US1 (T002 → T003)**: T002 creates the flags + test file; T003 threads the conductor and
  depends on T002's flags existing.
- **US2 (T004)**: independent of US1 (different files); needs T002's test file to exist, so runs
  after T002. Frontend + test file only.
- **US3 (T005), US4 (T006), US5 (T007)**: all edit `frontend/index.html`, so they run
  sequentially after T004; ordered by story priority.
- **Polish (T008 → T009 → T010)**: after all code tasks; T010 is human-scheduled.

### Parallel Opportunities

- T003 (harness/conductor.py) ∥ T004 (frontend/index.html) once T002 lands, if desired; they
  touch disjoint files but share `test_lossless_brief.py`, so keeping the linear order is the
  low-friction default. Everything else is sequential on `index.html` or the shared test file.

---

## Implementation Strategy

**MVP = Phase 1 + Phase 3 + Phase 4 (US1 + US2)**: US1 repairs the reported intent loss; US2
exposes the strongest lever at brief time. Both are P1 and together they deliver "your words
reach the image". US3-US5 are small honesty increments in priority order. T010, the paid
eye-gate, runs once at the end when the operator is ready: subject fidelity and text-leakage are
pixel questions the structural suite cannot answer.
