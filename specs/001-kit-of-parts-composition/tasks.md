---
description: "Task list for Kit of Parts + Bespoke Per-Message Composition"
---

# Tasks: Kit of Parts + Bespoke Per-Message Composition

**Input**: Design documents from `specs/001-kit-of-parts-composition/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-22), research.md (D1-D7), data-model.md, contracts/ (4 files), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory, and the plan/data-model seed them. Tests assert VALUES a wrong build fails; they NEVER contain paid image generation (§ Cost discipline). Pixel quality is human-eye only (§II).

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project. Pipeline code in `harness/`, reused reconciliation in `register/`, brand data in `answer_keys/` + `config/` + NEW `kits/`, self-tests as `test_*.py` at repo root. Outputs under `output/run_*/sign_*/` (gitignored).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Stand up the kit DATA layer everything else reads. No code logic yet.

- [X] T001 Create `kits/` directory and author starter `kits/aia.json` (modes, icon_vocabulary with meaning_cues + mode + icon_description, layout_vocabulary with >=2 archetypes each defining non-overlapping icon_zone + text_zone) per `specs/001-kit-of-parts-composition/contracts/kit-schema.md`. Cover at least the 2-sign AIA set meanings (守住钱袋子/护好幸福家 → protect/money_bag; 远离非法金融/抵制高息诱惑 → resist/megaphone_x).
- [X] T002 [P] Add `kits/README.md` noting the kit is human-authored brand DATA (committed, NOT gitignored like `brands/`), and confirm `git check-ignore kits/aia.json` reports it is tracked.

**Checkpoint**: A valid authored AIA kit exists on disk for the loader and selectors to consume.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The kit loader/validator + derived `kit_profile.json`. BLOCKS US1 and US3 (both compose from a kit). US2 (fit clamp) does not depend on this phase.

**⚠️ CRITICAL**: No kit-composition story work begins until `harness/kit.py` exists and validates.

- [X] T003 [P] Write `test_kit.py` (falsifiable, no paid calls) asserting: (a) a valid `kits/aia.json` loads; (b) every declared mode is served by >=1 archetype; (c) duplicate icon `id`s, identical `meaning_cues` sets, and overlapping icon_zone/text_zone each RAISE the specific rule from `contracts/kit-schema.md`; (d) on a seeded reference-vs-answer-key palette clash the derived profile carries the ANSWER-KEY hex and records it in `conflict_resolutions`. MUST FAIL before T004/T005.
- [X] T004 Implement `harness/kit.py` load + validate of `kits/<brand>.json` enforcing all `contracts/kit-schema.md` rules (raise with the specific rule violated, no silent partial kit). The validation cases in `test_kit.py` pass.
- [X] T005 Implement `harness/kit.py` `kit_profile.json` derivation per `contracts/kit-profile-schema.md`: merge `answer_keys/<brand>.json` (HARD locks) + `register_profile.json` + optional `calibration.json` (SOFT dims via `register/`), ANSWER KEY WINS every conflict, honest-null `notes` when reference style extraction is absent. CLI per `contracts/cli-contract.md` (`--brand --answer-key --register-profile [--calibration] --out`). The conflict case in `test_kit.py` passes.

**Checkpoint**: `kit.py` validates an authored kit and emits a derived `kit_profile.json`; reconciliation (§VI) and answer-key-wins (D6) proven by test.

---

## Phase 3: User Story 1 - Each sign is a distinct composition, not a re-texted clone (Priority: P1) 🎯 MVP

**Goal**: Per message, deterministically choose a meaning-driven icon AND a distinct layout archetype, route the campaign through the kit path, and surface the choices at the human taste gate. Distinctness is DECIDED here (pixel distinctness is judged later by eye).

**Independent Test**: `.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json --out /tmp/dry --dry-run --no-approve` emits, per sign, a chosen icon + distinct archetype + reserved text_zone + needs_review, with NO model/image calls; the two AIA signs get DIFFERENT archetypes. Confirmed free via dry-run + `test_compose_select.py` + `test_conductor.py`.

> **Inputs file**: `conductor_inputs_example.json` (repo root) already IS the 2-sign AIA set (s1 守住钱袋子/护好幸福家 → protect; s2 远离非法金融/抵制高息诱惑 → resist). Reuse it for T009/T011/T020. On the kit path its `reference_relationship` clone dial is IGNORED (D6: reference feeds the kit, never clones), and a pre-filled `hero_icon` is treated as a human OVERRIDE of the tool's proposal, not a bypass of compose_select.

### Tests for User Story 1

- [X] T006 [P] [US1] Write `test_compose_select.py` (falsifiable, no paid calls): 钱袋子/储蓄 → `chosen_icon=money_bag`; a nonsense message with ZERO cue hits → `chosen_icon=null` + `needs_review=true` (proves the floor rejects score-0, pinning A1); a message that ties two entries at the top score → `chosen_icon=null` + `needs_review=true` (ambiguous); two different-mode messages → two DIFFERENT `chosen_archetype`; exhausting the layout vocabulary → `archetype_reused=true` + `needs_review=true`. MUST FAIL before T007/T008.

### Implementation for User Story 1

- [X] T007 [US1] Implement `harness/compose_select.py` deterministic meaning→mode→icon match writing `composition.json` fields `detected_mode`, `chosen_icon`, `icon_match_score`, `needs_review`/`needs_review_reason`. CONCRETE rule (pins A1, falsifiable): `icon_match_score` = the count of distinct `meaning_cues` that occur as substrings of the joined message text; an entry is eligible only if its score >= 1; the winner is the SINGLE highest-scoring eligible entry. Honest-null (`chosen_icon=null`, `detected_mode=null`, `needs_review=true`) when the top score is 0 (no cue hit) OR two or more entries tie for the top score (ambiguous). No generative fallback (D2).
- [X] T008 [US1] Add collision-avoiding layout-archetype selection to `harness/compose_select.py` (`--campaign-used` set; pick a distinct archetype serving the mode; reuse + `archetype_reused=true` + `needs_review` only when the vocabulary is exhausted; NO auto-jitter) plus `--explain` that prints the composition JSON and exits pre-call. `test_compose_select.py` passes.
- [X] T009 [US1] Route `harness/conductor.py` family jobs through the kit path: after the shared `register_profile` (+ calibration), build `kit_profile.json` ONCE via `harness/kit.py`, then call `compose_select` per sign and write each `output/run_*/sign_*/composition.json`. `--dry-run` emits chosen icon + archetype + text_zone + needs_review with zero model/image calls (per `contracts/cli-contract.md`).
- [X] T010 [US1] Surface per-sign icon + layout proposals and any `needs_review` at the existing conductor approve/nudge gate; let a nudge override a sign's icon or archetype (re-run that sign only); record every choice + needs_review in `conductor_manifest.json` (§I human taste gate, §V honest nulls).
- [X] T011 [US1] Update `test_conductor.py` so the dry-run plan asserts the kit route is taken and the 2-sign AIA set receives DISTINCT archetypes (no paid calls).

**Checkpoint**: The reframe's decision layer is proven free via dry-run: distinct, meaning-driven compositions are CHOSEN and gated by the human. This is the MVP.

---

## Phase 4: User Story 2 - Headline text fits inside the sign with margin (Priority: P1)

**Goal**: Size the licensed headline DOWN to fit its reserved zone with margin; honest-null when it cannot fit. Fixes failure (a). Independent of the kit (uses a supplied zone).

**Independent Test**: `.venv/bin/python test_fit_to_zone.py` green: a long headline yields a strictly smaller `final_size_px` than a short one in the same zone with the rendered box inside the zone plus margin; an unfittable headline yields `fits=false`, `final_size_px=null`, `needs_review=true`.

### Tests for User Story 2

- [X] T012 [P] [US2] Write `test_fit_to_zone.py` (falsifiable, no paid calls): assert the clamp returns a strictly smaller `final_size_px` for a longer headline in the same `text_zone`; the rendered box (Pillow-measured) sits inside the zone with `margin_px` on every edge; an oversized headline at `min_size_px` returns `fits=false`/`final_size_px=null`/`needs_review` (never a clipped render), per `contracts/composition-schema.md` FitResult. MUST FAIL before T013.

### Implementation for User Story 2

- [X] T013 [US2] Implement the fit-to-zone clamp in `harness/composite_text.py`: given headline text + `text_zone` (px) + the licensed font resolved by the existing `resolve_font`, binary/linear-search the largest `size_px` whose Pillow-measured multi-line box fits the zone with `margin_px`; floor at `min_size_px` → honest-null (`fits=false`). Leave existing `composite()` + compliance manifest unchanged. `test_fit_to_zone.py` passes.

**Checkpoint**: Type is sized to the zone, never the reverse; unfittable text is an honest null, not a clip.

---

## Phase 5: User Story 3 - Graphics are not damaged by text placement (Priority: P2)

**Goal**: Render each sign by painting the panel + chosen icon into the icon_zone and keeping the text_zone CLEAR, then composite the fitted headline into that zone. No scrub step → no icon damage. Fixes failure (b). Integrates US1 (composition.json) + US2 (fit clamp).

**Independent Test**: a structural test confirms the kit reserve-box prompt keeps icon_zone and text_zone disjoint and that the headline is composited into the text_zone with NO scrub/OCR-erase step invoked; then the paid eye check (Polish) confirms intact icons.

### Tests for User Story 3

- [X] T014 [P] [US3] Write `test_kit_reserve_box.py` (falsifiable, no paid calls; use `--explain` and a fixture composition.json): assert scene_author kit mode keeps `icon_zone` and `text_zone` disjoint, places the composited headline anchor inside `text_zone`, and takes NO render-and-scrub path (no OCR-erase). MUST FAIL before T015/T016.

### Implementation for User Story 3

- [X] T015 [US3] Add kit reserve-box mode to `harness/scene_author.py` (`--kit-profile` + `--composition`): build a generation prompt that paints `panel_treatment` + the chosen icon's `icon_description` INSIDE `icon_zone` and keeps `text_zone` clear; `--explain` prints the resolved source + mode and exits before any model call. Do not use the render-and-scrub or aligned-prompt-clone paths for kit jobs.
- [X] T016 [US3] Wire the composite step in `harness/scene_author.py`: after generation, composite the licensed headline into `text_zone` at `fitted_type.final_size_px` (reuse `composite_text.composite` + the T013 fit clamp), emit the compliance manifest, and set per-sign `needs_review` from the composition. `test_kit_reserve_box.py` passes.
- [X] T016a [US3] Add a compliance-manifest assertion to `test_kit_reserve_box.py` (FR-006 / SC-005, non-negotiable): composite the headline onto a LOCAL fixture PNG (no paid generation) on the kit path and assert `final.png.compliance.json` is emitted with every headline layer resolved to a licensed font (`resolution` != `MISSING`/`fallback_system`). This proves the licensed-font guarantee survives the kit reroute.
- [X] T017 [US3] Route `harness/conductor.py` execute (non-dry-run) for kit jobs to scene_author kit mode (bypass the aligned-prompt clone for kit jobs); record per-sign generation + needs_review in `conductor_manifest.json`.

**Checkpoint**: All three failures are addressed structurally (a: fit clamp; b: disjoint zones, no scrub; c: distinct per-message selection). Ready for the paid eye gate.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the one paid eye-judged run.

- [X] T018 [P] Update `SYSTEM_MAP.md` (kit-of-parts frame BUILT; retire the 6/18 clone-failure live note) and `CLAUDE.md` (mark the fit-to-zone clamp as existing; update the "no fit-to-margin clamp" pitfall) in the same commit that makes them stale (§VII).
- [X] T019 [P] Run `quickstart.md` steps 1-4 (test_kit, test_compose_select, test_fit_to_zone, test_kit_reserve_box, conductor dry-run + test_conductor) and confirm all free structural surfaces are green, INCLUDING the SC-005 non-negotiables check (compliance manifest emits on the kit path per T016a; needs_review threaded into the manifest; no em-dashes in any user-facing string).
- [ ] T020 The ONE paid run: `.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json`; judge `output/run_*/sign_*/final.png` by the HUMAN EYE against `desiredresultaia.jpg` for SC-001..005 (distinct compositions, text fits with margin, icons intact, distinct-yet-cohesive family, compliance + honest nulls hold). Record the verdict in `SYSTEM_MAP.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup (needs `kits/aia.json`). BLOCKS US1 and US3.
- **US1 (Phase 3)**: Depends on Foundational. The MVP.
- **US2 (Phase 4)**: Depends ONLY on Setup conventions; independent of Foundational/US1 (uses a supplied zone). Can run in parallel with Foundational/US1.
- **US3 (Phase 5)**: Depends on Foundational + US1 (consumes `composition.json` + `kit_profile.json`) + US2 (uses the fit clamp).
- **Polish (Phase 6)**: Depends on US1+US2+US3.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on US2/US3.
- **US2 (P1)**: Independent (fit clamp on a supplied zone). Parallelizable with US1.
- **US3 (P2)**: After US1 + US2 (integration story).

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- In US1: icon match (T007) before archetype selection (T008) before conductor routing (T009) before gate wiring (T010) before the conductor test update (T011).
- In US3: kit reserve-box prompt (T015) before the composite wiring (T016) before conductor execute routing (T017).
- Commit after each task (§VII).

