# BUILD SPEC: Fix reserved-zone overpaint + legibility gate, re-run sign #1 clean

## Context (read first)
- Root-A chroma containment is PROVEN and working (output/chroma_sign1/: container_bbox clean,
  0 text px outside container, 0 green fringe — DO NOT re-litigate or rebuild containment).
- THE REMAINING DEFECT (one bug, two fixes): in output/chroma_sign1/preview_white.png the
  composited headline 守住钱袋子/护好幸福家 is centered + licensed-correct but BURIED under a
  RED RECTANGLE. gpt-image-2 painted a darker-red "headline plate" INSIDE the reserved blank
  zone; ghost-OCR didn't catch it (it's a SHAPE, not text), so the real headline composited
  under/behind it. verify_chroma.json wrongly reported overall_pass:true because no gate checks
  legibility/occlusion.
- Files: harness/scene_author.py (assemble_final_prompt — reserved-area block), 
  harness/measure_canvas.py (detect + reserved-zone analysis), harness/closed_loop_composite.py
  (compositing + the existing contrast legibility guard), output/chroma_sign1/* (the defective run).
- venv .venv; keys via dotenv ~/.hermes/.env.

## IMPORTANT — do NOT burn turns self-monitoring (this killed the last run)
Run any generation SYNCHRONOUSLY in the foreground via a single python script with its own
internal timeout (e.g. subprocess/openai call inside one `.venv/bin/python script.py` invocation
that blocks until done and prints results). DO NOT launch background processes and poll them.
DO NOT use a Monitor/poll loop. One blocking call, read the output, move on.

## Fix 1 — keep the reserved zone truly empty (prompt side)
In assemble_final_prompt's RESERVED HEADLINE AREA block (chroma/event-prop path), strengthen the
language so the model leaves the zone as BARE BASE FILL — no plate, no panel, no banner, no
darker rectangle, no container-within-container, no frame behind the headline. Explicit:
"Inside the reserved headline area render ONLY the flat base red fill — absolutely no rectangle,
plate, banner, box, panel, shadow, or shape of any different shade. The headline is added later
and must sit directly on the flat fill." Keep all other blocks intact.

## Fix 2 — detect + patch reserved-zone intrusions (deterministic backstop)
The prompt won't be 100% obeyed, so add a backstop in the measure/composite path:
- In closed_loop_composite, BEFORE compositing the headline, inspect the reserved zone (the
  free_space_bbox / planned reservation region) on the generated image: if it contains pixels
  whose color differs materially from the surrounding container base fill (i.e. a plate/panel
  was painted — detect by sampling the container's dominant fill color and flagging a connected
  region inside the zone that deviates > threshold in Lab/RGB distance AND isn't an icon/mascot
  hue), PATCH it: flood the reserved zone with the sampled base fill color (the same cover-redraw
  fill technique). This guarantees the headline lands on clean flat fill.
- Be conservative: only patch INSIDE the reserved/free-space region, never touch icons/mascot/
  footer/edges. Report how many px were patched.

## Fix 3 — legibility/occlusion gate (so this can never silently pass again)
Add to the verification (and to closed_loop_composite's guard) an OCCLUSION check that would have
caught this:
- After compositing, OCR the FINAL image for the headline text. The headline must be (a) detected
  by OCR at the expected location with good confidence, AND (b) its pixels must be the visually
  dominant mark there (high contrast vs immediate background, not covered). 
- Concretely: crop the headline region from the FINAL composite, OCR it — require each headline
  line is read back with confidence > 0.85. If a plate still occludes, OCR confidence drops /
  text missing → gate FAILS. Emit pass/fail per line + overall. This gate must be part of
  overall_pass (a buried headline => overall_pass:false).

## Re-run + verify (real generation, sign #1, foreground/blocking)
1. Regenerate sign #1 through the fixed chroma path (same args as the chroma_sign1 run; report
   whether you used the multi-panel ref or not — prefer WITHOUT, as the prior spec found it
   encourages full-bleed). Output to output/chroma_sign1_v2/.
2. Run ALL gates: a) chroma recovery clean, b) 0 text px outside container, c) centered ±0.06,
   d) licensed_exact, e) no green fringe, AND f) NEW occlusion/legibility gate (headline OCR
   confidence > 0.85 per line on the FINAL image).
3. VISUAL sanity: state plainly whether preview_white.png shows a clean, legible headline on
   flat fill with no plate. (You can't grade aesthetics, but you CAN confirm via the OCR-readback
   gate + reporting the reserved-zone patch px.)

## Honest reporting
Show: reserved-zone intrusion detected? px patched? the per-line headline OCR-readback confidence
on the FINAL image, all gates a–f with real numbers, and paths+sizes of generated/final/cutout/
preview_white. If the headline is still occluded, say so — do not report pass unless gate f passes.

## Conventions
Reuse existing helpers (cover-redraw fill, _max_rectangle, the contrast guard). Keep legacy paths
working. No background processes / no self-polling. No git commits. venv .venv.
