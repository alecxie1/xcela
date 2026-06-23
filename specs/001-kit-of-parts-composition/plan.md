# Implementation Plan: Kit of Parts + Bespoke Per-Message Composition

**Branch**: `001-kit-of-parts-composition` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-kit-of-parts-composition/spec.md`

## Summary

Replace the "ONE TEMPLATE, N TEXTS" frame (render-and-scrub + dial=`extend`, which clones one
aligned prompt behind every message) with how a human designer actually works: lock a KIT OF
PARTS once per campaign, then compose each sign bespoke from its message.

Technical approach (grounded in the existing code, which already has the load-bearing pieces):
the kit is split into an AUTHORED layer (a per-brand `kits/<brand>.json` holding a meaning→icon
vocabulary and a layout-archetype vocabulary, both human-authored brand DATA) and a DERIVED
layer (palette, font role, frame treatment pulled from `answer_keys/<brand>.json` +
`register_profile` + reference calibration, with the answer key winning every conflict). Per
message the tool (1) deterministically matches the message meaning to an icon-vocabulary entry,
(2) deterministically selects a distinct layout archetype (collision-avoiding), (3) takes the
archetype's reserved text zone, (4) fits the licensed headline INTO that zone with margin via a
new fit-to-zone clamp, and (5) builds a generation prompt that paints background + the chosen
icon in its zone and keeps the text zone CLEAR. The licensed headline is then composited into
the cleared zone. This eliminates the scrub step (text zone is never painted, so no ghost text
to erase and no icon damage), fixes oversize text (fit-to-zone clamp), and makes signs distinct
(per-message icon + archetype). The human stays at the input gate (authors the kit, supplies
messages + reference) and the taste gate (approves/overrides each icon and layout proposal).

The reframe ROUTES family jobs through kit composition; it reuses `register/` (reconciliation),
`composite_text` (licensed font + compliance manifest), `scene_author`'s reservation concept,
and `measure_canvas` (verification), and adds three genuinely new capabilities: the kit data
layer, the deterministic icon/layout selectors, and the fit-to-zone clamp.

## Technical Context

**Language/Version**: Python 3.11 (run as `.venv/bin/python`; deps via `uv pip install --python .venv/bin/python`)

**Primary Dependencies**: anthropic (authoring/vision: claude-opus-4-5 → claude-sonnet-4-6), openai (gpt-image-2 generation), Pillow (compositing), RapidOCR + numpy (measure verification), PyYAML (config), python-dotenv (keys from `~/.hermes/.env`)

**Storage**: Files only. Brand data as JSON/YAML (`answer_keys/`, `config/`, new `kits/`); per-run artifacts + PNGs under `output/run_*/sign_*/` (gitignored).

**Testing**: Falsifiable STRUCTURAL self-tests in the existing `test_*.py` style (plain `.venv/bin/python` scripts, no pytest dependency), plus `--dry-run` / `--explain` free surfaces. NO paid image generation inside any test (constitution cost discipline). Pixel quality is validated ONLY by the human eye on a real `output/` file.

**Target Platform**: Linux CLI pipeline (WSL2), stdlib-orchestrated subprocess tree rooted at `harness/conductor.py`.

**Project Type**: Single project (CLI image-design pipeline). No frontend/backend split.

**Performance Goals**: Not latency-bound. Cost-bound: gpt-image-2 is the expensive, slow step. One paid generation per sign; selection/fit/compose steps are deterministic and free. Campaign N is small (a handful of signs).

**Constraints**: No paid generation in tests. Honest nulls + needs_review on every step that can fail. Human approve/nudge gate preserved. Licensed-font compliance manifest preserved. No em-dashes in user-facing text. No AIA-specific literals in shared/brand-general code (AIA specifics live in `kits/aia.json` / `answer_keys/aia.json`).

**Scale/Scope**: v1 is the AIA flat-graphic event-sign task only. Brand-generality is designed-in (per-brand data, no literals in code) but proven later. 2-sign AIA set is the primary ground-truth case.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The kit is human-AUTHORED (input gate); every per-message icon + layout choice is a PROPOSAL surfaced at the existing approve/nudge gate (taste gate). No step walks away. | PASS |
| II. Ground truth = the eye | All SC-001..005 are human-eye judgments on real output files. Automated tests assert STRUCTURE only (distinct icon/archetype chosen, a reserved zone exists, type fits the zone in pixels). No VLM self-score counts as proof. | PASS |
| III. Falsifiable tests only | Each new module ships a test that asserts a VALUE a wrong build fails (e.g. 钱袋子 → money-bag entry; two distinct-mode messages → two distinct archetypes; a long headline's fitted size_px is strictly smaller and its rendered box fits the zone with margin). No token-presence gates. | PASS |
| IV. Generalize, do not hand-tune | Icon/layout vocabularies live in `kits/<brand>.json` (DATA). Selectors, fit clamp, and routing are brand-general code with zero AIA literals. The kit is the per-brand knob, not the code. | PASS |
| V. Honest nulls | No icon match → null + needs_review (human picks). Type can't fit at min size → null + needs_review. Layout vocabulary exhausted → reuse + flag needs_review. Every fallback recorded in the manifest. | PASS |
| VI. Reconciliation per-dimension | Kit derivation reuses `derive_register` (DIRECTION) + `calibrate_from_reference` (MAGNITUDE). Answer key governs HARD locks (color, fonts, logo); reference feeds SOFT dimensions; answer key wins every conflict (clarified). | PASS |
| VII. Repo is durable context | Decomposed into one-module-one-test-one-commit tasks (see Project Structure). CLAUDE.md + SYSTEM_MAP updated in the commit that makes them stale. | PASS |

**Cost discipline**: All structure verified on `--dry-run` / `--explain` / self-tests first; one paid `conductor.py` run judged by eye only when structure is green. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-kit-of-parts-composition/
├── spec.md              # Feature spec (clarified 2026-06-22)
├── plan.md              # This file
├── research.md          # Phase 0 output: key technical decisions
├── data-model.md        # Phase 1 output: kit + composition entities
├── quickstart.md        # Phase 1 output: dry-run + paid validation guide
├── contracts/           # Phase 1 output: data + CLI contracts
│   ├── kit-schema.md            # kits/<brand>.json authored-vocabulary schema
│   ├── kit-profile-schema.md    # derived runtime kit_profile.json
│   ├── composition-schema.md    # per-sign composition.json
│   └── cli-contract.md          # conductor/scene_author flag + routing changes
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
harness/
├── conductor.py             # CHANGED: route family jobs through the kit path; surface
│                            #   icon/layout proposals at the approve gate; record needs_review
├── scene_author.py          # CHANGED: reserve-box composition driven by the chosen archetype
│                            #   (icon zone + clear text zone), not free Anthropic authoring
├── composite_text.py        # REUSED + EXTENDED: fit-to-zone type clamp before compositing
├── measure_canvas.py        # REUSED: verify text fits zone / zones don't collide (structural)
├── kit.py                   # NEW: load + validate kits/<brand>.json; derive runtime kit_profile
│                            #   (answer key wins conflicts); reuse register/ for soft dims
└── compose_select.py        # NEW: deterministic meaning→mode→icon match (honest-null on miss)
                             #   + collision-avoiding layout-archetype selection (reuse+flag)

register/                    # REUSED unchanged: derive_register, calibrate_from_reference,
                             #   reference_style_to_prompt (kit derivation calls these)

kits/
└── aia.json                 # NEW (DATA): AIA icon vocabulary + layout-archetype vocabulary,
                             #   human-authored; the ONLY place AIA composition literals live

answer_keys/aia.json         # REUSED: brand DNA (palette, typography.styles, logo) — wins conflicts
config/aia.yaml              # REUSED: thin per-brand harness config

test_kit.py                  # NEW: kit load/validate + answer-key-wins-conflict assertions
test_compose_select.py       # NEW: meaning→icon + distinct-archetype + honest-null assertions
test_fit_to_zone.py          # NEW: long headline scales down; impossible → null assertions
test_conductor.py            # CHANGED: dry-run plan shows kit path + distinct archetypes
```

**Structure Decision**: Single project, extending the existing stdlib-orchestrated `harness/`
subprocess tree. Two NEW modules (`harness/kit.py`, `harness/compose_select.py`) and one NEW
data file (`kits/aia.json`) carry the genuinely new capability; `composite_text.py` gains the
fit-to-zone clamp; `conductor.py` + `scene_author.py` are re-routed. `register/` is reused as-is.
This honors FR-008 (no AIA literals in code) by isolating all AIA composition specifics in
`kits/aia.json`, and the constitution's one-module-one-test-one-commit rule by keeping each new
capability in its own module with its own falsifiable test.

## Complexity Tracking

> No constitution violations. Section intentionally empty.
