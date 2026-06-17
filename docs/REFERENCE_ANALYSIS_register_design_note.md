# Design Note — Reference Analysis Layer + Register Inference (2026-06-11)

## Origin
Richard's team feedback on the 6 AIA signs: "好一些，但这些设计更贴近标识类。手举牌是活动时拿在
手上拍照的，需要灵动一些，亮眼，让参与活动的人愿意拿在手上拍照。" + 4 reference images of the
WANTED style (die-cut shapes, saturated playful color, bubbly white-stroke fonts, cartoon
icons/mascots, NO logo). Alec's deeper read: the refs should have influenced our INITIAL run;
we need a reference-analysis layer + a cross-check-ref-with-brand-DNA procedure. Critical
observation: the ref is STILL predominantly AIA red — brand DNA held, but ATMOSPHERE relaxed.

## The core insight: the DIFF (reference − brand DNA) IS the register
The reference is not "abandon brand." It's "brand DNA with selective relaxation," and it SHOWS
which dimensions flex vs hold. Cross-checking ref attributes against the answer key yields:
  - HELD dimensions (ref matches brand) → keep locked (e.g. color = AIA red).
  - FLEXED dimensions (ref diverges from brand) → these divergences are INSTRUCTIONS, not
    errors: logo absent → droppable; font bubbly → relax to rounded; shape die-cut → free;
    tone playful → register shift.
=> We do NOT need to hand-author register tables. The reference TEACHES the register,
empirically, per brand + per asset type. Generalizes to any brand / unfamiliar asset type
provided one good reference exists.

## Why we missed it (root cause, two parts)
1. WRONG QUESTION: our forensic vision pass asked "what does it LOOK like?" (colors/shapes/
   fonts) — never "what is this object FOR? who holds it, when, why? what makes someone want
   to grab it?" The 灵动/亮眼/grabbable quality lives in that second question. Atmosphere was
   in the pixels; we never pointed the question at it.
2. EXTRACTION WITHOUT AUTHORITY: the one atmospheric note ("playful-official hybrid") got
   dropped downstream — scene-author was primed "premium brand studio" + corporate locks, so a
   soft observation couldn't override hard priming. The register layer must carry AUTHORITY to
   relax locks, not just observe.

## Make the intangible FALSIFIABLE (Alec's standard)
Inferring "lively/grabbable" is a JUDGMENT, not an extraction — the fuzzy thing Alec distrusts.
So:
  STEP 0 (falsify the core assumption BEFORE building): show a VLM the 4 lively refs + our 6
  corporate signs, blind; ask it to score playfulness/energy/"would someone hold this for a
  photo." If refs score high + our signs low (matching Alec's eye) → inference is trustworthy,
  build the layer. If it can't discriminate → register must be HUMAN-SET, design different UX.
  One-hour test, gates the whole feature.

  IF it passes: output a STRUCTURED, inspectable register profile (not a hidden vibe):
    { formality, playfulness, energy, brand_anchors_held[], brand_locks_flexed[],
      social_function, inferred_register }
  Human eyeballs + corrects the profile BEFORE generation (calibration gate, same pattern as
  approval loop). Intangible → inspectable → falsifiable.

## Architecture
- Reference does DOUBLE DUTY: (a) upstream → analysis → register profile → conditions
  scene-author (NEW, with lock-relaxation authority); (b) downstream → visual exemplar to
  gpt-image-2 at generation (existing).
- RECONCILIATION LEVELED UP: we solved brief-vs-brand (lock lookup). This is REFERENCE-vs-brand.
  Rule: reference wins on register/atmosphere dimensions; brand wins on HARD identity (exact
  hex, licensed font FILES). Ref can say "go rounded" but can't invent a non-library font;
  can drop the logo but can't change the red.

## OPEN FORK — RESOLVED (2026-06-11, Alec)
Decision: reference PRIMARY, brief-occasion FALLBACK, human ALWAYS gets a calibration gate to
override. BUT the real fix came from Alec's deeper observation (below), which reorders priority.

## KEY REALIZATION (Alec): the brief intake was the actual failure point
The real run failed because: (a) brief text was just "手举牌" — too sparse; (b) even Alec (the
expert) would not have inferred the register from that; (c) Alec did not even comprehend the 4
attached reference images AS past examples / register-bearing — they were "just attached files."
=> If the human-in-loop didn't connect the dots, no downstream inference could. The fix belongs
at the INPUT layer, not the inference layer.

