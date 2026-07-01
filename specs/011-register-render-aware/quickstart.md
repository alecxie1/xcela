# Quickstart: Render-Aware Register (011)

Validation guide. Everything except the last section is FREE (no paid model calls).

## Prerequisites

- Repo root, `.venv` present. Run everything as `.venv/bin/python`.
- Any brand key in `answer_keys/` (the register engine only needs the typography styles map;
  the new tests build subfields dicts inline).

## 1. The feature's own self-test (the primary gate)

```bash
.venv/bin/python test_register_render_aware.py
```

Expected: all checks PASS, covering the contract table in
[contracts/derive_register_contract.md](contracts/derive_register_contract.md):
photo+playful suppresses to `marketing` with the trace naming render_style; flat and absent stay
`event_prop` (absent byte-identical); explicit event usage wins over photo; marketing keywords
match explicitly; tone cues retained without `shape:die-cut`; normalizer drift guard.

## 2. No-regression sweep (SC-006)

```bash
.venv/bin/python test_conductor.py
.venv/bin/python test_render_and_scrub.py
.venv/bin/python test_render_modes.py
```

Expected: green, unchanged from before the feature.

## 3. End-to-end plumbing check (dry-run, no model calls)

```bash
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/011dry --thin --dry-run --no-approve
```

Then inspect:

- `/tmp/011dry/subfields.json` carries `render_style` verbatim when the inputs file has it
  (add `"render_style": "photographic"` to a copy of the inputs to see it threaded).
- A NON-thin dry-run of the same inputs writes `subfields.json` WITHOUT the key (kit/legacy
  byte-identical guarantee).

To see the live derivation trace directly:

```bash
.venv/bin/python register/derive_register.py --subfields /tmp/011dry/subfields.json \
    --brand aia --out /tmp/011dry
```

Expected with a photographic + playful/no-event subfields file: `inferred_register: marketing`
and a trace line naming the render choice as the suppression reason.

## 4. The ONE paid run (SC-007, deferred human eye-gate)

Only after 1-3 are green and a human is ready to judge:

```bash
.venv/bin/python harness/conductor.py --brand <playful-brand> --inputs <photo-marketing-inputs>.json --thin
```

Judge `output/run_*/sign_*/final.png` with the eye: it must read as a playful marketing poster
(polished promotional piece, energetic, on-brand), NOT a hand-held event prop and NOT a stiff
corporate poster. A green self-test proves structure, never pixels.
