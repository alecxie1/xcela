# SPEC BRIEF for /speckit-specify — Feature 003: Thin-spine prompt-compose route

Paste the body below as the /speckit-specify description (or point Claude Code at this file).

---

## Problem / why
The faithful 6-sign paid run (SYSTEM_MAP 2026-06-24 PM regroup) proved by the human eye that the
KIT COMPOSITION layer makes output WORSE on a real brief: it produced 2 good signs, 3 near-duplicates
(s3/s5/s6 all the same archetype+icon), 1 blank honest-null. Raw gpt-image-2 on the SAME brief
produced 6 varied on-brief signs in one shot. Decision: CUT the composition layer, let gpt-image-2
compose the whole sign from one assembled prompt. This feature builds that thin route.

## Goal (interim milestone — READ THIS, it scopes "done")
PROVE THE THIN SPINE END-TO-END, agent-free. This is NOT shipping the product. The licensed-font
MOAT is deliberately DEFERRED (separate later spec). The interim deliverable is the RAW
`generated.png` (gpt-painted text, a KNOWN-TEMPORARY debt). "Done" = the agent-free spine runs from
one CLI command and each stage is visible/inspectable. Do NOT re-bundle the moat, the kit, or any
composition logic into this feature.

## Verified codebase state (STEP ZERO — confirm before building)
- `harness/conductor.py build_plan()` already routes on `kit_mode = kitlib.kit_exists(brand)`. The
  kit route (compose_select → kit.py → scene_author --kit-profile) is what we are RETIRING as default.
- `harness/scene_author.py` ALREADY has the exact shape we want in its reference-job path
  (~L1187-1238): `final_prompt = <a prompt>` → `generate_variant(final_prompt, refs, out_png,
  size=...)` → `generated.png`, with NO tier-3 authoring and NO post-processing required. The thin
  route is essentially this path fed by a NEW prompt assembler and STOPPED at generated.png.
- `harness/format_size.py` (002) already resolves `--size`. `harness/prompt_elements.py` (002)
  already builds the verbatim mandatory/forbidden clause. REUSE both; do not reinvent.
- `generate_variant` already accepts `size` and a list of reference images ([logo, ref]).

## The change (smallest viable)
1. NEW prompt assembler (call it `assemble_thin_prompt`) in scene_author.py (or a small stdlib
   module): builds ONE generation prompt directly from the brief, NO kit, NO tier-3, NO compose_select:
   - the per-sign messages VERBATIM (exact headline text, the model paints it for now),
   - the campaign + per-sign `mandatory_elements` / `forbidden_elements` via `prompt_elements`
     (so 分别画叉 reaches the prompt),
   - the answer_key palette hex + logo treatment + any VI hint as STYLE guidance,
   - the register/dial hint (KEEP the dial — it sets task-vs-brand magnitude; this task reads
     "expressive departure / task-governs", a corporate asset would read the other way),
   - the reference image fed to gpt as a visual exemplar (ref+prompt is designed-in).
2. NEW scene_author mode `--thin` (or `run_thin_mode`): assemble_thin_prompt → generate_variant
   (with the 002-resolved `--size`) → STOP at `generated.png`. No measure, no composite, no scrub,
   no kit_profile, no composition.json. `--explain` prints the prompt source + mode and exits.
3. conductor routing: a brand with a kit currently auto-takes the kit route. Add a way to take the
   THIN route as the DEFAULT for flat_graphic jobs (e.g. a `--thin` conductor flag, or make thin the
   default and keep kit behind an opt-in flag). The plan/dry-run must show the thin steps:
   register/dial → assemble_thin_prompt → generate → (gate). NO compose_select / kit / measure steps.
4. Manifest: record `route: "thin"`, the assembled prompt path, the size_resolution (002), the
   verbatim mandatory/forbidden elements, and an explicit `licensed_type: "deferred (raw gpt text)"`
   honest-null marker so the moat gap is TRACKED, not silent.

## Keep / cut / defer (bind to SYSTEM_MAP 6/24 PM)
- KEEP active: intake(002), register/dial, answer_key locks, logo→gpt, human approve/nudge gate,
  manifest, format_size + prompt_elements.
- CUT from the default path: compose_select, kit layout archetypes, reserve-box zones, fit-to-zone
  clamp. (Leave the kit CODE in the repo behind an opt-in flag; do not delete files this feature —
  just stop selecting them by default. A later spec may remove them.)
- DEFER (do NOT build here): the licensed-font moat (resolve_font/composite_text/furniture+typeset).

## Falsifiable tests (constitution §III — assert VALUES a wrong build can't satisfy; NO paid calls)
- A dry-run of the faithful 6-sign brief (`inputs_lily_aia.json`) on the thin route emits a plan whose
  steps are register/dial → assemble_thin_prompt → generate per sign, and contains NO compose_select,
  NO kit, NO measure, NO composite step. (The current default would show kit steps — this asserts the
  route actually changed.)
- `assemble_thin_prompt` output for a sign CONTAINS the exact verbatim headline string(s) and, for
  s5/s6, the exact string 分别画叉 (byte-for-byte equality, not a paraphrase).
- The thin route produces `generated.png` and NO composition.json / kit_profile.json / final.png
  (asserts the post-processing is genuinely skipped, not just renamed).
- Manifest records `route:"thin"` and `licensed_type:"deferred"` (the tracked-debt honest null).
- Standalone: conductor runs the thin route end-to-end from ONE CLI command with no kit files needed.
- Run the FULL existing suite (002 tests must stay green — back-compat).

## Hard rules
- NO image generation / paid calls in any test (cost discipline). Build on dry-run/--explain.
- NO background processes / poll loops in the build. Foreground blocking only. `.venv/bin/python`.
- Stdlib-only in conductor + prompt assembler (no new deps).
- Honest reporting: real test output from disk; if something fails, say so.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (constitution §VII).

## Definition of done
- Thin route builds + all tests green (paste real output).
- Dry-run of inputs_lily_aia.json shows thin steps only (paste the step list).
- One commit on a 003 feature setup, clear message.
- Report: files changed, the route-selection mechanism, test output, the dry-run step list.
- The ONE paid run (6 signs, thin route) is the human's eye-gate AFTER the build — NOT in the build.
