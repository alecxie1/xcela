# Quickstart: Explicit Usage Wins (014)

All FREE except the optional eye confirmation, which piggybacks on a natural run.

## 1. The feature's own self-test

```bash
.venv/bin/python test_explicit_usage_wins.py
```

Expected: all checks PASS per [contracts/explicit_usage_contract.md](contracts/explicit_usage_contract.md).

## 2. No-regression sweep

```bash
for t in test_register_render_aware test_conductor test_render_and_scrub test_render_modes \
         test_lossless_brief test_product_refs test_frontend_nav; do
  .venv/bin/python $t.py || break
done
```

Expected: all green, unchanged (register_render_aware 8/8 in particular).

## 3. The live trace (free, reproduces the defect fixture)

Rerun the exact failing brief's derivation without any paid step: a subfields JSON with
usage_context containing "social"/"promotional", vibe formality 2 / playfulness 8, and
`render_style: "flat vector"`, through `register/derive_register.py --subfields ... --brand CJXQ
--out /tmp/014check`. Expected: `inferred_register: marketing`, a single SUPPRESSED line naming
the matched keyword, `font:rounded` + `palette:playful-accents` flexed, NO `shape:die-cut`.
(Compare run_CJXQ_20260701_173925's trace, where the same brief promoted to event_prop.)

## 4. Eye confirmation (SC-005, cheap path)

No dedicated paid run: on the next natural FLAT run from a playful brand with marketing usage
(or a rerun of the 173925 brief whenever convenient), the eye confirms a flat rectangular
marketing poster with playful tone, not a hand-held die-cut sign. Record the verdict in
SYSTEM_MAP when it happens.
