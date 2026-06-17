# Design Note — Font Intelligence (Layer 2: Selection) — 2026-06-11

## Trigger (Alec's critique of the first composite, all three points confirmed)
The font-compliance proof (final.png, Pillow+SimHei) looked NOTICEABLY WORSE than the all-AI
version: (1) font too thin — wrong register for a call-to-action sign; (2) too much negative
space; (3) graphics bleeding/edging out of the signage.

## Root cause (one sentence)
Type treatment is a Tier-3 DESIGN decision and we let it bypass the scene-author — the
headline spec (font/weight/size/position) was written mechanically, and the blank-area
generation designed a composition WITHOUT its protagonist (text), so graphics drifted and
space went dead. Same class of mistake as hand-writing prompts: rendering automated,
judgment not.

## The three-layer font architecture
1. EXTRACTION (built 6/11): VI → answer-key typography block with VI-declared roles
   (主要/系统/数字平台/标题/正文), license notes, usage rules, per-page provenance.
2. SELECTION (THE GAP — this note): which font role, weight, size for THIS occasion and
   THIS text layer. Owner: scene_author. Mechanism:
   - tier-3 text_layout entries gain: font_role (MUST be one of the answer key's roles),
     weight (from the family's available weights), case/treatment.
   - Scene-author chooses FROM the VI's vocabulary, never invents fonts.
   - Occasion drives register: call-to-action sign → heaviest display weight;
     premium poster → lighter elegant face; body/footer → system/digital role.
   - Primary + secondary in the same material = per-layer role assignment (headline
     chinese_primary heavy, footer digital regular) — falls out of the schema naturally.
   - VI rules (e.g. 友邦红背景上的正文应选择白色字体; 不建议使用手写字体) become validation
     constraints on the scene-author's choices.
3. RENDERING (built): composite_text.py resolves font_role→file via answer key, draws.

## Fix for negative-space + bleeding (same build)
Scene-author authors the blank reservation FROM its own text plan (it knows: 2 lines × 5
chars × 160px heavy = reserve exactly that box), instead of prompt-level "leave a big empty
area". Composition is then designed around a correctly-sized protagonist.

## Alternative compositing strategy to A/B test (flat graphics only)
COVER-AND-REDRAW: let gpt-image-2 render look-alike text (composition stays coherent — text
and graphics negotiate space), then compositor detects headline bbox, patches with flat local
bg color, redraws real font same position/size. Flat design = solid bg behind text → patch is
nearly artifact-free. Hypothesis: preserves the AI version's superior composition AND delivers
real-font compliance. Test head-to-head vs improved blank-reservation.

## Weight availability gotcha
A single .ttf (e.g. SimHei) has ONE weight. Real brand families (汉仪旗黑 55s-95s, Everest
Thin→Bold) ship as multiple files. Answer-key typography entries need a weights map
({"55s": path, "75s": path, ...}) once brand files arrive; until then weight requests
degrade to stroke_width simulation in Pillow (crude) or the single available file + honest
note. Surface this in the materials ask: request the FULL weight range of each family.

## Status
- Captured as the next scene_author build after the extraction layer lands.
- NOT built yet. Blocked on nothing technical — just sequencing.
