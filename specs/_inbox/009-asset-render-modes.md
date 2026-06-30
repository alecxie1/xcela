# SPEC BRIEF for /speckit-specify - Feature 009: beyond flat-vector event signs (render modes)

DECISION MAP. The forks below were SETTLED in conversation (2026-06-30) and grounded in the ACTUAL code.
This is the substrate so the spec fills a known shape. THE BIG ONE: the tool currently generates ONLY
flat-vector die-cut event signs; this lets the task drive the RENDER MODE and FRAMING so a designer can
also produce flat rectangular posters/flyers and PHOTOGRAPHIC posters, on the thin route.

---

## Problem / why
The tool only ever produces flat-vector die-cut hand-held event signs, even though the brief's
`asset_type` is free text. Two hard-codings cause it: (1) the conductor hard-wires
`ASSET_PROFILE = "flat_graphic"` (`conductor.py:62`) and passes it into every scene_author call
(`:188/:219/:236`); `asset_type` only nudges `usage_context`, never the render mode (`conductor.py:24`
states this). (2) The thin prompt opener hard-codes "hand-held event sign" in BOTH flat branches
(`scene_author.py:850-860`), so even a flat POSTER announces itself as a hand-held event sign. This is the
tool built for ONE task; brand DNA and task needs DIVERGE and the task must govern the SOFT dimensions
(render style, shape, register) per-dimension (constitution §VI), not be frozen to event signs.

Encouragingly, the BONES already exist: `scene_author.ASSET_PROFILES` defines BOTH `photo` and
`flat_graphic` dialects (`:33-44`); scene_author already accepts `--asset-profile photo|flat_graphic`
(`:1344`); `assemble_thin_prompt` already drops the flat-vector negatives for a non-graphic profile
(`:924-927`) and has a generic non-graphic opener `else` branch (`:862`); `chroma_contain_active` already
returns False for any non-flat profile (`:136-141`); and the thin route never invokes chroma / measure /
composite. So the unlock is mostly: stop hard-wiring the profile, let the human pick it, and generalize
the opener. Scoped to the thin route, this is tractable.

## Goal (scopes "done")
On the thin route (the live-runner path: reference required, chroma off, deliverable final.png), the
designer EXPLICITLY picks a RENDER STYLE (flat vector vs photographic); the chosen mode drives the
prompt's render dialect, and the SHAPE/FRAMING follows from the register (event_prop -> die-cut hand-held
prop; marketing/formal -> rectangular poster/flyer). "Done" = a designer generates a PHOTOGRAPHIC poster
and a flat rectangular flyer through the live-runner, not just a die-cut event sign, with the existing
flat event-sign path unchanged.

## LOCKED decisions (settled in conversation; do NOT relitigate)

