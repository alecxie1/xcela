# Tasks: 023-edit-mode

**Input**: `specs/023-edit-mode/spec.md` + `plan.md`
**Tests**: included (constitution III: one falsifiable test per task; all FREE, no paid calls)
**Convention**: one task = one commit (repo dev workflow).

## Phase 1: Foundational (the inputs contract)

- [X] T001 the edit inputs contract: `inputs_writer.to_edit_inputs` (pure, fail-loud on
      missing base/instruction/bad region) + `write_inputs` mode dispatch + the
      to_inputs no-mode-key pin; `conductor.validate_inputs` edit branch (empty
      messages legal IFF mode=edit, the exact `has no messages` string preserved for
      design mode; base-exists / instruction-non-empty / region-shape checks). NEW
      `test_edit_mode.py`: writer + validate checks by value.

## Phase 2: User Story 1 — the edit run (P1)

- [X] T002 [US1] `harness/edit_author.py` (compose_edit_prompt PURE: verbatim CHANGE +
      PRESERVE + region-iff-set + product-fidelity-iff-products + style-notes channel;
      edit_size via PIL + resolve_size; build_region_mask; outside_region_stats with a
      named threshold constant; CLI derive/verify/generate legs with the runtime mask
      fallback) + `generate.generate_variant` additive `mask_path=None`. Tests: compose
      by value, mask + stats on synthetic images by value, mask-param default pin.
- [X] T003 [US1] the conductor edit route + server threading: build_plan/execute early
      branches (`_execute_edit` mirroring the 015 gate machinery; assumptions=[]),
      write_glue_artifacts early return, main() edit+full loud refusal;
      `parse_run_form` principal-upload dispatch (base part, loud refusal) +
      `write_run_inputs` base save. Tests: dry-run plan shape (route edit, no
      register steps), a REAL FREE `--phase derive` on a tmp fixture (verbatim prompt,
      gate awaiting, assumptions []), generate preflight refusal, parse/write dispatch
      by value.

## Phase 3: User Story 2 — the region + the form (P2)

- [X] T004 [US1+US2] the form: job-mode control (新设计 default, THE untouched-form pin)
      + edit fieldset (base upload, instruction, region canvas with drag-rect +
      清除选区, products shared) + design-fields hidden in edit mode + startRun branch
      (edit: loud Chinese base/instruction refusals; design: the EMPTY-MESSAGES loud
      Chinese guard naming the field, before any POST). Tests: grep pins for the mode
      control + defaults, edit controls, all three refusal strings, the guard's
      position; update any moved pinned form-grep dated in place.

## Phase 4: User Story 3 — the brand palette (P2)

- [X] T005 [US3] palette management: manage.html add-color / remove-row / per-color
      CN+EN name inputs, save payload carries names; brand_manager.update_brand
      computes rgb from hex (never None) — both halves of the wipe wart dead. Tests:
      test_brand_manager names+rgb round-trip by value, control greps.

## Phase 5: Polish & ship

- [X] T006 docs + sweep + ship: playbook.html gains the 改图 section + palette
      management line; CLAUDE.md + SYSTEM_MAP current; FULL suite sweep green; commit +
      push origin (origin ONLY — the vm remote is retired).
- [ ] T007 HUMAN GATES (spend, operator-run): (a) the mask probe — DONE 2026-07-21 on
      the real bowl swap (`output/run_CJXQ_editdry_20260721`, $0.08): images.edit
      ACCEPTED the mask but enforcement is SOFT (raw outside-mad 25.6 vs threshold 8);
      answered by the hard-composite hardening (deliverable = base + feathered region
      paste, byte-identical outside by construction, both stats audited);
      (b) SC-002 the 蒙自源 bowl swap — CLI dry run operator-judged GOOD 2026-07-21
      (swap landed, slogan/logo/other dishes intact); the browser-flow rehearsal is
      still owed before the client demo; (c) SC-005 the palette flow — open. Generate/
      export counters and the 022 T005 form gate can piggyback on the same session.

## Dependencies

- T001 -> T002 -> T003 -> T004 -> T006 -> T007; T005 independent after T001 (parallel
  in principle, sequential in the one-commit-per-task flow).
- US1 alone (T001-T004 minus the region canvas) is the MVP; the region work rides in
  T002/T004 but degrades honestly (no region = full-canvas + preserve clause).

## Implementation strategy

Contract first (T001), engine second (T002-T003, provable free end-to-end), surface
third (T004), the folded palette story (T005), then ship + the three human gates.
