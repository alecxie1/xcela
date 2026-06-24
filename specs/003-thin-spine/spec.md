# Feature Specification: Thin-spine prompt-compose route

**Feature Branch**: `002-faithful-brief-intake` (003 work; see commit) / future `003-thin-spine`

**Created**: 2026-06-24

**Status**: BUILT (interim milestone) — structurally green; the ONE paid 6-sign eye-gate is the
human's action AFTER the build (NOT in the build).

**Input**: `specs/_inbox/003-thin-spine.md` (code-grounded brief). Bound to the SYSTEM_MAP
2026-06-24 PM regroup keep/cut/defer decision.

## Problem / why

The faithful 6-sign paid run (`output/run_aia_20260624_104106/`) gave the first un-confounded
verdict by Alec's eye: on Lily's real anti-fraud brief the KIT COMPOSITION layer produced 2 good
signs, 3 near-duplicates (s3/s5/s6 all `resist_panel` + `megaphone_x`), and 1 blank honest-null
(s4, no icon match). Raw gpt-image-2 on the SAME brief produced 6 varied on-brief signs in ONE
shot. The bitter lesson, on our own task: the deterministic composition layer COMPETES with the
model and LOSES — it constrains gpt-image-2 down to its own threadbare vocabulary. It is not
neutral; it makes output WORSE on the real distribution of briefs.

Decision: CUT the composition layer from the default path; let gpt-image-2 compose the whole sign
from one assembled prompt. This feature builds that thin route.

## Goal (interim milestone — this scopes "done")

PROVE THE THIN SPINE END-TO-END, agent-free. This is NOT shipping the product. The licensed-font
MOAT is deliberately DEFERRED (separate later spec). The interim deliverable is the RAW
`generated.png` (gpt-painted text, a KNOWN-TEMPORARY debt). "Done" = the agent-free spine runs from
one CLI command and each stage is visible/inspectable. Do NOT re-bundle the moat, the kit, or any
composition logic into this feature.

## Keep / cut / defer (binds to SYSTEM_MAP 2026-06-24 PM)

- **KEEP active**: intake (002), register/dial, answer_key brand locks (color/font/logo), logo→gpt,
  the human approve/nudge gate, the manifest, `harness/format_size.py` + `harness/prompt_elements.py`.
- **CUT from the DEFAULT path (not deleted)**: `compose_select`, kit layout archetypes, reserve-box
  icon_zone/text_zone, fit-to-zone clamp. The kit CODE stays in the repo behind an opt-in; this
  feature just stops selecting it by default. A later spec may remove it.
- **DEFER (NOT built here)**: the licensed-font moat (`resolve_font` / `composite_text` /
  furniture + deterministic typeset). Tracked as an explicit `licensed_type: "deferred (raw gpt
  text)"` honest-null marker so the moat gap is visible, not silent.

## Clarifications

### Session 2026-06-24

- Q: Route-selection mechanism — make thin the default, or opt-in? → A: **Opt-in `--thin`
  conductor flag** (one of the two mechanisms the brief explicitly offers). The decisive
  back-compat hard rule ("the existing 002 suite must stay green") forbids flipping the global
  default this commit: `test_conductor` checks 2 + 3 assert the kit route for AIA. `--thin` lets
  the thin route be the route for any flat_graphic job today, keeps every existing test green, and
  leaves flipping the default (with the kit tests migrated behind `--kit`) to a follow-up. The
  thin route is the chosen path for the interim paid run.
- Q: Does the thin route use the reference via the analyzer (compose_select / aligned-prompt)? →
  A: No. The reference image is fed to gpt-image-2 as a visual exemplar (ref + prompt, designed-in)
  and still sets register MAGNITUDE via `calibrate_from_reference`, but there is NO analyzer /
  aligned-prompt clone step on the thin route (that is the legacy path).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thin route composes the whole sign from one prompt (Priority: P1)

A non-designer's faithful brief (intake 002) is turned into ONE assembled generation prompt per
sign — verbatim headline text + verbatim mandatory/forbidden elements + answer-key palette/logo
locks + the register/dial hint + (optionally) a fed reference exemplar — and gpt-image-2 composes
the whole sign. The pipeline STOPS at `generated.png`. No kit, no tier-3, no compose_select, no
measure, no composite.