| Decision | Locked value | Rationale |
|---|---|---|
| v1 surface | the THIN route / live-runner ONLY (reference required, chroma off, no measure/composite) | the kit / tier-3 / no-reference-cutout / legacy render-and-scrub paths are where the hard flat-vector + chroma + OCR-composite assumptions live; a much bigger lift, OUT of scope |
| Render style choice | an EXPLICIT human pick at the input gate (a control: flat vector / photographic), default flat vector | agent-free: the human picks the mode; NO model classifier of free-text asset_type (silent judgment is rejected) |
| Render style -> internal | `render_style` (user term: flat vector / photographic) maps to `asset_profile` (flat_graphic / photo) | reuse the existing asset_profile machinery + the `--asset-profile` flag and ASSET_PROFILES dialects |
| Shape / format | DERIVED from the register (event_prop -> die-cut hand-held prop; marketing/formal -> rectangular poster/flyer), NOT a second manual control | per-dimension reconciliation (§VI); the human already drives it via usage_context -> register; one explicit control (render style) keeps the gate simple |
| Conductor | the thin path STOPS hard-wiring flat_graphic; it carries the chosen asset_profile from the brief into the thin argv + the manifest/subfields | the brief drives the render mode now (the whole point) |
| Opener generalization | `assemble_thin_prompt` gets a real PHOTOGRAPHIC opener AND the flat opener stops hard-coding "hand-held event sign" (register-aware; uses the brief's asset_type for specificity) | unlocking photo forces de-hard-coding the event-sign framing anyway; both halves of "flat-vector event signs" |
| Negatives | split the current bundle: render-AGNOSTIC text negatives (no gibberish/garbled text, no extra Chinese beyond the headline, no tagline/watermark) ALWAYS apply; the flat-only render negatives (no photographic shading, no 3D realism) apply ONLY to flat_graphic | a photo poster must keep the text guards but allow photographic realism |
| Deliverable | final.png (the reference job), chroma OFF (already true for the reference job; photo auto-disables chroma) | unchanged; no cutout on the thin reference path |
| Default | render_style defaults to flat vector (back-compat); the existing event-sign path is byte-unchanged | no regression for the proven path |

## The change, stage by stage (thin route only)
```
frontend/index.html      : add a Render style control (flat vector / photographic); post it in the form.
frontend/inputs_writer.py: carry render_style -> the inputs JSON (map to asset_profile or keep render_style
                           and let the conductor map). PURE, verbatim for the other fields.
harness/conductor.py     : the THIN argv builder (_scene_author_thin_argv, :236) takes the asset_profile
                           from the brief instead of the ASSET_PROFILE constant; the manifest/subfields
                           record the chosen profile (drop the "ALWAYS flat_graphic" notes, :402-403/:970-971
                           for the thin path). The kit/legacy/no-ref argv builders (:188/:219) stay
                           flat_graphic (out of scope).
harness/scene_author.py  : assemble_thin_prompt opener becomes (asset_profile x register)-aware: photo ->
                           a real photographic opener; flat + event_prop -> die-cut hand-held prop
                           (unchanged); flat + marketing/formal -> rectangular poster/flyer (NEW, no
                           "hand-held event sign"); split the negatives (render-agnostic text guards always;
                           flat-only render negatives only for flat_graphic).
```

## Verified codebase state (STEP ZERO - confirm before building)
- `conductor.py:62` `ASSET_PROFILE = "flat_graphic"`; passed at `:188/:219/:236`; `:24` "output is ALWAYS
  flat_graphic". `_scene_author_thin_argv` (:228-239) uses the constant, takes no asset_profile param.
- `scene_author.py:33-44` ASSET_PROFILES has `photo` + `flat_graphic`; `:1344` `--asset-profile` flag
  (choices photo|flat_graphic). `assemble_thin_prompt` (:846+) branches: `:850-855` is_graphic+event_prop
  (die-cut prop), `:856-860` is_graphic else (HARD-CODES "hand-held event sign"), `:862` non-graphic else
  (weak "A promotional marketing asset for {brand}."); `:924-927` negatives gated on is_graphic (bundles
  render + text negatives). `_primary_color_hex` + register directive unchanged by 009.
- `chroma_contain_active` (:136-141) returns False for any non-flat profile; the thin route never invokes
  chroma/measure/composite, so a photo poster on the thin route is clean.
- register: `derive_register` maps usage_context -> event_prop/marketing/formal and flexes shape:die-cut
  for event_prop; the opener can read the register to choose die-cut vs rectangular.
- The live-runner is reference-required (007); deliverable final.png; chroma off. Good fit for v1.

## Forks already resolved (do not reopen)
- thin route only (kit/legacy/no-ref/cutout/measure-composite OUT).
- explicit human render-style pick (NOT a model classifier).
- shape derived from register (no second manual control).
- flat vector is the default (back-compat; event-sign path unchanged).
- v1 beachhead = flat-rectangular + photographic on the reference thin path.

## Out of scope (v1)
- The kit / tier-3 / no-reference-cutout / legacy render-and-scrub paths and the measure/composite OCR
  pipeline (where the flat-vector + chroma assumptions are baked).
- The no-reference (chroma ON, cutout.png) job in any render mode.
- Auto-classifying asset_type into a render mode (the human picks).
- New physical print specs, bleed/format presets, social-tile sizes beyond what format_size already does.
- typography / font roles, the palette work (008), and any conductor input-contract change beyond adding
  the render-style carrier.
- Generation quality tuning of the photo dialect to one image (generalize, do not hand-tune).

## Falsifiable tests (constitution §III - assert VALUES a wrong build cannot satisfy; NO paid calls)
- `assemble_thin_prompt(..., asset_profile="photo", ...)` -> the prompt CONTAINS photographic language and
  does NOT contain "FLAT VECTOR" or "no photographic shading"; it STILL contains the text guards (the
  verbatim headline; no-extra-Chinese / no-gibberish). A wrong build that ignores the profile still says
  flat vector -> fails.
- `assemble_thin_prompt(..., asset_profile="flat_graphic", register=marketing/non-event_prop)` -> the
  opener does NOT contain "hand-held event sign"; it reads as a rectangular poster/marketing graphic. A
  wrong build (hard-coded event sign) fails.
- `assemble_thin_prompt(..., asset_profile="flat_graphic", register=event_prop)` -> UNCHANGED (still
  die-cut hand-held prop + the flat render negatives) (regression).
- The conductor thin argv carries the brief's asset_profile: `build_plan` with render_style=photographic ->
  the scene_author thin argv contains `--asset-profile photo` (NOT the flat_graphic constant). A wrong
  build (constant) fails.
- `inputs_writer.to_inputs` round-trips render_style -> the inputs JSON (and maps to asset_profile if that
  is where the mapping lives); the other fields stay verbatim (002 invariant).
- The served live-runner page has a render-style control (structural grep).
- Default / omitted render_style -> flat vector -> the event-sign path is byte-unchanged (regression).

## Hard rules
- NO paid model calls in any automated test (assert the assembled prompt STRING + the argv + the inputs
  round-trip; never generate). The one paid sign (a real photographic poster) is the human eye-gate (§II).
- Agent-free: the human picks the render style at the input gate; no silent classifier (§I).
- GENERALIZES, not hand-tuned: the opener/negatives logic is task-general (driven by asset_profile +
  register), no one-image tuning (§IV).
- Reconciliation per-dimension (§VI): brand still governs color/font/logo HARD; the task governs render
  style + shape + register SOFT. Do not collapse the split.
- Honest-null: an unrecognized render_style falls back to flat vector (the safe default), recorded.
- Thin route ONLY; kit/legacy/no-ref/measure-composite UNCHANGED; the conductor input contract changes
  only by adding the render-style carrier.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII). NO em-dashes in user-facing text.

## Open questions for /speckit-plan (flag, do not solve in the spec)
- The carrier in the inputs JSON: a user-facing `render_style` field vs the internal `asset_profile`, and
  WHERE render_style -> asset_profile is mapped (inputs_writer vs conductor). Resolve against the 002
  inputs contract + the conductor.
- The EXACT photographic opener wording and the negatives regrouping (like the 008 ROLE_GUIDANCE wording,
  confirm verbatim at plan/clarify).
- Whether photo + event_prop (a photographic hand-held prop) is allowed in v1 or constrained to the
  marketing/formal registers; pick the sensible default and state it.
- The opener's source of asset_type specificity (the brief's free-text asset_type) and how much of it to
  inject without letting gpt hallucinate (the thin route paints any Chinese it sees).
```
