# Tasks: Pre-Spend Confirm Gate

**Input**: Design documents from `specs/015-pre-spend-confirm-gate/`

**Prerequisites**: plan.md, spec.md (clarified), research.md, data-model.md, contracts/ (cli-phases, assumptions-schema, server-routes), quickstart.md

**Tests**: included per constitution §III (falsifiable structural tests are mandatory in this project; every FR names a property a wrong build cannot fake). NO paid calls in any automated task; the one paid step is the human-scheduled eye-gate (T017).

**Organization**: grouped by user story. US1 alone is the MVP (gate visible, spend blocked, confirm generates once).

**Commit discipline** (§VII): one task, one commit; CLAUDE.md + SYSTEM_MAP updated in the SAME commit that stales them (T015).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (baselines the whole feature pins against)

- [x] T001 Create `test_confirm_gate.py` scaffold + pre-015 baselines: capture (a) the thin-route register profile + trace baseline as inlined literals (reuse the 014 pinning pattern from `test_explicit_usage_wins.py`), (b) a `build_plan` full-run thin argv baseline (the `--phase full` byte-identity reference), (c) the archived `run_CJXQ_20260701_173925` defect subfields as a committed fixture in `tests_support/fixtures/subfields_173925.json` (the SC-003 replay input). Scaffold runs green with zero feature code (baselines only assert today's behavior).

---

## Phase 2: Foundational (the two CLI seams every story stands on)

- [x] T002 (drift guard amended to an EXPLICIT `--verify-prompt` flag mid-task: the legacy CLI approve-nudge re-runs the step on the same dir with a changed prompt and must keep overwriting; contract updated) `--prompt-only` + resume drift guard in `harness/scene_author.py` (contracts/cli-phases.md): argparse flag, thin driver returns immediately after `final_prompt.txt` is written (no `generate` import, no refs assembly); WITHOUT the flag, when `final_prompt.txt` already exists in `--out`, re-assemble and compare, on mismatch exit nonzero with the named drift error, on match generate as today; no existing file = byte-identical current behavior. Checks in `test_confirm_gate.py`: prompt-only writes the prompt and makes zero generation calls (stubbed `generate_variant`); drift mismatch fails loud; match proceeds (stubbed).
- [ ] T003 `--phase derive|generate|full` in `harness/conductor.py` (contracts/cli-phases.md): default `full` byte-identical (assert plan/argv equality against the T001 baseline); `derive` = calibrate (SKIPPED iff `<out>/calibration.json` exists) + derive_register + scene_author thin with `--prompt-only` + write `gate_state.json` (`awaiting_confirmation`) + manifest note "derived, awaiting confirmation; no image spend", then exit (no approve gate step); `generate` = refuse with a named error unless gate state is `confirmed` and `sign_s1/final_prompt.txt` exists, run the scene_author step without `--prompt-only`, write `generating` then `done`; `--phase derive` on a kit/legacy route = named fail-loud error. Checks: stubbed-run_step argv assertions for both phases (the 009/012 drift-guard pattern), calibrate skip on resume, wrong-state refusal.

**Checkpoint**: the conductor can stop before spend and resume after it; nothing user-facing yet.

---

## Phase 3: User Story 1 (P1): see what the tool decided before paying (MVP)

**Goal**: every browser run stops at a gate showing the derived register, anchors/flexes, prompt, and every recorded assumption; confirm (cost-stated, idempotent) triggers exactly one generation.

**Independent test**: submit a brief in the browser; the run stops with the plan and assumption list visible and NO `generated.png`; confirm; exactly one generation runs from the confirmed plan (quickstart steps 1 and 3, minus the answer loop).

- [ ] T004 [P] [US1] `--assumptions-out` in `register/derive_register.py` (contracts/assumptions-schema.md): when present, write the engine's AssumptionRecords: `register_lane` (usage_context matched no USAGE_RULES row, including blank; options = marketing pick writing `"marketing"` and event-prop pick writing `"held for photos"`; the formal option arrives with T009) and `magnitude` (slider source fell back from calibration; options = the two vibe slider integers). When absent: profile + trace BYTE-IDENTICAL to the T001 pins. Checks: record shapes per contract; the 173925 fixture replay emits the `register_lane` record (SC-003); no-flag byte-identity.
- [ ] T005 [US1] Assumption aggregation in `harness/conductor.py`: derive phase appends conductor-level records (`render_style` unrecognized -> flat_graphic, `relationship_dial` unrecognized -> extend, `format_size` unparseable/clamped from `fmtsize.resolve_size`) to the engine records and writes `<out>/assumptions.json` (ordered per contract); zero guesses = `[]`. Checks: each conductor record fires on the exact triggering input and NOT on recognized input; the union file validates against the contract shapes; no em-dash in any emitted string (FR-013).
- [ ] T006 [US1] Phase-1 flow + confirm route in `frontend/runner.py` + `frontend/server.py` (contracts/server-routes.md): runner argv builders gain the phase parameter (pure, testable; nudge rerun = phase derive on a NEW run dir per clarification Q2); `POST /run` launches `--phase derive` via the existing `_launch_async` + `run_error.txt` channel; NEW `POST /run/<id>/confirm` per contract: only from `awaiting_confirmation`, writes `confirmed` (+ prompt sha + cost label) BEFORE launching `--phase generate`, no-ops with the current state on `confirmed|generating|done` (FR-012). Checks: argv builders; idempotency (second confirm triggers zero launches, stubbed); state transition order.
- [ ] T007 [US1] Gate stage + panel in `frontend/run_view.py` + `frontend/index.html` (contracts/server-routes.md): stages payload gains `gate` (state + assumptions + answers_applied + cost label; `present: false` honest null for pre-015 run dirs); the run view renders the gate panel when awaiting: derivation summary (register lane, anchors_held, locks_flexed), read-only explicit inputs, one row per assumption (cause sentence + assumed value; controls wired in US2), confirm button labeled with the paid cost; `confirmed|generating` shows paid-progress; `done` falls through to today's image + approve/nudge gate. Checks: stage payload contract over a synthetic run dir; honest null; presence greps for the panel + cost label (declared the weakest gate per the 010 precedent).
- [ ] T008 [US1] US1 falsifiable sweep in `test_confirm_gate.py`: end-to-end stubbed browser flow (POST /run -> derive artifacts land, zero generation calls -> confirm -> exactly one generate launch); drift-guard reset path (inputs mutated after confirm -> generate fails loud, state back to `awaiting_confirmation`); manifest carries the honest awaiting note (FR-010).

**Checkpoint**: US1 alone is shippable: the gate exists, spend is blocked, misframes are visible pre-spend, confirm pays once.

---

## Phase 4: User Story 2 (P2): fix a wrong assumption without paying

**Goal**: constrained picks on assumption rows write back into the run's inputs, re-derive free in seconds, and are recorded as explicit human statements.

**Independent test**: at a gate with a non-empty assumption list, change one answer; the derivation updates with zero generations; the updated profile equals a fresh run's profile with that value from the start (quickstart step 3 answer loop).

- [ ] T009 [US2] The formal lane hard row in `register/derive_register.py` (contracts/cli-phases.md): ONE additive USAGE_RULES row `(("formal document", "official notice"), "formal")` appended LAST; the `register_lane` record's options gain the formal pick writing `"formal document"`; verify `REGISTER_HINTS` covers `formal` (it is an existing register value via the formality>=8 override) and add the hint entry if missing. Checks: the new keywords derive `formal` as a hard base (no vibe resolution); ALL T001-pinned baselines byte-identical (the row is inert for every input lacking the phrases); event rows keep precedence.
- [ ] T010 [US2] Answer route + write-back in `frontend/server.py` (+ a small pure `apply_answer` helper in `frontend/inputs_writer.py`) (contracts/server-routes.md): `POST /run/<id>/answer {assumption_id, label}` resolves the write from the run dir's own `assumptions.json` (unknown id/label or non-awaiting state = named fail-loud, previous derivation kept); applies `writes` to the run dir `inputs.json`; appends `answers_applied` provenance to `gate_state.json`; re-launches `--phase derive --out <run_dir>` (calibration.json present -> vision calls skipped). Checks: refusals; provenance; the re-derive launch argv; calibrate argv NEVER present on an answer re-derive.
- [ ] T011 [US2] Gate controls in `frontend/index.html`: each assumption row renders its constrained control (lane/size/render/dial picks as selects, magnitude as the two sliders) posting to the answer route; the panel re-polls and refreshes; a named error from the route is shown and the previous derivation stays. Checks: presence greps for the controls + the error surface (weakest gate, declared).
- [ ] T012 [US2] Round-trip identity sweep in `test_confirm_gate.py` (FR-006, the feature's load-bearing test): for EVERY shipped option of EVERY record type (3 lane picks, each size pick, slider values, render picks, dial picks): apply write-back + re-derive == a fresh run whose inputs carried that value from the start (byte-comparable register profile + assumptions recomputed whole, never accumulated); plus SC-002's structural half: the answer loop makes zero generation calls.

**Checkpoint**: the correction loop is free, convergent, and provably path-independent.

---

## Phase 5: User Story 3 (P3): no friction when nothing was guessed, no regression anywhere

**Goal**: a complete brief costs one extra click and zero questions; every existing surface is byte-identical.

**Independent test**: a zero-guess brief renders a gate with zero rows + confirm; the full prior suite sweep is green (quickstart step 2).

- [ ] T013 [P] [US3] Zero-guess and legacy rendering: gate with `assumptions == []` shows summary + confirm only, manufactures no questions (FR-008, SC-004); pre-015 run dirs render exactly as today (honest-null gate stage). Checks in `test_confirm_gate.py` over synthetic run dirs (one empty-assumptions, one pre-015 shape).
- [ ] T014 [US3] Byte-identity + no-regression closure: assert `--phase full` thin artifacts byte-identical to the T001 baseline; kit/legacy plan argv untouched; `derive_register` without `--assumptions-out` byte-identical (profile + trace) INCLUDING post-T009 (formal-row inertness); nudge rerun argv lands on phase derive (new run dir, gate present). Then run the full prior sweep (quickstart step 2 list: conductor, render_and_scrub, thin_route, render_modes, register_render_aware, explicit_usage_wins, lossless_brief, product_refs, reference_upload, frontend_intake/runner/stages, frontend_nav, multipart, onboard) and update ONLY the tests whose flow intentionally changed (e.g. `test_frontend_runner.py` argv shape), each updated assertion staying falsifiable (§III), never weakened to token presence.

---

## Phase 6: Polish, docs currency, and the human gates

- [ ] T015 [P] Update `CLAUDE.md` (active-feature block above the SPECKIT markers) + `SYSTEM_MAP.md` (header status + journey 4 gains the gate step) in the same commit that stales them (§VII): the browser flow now stops at the pre-spend gate; answers are explicit human statements; the CLI default is untouched; note the deferred full-interview upgrades stay in the inbox brief.
- [ ] T016 Run the complete free surface one last time and paste real output into the task: `test_confirm_gate.py` (all checks), the quickstart step 2 sweep, and the server GET/POST smoke over a synthetic run dir (stages gate stage, confirm idempotency, answer refusal), NO paid calls anywhere.
- [ ] T017 The human gates (quickstart steps 3-4, NOT automated; needs the human, the last step spends): (a) FREE browser dry pass: ambiguous brief ("goes viral on rednote" + "about poster size") stops at the gate with two assumption rows, a pick refreshes the plan in seconds, walking away leaves the honest draft, a server restart re-renders the gate from disk; (b) the ONE paid eye-gate (SC-006): change an answer, confirm (cost stated), exactly one generation, judge by eye that the image matches the confirmed framing, then nudge and confirm the rerun lands on a NEW gate before any second spend. Record the verdict in `SYSTEM_MAP.md`.

---

## Dependencies

- T001 -> T002, T003 (baselines exist before seams change behavior)
- T002 + T003 -> all US1 tasks
- Within US1: T004 [P] and T006 can start together after T003 (different files); T005 needs T004 (merges its records); T007 needs T005 + T006 (renders their artifacts); T008 needs T004-T007
- US1 -> US2 (the gate and records must exist before controls edit them); within US2: T009 -> T010 -> T011 -> T012
- US3: T013 [P] anytime after T007; T014 LAST among code tasks (the closure sweep)
- T015 [P] with any late task; T016 after T014; T017 after T016, human-scheduled

## Parallel opportunities

- T004 (register/) alongside T006 (frontend/) after the foundational phase: disjoint files
- T013 alongside US2 tasks: it only touches rendering paths US2 does not
- T015 docs alongside T014/T016

## Implementation strategy

MVP = Phases 1-3 (T001-T008): the gate exists, spend is blocked, assumptions are visible,
confirm pays once. That alone converts every future derivation defect from a paid misrender
into a free catch. US2 (T009-T012) adds the free correction loop; US3 (T013-T014) locks the
zero-friction and no-regression guarantees; T017 is the load-bearing human verdict, with its
free half (the dry pass) available before any spend.
