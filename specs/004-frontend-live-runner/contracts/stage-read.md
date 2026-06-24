# Contract: stage read (`run_view` over a run dir)

`run_view(run_dir) -> dict` reads the run dir's artifacts and reports each stage as present-with-
content OR absent-with-note. READ-ONLY; recomputes nothing. Polled progressively by the browser.

## Stages (from the thin route's write order)

| Stage key | Artifact | Content surfaced |
|-----------|----------|------------------|
| `brief` | `inputs.json` | the fields the conductor received |
| `register` | `register_profile.json` | inferred_register, formality, playfulness, anchors_held, locks_flexed |
| `prompt` | `sign_s1/final_prompt.txt` | the full assembled prompt text |
| `image` | `sign_s1/generated.png` | path (served by the http layer) |
| `notes` | `conductor_manifest.json` | honest-null / needs_review notes |

Each stage entry: `{ "present": bool, "content": <value or null>, "note": <manifest note or null> }`.

## Rules (falsifiable)

1. Reads the artifact PATHS above (SC-003: the UI consumes the agent-free artifacts, not a parallel
   in-UI computation).
2. Progressive: given a dir with `register_profile.json` + `final_prompt.txt` but no
   `generated.png`, `register` and `prompt` are `present: true` while `image` is `present: false`
   (the dial + prompt surface before the paid image).
3. A missing artifact yields `present: false` + the manifest note when one exists; it NEVER
   fabricates a placeholder value or image (honest null, §V).
4. A run dir that does not exist / is empty yields all-absent (no crash).
