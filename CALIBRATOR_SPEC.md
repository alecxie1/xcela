# BUILD SPEC: Reference Register Calibrator + Sign #1 Rerun at the TRUE Target

## Context (read first)
- docs/REFERENCE_ANALYSIS_register_design_note.md — esp. "CORRECTED FALSIFICATION (2026-06-12)".
- register/derive_register.py — the subfields→register_profile engine (built; traced rules).
  Its current event_prop sliders were anchored on contaminated post-hoc images → it OVERSHOOTS.
- KNOWN BASELINES (blind, Step-0 rubric: formality / playfulness, 0-10):
    our 6 corporate signs ≈ 7.8 / 2.8 (logo Y)
    REAL handoff reference `/mnt/c/Users/Alecx/Downloads/aia real task.png` = 6 / 7 (logo N)
    our first event_prop run (output/eventprop_sign1/) = 3.0 / 8.0 → overshot past the target
- THE PRINCIPLE TO IMPLEMENT: when a reference exists, the REFERENCE sets register MAGNITUDE
  (target coordinates); SUBFIELDS set DIRECTION (playful vs formal, logo or not). Without a
  reference, fall back to moderated register defaults (event_prop ≈ formality 5, playfulness 7
  — NOT 2/8).
- scene_author.py has --register-profile (lock-relaxation authority) from the previous build.

## Part 1 — `register/calibrate_from_reference.py` (~120 lines)
CLI: .venv/bin/python register/calibrate_from_reference.py --image <ref.png> --brand aia --out <dir>
1. BLIND-SCORE the reference on the Step-0 rubric via ONE Anthropic vision call
   (anthropic python pkg, model claude-opus-4-5, image attached base64; ask EXACTLY the Step-0
   format: FORMALITY/PLAYFULNESS/ENERGY/GRAB 0-10 + LOGO Y/N + TOP FEATURES ≤12 words; parse with
   regex; energy/grab recorded but NOT used for targets).
2. EXTRACT REGISTER-RELEVANT ATTRIBUTES in a SECOND structured vision call: dominant colors w/ hex
   estimates, shape language (die-cut/organic/rect), icon style (cartoon/flat/none), font feel
   (rounded/sharp/script), text effects (white stroke outline? shadow?), logo present.
3. CROSS-CHECK vs brand DNA (answer_keys/<brand>.json): for each dimension mark HELD (matches
   brand: e.g. dominant color ≈ AIA red #D31145 within reasonable distance) or FLEXED (diverges:
   logo absent, font rounded vs brand sharp...). This is the (reference − brand DNA) diff.
4. OUTPUT <out>/calibration.json:
   { "register_target": {"formality": N, "playfulness": N},      // FROM the blind score
     "anchors_held": [...], "locks_flexed": [...],                // FROM the diff
     "style_evidence": {shape/icon/font/effects/colors...},       // FROM call 2
     "logo_present_in_ref": bool,
     "_source_image": path, "_blind_score_raw": "..." }

## Part 2 — merge calibration into derive_register.py
- New optional arg --calibration <calibration.json>.
- When present: register_target REPLACES the rule-table slider defaults (subfields still decide
  direction/logo/strictness; conflicts trace plainly, e.g. subfields say logo omit + ref shows no
  logo → consistent). style_evidence merges into the profile hints (shape_language_hint etc. get
  CONCRETE evidence: "white-stroke outlined text" not just "cartoon style").
- Without calibration: moderate the built-in event_prop defaults to formality 5 / playfulness 7
  (fix the 2/8 overshoot defaults regardless).
- The derivation trace MUST show which source set each value (subfields vs calibration vs default).

## Part 3 — THE RERUN AT THE TRUE TARGET (falsifiable, end-to-end)
1. calibrate_from_reference.py --image "/mnt/c/Users/Alecx/Downloads/aia real task.png" --brand aia
   → expect register_target ≈ formality 6 / playfulness 7 (the model's blind read; accept ±1 —
   record what it actually returns, do NOT force 6/7).
2. derive_register.py with the SAME 手举牌 subfields as last run + --calibration → new profile.
   Verify trace shows magnitude from calibration, direction from subfields.
3. scene_author.py --brand aia --asset-profile flat_graphic --register-profile <new profile>
   --intent-file intents/aia_sign1.json --ref-image "/mnt/c/Users/Alecx/Downloads/aia real task.png"
   → output/eventprop_sign1_calibrated/generated.png
4. BLIND-SCORE the result (fresh vision call, Step-0 rubric).
   SUCCESS = lands within ±1.5 of the register_target on BOTH axes (i.e. ≈6±1.5 formality,
   ≈7±1.5 playfulness) — neither corporate (old 7.8/2.8) NOR overshot (last run 3.0/8.0).
   Report the trajectory: corporate → overshoot → calibrated, as three (formality, playfulness)
   points vs the target. Honest verdict; if it misses, diagnose (prompt authority too strong/weak?).

## Honest reporting
Show: calibration.json verbatim, the derivation trace, the blind score of the new image, the
trajectory table, verdict. No hand-tuning the image; no forcing expected numbers.

## Conventions
venv .venv; uv pip install --python .venv/bin/python for new deps. Keys via dotenv ~/.hermes/.env.
Keep all existing CLI behavior backward-compatible. No git commits.
