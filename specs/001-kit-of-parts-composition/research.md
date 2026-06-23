# Phase 0 Research: Kit of Parts + Bespoke Composition

All decisions below are grounded in the ACTUAL code (verified by reading `harness/conductor.py`,
`harness/scene_author.py`, `harness/composite_text.py`, `harness/measure_canvas.py`, the
`register/` modules, and `answer_keys/aia.json` / `config/aia.yaml`). The spec's Assumptions
required this reuse verification before proposing new modules.

---

## D1. Where the kit lives (authored vs derived)

**Decision**: Split the kit into two layers.
- AUTHORED layer → a NEW per-brand data file `kits/<brand>.json`, holding `icon_vocabulary`
  (meaning→icon entries) and `layout_vocabulary` (layout archetypes). Human-authored brand DATA.
- DERIVED layer → computed at runtime into a `kit_profile.json` artifact: palette, font role,
  frame/border treatment, register, pulled from `answer_keys/<brand>.json` + `register_profile`
  + reference calibration.

**Rationale**: The icon/layout vocabulary is task-specific (event-sign) and human-authored
(clarified), so it does not belong in `answer_keys/<brand>.json` (brand DNA: color/typography/
logo) nor in `config/<brand>.yaml` (thin harness config). A dedicated `kits/<brand>.json` keeps
all AIA composition literals in DATA (FR-008) and out of shared code. The derived layer already
has a home: `register/derive_register.py` produces `register_profile` (with `brand_anchors_held`
/ `brand_locks_flexed`, font role hints) and `calibrate_from_reference.py` produces the reference
magnitude + style evidence. `kit.py` merges these into one `kit_profile.json` the composer reads.

**Alternatives considered**:
- Extend `answer_keys/<brand>.json`: rejected — pollutes brand DNA with task-specific vocab;
  the DNA is shared across asset types, the kit is per-task.
- Put vocab in `config/<brand>.yaml`: rejected — config is intentionally a thin spine; variants
  there are brand-AGNOSTIC, the kit vocab is brand-specific content.

---

## D2. Deterministic meaning→icon matching (FR-002, clarified)

**Decision**: Each `icon_vocabulary` entry carries `meaning_cues` (a list of authored keyword/
phrase cues, e.g. `["钱袋","钱袋子","储蓄","存款"]` → `money_bag`) and a `mode` tag
(protect / warn / resist). `compose_select.py` matches a message against cues by deterministic
token/substring containment, scoring by number/specificity of cue hits. The highest-scoring
entry above a confidence floor wins. Below the floor → honest-null + needs_review (human picks).
Selection is deterministic; NO generative/LLM guess decides the icon.

**Rationale**: The clarification is explicit: "deterministic-first (match against the authored
vocabulary, not an open-ended generative guess) and must honest-null when no confident match
exists." Authored cues make the match reproducible and falsifiable (test: 钱袋子 → money_bag;
nonsense → null). The chosen entry holds an `icon_description` that gpt-image-2 RENDERS in the
icon zone — so the SELECTION is deterministic while the RENDERING stays generative, cleanly
separating the two. This matches constitution III (falsifiable) and V (honest nulls).

**Alternatives considered**:
- LLM classifies meaning→icon: rejected for v1 — non-deterministic (constitution III; the code
  already notes VLM extraction is non-deterministic), and the clarification forbids open-ended
  generative guessing for the pick. May be added later as a SUGGESTION the human approves, but
  the v1 floor is deterministic cue matching.
- Embedding similarity over icon names: rejected for v1 — adds a model dependency and
  non-determinism for a vocabulary small enough to cue-author by hand.

---

## D3. Layout-archetype selection + collision avoidance (FR-003, clarified)

**Decision**: `layout_vocabulary` holds multiple distinct archetypes, each tagged with the
`mode`(s) it serves and carrying zone geometry (icon zone + reserved text zone as canvas
fractions) plus a panel/background treatment spec. `compose_select.py` selects per message: from
the archetypes serving the message's mode, pick one; across the campaign, assign DISTINCT
archetypes (greedy, collision-avoiding) so no two signs collide while the vocabulary has supply.
Only when the vocabulary is genuinely exhausted does it reuse an archetype, and then it flags the
reused signs `needs_review`. No hard cap. The tool does NOT auto-jitter a reused composition.

