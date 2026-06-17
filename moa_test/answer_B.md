## The core reframe

You're not asking "did the output change?" You're asking two separate questions that must *both* pass:

1. **Magnitude:** Is the variation a weight change induces larger than seed-to-seed noise?
2. **Repeatability/direction:** Does the weight change move images in a *consistent direction*, or does it just add more random scatter?

This distinction is the whole game. A weight knob that injects extra randomness will *increase* pairwise image distances (passes a naive magnitude test) while being useless for learning, because it has no reproducible effect. So your decision rule needs a **directional-consistency** term, not just a distance threshold.

Below is a 4-phase protocol. Phases −1 and 0 are prerequisites; skipping them is how you fool yourself.

---

## Phase −1: Determinism sanity check (½ day)

Before anything, verify your assumed noise source is the only noise source.

- Generate the **same prompt + same weights + same seed**, 5 times.
- Measure pairwise distance.

**Expected:** ~0 (bit-identical or trivially close). **If not:** your API has server-side nondeterminism you can't seed (batching, mixed hardware, prompt caching). That's an *irreducible* noise floor that sits *underneath* your seed noise, and every later conclusion is contaminated unless you measure and subtract it. Don't proceed until you know this number.

---

## Phase 0: Pick a metric and measure the noise floor (1 day)