### Parallel Opportunities

- T002 ∥ T001 finalization (different files).
- T003 (test_kit) is [P]; write while authoring the kit.
- US2 (T012→T013) runs fully in parallel with Phase 2 + US1 — different file (`composite_text.py`) and an independent test.
- T006, T012, T014 (the three story test files) are all [P] and can be drafted together.
- T018 ∥ T019 in Polish (docs vs running self-tests).

---

## Parallel Example: starting the build

```bash
# After Setup, kick off the independent US2 track alongside Foundational + US1:
Task: "T012 Write test_fit_to_zone.py (US2)"      # composite_text.py track
Task: "T003 Write test_kit.py (Foundational)"     # kit.py track
Task: "T006 Write test_compose_select.py (US1)"   # compose_select.py track
# Each test MUST FAIL first, then implement its module.
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup (author `kits/aia.json`).
2. Phase 2 Foundational (`kit.py` validate + derive).
3. Phase 3 US1 (compose_select + conductor kit routing + gate).
4. **STOP and VALIDATE**: dry-run the 2-sign AIA set; confirm DISTINCT archetypes + honest nulls, all free. The reframe's core decision layer is proven without spend.

### Incremental Delivery

1. Setup + Foundational → kit ready.
2. US1 → distinct compositions CHOSEN (dry-run MVP).
3. US2 → text fits its zone (independent, parallelizable).
4. US3 → render with disjoint zones + composited fitted text (integrates US1+US2).
5. Polish → update durable docs, run free surfaces, then the ONE paid eye-judged run.

### Notes

- [P] = different files, no incomplete dependencies.
- No paid image generation in ANY test (§ Cost discipline). Only T020 spends, and only the human eye validates its pixels (§II).
- All AIA literals live in `kits/aia.json` (§IV / FR-008); `kit.py`, `compose_select.py`, the fit clamp, and routing stay brand-general.
- No em-dashes in any user-facing text or needs_review reason (Output rule).
