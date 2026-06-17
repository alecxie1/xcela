# BUILD SPEC: Layer-2 Font Intelligence + Composition-Aware Reservation + A/B

## Context (read first)
- docs/FONT_INTELLIGENCE_design_note.md — the design rationale (Alec's critique: composite
  looked worse than all-AI version: font too thin for call-to-action, dead negative space,
  graphics bleeding out — root cause: type treatment bypassed the scene-author).
- harness/scene_author.py — the scene authoring engine (you will extend it).
- harness/composite_text.py — the compositor with font_role/brand answer-key resolution (built, working).
- answer_keys/aia.json — typography block: roles (english_primary=AIA Everest, chinese_primary=
  汉仪甄选37款字体 w/ file_fallback simhei.ttf), rules[], and _candidates_rejected listing the
  汉仪 library members WITH WEIGHTS (元隆黑-75简, 玄宋55/75简, 赤云隶95简, 雅酷黑-55简...).
- Goal: the scene author DESIGNS the type (role/weight/size) and the composition reserves
  exactly the space its own text plan needs. Then A/B two compositing strategies.

## Part A — scene_author.py: typography-aware tier-3 (flat_graphic profile)
1. Load the answer key's typography block (roles + rules + _candidates_rejected names —
   the rejected pile is the LIBRARY VOCABULARY, pass the names as "library_members").
2. Inject into the meta-prompt a TYPOGRAPHY VOCABULARY section: available roles (with VI names),
   library members w/ their weight suffixes, and the VI rules verbatim as constraints.
3. text_layout entries now REQUIRE: font_role (one of the answer key roles), weight_hint
   (descriptive: heavy-display / bold / regular / light — and if a specific library member
   fits, name it, e.g. 汉仪元隆黑-75简 for call-to-action), size_px (explicit), color_hex.
   The author must REASON about occasion register: call-to-action sign → heavy display;
   premium/elegant → lighter; footer/body → digital/system role. Never invent font names
   not in the vocabulary.
4. NEW tier-3 field "headline_reservation": {x_frac, y_frac, w_frac, h_frac} — the exact
   box the composition must keep clear for composited text, COMPUTED FROM its own text plan
   (lines × chars × size_px vs canvas 1536x1024). The author designs the composition AROUND
   this box as the protagonist — graphics must NOT bleed past the container edges and must
   yield this space. Composition % rules (text dominance) still apply.
5. VALIDATION (deterministic, in code, after authoring): every text_layout.font_role exists
   in the answer key; headline_reservation fracs in [0,1] and area ≥ rough text area needed
   (chars × size_px² × 1.15 fudge). Violations → print warning + ONE re-ask with the
   violation named, then proceed with best effort (honest note in output).

## Part B — assemble_final_prompt: precise reservation rendering
For flat_graphic with headline_reservation: replace vague "leave empty space" language with
exact placement: "Reserve a completely blank area at [x..x+w]×[y..y+h] (fractions of canvas)
— no text, no graphics, no marks; the headline will be added in post. Design the composition
so this blank area reads as the intentional focal zone." Headline text_layout entries marked
composited=true are EXCLUDED from the image prompt (footer/small text still rendered by the
model — only reserved-area text is composited).

## Part C — auto-generated composite spec (close the loop)
New: scene_author writes <out>/composite_spec.json derived from tier-3: for each
composited=true text layer → {content, font_role, brand, weight_hint, size_px, color,
anchor_frac centered in the reservation box, letter_spacing}. After generation, run
composite_text.py with that spec automatically (add --brand to scene_author CLI or infer).
Final output: <out>/generated.png (blank) + <out>/final.png (composited). The single source
of truth for type is the tier-3 plan — no hand-written specs anywhere.

## Part D — the A/B test (REAL runs, both paths, AIA sign #1)
PATH 1 (reservation): run the full extended pipeline:
  .venv/bin/python harness/scene_author.py --brand aia --out output/ab_path1_reservation \
    --intent-file intents/aia_sign1.json --asset-profile flat_graphic \
    --style-notes "<same two campaign rules used in the batch — read them from any aia_sign*_toolrun manifest or reuse: container shapes expressive/varied not plain rounded rectangle; text is protagonist, graphics subordinate>" \
    --ref-image "/mnt/c/Users/Alecx/Downloads/aia real task.png"
  → final.png composited via Part C with chinese_primary fallback (simhei) at the
  weight/size the scene author chose.
PATH 2 (cover-and-redraw): take output/aia_sign1_toolrun/generated.png (the all-AI version
  whose composition Alec liked). Build harness/cover_redraw.py (~100 lines):
  - Crop the known headline region (the two big lines 守住钱袋子/护好幸福家 — locate by
    scanning for the largest dark-red text mass in the upper-middle; a simple approach:
    color-threshold AIA red/dark tones in the center band, take bbox, pad 4%).
  - Sample the local background color around the bbox (median of a 10px ring), fill bbox.
  - Redraw both lines with composite_text.py (chinese_primary, size to match original
    visual weight ~same bbox height, heavy stroke_width 2-3 to compensate single-weight
    simhei thinness, color sampled from the original text pixels before patching).
  → output/ab_path2_coverredraw/final.png. If bbox detection is unreliable, hardcode an
  approximate region from looking at the image dims (state honestly that detection was manual).
BOTH paths print: real file sizes, the tier-3 typography choices (path 1), the detected/used
bbox + colors (path 2).

## Honest reporting
- Show the tier-3 text_layout + headline_reservation JSON the author produced.
- If the reservation comes back violated by the generator (graphics/text in the reserved box),
  say so plainly — that IS a finding for the A/B.
- Do not retouch outputs by hand. No claims without file evidence.

## Conventions
venv .venv; use `uv pip install --python .venv/bin/python <pkg>` for any new deps (no pip in
venv). Keys auto-load via dotenv. Do not break photo-profile behavior of scene_author
(taichi runs must still work — keep changes additive/conditional). No git commits.
