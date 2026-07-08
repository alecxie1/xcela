---
description: "Task list for Role-aware Brand Palette + Exactly-one-primary"
---

# Tasks: Role-aware Brand Palette + Exactly-one-primary

**Input**: Design documents from `specs/008-palette-role-guidance/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-30: 5-role vocabulary + extend the gate), research.md (D1-D4), data-model.md, contracts/ (palette-prompt + roles-gate), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests assert the assembled prompt STRING (each color's hex + its role instruction; blank fallback; background guard both directions; anchor unchanged), the validator (raises on 0 and on >=2 primaries, passes on 1), and the gate-role sync. NO paid model calls (never generate). The one paid sign (the eye-gate) is the human's after the build.

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project. Generation: `harness/scene_author.py` (thin prompt). Validator: `brand_intake/validate_key.py`. Gate: `frontend/onboard.html` (web) + `brand_intake/intake.py` (CLI). Self-test as `test_palette_roles.py` at repo root; `test_brand_key.py` + `test_onboard.py` extended. Brand palette identity stays a HARD lock; per-role usage is GUIDANCE. The EXACT confirmed wording (data-model.md / inbox brief) is verbatim, no paraphrase.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The role vocabulary + instruction map both stories stand on (the thin prompt consumes it; the gate-role sync test asserts against it). No prompt/gate edit yet.

- [X] T001 [P] Add `ROLE_GUIDANCE` to `harness/scene_author.py` (module constant, near `assemble_thin_prompt`) per `contracts/palette-prompt-contract.md` + `data-model.md`: a dict of the 5 canonical roles -> the CONFIRMED VERBATIM instruction text (primary / secondary / accent / background / text) plus a blank/unknown FALLBACK string ("part of the brand palette: use where appropriate to keep the design on-brand."). Brand-general (no brand/color literals). Do NOT touch the color block yet.
- [X] T002 [P] Create `test_palette_roles.py` (stdlib, no paid calls) with the FIRST check: `ROLE_GUIDANCE` defines exactly the 5 named roles and each carries its verbatim instruction substring (accent contains "use sparingly"; secondary contains "support the primary"; text contains "legible"; primary contains "dominant"; background contains "fill the background"), plus a non-empty blank/unknown fallback. MUST FAIL before T001 (write alongside; both [P], different files).

**Checkpoint**: the role vocabulary + instruction map exist, independently testable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None beyond Setup. `ROLE_GUIDANCE` (Phase 1) is the only shared prerequisite; once its map test is green, both user stories can begin. `_primary_color_hex` and the register directive are reused UNCHANGED.

**Checkpoint**: the map is green; user-story work can start.

---

## Phase 3: User Story 1 - Every brand color drives real design behavior (Priority: P1) 🎯 MVP

**Goal**: The thin prompt lists every brand color with a role-specific instruction (guidance, not must-use), so the full palette shapes the output, not just the primary. Palette identity stays a hard lock.

**Independent Test**: Given a brand key with primary + secondary + accent (+ background + text), the assembled thin prompt contains EACH color's hex AND its role-instruction substring; a primary-only build fails. Free, no model calls (assert the assembled string).

### Tests for User Story 1

- [X] T003 [US1] Add to `test_palette_roles.py` the prompt checks: build a brand key with primary + secondary + accent + background + text and call `scene_author.assemble_thin_prompt(...)`; assert EACH color's hex AND its `ROLE_GUIDANCE` instruction substring appears (a primary-only build fails); a color with role "" or "weird" appears with the blank/unknown fallback line; the BACKGROUND guard BOTH directions (`has_reference=True` -> the background line contains "fill the background"; `has_reference=False` -> it does NOT, the color still listed via fallback); the header contains "must read as this brand's" (hard lock preserved); `_primary_color_hex` still returns the single primary (anchor unchanged). MUST FAIL before T004.

### Implementation for User Story 1

- [X] T004 [US1] Edit `assemble_thin_prompt`'s color block in `harness/scene_author.py` (`:884-891`) per `contracts/palette-prompt-contract.md`: replace the header line with the confirmed wording (keeps "must read as this brand's"); for each color emit `  name_cn/name_en: #hex [role] - <instruction>` where `<instruction>` is `ROLE_GUIDANCE[role]` (blank/unknown -> fallback); if `role == background` AND NOT `has_reference`, use the fallback (color still listed, no backdrop instruction). Do NOT touch `_primary_color_hex` / `_register_directive` / the headline / mandatory / forbidden / logo / reference / negatives blocks. `test_palette_roles.py` US1 checks pass.