**Generate:** 1 fixed prompt, 1 fixed weight config, **40 different seeds** → 40 images. Repeat for **5 different prompts** (so you know the noise floor isn't a one-prompt fluke). ~200 images.

**Compute** for each metric you have (CLIP/embedding cosine distance, SSIM, color-histogram χ²):
- All pairwise distances within a (prompt, config) group → this is your **noise distribution** `D_noise`.
- Summaries: `μ_noise`, `σ_noise`, and the **95th percentile `q95_noise`**.

**Metric selection rule — reject metrics that are saturated:**
- If a metric reports ~all distances clustered near 0 (everything looks "identical") *or* near max (everything looks "totally different"), it has no dynamic range to detect signal. Discard it.
- Validate the survivor against humans: hand-pick ~10 image pairs spanning "obviously same-ish" to "obviously different," eyeball-rank them, and confirm your metric's ordering correlates. CLIP cosine usually tracks *semantic* change but is blind to pure color/composition shifts; SSIM is the opposite. **Pick a primary metric that matches what your marketing users actually care about,** and keep a secondary as a cross-check.

Normalize embeddings to unit length before any distance math.

Output of this phase: a single number you'll reuse everywhere — **`q95_noise`** = "how far apart two images of the same config typically get, by chance."

---

## Phase 1: Per-dimension signal test (core experiment)

Do this **one weight dimension at a time.**

**Generate:**
- **3 levels** of the dimension spanning the range you'd actually use (low / mid / high). *Use 3, not 2* — a 2-level test misses threshold/nonlinear knobs where both points land in a flat region and you falsely conclude "no effect."
- The **same set of 25 seeds** across all levels (matched seeds).
- Repeat across **2 prompts** to catch prompt-dependence.
- Count: 3 × 25 × 2 = 150 images per dimension.

Embed everything → vectors `v(level, seed, prompt)`. Analyze per prompt, then check the prompt agreement.

**Three statistics:**

**(1) Discriminability (magnitude vs noise)**
```
μ_L      = mean over seeds of v at level L      (centroid)
Δ        = ||μ_low − μ_high||                   (signal: centroid separation)
σ_within = sqrt(mean over all (L,seed) of ||v − μ_L||²)   (seed noise)
d' = Δ / σ_within
```
`Δ` averages seed noise out of the centroids, so it isolates the weight effect.

**(2) Significance (permutation test — handles noise non-parametrically)**
- Pool all images from levels low+high, randomly relabel them low/high, recompute `Δ_perm`.
- Repeat 10,000×. `p = fraction(Δ_perm ≥ Δ_observed)`.
- This builds the null "what centroid gap appears from pure noise" directly from your data.

**(3) Directional consistency (the repeatability term — most important)**
Using matched seeds:
```
δ_i = v(high, s_i) − v(low, s_i)        (per-seed change vector)
R = ||mean_i(δ_i)|| / mean_i(||δ_i||)   (resultant ratio, 0..1)
```
- `R ≈ 1`: every seed moves the same way → real, learnable, reproducible effect.
- `R ≈ 0`: large but randomly-directed moves → the knob adds noise, **not** signal. This is the trap your whole project is trying to avoid, and `R` is the metric that catches it.

---

## Phase 1 decision rule

Declare a weight dimension **"real, repeatable change above the noise floor"** only if **ALL** hold:

| Test | Threshold | Why |
|---|---|---|
| Magnitude | `Δ > q95_noise` | The avg low vs avg high image differs more than two random seeds of one config do |
| Discriminability | `d' ≥ 1.0` | Signal at least as large as seed scatter (tune; 1.0 ≈ clearly visible) |
| Significance | permutation `p < 0.01` | Gap isn't a fluke |
| **Consistency** | `R ≥ 0.5` | Change has a reproducible *direction*, not just scatter |
| Robustness | All above hold on **both prompts** | Not a single-prompt artifact |

**Declare "indistinguishable from sampling noise"** if `Δ < q95_noise` OR `p > 0.05` OR `R < 0.3`. The last condition is what kills the "it changed but only randomly" case.

**Multiple-comparison correction:** you're testing many dimensions. Apply Benjamini–Hochberg FDR (or Bonferroni) across the per-dimension `p` values, or some knobs will pass by chance.

---

## Failure modes that make your conclusion wrong

1. **Hidden API nondeterminism** (Phase −1). If fixed-seed isn't reproducible, your "noise floor" is inflated and you'll under-call real effects. Measure it; subtract it in quadrature from `σ_within` if nonzero.

2. **Metric/human mismatch.** CLIP says "no change" while a human sees an obvious palette shift (or vice versa with SSIM). You'll mislabel real knobs as noise. *Mitigation:* require your primary metric to pass the Phase-0 human-ordering check; report secondary-metric disagreement as a flag.

3. **The randomness-amplifier knob.** A weight that just increases output variance passes `Δ > q95_noise` and `p < 0.01` but fails `R`. Without the consistency term you'd "learn" a knob that does nothing reproducible. This is *the* failure your project must avoid — don't drop `R`.

4. **Two-level flat-region trap.** Nonlinear/threshold knobs read as dead if both tested levels sit in a flat part of the response. Use 3+ levels.

5. **Seed×weight interaction.** A knob that works for some seeds, not others, shows moderate `Δ` but low `R`. That's correctly flagged as not-learnable here — good — but note it means the effect is conditional, worth logging rather than discarding.

6. **Dimension interaction.** Your honing loop perturbs *multiple* weights at once; per-dimension characterization can't see synergy/cancellation between knobs. Treat Phase-1 results as *necessary screening* (kill the dead knobs) but validate the live ones jointly before trusting the loop.

7. **Embedding anisotropy.** Raw CLIP cosine can be dominated by a few high-variance dims. Whiten embeddings (or at least mean-center per the Phase-0 corpus) before distance computation, or `Δ`/`σ` ratios get distorted.

8. **Underpowered n.** With n=25 seeds and permutation testing you can reliably detect effects around `d' ≈ 0.7+`. If a knob's true effect is subtle-but-real, you may miss it; if a dimension matters to you and reads null, re-run with n=50 before concluding "noise."

9. **The downstream loop trap (out of scope but flag it now).** Even a dimension that passes here only earns the *right* to be in the loop. The loop's actual learning signal is a human's noisy 1-of-4 choice (~2 bits, with its own preference variance). Characterizing knob signal-vs-noise does **not** characterize *human-preference* signal-vs-noise — that's a separate experiment (test–retest the same human on the same 4 drafts; if they don't agree with themselves, the loop can't learn regardless of how good your knobs are).

---

## Implementation checklist (this week)

- Day 1: Phase −1 + write metric + distance functions.
- Day 2: Phase 0, generate 200 images, lock `q95_noise` and primary metric.
- Day 3–4: Phase 1 on your top 3–5 candidate dimensions (150 images each).
- Day 5: Run the three statistics + decision table + FDR correction; produce a per-dimension verdict table (`Δ, q95_noise, d', p, R, prompt-agreement, VERDICT`).

That verdict table is the falsifiable deliverable: every dimension is labeled **learnable** or **noise** by an explicit, pre-registered rule.