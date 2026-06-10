# Research Brief: Is NuExtract3 the Right ANALYSIS-Layer Model for the Brand-Asset Pipeline?

**Decision question:** Should we "just pick NuExtract3 and skip the 3-way bake-off" for the
ANALYSIS layer that emits Brand-DNA JSON consumed by GPT Image 2 — or do the subjective
visual fields warrant keeping a general VLM (Gemini / Claude) in the mix?

**One-line answer:** NuExtract3 is an excellent tool for the part of the pipeline we have
*already solved deterministically*, and a structural mismatch for the *only* part that
remains (open-ended visual interpretation). Do **not** make it the sole ANALYSIS model.

---

## 1. What It Is

| Attribute | Detail |
|---|---|
| **Model** | NuExtract3 — open-weight VLM specialized for document understanding |
| **Vendor** | NuMind (NuExtract.ai) |
| **Parameters** | 4B |
| **Base model** | Qwen3.5-4B |
| **Training objective** | SFT (next-token) → Reinforcement Learning for template adherence + extraction-specific reasoning |
| **Context window** | 131,072 tokens |
| **Max output (eval setting)** | Evaluated up to 65,000 output tokens (thinking + answer); typical answers ~1.8–2k tokens |
| **License** | **Apache 2.0 — truly open-weight, commercial-usable, no strings** |
| **Release date** | May 19, 2026 |
| **Reasoning** | Toggleable (`enable_thinking`); trained to use ~as many thinking tokens as answer tokens (vs 10× for generalists) |

**Version history**
- **NuExtract (v1, 2024):** Fine-tune of Phi-3-mini (3.8B), text-only, 2k-token input limit.
  Own model card: *"purely extractive, so all text output by the model is present as is in the original text."* This is the foundational design philosophy.
- **NuExtract-1.5 / -smol:** Multilingual, longer context, smaller variants. Still text→JSON.
- **NuExtract-2.0 (mid-2025):** First VLM generation. 2B/4B/8B on Qwen2-VL / Qwen2.5-VL. Native vision; introduced `string` (abstraction-allowed) vs `verbatim-string` (exact-copy).
- **NuExtract3 (May 2026):** Unifies structured extraction (→JSON) and content extraction (→Markdown/OCR). Qwen3.5-4B, RL-trained, reasoning toggle, 20 field types, template generation from natural language.

---

## 2. Capabilities

**Both core tasks:** structured extraction (text/image + JSON template + instructions → JSON) AND image-to-Markdown/OCR (with HTML tables, LaTeX).

**Schema handling (strong):** accepts a JSON template with typed leaves (`verbatim-string`, `string`, `integer`, `number`, dates, `country`, `currency`, `email`, enums, multi-enums, arrays); supports freeform instructions + few-shot; ships `convert_json_schema_to_nuextract_template`; returns null/[] when not found (anti-hallucination by design).

**Vision: native (Qwen-VL stack), no pre-OCR needed.**

**Chinese: claimed-and-plausible but UNVERIFIED for our doc class.** NuMind lists Chinese as supported; Qwen-VL base is strong at CJK OCR. But ALL published benchmarks are Latin-script business docs; no Chinese-specific number, no stylized/branded CJK typography eval.

---

## 3. Subjective / Semantic Fields — THE CRUX

NuExtract3 is the **wrong-shaped tool** for the remaining need:

1. **Design lineage is explicitly extractive** — "purely extractive, all output present as-is." Every version refines faithful value retrieval, not creative description.
2. **The `string` abstraction type ≠ visual interpretation.** It paraphrases info conceptually present in the document (summarizing existing text). It is NOT "look at a woodcut motif and infer 'rustic heritage tone'" — an aesthetic world-knowledge judgment with no literal source string.
3. **Corpus + metric optimize for literal fidelity.** 600-doc benchmark = invoices/receipts/forms/posters/floor plans/contracts. "EXTRA" metric (Levenshtein on string leaves, exact-match on typed leaves) rewards reproducing document values and would PENALIZE free-form interpretive prose.
4. **RL trained for template adherence + anti-looping**, the opposite of rich evocative description.

**Conclusion for our hardest fields** (`imagery_style`, `photography_style`, `tone`, `logo_appearance`): these are generative visual-interpretation tasks feeding GPT Image 2, requiring art/design vocabulary, aesthetic judgment, fluent prose. NuExtract3 is specifically trained to SUPPRESS that in favor of grounded extraction. A 4B distilled-to-terse model is structurally disadvantaged here vs a large general VLM.

---

## 4. Self-Hosting Reality

