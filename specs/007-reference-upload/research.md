# Phase 0 Research: Reference-image Upload in the Live-runner

The spec's decisions are LOCKED by the 006 precedent; the only genuinely open items are the two the
brief flagged for `/speckit-plan`. Both are resolved here, grounded in the confirmed code (read
2026-06-29). No NEEDS CLARIFICATION remains.

## Decision 1: Where the shared `save_upload` helper lives

**Decision**: A NEW tiny module `frontend/uploads.py` exposing
`save_upload(file_tuple, dest_dir, name=None) -> str`. NOT folded into `frontend/multipart.py`.

**Rationale**:
- `frontend/multipart.py` is documented and built as PURE (its docstring: "PURE (bytes in, dict out) so
  it is unit-testable without HTTP"; no filesystem import). Adding a function that WRITES bytes to disk
  would break that single responsibility and make the module no longer a pure parser. `test_multipart.py`
  asserts a pure round-trip; keeping `multipart.py` filesystem-free preserves that test surface intact.
- The save-upload step is a distinct concern (take a parsed `(filename, bytes)` tuple, write it under a
  dest dir, return the path). A small dedicated module is the honest home and is trivially unit-testable
  on its own (`test_reference_upload.py` writes to a tmp dir and asserts the bytes + path).
- Symmetry with the existing split: `multipart.py` parses the wire; `uploads.py` lands the file. Both
  stay tiny and stdlib-only.

**Alternatives considered**:
- *Fold into `multipart.py`*: rejected. Mixes parsing (pure) with disk I/O (effectful); muddies the
  proven pure module and its test.
- *Fold into `brand_intake/persist.py`*: rejected. `persist.py` is the brand-write home (place logo +
  write key + id-collision under `answer_keys/` and `brands/`); a generic frontend upload-saver does not
  belong there, and it would couple the 004 run path to the brand-onboarding module.
- *Inline at each call site (status quo for 006)*: rejected. That is exactly the duplication 007 removes
  (Decision 2).

## Decision 2: Refactor 006's logo-save onto the shared helper NOW (same change) vs only add 004's call site

**Decision**: Refactor 006's logo-save onto `save_upload` in the SAME change. Both the new `/run`
reference-save and the existing `/onboard/save` logo-save call `save_upload`.

**Rationale**:
- The brief's DRY requirement (and constitution §VII) wants ONE save-upload home. Today
  `server.py` `_onboard_save` does the save-upload inline (lines 154-160: make a temp dir, write
  `logo[1]` bytes to `tmp/logo[0]`, pass the path to `persist.place_logo`). That IS the save-upload
  pattern; leaving it inline while adding a parallel saver for `/run` would create two homes for one
  step, the opposite of the goal.
- Two real call sites prove the helper GENERALIZES (constitution §IV) rather than being a one-use wrapper
  shaped to the reference case. The refactor is small (replace ~5 lines with one call) and stays in the
  same commit, so the helper is never speculative.
- Behavior is preserved: the logo still lands in a temp file that `persist.place_logo` reads and copies
  under `brands/<brand>/`; only the "write the uploaded bytes to a temp path" step is now shared.

**Alternatives considered**:
- *Only add 004's call site, leave 006 inline*: rejected. Leaves the duplication the brief calls out;
  defers the DRY win with no benefit (the refactor is trivial and low-risk).
- *Refactor 006 in a separate later spec*: rejected. Same-change refactor is cheaper (one test pass over
  both call sites) and the helper has no reason to exist single-use.

## Decision 3: The `/run` multipart shape (other fields + the reference file)

**Decision**: The browser posts `POST /run` as `multipart/form-data` with ONE text field `form` carrying
`JSON.stringify(formState)` plus one file part `reference`. The server parses with the existing
`multipart.parse_multipart`, reads `fields["form"]` (JSON) for the brief, and `files["reference"]` for
the upload.

**Rationale**:
- Mirrors the proven `/onboard/save` shape exactly (a `verified` JSON field + a `logo` file part), so
  the server code and the client `FormData` code are consistent across the two upload routes (one mental
  model). No new parser, no new convention.
- Keeping the brief as ONE JSON field (rather than scattering ~15 fields as individual multipart parts)
  preserves the 002 verbatim invariant trivially: the strings (messages, mandatory_elements) round-trip
  as JSON exactly as they do today over the JSON `/run` body. `inputs_writer.to_inputs` is unchanged.

**Alternatives considered**:
- *One multipart field per brief field*: rejected. More wire surface, more parsing, and multi-line
  textareas (messages) are cleaner as JSON than as repeated form fields.
- *Keep `/run` JSON + a separate upload endpoint that returns a path the client re-sends*: rejected. Two
  round-trips and a client-held server path (the footgun we are removing); a single multipart POST is
  simpler and matches 006.

## Decision 4: Where the reference is saved + naming + ordering

**Decision**: Save the reference INTO the per-run dir as `reference<ext>` (extension from the uploaded
filename; basename-sanitized to prevent path traversal), via `save_upload(file_tuple, run_dir,
name="reference"+ext)`. Inject that saved path into the form dict as `reference_image` BEFORE
`write_inputs`. Order: parse -> require a reference file (fail loud 400 if absent) -> validate brand ->
acquire single-flight -> mkdir run_dir -> save the reference -> inject path -> write_inputs -> launch.

**Rationale**:
- Co-locating the reference with the run's artifacts (`output/run_*/`) keeps the run auditable (the
  inputs JSON and the exact reference that produced the sign sit together). The brief's example is
  `run_*/reference.png`.
- The missing-reference check moves from "non-empty string" to "a `reference` file part is present", and
  fires BEFORE the run dir is created / single-flight is acquired, so a missing reference launches
  nothing (FR-005 / US2). `save_upload` runs only after the run dir exists.
- Sanitizing to the basename closes a path-traversal hole an uploaded `filename` could otherwise open.

**Alternatives considered**:
- *Save to a shared temp then move*: rejected. Unnecessary; the run dir already exists at save time and
  is the final auditable home.
- *Keep the uploaded filename verbatim*: acceptable but a fixed `reference<ext>` is tidier and avoids odd
  filenames in the run dir; either passes the tests (the test asserts the file EXISTS and its path is in
  the JSON, not a specific name).

## Reuse map (what is touched vs untouched)

| Component | 007 disposition |
|-----------|-----------------|
| `frontend/multipart.py` | UNCHANGED (reused; stays pure) |
| `frontend/inputs_writer.py` | UNCHANGED (still reads `reference_image` as a path from the form dict) |
| `frontend/uploads.py` | NEW (the shared save-upload helper) |
| `frontend/server.py` `/run` | CHANGED (JSON -> multipart; save + inject; fail-loud on missing reference) |
| `frontend/server.py` `_onboard_save` | CHANGED (logo-save refactored onto `save_upload`; behavior preserved) |
| `frontend/index.html` | CHANGED (file input replaces typed path; FormData submit) |
| conductor / thin route / `scene_author --ref-image` / generate | UNCHANGED (the input contract is the durable boundary) |
| `runner.build_conductor_argv` | UNCHANGED |