**Checkpoint**: every roled color carries an operative instruction in the thin prompt; the anchor is unchanged. MVP.

---

## Phase 4: User Story 2 - Onboarding enforces exactly one primary + offers all 5 roles (Priority: P1)

**Goal**: The verify gate lets the designer assign any of the 5 roles and is told exactly one must be primary; a save with zero OR more-than-one primary fails loud (no key written). The gate stays in sync with the role map.

**Independent Test**: `validate_lean_key` raises on 0 and on >=2 primaries, passes on exactly 1; `onboard.save_draft` blocks a multi-primary save (no file); the gate (onboard.html options + intake.py prompt) offers exactly the named `ROLE_GUIDANCE` roles; the served page states the rule. Free, no model calls.

### Tests for User Story 2

- [X] T005 [US2] Add the exactly-one-primary + gate-sync checks: in `test_brand_key.py` assert `validate_lean_key` RAISES (named reason) on a key with TWO primaries and PASSES on exactly one (the existing 0-primary + single-primary cases stay green); in `test_onboard.py` add a save with two primaries -> fails loud, NO key file written; in `test_palette_roles.py` add the gate-role SYNC check: the roles offered by `frontend/onboard.html` (`<select>` options) AND by the `brand_intake/intake.py` prompt equal the named roles in `scene_author.ROLE_GUIDANCE`, AND `onboard.html` contains the "exactly one primary" instruction with NO em-dash. MUST FAIL before T006/T007/T008.

### Implementation for User Story 2

- [X] T006 [US2] Tighten `brand_intake/validate_key.py` `validate_lean_key` per `contracts/roles-gate-contract.md`: count items with `role == "primary"` (case-insensitive) carrying a `printed_html` hex; raise `KeyValidationError` (existing named message) on 0; raise `KeyValidationError` (new named reason: more than one primary, assign one and make the others secondary) on >=2; pass on exactly 1 (then the existing logo_path checks, unchanged). `test_brand_key.py` + `test_onboard.py` US2 checks pass.
- [X] T007 [US2] Edit `frontend/onboard.html`: the color role `<select>` offers all 5 roles (add `accent` + `text` to the current primary/secondary/background, `:107-110`); add a visible "exactly one primary" instruction near the colors step (`:104`). No em-dashes. The gate-sync check passes.
- [X] T008 [US2] Edit `brand_intake/intake.py`: the CLI verify-gate role prompt (`:119`) offers all 5 roles (primary/secondary/accent/background/text); the batch default (first=primary, rest=secondary, `:105-107`) is UNCHANGED (still exactly one primary). The gate-sync check passes.

**Checkpoint**: one unambiguous primary enforced at save (CLI + web); the full role vocabulary is assignable and in sync with the map.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the human eye-gate.

