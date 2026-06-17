# Reference Register Calibrator — Rerun at the True Target (2026-06-12)

Spec: CALIBRATOR_SPEC.md. Built: register/calibrate_from_reference.py (blind Step-0 score +
style-evidence extraction + brand-DNA cross-check → calibration.json), derive_register.py
--calibration (reference sets MAGNITUDE, subfields set DIRECTION, every value's source traced;
no-calibration event_prop defaults moderated to 5/7), scene_author.py register-target line
(gated on _slider_source — old profile files render byte-identically).

## Run (all real API calls, nothing forced)
1. calibrate_from_reference.py on `/mnt/c/Users/Alecx/Downloads/aia real task.png`:
   blind score FORMALITY 4 / PLAYFULNESS 7 / ENERGY 7 / GRAB 5 / LOGO N.
   NOTE: spec expected ≈6/7 from the corrected-falsification read; the model returned 4/7.
   Recorded as-is per honest-reporting rule.
   Cross-check: primary_color HELD (#8B2332 ≈ #D31145, ΔRGB 77); logo/font/shape/icon/
   text_effects all FLEXED — matches the design-note diff exactly.
2. derive_register --calibration: trace shows MAGNITUDE from calibration (4/7), DIRECTION from
   subfields (event_prop, logo:omit — "subfields say logo omit + ref shows no logo => consistent"),
   style_evidence merged into hints as concrete REFERENCE EVIDENCE strings.
3. scene_author → output/eventprop_sign1_calibrated/{generated,final}.png. Headline composited
   licensed_exact ×2 (汉仪元隆黑-75). Tier-3 validation clean first pass.
4. Blind score of final.png (3 calls, zero variance): formality 3.0 / playfulness 8.0 / grab 6.0.

## Trajectory (formality, playfulness)
| point                                        | formality | playfulness |
|----------------------------------------------|----------:|------------:|
| corporate (6 signs, baseline)                | 7.8       | 2.8         |
| overshoot (eventprop_sign1, uncalibrated)    | 3.0       | 8.0         |
| calibrated (THIS run)                        | 3.0       | 8.0         |
| register_target (calibration, this session)  | 4         | 7           |
| historical read of same ref (design note)    | 6         | 7           |
| same-day re-read of ref, 3× (diagnostic)     | 3.0       | 7.0         |

## Verdict
- By the spec formula (within ±1.5 of register_target on BOTH axes): **PASS** — |3−4|=1.0,
  |8−7|=1.0. Also within ±1 of where TODAY's scorer places the reference itself (3.0/7.0).
- By the spec's parenthetical expectation (6±1.5 formality): **MISS** — formality 3 vs 6.
- Honest reading: the pass is weak evidence. The image score is IDENTICAL to the uncalibrated
  run (3.0/8.0) — this generation was not measurably moved by calibration; the criterion was
  met because the measured target (4/7) sat lower than the historical 6/7.

## Diagnosis
1. CALIBRATOR VARIANCE ON FORMALITY: the same reference reads formality 6 (earlier session) vs
   4 (calibrator, Step-0 text format) vs 3.0×3 (JSON rubric, today). Playfulness is stable at 7
   across all reads. The formality axis of this ref is scorer-session-dependent; a single-call
   calibration inherits that noise. Fix candidate: calibrate from the MEAN of n≥3 blind calls.
2. PROMPT AUTHORITY THRESHOLD: the register-target line only adds the "soften, don't abandon
   official" qualifier at formality ≥5. Target 4 didn't trigger it, so the prompt stayed
   full-playful (same priming/opening as the overshoot run) → same 3/8 outcome. Had the
   calibration returned 6, the directive would have changed materially — untested this run.
3. COMPOSITE DEFECT (orthogonal to register): gpt-image-2 rendered the headline INSIDE the
   reserved blank zone, so the composited licensed text overlaps a ghost headline in final.png.
   Reservation enforcement at generation time is not reliable; needs a post-gen blank-zone check
   (same family as check_reservation_legibility) + regenerate-or-inpaint.

## What is proven vs not
- PROVEN: the pipeline plumbing — calibration measured, magnitude/direction split traced,
  evidence merged, target line reaches both the authoring prompt and the image prompt.
- PROVEN: no-calibration event_prop defaults now 5/7 (overshoot default fixed, traced).
- NOT proven: that a calibrated magnitude actually steers the generated register away from
  the priming — the one configuration that would test it (target formality ≥5) didn't occur
  because the calibrator read 4. Next falsifiable step: stabilize the calibrator (mean of 3),
  and if it then reads ≥5, rerun and check the image moves off 3/8.
