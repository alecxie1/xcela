# Phase 0 Research: Frontend Live-Runner (single-sign)

All decisions are grounded in the verified code (read this session): `conductor.py` (`--thin`,
`--no-approve`, `--inputs`, `--out`, run dir = `output/run_<brand>_<timestamp>`,
`_scene_author_thin_argv`, `run_approve_gate` terminal `input()` loop, no top-level `--style-notes`),
`scene_author.assemble_thin_prompt(style_notes=...)` + the `--thin`/`--style-notes` CLI, and the 002
intake (`validate_inputs`, `format_size.py`, `prompt_elements.py`).

---

## D1. The rerun-trigger mechanism (the brief's flagged open question)

**Decision**: The UI drives every (re)run by shelling out to the EXISTING conductor CLI with the
interactive gate OFF:
- first run: `conductor.py --brand <b> --thin --no-approve --inputs <single_sign.json>`
- nudge:     `conductor.py --brand <b> --thin --no-approve --inputs <single_sign.json> --style-notes "<note>"`

Each call (no `--out`) writes a NEW `output/run_<brand>_<timestamp>/` dir, so attempts are preserved
(matches the clarified "new run dir per attempt"). The taste gate lives in the UI (the human):
approve = stop calling; nudge = call again with `--style-notes`. The ONE conductor change is a
top-level `--style-notes` flag threaded (campaign-level) into `_scene_author_thin_argv`.

