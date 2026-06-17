# Design Note — Reference as Primary Visual Channel (2026-06-13)

## Origin
Client sent the 定稿 (final used version) of the AIA 手举牌 signs. Alec's observation: the final
is "almost just an extension of the initial reference image" — same colors, fonts, icon style,
no logo, protruding-icon device; only the MESSAGE differs per sign. The ref had ~90% control over
the final. Alec's question: are we FEEDING refs to gpt-image-2 directly, or PARSING them to text?

## VERIFIED CURRENT STATE (read the code, don't trust memory)
- generate.py uses images.edit (CAN take multiple ref images).
- scene_author chroma batch was run WITHOUT --ref-image. With register logo:omit flexed + no ref,
  it hit the fallback (scene_author.py ~L933): fed the AIA LOGO as the reference image — the very
  logo the prompt forbids drawing.
- calibrate_from_reference parses the ref → style_evidence TEXT → register profile → prompt.
=> In the chroma runs, the style reference reached generation ONLY as a parsed text paraphrase;
   the image channel was wasted on a forbidden logo. We are in DESCRIBE mode for style, not FEED.

## CORE INSIGHT: we are violating our own proven law
DESCRIBE-vs-FEED law (proven on logos): feed real pixels → faithful; describe in words →
hallucinate (Taichi yin-yang → dragon when described). The STYLE reference obeys the same law.
Ground truth (final ≈ ref) says the ref should govern output nearly directly — yet we route it
through a lossy text paraphrase and waste the image slot. We're DESCRIBING the one thing we have
hard proof we should FEED.

## HONEST COUNTER-EVIDENCE (the necessary nuance)
The FIRST AIA runs DID feed the ref directly (image=[logo, ref]) and STILL came out 太标识类
(too corporate). Feeding alone was NOT sufficient. Why: TEXT PROMPT and IMAGE REF COMPETE, and
gpt-image-2 weights the text prompt heavily. The early prompt said "premium corporate brand
studio" → overrode the playful ref → prompt won.
=> LAW: feeding the ref is necessary but not sufficient — the PROMPT MUST NOT FIGHT THE REF.
   Two channels must point the same way.

## SYNTHESIS: aligned two-channel conditioning
- VISUAL channel (FEED, not describe): a SINGLE-PANEL CROP of the ref → gpt-image-2 style exemplar.
  Carries color/font/icon-style/protruding-icon device — what text cannot name.
- SEMANTIC channel (PARSE): scene-author picks WHICH icon per message (money bag=钱袋子,
  eyes=awareness, fist=resistance — selections the ref shows the STYLE of but not the CHOICE of),
  copy, hierarchy; register calibration makes the PROMPT AGREE with the ref (not fight it).
- THE UNLOCK = the CROP. The ref is a 4-PANEL contact sheet; feeding the whole grid made
  gpt-image-2 imitate "a grid" (full-bleed contamination — why direct-feed was dropped). A single
  cropped panel = "make ONE sign like this" = style signal without layout poison. Re-enables the
  visual channel without the regression that killed it.

## CAVEATS
1. NO-REF tasks still need the parse/register path — it's the floor. This enhancement is for
   ref-present jobs (common but not universal).
2. OVER-CLONING risk: too much ref-weight → photocopier. Good for "extend this campaign," wrong
   for "new campaign, vague mood ref." Ref-weight = a DIAL scaled by how much the task IS an
   extension of the ref, not a switch.
3. PROTRUDING-ICON vs CONTAINMENT tension: ref + final both have the hero icon BREAKING the card
   edge; our chroma containment forces everything INSIDE one blob. Fix: container-for-text-math
   ≠ silhouette-for-style. Feed a panel w/ protruding icon, imitate it; key composite math off
   the main card body only.

## FALSIFIABLE NEXT TEST (proposed)
Crop ONE panel from `aia real task.png`. Re-run sign #1 chroma WITH that panel fed as a style
exemplar AND an aligned (playful) prompt. Compare to the no-ref chroma version AND to the 定稿.
SUCCESS = the fed-crop version is visibly closer to the 定稿 (icon style, font, protruding device,
color discipline) than the parse-only version. If yes → ref becomes a first-class VISUAL input,
not just a parse source. If no → the parse paraphrase is good enough and the gap is elsewhere.

## STATUS: brainstorm/analysis only — NOT built. Reframes next-session priorities:
the ref-as-visual-channel test likely OUTRANKS the font-weight tweak, because the ref carries
the font/icon/size answer directly — feeding it may fix multiple gaps (font, icon style, size,
protruding device) in one move instead of tuning each deterministically.

## DECISIONS (Alec, 2026-06-13) — RESOLVED, ready to build next session
1. CROP IS NOT A BLOCKER: the human crops the ref to ONE panel before feeding (2-sec human job,
   same as a real designer would). Do NOT engineer auto-cropping. ("automate judgment, not clicks.")
2. FEED THE REF IMAGE DIRECTLY to gpt-image-2 (single cropped panel as style exemplar). Stop
   relying on the parsed-text paraphrase ALONE for style. This is the describe→feed law applied
   to style refs.
3. KEEP BOTH CHANNELS (guardrail — do NOT delete the parse path when adding image-feed):
   - VISUAL (fed image) = the LOOK: font, icon style, color, protruding-icon device.
   - SEMANTIC (parse/register) = the MEANING: which icon per message, copy, hierarchy, AND making
     the PROMPT AGREE with the ref. Early direct-feed failed (太标识类) because the corporate prompt
     FOUGHT the playful ref — feeding alone is necessary, not sufficient. Two channels, same direction.
4. OVER-CLONING → an INTAKE QUESTION (not a dial): ask the human "is this ref a TEMPLATE to extend /
   a STYLE to match / vague INSPIRATION (new campaign)?" Governance follows from the answer +
   the lock table (ref never overrides hard brand identity) + the crop (layout can't bleed).
   The AIA 定稿 = template-extension type → ~90% clone was CORRECT for that type.
   Add as a field tied to the reference_image input in the intake schema (brief_schema_v3).
