# Implementation Plan: Render-Aware Register

**Branch**: `011-register-render-aware` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-register-render-aware/spec.md`

## Summary

Fix the flat-vector-era heuristic in `register/derive_register.py` where a playful+informal brand
vibe promotes a `marketing` job to `event_prop` regardless of what is being made. Thread the
brief's `render_style` (feature 009, already captured on the thin route) one layer further, into
the subfields the register engine consumes, and GATE the vibe promotion so it does not fire for
photographic renders. An explicit event-prop usage phrase still wins. When the gate holds a
playful brand's job in `marketing`, retain the playful TONE cues (rounded font, playful accents)
while excluding the die-cut PROP-format cue: format follows the task, tone follows the vibe,
decided independently (constitution VI, the per-dimension split). Every gate decision and every
retained cue lands in `_derivation_trace`. Scope: the register engine + the thin-route subfields
plumbing only; the 009 opener matrix and the legacy/kit paths are untouched.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`, run as `.venv/bin/python`)

**Primary Dependencies**: stdlib only (both touched modules, `register/derive_register.py` and
`harness/conductor.py`, are stdlib-pure and must stay that way)

**Storage**: run-dir JSON artifacts (`subfields.json`, `register_profile.json`); no DB

**Testing**: repo-style standalone self-test scripts (`test_*.py`, no pytest), free structural
surfaces only; the new test imports `derive_register` as a pure function (no subprocess, no paid
calls)

**Target Platform**: local Linux/WSL2 CLI + the thin local web frontend that shells out to it

**Project Type**: CLI pipeline (conductor orchestrates subprocess steps)

**Performance Goals**: N/A (deterministic rule-table inference, microseconds)

**Constraints**: zero paid model calls in tests; `register/` must not import `harness/` (the
conductor invokes `derive_register.py` as a subprocess, so there is no shared import path);
kit/legacy subfields.json must stay byte-identical

**Scale/Scope**: 2 modules edited, 1 new self-test file, ~40 lines of engine change

## Constitution Check

*GATE: evaluated pre-Phase-0 and re-checked post-Phase-1 design. All PASS.*

| Principle | Verdict | How the plan satisfies it |
|---|---|---|
| I. Agent-free, not human-free | PASS | `render_style` is a HUMAN input at the input gate (009 form field). The gate suppresses a machine GUESS (vibe heuristic), never a human statement: an explicit event-prop usage phrase wins over the gate (FR-004/US3). |
| II. Ground truth is the eye | PASS | Automated tests prove structure (register value, trace content, cue set). The pixel claim (a playful marketing poster, not a prop, not a corporate poster) is SC-007, a deferred human eye-gate on one paid run. |
| III. Falsifiable tests only | PASS | Tests assert VALUES a wrong build cannot satisfy: register equals `marketing` under photo (a no-gate build returns `event_prop`); register equals `event_prop` under flat (an over-eager gate returns `marketing`); `shape:die-cut` ABSENT while `font:rounded` + `palette:playful-accents` PRESENT in `brand_locks_flexed` (a tone-stripping build fails the presence half, a format-leaking build fails the absence half); trace entry names the render choice. No token-presence-only gates. |
| IV. Generalize, do not hand-tune | PASS | The gate keys on (render choice x vibe), not on any brand or image. Tone retention keys on the vibe alone (FR-011), so it applies to every playful brand's marketing job, not just the watermelon post that exposed the bug. |
| V. Honest nulls | PASS | Absent/unrecognized `render_style` takes the historical flat interpretation with ZERO behavior change (FR-007); the gate writes a trace line only when it actually fires, so untouched paths produce byte-identical profiles. |
| VI. Reconciliation per-dimension | PASS | This feature IS the per-dimension split: format (prop vs poster) is task-governed via render choice; tone (playful vs restrained) is vibe-governed. The old code collapsed both into one register label; the fix decides them independently. |
| VII. Repo is the durable context | PASS | One spec, one plan, per-task commits; CLAUDE.md + SYSTEM_MAP.md updated in the same commit that makes them stale. |
| Cost discipline | PASS | The new self-test imports the pure function, zero paid calls. The ONE paid run is the deferred SC-007 eye-gate, run only after structure is green. |
| Output rule | PASS | No em-dashes in any NEW operator-facing text this feature writes (the two new trace lines, docs updates). Pre-existing spec artifacts and trace strings follow repo precedent and are not swept here. |

## Project Structure

### Documentation (this feature)

```text
specs/011-register-render-aware/
├── plan.md              # This file
├── research.md          # Phase 0 output (design decisions, all resolved)
├── data-model.md        # Phase 1 output (subfields + register_profile deltas)
├── quickstart.md        # Phase 1 output (free validation commands + the eye-gate)
├── contracts/
│   └── derive_register_contract.md   # Phase 1 output (pure-function behavior table)
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks, NOT created here)
```

### Source Code (repository root)

```text
register/
└── derive_register.py       # EDIT: photo gate on the vibe promotion (step 2), marketing
                             #   keyword row in USAGE_RULES, playful-tone retention for
                             #   marketing + playful vibe (step 4), trace entries for both

harness/
└── conductor.py             # EDIT: build_subfields(inputs, thin=False) adds the raw
                             #   render_style key ONLY on the thin route;
                             #   write_glue_artifacts passes its existing thin flag through

test_register_render_aware.py  # NEW: free self-test over the pure function (US1-US4,
                               #   FR-007 no-regression, normalizer drift guard)

CLAUDE.md / SYSTEM_MAP.md      # EDIT: same-commit currency (constitution VII)
```

**Structure Decision**: no new modules, no new directories. The register engine already owns the
inference and its trace; the conductor already owns subfields assembly and already knows `thin`.
The feature threads one field and edits one rule table, which is why the whole change stays inside
the two existing files plus one new test.

**Explicitly NOT touched** (FR-008): `harness/scene_author.py` (the 009 opener matrix and
`ASSET_PROFILES` consume the register profile unchanged), `harness/kit.py`, the legacy
render-and-scrub path, `frontend/` (the form already captures `render_style` since 009).

## Complexity Tracking

No constitution violations. Table intentionally empty.
