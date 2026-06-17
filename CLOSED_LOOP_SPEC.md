# BUILD SPEC: Closed-Loop Composite — measure-then-place (fixes ghost text + off-center anchoring)

## Context (read first)
- ROOT CAUSE (diagnosed, verified): composite placement is OPEN-LOOP. composite_spec.json anchors
  text at coordinates from the tier-3 PLAN (headline_reservation), but gpt-image-2 paints its own
  geometry — the actual container interior lands elsewhere (in output/eventprop_sign1_calibrated/:
  text sits 10-20% above the bubble's optical center; AND the model painted a ghost headline inside
  the reserved zone that the blind composite overlapped). Plan frame ≠ painted frame.
- THE FIX: after generation, MEASURE the painted image; patch any ghost text; composite anchored to
  the DETECTED free-space center, not the planned one.
- Working pieces to reuse: harness/cover_redraw.py (text-mask patching, proven on 5 signs),
  harness/composite_text.py (font resolution + compliance manifest + legibility guard),
  harness/scene_author.py (writes composite_spec.json with composited=true layers).
- Test asset: output/eventprop_sign1_calibrated/generated.png (has BOTH defects: ghost headline
  inside reservation + bubble interior lower than planned). Expected text: 守住钱袋子 / 护好幸福家.
- venv: .venv. OCR: install rapidocr-onnxruntime via `uv pip install --python .venv/bin/python
  rapidocr-onnxruntime` (deterministic, local, no API). Pillow/numpy already present.

## Part 1 — `harness/measure_canvas.py` (~150 lines, the sensor)
CLI: .venv/bin/python harness/measure_canvas.py --image IN.png --out report.json
  [--expected-text "守住钱袋子;护好幸福家"]
Produces a measurement report:
1. TEXT DETECTION (rapidocr): all text boxes w/ {text, bbox_frac, confidence}. Flag boxes whose
   text fuzzy-matches any --expected-text entry (these are GHOST headlines the model painted
   despite reservation) vs other text (footer etc. — leave alone).
2. CONTAINER GEOMETRY: detect the sign's container interior free space:
   - dominant container color mask (largest saturated connected region, e.g. AIA red bubble)
   - interior = container minus: detected text boxes, large icon/mascot masses (high-saturation
     blobs that aren't container color — e.g. gold mascot), and a margin inside container edges.
   - output: container_bbox_frac, interior_free_bbox_frac, optical_center_frac (centroid of the
     largest free rectangular region able to fit a given w×h — implement a simple max-rectangle
     or grid-scan; exact optimality NOT required, robustness is).
3. Output JSON: {text_boxes[], ghost_text_boxes[], container_bbox, free_space_bbox,
   optical_center, mascot_bbox?}. Honest nulls when detection fails (don't invent geometry).

## Part 2 — `harness/closed_loop_composite.py` (~120 lines, the actuator)
CLI: .venv/bin/python harness/closed_loop_composite.py --image gen.png --spec composite_spec.json
  --brand aia --out final.png
Flow:
1. Run measure_canvas (import, not subprocess) with expected-text = the spec's composited contents.
2. If ghost_text_boxes: patch them out via the cover_redraw text-mask approach (reuse/import its
   masking + local-bg fill; do NOT clip neighbors).
3. RE-ANCHOR: replace each spec layer's anchor_frac with positions derived from free_space_bbox:
   stack the N composited lines vertically centered on optical_center, preserving the spec's
   line order, size_px, and inter-line gap ratio (derive gap from original anchor_frac deltas).
   Clamp so text (at size_px + stroke) fits inside free_space_bbox; if it can't fit, shrink
   size_px proportionally (min 70% of original) and note it.
4. Composite via composite_text.py functions (keep compliance manifest + legibility guard —
   guard now checks contrast against the ACTUAL pixels behind each re-anchored line).
5. Write final.png + final.png.compliance.json + placement_report.json
   (planned vs detected anchors, ghost patches applied, any size shrink).

## Part 3 — integrate into scene_author.py
After generation, when the spec has composited=true layers: call closed_loop_composite instead of
the blind composite. Keep a --no-closed-loop escape hatch (old behavior) for A/B comparison.

## Part 4 — PROOF on the real defective asset (no new generation needed)
1. Run closed_loop_composite on output/eventprop_sign1_calibrated/generated.png with its existing
   composite_spec.json → output/eventprop_sign1_closedloop/final.png.
2. VERIFY (deterministic, in your report):
   a. measure_canvas on the NEW final.png: ghost_text_boxes for the expected headline = the
      composited text only (i.e. OCR finds 守住钱袋子/护好幸福家 ONCE each, not twice — no double/ghost).
   b. The composited lines' bbox center is within ±0.05 frac of the detected optical_center (x and y).
   c. Compliance manifest still licensed_exact (汉仪元隆黑-75简 per the spec's weight_hint).
   d. Pixel-diff ring check: patches didn't damage the mascot/container edges.
3. Also run the OLD blind path (--no-closed-loop) to output/eventprop_sign1_closedloop/blind_baseline.png
   for side-by-side. Report both.

## Honest reporting
Show: measurement report JSON (ghost boxes found, free-space bbox, optical center), placement_report
(planned vs detected anchors, shifts applied), verification results a-d with real numbers, both
output paths + sizes. If OCR misses the ghost text or the free-space detection is unstable, report
that plainly — detector reliability is exactly what we're evaluating. No hand-tuning.

## Conventions
Reuse existing functions by import where possible; don't duplicate masking/compositing logic.
Don't break existing CLIs. Keys not needed (no API calls except none). No git commits.
