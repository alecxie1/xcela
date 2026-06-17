# BUILD SPEC: mandatory_overlay primitive (X-marks generalized) + #3 dup-text fix

## Context (read first)
- Chroma-key event-prop pipeline is PROVEN clean on signs #1, #2 (output/chroma_sign1_v2,
  output/chroma_sign2). Batch result: #2 clean, #5 mostly (X=splatter), #3 + #4 defective.
- TWO fixes, both at the COMPOSITE stage (harness/closed_loop_composite.py + measure_canvas.py):
  FIX A (generalizes — a real tool primitive): "mandatory_overlay" — a graphic element that must
    be drawn OVER a specific composited text span. X-marks (分别画叉) are ONE instance. Build the
    PRIMITIVE, not an AIA X-mark special case.
  FIX B (general bug): #3-style DUPLICATE/GHOST decorative text — the model painted a second,
    differently-COLORED copy of the headline (e.g. yellow dup over the white headline). The
    current ghost-patcher only catches same-zone matches; it misses a recolored duplicate
    elsewhere. Generalize ghost detection to catch ANY OCR box whose text matches a composited
    headline, regardless of color/position, and patch it.
- Files: harness/closed_loop_composite.py, harness/measure_canvas.py (OCR + geometry),
  harness/cover_redraw.py (has an X-redraw stroke routine from the pre-chroma batch — reuse).
  Intent schema: intents/aia_sign4.json / aia_sign5.json mark fraud terms as special_elements.
- venv .venv; keys dotenv ~/.hermes/.env. NO background processes / NO self-polling (turn-burn).
  Run generation as ONE synchronous blocking python call.

## Part 1 — generalize the intent → composite_spec: mandatory_overlay
Extend the composited-text spec so a text layer can carry an overlay directive:
  {"content":"金融传销", "font_role":..., ..., "composited":true,
   "mandatory_overlay": {"type":"cross_x", "color":"#D31145", "stroke_frac":0.06,
                          "style":"bold_round", "coverage":"span"}}
- type vocabulary (extensible): "cross_x" (two diagonal strokes crossing the span),
  later "circle", "underline", "badge" — build cross_x now, leave the dict open.
- scene_author/intent-mapping: when intent special_elements says a term must be 画叉/crossed,
  emit that term as a composited layer WITH mandatory_overlay type=cross_x. (For aia_sign4/5 the
  two fraud terms each get their own cross_x overlay. The 拒绝欺诈 headline does NOT.)

## Part 2 — render mandatory_overlay AFTER text composite (closed_loop_composite.py)
- After a composited text layer is drawn at its re-anchored position, if it has
  mandatory_overlay, draw the overlay OVER that layer's actual rendered bbox:
    cross_x → two thick diagonal strokes (rounded caps) spanning the text bbox + ~8% padding,
    color from the directive, width = stroke_frac * bbox_height. Must visibly cross the glyphs.
- Sample the X color from the directive (not the image) so it's deterministic. If multiple
  overlay terms, each gets its own X over ITS span (the 分别 = "separately" requirement).
- Re-run the occlusion gate AFTER overlays: the term text must STILL read back (an X crossing
  it is fine — OCR of a crossed term should still match > 0.6; tune threshold so a crossed-out
  term passes but a buried/garbled one fails). Report per-term.

## Part 3 — FIX B: catch recolored duplicate headline text
In measure_canvas detect_text / the ghost logic: currently ghosts = OCR boxes matching expected
text. Confirm this ALREADY catches a recolored duplicate (it should — match is on TEXT not color).
The #3 failure was likely that the duplicate sits OUTSIDE the reserved zone so it wasn't patched.
FIX: patch EVERY ghost box that matches a composited headline, wherever it is (not just inside the
reserved zone), EXCEPT the one we intend to composite over. Concretely: of all OCR boxes matching
headline line L, keep none painted — patch them all, then composite the licensed L once. Verify
the final OCR finds line L exactly ONCE.

## Part 4 — re-run #3, #4, #5 (the three that weren't clean), verify
Re-run each through the fixed pipeline (same args as the batch; sign #2 already clean, skip).
Per sign, verify + REPORT real numbers:
  a. contained / not full-bleed (chroma container_bbox inside [0.02,0.98])
  b. occlusion gate: every composited line/term reads back (crossed terms pass if still matchable)
  c. #3 specifically: headline appears EXACTLY once (no yellow dup) — OCR count per line == 1
  d. #4/#5: BOTH fraud terms present + EACH has its own X crossing it (report X bbox vs term bbox
     overlap; each X must overlap its term's center)
  e. licensed_exact compliance; no green residual
Then VISUAL self-check note per sign (you can't grade aesthetics, but confirm via OCR-count +
overlap-geometry + readback numbers).

## Honest reporting
Per sign: what was wrong, what the fix changed, verifications a-e with real numbers, final
preview_white.png path+size. If X still lands wrong or dup persists, say so + diagnose. Don't
hand-edit images. The goal is the PRIMITIVE working, proven on these 3 signs — not a one-off.

## Conventions
Reuse cover_redraw's stroke routine + existing patch/composite helpers. Keep non-overlay specs
working unchanged. venv .venv. No git commits. No background/self-poll.