**Falsifiable tests** (assert VALUES; NO paid/image calls):
- `assemble_thin_prompt` output for a sign CONTAINS the exact verbatim headline string(s); for
  s5/s6 it CONTAINS the exact string `分别画叉` (byte-for-byte, not a paraphrase).
- `scene_author --thin --explain` reports `route:"thin"`, `generation_prompt_source:
  "assemble_thin_prompt"`, `uses_tier3:false`, `uses_kit:false`, `composite:"none"`,
  `measure:false`, `licensed_type:"deferred (raw gpt text)"` — and EXITS before any model call.

### User Story 2 - Conductor routes flat_graphic jobs through the thin spine (Priority: P1)

With `--thin`, the conductor routes a flat_graphic job (even a brand that HAS a kit) through the
thin spine: register/dial prep → per-sign `scene_author --thin` (assemble_thin_prompt → generate
→ stop). The plan/dry-run shows the thin steps and contains NO `compose_select` / kit / measure /
composite step.

**Falsifiable tests**:
- A `--dry-run --thin` of `inputs_lily_aia.json` emits a plan whose steps are register (calibrate +
  derive_register) then one `scene_author --thin` per sign, with NO `kit` step, NO `analyzer` step,
  and no `--kit-profile` / `--composition` / `--aligned-prompt` in any scene_author argv. The
  per-sign argv for s5/s6 carries `--mandatory-elements 分别画叉`; s1–s4 do not. (The default route
  for AIA would show kit steps — this asserts the route actually changed.)
- Without `--thin`, AIA still takes the kit route (compositions present) — proving `--thin` is what
  changed the route (back-compat).
- Standalone: a brand with NO kit, run with `--thin`, still produces a thin plan (no kit files
  needed) from ONE CLI command.

### User Story 3 - Tracked-debt manifest (Priority: P2)

The run records `route:"thin"`, the assembled prompt path, the verbatim mandatory/forbidden
elements, the size resolution (002), and `licensed_type:"deferred (raw gpt text)"` so the moat gap
is TRACKED, not silent.

## Requirements *(mandatory)*

- **FR-001**: A new `assemble_thin_prompt` (stdlib, in `harness/scene_author.py`) builds ONE
  generation prompt directly from the brief: verbatim messages, verbatim mandatory/forbidden via
  `prompt_elements.elements_clause`, answer-key palette hex + logo treatment + slogan hint, the
  register/dial directive (reusing the existing `_register_directive` / dial), and a fed-reference
  note. No kit, no tier-3, no compose_select.
- **FR-002**: A new `scene_author --thin` mode (`run_thin_mode`): assemble_thin_prompt →
  `generate_variant` (with the 002-resolved `--size`) → STOP at `generated.png`. No measure, no
  composite, no kit_profile, no composition.json. `--explain` prints the prompt source + mode +
  route + licensed_type and exits before any model call.
- **FR-003**: Conductor `--thin` routing: a flat_graphic job takes the thin route. The plan shows
  register/dial → per-sign `scene_author --thin`; NO compose_select / kit / measure / composite.
- **FR-004**: Manifest records `route:"thin"`, the assembled prompt path, `size_resolution` (002),
  verbatim mandatory/forbidden, and `licensed_type:"deferred (raw gpt text)"`.
- **FR-005**: REUSE `harness/format_size.py` (size) and `harness/prompt_elements.py` (verbatim
  elements). Do not reinvent.
- **FR-006**: Do NOT delete the kit code; just stop selecting it by default (it stays behind the
  absence of `--thin`).
- **FR-007**: Stdlib-only in conductor + the prompt assembler (no new deps). No image generation /
  paid calls in any test. No background processes / poll loops.

## Success Criteria *(mandatory)*

- **SC-001**: Thin route builds; the full existing self-test suite stays green (002 back-compat).
- **SC-002**: `--dry-run --thin` of `inputs_lily_aia.json` shows thin steps only (no kit/compose/
  measure/composite).
- **SC-003** (human, AFTER the build): the ONE paid 6-sign thin-route run, judged by Alec's eye, is
  the eye-gate. NOT part of this build.
