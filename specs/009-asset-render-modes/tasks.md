---
description: "Task list for Beyond Flat-vector Event Signs (Render Modes)"
---

# Tasks: Beyond Flat-vector Event Signs (Render Modes)

**Input**: Design documents from `specs/009-asset-render-modes/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-30: photo any-register + render_style carrier), research.md (D1-D5, opener wording CONFIRMED), data-model.md, contracts/ (render-style + thin-opener), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests assert the assembled prompt STRING (dialect switch, opener matrix, negatives split), the `normalize_render_style` mapping, the `build_plan` thin argv, and the inputs round-trip. NO paid model calls. SC-007 (does the output actually look photographic) is the LOAD-BEARING human eye-gate, NOT automatable - a green structural test proves only that the dialect SWITCHED.

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project. Generation dialect: `harness/scene_author.py` (`assemble_thin_prompt` opener + negatives). Plumbing: `harness/conductor.py` (render_style -> asset_profile + thin argv + manifest), `frontend/inputs_writer.py` (carry render_style), `frontend/index.html` (the control). Self-test as `test_render_modes.py` at repo root. Thin route ONLY; the flat event-sign path stays byte-identical. Confirmed opener wording is verbatim (research.md Decision 2 / data-model.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The test scaffold + shared fixtures all three stories assert against. No engine edit yet.

- [X] T001 [P] Create `test_render_modes.py` (stdlib, no paid calls) with shared fixtures: a minimal brand key (`fields.brand_name_cn/en` + a small `colors.items`), an event_prop register profile (`{"inferred_register": "event_prop"}`) and a marketing register profile (`{"inferred_register": "marketing"}`), and import wiring for `harness/scene_author.py` + `harness/conductor.py`. Add a first sanity check: `scene_author.ASSET_PROFILES` defines both `photo` and `flat_graphic`. (The per-story checks land in T002/T004/T006.)

**Checkpoint**: the test scaffold + fixtures exist; the dialects are present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None beyond Setup. The change is localized; US1/US2 edit `assemble_thin_prompt` (sequential, same function), US3 edits the plumbing (different files). No shared engine scaffolding is needed first.

**Checkpoint**: user-story work can start.

---

## Phase 3: User Story 1 - Choose a render style and generate in it (Priority: P1) 🎯 MVP

**Goal**: The photographic render dialect exists in the thin prompt: a photographic brief yields photographic language (no flat-vector negatives), while keeping the text guards.

**Independent Test**: `assemble_thin_prompt(..., asset_profile="photo", ...)` contains photographic language and NOT "FLAT VECTOR" / "no photographic shading", but keeps the text guards (verbatim headline, no extra Chinese / no gibberish). A build that ignores the profile still says flat vector and fails. Free, no model calls.

### Tests for User Story 1

- [X] T002 [US1] Add to `test_render_modes.py` the photo-dialect checks: `assemble_thin_prompt(key, ["守住钱袋子"], register_profile=<marketing>, asset_profile="photo", has_reference=True)` -> the prompt CONTAINS photographic language ("PHOTOGRAPHIC" / "photographic realism") and does NOT contain "FLAT VECTOR" or "no photographic shading"; it STILL contains the text guards ("no extra Chinese", "no gibberish") and the verbatim headline (守住钱袋子). Also assert the photo + event_prop opener works (photographic + prop framing, no error). MUST FAIL before T003.

### Implementation for User Story 1

- [X] T003 [US1] In `harness/scene_author.py` `assemble_thin_prompt` (def `:844`), add the two PHOTOGRAPHIC openers (photo + event_prop; photo + marketing/formal) per the CONFIRMED verbatim wording (research.md Decision 2), replacing the weak non-graphic `else` opener (`:878`, "A promotional marketing asset for..."); and SPLIT the thin NEGATIVES line (`:952`): a render-agnostic text-guard clause (no gibberish / no extra Chinese / no tagline / no watermark) applied in BOTH modes, plus a flat-only render clause (no photographic shading, no 3D realism) so the flat NEGATIVES line stays byte-identical. Do NOT touch the flat opener branches in this task (that is US2). `test_render_modes.py` US1 checks pass.

**Checkpoint**: the photographic dialect is live in the thin prompt (driven by asset_profile). MVP dialect.

---

## Phase 4: User Story 2 - Framing follows the asset, not a hard-coded event sign (Priority: P1)

**Goal**: A flat brief in a marketing / wall-posted register reads as a rectangular poster, not a hand-held event sign; the flat event-prop framing is unchanged.

**Independent Test**: `assemble_thin_prompt(..., asset_profile="flat_graphic", register=<marketing>)` opener does NOT contain "hand-held event sign" and reads as a rectangular poster; `register=<event_prop>` opener is byte-unchanged (die-cut prop + the flat render negatives). Free, no model calls.

### Tests for User Story 2

- [X] T004 [US2] Add to `test_render_modes.py` the framing checks: flat + marketing register -> the opener does NOT contain "hand-held event sign" AND DOES contain rectangular-poster language ("rectangular", "poster" or "flyer"). Assert PRESENCE, not only absence: a pure-absence check is a no-op gate (§III) because the event_prop opener says "hand-held event photo-prop sign" (a superstring), so absence of the exact substring "hand-held event sign" does not distinguish the rewrite. flat + event_prop register -> the opener contains "hand-held event photo-prop sign" + "die-cut" AND the NEGATIVES line contains "no photographic shading" (byte-unchanged regression). MUST FAIL before T005.

### Implementation for User Story 2

- [X] T005 [US2] In `harness/scene_author.py` `assemble_thin_prompt`, rewrite the flat non-event_prop opener (the `elif is_graphic` branch, `:872-877`, currently "a designed hand-held event sign") to the CONFIRMED rectangular marketing poster wording (no "hand-held event sign", no em-dash, research.md Decision 2). Leave the `is_graphic and is_event_prop` branch (`:866-871`) BYTE-IDENTICAL (regression). `test_render_modes.py` US2 checks pass.

**Checkpoint**: flat framing is register-aware; the event-sign path is unchanged.

---

## Phase 5: User Story 3 - The choice reaches generation; the existing path is unchanged (Priority: P1)

**Goal**: The designer's `render_style` flows from the brief through the conductor to the generation step (no more hard-wired flat), defaulting to flat vector with the event-sign output unchanged.

**Independent Test**: `normalize_render_style` maps photographic->photo, else->flat_graphic; `build_plan` for a photographic brief -> the thin argv carries `--asset-profile photo` (not the flat default); a default brief -> flat; `inputs_writer` round-trips `render_style`; the served page has the control. Free, no model calls.

### Tests for User Story 3

- [X] T006 [US3] Add to `test_render_modes.py` the plumbing checks: `conductor.normalize_render_style("photographic") == "photo"`, `("flat vector") == "flat_graphic"`, `("") == ("zzz") == "flat_graphic"` (fallback); `conductor.build_plan(<inputs with render_style="photographic">, "aia", <tmp>, no_approve=True, thin=True)` -> the scene_author thin argv contains `--asset-profile photo` (and a default-render_style brief -> `--asset-profile flat_graphic`); `inputs_writer.to_inputs({... "render_style": "photographic" ...})["render_style"] == "photographic"` and a brief without it defaults to flat vector; `frontend/index.html` contains a render-style control (grep). MUST FAIL before T007/T008/T009.

### Implementation for User Story 3

- [X] T007 [US3] In `harness/conductor.py`: add `normalize_render_style(value) -> asset_profile` (mirrors `normalize_dial`: "photographic"->"photo", else->"flat_graphic", case/space-insensitive, fallback flat_graphic); give `_scene_author_thin_argv` (`:228`) a new `asset_profile` param (default `ASSET_PROFILE`) used in `--asset-profile`; in `build_plan` read `inputs.get("render_style")`, map it, and pass it to `_scene_author_thin_argv` (`:359`); record `render_style` (raw) + resolved `asset_profile` in the manifest and update the thin-path "ALWAYS flat_graphic" notes (`:402-403/:970-971`). Leave the kit/legacy/no-ref argv builders (`:188/:219`) on `ASSET_PROFILE`. `test_render_modes.py` plumbing checks pass.
- [X] T008 [P] [US3] In `frontend/inputs_writer.py` `to_inputs`: carry `render_style` VERBATIM into the inputs dict (default "flat vector" when absent); pure pass-through, no mapping here; the other fields stay verbatim (002 invariant).
- [X] T009 [P] [US3] In `frontend/index.html`: add a Render style control (a `<select>` flat vector / photographic), defaulting to flat vector, and include `render_style` in the posted `formState()`. No em-dashes.

**Checkpoint**: a designer's render choice reaches generation; default flat vector; event-sign output unchanged.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the LOAD-BEARING human eye-gate.

- [X] T010 [P] Update `CLAUDE.md` + `SYSTEM_MAP.md` in the same commit that makes them stale (§VII): the task now drives render mode + framing on the thin route (`render_style` -> `normalize_render_style` -> `asset_profile`; the (asset_profile x register) opener matrix; the negatives split; flat event-sign byte-unchanged); thin route only; photo any-register; SC-007 the load-bearing eye-gate. Note the deferred items (kit/legacy/no-ref/cutout generalization; asset_type-driven opener specificity).
- [X] T011 [P] Run the free structural suite and paste real output: `test_render_modes.py` (all checks), `test_thin_route.py` + `test_conductor.py` (regression), `test_palette_roles.py` + `test_frontend_intake.py`; confirm the prior 001-008 suites stay green. ALSO assert FR-011 structurally: the served `index.html` user-facing strings contain NO em-dash (`—`) (a free grep), and the NEW openers in `scene_author.py` contain no em-dash (the event_prop opener keeps its pre-existing one by design).
- [ ] T012 The LOAD-BEARING human eye-gate (SC-007, NOT automated; folds into the back-half paid run): generate with render style = photographic in a wall-posted (marketing) usage and judge `output/run_*/sign_*/final.png` by EYE (§II) - does it actually read as a PHOTOGRAPHIC poster (real photography, depth, lighting), not flat illustration? Then a flat brief in a marketing usage -> a rectangular poster, not a die-cut sign. A green structural test proves only the dialect SWITCHED; only the eye confirms the output. Record the verdict in `SYSTEM_MAP.md`. Needs spend + the human; left for the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; the test scaffold + fixtures.
- **Foundational (Phase 2)**: none beyond Setup.
- **US1 (Phase 3)**: after Setup. The photographic dialect + negatives split in `assemble_thin_prompt`. MVP dialect.
- **US2 (Phase 4)**: after US1 (edits the SAME function `assemble_thin_prompt`, a different branch - sequential on that file).
- **US3 (Phase 5)**: after Setup; largely INDEPENDENT of US1/US2 (different files: conductor / inputs_writer / index.html). Can proceed in parallel with US1/US2.
- **Polish (Phase 6)**: after US1 + US2 + US3.

### Within Each User Story

- The test task (test-first) is written and MUST FAIL before its implementation tasks.
- `scene_author.py` `assemble_thin_prompt` is touched by US1 (T003: photo openers + negatives) then US2 (T005: flat-marketing opener) - same function, sequential.
- US3: `normalize_render_style` + the thin argv (T007) gate the build_plan check; inputs_writer (T008) and index.html (T009) are different files and parallel.
- Commit after each task (§VII).

### Parallel Opportunities

- Setup: T001 alone.
- US3: T008 (inputs_writer) ∥ T009 (index.html) are different files; T007 (conductor) is independent of both.
- US1/US2 (scene_author) can run in parallel with US3 (conductor/frontend) - different files.
- Polish: T010 ∥ T011 (docs vs running self-tests).
- The per-story checks all live in `test_render_modes.py`, so they are added sequentially to that file.

---

## Parallel Example: kicking off

```bash
# Setup, then the engine dialect (US1) and the plumbing (US3) in parallel (different files):
Task: "T001 Create test_render_modes.py scaffold + fixtures"
Task: "T003 Add photographic openers + split negatives in scene_author.py"   # US1
Task: "T007 normalize_render_style + thread asset_profile in conductor.py"     # US3
```

---

## Implementation Strategy

### MVP First (Setup + US1)

1. Phase 1 Setup (the test scaffold + fixtures).
2. Phase 3 US1 (the photographic dialect + negatives split): a photographic brief assembles a photographic prompt.
3. **STOP and VALIDATE**: `test_render_modes.py` US1 checks green + `test_thin_route.py` green - the dialect switches, all free. (The live-runner can drive it once US3 lands.)

### Incremental Delivery

1. Setup → the test scaffold.
2. US1 → the photographic dialect (MVP).
3. US2 → register-aware framing (flat marketing != event sign; event_prop unchanged).
4. US3 → the choice reaches generation (the live-runner drives the mode; default flat vector; event-sign unchanged).
5. Polish → durable docs, free suite green, then the LOAD-BEARING human eye-gate (the real proof).

### Notes

- [P] = different files, no incomplete dependencies.
- NO paid model calls in ANY automated test (§ Cost discipline). Tests assert the prompt STRING + the mapping + the argv + the inputs round-trip; never generate. Only T012 (the photographic sign) spends, and it is the LOAD-BEARING eye-gate (§II) - this feature's value is NOT structurally provable.
- Agent-free (§I): the human picks the render style; no classifier.
- GENERALIZES (§IV): the opener/negatives logic is task-general (asset_profile x register); no one-image tuning.
- Reconciliation per-dimension (§VI): brand HARD (color/font/logo unchanged), task SOFT (render style + shape). The flat event-sign path is byte-unchanged (FR-007 / SC-005).
- Honest-null (§V): unrecognized / omitted render_style -> flat vector, recorded in the manifest.
- Thin route ONLY; kit / tier-3 / no-reference / legacy / measure-composite UNCHANGED; conductor input contract changes only by adding the `render_style` carrier.
- No em-dashes in NEW user-facing text (the control + the new openers); the existing event_prop opener keeps its pre-existing em-dash to preserve byte-identity.
