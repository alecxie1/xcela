# Tasks: 022-form-size-progress

**Input**: `specs/022-form-size-progress/spec.md` + `plan.md`
**Tests**: included (constitution III: one falsifiable test per task; all FREE, no paid calls)
**Convention**: one task = one commit (repo dev workflow); [P] = parallelizable in principle,
though the repo's one-commit-per-task flow runs them sequentially.

## Phase 1: Setup

No setup tasks: no new modules, dependencies, or structure (plan.md).

## Phase 2: Foundational

- [X] T001 px parsing pinned in harness/format_size.py + test_format_size.py: add 像素 to
      the unit normalization table (identity on ASCII input pinned against the existing
      literal); extend test_format_size.py with value checks — resolve_size("750x300px")
      resolves to aspect 2.5 within existing delta bounds, "７５０×３００像素" normalizes to
      the same result, and a pre-022 cm case stays byte-identical.

## Phase 3: User Story 1 — structured size input with real units (P1)

**Goal**: W + H numeric inputs + cm/px unit select composing the SAME canonical brief string.
**Independent test**: composed-string byte-identity + resolved aspect, all free, by value.

- [ ] T002 [US1] the form: in frontend/index.html replace the single 尺寸 free-text input
      with W/H numeric inputs + a cm/px select (defaults 60/40/cm); formState() composes
      `"<W>x<H><unit>"` (untouched form -> exactly "60x40cm", THE pin); blank/zero/NaN W or
      H refuses loudly client-side before POST /run (FR-004); the FR-005 note (aspect-
      preserving ~1.5MP draft, not exact-pixel) sits adjacent to the fields. NEW
      test_form_size_progress.py: value-bearing grep pins for the three controls, the
      compose expression AND its default values (the SC-002 automated half), the refusal,
      and the note; update any pinned form-grep that named the old field (dated in place,
      never weakened — check test_deploy_readiness, test_lossless_brief, test_frontend_*
      first). All new user-facing copy: Chinese, no em-dashes.

## Phase 4: User Story 2 — the wait has stated expectations (P2)

**Goal**: elapsed-seconds counter + typical-duration copy on both waits; never a progress bar.
**Independent test**: wiring pins + the no-percentage guard; behavior judged at the T005 flow gate.

- [ ] T003 [US2] wait expectations: in frontend/index.html add a WAIT_EXPECT constants map
      (ONE place: derive + generate + layered-export typical-duration copy) and an
      elapsed-seconds counter rendered during the derive wait, the paid generation wait,
      and the export wait, keyed off the existing poll()/gate/export states; counter +
      copy CLEAR when the wait ends (image present, gate awaiting, export done/failed, or
      error surfaced) and never render on finished or pre-022 runs (FR-008). On resume
      (URL hash / runs picker) the counter starts from when THIS client began observing —
      understated elapsed is the accepted honest behavior (spec edge case). TIMING SOURCE
      (auditable, never invented): derive = inputs.json mtime -> gate_state.json mtime;
      generate = confirmation.confirmed_at -> generated.png mtime; export = export state
      created -> zip mtime; measured across the recent real CJXQ run dirs in output/, the
      measured runs named in a comment above WAIT_EXPECT. Copy is user-facing: Chinese,
      no em-dashes. Extend test_form_size_progress.py: pins for WAIT_EXPECT (all three
      kinds), the three wait renderings, the clear paths, and a guard that no
      percent/progress-bar markup exists anywhere in the stages panel (FR-007).

## Phase 5: Polish & ship

- [ ] T004 docs + sweep + ship: playbook.html 尺寸 row mentions px + the aspect-only draft
      contract; CLAUDE.md + SYSTEM_MAP status current; FULL suite sweep green; commit +
      push origin (origin ONLY — the vm remote is retired).
- [ ] T005 HUMAN GATE (SC-004): one FREE derive driven through the new W/H/px fields by
      the operator — judge the form flow, the composed size in the run's inputs.json on
      disk (the SC-002 byte-identity observation), the 015 gate's size row on a clamped
      case, and the DERIVE wait counter ticking/clearing. The generate and export
      counters are structurally pinned by T003 and judged opportunistically on the next
      routine PAID run (this gate spends nothing; never confirm just to watch a timer).

## Dependencies

- T001 -> T002 (the pin T002's tests lean on) -> T003 -> T004 -> T005.
- US1 (T002) and US2 (T003) are independently testable increments; US1 alone is the MVP.

## Implementation strategy

MVP first: T001+T002 answer 问题04+05 and are shippable alone; T003 answers 问题06; T004/T005
close the loop. Every task's tests are free; the ONLY human step is the T005 flow gate.
