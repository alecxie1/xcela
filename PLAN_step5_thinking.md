# PLAN: Step 5 — Field Coverage, Reproducibility, and Model-Mixing Architecture

_Written: 2026-06-05. Decision-oriented; not a reference doc._

---

## Question 1 — Field Coverage Completeness

### Analysis

Current answer keys cover 8 field groups. The evaluation framework (docs/) has a three-tier taxonomy. Here is a field-by-field verdict for everything NOT yet built:

| Field | Extraction route | Value for GPT Image 2 | Verdict |
|---|---|---|---|
| `spacing_specs` (clear-space mm, min-size px) | Text layer → regex on numeric + unit patterns | Low — GPT Image 2 ignores sizing constraints | **SKIP as extraction target; capture in schema as metadata-only** |
| `color_usage_roles` (primary / secondary / accent) | Already partially in colors array; upgrade role enum | Medium — guides generation color balance | **ADD** — cost is one enum field per color entry, already partially present |
| `imagery_style` (photography vs illustration, warmth, compositional mood) | VLM (like tone); unverifiable from text layer | **High** — directly feeds image generation prompts | **ADD as VLM/subjective field**, same treatment as tone |
| `logo_description` (structured checklist) | Already in answer keys as subjective rubric; needs formalization | Medium — more structured logo desc → better generation | **EXPAND** existing logo field into explicit elements list (icon shape, icon color, text arrangement) |
| `textures` | VLM; high variance; hard to verify without pixel comparison | Low-medium — GPT Image 2 handles texture via style prompts anyway | **DEFER** — not a blocker; add in v2 if generation quality is weak |
| `brand_discourse` (三才文化, 五道工序 narrative) | Text layer (when present); brand-specific; no generalizable extractor | Very low — GPT Image 2 won't process Chinese cultural philosophy into visuals | **SKIP** — over-engineering, does not generalize |
| `forbidden_color_combos` | Rare in PDFs; requires semantic parse of rule text | Very low for generation | **SKIP** — almost never printed explicitly; not worth an extractor |
| `typography_hierarchy` (H1/H2/body size ratios) | Text layer sometimes; VLM otherwise | Low — generation layer produces images, not set typography | **SKIP for now** — add only if you build a layout-generation layer |

### Recommendation

Add exactly **three things** to the schema:

1. `color_usage_roles` — upgrade each color entry from `{primary,secondary}` to `{primary, secondary_accent, secondary_neutral, background}`. Text-layer extractable from role headers in most VI manuals; VLM fallback.

2. `imagery_style` — a free-text + tag field (e.g., `{description: "warm documentary photography, natural light, earth tones", tags: ["photography","warm","natural"]}`). Scored subjectively; verified in bake-off. **This field has the highest leverage for generation quality.**

3. Formalize `logo_description` from a rubric blob into an explicit elements checklist: `{icon_shape, icon_colors, text_lockup, mono_variant_available}`. Scoring stays rubric-based; this makes the spec more useful to GPT Image 2.

Do NOT build extractors for spacing rules, brand discourse, or forbidden color combos. They are intellectually interesting but generation-irrelevant.

### What to do next

- [ ] Add `color_usage_roles` enum to both existing answer keys (one afternoon of work)
- [ ] Draft `imagery_style` entries for 太极堡 and 秀才弄 manually (these become ground truth)
- [ ] Restructure `logo` fields in both answer keys into the explicit elements checklist
- [ ] Update `score_v4.py`: `color_usage_roles` → exact/set scoring; `imagery_style` → bake-off only (subjective); `logo` elements → rubric with partial credit per element

---

## Question 2 — Reproducibility

### Two senses, separate problems

**2a. Run-to-run variance (VLM fields only)**

Deterministic fields (colors, text-layer fonts, motifs) have zero run-to-run variance by construction. The ~2pp spread you observed only affects VLM fields.

The ~2pp observation is currently anecdotal. To make it rigorous:

- Run the same PDF 5× through each VLM candidate at temperature=0
- Score each run against the answer key
- Compute per-field stddev; flag any field where stddev > 0.3 score points (on a 10-pt field scale)

If stddev is within noise (< 0.3 pts) at temp=0, the problem is solved. If it's not, use 3-sample majority voting on VLM fields — take the mode for categorical fields, the median for numeric, the highest-confidence response for prose. Do NOT run majority voting on text-layer fields; they're already deterministic.

**2b. Generalization to unseen brands**

n=2 with opposite failure modes is a good stress contrast but gives you exactly zero variance estimate. You need ~10 brands to claim generalization.

**Selection criteria for the golden set** — aim to span all of these axes:

| Axis | Needed variants |
|---|---|
| Text layer quality | Good (like 太极堡 main pages) / garbled (like 太极堡 p22) / absent (like 秀才弄) |
| Color spec format | Printed hex / Pantone-only / CMYK-only / RGB-only |
| Language | CN-only / EN+CN bilingual / EN-only |
| Brand category | F&B (covered) / retail / service / cultural/lifestyle |
| Palette complexity | 2-color / 4-color / 6+ color |
| Motif presence | With motif section / without |
| VI house style | International-style (grid, Helvetica) vs traditional Chinese vs mixed |

With 10 PDFs you can't span all combinations — aim for at most 3 overlapping per PDF. Priority: text-layer variety and color-spec variety, because those drive your two main extraction routes.

**The metric that says "it generalizes"**:

> Average score_v4 across all 10 brands ≥ B (75%) on objective_printed fields; no single brand below C (60%) on objective fields; stddev across brands ≤ 10pp.

