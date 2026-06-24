# Contract: local HTTP endpoints (`frontend/server.py`)

A stdlib `http.server` local app (localhost, single-operator). Thin glue: it writes the inputs JSON,
shells out to the conductor, and reads the run dir. It holds NO generation/register/prompt logic.

| Route | Method | Behavior |
|-------|--------|----------|
| `/` | GET | serve `index.html` (the form + progressive stage panels + approve/nudge) |
| `/brands` | GET | list brand ids from `answer_keys/*.json` (the dropdown source) |
| `/run` | POST | body = form state (+ optional `style_notes`); `inputs_writer` → single-sign inputs JSON on disk; `runner.build_conductor_argv` + `launch`; return the new `run_id` (run-dir name) |
| `/run/<id>/stages` | GET | `run_view(run_dir)` → the stage dict (polled ~1s for progressive render) |
| `/run/<id>/image` | GET | serve `sign_s1/generated.png` for that run (404 until it lands) |

## Rules

1. Single-flight: while a run is in flight, `/run` is rejected/disabled until it reaches the taste
   gate (the instrument is single-operator, single-sign).
2. `/run` REQUIRES a `reference_image` (v1); it rejects a body without one (FR-005).
3. The server NEVER calls gpt-image-2 itself; it only launches the conductor (the paid step) on a
   human-initiated POST, with the real per-run cost (~$0.08) labeled in the UI (FR-009).
4. The paid path is never exercised by automated tests; tests target `inputs_writer`, `run_view`,
   and `build_conductor_argv` directly (FR-012 / cost discipline).
5. No em-dashes in any user-facing string the server or page emits (Output rule).
6. The server is OPTIONAL: the conductor thin route still runs from one CLI command with the server
   absent (FR-011 / SC-005).
