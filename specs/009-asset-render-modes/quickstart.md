# Quickstart: Beyond Flat-vector Event Signs (Render Modes)

Free structural validation first, then the LOAD-BEARING human eye-gate (this feature's value is only
provable by the eye on a real generated image).

## Prerequisites

- Python 3.11 `.venv` (run everything as `.venv/bin/python`).
- A brand answer_key (e.g. `aia`) and a reference image (the live-runner reference job).

## 1. Free structural self-tests (NO paid calls)

```bash
# the new feature test (dialect switch, opener matrix, negatives split, mapping, thin argv, inputs)
.venv/bin/python test_render_modes.py

# regression: the thin route, conductor, and the prior frontend suites
.venv/bin/python test_thin_route.py
.venv/bin/python test_conductor.py
.venv/bin/python test_frontend_intake.py
.venv/bin/python test_palette_roles.py
```

Expected: each prints `RESULT: N/N checks passed` and exits 0. The new test asserts (each a VALUE a wrong
build cannot satisfy):
- photo dialect: the assembled prompt has photographic language and NO "FLAT VECTOR" / "no photographic
  shading", but keeps the text guards + the verbatim headline.
- flat + marketing register: the opener drops "hand-held event sign" (rectangular poster); flat + event_prop
  is byte-unchanged (still die-cut prop + the flat render negatives).
- `normalize_render_style` maps photographic->photo, everything else->flat_graphic.
- `build_plan` for a photographic brief -> the thin argv carries `--asset-profile photo`; default -> flat.
- `inputs_writer` carries `render_style` verbatim; the served page has the render-style control.

## 2. Live-runner smoke (free)

```bash
.venv/bin/python frontend/server.py    # http://localhost:8765, open /
```

- Confirm a Render style control (flat vector / photographic) is present, defaulting to flat vector.

## 3. The LOAD-BEARING human eye-gate (the one paid sign, SC-007; NOT automated)

```bash
.venv/bin/python frontend/server.py    # open /, pick a reference, set render style = photographic, Run
```

Generate with render style = photographic in a wall-posted (marketing) usage, and judge `output/run_*/
sign_*/final.png` by EYE (constitution §II): does it actually read as a PHOTOGRAPHIC poster (real
photography, depth, lighting), not a flat illustration? Then generate a flat brief in a marketing usage and
confirm it reads as a rectangular poster, not a die-cut event sign. A green structural test proves only that
the dialect SWITCHED; only the eye confirms the output looks right. Record the verdict in `SYSTEM_MAP.md`.
This folds into the existing back-half paid run; 009 ships no separate paid run.