| Aspect | Detail |
|---|---|
| **VRAM** | 4B bf16 ≈ 8–9 GB; fits 12–16 GB consumer GPU; quantized (GGUF/AWQ) fits 8 GB |
| **Serving** | First-class vLLM; HF Transformers (AutoModelForVision2Seq, FA2); optional MTP speculative decoding |
| **Settings** | Prod: enable_thinking=False, temp ≈ 0.2. Thinking (temp ≈ 0.6) only for hard layouts |
| **Quantization** | Community GGUF; llama.cpp limitation: --mmproj (vision) incompatible with spec-decode draft-mtp |
| **Hosted API to test first** | YES — NuExtract Platform API + free HF Space (spaces/numind/NuExtract-3-4B) |
| **API cost** | ~$5/M tokens (v2.0 PRO: $1/M in, $5/M out; pixels 28×28/token) |

Trivially self-hostable and cheap to trial. Feasibility is NOT the question — fit is.

---

## 5. Benchmarks (ALL self-reported; public leaderboard "coming weeks", not yet available)

Structured extraction (internal 600-doc, EXTRA metric, 0-shot):

| Model | Score | Failed | Avg Thinking Tokens |
|---|---|---|---|
| **NuExtract3 (4B)** | **0.651 ± 0.019** | 27 | 2,036 |
| gemma-4-E4B-it | 0.538 | 31 | 3,005 |
| Qwen3.5-9B | 0.479 | 170 | 22,409 |
| GLM-4.6V-Flash | 0.435 | 153 | 2,989 |
| Qwen3.5-4B (base) | 0.417 | 229 | 27,177 |
| Ministral-3-3B | 0.240 | 344 | 27,586 |

Beats a 9B at <half size — real domain fine-tune win. OCR judged by Gemini-as-LLM-judge.

**Critical gap:** NO head-to-head vs Gemini Flash/Pro, Claude, GPT-4o on extraction. Comparisons are open-weight peers only. "Displaces closed APIs" = vendor positioning, not measured. ZERO benchmark touches subjective fields or Chinese docs.

---

## 6. Limitations / Red Flags

- Benchmarks self-reported, self-selected (open-weight peers only; OCR scored by a competitor's model — mild circularity).
- **No evidence of subjective/aesthetic description capability** — decisive for our use case.
- No Chinese-specific numbers; no stylized brand-typography eval.
- Reasoning hurts small models (repetition loops); they default to non-thinking.
- 4B world-knowledge ceiling — naming niche art/photo styles leans on broad pretraining a 4B specialist lacks.
- Tooling rough edges (llama.cpp vision + spec-decode incompatibility).

---

## 7. Verdict

**"Just pick NuExtract3 and skip the bake-off" is NOT defensible — because NuExtract3 is the wrong tool for the only job we have left.**

- **Objective fields** (hex, fonts, slogans): ALREADY SOLVED deterministically at ΔE=0. NuExtract3's core strength is the thing we no longer need.
- **Subjective fields**: the ONLY remaining VLM job — open-ended visual interpretation feeding an image generator — precisely what NuExtract3 is trained to suppress. A frontier general VLM (Gemini/Claude) excels at exactly this.

**Recommendation:** Keep a general VLM for subjective fields; do NOT adopt NuExtract3 as sole/primary model. The "bake-off" collapses from 3-way to a narrow **2-way: which general VLM (Gemini vs Claude) writes the best art-direction prose for GPT Image 2** — a quick, cheap eval worth doing on real VI manuals. NuExtract3 = optional cheap JSON-coercion/literal-CJK utility, not the brain (and largely redundant given deterministic OCR already nails objective fields). Don't let "Apache-2.0 + self-hostable + 4B" decide an interpretation problem.

---

## Bottom Line

NuExtract3 is a strong, cleanly-licensed, cheaply self-hostable 4B VLM that beats larger open models at faithfully extracting values literally present in a document — exactly the capability we already solved deterministically. Our one remaining VLM job is the opposite: open-ended, world-knowledge-heavy visual interpretation that feeds an image generator, and NuExtract3 is designed/trained/benchmarked to suppress that. So "just pick NuExtract3" is the wrong call — not because it's bad, but because it's optimized for the solved half and mismatched to the unsolved half. Keep a general VLM (Gemini or Claude) for subjective fields; run a quick 2-way prose-quality comparison on real Chinese VI manuals.

**Confidence: High (~85%)** that NuExtract3 is mismatched to subjective visual description (follows from its extractive design, training objective, benchmark metric). **Moderate (~60%)** on Chinese-VI OCR quality (claimed, unbenchmarked for CJK/stylized type) — worth a quick empirical check IF used for any literal extraction.

### Sources
- about.nuextract.ai/blog/nuextract-3-release
- HuggingFace: numind/NuExtract3, numind/NuExtract-2.0-4B, numind/NuExtract (v1)
- documentation.nuextract.ai (languages, pricing)
- numind.ai/blog/nuextract-a-foundation-model-for-structured-extraction
- 7minAI coverage; r/LocalLLaMA & r/MachineLearning (via search); github.com/numindai/nuextract
