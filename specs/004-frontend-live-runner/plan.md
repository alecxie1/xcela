# Implementation Plan: Frontend Live-Runner (single-sign)

**Branch**: `004-frontend-live-runner` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-frontend-live-runner/spec.md`

## Summary

The thin spine (feature 003) runs agent-free from one CLI command and is eye-verified. This feature
adds a LOCAL web frontend, THIN over that CLI, so the operator can drive ONE single-sign brief
himself: type a structured form, press Run (paid, cost-labeled), watch the stages appear
progressively from the run directory (brief → register/dial → assembled prompt → generated sign),
and take one of two taste actions (approve, or nudge-rerun with a binding note).

Technical approach (grounded in the verified code): the UI is a stdlib local web server + a single
static HTML/vanilla-JS page — NO framework, NO build step, NO new dependencies (matches the repo's
stdlib ethos and the thin posture). It NEVER reimplements generation/register/prompt assembly: it
(1) writes a single-sign inputs JSON in the 002 shape, verbatim; (2) shells out to the EXISTING
`conductor.py --thin --no-approve` (each call makes a new timestamped `run_*` dir); (3) polls that
run dir and renders each artifact as it lands. The taste gate lives in the UI (the human): approve =
stop; nudge = re-invoke the conductor with the binding note. The ONE conductor change needed is a
top-level `--style-notes` pass-through flag (the conductor already threads `--style-notes` to the
thin `scene_author` on its interactive nudge path; this exposes the same as a non-interactive CLI
surface) so a nudge-rerun is a plain CLI call that writes a NEW run dir, never UI-orchestrated.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`). Frontend = stdlib `http.server` local server + one
static HTML page with vanilla JS (no framework, no bundler, no new deps).

**Primary Dependencies**: none new. Reuses `conductor.py --thin`, `scene_author --thin`
(`assemble_thin_prompt(style_notes=...)`), the 002 intake (`validate_inputs`, `format_size.py`,
`prompt_elements.py`), `register/`, and the run-dir artifact contract. gpt-image-2 is the paid step,
human-triggered.

**Storage**: Files. The form writes a single-sign inputs JSON; the conductor writes per-run
artifacts under `output/run_*/` (gitignored). Brand data in `answer_keys/`.

**Testing**: Falsifiable STRUCTURAL self-tests in the `test_*.py` style (stdlib). NO paid image
generation in any test — tests target the pure form-writer, the run-dir stage reader, and the
conductor-argv builder. The one paid single-sign run is the human's eye-gate after the build.

**Target Platform**: Localhost web app on the operator's machine, invoking the CLI on the same host
and reading the run dir. Single-operator, single-flight, single-sign.

**Project Type**: Single project + a thin local web frontend over the existing CLI. No hosted/multi-
user service.

**Performance Goals**: Not latency-bound. The paid gpt-image-2 call (~$0.08 single-sign) dominates;
the UI polls the run dir (~1s) to render stages progressively. The dial + assembled prompt appear
before the paid image returns.

**Constraints**: THIN over the agent-free core (shell out to the CLI; never reimplement
generation/register/prompt assembly). Reruns run through the conductor CLI, not the UI. Structured
form only (no NL parser). Reference required (v1). Honest nulls on missing artifacts. Cost-labeled
paid trigger. No paid generation in tests. No em-dashes in user-facing text. The standalone CLI must
run with the frontend absent.

