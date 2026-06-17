# Protocol: Separating Weight-Signal from Sampling-Noise

Your instinct is correct, and the clean way to frame it is: **the seed-variation distribution is your null hypothesis.** A weight dimension is "real and learnable" only if changing it moves the output *more reliably and more in the intended direction* than merely changing the seed does. Below is a protocol you can implement this week.

---

## Step 0 — Pre-flight: Is the seed even honored? (do this first, ~1 hour)

Generate **same prompt + same weights + same seed**, 3×.

- **Pixel-identical (hash match)** → seeds are deterministic. You can use the powerful **paired-seed** design (Step 3).
- **Different** → the API has irreducible nondeterminism even at fixed seed. You must use the **distributional/classifier** design and fold this residual into your noise floor.

Many hosted diffusion endpoints do *not* guarantee seed determinism. **Assume distributional until proven otherwise.** This one test changes everything downstream.

Also: **pin the model version** and **log the final prompt** the API actually used (after any safety rewriting). Silent model drift or prompt rewriting will masquerade as a weight effect.

---

## Step 1 — Lock your measurement instruments (never collapse to one metric)

A weight can move color while leaving semantics untouched, or vice versa. Use a panel and **freeze it before generating anything**:

| Axis | Metric | Distance |
|---|---|---|
| Semantic | DINOv2 or CLIP ViT-L embedding | cosine |
| Structural | SSIM (resize to common res; **paired same-seed only**) | 1 − SSIM |
| Color/palette | HSV histogram (8×8×8 bins) | Earth Mover's / χ² |
| Perceptual | LPIPS (optional, good middle ground) | LPIPS |

**Plus a targeted score per dimension.** For each weight dimension, pre-register one primary metric matching what it's *supposed* to do:

| Dimension | Targeted metric |
|---|---|
| Minimalism | CLIP score: "minimalist clean ad" − "busy cluttered ad" |
| Brand color | HSV distance to brand palette |
| Product prominence | detector/segmenter bbox area fraction |
| Text emphasis | OCR text area / box count |
| "Luxury" feel | CLIP pos−neg, **or blinded human rating** |

Pre-registering the metric matters: if you try 20 metrics and keep the one that "works," you manufacture false positives.

---

## Step 2 — Build the noise floor (the null distribution)

Pick **5–12 representative briefs** (not 1 — noise is prompt-dependent; busy scenes vary more than centered products on white).

For each brief, at baseline config **W0**, generate **K ≈ 32–40 images with different seeds**. Compute all pairwise distances → this is your **noise distribution N** per (brief, metric). Record median, SD, and 95th percentile.

**Critical:** also measure the noise floor at the *changed* value W1, not only at W0. Noise is heteroscedastic — some configs are intrinsically more chaotic, and comparing a stable baseline to a noisy variant will fool you.

---

## Step 3 — Generate the signal: one dimension at a time, dose-response

For each weight dimension, use **≥3 levels** (e.g. W0, W_mid, W_high; ideally 5 levels: −2,−1,0,+1,+2), holding all other weights fixed. Three+ levels let you detect a *monotonic trend*, not a single coin-flip difference, and catch threshold/saturation effects.

**Paired design (if seeds are deterministic — strongly preferred):**
Use the *same* seed list at every level. The paired displacement
`d_i = dist(img(W0, seed_i), img(W1, seed_i))`
isolates the weight effect with seed perfectly controlled.

**Distributional design (if nondeterministic):**
Generate fresh seeds per level and rely on the classifier test below.

**Generation budget:** `briefs × seeds × levels`. E.g. `12 × 32 × 5 = 1,920` images per dimension (baselines reusable across dimensions). Cost-bound? Screen with `8 briefs × 16 seeds × {−2, 0, +2}`, then confirm winners at full resolution.

---

## Step 4 — The decision rule

The deployment question is: *in your 4-draft loop, drafts differ by seed AND weight — does the weight signal survive seed noise?* Test exactly that.

### Primary test A — Can a classifier recover the weight label across seeds?
1. Pool W0 and W1 images (across all seeds) in embedding space.
2. Train logistic regression to predict the weight label; **5-fold CV**, report mean accuracy + 95% CI.
3. Build the null by **permutation**: shuffle labels, re-run CV, repeat 5,000×. p = fraction of shuffles ≥ observed.

### Primary test B — Dose-response slope (uses all levels)
Standardize the targeted score into seed-noise units:
`y[b,l,s] = (score − mu0[b]) / sigma0[b]`
Fit slope of `y` vs level. Test it with a **seed-blocked permutation test**: within each (brief, seed) block, shuffle the level labels, recompute slope, repeat 10,000×. This respects your blocking and needs no distributional assumptions.

### Secondary test — AUC of signal vs noise distance (interpretability)
For each metric: `AUC = P(weight-change distance > same-weight seed-change distance)`.
- AUC ≈ 0.5 → weight does no more than reseeding (null).
- AUC ≥ 0.9 → weight reliably dominates seed noise *on that axis*, telling you *which* axis it moves.

### Two repeatability numbers you must distinguish
- **Paired repeatability** `W_pair = P(y at +2 > y at −2 | same seed)` — does the weight reliably push the intended direction when seed is controlled?
- **Unpaired one-shot separability** `AUC_unpaired = P(y_high(seed s1) > y_low(seed s2))` — if you show *one* image per config with *unrelated* seeds, does the higher-weight one usually look more like the target? **This is the number that matters for your actual 4-draft loop if drafts use independent seeds.**

