# Phase 0 Research: Beyond Flat-vector Event Signs (Render Modes)

The spec's forks were settled (Clarifications). The three deferred HOW items are resolved here, grounded in
code read 2026-06-30. No NEEDS CLARIFICATION remains. The opener wording (Decision 2) is PROPOSED VERBATIM
for the user's sign-off before implement (as with the 008 role wording).

## Decision 1: render_style carrier + where it maps to asset_profile

**Decision**: `render_style` (user terms: "flat vector" / "photographic") is carried VERBATIM from the form
through `inputs_writer` into the inputs JSON. The conductor maps it to the engine `asset_profile`
(`flat_graphic` / `photo`) via a new `normalize_render_style(value)` helper (mirroring `normalize_dial`),
threaded into `_scene_author_thin_argv` (a new `asset_profile` param, default `ASSET_PROFILE` for
back-compat), so the thin argv carries `--asset-profile photo|flat_graphic`.

**Rationale**:
- The frontend + the brief speak the USER vocabulary (`render_style`); the engine speaks `asset_profile`.
  The conductor is the single boundary that builds the scene_author argv and owns `ASSET_PROFILE` (`:62`),
  so the translation belongs there, in one place. `inputs_writer` stays a pure pass-through (it already
  carries free-text fields verbatim; adding a mapping there would leak engine vocabulary into the frontend).
- `_scene_author_thin_argv` is the ONLY thin-argv site (`:228`, called once from `build_plan:359`), and
  `run_thin_mode` already forwards `args.asset_profile` to `assemble_thin_prompt` (`scene_author.py:1009`),
  and `--asset-profile` already accepts `photo|flat_graphic` (`:1344`). So the only missing link is the
  conductor passing the mapped value instead of the constant.
- Mapping: `"photographic" -> "photo"`; everything else (including "flat vector", blank, unrecognized) ->
  `"flat_graphic"` (honest-null safe default, recorded). Case / whitespace-insensitive.

**Alternatives considered**:
- *Map in `inputs_writer`*: rejected. Pushes engine vocabulary (`asset_profile`) into the frontend; the
  conductor would still need a fallback for CLI briefs. One translation point in the conductor is cleaner.
- *Carry `asset_profile` directly in the brief (no user term)*: rejected at clarify (Q2=A); the brief keeps
  the user term `render_style`.

## Decision 2: opener wording (CONFIRMED VERBATIM 2026-06-30)

**Decision**: `assemble_thin_prompt`'s opener becomes (asset_profile x register)-aware. `{cn}`/`{en}` are
the brand names. v1 uses generic register-derived nouns, NOT the free-text `asset_type`.

- **flat + event_prop (UNCHANGED, byte-identical - regression):**
  `A FLAT VECTOR GRAPHIC DESIGN: a playful, eye-catching hand-held event photo-prop sign for {cn} ({en}). It is a fun die-cut prop people want to grab and pose with — NOT a corporate sign, NOT a photograph, NOT 3D. Bubbly flat illustration style, festival energy.`
- **flat + marketing/formal (REWRITE; was "a designed hand-held event sign"):**
  `A FLAT VECTOR GRAPHIC DESIGN: a rectangular marketing poster for {cn} ({en}). NOT a photograph, NOT 3D: modern flat illustration, advertising quality, crisp and clean, composed as a full rectangular poster or flyer.`
- **photo + event_prop (NEW):**
  `A PHOTOGRAPHIC hand-held event prop for {cn} ({en}): a real, photographed prop people grab and pose with. Photographic realism, natural lighting and depth, advertising photography quality.`
- **photo + marketing/formal (NEW):**
  `A PHOTOGRAPHIC marketing poster for {cn} ({en}): a real photographed scene composed as a full rectangular poster. Photographic realism, natural lighting, depth of field, advertising photography quality. NOT a flat illustration, NOT a cartoon.`

**Rationale**:
- The event_prop flat opener is kept byte-identical (em-dash included) so the proven event-sign path does
  not regress (FR-007 / SC-005). Its pre-existing em-dash is legacy debt, retained deliberately for
  byte-identity; the NEW openers are em-dash-free (output rule).
- The flat-marketing opener is the bug fix (US2): today it says "a designed hand-held event sign" for a
  poster; now it reads as a rectangular poster.
- The photo openers use photographic language (realism, lighting, depth of field) and explicitly negate
  flat/cartoon, so the dialect is unambiguous.
- Generic nouns ("marketing poster", "hand-held event prop") avoid threading `asset_type` into
  `assemble_thin_prompt` and the risk that gpt paints the asset_type text onto the canvas; asset_type
  specificity is deferred (Decision 4).

**Alternatives considered**:
- *Inject the brief's `asset_type` for specificity*: deferred. Needs a new param threaded conductor ->
  argv -> run_thin_mode -> assemble_thin_prompt, and risks on-canvas hallucinated text; generic
  register-derived nouns are enough for v1.

## Decision 3: negatives regrouping

**Decision**: Split the current single negatives line (`scene_author.py:952`) into a render-AGNOSTIC
text-guard clause applied in BOTH modes and a flat-only render clause:
- flat (`is_graphic`): `NEGATIVES: no photographic shading, no 3D realism, no gibberish or garbled text, no extra Chinese text beyond the headline above, no tagline, no watermark.` (byte-identical to today)
- photo (else): `NEGATIVES: no gibberish or garbled text, no extra Chinese text beyond the headline above, no tagline, no watermark.`

**Rationale**:
- The thin route paints any Chinese it sees, so the text guards (verbatim headline only, no extra Chinese /
  no gibberish / no tagline / no watermark) must apply in BOTH render modes. The render negatives
  ("no photographic shading, no 3D realism") are flat-ONLY and would defeat the photographic mode.
- Building the flat line by prepending the render clause to the shared text-guard string yields a
  byte-identical flat NEGATIVES line, preserving the event-sign regression.

## Decision 4 (from the brief): asset_type specificity in the opener

**Decision**: DEFERRED out of v1. The opener uses generic register-derived nouns, not the free-text
`asset_type`. Rationale: avoids new plumbing (an asset_type param to assemble_thin_prompt) and the on-canvas
hallucination risk; the register already distinguishes poster vs prop. A later enhancement can add it.

## Decision 5 (from clarify): photographic event-prop allowed

Resolved at clarify (Q1=A): photographic is allowed for ANY register, including event_prop; the photo +
event_prop opener above covers it. No restriction, no warning.

## Reuse map (touched vs untouched)

| Component | 009 disposition |
|-----------|-----------------|
| `scene_author.ASSET_PROFILES` + `--asset-profile` flag + `run_thin_mode` forwarding | REUSED unchanged |
| `scene_author.assemble_thin_prompt` opener + negatives | CHANGED (matrix opener + negatives split) |
| `scene_author` event_prop flat opener + flat NEGATIVES line | BYTE-UNCHANGED (regression) |
| `conductor.normalize_render_style` | NEW (user term -> asset_profile) |
| `conductor.build_plan` + `_scene_author_thin_argv` | CHANGED (thread the mapped asset_profile + manifest) |
| `conductor` kit/legacy/no-ref argv builders (:188/:219), chroma/measure/composite | UNCHANGED |
| `inputs_writer.to_inputs` | CHANGED (carry render_style verbatim) |
| `frontend/index.html` | CHANGED (render-style control) |