**Scale/Scope**: v1 single-sign, single brand with an answer key (AIA today; brand-general via the
`answer_keys/*.json` dropdown). Campaign/multi-sign, brand-intake front half, ref-less runs, and the
font moat are explicitly out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The UI IS the taste gate (human approves/nudges); the structured form keeps every field verbatim (no NL-parser agent); reruns go through the agent-free conductor CLI, not UI orchestration. | PASS |
| II. Ground truth = the eye | The UI surfaces the real `generated.png` for the human's verdict; tests assert STRUCTURE only (verbatim JSON, stage paths, argv). No VLM self-score. | PASS |
| III. Falsifiable tests only | Form-writer emits byte-for-byte 002 JSON with exactly one `signs[]` entry that `validate_inputs` accepts; stage reader returns artifact presence/content + honest null; argv-builder yields `--thin --no-approve [--style-notes]`. Each fails a wrong build. | PASS |
| IV. Generalize, do not hand-tune | Brand is a dropdown over `answer_keys/*.json`; no AIA literals in UI code. The form renders the 002 contract, brand-general. | PASS |
| V. Honest nulls | A missing stage artifact (e.g. honest-null blank sign) is shown as the null + the manifest note, never a fabricated placeholder. | PASS |
| VI. Reconciliation per-dimension | Untouched. The UI READS `register_profile.json`; it never computes the register. | PASS |
| VII. Repo is durable; thin core | UI shells out to the CLI + reads artifacts; no new deps (stdlib server + static page); the standalone thin route runs UI-absent (test-proven). One-module-one-test-one-commit. CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid generation in any test; the paid single-sign run is human-triggered and
cost-labeled. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-frontend-live-runner/
├── spec.md              # Feature spec (clarified 2026-06-24: progressive stages + new-run-per-nudge)
├── plan.md              # This file
├── research.md          # Phase 0: trigger mechanism, UI stack, progressive polling, reuse map
├── data-model.md        # Phase 1: form state, inputs JSON, run stages, attempt entities
├── contracts/
│   ├── inputs-json.md          # the single-sign 002-shape JSON the form writes
│   ├── run-trigger.md          # conductor CLI surface the UI calls (--thin --no-approve [--style-notes])
│   ├── stage-read.md           # run-dir artifacts the UI polls + honest-null rules
│   └── http-endpoints.md       # the local server routes (form, run, stages, image)
├── quickstart.md        # Phase 1: free structural validation + the human's paid run
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
frontend/                       # NEW: the thin local web frontend (stdlib + one static page)
├── inputs_writer.py            # pure: single-sign form state -> 002-shape inputs JSON (verbatim, 1 sign)
├── run_view.py                 # pure: run_dir -> stage dict (artifact presence + content); honest null
├── runner.py                   # build_conductor_argv (pure, testable) + launch (subprocess -> run dir)
├── server.py                   # stdlib http.server glue: form page, POST /run, GET /run/<id>/stages, image
└── index.html                  # the form + progressive stage panels + approve / nudge (inline vanilla JS)

harness/
└── conductor.py                # CHANGED: add top-level --style-notes (campaign-level) threaded to the
                                #   thin scene_author argv, so a non-interactive nudge-rerun is a plain CLI
                                #   call writing a NEW run dir. No other conductor change (single-sign already
                                #   works: the per-sign loop runs once for a 1-entry signs[]).

test_frontend_intake.py         # NEW: inputs_writer -> verbatim 002 JSON, exactly 1 sign, validates.
test_frontend_stages.py         # NEW: run_view over a synthetic run dir -> stages + honest null on missing.
test_frontend_runner.py         # NEW: build_conductor_argv -> --thin --no-approve [--style-notes] (no exec).
test_conductor.py               # CHANGED: --style-notes threads to the thin scene_author argv (dry-run);
                                #   standalone thin run intact (one command, UI absent).
```

**Structure Decision**: A new top-level `frontend/` package holds the thin UI. The genuinely new
capability is split into PURE, testable modules — `inputs_writer` (form → verbatim JSON),
`run_view` (run dir → stages), and `runner.build_conductor_argv` (the CLI surface) — with
`server.py` + `index.html` as thin glue that wires them to `http.server` and the browser. The ONLY
engine change is a `--style-notes` pass-through on `conductor.py` (small, agent-free CLI surface) so
the browser taste gate's nudge is a plain conductor call, not UI-orchestrated generation (resolving
the brief's flagged open question). Nothing in generation/register/prompt assembly is reimplemented
(FR-006), and the standalone thin route still runs UI-absent (FR-011 / SC-005).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
