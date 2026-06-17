# Register Engine — Falsifiable Proof Result (2026-06-12)

Spec: REGISTER_ENGINE_SPEC.md. Built: register/derive_register.py (deterministic, traced),
register/blind_score.py (Step-0 rubric scorer), scene_author.py --register-profile (lock-relaxation
authority), answer_keys/aia.json typography.styles map (rounded=汉仪元隆黑 / sharp=汉仪雅酷黑).

## Run
subfields (intents/aia_sign1_eventprop_subfields.json: 手举牌, held-for-photos, vibe 2/8/7, logo omit)
→ derive_register → event_prop, anchors=[primary_color], flexed=[logo:omit, font:rounded,
shape:die-cut, palette:playful-accents], font resolved to brands/aia/fonts/HYYuanLongHei75W.ttf
→ scene_author --register-profile → output/eventprop_sign1/{generated,final}.png.
Headline composited licensed_exact ×2 with 汉仪元隆黑-75 (rounded). Tier-3 validation clean first pass.

## Blind scores (Step-0 rubric, 3 fresh vision calls each, claude-opus-4-5)
| group                      | playfulness | formality | grab |
|----------------------------|------------:|----------:|-----:|
| client refs (baseline)     | 7.5         | 4.75      | —    |
| our 6 corporate signs      | 2.8         | 7.8       | —    |
| NEW final.png (mean of 3)  | **8.0**     | **3.0**   | 6.0  |
| NEW generated.png (pre-composite) | 8.0  | 3.0       | 7.0  |

SUCCESS CRITERIA playfulness>=6 AND formality<=5: **PASSED — full crossover.** The new sign
clusters with (slightly beyond) the client refs and is ~5 points away from our corporate signs
on both axes. Zero per-call variance (3×3/8 on final, 3×3/8 on generated).

## Honest notes
- Image not hand-tuned; single generation, first attempt.
- Headline font IS compliant in final.png (composited with the real rounded licensed file) —
  but per spec the grade is REGISTER (shape/color/icon/tone), which the pre-composite
  generated.png also passes identically.
- grab (the target outcome) = 6–7: grabbable but not at ceiling; scorers noted the financial
  footer text tempers grab. Possible next lever: white-stroke outlined headline (refs have it;
  our composite renders plain fill).
- Caveat: blind scorer is the same model family that authored tier-3 (different call, no shared
  context, image-only input). Step-0 baselines came from the same rubric, so the comparison is
  internally consistent.
