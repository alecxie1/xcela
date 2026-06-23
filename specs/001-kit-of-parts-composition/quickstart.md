# Quickstart: validating Kit of Parts + Bespoke Composition

How to prove this feature works end to end. Free STRUCTURAL surfaces first (no spend), then the
one PAID run judged by the human eye. Per the constitution: a green self-test proves structure,
never beauty; only the eye validates pixels.

## Prerequisites

- Python 3.11 env at `.venv` (run everything as `.venv/bin/python ...`).
- API keys present in `~/.hermes/.env` (only needed for the paid run; not for dry-run/self-tests).
- Brand data present: `answer_keys/aia.json`, `config/aia.yaml`, and the NEW `kits/aia.json`
  (authored per contracts/kit-schema.md).
- An AIA inputs file with a style reference and the 2-sign set (extend
  `conductor_inputs_example.json`: messages 守住钱袋子/护好幸福家 and 远离非法金融/抵制高息诱惑).

## Step 1 — Validate the authored kit (free)

```
.venv/bin/python test_kit.py
```
Expect: kit loads; every mode is served by an archetype; every archetype's `icon_zone` and
`text_zone` do not overlap; on a seeded reference-vs-answer-key palette clash the answer-key hex
wins and `conflict_resolutions` records it. A malformed kit fails with the specific rule violated.

## Step 2 — Validate deterministic selection (free)

```
.venv/bin/python test_compose_select.py
```
Expect: 钱袋子/储蓄 → `chosen_icon = money_bag`; a nonsense message → `chosen_icon = null` with
`needs_review = true`; two different-mode messages → two DIFFERENT `chosen_archetype`; exhausting
the layout vocabulary → `archetype_reused = true` + `needs_review = true`.

## Step 3 — Validate fit-to-zone (free)

```
.venv/bin/python test_fit_to_zone.py
```
Expect: a long headline yields a strictly smaller `final_size_px` than a short one in the same
zone, with `rendered_box_frac` inside `text_zone` plus margin; a headline that cannot fit at
`min_size_px` yields `fits = false`, `final_size_px = null`, `needs_review = true` (never clipped).

## Step 4 — Dry-run the whole campaign plan (free, no model calls)

```
.venv/bin/python harness/conductor.py --brand aia \
    --inputs <your_aia_inputs>.json \
    --out /tmp/dry --dry-run --no-approve
```
Expect: `plan.json` plus, per sign, the chosen icon + archetype + reserved `text_zone` +
needs_review, all WITHOUT any vision/Anthropic/image call. Confirm the two signs get DIFFERENT
archetypes (the reframe's core), and the reference is consumed into `kit_profile`, not cloned.

```
.venv/bin/python test_conductor.py
```
Expect: conductor self-test green (kit route present in the dry-run plan; distinct archetypes).

## Step 5 — The ONE paid run (judge by eye)

```
.venv/bin/python harness/conductor.py --brand aia --inputs <your_aia_inputs>.json
```
Approve/nudge at the gate (override any icon/layout proposal you dislike). Then open
`output/run_*/sign_*/final.png` and judge with your EYE against `desiredresultaia.jpg`:

- SC-001: the two signs are DISTINCT compositions (different icon AND layout), not re-texted clones.
- SC-002: all headline text sits inside the sign with visible margin on every edge (zero clipping).
- SC-003: each hero icon is intact, not overlapped, no scrub artifact.
- SC-004: the family reads as distinct-yet-cohesive, closer to the ground truth than the 6/18 output.
- SC-005: `final.png.compliance.json` shows licensed fonts resolved; manifest records any
  needs_review; no em-dashes in any user-facing text.

If any sign carries `needs_review`, the manifest names why (no icon match / archetype reused /
text could not fit). That is the honest-null path working, not a failure to hide.

## References

- Data shapes: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Decisions + reuse map: [research.md](./research.md)
