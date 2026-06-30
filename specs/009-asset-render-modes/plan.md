# Implementation Plan: Beyond Flat-vector Event Signs (Render Modes)

**Branch**: spec dir `009-asset-render-modes`; work continues on the existing `006-web-onboarding-gate` git branch by deliberate reuse (as with 007/008) | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-asset-render-modes/spec.md`

## Summary

The tool only ever renders flat-vector die-cut event signs: the conductor hard-wires
`ASSET_PROFILE = "flat_graphic"` (`conductor.py:62`) and the thin opener hard-codes "hand-held event sign"
in both flat branches (`scene_author.py:866-878`). This feature lets the TASK drive the render mode and
framing on the thin route: the designer EXPLICITLY picks a `render_style` (flat vector / photographic), the
conductor maps it to the engine's `asset_profile` and stops hard-wiring flat, and `assemble_thin_prompt`
becomes (asset_profile x register)-aware so a photographic poster and a flat rectangular flyer are possible,
not just a die-cut sign. Brand still governs color/font/logo HARD; the task governs render style + shape
SOFT (constitution §VI). The bones already exist (both dialects in `ASSET_PROFILES`, the `--asset-profile`
flag, chroma auto-off for non-flat, `run_thin_mode` already forwarding `args.asset_profile`), so this is a
small, localized change.

The three deferred decisions are RESOLVED here, grounded in the code:

1. **Carrier + mapping**: `render_style` is carried VERBATIM by `inputs_writer` into the inputs JSON (the
   frontend speaks the user term). The conductor maps it to `asset_profile` at the engine boundary via a new
   `normalize_render_style` helper (mirrors `normalize_dial`), threaded into `_scene_author_thin_argv` (a new
   `asset_profile` param) so the thin argv carries `--asset-profile photo|flat_graphic` instead of the
   constant. `inputs_writer` stays a pure pass-through; the conductor owns the user-term -> internal-dialect
   translation (the single place that builds the scene_author argv and owns ASSET_PROFILE).
2. **Opener wording** (register-aware; proposed verbatim below, for your sign-off like the 008 role wording):
   the flat + event_prop branch is BYTE-UNCHANGED (regression); the flat + marketing/formal branch is
   rewritten to a rectangular poster (drops "hand-held event sign"); two NEW photographic branches
   (event_prop prop / marketing poster). v1 uses generic register-derived nouns, NOT the free-text
   `asset_type` (deferred: avoids extra plumbing + the gpt-paints-asset_type risk).
3. **Negatives regrouping**: split the bundled negatives into render-AGNOSTIC text guards (no gibberish / no
   extra Chinese / no tagline / no watermark) that apply in BOTH modes, and a flat-only render clause
   (no photographic shading, no 3D realism). The flat NEGATIVES line stays byte-identical (regression).

Scope is the thin route only (reference job: chroma off, deliverable final.png, no measure/composite); the
kit / tier-3 / no-reference-cutout / legacy paths are untouched.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`). Prompt assembly is stdlib string-building; the live-runner
control is vanilla JS.

**Primary Dependencies**: none new. Touches `harness/scene_author.py` (thin opener + negatives),
`harness/conductor.py` (render_style -> asset_profile + thin argv + manifest), `frontend/inputs_writer.py`
(carry render_style), `frontend/index.html` (the render-style control).

**Storage**: None new. The brief gains a `render_style` field; the run manifest records render_style +
the resolved asset_profile.

**Testing**: Falsifiable STRUCTURAL self-tests (`test_*.py`, stdlib) over the assembled prompt STRING + the
`build_plan` thin argv + the inputs round-trip. NO paid model calls. SC-007 (the output actually looks
photographic) is the LOAD-BEARING human eye-gate, NOT automatable.

**Target Platform**: Localhost web app + CLI on the designer's machine (same as 004-008).

**Project Type**: Single project; a localized change to the thin prompt + the conductor mapping + the
live-runner control.

**Performance Goals**: N/A (string assembly + a dict lookup).

**Constraints**: thin route ONLY (kit/tier-3/no-ref/cutout/measure-composite UNCHANGED). Agent-free: the
human picks render style; no classifier (§I). GENERALIZES (driven by render_style + register, no one-image
tuning, §IV). Reconciliation per-dimension: brand HARD, task SOFT (§VI). Honest-null: unrecognized
render_style -> flat vector, recorded (§V). The flat event-sign path is byte-unchanged (regression). No
em-dashes in NEW user-facing text (the existing event_prop opener keeps its pre-existing em-dash to preserve
byte-identity; flagged as pre-existing debt).

