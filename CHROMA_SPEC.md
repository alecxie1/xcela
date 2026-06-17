# BUILD SPEC: Chroma-Key Containment — integrate Root-A fix end-to-end

## Context (read first)
- ROOT CAUSE (proven): signs #2–#5 placed text outside the sign / mis-sized / over-extended
  because the generator paints FULL-BLEED designs and measure_canvas.py's detect_container()
  then GUESSES the sign boundary from color heuristics — returning the whole canvas or a random
  corner. Verified: container_bbox came back as [0.02,0.04,0.98,0.97] (whole canvas) on sign #3,
  a tiny corner on #2, etc.
- ROOT-A FIX (prototype PROVEN in proto_root_a.py, run it / read it): generate the sign as ONE
  die-cut object on a flat CHROMA-KEY green (#00B140) backdrop. gpt-image-2 does NOT support
  api background=transparent (400 error) — chroma key is the workaround. Then the container mask
  is RECOVERED DETERMINISTICALLY by color-distance from the key (6 lines), not guessed. Prototype
  result: opaque_components_large=1, transparent_frac=0.335, container_bbox=[0.059,0.046,0.936,
  0.959], center=[0.497,0.502], solidity=0.83 — a clean single contained object. Artifact at
  output/protoA_sign1/generated.png + cutout.png + alpha_report.json.
- Files: harness/scene_author.py (assemble_final_prompt + generation), harness/measure_canvas.py
  (detect_container), harness/closed_loop_composite.py (consumes container_bbox/free_space/
  optical_center). venv .venv; keys via dotenv ~/.hermes/.env. scipy now installed.

## Part 1 — generation: chroma-key framing for die-cut event props
In scene_author.py, add a CHROMA-KEY CONTAINMENT mode, gated to flat_graphic asset_profile when
the register/intent indicates a die-cut prop (event_prop register, or a new flag
--chroma-contain). When active, assemble_final_prompt PREPENDS a containment directive (adapt
from proto_root_a.py's CRITICAL FRAMING block):
  - render ONE die-cut sign as ONE discrete centered object occupying ~78% of frame
  - everything outside the die-cut shape = pure flat #00B140 chroma green, nothing on it
  - all fills/icons/text strictly INSIDE the shape; icon colors must avoid green (#00B140)
  - keep the existing reserved-headline-area + register/style/palette/footer blocks
Store chroma_key_hex in the run manifest so downstream knows the backdrop color.
Keep non-chroma behavior unchanged when the mode is off (poster/photo profiles unaffected).

## Part 2 — measure_canvas.py: deterministic chroma container recovery
Add detect_container_chroma(image_path, key_hex="#00B140", text_boxes_frac, fit_wh_frac):
  - mask = color-distance-from-key > 90  (sign = far from green)
  - DEFRINGE: erode the mask 1–2 px and despill green at edges so the white container stroke
    has no green halo (anti-aliased green/white boundary is the main risk).
  - keep the LARGEST connected component as the container (drop stray specks); fill holes.
  - container_bbox / container mask come straight from this (no HSV guessing).
  - free space = container interior minus OCR text boxes minus large non-fill-color blobs
    (mascot) minus edge margin; optical_center = center of largest free rectangle. REUSE the
    existing _max_rectangle / _fill_holes / _bbox_of / _label_components helpers.
  - return the SAME report shape as detect_container (container_bbox, free_space_bbox,
    optical_center, mascot_bbox, container mask, notes) so closed_loop_composite is unchanged.
Add a measure(..., chroma_key_hex=None) switch: when set, use the chroma path; else the legacy
HSV path. Plumb a --chroma-key CLI arg. Honest nulls on failure (e.g. green not found → note +
fall back to legacy path, say so).

## Part 3 — final deliverable: strip the green
A 手举牌 gets physically die-cut, so green must not survive. closed_loop_composite (or a new
finalize step) must, AFTER compositing the licensed headline:
  - produce <out>/cutout.png — RGBA, green→alpha=0 (the die-cut, transparent bg), defringed.
  - produce <out>/preview_white.png — cutout flattened onto white (human-gradeable, no green).
  - the composited headline + ghost-patch all happen on the RGB sign BEFORE green-strip.
Final outputs: generated.png (raw, green), final composited (green), cutout.png (transparent),
preview_white.png (white).

## Part 4 — PROVE one full sign end-to-end (real generation)
Run sign #1 (守住钱袋子 / 护好幸福家) through the FULL integrated path:
  scene_author --brand aia --asset-profile flat_graphic --chroma-contain
    --register-profile output/eventprop_sign1_calibrated/register_profile.json
    --intent-file intents/aia_sign1.json
    --ref-image "/mnt/c/Users/Alecx/Downloads/aia real task.png"
    --out output/chroma_sign1
  (NOTE: consider NOT passing the multi-panel ref image, or test both — the 4-panel
   'aia real task.png' encourages full-bleed/multi-panel imitation which fights containment.
   Try WITHOUT the ref first; if register drifts, add it back. Report which you used.)
VERIFY (deterministic, real numbers in your report):
  a. chroma recovery: exactly 1 large container component; transparent(green) frac > 0.12;
     container_bbox fully inside [0.02 .. 0.98] on all sides (NOT whole-canvas, NOT tiny corner).
  b. headline CONTAINED: every composited headline text pixel lies INSIDE the container mask
     (0 text pixels on what was green). Report the count of text px outside container (must be ~0).
  c. centered: composited block center within ±0.06 of detected optical_center.
  d. compliance: licensed_exact (rounded family 汉仪元隆黑 for this register).
  e. no green fringe: in preview_white.png, count pixels within 40 of #00B140 (should be ~0).
Compare container_bbox vs the BROKEN batch (#2 tiny corner / #3 whole canvas) to show the fix.

## Honest reporting
Show: which ref-image choice you used, the chroma container_bbox + recovery metrics, verify a–e
with real numbers, and paths+sizes of generated/cutout/preview_white. If containment fails
(green bleed, multi-object, text escapes), report plainly + diagnose — do not hand-fix the image.

## Conventions
Reuse existing helpers; don't duplicate. Keep legacy (non-chroma) paths working. No git commits.
venv .venv; uv pip install --python .venv/bin/python for any dep.
