# Research: Render-Aware Register (011)

**Phase 0 output.** No external unknowns: every question resolves from the codebase. Technical
Context contains no NEEDS CLARIFICATION. The five design decisions below were made by reading the
current code (`register/derive_register.py`, `harness/conductor.py:104-149,321-378,1071-1088`,
`harness/scene_author.py:136-142,380-410`).

## D1. How the render choice reaches the register engine

**Decision**: Add the RAW `render_style` string (verbatim from the brief inputs) into the
subfields dict, only on the thin route: `build_subfields(inputs, thin=False)` gains the flag and
includes `"render_style": inputs.get("render_style")` when `thin` is true and the key is present.
`write_glue_artifacts` already takes a `thin` flag (signature at harness/conductor.py:1071,
passed `thin=args.thin` at the `main()` call site, line 1148) and passes it through.
No new CLI flag on `derive_register.py`: the field rides inside the existing `--subfields` file.

**Rationale**: `build_subfields`'s documented contract is an identity pass-through (no inference,
no judgment glue); passing the raw human term verbatim preserves that, keeps provenance honest
(the trace can quote what the human actually picked), and needs zero contract change to the
`derive_register` CLI. Gating on `thin` keeps kit/legacy `subfields.json` byte-identical, which
is the strongest possible FR-007/FR-008 no-regression guarantee: `derive_register` is shared by
all three routes, so the safe seam is to never show the field to the routes that always render
flat.

**Alternatives considered**:
- A `--render-style` CLI flag on `derive_register.py`: rejected; a second input channel for one
  field splits the subfields contract and needs conductor argv changes in two builders.
- Passing the already-normalized asset_profile (`photo`/`flat_graphic`): rejected; cooks the
  value before the inference layer, breaking the identity pass-through and hiding the human's
  actual words from the trace.
- Including `render_style` on ALL routes: rejected; a kit-brand brief that carries
  `render_style: photographic` would silently flip the kit lane's register even though the kit
  path always renders flat. Out of scope per FR-008.

## D2. Where the photo interpretation lives

**Decision**: A tiny local predicate in `derive_register.py` (e.g. `_render_is_photo(value)`)
that treats `photographic`/`photo` (case/whitespace-insensitive) as photographic and everything
else (absent, blank, unrecognized) as flat, mirroring `conductor.normalize_render_style`.

**Rationale**: The conductor invokes `derive_register.py` as a SUBPROCESS; there is no import
path between `harness/` and `register/`, and `register/` must stay free of harness imports. The
rule is two string literals; the duplication risk is handled by a drift-guard test that imports
BOTH modules and asserts they agree on a shared table of inputs ("photographic", "photo",
"PHOTOGRAPHIC ", "flat vector", "", None, "watercolor"). Constitution V trade-off, decided
consciously: a non-empty unrecognized value (e.g. "watercolor") is treated as flat WITHOUT a
trace note, because FR-007 requires the absent/unrecognized path to behave exactly as before and
contract row 3 binds the absent case to byte-identity; the fallback is still auditable because
subfields.json preserves the raw value the human typed.

**Alternatives considered**:
- Importing `normalize_render_style` from the conductor: rejected; wrong dependency direction
  (the engine would import its orchestrator) and requires sys.path games in a subprocess-invoked
  script.
- Extracting a shared third module: rejected; one two-line predicate does not justify a new
  module (constitution VII: small enough to fit a fresh context).

## D3. Where the gate sits in the derivation

**Decision**: Wrap ONLY the marketing-to-event_prop vibe promotion (derive_register.py:96-98,
the `formality<=3 and playfulness>=7` branch). If that branch would fire AND the render is
photographic, suppress the promotion and append a trace line naming the render choice (FR-005),
e.g. `vibe would promote to event_prop (formality=2<=3, playfulness=8>=7) but render_style=
'photographic' is a photographic asset, not a flat prop => SUPPRESSED, register stays marketing`.
When the render is flat/absent, the branch behaves exactly as today and writes NO new trace line.

**Rationale**: The usage-rule path that sets `base = event_prop` from explicit keywords (rows in
`USAGE_RULES`) is upstream and untouched, so US3/FR-004 (explicit human signal wins over the
gate) holds by construction, not by an extra override. The formal branch (`formality>=8`) and the
event_prop demotion branch are unrelated to the defect and stay untouched (spec edge cases).
Tracing only when the gate fires keeps untouched paths byte-identical (FR-007, honest nulls).

**Alternatives considered**:
- Gating at the usage-rule table (drop the `event_prop` base for photo jobs): rejected; that
  would override the explicit human keyword, violating FR-004 and constitution I.
- A post-hoc register rewrite after step 2: rejected; the trace would show a decision then a
  reversal, which is harder to read than never making the wrong promotion.

## D4. Marketing keyword coverage (FR-006)

**Decision**: Append one row to `USAGE_RULES`, AFTER all existing rows:
`(("marketing", "social", "instagram", "promotional"), "marketing")`.

**Rationale**: First-matching-row-wins is the table's documented semantics; appending last means
every existing phrase (including the event-prop keywords, which encode the explicit human signal)
keeps its current precedence, and the new words only catch briefs that today fall through to the
unmatched default. The existing trace line already records which keyword matched, satisfying the
"explicit match, not fallback" requirement with no new trace code.

**Alternatives considered**:
- Inserting before the `formal_leaning` row: rejected; "handed out at a marketing event" would
  flip from formal_leaning to marketing, an unrequested behavior change.

## D5. Playful-tone retention mechanism (FR-009/010/011)

**Decision**: After the register is resolved (step 4 region), when `register == "marketing"` AND
the vibe is the same promoting vibe (`formality<=3 and playfulness>=7`): flex
`font:rounded` + `palette:playful-accents` into `brand_locks_flexed` (NOT `shape:die-cut`), and
set `font_role_hint = "rounded display"` plus a playful-marketing `tone_hint` while KEEPING
marketing's `shape_language_hint` (clean card / full-bleed, rectangular). Append a trace line
listing the retained cues and naming the vibe as the reason.

**Rationale**: This is exactly the vocabulary the downstream already consumes with zero 009
changes (FR-008): `scene_author` maps `font:rounded` and `palette:playful-accents` flex tokens to
prompt lines (scene_author.py:380-396) and resolves `font_role_hint` against the licensed styles
map (derive_register.py step 5), so the retained tone drives both the prompt and the licensed
font pick. Withholding `shape:die-cut` keeps the format rectangular AND keeps chroma containment
off (scene_author `chroma_contain_active` keys on event_prop or the die-cut flex), so no prop
behavior leaks in (FR-010). Keying on the vibe rather than the render choice makes the retention
apply wherever marketing meets a playful vibe (FR-011); on the flat path that combination still
promotes to event_prop first (FR-003), so flat behavior is unchanged.

**Alternatives considered**:
- A new `tone` field in the register profile consumed by scene_author: rejected; requires 009
  opener-matrix changes, violating FR-008, and duplicates an existing mechanism.
- Blending sliders (raise playfulness magnitude instead of cues): rejected; sliders set
  MAGNITUDE and are calibration-owned; the defect is about direction-level cues, and slider
  nudges are not falsifiable as discrete cue assertions.