## Alec's idea: GUIDED SUBFIELDS on brief intake (now the PRIMARY register signal)
Prompt the user with pre-set subfields when they enter a brief: context, use/用途, vibe/语气
(fun↔official), logo-or-not, size, audience, etc. Why this beats pure inference:
- Scaffolds TACIT knowledge into EXPLICIT fields. Alec couldn't synthesize "event_prop register"
  from "手举牌", but he'd answer "用途? → held at events for photos / vibe? → fun" in 2 seconds
  WITHOUT needing the word "register." Human supplies cheap FACTS; system makes the designer's
  LEAP (facts → register). Neither does the other's job. = "automate judgment, not clicks."
- The FORM ITSELF TEACHES: asking "logo or not? vibe? use?" surfaces the dimensions that drive
  register, turning a human who "wouldn't have gotten it" into one who supplies the exact signal.
  The questionnaire is a thinking prosthesis.
- This IS tier-2 of brief_schema_v2.json (human intent), rendered as a GUIDED FORM not free text.
  Alec's idea didn't add a component — it gave the existing brief-intake layer its real shape.

## REGISTER: three input signals, priority order
1. SUBFIELDS (primary) — guided form, human-populated. Cheap, explicit, no design vocab needed.
2. REFERENCE DIFF (enriches) — when a ref exists, derive flex/hold map (ref − brand DNA). Catches
   nuance a form can't name ("predominantly red but softened").
3. BRIEF OCCASION (fallback) — bare-text inference when neither form nor ref present.
All three → one structured register profile → CALIBRATION GATE (human eyeballs/corrects) →
scene-author generates with lock-relaxation authority.

## CORRECTED FALSIFICATION (2026-06-12) — test the ONE legitimate reference, not post-hoc images
METHODOLOGY FIX (Alec): the handoff consisted of brief + ONE reference (`aia real task.png`,
= the 4-sign design sheet, byte-identical 150701b to screenshot-...332771). The 3 photos of
people holding props were sent by Richard AFTER our first run failed — post-hoc clarification,
and confounded (visible hands inflate "grab"). Honest question: could we infer register from
what we ACTUALLY HAD at handoff? Re-ran blind Step-0 on `aia real task.png` alone:
  REAL handoff ref:  playfulness 7, formality 6, logo N
  Our 6 corporate:   playfulness 2.8, formality 7.8, logo Y
  (contaminated people-photos: 7.5 / 4.75 — DO NOT use as target)
FINDING A: YES, register was inferable at handoff. Playfulness gap 7 vs 2.8 = 4+ pts on the
strongest axis, logo absent. Our failure was PROCESS (never analyzed the ref for register), not
missing signal. Reference-diff path validated on legitimate input.
FINDING B (the important one): our event_prop generation scored 8.0/3.0 — it OVERSHOT the real
target (7/6) into too-casual, because the subfield vibe sliders were hand-anchored to the
CONTAMINATED people-photos. CORRECT TARGET = playful~7, formal~6 ("approachable-official",
softened not abandoned — it's a public-safety PSA). DIVISION OF LABOR CONFIRMED: SUBFIELDS give
DIRECTION (playful, no logo); REFERENCE calibrates MAGNITUDE (how playful: 7 not 8; keep
formality 6 not 3). The "predominantly red but softened" nuance = the formality-6 reading.
ACTION: derive_register must not hardcode extreme sliders; when a reference exists, its blind
register score SETS the target coordinates (magnitude), subfields set direction. event_prop
default sliders should be moderated (formality ~5-6, playfulness ~7), not 2/8.

## Build order (revised)
- STEP 0 (still first): falsification test — can a VLM discriminate playful-prop vs corporate-
  sign on the 4 refs + our 6 signs? Gates the REFERENCE-DIFF path (signal #2).
- The SUBFIELDS path (signal #1) does NOT need the falsification test — it's structured fact
  collection, not fuzzy inference. Can build independently. Likely highest ROI + lowest risk.

## Status: DESIGN ONLY — not built. Next concrete step = STEP 0 falsification test.
Related: register feature (lock relaxation by asset register) from prior turn folds INTO this —
register is DERIVED (from ref diff or brief occasion), not hand-tabled.
Compliant-but-playful principle still holds: relaxed register picks a PLAYFUL LICENSED font
from the brand library (e.g. 汉仪圆隆黑 HYYuanLongHei, already in brands/aia/fonts/) — stays
font-compliant while looking lively. Logo becomes optional per register.
