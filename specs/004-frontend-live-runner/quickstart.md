# Quickstart: validating the Frontend Live-Runner

Free STRUCTURAL surfaces first (no spend), then the one PAID single-sign run is the operator's
eye-gate. A green self-test proves structure, never pixels (constitution §II).

## Prerequisites

- Python 3.11 env at `.venv` (run as `.venv/bin/python ...`). No new dependencies (stdlib server).
- Brand data present: `answer_keys/aia.json` (+ `kits/`, `brands/` for the eventual paid run).
- A reference image on disk (required in v1). Reference instance: `inputs_lily_aia.json`.

## Step 1 — Verbatim single-sign intake (free)

```
.venv/bin/python test_frontend_intake.py
```
Expect: `inputs_writer` turns a filled single-sign form state into a 002-shape inputs JSON with
EXACTLY one `signs[]` entry; `messages`, `mandatory_elements`, and the three vibe integers equal the
typed values byte-for-byte; the output passes `conductor.validate_inputs`.

## Step 2 — Progressive stage reader (free)

```
.venv/bin/python test_frontend_stages.py
```
Expect: over a synthetic run dir with `register_profile.json` + `final_prompt.txt` but no
`generated.png`, `run_view` reports register + prompt PRESENT and image ABSENT (the progressive
surface); a missing artifact yields absent + the manifest note, never a fabricated placeholder.

## Step 3 — Run trigger argv + conductor --style-notes (free)

```
.venv/bin/python test_frontend_runner.py
.venv/bin/python test_conductor.py
```
Expect: `build_conductor_argv` yields `--thin --no-approve --inputs` (no `--out`), and adds
`--style-notes <note>` only on a nudge; the conductor self-test confirms `--style-notes` threads to
the thin `scene_author` argv (dry-run) and the standalone thin route is intact (one command, no UI).

## Step 4 — Drive it in the browser, then the PAID run (operator)

```
.venv/bin/python frontend/server.py        # serves http://localhost:<port>
```
In the browser: pick brand `aia`, fill the single-sign form (one sign, a reference image, vibe
sliders, `分别画叉` as a mandatory element, `60x40cm`), press Run (labeled ~$0.08). Watch the stages
appear progressively: brief → register/dial → assembled prompt → generated sign. Then judge:
- SC-001: you completed the brief, ran it, watched dial + prompt + sign appear, and approved/nudged.
- SC-002/SC-003: the inputs JSON is verbatim + one sign; the stages came from the run-dir artifacts.
- SC-004: a nudge with a binding note regenerated into a NEW run dir, the note in the new prompt, the
  prior attempt still there to compare.
- SC-005: `conductor.py --brand aia --thin --no-approve --inputs <single>.json` still runs with the
  server off.

## References

- Data shapes: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Decisions + reuse map: [research.md](./research.md)
