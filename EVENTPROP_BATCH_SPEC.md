# BUILD SPEC: Calibrated Register Rerun — AIA Signs #2–#5, Closed-Loop Composite

## Context (read first — everything is already built, this is an EXECUTION run + robustness test)
- The full pipeline now exists end-to-end and was proven on sign #1:
  calibration (register/calibrate_from_reference.py output already exists for the AIA ref) →
  derive_register (register/derive_register.py, --calibration) →
  scene_author (--register-profile, lock relaxation, event_prop → rounded font 汉仪元隆黑) →
  generate → CLOSED-LOOP composite (harness/closed_loop_composite.py: measure_canvas OCR ghost
  detection + patch + re-anchor to detected optical center + licensed compositing).
- Reference asset for sign #1 proof: output/eventprop_sign1_closedloop/final.png (all 4
  verifications passed). The 手举牌 subfields file: intents/aia_sign1_eventprop_subfields.json.
  The calibration: output/eventprop_sign1_calibrated/calibration.json (register_target 4/7,
  locks_flexed incl. logo omit, style_evidence from the real handoff ref).
- THIS RUN: produce the lively-register versions of signs #2–#5 (the client's actual remaining
  tasks), each through the IDENTICAL pipeline, and stress-test the closed-loop detector across
  4 different container geometries (it has only ever seen sign #1's bordered bubble).
- Intent files exist: intents/aia_sign2.json (远离非法金融，抵制高息诱惑), aia_sign3.json
  (珍惜一生血汗，远离非法金融), aia_sign4.json (金融传销+虚拟货币骗局 each crossed out 分别画叉),
  aia_sign5.json (非法集资+网络金融诈骗 each crossed out).
- Style ref image: /mnt/c/Users/Alecx/Downloads/aia real task.png (pass as --ref-image).

## Execution per sign (N = 2,3,4,5)
1. Reuse the SAME register derivation as sign #1 (same subfields semantics apply: 手举牌, held
   for photos, general public, event; logo omit) — derive once per sign or reuse the existing
   profile if derive_register is deterministic given identical inputs (it is; state which you did).
2. scene_author.py --brand aia --asset-profile flat_graphic
   --register-profile <profile> --intent-file intents/aia_signN.json
   --ref-image "/mnt/c/Users/Alecx/Downloads/aia real task.png"
   --out output/eventprop_signN/
   (closed-loop composite should run automatically per the Part-3 integration; if the
   integration routes differently, run closed_loop_composite.py manually on generated.png +
   composite_spec.json → final.png. State which route executed.)
3. SIGNS #4/#5 SPECIAL: the X-marks (分别画叉). The intent files mark them as mandatory
   special_elements. Two acceptable outcomes — (a) the model paints the X over reserved-zone-
   adjacent term blocks and the composited terms get re-anchored to sit under the painted X
   (verify visually the X still crosses the new text), or (b) terms + X both end up painted
   (not composited) — in which case ONLY composite what the spec marks composited=true and
   verify no double-render. Handle pragmatically, report what happened per sign. If the X ends
   up orphaned (crossing nothing), redraw it programmatically over the composited term (the
   cover_redraw X-redraw approach from the earlier batch).

## Verification per sign (deterministic, same as sign-1 proof)
a. OCR: each expected headline/term appears EXACTLY once in final.png (no ghost doubles).
b. Composited block center within ±0.05 of detected optical center (skip for layers that ended
   up painted-not-composited; say so).
c. Compliance manifest: every composited line licensed_exact (rounded family for this register).
d. Patch collateral: mascot/icon + container-edge ring changed pixels ≈ 0.
e. REGISTER CHECK (the client-facing one): blind-score each final.png on the Step-0 rubric
   (3 runs each via the existing register/blind_score.py if it supports arbitrary images, else
   one structured vision call per sign through the same anthropic pattern); report
   formality/playfulness per sign vs target (4/7 ±1.5) — i.e. confirm all four land in the
   lively register, not back in corporate.

## Detector robustness reporting (the secondary purpose)
Per sign, report: container shape the scene-author chose, whether measure_canvas's geometry
detection succeeded first try (container bbox / free space / optical center sane), any
detection failures or weird masks, and whether the borderless/odd-shape code path got exercised.
This is the first multi-geometry test of the sensor — failures are FINDINGS, not embarrassments.

## Honest reporting
Per sign: route executed, X-mark outcome (#4/#5), verifications a–e with real numbers, detector
robustness notes, final.png path + size. Overall: a 4-row summary table. No hand-tuning, no
forcing numbers. If a sign fails register or centering, deliver it anyway + diagnose.

## Conventions
venv .venv. Keys via dotenv ~/.hermes/.env (Anthropic for scene author + blind scores, OpenAI for
gpt-image-2). Sequential generation is fine (4 images, high quality). No git commits.
