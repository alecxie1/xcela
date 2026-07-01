# Tasks: Render-Aware Register

**Input**: Design documents from `/specs/011-register-render-aware/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/derive_register_contract.md, quickstart.md

**Tests**: Included in every implementation task (constitution III makes falsifiable tests
mandatory, not optional). Repo style applies: one task, one module, one falsifiable test, one
commit; the test lands in the SAME commit as the code it gates. All tests are FREE (pure-function
imports, no subprocess, no paid model calls).

**Organization**: Tasks are grouped by user story. Contract row numbers refer to
[contracts/derive_register_contract.md](contracts/derive_register_contract.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

## Path Conventions

Repository-root paths (this repo is a flat CLI pipeline, no `src/`): engine at
`register/derive_register.py`, orchestrator at `harness/conductor.py`, self-tests at
`test_*.py` in the root.

---

## Phase 1: Setup

**Purpose**: Record the pre-feature baseline so every later no-regression claim is falsifiable.

- [X] T001 Run the existing free suites and record them green BEFORE any edit:
      `.venv/bin/python test_conductor.py`, `.venv/bin/python test_render_and_scrub.py`,
      `.venv/bin/python test_render_modes.py`. Also capture a pre-feature reference profile for
      the FR-007 byte-identity check: import `derive_register` and dump
      `json.dumps(profile, sort_keys=True)` for a playful/no-event subfields dict WITHOUT
      `render_style`, using a minimal inline brand_key (no styles map, so the dump is
      machine-independent). Save the dump to the session scratchpad; T007 inlines it as the
      `EXPECTED_PREFEATURE_PROFILE` literal inside `test_register_render_aware.py`, so the
      baseline is repo-contained and survives the scratchpad. The exact subfields dict and
      brand_key are reused verbatim in T007. No repo file changes in this task; if anything is
      already red, STOP and report (honest nulls).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The FR-001 plumbing and the render predicate. Both user-visible behaviors (US1 gate,
US1 tone retention) read these; nothing story-level can be tested end to end without them.

**⚠️ CRITICAL**: Complete before any user story phase.

- [X] T002 [P] Thread `render_style` into the thin-route subfields in `harness/conductor.py`:
      give `build_subfields(inputs, thin=False)` the new keyword; when `thin` is true AND the
      inputs carry the key, include `"render_style": inputs.get("render_style")` VERBATIM (raw,
      no normalization, per research D1); update the single call site in `write_glue_artifacts`
      (harness/conductor.py:1074) to pass its existing `thin` flag. Create
      `test_register_render_aware.py` with the plumbing check: `build_subfields(inputs, thin=True)`
      contains the raw value; `build_subfields(inputs)` and `build_subfields(inputs, thin=False)`
      return a dict WITHOUT the key and equal to the pre-feature shape (kit/legacy byte-identical
      invariant, data-model §1). Commit: `feat(011): thread render_style into thin subfields (T002)`.

- [X] T003 [P] Add the local render predicate `_render_is_photo(value)` to
      `register/derive_register.py`: `strip().lower()` in `("photographic", "photo")` means photo;
      everything else (absent, blank, unrecognized) means flat (research D2). NOT yet consulted by
      the derivation (that is T004), so behavior is unchanged. Add the drift-guard check to
      `test_register_render_aware.py`: import BOTH `harness.conductor.normalize_render_style` and
      the new predicate and assert they agree on the shared table `"photographic"`, `"photo"`,
      `" PHOTOGRAPHIC "`, `"flat vector"`, `""`, `None`, `"watercolor"` (contract §Drift guard).
      Commit: `feat(011): render predicate + normalizer drift guard (T003)`.

**Checkpoint**: Plumbing green, predicate green, all pre-existing suites still green.

---

## Phase 3: User Story 1 - Photographic marketing keeps a marketing register, playful character intact (Priority: P1) 🎯 MVP

**Goal**: A photographic job from a playful+informal brand with no event language resolves to
`marketing` (format follows the task), the trace names the render choice as the suppression
reason, and the design cues keep the playful tone (rounded font + playful accents) WITHOUT the
die-cut prop shape (tone follows the vibe; the two are decided independently).

**Independent Test**: spec US1: run `derive_register` on a photographic + playful/no-event
subfields dict; assert register `marketing`, the trace suppression line, and the exact cue set.

- [X] T004 [US1] Gate the vibe promotion in `register/derive_register.py` step 2 (the
      `formality<=3 and playfulness>=7` branch at lines 96-98): when the branch would fire AND
      `_render_is_photo(subfields.get("render_style"))`, do NOT promote; append ONE trace line
      naming the raw render_style value as the reason (FR-002, FR-005; research D3 wording). When
      the render is flat or absent the branch runs exactly as today and writes NO new trace line.
      Tests in `test_register_render_aware.py` (falsifiable VALUES, not token presence):
      contract row 1 register half (photo+playful+no-event yields `marketing`, and the trace
      contains a line naming `photographic`; a no-gate build yields `event_prop` and fails);
      contract row 5 (photo + `formality>=8` still yields `formal`); contract row 7
      (`"watercolor"` behaves exactly like flat: `event_prop`).
      Commit: `feat(011): photo render gates the vibe event_prop promotion (T004)`.

- [X] T005 [US1] Playful-tone retention in `register/derive_register.py` step 4 region: when the
      resolved register is `marketing` AND the vibe is the promoting combination
      (`formality<=3 and playfulness>=7`), flex `font:rounded` + `palette:playful-accents` into
      `brand_locks_flexed` (NEVER `shape:die-cut`), set `font_role_hint = "rounded display"` (so
      step 5 resolves the licensed rounded family) and a playful-marketing `tone_hint`, keep
      marketing's `shape_language_hint` untouched, and append ONE trace line listing the retained
      cues and naming the vibe as the reason (FR-009/010/011; research D5). Keyed on the VIBE, not
      the render choice. Tests: contract row 1 cue half; assert `font:rounded` AND
      `palette:playful-accents` PRESENT in `brand_locks_flexed` (a tone-stripping build fails),
      `shape:die-cut` ABSENT (a format-leaking build fails), `font_role_hint == "rounded display"`,
      `shape_language_hint` equal to the marketing default (no die-cut wording), `tone_hint`
      different from `REGISTER_HINTS["marketing"]["tone_hint"]` and carrying the playful-marketing
      wording (a build that forgets the tone_hint delta fails), and the retention trace line
      present. Also assert a NON-playful marketing profile (e.g. formality 5) gains none of this
      (unchanged hints INCLUDING the default marketing tone_hint, no trace line).
      Commit: `feat(011): playful tone retained on marketing, prop format excluded (T005)`.

- [X] T006 [US1] US1 checkpoint sweep: run `.venv/bin/python test_register_render_aware.py` plus
      the three pre-existing suites from T001 (SC-006), then the quickstart §3 dry-run plumbing
      check (`--thin --dry-run` inputs copy with `"render_style": "photographic"`; inspect
      `subfields.json` and the standalone `register/derive_register.py` CLI trace output). Fix
      anything red before proceeding. No new files; commit only if fixes were needed.

**Checkpoint**: US1 fully functional and independently testable; the reported defect is fixed.

---

## Phase 4: User Story 2 - Flat assets preserve the existing event-prop behavior (Priority: P1)

**Goal**: The shipped flat die-cut path is provably untouched: flat and render-absent jobs derive
byte-identical profiles to the pre-feature engine.

**Independent Test**: spec US2: run `derive_register` on the same playful/no-event subfields with
a flat render and with no render key; assert `event_prop` both times, the absent case byte-identical.

- [X] T007 [US2] No-regression assertions in `test_register_render_aware.py`: contract row 2
      (`render_style: "flat vector"` + playful + no event language yields `event_prop`, promotion
      trace line present, NO suppression line, NO retention line) and contract row 3 (render_style
      ABSENT yields a profile whose sorted-keys JSON equals the `EXPECTED_PREFEATURE_PROFILE`
      literal captured in T001 and inlined in this test file: same register, same cues, same
      trace, an over-eager gate or a stray trace line fails). FR-003/FR-007,
      SC-002. Test-only change.
      Commit: `test(011): flat + render-absent paths byte-identical (T007)`.

**Checkpoint**: US1 and US2 both green; the fix cannot have regressed the production flat path.

---

## Phase 5: User Story 3 - An explicit event-prop request always wins (Priority: P2)

**Goal**: An explicit human usage phrase ("held for photos") keeps `event_prop` even on a
photographic render; the gate suppresses a machine guess, never a human statement.

**Independent Test**: spec US3: photographic subfields whose usage_context contains an explicit
event-prop phrase; assert `event_prop`.

- [X] T008 [US3] Explicit-signal assertions in `test_register_render_aware.py`: contract row 4
      (`render_style: "photographic"` + `usage_context: "held for photos / posed with"` + playful
      vibe yields `event_prop`; the trace shows the usage-rule match and NO suppression line).
      This holds by construction (the gate wraps only the vibe promotion, research D3), so the
      test is the falsifiable proof of FR-004/SC-003, guarding future refactors. Test-only change.
      Commit: `test(011): explicit event-prop usage beats the render gate (T008)`.

**Checkpoint**: The human override is locked in by a test a gate-everything refactor would fail.

---

## Phase 6: User Story 4 - Common marketing usage phrases are recognized (Priority: P3)

**Goal**: "marketing", "social", "instagram", "promotional" match an explicit marketing usage
rule instead of falling through to the unmatched default.

**Independent Test**: spec US4: usage_context containing a common marketing word; assert the trace
records an explicit keyword match, not the default line.

- [X] T009 [US4] Append the LAST row `(("marketing", "social", "instagram", "promotional"),
      "marketing")` to `USAGE_RULES` in `register/derive_register.py` (research D4: appending last
      preserves every existing row's precedence, including the event-prop rows). Tests in
      `test_register_render_aware.py`: contract row 6 (usage `"instagram feed"` yields a trace
      line recording the matched keyword and NOT the `"matched no rule => marketing base
      (default)"` line); precedence guard (usage `"instagram photo"` still matches the earlier
      event row on `"photo"` and yields `event_prop` base, so the new row cannot shadow an
      explicit event phrase). FR-006, SC-004 trace clarity.
      Commit: `feat(011): marketing usage keyword coverage (T009)`.