**Scale/Scope**: v1 = the render-style control + the conductor mapping + the opener/negatives generalization
on the thin route. No kit/legacy/no-ref change, no asset_type-driven specificity.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The designer EXPLICITLY picks the render style at the input gate; no model classifies asset_type. The human stays at the input + taste gates. | PASS |
| II. Ground truth = the eye | SC-007 is the LOAD-BEARING human eye-gate (does the output actually look photographic). Tests assert the prompt STRING / argv only; no VLM PASS counts. | PASS |
| III. Falsifiable tests only | photo prompt has photographic language and NOT "FLAT VECTOR"/"no photographic shading" but keeps the text guards; flat-marketing opener drops "hand-held event sign"; flat event_prop byte-unchanged; build_plan thin argv carries the brief's asset_profile not the constant; inputs round-trips render_style. Each fails a wrong build on a VALUE. | PASS |
| IV. Generalize, do not hand-tune | The opener/negatives logic is task-general (driven by asset_profile + register); no one-image tuning. | PASS |
| V. Honest nulls, never invented | Unrecognized / omitted render_style -> flat vector fallback, recorded in the manifest; no silent mode guess. | PASS |
| VI. Reconciliation per-dimension | Brand still governs color/font/logo HARD; the TASK governs render style + shape SOFT (register-derived). The split is preserved, not collapsed. | PASS |
| VII. Repo is durable; thin / reuse | Stdlib only; reuses the existing dialects + `--asset-profile` flag + `run_thin_mode`; one mapping helper; thin-route-only; one-module-one-test-one-commit; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid model calls in any automated test. The one paid sign is the human eye-gate
(SC-007), genuinely load-bearing here, run after the build. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/009-asset-render-modes/
├── spec.md              # Feature spec (clarified 2026-06-30: photo any-register + render_style carrier)
├── plan.md              # This file
├── research.md          # Phase 0: the 3 decisions (carrier/mapping, opener wording, negatives split)
├── data-model.md        # Phase 1: render_style -> asset_profile, the opener matrix, the negatives split
├── contracts/
│   ├── render-style-contract.md   # the render_style field + normalize_render_style + the thin argv
│   └── thin-opener-contract.md    # the (asset_profile x register) opener matrix + negatives + verbatim text
├── quickstart.md        # Phase 1: free structural validation + the LOAD-BEARING eye-gate
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # CHANGED: add a Render style control (flat vector / photographic), default flat
│                         #   vector; include it in the posted form state. No em-dashes.
└── inputs_writer.py     # CHANGED: carry `render_style` VERBATIM into the inputs JSON (default "flat
                         #   vector"); pure pass-through, no mapping here. Other fields unchanged.

harness/
├── conductor.py         # CHANGED: NEW normalize_render_style(value) -> asset_profile (photo|flat_graphic,
│                         #   fallback flat_graphic); build_plan reads inputs.render_style and threads the
│                         #   mapped profile into _scene_author_thin_argv (new asset_profile param,
│                         #   defaulting to ASSET_PROFILE for back-compat); record render_style + resolved
│                         #   asset_profile in the manifest; update the thin-path "ALWAYS flat_graphic" notes.
│                         #   Kit/legacy/no-ref argv builders (:188/:219) UNCHANGED.
└── scene_author.py      # CHANGED: assemble_thin_prompt opener becomes (asset_profile x register)-aware -
                         #   flat+event_prop UNCHANGED (byte-identical); flat+marketing rewritten to a
                         #   rectangular poster (no "hand-held event sign", no em-dash); NEW photo+event_prop
                         #   and photo+marketing openers; split the negatives (render-agnostic text guards
                         #   always; flat-only render negatives only for is_graphic, byte-identical for flat).

test_render_modes.py     # NEW: falsifiable structural self-test (no paid calls). photo dialect (no FLAT
                         #   VECTOR / no "no photographic shading", keeps text guards); flat-marketing opener
                         #   drops "hand-held event sign"; flat event_prop byte-unchanged; normalize_render_style
                         #   mapping + fallback; build_plan thin argv carries --asset-profile from the brief;
                         #   inputs_writer round-trips render_style; index.html has the control (grep).
```

**Structure Decision**: The change is localized: one mapping helper in the conductor (`normalize_render_style`,
mirroring `normalize_dial`) translating the user term to the engine `asset_profile` at the single thin-argv
site (`_scene_author_thin_argv`), and a (asset_profile x register) restructure of `assemble_thin_prompt`'s
opener + a negatives split. `inputs_writer` carries `render_style` verbatim (user vocabulary at the frontend
boundary; the conductor translates). The flat event_prop opener and the flat NEGATIVES line are kept
byte-identical so the proven event-sign path does not regress (FR-007 / SC-005); only the flat-marketing
opener (already mislabeled today) changes, plus the two new photo branches. Nothing in the kit / tier-3 /
no-reference / legacy paths, the chroma/measure/composite pipeline, or the conductor input contract (beyond
adding the `render_style` carrier) changes (FR-009).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