**Rationale**: The conductor already threads `--style-notes` to the thin `scene_author` on its
INTERACTIVE nudge path (`run_approve_gate`, lines ~722-744), and `assemble_thin_prompt` already turns
`style_notes` into a binding clause. Exposing the same as a non-interactive top-level flag is the
smallest possible surface and keeps ALL generation/rerun orchestration in the agent-free conductor —
the UI never re-implements it (constitution §I/§VII; the brief's stated "likely answer"). `--no-approve`
already exists and bypasses the terminal `input()` gate, so the UI is not blocked by it.

**Alternatives considered**:
- UI re-implements the rerun (re-invoke `scene_author` itself): REJECTED — violates the thin posture;
  duplicates the conductor's prep chain (register/calibrate/intent).
- Make the conductor's `run_approve_gate` browser-drivable (a socket / HTTP gate): REJECTED — far more
  surface than a one-flag pass-through; the UI-as-gate + `--no-approve` already covers it.
- Reuse the same run dir per nudge (pass `--out`): REJECTED by the clarification (new dir per attempt).

---

## D2. UI stack (deferred to plan by the brief)

**Decision**: A LOCAL web app = stdlib `http.server` server (`frontend/server.py`) + ONE static HTML
page with inline vanilla JS (`frontend/index.html`). No framework, no bundler, no new dependency.

**Rationale**: The repo is stdlib-first (the conductor is stdlib-only by design); a single-operator
local test instrument does not justify an npm/React toolchain. A stdlib server keeps the surface thin
(constitution §VII), runs with `python frontend/server.py` and nothing to install, and is trivial to
keep "thin over the CLI" (the server only writes the inputs JSON, shells out, and reads the run dir).
Vanilla JS polling renders stages progressively with no build step.

**Alternatives considered**: React/Vue + a dev server (REJECTED — new toolchain, build step, deps for
a single-user local tool); a TUI (REJECTED — the brief locks a browser UI so the operator can see the
`generated.png`); Flask/FastAPI (REJECTED — a new dependency where `http.server` suffices).

---

## D3. Progressive stage rendering (clarified)

**Decision**: The browser polls `GET /run/<id>/stages` (~1s) while a run is in flight;
`frontend/run_view.py` reads the run dir and reports, per stage, presence + content: brief echo,
`register_profile.json` (dial), `sign_s1/final_prompt.txt` (assembled prompt), `sign_s1/generated.png`
(sign), plus `conductor_manifest.json` notes. Each stage renders as soon as its artifact exists, so
the dial + prompt show BEFORE the paid image returns.

**Rationale**: The thin route writes artifacts incrementally in this order
(`subfields → calibration → register_profile → intent_s1 → sign_s1/final_prompt.txt →
sign_s1/generated.png → conductor_manifest.json`), so polling the dir surfaces them progressively for
free — no streaming protocol, no conductor change. The falsifiable property lives in `run_view` (per-
artifact presence reporting over a synthetic partial run dir), independent of the live server.

**Alternatives considered**: server-sent events / websockets (REJECTED — more surface than polling for
a localhost single-user tool); render-on-complete (REJECTED by the clarification — blinds the operator
to the dial/prompt before the paid image).

---

## D4. Single-sign verbatim intake (FR-001/FR-002/FR-003)

**Decision**: `frontend/inputs_writer.py` is a PURE function: single-sign form state → the 002-shape
inputs JSON, with exactly one `signs[]` entry, every literal value byte-for-byte (no rephrase /
reorder / inference). It renders the 002 contract (`specs/002-faithful-brief-intake/contracts/
inputs-schema.md`), NOT the stale repo-root `brief_schema.json`. The output MUST satisfy
`conductor.validate_inputs`.

**Rationale**: The 002 pivot killed the lossy prose→fields translator; the form is the faithful
substitute. Making the writer a pure function lets the test assert byte-for-byte equality (messages,
mandatory_elements, the three vibe integers) + the one-sign invariant + `validate_inputs` acceptance
with no server and no paid call. Reuses the 002 schema as the single source of truth.

**Alternatives considered**: an NL prose box parsed by an LLM (REJECTED on principle — the confound
002 removed). Rendering `brief_schema.json` (REJECTED — stale field names; would fail verbatim intake).

---

## D5. Stage reader honest nulls (FR-010 / constitution §V)

**Decision**: `run_view` reports each artifact as present-with-content OR absent; on absent (e.g. an
honest-null blank sign, or a step that failed) it surfaces the null + the relevant
`conductor_manifest.json` note. It never fabricates a placeholder image or value.

**Rationale**: Constitution §V. The manifest already records honest-null notes; the UI's job is to
SHOW them, not hide the gap. Falsifiable: a synthetic run dir missing `generated.png` yields an
"absent + note" stage, not a fabricated one.

---

## D6. No paid generation in tests (FR-012 / cost discipline)

**Decision**: Tests target the three pure modules — `inputs_writer`, `run_view`,
`runner.build_conductor_argv` — plus a conductor dry-run for the `--style-notes` thread. The server's
`POST /run` shells out to the paid conductor only on a human click; no test calls it. The one paid
single-sign run (~$0.08) is the human's eye-gate after the build.

**Rationale**: Constitution cost discipline. Splitting the side-effecting launch (`runner.launch`)
from the pure `build_conductor_argv` keeps the trigger testable without spending.

---

## Reuse summary (verified against code)

| Existing capability | File | Reused for |
|---------------------|------|-----------|
| `--thin --no-approve --inputs` run, timestamped run dir | `harness/conductor.py` | D1 trigger (each call = new run dir) |
| `--style-notes` → thin `scene_author` (interactive nudge today) | `harness/conductor.py` + `scene_author.py` | D1 nudge (exposed as a top-level flag) |
| `assemble_thin_prompt(style_notes=...)` binding clause | `harness/scene_author.py` | D1 nudge prompt |
| `validate_inputs` (002, accepts the new fields, back-compat) | `harness/conductor.py` | D4 form output validation |
| 002 inputs schema + `format_size.py` + `prompt_elements.py` | feature 002 | D4 form contract |
| run-dir artifact contract (register_profile / final_prompt / generated.png / manifest) | thin route | D3/D5 stage reader |

| Genuinely NEW | Why nothing existing covers it |
|---------------|-------------------------------|
| `frontend/` (server + page + inputs_writer + run_view + runner) | No UI / form / stage-reader exists |
| conductor top-level `--style-notes` | Only the interactive gate threads it today; the UI needs a non-interactive surface |