### Multiple comparisons
You'll test many dimensions × metrics. Apply **Benjamini–Hochberg FDR** (or Bonferroni) or you'll "discover" effects by chance — the exact failure you're avoiding.

### Effect size, not just significance
With 40 seeds, permutation tests will flag tiny, useless effects. Require a magnitude threshold too.

---

## Step 5 — Three-tier verdict

**GREEN — real and usable in one-shot draft selection:**
- Dose-response FDR q < 0.05, correct direction
- |Δ_range| ≥ 0.5 seed-noise SD (≥1.0 = strong)
- Classifier CV accuracy ≥ 0.80, CI lower bound > 0.5
- Paired `W_pair` 95% CI lower bound > 0.60
- **`AUC_unpaired` 95% CI lower bound > 0.65**
- Holds in ≥70% of briefs
- Controls behave (Step 6)

**YELLOW — real but too weak for one-shot learning:**
Passes paired causal tests (q<0.05, W_pair>0.60) but **fails `AUC_unpaired`**. The weight does something real, but seed noise drowns it in a single image. → Don't update from a single 4-way winner with independent seeds. Instead: use the **same seed across all 4 variants**, average over multiple seeds, use a smaller learning rate, or use larger weight perturbations.

**RED — indistinguishable from sampling noise:**
Permutation not significant after FDR, inconsistent direction, or effect below threshold. RED ≠ "effect is zero" — it means too small/inconsistent for your loop at this sample size. (If a dimension goes RED, also check whether your weight syntax is even being honored — RED can mean "the API ignores this knob," not "the concept is impossible.")

---

## Step 6 — Controls (these validate the protocol itself; skip them and you can't trust any result)

- **Positive control:** a knob you *know* is strong (e.g. "dominant red background" vs "dominant blue"). The protocol MUST flag it GREEN. If not, your metrics are blind.
- **Negative / sham control:** two *identical* configs given different labels (or a no-op token). The protocol MUST flag it RED. If a fake difference reads "real," your test is a rubber stamp and every result is suspect.
- **Duplicate control:** 5–10% same-prompt/same-seed regenerations to confirm seed stability throughout the run.

---

## Step 7 — Use cluster bootstrap for all CIs

Resample **briefs** with replacement, then seeds within brief. 2,000 replicates. Naively bootstrapping 1,920 images as if independent will give you false confidence — they're clustered within 12 briefs.

---

## Step 8 — Validate the actual loop end-to-end

After dimension-level testing, simulate the real loop: for each brief×seed, sample 4 configs the way your tool will, generate them (same seed), have humans pick, and fit a **Bradley–Terry / logistic model** with random effects for brief and seed.
- Weight coefficients stable and significant → learnable signal.
- Seed/brief random effects dominate, weight coefficients ≈ 0 → your update is a random walk.

---

## Failure modes that would make your conclusion wrong

1. **Seed nondeterminism silently confounds everything** — Step 0 + paired design is the only defense.
2. **Metric blindness** — CLIP is insensitive to subtle palette/texture; a real effect reads null on the wrong metric. → use the panel, never collapse.
3. **Two-point trap** — testing only W0 vs W1 misses threshold/non-monotonic effects. → ≥3 levels.
4. **Heteroscedastic noise** — measuring the floor only at baseline understates it at the variant. → measure both endpoints.
5. **Prompt overfitting** — effect real for one brief vanishes for others. → multiple briefs, require ≥70%.
6. **Significance ≠ magnitude** — require the effect-size threshold, not just p<α.
7. **Separable ≠ human-perceptible** — a classifier can split clusters humans can't see. → once GREEN, confirm with a quick human 2AFC before trusting it as a *preference* axis.
8. **Multiple comparisons** — FDR-correct across all dims/metrics.
9. **Model drift / prompt rewriting** — pin version, randomize job order, log final prompts.
10. **Same-seed overestimates production reliability** — paired tests prove causality but your production loop may use independent seeds; that's why `AUC_unpaired` gates GREEN.

---

## One-week implementation plan

```
Day 1  Step 0 seed test. Pin model. Lock metric panel + targeted metrics. Wire embedding/distance funcs.
Day 2  Generate noise floor: briefs × ~32 seeds × {W0, W1}.
Day 3  Generate signal: 2–3 candidate dims × ≥3 levels × 32 seeds (same seeds across levels).
Day 4  Build classifier+permutation+AUC pipeline. Run POSITIVE & NEGATIVE controls FIRST — they gate everything.
Day 5  Run all dims, FDR-correct, cluster-bootstrap CIs. Produce table:
       [dim | dose_resp_q | direction | Δ_range(SD) | CV_acc(CI) | W_pair(CI) | AUC_unpaired(CI) | AUC_clip/ssim/color | VERDICT]
```

Only GREEN dimensions enter your honing loop. YELLOW dimensions go in only with same-seed comparison or multi-seed averaging. Everything else, you'd be fitting to randomness — precisely what this protocol exists to prevent.

A useful bonus: the measured SNR (classifier accuracy / AUC) per dimension can set a **per-dimension learning rate** in the loop — nudge high-SNR dims more, barely-above-noise dims less.

Want me to sketch the scoring/classifier/permutation code, or the Bradley–Terry loop simulation?