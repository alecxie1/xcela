---
description: "Task list for Faithful Self-Service Brief Intake + Review"
---

# Tasks: Faithful Self-Service Brief Intake + Review

**Input**: Design documents from `specs/002-faithful-brief-intake/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-23; target-area size model + profile-agnostic), research.md (D1-D8), data-model.md, contracts/ (4 files), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory; the plan/data-model seed them. Tests assert VALUES a wrong build fails; they NEVER contain paid image generation (§ Cost discipline). Pixel quality is human-eye only (§II).

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project. Pipeline code in `harness/`, brand data in `answer_keys/` + `kits/`, self-tests as `test_*.py` at repo root. Outputs under `output/run_*/` (gitignored). The "surface" is an EXTENSION of the existing CLI form + a CLI review digest (no new UI stack).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Provide the faithful AIA brief fixture the wiring + intake tests run against.

- [X] T001 Update `conductor_inputs_example.json` to the faithful 6-sign AIA brief: all 6 signs, `mandatory_elements` = ["分别画叉", "设计两种样式"], `forbidden_elements` = [], top-level `format_size` = "60x40cm", the reference image + relationship, and the full `context` block. This is the fixture downstream tests read.

**Checkpoint**: A complete, faithful AIA brief exists as the conductor inputs fixture.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the conductor ACCEPT + carry the three previously-dropped fields end to end (the shared spine both US1 emit and US2 wiring build on). No size resolution or prompt injection yet.

**⚠️ CRITICAL**: US1 and US2 both depend on the conductor carrying these fields.

- [X] T002 Extend `harness/conductor.py` to accept the 3 new top-level inputs fields (`format_size`, `mandatory_elements`, `forbidden_elements`): `validate_inputs` stays BACK-COMPAT (the fields are optional; absent → empty/None, never invented); `build_plan` surfaces them in the dry-run plan; `build_compositions` attaches the campaign `mandatory_elements` / `forbidden_elements` VERBATIM to each per-sign `composition.json`. The conductor still emits `flat_graphic` and bakes in NO orientation/profile assumptions (asset_type captured, not yet used to select a profile — future spec).
- [X] T003 [P] Update `test_conductor.py`: assert the dry-run plan CARRIES the 3 new fields when present AND runs unchanged when ABSENT (back-compat); add the SC-004 STANDALONE proof — the conductor runs from a pre-written inputs JSON containing the new fields with NO intake form. Existing 5 checks stay green.

**Checkpoint**: The conductor losslessly carries the new fields; the standalone path is proven.

---

## Phase 3: User Story 1 - Self-service faithful intake (Priority: P1) 🎯 MVP

**Goal**: The human fills EVERY `brief_schema_v3` field through the extended CLI form, and the emitted conductor inputs + manifest are a lossless, verbatim image of the brief (no drop, no rephrase, no agent inference).

**Independent Test**: Drive `ask_questions` with a scripted 6-sign brief (incl. `format_size`, `mandatory_elements` with `分别画叉`, `forbidden_elements`) and confirm every field appears VERBATIM in the emitted inputs and the manifest, with 6 signs and a blank optional recorded empty. Free, no model calls.

### Tests for User Story 1

- [X] T004 [P] [US1] Write `test_faithful_intake.py`: drive `conductor.ask_questions` with an injectable `ask` over a full 6-sign brief; assert the emitted inputs contain EVERY entered field verbatim (asset_type, format_size, usage_context, audience, vibe, logo_treatment, brand_strictness, occasion, per-sign messages, mandatory_elements incl. `分别画叉`, forbidden_elements, AND the reference image + relationship per FR-006 002-scope), 6 signs (no collapsing), literal text byte-for-byte unchanged, and a blank optional recorded empty (honest null). MUST FAIL before T005.

### Implementation for User Story 1

- [X] T005 [US1] Extend `harness/conductor.py` `ask_questions` to capture ALL `brief_schema_v3` fields: add prompts for `format_size`, `mandatory_elements` (semicolon-separated, verbatim), `forbidden_elements` (semicolon-separated, verbatim), and make `usage_context` + `audience` explicitly askable (defaulting to today's derived values). Write them into the inputs JSON. No agent rephrases or maps any value (FR-003). `test_faithful_intake.py` icon/field checks pass.
- [X] T006 [US1] Record the lossless brief echo in `harness/conductor.py` `execute`: write `brief_fields_received` (the inputs the pipeline actually consumed) plus `format_size` / `mandatory_elements` / `forbidden_elements` VERBATIM into `conductor_manifest.json` (FR-002). Extend `test_faithful_intake.py` to assert every entered field also appears verbatim in the manifest echo (dry-run or a stubbed execute path; no paid gen).

**Checkpoint**: Intake is lossless and verbatim, emit + manifest. The confound is removed at the source. MVP.

---

## Phase 4: User Story 2 - The previously-dropped fields reach generation (Priority: P1)

**Goal**: `format_size` drives the output pixel size (aspect-preserving, nearest the default ~1.57 MP target) and `mandatory_elements` / `forbidden_elements` reach the generation prompt + manifest. The de-hardcoding of `1536x1024` / `CANVAS`.

**Independent Test**: `test_format_size.py` green (size invariants + default-target landings + clamp), and a dry-run/explain of a brief with `分别画叉` + `60x40cm` shows both in the manifest + the kit prompt. Free, no model calls.

### Tests for User Story 2

- [X] T007 [P] [US2] Write `test_format_size.py`: assert `resolve_size` invariants (both edges multiples of 16, max edge ≤ 3840, pixels in [655_360, 8_294_400], `aspect_resolved` ≈ requested) AND the default-target landings: `60x40cm` (3:2) → `1536x1024`, `40x60cm` → `1024x1536`, `50x50cm` → ~`1248x1248`, a 3:1 → ~`2160x720`; a >3:1 banner → clamped to 3:1 + `needs_review` AND a <1:3 extreme-portrait → clamped to 1:3 + `needs_review` (symmetric, per the Edge Cases clause); unparseable → a default valid size + a non-null `note`. Assert portrait AND square land (profile-agnostic, not landscape-only, D8). MUST FAIL before T008.

### Implementation for User Story 2

- [X] T008 [US2] Implement `harness/format_size.py` `resolve_size(format_size, target_area=1_572_864)` per `contracts/cli-contract.md`: parse the physical numbers, clamp aspect to [1/3, 3] (clamp → needs_review), compute the valid ×16 pixel size preserving the aspect NEAREST `target_area` within the constraints, and return the full Size Resolution. Stdlib, profile-agnostic. `test_format_size.py` passes.
- [X] T009 [P] [US2] Implement `harness/prompt_elements.py` `elements_clause(mandatory, forbidden) -> str`: a render-dialect-NEUTRAL clause (verbatim REQUIRED elements + NEGATIVES); empty lists → empty clause (nothing fabricated). No flat_graphic assumptions (reusable by the future photo/poster assembler, D8).
- [X] T010 [US2] Wire size + elements through `harness/conductor.py`: resolve the size ONCE via `format_size.resolve_size`; record `size_resolution` (+ `format_size`) in `conductor_manifest.json`; pass `--size <WxH>` to the kit `scene_author` invocation (`_scene_author_kit_argv`). A `mandatory_elements` ∩ `forbidden_elements` conflict sets a campaign `needs_review` with the reason (honest null, §V).
- [X] T011 [US2] Wire `harness/scene_author.py` kit mode: add `--size <WxH>` (default `1536x1024`); use it for `generate_variant(size=...)` AND derive `canvas_wh = (W, H)` for `compose_kit_headline` (de-hardcode `CANVAS`); `assemble_kit_prompt` calls `prompt_elements.elements_clause` with the composition's `mandatory_elements` / `forbidden_elements` (verbatim). `--explain` reflects the resolved size + that mandatory/forbidden are in the prompt source (exits before any model call).
- [X] T012 [US2] Write `test_brief_wiring.py`: dry-run + kit `scene_author --explain` over a brief with `分别画叉` + `60x40cm`; assert the manifest records `size_resolution` (landscape `1536x1024`) + `mandatory_elements`; the kit prompt / `--explain` source contains `分别画叉`; a brief with NO `mandatory_elements` fabricates nothing (honest null); a mandatory∩forbidden conflict sets `needs_review`. No paid generation.

**Checkpoint**: The two dropped fields now drive generation and are recorded. The pipeline can finally be tested on a complete brief.

---

## Phase 5: User Story 3 - Self-service review (Priority: P1)

**Goal**: One read-only digest of a run: output images, the inputs the pipeline received, per-sign composition picks, and every needs_review flag, for the human's eye.

**Independent Test**: `test_review.py` green over a synthetic run dir; the digest lists each sign's image + icon + archetype + text_zone + needs_review + the campaign fields, and degrades gracefully on missing artifacts.

### Tests for User Story 3

- [ ] T013 [P] [US3] Write `test_review.py`: build a SYNTHETIC run dir (a `conductor_manifest.json` with `size_resolution` + mandatory/forbidden + `brief_fields_received`, two `sign_*/composition.json`, a fixture `final.png` + `.compliance.json`); assert the digest shows, per sign, the image path + chosen icon + layout archetype + reserved text_zone + needs_review + reason, plus the campaign fields; assert a sign with a MISSING `final.png` or a run with NO kit `composition.json` is reported as honest-null (no crash, profile-agnostic, D8). MUST FAIL before T014.

### Implementation for User Story 3

- [ ] T014 [US3] Implement `harness/review.py --run <dir>` per `contracts/review-digest-contract.md`: READ-ONLY over `conductor_manifest.json` + `sign_*/composition.json` + `sign_*/final.png(.compliance.json)` + `sign_*/run_manifest.json`; print the per-sign + campaign digest and write `review.md` into the run dir; recompute nothing; degrade gracefully (honest null) on missing / non-kit artifacts; no em-dashes. `test_review.py` passes.

**Checkpoint**: The human has one place to see what the pipeline got and render an eye verdict. The clean test can run end to end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces (incl. the 001 regression suite), then the human's paid run.

- [ ] T015 [P] Update `SYSTEM_MAP.md` + `CLAUDE.md` in the same commit that makes them stale (§VII): the intake is fixed (faithful self-service form), the 3 dropped fields are wired (`format_size` → target-area size; `mandatory_elements`/`forbidden_elements` → prompt + manifest), the review digest exists, and `asset_type → asset_profile` selection + the photo/poster render dialect is an explicit FUTURE spec.
- [ ] T016 [P] Run quickstart steps 1-4 (`test_format_size`, `test_faithful_intake`, `test_brief_wiring`, `test_review`, `test_conductor`) and confirm the 001 regression suite stays green (`test_kit`, `test_compose_select`, `test_fit_to_zone`, `test_kit_reserve_box`, `test_render_and_scrub`) — no regression from the new fields / de-hardcoded canvas.
- [ ] T017 The human's run (SC-003, NOT automated): `.venv/bin/python harness/conductor.py --brand aia` (the extended form; fill all 6 signs, 分别画叉, 设计两种样式 verbatim, 60x40cm, the reference) → the one PAID pipeline run → `.venv/bin/python harness/review.py --run output/run_aia_<ts>` → judge by eye (constitution §II). Record the verdict in `SYSTEM_MAP.md`. Needs spend + the human; left for the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup (uses the fixture). BLOCKS US1 and US2.
- **US1 (Phase 3)**: Depends on Foundational. The MVP.
- **US2 (Phase 4)**: Depends on Foundational. `format_size.py` (T008) + `prompt_elements.py` (T009) are independent of US1 and can run in parallel with it; the conductor/scene_author wiring (T010/T011) shares files the Foundational phase touched, so it follows Foundational.
- **US3 (Phase 5)**: Depends on Foundational (reads the manifest shape US1/US2 produce). `review.py` is independent of US1/US2 code and testable on a synthetic run dir, so it can be built in parallel once the manifest contract is fixed.
- **Polish (Phase 6)**: Depends on US1+US2+US3.

### User Story Dependencies

- **US1 (P1)**: After Foundational. The MVP increment.
- **US2 (P1)**: After Foundational. `format_size.py` + `prompt_elements.py` are independent modules (parallelizable with US1); the wiring tasks come after Foundational.
- **US3 (P1)**: After Foundational (needs the manifest shape). Independent module; testable in isolation.

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- US2: `test_format_size` (T007) before `format_size.py` (T008); `prompt_elements.py` (T009) before the wiring (T010/T011) that calls it; `test_brief_wiring` (T012) closes the story.
- Commit after each task (§VII).

### Parallel Opportunities

- T003 (test_conductor update) is [P] vs the US module tests.
- The three new stdlib modules' tests — T004 (intake), T007 (format_size), T013 (review) — are all [P] and can be drafted together.
- `format_size.py` (T008) ∥ `prompt_elements.py` (T009) ∥ `review.py` (T014) are different files.
- T015 ∥ T016 in Polish (docs vs running self-tests).

---

## Parallel Example: kicking off after Foundational

```bash
# Three independent test files first (each MUST FAIL), then implement each module:
Task: "T004 Write test_faithful_intake.py (US1)"     # conductor ask_questions
Task: "T007 Write test_format_size.py (US2)"         # format_size.py
Task: "T013 Write test_review.py (US3)"              # review.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup (faithful brief fixture).
2. Phase 2 Foundational (conductor carries the new fields; standalone proof).
3. Phase 3 US1 (extended form + lossless manifest echo).
4. **STOP and VALIDATE**: drive `ask_questions` over the 6-sign brief; confirm every field verbatim, no drop. The confound is removed at the source, all free.

### Incremental Delivery

1. Setup + Foundational → the conductor carries the new fields.
2. US1 → faithful intake (lossless emit + manifest). MVP.
3. US2 → the dropped fields drive generation (size + mandatory/forbidden), de-hardcoded canvas.
4. US3 → self-service review digest.
5. Polish → durable docs, free regression suite green, then the human's paid run + eye verdict (the first clean test).

### Notes

- [P] = different files, no incomplete dependencies.
- No paid image generation in ANY test (§ Cost discipline). Only T017 spends, and only the human eye validates its pixels (§II).
- The new code (`format_size.py`, `prompt_elements.py`, `review.py`, the manifest additions) is ASSET-PROFILE-AGNOSTIC (no flat_graphic / die-cut / orientation literals); the 1536x1024 target is a configurable default, not a hardcoded canvas (D8 / FR-008-adjacent).
- No em-dashes in any user-facing text or needs_review reason (Output rule).
- `asset_type → asset_profile` selection and the photo/poster render dialect are OUT OF SCOPE (future spec); 002 only keeps the new code profile-agnostic so that path is pure addition.
