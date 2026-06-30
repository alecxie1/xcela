# Phase 1 Data Model: Reference-image Upload in the Live-runner

No database. The "entities" are the in-flight shapes the upload flows through. The durable boundary (the
inputs JSON contract the conductor reads) is UNCHANGED; only the frontend's source of `reference_image`
changes.

## Multipart `/run` request

The browser posts `multipart/form-data` to `POST /run`:

| Part | Type | Content |
|------|------|---------|
| `form` | text field | `JSON.stringify(formState)` - all the brief fields EXCEPT the reference (brand, asset_type, format_size, vibe, messages, mandatory_elements, ...). Verbatim strings (002 invariant). |
| `reference` | file part | the uploaded reference image: `(filename, bytes)` after parse. |
| `style_notes` | text field (optional) | the nudge note on a re-run (today carried as a JSON field; rides as a form field here). |

Parsed by `multipart.parse_multipart(body, content_type)` -> `{fields: {form, style_notes?}, files:
{reference}}`. No reference file part -> fail loud (400), no run launched.

## Uploaded reference file (the multipart file tuple)

- Shape: `(filename: str, bytes: bytes)` - the `multipart.py` file-tuple contract.
- Validation: presence is REQUIRED (v1). Bytes are NOT inspected for image-ness in v1 (a bad image fails
  loud at the paid generation step, the existing 004 behavior).
- Saved by `save_upload(file_tuple, run_dir, name="reference"+ext)` -> a path string. `ext` is taken
  from the uploaded filename; the saved name is basename-only (no path separators -> no traversal).

## Saved reference + the run dir

- Location: `output/run_<brand>_<timestamp>/reference<ext>` (inside the per-run dir, beside `inputs.json`
  and the generated artifacts). Auditable: the exact reference that produced the sign is co-located.
- Lifecycle: written once at run start; persists with the run (not transient like 006's draft).

## Inputs JSON (`output/run_*/inputs.json`) - UNCHANGED contract

- `reference_image`: a PATH string on disk. Today: the designer-typed absolute path. After 007: the
  server-saved path returned by `save_upload`. The KEY, the type (path), and every other field are
  unchanged. `inputs_writer.to_inputs` is not modified - the server injects the saved path into the form
  dict as `reference_image` before calling `write_inputs`.
- The 002 verbatim fields (`messages`, `mandatory_elements`, `forbidden_elements`, occasion, etc.) pass
  through exactly as today (they ride in the `form` JSON field, decoded and parsed, handed to
  `to_inputs` unchanged).
- `reference_image` is a FILE LOCATION, not typed brand CONTENT, so a server-assigned saved path does
  NOT violate the 002 faithful-intake invariant (that rule forbids rephrasing typed content like
  messages / mandatory_elements, not relocating an input file).

## `save_upload` helper (the shared write step)

- Signature: `save_upload(file_tuple, dest_dir, name=None) -> str`.
- Input: a `(filename, bytes)` tuple (from `multipart.parse_multipart`), a destination directory, an
  optional explicit save name.
- Behavior: ensure `dest_dir` exists; compute the save name (`name` if given, else the uploaded
  filename), reduced to its basename; write the bytes to `dest_dir/<save_name>`; return the path string.
- Guarantee: bytes preserved byte-for-byte (binary round-trip). No default substitution, no fabrication.
- Call sites: (a) `/run` reference-save (dest = the run dir, name = `reference<ext>`); (b) the refactored
  `_onboard_save` logo-save (dest = the onboard temp dir, name = the uploaded logo filename). Behavior at
  (b) is preserved; only the inline write becomes a `save_upload` call.

## Validation rules (where each FR is enforced)

| Rule | Where | FR |
|------|-------|----|
| Reference file part REQUIRED; absent -> 400, no run | `server.py` `/run`, before mkdir/single-flight | FR-005 |
| Reference saved into the run dir; that path is `reference_image` | `server.py` `/run` via `save_upload` + inject | FR-003 |
| Uploaded bytes preserved exactly | `save_upload` | FR-004 |
| Other brief fields verbatim | `inputs_writer.to_inputs` (unchanged) | FR-008 |
| `reference_image` stays a path; contract unchanged | `inputs_writer` + conductor (unchanged) | FR-006 / FR-009 |
| One save-upload home, two call sites | `frontend/uploads.py` used by `/run` + `_onboard_save` | FR-007 |
