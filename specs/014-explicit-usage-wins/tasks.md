# Tasks: Explicit Usage Wins Over the Vibe Guess

**Input**: Design documents from `/specs/014-explicit-usage-wins/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/explicit_usage_contract.md, quickstart.md

**Tests**: Included inside every implementation task (constitution III; one task, one module,
one falsifiable test, one commit). All tests FREE (pure `derive_register` imports). Contract
rows refer to [contracts/explicit_usage_contract.md](contracts/explicit_usage_contract.md).

**Organization**: this is a ~12-line single-module fix, so the three user stories share ONE
engine task + ONE test task; each story still has its own named, independently runnable checks
inside the test file.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Repo root, flat layout: engine `register/derive_register.py`, self-tests `test_*.py` in root.

---

## Phase 1: Setup

**Purpose**: baseline green; the byte-identity anchor already exists.

- [X] T001 Run the existing free suites and record them green BEFORE any edit
      (`test_register_render_aware.py` 8/8 in particular, plus `test_conductor.py`,
      `test_render_and_scrub.py`, `test_render_modes.py`, `test_lossless_brief.py`,
      `test_product_refs.py`, `test_frontend_nav.py`: the same seven-suite sweep quickstart §2
      runs after the fix). No new baseline capture needed: contract row 2 reuses
      `test_register_render_aware.EXPECTED_PREFEATURE_PROFILE` (same wall-posted fixture, still
      the current output; verify by running that suite). If anything is red, STOP and report
      (honest nulls). No repo file changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

None. One module, one fix; the stories differ only in which checks they own.

---

## Phase 3: User Story 1 - A flat marketing post from a playful brand stays a marketing post (Priority: P1) 🎯 MVP

**Goal**: the vibe promotion no longer overrides an explicit marketing-keyword match, on any
render lane; the suppression is traced by keyword; tone retention applies automatically.

**Independent Test**: contract row 1: flat/absent render + promoting vibe + each of the four
marketing keywords yields `marketing` with one keyword-naming SUPPRESSED line, tone cues, and no
die-cut cue.

- [X] T002 [US1] The fix in `register/derive_register.py`: hoist the marketing row into the
      module constant `MARKETING_USAGE_KEYWORDS = ("marketing", "social", "instagram",
      "promotional")` and use that SAME tuple object in `USAGE_RULES` (research D1); the match
      loop records `base_row` + the already-computed `hit` keyword; in the promotion branch
      insert ONE elif between the 011 photo gate and the promotion: when
      `base_row is MARKETING_USAGE_KEYWORDS`, do NOT promote and append one trace line naming
      the matched keyword (no em-dash), e.g. "vibe would promote to event_prop (...) but
      usage_context explicitly matched 'social' (a human marketing statement, not a guess) =>
      promotion SUPPRESSED, register stays marketing". Photo gate stays FIRST and byte-unchanged
      (research D2: FR-006 single-entry by if/elif construction). Create
      `test_explicit_usage_wins.py` (011 test pattern; imports `derive_register` and the
      baseline literal from `test_register_render_aware`) with the US1 check covering contract
      row 1 for ALL FOUR keywords: register `marketing`, exactly one "SUPPRESSED" line naming
      that keyword, `font:rounded` + `palette:playful-accents` present, `shape:die-cut` absent,
      `font_role_hint == "rounded display"`, no em-dash in the new line; plus contract row 5
      (photographic + "instagram feed": `marketing`, EXACTLY one SUPPRESSED line, and it names
      the render, not the keyword).
      Commit: `feat(014): explicit marketing usage beats the vibe promotion (T002)`.

**Checkpoint**: the observed defect (run_CJXQ_20260701_173925) is fixed; the double-gate trace
is pinned.

---

## Phase 4: User Story 2 - Legacy behavior outside the marketing keywords is untouched (Priority: P1)

**Goal**: over-suppression is impossible to ship: the wall-posted lane and the unmatched default
are pinned byte-for-byte.

**Independent Test**: contract rows 2-3: wall-posted profile equals the imported pre-feature
literal; unmatched free text still promotes.

- [X] T003 [US2] No-regression checks in `test_explicit_usage_wins.py`: contract row 2 (the
      wall-posted + promoting-vibe profile's sorted-keys JSON equals
      `test_register_render_aware.EXPECTED_PREFEATURE_PROFILE` byte-for-byte for BOTH the
      absent-render case AND the explicit `"flat vector"` case: the flat lane writes no render
      trace line today, so the two profiles are identical and the second assertion is free; a
      build that starts tracing the flat lane, or over-suppresses on it, fails here) and
      contract row 3
      (usage "random gibberish nobody typed" + promoting vibe yields `event_prop` with the
      "matched no rule" default line AND the "vibe overrides" promotion line, zero SUPPRESSED
      lines). Also run the full existing-suite sweep and record it green (SC-004), especially
      `test_register_render_aware` 8/8 (its check7 survives per research D3). Test-only change.
      Commit: `test(014): wall-posted byte-identity + default promotion pinned (T003)`.

**Checkpoint**: both P1 stories done; an over-suppressing refactor now fails loudly.

---

## Phase 5: User Story 3 - Explicit event-prop usage keeps absolute precedence (Priority: P2)

**Goal**: the other human signal stays sovereign under future rule-table edits.

**Independent Test**: contract row 4: "instagram photo" (event keyword + marketing keyword in
one phrase) resolves `event_prop` via the event row with zero suppression entries.

- [X] T004 [US3] Precedence check in `test_explicit_usage_wins.py`: contract row 4 instantiated
      on BOTH lanes (usage "instagram photo" + promoting vibe, once with photographic render and
      once with render absent: register `event_prop` via the event-row match ("matched 'photo'"),
      ZERO lines containing "SUPPRESSED" in either profile), so the new suite alone covers its
      contract row's "any" render claim rather than leaning on the 011 suite's absent-render
      case; plus contract row 6 (photographic + wall-posted: the 011 photo-gate case
      byte-unchanged, its existing photo suppression line intact). Test-only change.
      Commit: `test(014): event-row precedence + 011 photo lane pinned (T004)`.

**Checkpoint**: all three stories green.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T005 Free live-trace validation per quickstart §3: write the 173925-defect subfields
      fixture (usage with "social"/"promotional", vibe 2/8, `render_style: "flat vector"`) to
      the scratchpad and run `register/derive_register.py --subfields ... --brand CJXQ --out
      /tmp/014check`; confirm register `marketing`, the keyword SUPPRESSED line, no die-cut
      flex. Fix anything wrong; commit only if fixes were needed.

- [X] T006 Repo currency (constitution VII): `CLAUDE.md` (active feature 014 built +
      structurally green; 013 moves to prior, its T009 eye-gate still pending) and
      `SYSTEM_MAP.md` (014 build-status block: the flat-lane leak, the row-identity gate, the
      single-entry trace rule, the cheap SC-005 eye path). No em-dashes in new text.
      Commit: `docs(014): CLAUDE.md + SYSTEM_MAP currency (T006)`.

- [X] T007 DEFERRED EYE CONFIRMATION (SC-005) - PASSED 2026-07-07 by the operator on
      `output/run_CJXQ_20260707_141245` (the 173925 re-brief: flat vector, "promotional social
      media post", vibe 2/8, plus one product shot): register=marketing via the 'social'
      suppression line (exactly one), no die-cut flex, flat+marketing rectangular opener; the
      image reads as a playful flat rectangular marketing poster (bubbly type, candy palette,
      mascots), NOT a hand-held sign. The same run also demonstrates 013 product fidelity on
      the flat lane: the branded JO'S CHA cups appear with printed logos. Feature COMPLETE.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: first, must be green.
- **US1 (T002)**: the fix + its checks; everything else asserts against it.
- **US2 (T003)**, **US3 (T004)**: test-only, sequential after T002 (shared test file), ordered
  by priority.
- **Polish (T005 → T006 → T007)**: after all code tasks; T007 is operator-scheduled and
  piggybacks on a natural run.

### Parallel Opportunities

None worth taking: one engine file and one shared test file; the feature is ~4 commits end to
end.

---

## Implementation Strategy

**MVP = Phase 1 + Phase 3 (T002)**: the defect is fixed and the double-gate trace pinned in one
commit. T003/T004 lock the blast radius (over-suppression and precedence) before docs. T007
costs nothing: the register value is fully visible in the free trace, so the eye only confirms
what the trace already proves, on a run that was going to happen anyway.
