# Implementation Plan: Reference-image Upload in the Live-runner

**Branch**: `007-reference-upload` (working on `006-web-onboarding-gate`) | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-reference-upload/spec.md`

## Summary

The 004 live-runner takes the reference image as a TYPED absolute server path
(`frontend/index.html:45`); the 006 onboarding screen in the SAME app takes the brand PDF + logo as
real UPLOADS. 007 closes that seam: the live-runner takes the reference as a file UPLOAD, the typed-path
field is gone, and the run consumes the uploaded file. Everything downstream is unchanged because the
conductor already reads `reference_image` as a path on disk; only the frontend's SOURCE of that path
changes (a server-saved upload instead of a designer-typed string).

This is a SURFACE change over a proven organ. It reuses the existing 006 `frontend/multipart.py` parser
(3/3 tested, binary-preserving) and the save-upload-to-disk-then-pass-the-path pattern 006 already runs
in `/onboard/save`. The two open questions the brief flagged for the plan are RESOLVED here, grounded in
the code:

1. **The shared save-upload helper lives in a NEW `frontend/uploads.py`** (not folded into
   `multipart.py`). `multipart.py` is documented PURE (bytes in, dict out, no filesystem) so it is
   unit-testable without disk; writing bytes to a dest dir is a separate concern. A tiny new module
   keeps both single-responsibility. Signature: `save_upload(file_tuple, dest_dir, name=None) -> str`
   (a `(filename, bytes)` multipart tuple + a destination dir to a saved path).
2. **006's logo-save IS refactored onto the shared helper in this SAME change** (DRY now). The inline
   logo-save in `server.py` `_onboard_save` (the `OUTPUT/.onboard_tmp` write, lines 154-160 today) is
   exactly this pattern; pointing it at `save_upload` removes the duplication immediately and gives the
   helper TWO real call sites (it generalizes, constitution §IV), all in one commit. The differing
   downstream (reference into the run dir for the conductor vs logo into a temp for `persist.place_logo`)
   stays at the call sites; only the write step is shared.

The `/run` route changes from JSON-only to multipart: the browser posts the other brief fields as ONE
JSON field (`form`) plus the `reference` file part (mirroring `/onboard/save`'s `verified` field + `logo`
file). The server parses, saves the reference into the run dir via `save_upload`, injects that path into
the form dict as `reference_image`, and calls `inputs_writer.write_inputs` UNCHANGED. `inputs_writer`,
the conductor, the thin route, and generation are all untouched.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`). Frontend = the existing stdlib `http.server` app
(`frontend/`); the live-runner screen is vanilla JS (no framework/build).

**Primary Dependencies**: none new. Reuses `frontend/multipart.py` (006), `frontend/inputs_writer.py`
(004, unchanged), the 004 server pattern, and the conductor thin route (unchanged).

**Storage**: Files. The uploaded reference is saved INTO the per-run dir (`output/run_*/reference<ext>`),
co-located with the run's artifacts (auditable); its path goes into `run_*/inputs.json` as
`reference_image`. No new persistent store.

**Testing**: Falsifiable STRUCTURAL self-tests in the `test_*.py` style (stdlib + a synthetic multipart
body, mirroring `test_multipart.py`). NO paid model calls; tests target the PURE `save_upload` helper +
the parse-save-assemble path + the fail-loud path, never `runner.launch` / generation. The one paid sign
(the UX eye-gate) folds into 004's pending T016.

**Target Platform**: Localhost web app on the designer's machine (same host runs the CLI). Single-operator,
single-flight, single-sign.

**Project Type**: Single project + the thin local web frontend (one field + one route changed, one new
tiny module).

**Performance Goals**: Not latency-bound. Saving the upload is a local byte write; the only paid step is
generation (unchanged, behind the existing single-flight Run button).

**Constraints**: THIN over the agent-free core. The conductor / CLI input contract is UNCHANGED
(`reference_image` = a path on disk); the frontend adapts. REUSE `multipart.py` (no new parser/dep).
Factor the save-upload step into ONE shared helper (DRY, used by 004 + 006). Reference REQUIRED in v1 ->
fail loud on missing. The standalone CLI runs with the frontend absent. The 002 verbatim invariant holds
for the other fields. No em-dashes in user-facing text.

