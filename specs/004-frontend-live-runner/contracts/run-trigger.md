# Contract: run trigger (the conductor CLI surface the UI calls)

The UI NEVER orchestrates generation. It builds + launches a plain conductor CLI call; the conductor
(agent-free) does all the work and writes a new run dir. This resolves the brief's flagged open
question (the conductor's interactive gate is a terminal `input()` loop, not browser-drivable).

## `runner.build_conductor_argv(inputs_path, brand, style_notes=None) -> list[str]`

Pure (no execution; testable free). Produces:

```
[PY, "harness/conductor.py", "--brand", <brand>, "--thin", "--no-approve",
 "--inputs", <inputs_path>] (+ ["--style-notes", <note>] iff style_notes)
```

- ALWAYS `--thin` + `--no-approve` + `--inputs`. NEVER `--out` (so each call makes a new
  `output/run_<brand>_<timestamp>/` dir — attempts preserved, clarified).
- `--style-notes` is added IFF a nudge note is supplied (the binding clause).

## `runner.launch(argv) -> run_dir`

The side-effecting half: runs the conductor as a subprocess, returns the new run-dir path (parsed
from the conductor's output / the newest `output/run_*` dir). Not exercised by automated tests (it
would spend); the human triggers it.

## Conductor change (the ONLY engine edit, harness/conductor.py)

Add a top-level `--style-notes` flag (campaign-level) threaded into `_scene_author_thin_argv` so a
non-interactive nudge-rerun is a plain CLI call. The conductor already threads `--style-notes` to the
thin `scene_author` on its INTERACTIVE nudge path and `assemble_thin_prompt` already consumes it; this
exposes the same capability non-interactively. Single-sign needs no other change (the per-sign loop
runs once for a 1-entry `signs[]`).

## Rules (falsifiable)

1. `build_conductor_argv` carries `--thin --no-approve --inputs` and no `--out`.
2. With a note, it additionally carries `--style-notes <note>` (verbatim).
3. `conductor.py --style-notes "x"` (dry-run, thin) yields a thin `scene_author` argv containing
   `--style-notes x` (the note reaches generation).
4. The conductor still runs the thin route from one command with the frontend absent (SC-005).
