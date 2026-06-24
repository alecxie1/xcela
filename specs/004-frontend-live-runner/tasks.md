---
description: "Task list for Frontend Live-Runner (single-sign)"
---

# Tasks: Frontend Live-Runner (single-sign)

**Input**: Design documents from `specs/004-frontend-live-runner/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-24: progressive stages + new-run-per-nudge), research.md (D1-D6), data-model.md, contracts/ (4 files), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests assert VALUES a wrong build fails; they NEVER call gpt-image-2 (§ Cost discipline) — they target the pure modules (`inputs_writer`, `run_view`, `runner.build_conductor_argv`) + a conductor dry-run. Pixel quality is human-eye only (§II).

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project + a NEW thin local web frontend in `frontend/` (stdlib `http.server` + one static page; no new deps). Engine reuse in `harness/`. Self-tests as `test_*.py` at repo root. Run artifacts under `output/run_*/` (gitignored).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Stand up the `frontend/` package the UI modules live in.

- [X] T001 Create the `frontend/` package: `frontend/__init__.py` (empty) and a short `frontend/README.md` noting it is a THIN local web frontend over the agent-free CLI (stdlib only, no new deps; the standalone CLI runs without it). Confirm `frontend/` is git-tracked (not gitignored).

**Checkpoint**: `frontend/` exists for the UI modules.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The ONE engine change — a non-interactive `conductor --style-notes` pass-through — so the browser taste gate's nudge is a plain CLI call (the brief's flagged open question). Blocks US3's nudge end-to-end.

**⚠️ CRITICAL**: The nudge-rerun cannot reach generation until the conductor accepts `--style-notes` non-interactively.

- [X] T002 [P] Update `test_conductor.py`: add a check that `conductor.py --brand aia --thin --style-notes "x" --dry-run --inputs <single>` threads `--style-notes x` into the thin `_scene_author_thin_argv`, AND that the standalone thin route still runs from one command (no UI). MUST FAIL before T003.
- [X] T003 Add a top-level `--style-notes` flag to `harness/conductor.py` (campaign-level), threaded into `_scene_author_thin_argv` via `execute` on the thin route (the conductor already threads it on the INTERACTIVE nudge path and `assemble_thin_prompt` consumes it; this exposes the same non-interactively). No other conductor change (single-sign already runs: the per-sign loop runs once for a 1-entry `signs[]`). `test_conductor.py` passes.

**Checkpoint**: A nudge is a plain `conductor --thin --no-approve --inputs X --style-notes "note"` call; reruns stay in the agent-free CLI.

---

## Phase 3: User Story 1 - Single-sign structured intake (Priority: P1) 🎯 MVP

**Goal**: A structured form's filled state becomes a single-sign 002-shape inputs JSON, verbatim, that the real conductor accepts.

**Independent Test**: `test_frontend_intake.py` green — the written JSON's `messages`, `mandatory_elements`, and the three vibe integers equal the typed values byte-for-byte; `signs[]` has exactly one entry; the JSON passes `conductor.validate_inputs`. Free, no model calls.

### Tests for User Story 1

- [X] T004 [P] [US1] Write `test_frontend_intake.py`: build a single-sign form state, call `inputs_writer`, and assert the JSON has exactly ONE `signs[]` entry; `messages` / `mandatory_elements` / `vibe.formality|playfulness|warmth` equal the typed values byte-for-byte (no rephrase/reorder/inferred field); a blank optional → empty (honest null); and the result passes `conductor.validate_inputs`. MUST FAIL before T005.

### Implementation for User Story 1

- [X] T005 [US1] Implement `frontend/inputs_writer.py` (pure, stdlib): `to_inputs(form_state) -> dict` building the 002-shape single-sign inputs per `contracts/inputs-json.md` (one `signs[]` entry; verbatim; `reference_image` required; renders the 002 contract, NOT the stale `brief_schema.json`) + `write_inputs(form_state, path)`. `test_frontend_intake.py` passes.

**Checkpoint**: The form's output is a lossless, CLI-valid single-sign brief. MVP intake.

---

## Phase 4: User Story 2 - Live run with inspectable stages (Priority: P1)

**Goal**: Press Run → the thin route executes via the existing CLI → the UI surfaces each stage PROGRESSIVELY from the run dir (brief → dial → assembled prompt → sign), the dial + prompt before the paid image.

**Independent Test**: `test_frontend_stages.py` + `test_frontend_runner.py` green (stage reader honest-null/progressive; argv builder), plus a server GET smoke. Free, no model calls.

### Tests for User Story 2

- [X] T006 [P] [US2] Write `test_frontend_stages.py`: over a SYNTHETIC run dir with `register_profile.json` + `sign_s1/final_prompt.txt` but NO `sign_s1/generated.png`, assert `run_view` reports `register` + `prompt` present and `image` absent (progressive surface); a missing artifact yields `present: false` + the manifest note (honest null), never a fabricated value; a nonexistent run dir yields all-absent (no crash). MUST FAIL before T008.
- [X] T007 [P] [US2] Write `test_frontend_runner.py`: assert `build_conductor_argv(inputs, "aia")` contains `--thin --no-approve --inputs` and NO `--out`; `build_conductor_argv(inputs, "aia", style_notes="x")` additionally contains `--style-notes x` (verbatim). MUST FAIL before T009.

### Implementation for User Story 2

- [X] T008 [US2] Implement `frontend/run_view.py` (pure, stdlib): `run_view(run_dir) -> dict` reading the artifact PATHS per `contracts/stage-read.md` (brief, register_profile, final_prompt, generated.png, manifest notes); each stage `{present, content, note}`; honest null on missing; no recomputation. `test_frontend_stages.py` passes.
- [X] T009 [US2] Implement `frontend/runner.py`: pure `build_conductor_argv(inputs_path, brand, style_notes=None)` per `contracts/run-trigger.md` (always `--thin --no-approve --inputs`, no `--out`; `--style-notes` iff a note) + side-effecting `launch(argv) -> run_dir`. `test_frontend_runner.py` passes.
- [X] T010 [US2] Implement `frontend/server.py` (stdlib `http.server`): `GET /` (serve the page), `GET /brands` (ids from `answer_keys/*.json`), `POST /run` (`inputs_writer` → JSON, `runner.launch` → `run_id`; reject if no `reference_image`; single-flight), `GET /run/<id>/stages` (`run_view`), `GET /run/<id>/image` (serve `generated.png`, 404 until it lands). Never calls gpt-image-2 itself. Per `contracts/http-endpoints.md`.
- [X] T011 [US2] Implement `frontend/index.html` (structured form + progressive stages): the single-sign labeled form (brand dropdown from `/brands`, asset_type, format_size, reference picker REQUIRED, three vibe sliders, logo_treatment/brand_strictness enums, occasion/usage/audience, mandatory/forbidden chips, the one sign's messages), a Run button labeled with the real ~$0.08 cost, and stage panels that POLL `/run/<id>/stages` (~1s) rendering each stage as it lands (dial + prompt before the image). Inline vanilla JS, no framework. No em-dashes in any UI text.

**Checkpoint**: The operator can run a single-sign brief and watch the dial + prompt + sign appear live. (US1 + US2 = the operator-visible MVP.)

---

## Phase 5: User Story 3 - Human taste gate (approve or nudge-rerun) (Priority: P1)

**Goal**: After a run, two actions only — approve (stop) or nudge (binding note → regenerate into a NEW run dir, prior attempt preserved + comparable).

**Independent Test**: a nudge re-invokes the conductor with `--style-notes` and no `--out` (new run dir), and `run_view` can present two distinct attempt dirs (prior preserved). Free; the paid nudge is the human's.

### Tests for User Story 3

- [X] T012 [P] [US3] Extend `test_frontend_runner.py` with the taste-gate semantics: a NUDGE builds an argv carrying `--style-notes <note>` and NO `--out` (so a new run dir per attempt), and APPROVE triggers no new conductor call. Add a `test_frontend_stages.py` assertion that `run_view` over two distinct synthetic attempt dirs returns each independently (prior attempt preserved + comparable). MUST FAIL before T013 where it asserts new behavior.

### Implementation for User Story 3

- [X] T013 [US3] Implement the taste gate in `frontend/index.html` + `frontend/server.py`: after a run reaches the sign, expose exactly TWO controls — Approve (stop; mark the current attempt the deliverable) and Nudge (a binding-note field → `POST /run` with `style_notes` → a NEW `run_id`; render the new attempt while keeping the prior viewable to compare). Reject-without-rerun is NOT offered. The nudge cost is labeled. `test_frontend_runner.py` + `test_frontend_stages.py` pass.

**Checkpoint**: The human taste gate works end-to-end against the agent-free CLI; attempts are preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces (incl. regression), then the operator's paid run.

- [ ] T014 [P] Update `SYSTEM_MAP.md` + `CLAUDE.md` in the same commit that makes them stale (§VII): the frontend live-runner is built (thin local server over `conductor --thin`), how the taste gate reaches the conductor (the `--style-notes` pass-through; nudge = new run dir), and that brand-intake / campaign / ref-less remain future specs.
- [ ] T015 [P] Run quickstart steps 1-3 (`test_frontend_intake`, `test_frontend_stages`, `test_frontend_runner`, `test_conductor`) and confirm the prior regression suites stay green (001: test_kit/compose_select/fit_to_zone/kit_reserve_box; 002: format_size/faithful_intake/brief_wiring/review; 003 thin route via test_conductor/test_render_and_scrub). Server GET smoke: start `frontend/server.py`, fetch `/` + `/brands` + `/run/<id>/stages` over a pre-existing synthetic run dir, with NO paid call. ALSO add two falsifiable UI-string assertions (free, structural): (a) FR-013 — `frontend/index.html` + `frontend/server.py` user-facing strings contain NO em-dash (`—`); (b) FR-009 — the rendered `index.html` Run/nudge control contains the per-run cost label (e.g. the `$0.08` string). These turn the two prose-only rules into checked properties.
- [ ] T016 The operator's run (SC-001/SC-004, NOT automated): `.venv/bin/python frontend/server.py`, fill a single-sign AIA brief (one sign, a reference image, vibe sliders, `分别画叉`, `60x40cm`), press Run (~$0.08), watch the stages appear progressively, then approve OR nudge (binding note → new run dir) and judge by eye (§II). Record the verdict in `SYSTEM_MAP.md`. Needs spend + the human; left for the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: The conductor `--style-notes` change. BLOCKS US3's nudge end-to-end. Independent of US1 and US2's first-run (which uses no notes), so it can proceed in parallel with US1/US2.
- **US1 (Phase 3)**: After Setup. Independent (pure `inputs_writer`). The intake MVP.
- **US2 (Phase 4)**: After Setup. `run_view` (T008) + `runner` (T009) are independent pure modules (parallel with US1); the server (T010) needs `inputs_writer` (US1) + `runner` (T009) + `run_view` (T008); the page (T011) needs the server.
- **US3 (Phase 5)**: After US2 (reuses the runner + server + page) and Foundational (the conductor `--style-notes` flag, so the nudge actually reaches generation).
- **Polish (Phase 6)**: After US1+US2+US3.

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- US2: `run_view`/`runner` (+ their tests) before `server.py` (T010) before `index.html` (T011).
- US3: T013 edits `index.html` + `server.py` (after US2 built them).
- Commit after each task (§VII).

### Parallel Opportunities

- The three new pure-module tests — T004 (intake), T006 (stages), T007 (runner) — are all [P] and can be drafted together; T002 (conductor) is [P] too.
- `inputs_writer.py` (T005) ∥ `run_view.py` (T008) ∥ `runner.py` (T009) are different files.
- T014 ∥ T015 in Polish (docs vs running self-tests).

---

## Parallel Example: kicking off after Setup

```bash
# Four independent test files first (each MUST FAIL), then implement each module:
Task: "T002 conductor --style-notes check (Foundational)"
Task: "T004 Write test_frontend_intake.py (US1)"
Task: "T006 Write test_frontend_stages.py (US2)"
Task: "T007 Write test_frontend_runner.py (US2)"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Phase 1 Setup (`frontend/` scaffold).
2. Phase 3 US1 (`inputs_writer` + test): the form's output is lossless + CLI-valid (free).
3. Phase 4 US2 (`run_view` + `runner` + `server` + `index.html`): press Run, watch progressive stages.
4. **STOP and VALIDATE**: run the free self-tests + a GET smoke; the operator can drive a single-sign brief and watch the dial + prompt + sign appear. (Foundational `--style-notes` can land alongside.)

### Incremental Delivery

1. Setup → `frontend/` exists.
2. Foundational → the conductor accepts `--style-notes` non-interactively (nudge-ready).
3. US1 → lossless verbatim intake (MVP intake).
4. US2 → live run + progressive stages (operator-visible MVP).
5. US3 → the two-action taste gate, new run dir per nudge.
6. Polish → durable docs, free regression green, then the operator's paid run + eye verdict.

### Notes

- [P] = different files, no incomplete dependencies.
- No paid image generation in ANY automated test (§ Cost discipline). The server's `POST /run` shells out to the paid conductor only on a human click; tests target the pure modules + a conductor dry-run. Only T016 spends, eye-validated (§II).
- THIN posture (§I/§VII): the UI shells out to the CLI + reads artifacts; it never reimplements generation, register derivation, or prompt assembly. The standalone thin route still runs UI-absent (T015 / SC-005).
- Honest nulls (§V): a missing stage artifact is shown as the null + the manifest note, never fabricated.
- No em-dashes in any user-facing text (server, page) (Output rule).
