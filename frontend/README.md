# `frontend/` - thin local web live-runner (feature 004)

A THIN local web frontend over the agent-free CLI. It lets the operator drive ONE single-sign brief:
type a structured form, press Run (paid gpt-image-2, cost-labeled), watch the thin route's stages
appear progressively from the run directory (brief -> register/dial -> assembled prompt -> generated
sign), and take the taste action (approve, or nudge-rerun with a binding note).

- **Stdlib only, no new dependencies.** `server.py` is a `http.server` app; `index.html` is one
  static page with inline vanilla JS. No framework, no build step.
- **Thin posture (constitution §I/§VII).** The UI writes the inputs JSON, shells out to
  `harness/conductor.py --thin --no-approve [--style-notes ...]`, and READS the run-dir artifacts. It
  NEVER reimplements generation, register derivation, or prompt assembly. Each (re)run is a new
  `output/run_*` dir; reruns go through the conductor CLI, not the UI.
- **The standalone CLI still runs with this frontend absent** - the frontend is optional.

Modules:
- `inputs_writer.py` - pure: single-sign form state -> the 002-shape inputs JSON (verbatim, one sign).
- `run_view.py` - pure: a run dir -> the stage dict (artifact presence + content); honest null on missing.
- `runner.py` - `build_conductor_argv` (pure) + `launch` (subprocess -> run dir).
- `server.py` - stdlib HTTP glue (form page, POST /run, GET /run/<id>/stages, image).
- `index.html` - the single-sign form + progressive stage panels + approve / nudge.

Spec / plan / contracts: `specs/004-frontend-live-runner/`.
