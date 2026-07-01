# Implementation Plan: Lossless Brief (Field Honesty on the Thin Route)

**Branch**: `012-lossless-brief` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-lossless-brief/spec.md`

## Summary

Stop the input gate from leaking. Five deltas, all on the brief-to-prompt path of the thin route:
(1) thread `asset_type` + `occasion` from the brief through the conductor into `assemble_thin_prompt`
as a SCENE/SUBJECT section (verbatim, context-not-text, absent when both fields are blank so the
prompt stays byte-identical); (2) expose the EXISTING binding-notes channel on the first-run form as
a design-notes field, with nudges APPENDING via the channel's already-established ";"-join contract
(frontend-only change, the server/runner/conductor channel is untouched); (3) remove the inert
audience + warmth controls from the form (hero_icon has no control today; the writer stays tolerant
for legacy JSON); (4) make reference_relationship a fixed 3-option select whose values map 1:1 onto
`normalize_dial`'s lanes; (5) rename the sign-era message label to verbatim-text wording. One new
free self-test covers the prompt section, the BOTH-call-sites argv threading (applying the 009
drift lesson), the form surface, and legacy back-compat.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`), stdlib only; frontend is the existing no-framework
single-file HTML + vanilla JS

**Primary Dependencies**: none new; touched modules (`harness/conductor.py`, `harness/scene_author.py`,
`frontend/index.html`, `frontend/inputs_writer.py`) stay stdlib/vanilla

**Storage**: run-dir JSON artifacts (inputs.json, manifests); no schema change, JSON contract
back-compatible

**Testing**: repo-style standalone self-test (`test_lossless_brief.py`), pure imports + the
stubbed-`run_step` execute pattern from render_modes check 5; UI assertions are greps on the served
HTML (the weakest gate, declared as such); no paid calls

**Target Platform**: local Linux/WSL2, thin route only

**Project Type**: CLI pipeline + thin local web form

**Performance Goals**: N/A (prompt assembly, microseconds)

**Constraints**: byte-identical prompt when asset_type+occasion are blank (FR-003); byte-compatible
inputs JSON for legacy briefs (FR-006); zero behavior change to register engine (011), render
openers (009), kit/legacy routes (FR-010)

**Scale/Scope**: 4 files edited, 1 new self-test, ~60 lines of change

## Constitution Check

*GATE: evaluated pre-Phase-0, re-checked post-Phase-1. All PASS.*

| Principle | Verdict | How |
|---|---|---|
| I. Agent-free, not human-free | PASS | The whole feature is an input-gate repair: human words either drive the output (scene line, design notes, dial choice) or the control is removed. No new inference, no new glue judgment. |
| II. Eye is ground truth | PASS | Structural tests prove the words reach the prompt; SC-007 (one paid re-brief of the CJXQ watermelon post) is the pixel proof, explicitly checking subject fidelity AND that no scene words leak as painted text. |
| III. Falsifiable tests | PASS | Values, not tokens: the scene section must contain the exact asset_type/occasion strings (a build that drops them fails); the blank case must be BYTE-identical (a build that adds empty scaffolding fails); the execute-path argv must carry the fields (a build-plan-only build fails, the 009 lesson); the form greps assert both absence (dead controls, free-text dial, sign-era label) and presence (3 options, notes field, new label wording). |
| IV. Generalize | PASS | Nothing brand- or task-specific: every brief gains the same lossless path. |
| V. Honest nulls | PASS | Blank fields produce NO section (nothing fabricated); retired fields remain recorded provenance; the scene line passes human words verbatim, never paraphrased. |
| VI. Reconciliation per-dimension | PASS | Scene/subject is task-side context; brand locks untouched; the dial keeps its 3-lane semantics, only its capture becomes explicit. |
| VII. Repo is durable context | PASS | CLAUDE.md + SYSTEM_MAP updated in the closing commit. |
| Cost discipline | PASS | All tests free; the one paid run is the deferred eye-gate. |
| Output rule | PASS | New labels/prompt headers use no em-dashes. |

## Project Structure

### Documentation (this feature)

```text
specs/012-lossless-brief/
├── plan.md              # This file
├── research.md          # Phase 0 (6 wiring decisions, all resolved from code)
├── data-model.md        # Phase 1 (brief/prompt/form deltas)
├── quickstart.md        # Phase 1 (free validation + the eye-gate)
├── contracts/
│   └── lossless_brief_contract.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
harness/scene_author.py    # EDIT: assemble_thin_prompt(asset_type=, occasion=) + the SCENE/SUBJECT
                           #   section (conditional, verbatim, context-not-text framing);
                           #   two new CLI flags --asset-type / --occasion (thin route only)
harness/conductor.py       # EDIT: _scene_author_thin_argv carries the two fields; BOTH call sites
                           #   (build_plan AND execute) pass them (the 009 drift lesson)
frontend/index.html        # EDIT: design-notes textarea (first run) + nudge JOIN via ";" into the
                           #   existing style_notes channel; remove audience + warmth controls;
                           #   reference_relationship becomes a 3-option <select>; message label
                           #   renamed to verbatim-text wording
frontend/inputs_writer.py  # EDIT (minimal): tolerate absent audience/warmth (legacy keys still
                           #   accepted verbatim when present); no new fields (style_notes rides
                           #   the form JSON to the runner, not the inputs file, unchanged)
test_lossless_brief.py     # NEW free self-test (see contract)
CLAUDE.md / SYSTEM_MAP.md  # EDIT: currency in the closing commit
```

**Structure Decision**: no new modules. The scene section lives in `assemble_thin_prompt` (the one
home of the thin prompt); the notes feature is frontend-only because the ";"-split contract already
exists end to end (`scene_author` splits `--style-notes` on ";" at both consumption sites); the form
changes are confined to `index.html` plus writer tolerance.

**Explicitly NOT touched** (FR-010): `register/` (011), the four render openers and negatives
(009), `harness/kit.py`, legacy render-and-scrub, `frontend/server.py` + `frontend/runner.py`
(the notes channel already flows through them unchanged).

## Complexity Tracking

No constitution violations. Empty.