The stddev cap is critical — a method that averages 80% but has one brand at 45% has a systematic failure mode you haven't found yet.

### What to do next

- [ ] Source 8 more brand VI PDFs (Chinese F&B / lifestyle brands with public VI manuals)
- [ ] For each, manually note: text-layer present? color spec format? language?
- [ ] Assign human-verified answer keys for objective fields only (colors + fonts + names + motifs); mark subjective fields as TBD
- [ ] Run 5× VLM benchmark on current 2 brands at temp=0 to get the actual variance number before assuming it's ~2pp

---

## Question 3 — Model-Mixing / Coherency Architecture

### Analysis

The worry ("does using Gemini in analysis weaken GPT Image 2 generation?") is real but the mechanism is more specific than it sounds.

The two layers communicate via **structured JSON, not shared embeddings**. This means:

**Model choice is completely irrelevant for objective fields.** A hex value `#D70321` is `#D70321` regardless of whether RapidOCR, Gemini, or NuExtract3 found it. Font name `方正标雅宋` is the same string. GPT Image 2 does not know or care which model populated the spec. Any model that achieves ΔE < 1 and exact string match is production-equivalent on these fields.

**Model choice matters for natural-language fields.** The fields that reach GPT Image 2 as prose are:
- `imagery_style.description`
- `logo_description.icon_shape` (if described in natural language)
- `tone.descriptors`
- Any other VLM-sourced text that becomes a generation prompt fragment

Here the phrasing and vocabulary choice could interact with GPT Image 2's interpretation. But the interaction is **second-order**: GPT Image 2 is a powerful image model trained on diverse natural language prompts. It does not have a "GPT-4V phrasing bias." The meaningful variation is whether the description is **accurate and specific**, not which model produced it.

Concrete claim: a description "温暖的大地色调，传统中国美食质感，摄影写实风格" vs "warm earthy tones, traditional Chinese food aesthetics, photographic realism" — the bilingual richness matters more than which model wrote it.

**Where model choice ACTUALLY matters in the bake-off:**

| What to test | Why |
|---|---|
| Description accuracy (existing score_v4 rubric) | Does model X correctly identify imagery style / tone / logo elements against the answer key? |
| Description specificity | Does model X produce vague ("modern Chinese aesthetic") or concrete ("warm amber + ink black, rustic handcraft feel, documentary photography") descriptions? |
| Generation quality downstream | Given model X's spec, does GPT Image 2 produce images that a human rates as "on-brand"? |

The third test is new and does not currently exist. **This is the under-specified gap.** "Generation quality" needs a rubric before the bake-off can be meaningful. Proposed 5-point rubric per generated image: (1) color palette match, (2) typography/style match, (3) motif/graphic presence, (4) overall brand feel, (5) photographic realism or illustration style per spec.

### Recommendation

**Architecture: keep the two-layer separation as-is.** Do not couple analysis and generation model choices. The JSON spec is the right interface.

**For the bake-off, run two rounds:**

Round 1 — Analysis quality: NuExtract3 vs Gemini vs Claude on the existing 2 brands. Score against answer keys using score_v4. Pay attention to VLM fields only (text-layer fields will tie). Winner: highest score on objective_visual + subjective fields at lowest latency/cost.

Round 2 — Generation quality: Take the NL-spec fragments from each model's Round 1 output (tone, imagery_style, logo_description). Feed each into a standardized GPT Image 2 prompt template. Blind-rate the resulting images using the 5-point rubric above. Winner: model whose NL descriptions produce the highest-rated images.

If Round 1 winner = Round 2 winner, the decision is easy. If they diverge (accurate descriptions produce worse images, or vice versa), that tells you the scoring rubric is misaligned with generation value — and you should re-weight answer-key scores to favor specificity over literal accuracy.

**One thing to watch for:** NuExtract3 (4B, self-hosted) may produce shorter/blunter NL descriptions than Gemini/Claude. Short descriptions are not always better for GPT Image 2 — test this explicitly.

### What to do next

- [ ] Write the 5-point generation quality rubric before the bake-off runs (this must be done first)
- [ ] Build a standardized prompt template that slots in spec fields: `{colors} | {tone} | {imagery_style} | {logo_description}` → GPT Image 2 prompt string
- [ ] Run both Round 1 and Round 2 for each model; build a comparison table
- [ ] If models tie on objective fields (expected), let generation quality be the tiebreaker

---

## Flags

**Over-engineering risks:**
- `brand_discourse` systems as extracted fields — never generalizes, low generation value, skip
- `forbidden_color_combos` — almost never machine-parseable from PDF rule text, skip
- Run-to-run variance study at n > 5 — 5 runs is enough to characterize stddev; don't over-invest here

**Under-specified gaps (fill these before building):**
- Generation quality rubric does not exist yet — the bake-off is meaningless without it
- "Generalizes" metric needs a numeric threshold commitment before sourcing PDFs (proposed: avg ≥ 75%, min ≥ 60%, stddev ≤ 10pp on objective fields)
- `imagery_style` field has no scoring type yet — add it to score_v4 as `subjective` (bake-off only) explicitly

---

## Single Recommended Next Action

**Write the generation quality rubric (5-point, per-image) and update the two existing answer keys to include `color_usage_roles` and `imagery_style` for 太极堡 and 秀才弄.**

This unblocks everything else: the bake-off (needs the rubric), the expanded scoring (needs the new answer key fields), and the PDF sourcing (you'll know what axes to prioritize once you see how hard `imagery_style` is to agree on for the existing 2 brands).
