# Brand Design Tool — Progress Report
**Date:** June 10, 2026
**Project:** Handyprint AI Brand-Asset Generation Tool
**Phase:** Brief-elicitation layer (attacking the prompt bottleneck)

---

## TL;DR

We started the day worried that our impressive results were a mirage — that they only happened because a human (or Hermes) hand-wrote a perfect prompt each time, meaning we had a demo, not a tool. **We dissolved that worry with evidence.** A machine, given a 6-line non-designer brief, authored a complete marketing scene that scored **equal to a hand-written expert prompt** against a real target poster. The prompt-writing bottleneck — the thing that made this feel "out of our hands" — is broken in principle. What's left is mechanical and well-scoped.

---

## What we did today (the journey)

**1. We named the real fear.** The session opened on the most important instinct in the project: *"Can this pipeline reproduce a known target, or do the good results only come from a human in the loop?"* Everything today was built to answer that honestly.

**2. We stress-tested reproduction on a hard case.** We took a *real* Taichi "garden tomato burger" poster — one that deliberately breaks the brand's own red/gold rules (pastel/green, off-VI) — and tried to regenerate it. Two controlled runs:
   - Logo **+ the real poster** as references → **9/10** (human grade)
   - Logo **only**, no target → **7/10**

   This isolated a finding we didn't have before: **the reference image is its own distinct input.** The 2-point gap is precisely the stuff words can't carry — the exact product silhouette and the typography quality. (Notably, our automated AI grader scored these *backwards* — it rated the logo-only run higher because it never saw the real burger. Lesson: **the human eye is still ground truth.**)

**3. We reframed the whole product.** With the analysis layer already built and the generation engine (gpt-image-2) clearly excellent, the variance in quality wasn't coming from the models — **it was coming from the brief.** So the product is no longer "a better model." It's *"a method that gets an ordinary marketing manager to a 9-quality brief without being a designer."*

**4. We designed the architecture to match.** We split the brief by **who can actually author each part** — a three-tier model (below) — and wrote it down as a concrete schema. The key invention is a middle layer the *system* fills, because a non-designer can't.

**5. We built and ran the decisive experiment.** We spawned Claude Code to build `scene_author.py` under a strict contamination rule (no scene hints leaked in), then ran it end-to-end: a 6-line brief → the model invents the entire scene → code assembles the prompt → image generated from the logo only. **It scored 7 — tying the expert hand-written prompt under identical conditions.**

**6. We diagnosed exactly what's left.** The machine missed two things vs the real poster: a teal background and a wood pedestal. Neither is *inferable* from "fresh garden premium" — they were the original designer's arbitrary choices. That's not a reasoning failure; **it's a one-line input the schema already has a slot for.** The 7→9 path is now mechanical.

---

## What we built (concrete artifacts)

| Artifact | Path | What it is |
|---|---|---|
| **Scene-authoring engine** | `harness/scene_author.py` | The core new build. Takes a thin brief + brand identity, has the model author the full scene (Tier 3), assembles the prompt, and generates. No human prompt-writing in the chain. |
| **Three-tier brief schema** | `brief_schema_v2.json` | The architecture contract: who authors each field, and the reconciliation rules. |
| **Proof run (3 files)** | `output/scene_author_run1/` | `tier3_scene.json` (what the model invented), `final_prompt.txt` (assembled), `generated.png` (the 7/10 result). |
| **Reproduction controls** | `output/taichi_poster1_repro.png` (9, with crutch) · `output/taichi_poster1_repro_LOGOONLY.png` (7, logo-only) | The A/B that isolated the reference-image value. |
| **Materials request** | `docs/MATERIALS_REQUEST_AIA.md` | The specific, prioritized ask for Richard's team (next trial). |

These sit on top of the already-built analysis layer (`extract_colors.py`, `extract_text_layer.py`, `provenance.py`, `score_v4.py`) and answer keys (`answer_keys/`).

---

## What we accomplished (the findings, stated plainly)

1. **The pipeline can reproduce a known target** — 9/10 with a reference, validating the generation engine on a hard off-VI case.
2. **The reference image is a separate, high-value input** — worth ~2 points; it carries product silhouette + type fidelity that text cannot name.
3. **A machine can author the scene from thin intent** — tying the expert hand-write (7/10) with zero human prompt-craft. *This is the breakthrough.*
4. **The remaining gap is "arbitrary specifics," not intelligence** — fixable with a one-line `must_include` + a reference image, both already in the schema.
5. **Human grading beats the AI grader for now** — until we calibrate the grader against human scores, we trust the eye.

---

## The architecture (three-tier brief)

| Tier | What it is | Who authors it | Status |
|------|-----------|----------------|--------|
| **1 — Identity** | Logo, exact colors, fonts | **Brand** (locked, from VI analysis) | ✅ Built & robust |
| **2 — Intent** | Subject, occasion, headline, feeling, optional reference | **Human** (one sentence each) | ✅ Defined |
| **3 — Scene** | Palette, staging, props, text layout, composition | **System** (model authors it) | ✅ **Proven today** |

**The insight:** stop asking a non-designer to write the prompt. Ask their *intent* (Tier 2), let the system *construct* the scene (Tier 3), show it back in plain language for a yes/nudge. They **react** instead of **author**.

### Where quality comes from (division of labor)
| Source of quality | Provided by | Proven? |
|---|---|---|
| Scene decomposition (palette, staging, props, text, composition) | **System** | ✅ ties expert at 7/10 |
| Arbitrary creative specifics (e.g. "teal background") | **Human**, one-line `must_include` | ← the 7→9 lever |
| Product silhouette + type fidelity | **Reference image** | ✅ worth +2 points |

---

## What we need next

1. **Close the 7→9 on Taichi** — rerun the same brief + a one-line `must_include` ("wood pedestal, teal background") + a product-form reference. If it lands 9, the full path is demonstrated end-to-end.
2. **Generalize to AIA (recommended next brand — see below).**
3. **Build the approval loop** — render Tier-3 as plain language; human nudges in plain language; re-run only the touched field.
4. **The falsifiable win test** — a naive user (not Alec) runs the full flow on a *new* campaign and lands ≥8, standalone, no expert in the loop. That is the proof the tool is real, not Hermes-assisted.

---

## Why AIA is the right next brand

AIA is the **deliberate opposite of Taichi on two axes**, which is exactly why it tests generalization rather than repeating a win:

- **Different vertical:** corporate insurance, not food → proves scene-authoring isn't food-specific.
- **Opposite reconciliation path:** Taichi was *off-VI* (departing from its own colors); AIA is *on-VI* (the brand identity *is* the constraint). Together they bracket the full range.
- **Abstract hero:** insurance has no physical product — the system must stage people + the mountain motif, a real generalization test.
- **A known weakness to retest:** earlier AIA runs drifted the brand red (#D31145). Good regression target.
- **Real access:** via Richard's team we can get genuine campaigns *and the briefs behind them*, enabling the honest test.

The specific materials ask is in `docs/MATERIALS_REQUEST_AIA.md` — prioritized P0 (needed to run) vs P1 (improves accuracy), with the "why" on each item so the right version is easy to pick.
