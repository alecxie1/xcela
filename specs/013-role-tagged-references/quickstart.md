# Quickstart: Role-Tagged References (013)

Everything except §4 is FREE (no paid calls).

## 1. The feature's own self-test

```bash
.venv/bin/python test_product_refs.py
```

Expected: all checks PASS per [contracts/product_refs_contract.md](contracts/product_refs_contract.md)
(prompt section + byte-identity, both-call-sites threading, cap fail-loud, refs-list prefix
equality, calibration isolation, multipart 0/2/7 cases, form greps).

## 2. No-regression sweep

```bash
for t in test_conductor test_render_and_scrub test_render_modes \
         test_register_render_aware test_frontend_nav test_lossless_brief; do
  .venv/bin/python $t.py || break
done
```

Expected: all green, unchanged.

## 3. End-to-end plumbing (dry-run + browser, no model calls)

Add `"product_images": ["/tmp/p1.png", "/tmp/p2.png"]` (real files) to a copy of a thin inputs
JSON, then:

```bash
.venv/bin/python harness/conductor.py --brand aia --inputs <copy>.json \
    --out /tmp/013dry --thin --dry-run --no-approve
```

Inspect `/tmp/013dry/plan.json`: the scene_author argv carries `--product-image` twice, in
order; the calibrate argv is unchanged. Then serve the form (`.venv/bin/python
frontend/server.py`): the old upload says Style reference, the optional product-shots
multi-file control exists, and picking 7 files is rejected with a message naming the cap of 6.

## 4. The ONE paid run (SC-006, deferred human eye-gate)

Rerun the CJXQ watermelon brief through the form, same style reference and messages as
`run_CJXQ_20260701_164912`, PLUS the branded cup shots uploaded as product references. Judge
with the eye against that run:

- the composition carries the ACTUAL branded cups: printed 茶救星球 JO'S CHA visible on the
  products, not generic photoreal look-alikes (the 012 observed gap, closed);
- the style/scene quality of the 012 run is retained (photographic, tropical, playful);
- no new text leakage (the only-the-headline guard still governs generated text).

Record the verdict in SYSTEM_MAP.