- [X] T009 [P] Update `CLAUDE.md` + `SYSTEM_MAP.md` in the same commit that makes them stale (§VII): role-aware palette on the thin route (the `ROLE_GUIDANCE` map; available palette with role guidance; palette identity still a hard lock); exactly-one-primary in the shared `validate_lean_key`; the gate offers 5 roles (web + CLI); the background-vs-chroma guard. Note the deferred items (generalize beyond flat-vector signs; multiple non-primary roles unconstrained).
- [X] T010 [P] Run the free structural suite and paste real output: `test_palette_roles.py` (all checks), `test_brand_key.py` + `test_onboard.py` (exactly-one-primary), `test_thin_route.py` (the thin route still assembles), `test_conductor.py`; confirm the prior 001-007 suites stay green. ALSO assert FR-011 structurally: the served `onboard.html` user-facing strings contain NO em-dash (`—`) (a free grep).
- [x] T011 The human eye-gate (SC-007, NOT automated; folds into the existing back-half paid run): generate a sign for a brand whose palette has accent / text / background roles and judge by EYE (§II) that the output uses the full palette per its roles (accent as small highlights, text color for type, background as the field, primary dominant), not just the primary everywhere. Record the verdict in `SYSTEM_MAP.md`. Needs spend + the human; left for the user. **CLOSED 2026-07-08, satisfied de facto:** the role-tagged CJXQ key (roles assigned in the web gate) drove the thin route's role-aware color block in three operator-passed eye-gates (011 T011, 012 T010, 014 T007); the judged outputs use the full candy palette per roles, not primary-everywhere.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; `ROLE_GUIDANCE` (T001) ∥ its map test (T002) are different files.
- **Foundational (Phase 2)**: none beyond Setup; `ROLE_GUIDANCE` (T001) is the only shared prerequisite, needed by US1's color block (T004) and US2's gate-sync test (T005).
- **US1 (Phase 3)**: after Setup (the color block consumes `ROLE_GUIDANCE`). The MVP.
- **US2 (Phase 4)**: after Setup (the gate-sync test references `ROLE_GUIDANCE`). Independent of US1 otherwise (different files: validator + gate vs the prompt color block).
- **Polish (Phase 5)**: after US1 + US2.

### Within Each User Story

- The test task (test-first) is written and MUST FAIL before its implementation tasks.
- `scene_author.py` is touched by T001 (constant) then T004 (color block) — same file, sequential.
- US2: the validator (T006), the web gate (T007), the CLI gate (T008) are different files and can run in parallel after T005; the gate-sync check needs T007 + T008.
- Commit after each task (§VII).

### Parallel Opportunities

- Setup: T001 ∥ T002 (different files).
- US2 impl: T006 (validate_key.py) ∥ T007 (onboard.html) ∥ T008 (intake.py) are different files.
- Polish: T009 ∥ T010 (docs vs running self-tests).
- The per-story checks all live in `test_palette_roles.py` (US1 + the US2 gate-sync) so they are added sequentially to that file, not in parallel with each other.

---

## Parallel Example: kicking off

```bash
# The shared role map + its test (different files), test-first:
Task: "T001 Add ROLE_GUIDANCE to harness/scene_author.py"
Task: "T002 Create test_palette_roles.py with the map-coverage check"
```

---

## Implementation Strategy

### MVP First (Setup + US1)

1. Phase 1 Setup (`ROLE_GUIDANCE` + the map test).
2. Phase 3 US1 (the thin prompt color block): every roled color carries an operative instruction.
3. **STOP and VALIDATE**: `test_palette_roles.py` US1 checks green + `test_thin_route.py` green — the palette is functional on the thin route, all free.

### Incremental Delivery

1. Setup → the role vocabulary + instruction map.
2. US1 → role-aware palette in the thin prompt (MVP).
3. US2 → exactly-one-primary at save (CLI + web) + the 5-role gate, in sync with the map.
4. Polish → durable docs, free suite green, then the human eye-gate (full palette per roles).

### Notes

- [P] = different files, no incomplete dependencies.
- NO paid model calls in ANY automated test (§ Cost discipline). Tests assert the assembled prompt STRING + the validator + the gate-role sync; never generate. Only T011 (the human sign) spends, eye-validated (§II).
- GENERALIZES, not hand-tuned (§IV): the role->instruction map is brand-general; no brand/color literals.
- Brand identity stays the HARD lock; only per-role usage is guidance (§VI). The header keeps "must read as this brand's".
- Honest-null (§V): an unroled / unknown-role color still reaches the prompt (generic palette line); the background guard avoids a fabricated chroma contradiction; the validator fails loud on a bad primary count.
- The EXACT confirmed role wording is verbatim (no paraphrase).
- Scope: thin prompt + validator + gate pickers ONLY; kit / tier-3 / legacy color paths, typography, the asset profile, and the conductor contract are UNCHANGED.
- No em-dashes in any user-facing text (the onboarding page, the new role lines shown in the prompt stage).
