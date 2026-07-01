# Quickstart: Lossless Brief (012)

Everything except §4 is FREE (no paid calls).

## 1. The feature's own self-test

```bash
.venv/bin/python test_lossless_brief.py
```

Expected: all checks PASS per [contracts/lossless_brief_contract.md](contracts/lossless_brief_contract.md)
(scene threading rows 1-4, notes channel 5-7, form surface 8-12, back-compat 13-14).

## 2. No-regression sweep

```bash
.venv/bin/python test_conductor.py
.venv/bin/python test_render_and_scrub.py
.venv/bin/python test_render_modes.py
.venv/bin/python test_register_render_aware.py
.venv/bin/python test_frontend_nav.py
```

Expected: all green, unchanged.

## 3. End-to-end plumbing (dry-run + browser, no model calls)

```bash
.venv/bin/python harness/conductor.py --brand aia --inputs <inputs-with-asset_type-and-occasion>.json \
    --out /tmp/012dry --thin --dry-run --no-approve
```

Inspect the planned scene_author argv in `/tmp/012dry/plan.json`: it carries `--asset-type` and
`--occasion` verbatim. Then `.venv/bin/python frontend/server.py`, open `/`, and eyeball the form:
no audience/warmth controls, the relationship dropdown has 3 described options, the design-notes
box exists, the message label states the verbatim contract.

## 4. The ONE paid run (SC-007, deferred human eye-gate)

Re-brief the CJXQ watermelon post through the form (photographic, same messages, asset_type and
occasion filled, a design note if desired). Judge with the eye against the pre-012 run
(`output/run_CJXQ_20260701_154416`):

- subject fidelity: the image is more specifically the ASKED-FOR asset (new-product social post);
- leakage: NO occasion/scene words painted anywhere on the asset (the slogan lesson);
- the design note (if given) is visibly obeyed.

Record the verdict in SYSTEM_MAP.
