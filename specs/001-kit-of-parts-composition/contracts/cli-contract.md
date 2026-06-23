# Contract: CLI + routing changes

The kit-composition path plugs into the EXISTING `harness/conductor.py` orchestration (campaign
loop, approve/nudge gate, manifest, dry-run). No new top-level orchestrator. Existing flags and
non-negotiables are preserved (FR-006).

## `harness/conductor.py`

- Unchanged flags: `--brand`, `--inputs`, `--out`, `--dry-run`, `--no-approve`.
- New behavior (no new REQUIRED flags): when `kits/<brand>.json` exists, family jobs ROUTE
  through the kit path:
  1. derive shared `register_profile` (+ calibration if a reference is supplied) [reuse],
  2. build `kit_profile.json` once via `harness/kit.py`,
  3. per sign, call `harness/compose_select.py` then route `scene_author` in reserve-box +
     fit-to-zone mode.
- The reference, when present, feeds `kit_profile` (style internalization); it does NOT trigger
  the aligned-prompt clone path for kit jobs (D6).
- `--dry-run` MUST emit, per sign, the chosen icon + archetype + reserved text_zone +
  needs_review WITHOUT any model or image call (free structural surface).
- The approve/nudge gate surfaces each sign's icon + layout proposal; a nudge can override the
  icon or archetype for a sign (human taste gate, constitution I).
- The conductor manifest records: `kit_profile` path, per-sign `composition.json`, and every
  `needs_review` with its reason (honest nulls, constitution V).

## `harness/kit.py` (NEW)

```
.venv/bin/python harness/kit.py --brand aia \
    --answer-key answer_keys/aia.json \
    --register-profile <run>/register_profile.json \
    [--calibration <run>/calibration.json] \
    --out <run>/kit_profile.json
```
- Loads + validates `kits/aia.json` (kit-schema.md); raises on any violation.
- Emits `kit_profile.json` (kit-profile-schema.md); answer key wins conflicts; honest-null notes.

## `harness/compose_select.py` (NEW)

```
.venv/bin/python harness/compose_select.py --brand aia \
    --kit kits/aia.json \
    --message "守住钱袋子;护好幸福家" \
    --campaign-used <comma-separated archetype ids already used this campaign> \
    --out <run>/sign_s1/composition.json
```
- Deterministic meaning→mode→icon match; honest-null + needs_review on miss.
- Collision-avoiding archetype selection given `--campaign-used`; reuse + flag when exhausted.
- `--explain` prints the resolved composition JSON and EXITS before any model call.

## `harness/scene_author.py` (CHANGED)

- New mode: kit reserve-box composition. Inputs: `--kit-profile`, `--composition`
  (composition.json). Paints `panel_treatment` + the chosen icon's `icon_description` inside
  `icon_zone`, keeps `text_zone` clear. Then the licensed headline is composited into `text_zone`
  at `fitted_type.final_size_px`.
- The aligned-prompt clone path remains for non-kit reference jobs (back-compat), but kit jobs do
  not use it.
- `--explain` still prints the resolved prompt SOURCE + mode and exits before any model call.

## `harness/composite_text.py` (EXTENDED)

- New fit-to-zone clamp callable: given headline text + `text_zone` (px) + resolved licensed font,
  return the largest `size_px` fitting with `margin_px`; null if it cannot fit at `min_size_px`.
- The existing `composite()` + compliance manifest are unchanged and still run after the clamp.

## Test surfaces (free; constitution cost discipline)

```
.venv/bin/python test_kit.py            # load/validate + answer-key-wins-conflict
.venv/bin/python test_compose_select.py # meaning->icon, distinct archetypes, honest nulls
.venv/bin/python test_fit_to_zone.py    # long headline shrinks; impossible -> null
.venv/bin/python test_conductor.py      # dry-run plan shows kit path + distinct archetypes
```
No paid generation in any test. The one paid run is judged by the human eye on
`output/run_*/sign_*/final.png`.