**Scale/Scope**: v1 = swap ONE form field (typed path -> file upload) + the one route that reads it +
one shared helper + the 006 logo-save call site onto that helper. No file-type validation, no batch
upload, no ref-less path, no back-half change (all out of scope).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The reference is a human INPUT gate; the change makes that input a file pick instead of a typed path. No model is added; no step is auto-glued. The human still supplies the reference and judges the pixels. | PASS |
| II. Ground truth = the eye | Tests assert STRUCTURE only (the save-upload round-trip, inputs points at the saved file, fail-loud, the verbatim invariant, the standalone CLI, the file-input grep). The one paid sign is the human's UX eye-gate (folded into 004 T016). No VLM PASS as proof. | PASS |
| III. Falsifiable tests only | `save_upload` writes real bytes to a real file and returns its path (bytes preserved); the assembled inputs JSON's `reference_image` points at a file that EXISTS in the run dir; missing reference RAISES / 4xx with no run launched; messages/mandatory_elements pass through verbatim; the standalone CLI still runs; the page uses a file input. Each fails a wrong build (a value, not token-presence). | PASS |
| IV. Generalize, do not hand-tune | The shared `save_upload` helper serves BOTH 004 (reference) and 006 (logo) - two call sites, no brand/task literals. No tuning to one image. | PASS |
| V. Honest nulls, never invented | No reference -> fail loud (4xx / raise), no run launched, no fabricated path. A bad image still fails loud at the paid step (existing behavior). Nothing is invented. | PASS |
| VI. Reconciliation per-dimension | Untouched. The reference still sets MAGNITUDE via the analyzer downstream; 007 only changes how the reference FILE reaches the conductor (a path, unchanged contract). | PASS |
| VII. Repo is durable; thin / reuse | Stdlib only (no new dep; reuse `multipart.py`); the conductor/CLI contract is unchanged and the standalone CLI runs with the frontend absent; the shared helper keeps 004 + 006 writing uploads identically (DRY); one-module-one-test-one-commit; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid model calls in any automated test; the change is on the FREE intake surface.
The one paid sign is the human's UX eye-gate folded into 004's pending T016. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/007-reference-upload/
├── spec.md              # Feature spec
├── plan.md              # This file
├── research.md          # Phase 0: the two open questions resolved (helper location; refactor 006 now)
├── data-model.md        # Phase 1: the multipart /run shape, saved reference, inputs contract
├── contracts/
│   ├── uploads-contract.md     # the shared save_upload(file_tuple, dest_dir, name) helper
│   └── http-run-endpoint.md    # POST /run as multipart (form JSON field + reference file)
├── quickstart.md        # Phase 1: free structural validation + the human browser smoke
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── uploads.py           # NEW (stdlib, small): save_upload(file_tuple, dest_dir, name=None) -> str.
│                        #   Writes a multipart (filename, bytes) tuple into dest_dir (basename-sanitized)
│                        #   and returns the saved path; bytes preserved. The ONE save-upload home.
├── multipart.py         # UNCHANGED. Stays PURE (bytes in, dict out); the new helper is the disk side.
├── inputs_writer.py     # UNCHANGED. Still reads `reference_image` as a path from the form dict.
├── server.py            # CHANGED: POST /run now parses multipart (form JSON field + `reference` file),
│                        #   fails loud on a missing reference, saves it into the run dir via save_upload,
│                        #   injects that path as form["reference_image"], then write_inputs (unchanged).
│                        #   _onboard_save's inline logo-save is refactored onto save_upload (DRY).
└── index.html           # CHANGED: the reference text input -> <input type="file">; the typed-path field
                         #   is removed; startRun posts FormData (form JSON + reference file); the
                         #   client-side guard checks a file is picked, not a non-empty string.

test_reference_upload.py # NEW: falsifiable structural self-test (no paid calls). save_upload round-trips
                         #   bytes to a real file; a synthetic multipart /run-style body -> inputs JSON
                         #   reference_image points at a file that EXISTS in the run dir; missing reference
                         #   fails loud (no run launched); messages/mandatory_elements verbatim; standalone
                         #   conductor --thin contract intact; the served page uses a file input (grep).
```

**Structure Decision**: One new tiny PURE module (`frontend/uploads.py`) holds the save-upload step,
called by BOTH the new `/run` reference-save and the refactored 006 logo-save. `multipart.py` and
`inputs_writer.py` are UNCHANGED (the parser stays filesystem-free; the inputs writer still reads
`reference_image` as a path - the server just injects a server-assigned path instead of forwarding a
typed one). `server.py` changes the `/run` body from JSON to multipart and adds the save-then-inject
step; the conductor, thin route, and generation are untouched (FR-006 / SC-006). `index.html` swaps one
input and the submit encoding. The reference lands in the run dir beside the run's other artifacts
(auditable); only a present reference launches a run (fail-loud on missing, FR-005).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