**Checkpoint**: All four stories green.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T010 Repo currency in the SAME commit that closes the feature (constitution VII): update
      `CLAUDE.md` (Active feature block: 011 built + structurally green, eye-gate pending; move
      010 to prior features) and `SYSTEM_MAP.md` (status + the new test surface
      `test_register_render_aware.py`). Verify no em-dashes in the NEW text 011 adds (the
      suppression + retention trace lines, the CLAUDE.md/SYSTEM_MAP updates); pre-existing text
      is out of scope.
      Commit: `docs(011): CLAUDE.md + SYSTEM_MAP currency (T010)`.

- [X] T011 DEFERRED HUMAN EYE-GATE (SC-007, quickstart §4) - PASSED 2026-07-01 by the operator on
      `output/run_CJXQ_20260701_154416` (CJXQ photographic watermelon marketing post): reads as a
      playful photographic marketing poster, not a prop, not corporate. The FIRST attempt
      (run_..._152554) rendered FLAT and exposed a 009 plan/execution drift (execute path dropped
      asset_profile), fixed in 265a524 with render_modes check 5 as the permanent guard.: ONE paid thin run for a playful brand
      with a photographic marketing brief
      (`.venv/bin/python harness/conductor.py --brand <playful-brand> --inputs <photo-marketing-inputs>.json --thin`),
      judged by the HUMAN EYE on `output/run_*/sign_*/final.png`: a playful marketing poster, not
      a hand-held prop, not a stiff corporate poster. Never run inside a self-test; requires the
      operator present. Record the verdict in SYSTEM_MAP.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none; run first, must be green.