**Rationale**: Directly encodes the clarification ("the kit holds MULTIPLE distinct layout
archetypes ... deterministically selects ... picks a different archetype on collision ... reuse
+ flag only when exhausted ... tool must NOT jitter; that is the human finishing layer"). Mode
comes from the matched icon entry's `mode` (D2), keeping mode and icon consistent. Deterministic
and falsifiable (test: two distinct-mode messages → two distinct archetypes; exhaustion → reuse
flagged).

**Alternatives considered**:
- Tool varies composition "ever so slightly" automatically: explicitly REJECTED by the
  clarification — slight variation is the human finishing layer at approve/canvas.
- Hard cap at the number of archetypes: REJECTED by the clarification — reuse+flag instead.

---

## D4. Generation + text reservation + non-collision (FR-004, FR-005)

**Decision**: Per message, build a generation prompt (extending `scene_author.assemble_final_prompt`
in reserve-box mode) that paints the archetype's background/panel treatment + the chosen icon's
`icon_description` INSIDE the archetype's icon zone, and keeps the archetype's text zone CLEAR.
The licensed headline is then composited into the cleared text zone by `composite_text.composite`.
Because the icon zone and text zone are disjoint by construction (the archetype defines both), no
scrub step is needed and the icon is never overpainted.

**Rationale**: The reserve-box path already exists (`scene_author` `reserve_box_mode` +
`write_composite_spec` + `composite_text`); the failure was that the reservation was authored
freely by Anthropic and ignored, and text was a clone. The reframe makes the reservation come
from the CHOSEN ARCHETYPE (kit-driven, per-message-distinct) and composites text into it. This
fixes failure (b) (no scrub damage) and (c) (distinct compositions) by construction. We do NOT
use render-and-scrub (the current default), which is the wrong frame per the spec.

**Alternatives considered**:
- Keep render-and-scrub and fix measure/scrub: REJECTED by the spec ("Fixing measure/scrub does
  NOT bridge this, it is the wrong frame").
- Fully procedural composite (no gpt): rejected for v1 — needs an icon-asset library that does
  not exist; gpt renders the described icon + bevel/border far more cheaply for now.

---

## D5. Fit-to-zone type clamp (FR-004 — fixes failure (a))

**Decision**: Add a fit-to-zone clamp invoked before compositing the headline: given the headline
text, the reserved zone (w/h fractions → pixels), and the licensed font (resolved via the
existing `composite_text.resolve_font`), compute the largest `size_px` whose rendered multi-line
text box fits inside the zone with a margin on all edges. Scale DOWN as needed. If the text does
not fit even at a defined minimum size, emit null + needs_review (do not clip, do not overflow).

**Rationale**: The known pitfall is "`place_measured` inherits gpt's text size, no fit-to-margin
clamp yet (failure (a))." The compositor already measures glyph extents via Pillow when it
renders; the clamp reuses that measurement to search for the fitting size. This is brand-general
(no AIA literals) and falsifiable (test: a long headline yields a strictly smaller size_px and a
rendered box within the zone; an impossible headline yields null). Composition owns the zone;
type is sized to fit, never the reverse (FR-004, north-star step 2d).

**Alternatives considered**:
- Let gpt size the text: REJECTED — that is the current failure; gpt over-sizes and overflows.
- Shrink the zone to the text: REJECTED — inverts the rule; the composition owns the zone.

---

## D6. Reference handling: internalize style, do not clone (FR-007, clarified)

**Decision**: For AIA family jobs the reference feeds the DERIVED kit layer only (palette, font
feel, frame/border treatment, register magnitude) via the existing
`calibrate_from_reference` + `reference_style_to_prompt` style extraction. It does NOT drive a
per-sign aligned-prompt clone. On ANY conflict between the reference and the answer key, the
answer key wins (clarified). The current conductor reference path (analyzer → aligned_prompt →
scene_author `--aligned-prompt`, tier-3 skipped) is BYPASSED for family/kit jobs; the reference's
style evidence flows into `kit_profile.json` instead.

**Rationale**: The clarification ("answer key always wins on any disagreement; reference still
internalized where there is no conflict") plus the spec's core ("the reference is a STYLE SYSTEM
to internalize, not a panel to clone"). Reusing `calibrate_from_reference`'s `style_evidence` and
`anchors_held`/`locks_flexed` gives the kit its soft dimensions while answer-key locks stay hard.

**Alternatives considered**:
- Keep the aligned-prompt clone path: REJECTED — it IS the "one template, N texts" machine the
  feature replaces.

---

## D7. Conductor routing + human gate (FR-006, constitution I)

**Decision**: `conductor.py` gains a kit-composition route for family jobs: after deriving the
shared `register_profile`/calibration, it builds `kit_profile.json` once (campaign constant), then
per sign calls `compose_select` (icon + archetype) and routes `scene_author` in reserve-box +
fit-to-zone mode. The per-sign icon and layout PROPOSALS (and any needs_review flags) are surfaced
at the EXISTING approve/nudge gate so the human approves or overrides before/at draft review. All
existing non-negotiables are preserved: licensed-font compliance manifest, honest nulls +
needs_review in the run manifest, the approve gate, no em-dashes.

**Rationale**: Constitution I (human at input + taste gates) and FR-006 (preserve guarantees).
The conductor already has the approve/nudge gate, per-sign loop, shared register profile, and
manifest with notes/needs_review — the route plugs into these rather than replacing them.

**Alternatives considered**:
- A brand-new top-level orchestrator: rejected — duplicates the conductor's gate/manifest/loop
  machinery; the existing conductor is the right host.

---

## Reuse summary (verified against code)

| Existing capability | File | Reused for |
|---------------------|------|-----------|
| Campaign loop, approve/nudge gate, manifest, honest-null notes, dry-run | `harness/conductor.py` | D7 routing + gate |
| Reserve-box mode, reservation concept, `assemble_final_prompt`, chroma framing | `harness/scene_author.py` | D4 generation + reserve |
| Licensed-font compositor, `resolve_font`, compliance manifest, glyph measurement | `harness/composite_text.py` | D4 composite + D5 fit clamp |
| OCR + container/free-space geometry (chroma path proven) | `harness/measure_canvas.py` | structural verification of fit/non-collision |
| `derive_register` (DIRECTION), `calibrate_from_reference` (MAGNITUDE), style extraction | `register/` | D1 derived kit + D6 reference |
| Brand DNA: colors (roles), `typography.styles` map, logo | `answer_keys/aia.json` | D1 hard locks (win conflicts) |

| Genuinely NEW | Why nothing existing covers it |
|---------------|-------------------------------|
| `kits/aia.json` (icon + layout vocabulary) | No icon/layout vocabulary exists anywhere in the repo today |
| `harness/kit.py` (load/validate + derive kit_profile) | No module merges authored vocab + derived style with answer-key-wins |
| `harness/compose_select.py` (meaning→icon + archetype selection) | No deterministic selection step exists |
| fit-to-zone clamp (in `composite_text.py`) | Pitfall confirms no fit-to-margin clamp exists (failure (a)) |
