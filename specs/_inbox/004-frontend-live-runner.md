# SPEC BRIEF for /speckit-specify — Feature 004: Frontend live-runner (single-sign)

Paste the body below as the /speckit-specify description (or point Claude Code at this file).
This file is the DECISION MAP. Every fork was argued and resolved with Alec (2026-06-24 PM, after
the thin-route prompt-fix re-run verified clean by his eye). Alec drives /speckit-specify himself;
this is the substrate so the spec fills a known shape, not rediscovers forks.

---

## Problem / why
The thin spine (feature 003) is built and validated by the human eye: the post-prompt-fix re-run
(`output/run_aia_20260624_142340/`, route=thin) produced 6 distinct on-brief signs, zero dupes, zero
blanks, no hallucinated tagline, 分别画叉 rendered as X marks not literal characters. The pipeline now
runs agent-free from one CLI command. What is missing is a way for Alec to DRIVE it himself without
hand-editing JSON and reading a terminal: type a brief into a form, watch the thin spine execute stage
by stage, judge the sign, and nudge-rerun if needed. This feature builds that frontend.

## Goal (scopes "done" — READ THIS)
A web frontend, THIN over the existing agent-free CLI, that runs the thin route for ONE single-sign
brief live, surfaces each stage from the run directory, and exposes the human taste gate
(approve OR nudge-rerun — two actions only). It is Alec's own test instrument first, a demo second.
"Done" = he can type a single-sign brief, press run, watch register/dial + assembled prompt +
generated.png appear, and approve or nudge, all in the browser, with the standalone CLI core unchanged.

## LOCKED decisions (do NOT relitigate these in the spec — they were argued and settled)

| Decision | Locked value | Rationale |
|---|---|---|
| Unit | ONE single-sign brief (the `signs[]` array has exactly one entry) | Zero conductor change; the honest atom of the pipeline |
| Mode | Live run is the DEFAULT (not replay) | Alec is the operator going forward, not a demo audience |
| Slice | Back half ONLY: brief -> dial -> prompt -> gpt -> sign -> gate | Brand-intake front half (upload logo/VI/refs -> analyze_brand_v3 -> answer_key) is a SEPARATE later spec |
| Input | STRUCTURED typed form (labeled fields), NOT natural-language prose | A prose->fields LLM parser is the lossy hand-translation the 002 pivot KILLED; the form keeps every field verbatim with no parser |
| Reference image | REQUIRED for v1 | This task type runs with a reference anyway; the ref-less thin path is structurally supported but its pixels are UNJUDGED, so it is DEFERRED, not offered in v1 |
| Taste gate | CORE, TWO actions only: approve (good, stop) OR nudge-rerun (give a binding note, regenerate). Reject-without-rerun is CUT (redundant: a bad single sign is nudged, not discarded). | Constitution §I (human stays at TASTE gates); a viewer that only shows finished pixels violates the thesis |
| UI posture | THIN: shells out to `conductor.py --thin`, READS the `sign_dir` artifacts, renders. NEVER reimplements generation. | Constitution §I + §VII; the standalone core must stay runnable with one command, no UI |

## Verified codebase state (STEP ZERO — confirm before building)
- `harness/conductor.py` runs the thin route via `--thin` TODAY. The single-sign case needs NO conductor
  change: the per-sign loop already processes one sign per iteration. A 1-entry `signs[]` just runs once.
- The thin route already writes the FULL trace to the run dir as it executes:
  `subfields.json` -> `calibration.json` -> `register_profile.json` -> `intent_s1.json` ->
  `sign_s1/final_prompt.txt` -> `sign_s1/generated.png` -> `conductor_manifest.json`.
  The UI is largely a RENDERER for that directory plus a trigger button. Confirm this list on disk.
- `register/derive_register.py` does NOT require a reference (falls back to `REGISTER_SLIDER_DEFAULTS`,
  the "moderated default / overshoot fix"). v1 still REQUIRES a ref by product decision, not by code limit.
