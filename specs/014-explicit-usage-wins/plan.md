# Implementation Plan: Explicit Usage Wins Over the Vibe Guess

**Branch**: `014-explicit-usage-wins` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-explicit-usage-wins/spec.md`

## Summary

One condition in one branch. `derive_register`'s usage-rule loop starts remembering WHICH row
produced the base (it already remembers the keyword for the trace); the playful-vibe
marketing-to-event_prop promotion then declines to fire when the base came from the
marketing-keywords row ("marketing", "social", "instagram", "promotional"), appending one trace
line naming the matched keyword. The photo gate (011) is checked FIRST, which keeps every
existing photo-lane trace byte-identical and satisfies the exactly-one-suppression-entry rule
(FR-006) by construction. Bases from every other row (wall-posted, the sign-era phrases) and the
unmatched default keep their promotion byte-identically; tone retention needs zero change (it
keys on register+vibe). One new self-test file in the 011 pattern.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`); `register/derive_register.py` stays stdlib-pure

**Primary Dependencies**: none

**Storage**: register_profile.json (value-level deltas only, no schema change)

**Testing**: new standalone `test_explicit_usage_wins.py`, pure-function imports of
`derive_register` (no subprocess, no paid calls); reuses the pre-feature baseline literal
already inlined in `test_register_render_aware.py` (same fixture, still current output)

**Target Platform**: local Linux/WSL2 CLI

**Project Type**: CLI pipeline (this feature: one engine module)

**Performance Goals**: N/A (rule-table inference)

**Constraints**: wall-posted + playful flat profile byte-identical to the existing baseline
literal; unmatched-default promotion unchanged; all existing register-suite checks that touch
this branch stay green untouched (verified: the 011 suite's check7 asserts only the match trace
and precedence, not the final register, so it survives the fix)

**Scale/Scope**: 1 module edited (~12 lines), 1 new self-test, 0 other files

## Constitution Check

*GATE: evaluated pre-Phase-0, re-checked post-Phase-1. All PASS.*

| Principle | Verdict | How |
|---|---|---|
| I. Agent-free, not human-free | PASS | The whole feature: a machine guess (vibe heuristic) stops overriding a human statement (an explicitly matched usage phrase). Same principle 011 applied to the photo lane. |
| II. Eye is ground truth | PASS | The fix's only pixel-facing effect is the register value, fully visible in the free trace; SC-005 defines the cheap eye path (free trace check + the next natural flat run). |
| III. Falsifiable tests | PASS | An unfixed build yields `event_prop` for flat+social+playful (fails the new check); an over-suppressing build breaks the wall-posted byte-identity literal or the unmatched-default promotion; a double-trace build fails the exactly-one-entry count. |
| IV. Generalize | PASS | Keys on the rule row, not on any brand, phrase instance, or image. |
| V. Honest nulls | PASS | The suppression is traced by name; untouched paths gain zero trace lines (byte-identity). |
| VI. Reconciliation per-dimension | PASS | Task keeps governing register direction; the change only corrects WHOSE signal sets it (human phrase over vibe guess). Tone retention (vibe-driven) untouched. |
| VII. Repo durable context | PASS | CLAUDE.md + SYSTEM_MAP in the closing commit. |
| Cost discipline | PASS | All tests free; no dedicated paid run required (SC-005's cheap path). |
| Output rule | PASS | The new trace line uses no em-dashes. |

## Project Structure

### Documentation (this feature)

```text
specs/014-explicit-usage-wins/
├── plan.md              # This file
├── research.md          # Phase 0 (3 decisions)
├── data-model.md        # Phase 1 (trace + rule-table deltas)
├── quickstart.md        # Phase 1 (free validation + the cheap eye path)
├── contracts/
│   └── explicit_usage_contract.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
register/derive_register.py   # EDIT: name the marketing row as MARKETING_USAGE_KEYWORDS (used
                              #   in USAGE_RULES); the match loop records the matched row +
                              #   keyword; the promotion branch gains ONE elif between the 011
                              #   photo gate and the promotion (suppress + trace when the base
                              #   row is the marketing row)
test_explicit_usage_wins.py   # NEW free self-test (see contract)
CLAUDE.md / SYSTEM_MAP.md     # EDIT: currency in the closing commit
```

**Structure Decision**: the engine already owns the rule table, the trace, and both prior gates;
the fix is ~12 lines inside it. No plumbing changes anywhere (render_style etc. already arrive
in subfields).

**Explicitly NOT touched** (FR-007): `harness/conductor.py`, `harness/scene_author.py`, the 009
openers, `register/calibrate_from_reference.py`, kit/legacy, `frontend/`.

## Complexity Tracking

No constitution violations. Empty.
