# Implementation Plan: Pre-Spend Confirm Gate

**Branch**: `015-pre-spend-confirm-gate` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-pre-spend-confirm-gate/spec.md`

## Summary

Every browser-launched thin run stops after deriving its plan (calibrate + derive_register +
assemble_thin_prompt) and BEFORE the paid gpt-image-2 call. The gate surfaces the derived
register, anchors/flexes, the final prompt, and a structured list of every assumption the
derivation recorded; assumption rows are the only editable surface (constrained picks recorded
as explicit human statements); answers write back into the run's inputs and re-derive free;
generation runs only on an explicit, idempotent, cost-stated confirmation. CLI one-shot and
kit/legacy behavior stay byte-identical.

Technical approach: split the run at the two natural seams that already exist. (1)
`scene_author.py` thin driver writes `final_prompt.txt` (line ~1077) before generation begins
(line ~1081): a `--prompt-only` flag returns right there. (2) `conductor.py` gains a
`--phase derive|generate|full` switch (default `full` = today, byte-identical): `derive` runs
calibrate (skipped when `calibration.json` already exists in `--out`) + derive_register +
scene_author `--prompt-only`, writes `assumptions.json`, stops; `generate` resumes an existing
run dir, re-assembles the prompt, fail-louds if it differs from the confirmed
`final_prompt.txt` (FR-007 drift guard), and generates. Assumptions are emitted STRUCTURED at
each guessing site (never parsed out of prose trace): `derive_register` gains an optional
`--assumptions-out` flag (profile bytes untouched, all 011/014 pins hold); conductor-level
guesses (render_style, dial, format_size) are appended by the conductor. The server splits
`POST /run` into phase-1 launch + `POST /run/<id>/answer` (write-back + free re-derive) +
`POST /run/<id>/confirm` (idempotent phase-2 launch); the existing stages UI gains the gate
panel.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`), stdlib only for all new code (established
project constraint; the frontend/harness glue has zero third-party deps)

**Primary Dependencies**: none new. Reuses `harness/conductor.py` (orchestrator),
`harness/scene_author.py` (thin driver + `assemble_thin_prompt`),
`register/derive_register.py` (the guessing sites + `_derivation_trace`),
`harness/format_size.py` (size resolution + `needs_review`), `frontend/server.py` +
`frontend/runner.py` + `frontend/run_view.py` + `frontend/index.html` (the live-runner),
`frontend/inputs_writer.py` (inputs JSON contract)

**Storage**: files in the run dir (`output/run_*/`), as today: `inputs.json`,
`calibration.json`, `register_profile.json`, `sign_s1/final_prompt.txt`, plus new
`assumptions.json` and `gate_state.json`

**Testing**: `test_confirm_gate.py` self-test (stdlib, no paid calls, stubbed generation via
the established stubbed-run_step / stubbed-execute pattern from 009/012/013); full
no-regression sweep of the existing suites

**Target Platform**: local Linux (WSL2), browser UI served by the stdlib `http.server`
frontend

**Project Type**: web-frontend-over-CLI (the 004 pattern: the server shells out to the
conductor and reads artifacts; it never reimplements derivation or generation)

**Performance Goals**: answer round-trip (write-back + re-derive + gate refresh) well under
30s (SC-002); derive phase adds no paid image call; calibration (two small vision calls)
runs once per run dir and is never repeated on answer changes

**Constraints**: existing artifacts and flows byte-identical when the feature is not
engaged (CLI default `--phase full`, kit/legacy untouched, register profile JSON bytes
unchanged, prior trace pins hold); no em-dashes in user-facing strings; no paid generation
in any automated test

**Scale/Scope**: single-operator local tool; one gate per run dir; ~5 assumption dimensions
in v1 (register lane, format size, magnitude fallback, render style, relationship dial)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **§I Agent-free, NOT human-free**: PASS, strengthened. The feature adds the missing
  INPUT-side human gate; nothing new is automated, judgment moves from silent defaults to
  explicit operator confirmation. No walk-away path is created (the gate blocks spend).
