# BUILD SPEC: Register Derivation Engine + Lock Relaxation + Falsifiable Proof

## Context (read first)
- docs/REFERENCE_ANALYSIS_register_design_note.md — full rationale.
- brief_schema_v3.json — the 4-bucket guided-subfields schema (artifact/use-context/content/tone+brand).
- Step-0 falsification (just ran) PASSED: a VLM discriminates register on PLAYFULNESS+FORMALITY
  (energy dropped as decoy; grab is the target outcome). Our 6 AIA signs scored playful≈2-4 /
  formal≈7-8; the 4 client reference props scored playful≈7-9 / formal≈3-5. The client wants the
  lively register; we delivered corporate. THIS BUILD makes the tool able to hit the lively register.
- scene_author.py (extended: --asset-profile, --style-notes, --intent-file, container_shape +
  text_graphic_hierarchy tier-3 fields, font_role selection from answer-key typography).
- answer_keys/aia.json — typography block; brands/aia/fonts/ has the licensed library INCLUDING
  HYYuanLongHei75W.ttf (汉仪圆隆黑, a ROUNDED gothic) and HYYakuHei-85W (sharp). index.json maps them.
- Principle: human supplies cheap FACTS (subfields); SYSTEM makes the designer's LEAP (register).
  Compliant-but-playful: relaxed register picks a PLAYFUL LICENSED font (圆隆黑), not a generic one.

## Part 1 — `register/derive_register.py` (the judgment engine, ~150 lines)
Pure function: subfields dict (bucket B + D mostly) + brand answer_key -> register_profile.
Input example (what a human WOULD have entered for the 手举牌 job):
  {"asset_type": "手举牌 hand-held event sign", "usage_context": "held for photos / posed with",
   "audience": "general public", "setting": "event / festival",
   "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
   "logo_treatment": "omit", "brand_strictness": "expressive departure"}
Output register_profile:
  {"inferred_register": "event_prop",
   "formality": 2, "playfulness": 8,
   "brand_anchors_held": ["primary_color"],        // what stays locked even when playful
   "brand_locks_flexed": ["logo:omit", "font:rounded", "shape:die-cut", "palette:playful-accents"],
   "font_role_hint": "rounded display",             // -> resolves to 圆隆黑 not 雅酷黑
   "shape_language_hint": "die-cut organic (speech bubble / burst / cloud), thick white stroke outline",
   "icon_style_hint": "cartoon/emoji-style, mascots, exaggerated",
   "tone_hint": "playful, energetic, grabbable photo-prop",
   "_derivation_trace": [ "usage_context=held-for-photos => event_prop base", ... ]}
DERIVATION RULES (deterministic, transparent, every decision traced):
- register tier from (usage_context + formality + playfulness): held-for-photos / low-formality /
  high-playfulness => event_prop; wall-posted / mid => marketing; handed-out formal / high-formality
  => formal. Use a small rule table, not an LLM (this must be inspectable + falsifiable).
- brand_anchors_held: ALWAYS keep primary brand color unless brand_strictness=expressive AND a
  reference says otherwise. (Client kept AIA red even in playful refs — anchor.)
- brand_locks_flexed derived from logo_treatment (omit->logo flexed), register (event_prop->shape
  die-cut + font rounded + palette accents).
- font_role_hint maps register->family role: event_prop->"rounded display"; formal->"sharp display".
  composite/scene_author resolves "rounded display" to the rounded licensed family via the answer-key
  typography + font index (圆隆黑 / HYYuanLongHei). Add a "style" tag to answer_keys/aia.json
  typography entries so rounded vs sharp is selectable: tag HYYuanLongHei as style:"rounded",
  HYYakuHei as style:"sharp/neutral". (Inspect the index; add a styles map.)
Write a register_profile.json to an out dir. Print the derivation trace.

## Part 2 — scene_author.py: accept a register profile + RELAX LOCKS
- New arg --register-profile <path>. When present, the meta-prompt gains a REGISTER DIRECTIVE block:
  the asset's register, what's held vs flexed, and EXPLICIT permission/instruction to depart from
  corporate defaults along the flexed dimensions (die-cut shapes, cartoon icons, rounded font,
  playful accent palette, drop logo) WHILE keeping anchors (AIA red).
- CRITICAL: this must carry AUTHORITY. Today scene_author is primed "premium brand studio" + locks.
  When register=event_prop, OVERRIDE that priming: prime as "fun event/experiential designer",
  instruct die-cut organic shapes + cartoon mascots + bubbly rounded type + white-stroke outlined
  text + saturated playful palette anchored by the brand color. logo omitted if flexed.
- font selection honors font_role_hint: event_prop -> rounded display -> 圆隆黑. Surface in tier3
  text_layout weight/role.
- Keep existing behavior intact when --register-profile absent (back-compat: all prior runs work).

## Part 3 — THE FALSIFIABLE PROOF (end-to-end, real generation)
1. Hand-write the subfields dict above (the 手举牌 facts) to intents/aia_sign1_eventprop_subfields.json.
2. derive_register.py -> register_profile.json. Verify inferred_register=event_prop, font=rounded.
3. scene_author.py --brand aia --asset-profile flat_graphic --register-profile <profile>
   --intent-file intents/aia_sign1.json (headline 守住钱袋子护好幸福家)
   --ref-image "/mnt/c/Users/Alecx/Downloads/aia real task.png"
   -> output/eventprop_sign1/generated.png
4. BLIND-SCORE the result on the SAME Step-0 rubric (formality/playfulness/grab, 0-10) via a fresh
   vision call. SUCCESS CRITERIA: playfulness >=6 AND formality <=5 — i.e. it now clusters with the
   client refs (7.5/4.75) instead of our old corporate signs (2.8/7.8). Report the scores vs both
   group means. If it does NOT cross over, say so plainly — that is a real finding about whether
   lock-relaxation actually moves register.
5. Note honestly: headline may be AI-painted in this run (compliance compositing is a separate,
   already-built step). Focus the grade on REGISTER (shape/color/icon/tone), not font compliance.

## Honest reporting
Show: the derivation trace, the register_profile.json, the blind scores of the new image vs the two
group baselines, and an honest verdict on whether subfields->register->relaxation closed the gap to
the lively target. Do not hand-tune the image. If lock-relaxation under-shoots (still too corporate),
diagnose why (priming not strong enough? palette anchor too dominant?).

## Conventions
venv .venv; uv pip install --python .venv/bin/python for deps. Keys via dotenv ~/.hermes/.env.
New code under register/; do not break existing scene_author/composite behavior. No git commits.