- **Foundational (Phase 2)**: after T001. T002 and T003 are parallel (different files).
- **US1 (Phase 3)**: needs T002 + T003. T004 before T005 (same file, retention reads the gated register).
- **US2 (Phase 4)**: needs T004 (asserts the gate does not over-fire); independent of T005 for the
  register half but run after Phase 3 to keep one linear commit chain in the shared test file.
- **US3 (Phase 5)**: needs T004. Test-only.
- **US4 (Phase 6)**: independent of the gate (rule-table row); needs only T001 baselines, but
  sequenced after US1-US3 by priority.
- **Polish (Phase 7)**: T010 after all code tasks; T011 after T010, human-scheduled.

### Parallel Opportunities

- T002 ∥ T003 (harness/conductor.py + test file vs register/derive_register.py).
- Everything else touches `register/derive_register.py` or the shared
  `test_register_render_aware.py`, so it runs sequentially; the feature is small enough that this
  costs nothing.

---

## Implementation Strategy

**MVP = Phase 1-4 (US1 + US2 together)**: US1 is the reported defect; US2 is the proof the fix
did not break the shipped flat path. The constitution treats the no-regression half as part of the
fix, so the MVP checkpoint is after T007. US3 (T008) and US4 (T009) are small, independent
increments. T011 (the paid eye-gate) is deferred until the operator is ready to judge pixels;
structure green never substitutes for the eye.