- The taste-gate generation capability EXISTS: `scene_author.assemble_thin_prompt` accepts `style_notes`
  (the human's nudge becomes a binding clause). BUT the conductor's current approve loop is a terminal
  `input()` gate (`harness/approve.py` / MAX_NUDGES=5). It CANNOT be driven from a browser as-is. See
  "Open question for /speckit-plan" below — do NOT let the UI orchestrate reruns itself.

## The form fields (render the REAL contract, verbatim — this is the anti-lossy core)
Render the 002 extended conductor-inputs schema, the artifact the conductor actually consumes. The
AUTHORITATIVE contract is `specs/002-faithful-brief-intake/contracts/inputs-schema.md`.
WARNING: the repo-root `brief_schema.json` is a STALE earlier artifact with different field names
(subject / asset_type=poster|banner / mood_shift). Do NOT render that file; it will fail the
verbatim-intake test against the real conductor. Reference instance: `inputs_lily_aia.json`.

Single-sign form maps to these fields (one `signs[]` entry):
- `asset_type` (free text, e.g. "手举牌 hand-held event sign")
- `format_size` (free text, e.g. "60x40cm"; 002 `format_size.py` resolves it to a valid pixel size)
- `reference_image` (file picker — REQUIRED in v1)
- `reference_relationship` (e.g. "template — extend this series")
- `context.vibe`: `formality`, `playfulness`, `warmth` (three integer sliders 0-10 — these DRIVE the
  register branch in derive_register.py; they are NOT decorative)
- `context.logo_treatment` (enum: omit / subtle / faithful)
- `context.brand_strictness` (enum: expressive departure / ... )
- `context.occasion`, `context.usage_context`, `context.audience` (free text)
- `mandatory_elements`, `forbidden_elements` (list/chip inputs — verbatim, e.g. 分别画叉)
- the ONE sign: `messages` (the headline string(s), verbatim — gpt paints them), optional per-sign
  `mandatory_elements` / `forbidden_elements`
- brand: a DROPDOWN over existing `answer_keys/*.json` (today only `aia`). NOT a brand-upload widget —
  that is the deferred front-half spec. The form selects an existing answer_key; it does not create one.

The form WRITES a single-sign inputs JSON (002 shape) to disk and invokes the existing CLI with it.
No field is rephrased, reordered, or inferred (002 FR-003: byte-for-byte pass-through).

## Stages the UI surfaces (the payoff is the MIDDLE, not just the pixels)
This is Alec's TEST instrument: he is checking whether the dial and the assembled prompt are RIGHT,
not only whether the final sign looks good. Surface as inspectable stages, read from the run dir:
1. the brief (echoed back from the written JSON)
2. register / dial: `register_profile.json` (inferred_register, formality/playfulness, anchors_held,
   locks_flexed) — show this; it is how he catches a wrong dial
3. the assembled prompt: `sign_s1/final_prompt.txt` — show this; it is how he catches a bad prompt
   BEFORE blaming the model
4. the generated sign: `sign_s1/generated.png`
5. the taste gate: approve (good, stop) OR nudge-rerun (binding note -> regenerate). Two actions only.
Do NOT spec "show the final image only" — that blinds the test instrument to WHY a sign came out wrong.

## Live-run cost
The live-run button calls PAID gpt-image-2. Single-sign is ~$0.08 per generation (the 6-sign run was
~$0.50). Label the real per-run cost on the button; the human triggers it deliberately.

## Keep / cut / defer
- KEEP (reuse, do not reinvent): `conductor.py --thin`, the 002 intake + `format_size.py` +
  `prompt_elements.py`, register/dial, answer_key locks, the run-dir artifact contract, the manifest.
- CUT from scope: campaign/multi-sign, the grid, parallelism, the K-cap concurrency pool. (Single-sign
  deletes that whole sub-project. If a user wants 6, they run 6 single-sign briefs FOR NOW — a later
  spec handles campaigns, where register coherence across signs must be solved deliberately.)
- DEFER (explicitly out of THIS spec): brand-intake front half (upload logo/VI/refs ->
  analyze_brand_v3 -> answer_key authoring + human verify); ref-less thin runs; the licensed-font moat.

## Open question for /speckit-plan (NOT for the spec — flag, do not solve here)
The browser taste gate needs a non-interactive way to trigger a single-sign (re)run with an optional
binding style note, because the conductor's gate is a terminal `input()` loop today. The LIKELY answer
is "the conductor grows a non-interactive single-sign-plus-optional-note entry point" (a small,
agent-free CLI surface the UI calls), NOT "the UI re-implements the rerun orchestration" (that would
violate the thin posture, §I/§VII). Resolve the exact mechanism at /speckit-plan against the real
`approve.py` + `assemble_thin_prompt(style_notes=...)` code.

## Falsifiable tests (constitution §III — assert VALUES a wrong build cannot satisfy; NO paid calls)
- The form, given a filled single-sign brief, WRITES an inputs JSON whose fields equal the typed values
  BYTE-FOR-BYTE (no rephrase, no reorder, no inferred field) — assert exact string equality on
  `messages`, `mandatory_elements`, and the three vibe integers, against the 002 schema shape.
- The written JSON has exactly ONE entry in `signs[]` (single-sign invariant).
- The written JSON validates against the EXISTING `validate_inputs` (back-compat with the real
  conductor — the form cannot emit a brief the CLI would reject).
- Stage rendering reads from the run-dir artifact PATHS (register_profile.json, final_prompt.txt,
  generated.png), asserting the UI consumes the agent-free artifacts, not a parallel in-UI computation.
- A dry-run / --explain path lets the frontend logic be tested with NO paid gpt-image-2 call
  (cost discipline §Cost): the build and its tests spend nothing.
- The standalone CLI core still runs the thin route end-to-end from ONE command with the frontend
  absent (assert the UI added no dependency the core needs).

## Hard rules
- NO image generation / paid calls in any automated test (constitution §Cost). Build on the written-JSON
  surface + dry-run/--explain. The ONE paid single-sign run is Alec's eye-gate AFTER the build.
- The UI MUST shell out to the existing CLI and read artifacts; it MUST NOT reimplement generation,
  register derivation, or prompt assembly (§I, §VII).
- Ground truth is Alec's eye on the real `generated.png` (§II). No VLM PASS is proof.
- Honest nulls (§V): if a stage artifact is missing (e.g. honest-null blank sign), the UI SHOWS the
  null + the manifest note; it never fabricates a placeholder or hides the gap.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII).
- NO em-dashes in any user-facing text (§Output rule).

## Definition of done
- Frontend runs the thin route for one single-sign brief live, in the browser, against the existing CLI.
- All four+ stages (brief, register/dial, assembled prompt, sign) render from the run dir.
- The taste gate (approve OR nudge-rerun, two actions) works end-to-end against a real run.
- Structural tests green (paste real output); the form-writes-verbatim-JSON test included.
- The standalone CLI still runs with the frontend absent (paste the one-command run).
- Report: files changed, the trigger mechanism, how the taste gate reaches the conductor, test output.
- The ONE paid single-sign run (~$0.08) is Alec's eye-gate AFTER the build, NOT inside it.