- **§II Ground truth is the user's eye**: PASS. The gate validates STRUCTURE (derivation,
  assumptions, prompt) pre-spend; pixels remain judged by the eye post-generation (SC-006
  eye-gate retained; the taste gate is unchanged).
- **§III Falsifiable tests only**: PASS. Key properties a wrong build cannot fake: zero
  generation calls in the derive phase (stubbed-generate assertion); per-option write-back
  round-trip identity (re-derived profile == fresh-run profile, byte-comparable); phase
  `full` byte-identity against today's artifacts; confirm idempotency (second confirm = no
  second generate call); prompt drift fail-loud. Assumptions are emitted structured at the
  guess site, NOT regex-parsed from prose (a token-presence gate is forbidden).
- **§IV Generalize, do not hand-tune**: PASS. The gate is brand- and task-agnostic; the
  assumption vocabulary comes from the engine's own guessing sites, not from any one image.
- **§V Honest nulls**: PASS. Abandoned drafts persist with an honest manifest note; a
  failed calibration surfaces as a magnitude assumption row instead of a silent fallback;
  every write-back is recorded (provenance in the manifest).
- **§VI Reconciliation core**: PASS. Answers set DIRECTION inputs only; MAGNITUDE stays
  image-driven (calibration is never re-run on answer changes, provably: calibrate argv
  independent of answers). The lane pick flows through the existing explicit-usage hard
  channel (014 semantics), never bypassing the per-dimension resolution.
- **§VII Repo is durable context**: PASS. Spec/plan/tasks in `specs/015-*`; CLAUDE.md +
  SYSTEM_MAP updated in the same commits that stale them.
- **Cost discipline**: PASS by construction: the feature's purpose is keeping the paid call
  out of the iteration loop; tests stub generation; the one paid run is the human eye-gate.

Post-design re-check (after Phase 1): no violations introduced; no Complexity Tracking
entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/015-pre-spend-confirm-gate/
├── spec.md              # feature spec (clarified 2026-07-08)
├── plan.md              # this file
├── research.md          # Phase 0: seam + emission + write-back decisions
├── data-model.md        # Phase 1: DerivationDraft, AssumptionRecord, Confirmation
├── quickstart.md        # Phase 1: free structural validation steps
├── contracts/
│   ├── assumptions-schema.md   # assumptions.json + gate_state.json shapes
│   ├── cli-phases.md           # conductor --phase + scene_author --prompt-only + derive --assumptions-out
│   └── server-routes.md        # POST /run (phase 1), /run/<id>/answer, /run/<id>/confirm, stages extension
└── tasks.md             # Phase 2 (/speckit-tasks output, not created here)
```

### Source Code (repository root)

```text
harness/
├── conductor.py         # --phase derive|generate|full; assumptions aggregation; resume-aware calibrate
├── scene_author.py      # thin driver --prompt-only (stop after final_prompt.txt); drift check on resume
└── format_size.py       # UNTOUCHED (its needs_review/defaulted result feeds an assumption record)

register/
└── derive_register.py   # optional --assumptions-out (structured records; profile bytes UNTOUCHED)

frontend/
├── server.py            # POST /run -> phase derive; new /run/<id>/answer + /run/<id>/confirm; idempotency
├── runner.py            # argv builders for the two phases (pure, testable)
├── run_view.py          # stages payload gains gate stage (assumptions + state)
├── inputs_writer.py     # write-back helper reuses the existing inputs JSON contract
└── index.html           # gate panel: derivation summary, assumption rows, confirm button (cost-stated)

test_confirm_gate.py     # the feature's falsifiable self-test (no paid calls)
```

**Structure Decision**: no new directories. The feature lands as surgical additions to the
existing thin-route files, honoring the established seams: pure argv builders in
`frontend/runner.py`, artifact-reading views in `frontend/run_view.py`, subprocess
orchestration only in `harness/conductor.py`, engine knowledge only in
`register/derive_register.py`.

## Complexity Tracking

No constitution violations to justify.
