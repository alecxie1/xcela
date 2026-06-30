# Feature Specification: Reference-image Upload in the Live-runner

**Feature Branch**: `007-reference-upload`

**Created**: 2026-06-29

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief (`specs/_inbox/007-reference-upload.md`). The 004 live-runner takes the
reference image as a TYPED absolute server path (`<input placeholder="/abs/path/to/reference.png">`),
while the 006 onboarding screen in the SAME local `frontend/` app takes the brand PDF + logo as real
file UPLOADS. That seam is inconsistent and designer-hostile: a designer will not know or want to type
`/abs/path/...`, and a typo becomes a silent file-not-found at the paid generation step. The typed-path
field was a deliberate v1 shortcut justified by "the single operator on his own machine"; the tool has
since moved to a designer-facing surface (the whole point of 006), so that justification no longer holds.
006 already BUILT and PROVED the upload machinery (`frontend/multipart.py`, 3/3 tested; the
save-upload-to-disk then pass-the-path pattern), so making 004 consistent is now cheap.

> **Scope note (constitution §IV / §VII):** 007 is a SURFACE change over a proven organ. It reuses the
> existing 006 `frontend/multipart.py` parser and the save-upload-to-disk pattern, swaps ONE form field
> (typed path to file upload) and the one route that reads it, and factors the save-upload step into a
> shared helper both the 004 reference-save and the 006 logo-save call. It does NOT change generation,
> register, prompt assembly, or the conductor / CLI input contract.

> **The contract this feature preserves (the standing rule):** the frontend adapts to the back-half,
> never the reverse. `reference_image` stays a PATH on disk in the inputs JSON; the conductor, the thin
> route, `scene_author --ref-image`, and generation are all untouched. Only the frontend's SOURCE of
> that path changes (server-assigned saved file instead of designer-typed string).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload the reference image instead of typing a path (Priority: P1)

The designer opens the live-runner in the browser, fills in the single-sign brief, and picks the
reference image from disk with a file picker (no path typing anywhere). On run, the sign generates from
the uploaded file.

**Why this priority**: This IS the feature. Without the upload the designer still has to know and type
an absolute server path, the exact footgun (silent file-not-found at the paid step) and the
inconsistency with 006 that 007 removes. One field changes; the whole designer-facing flow becomes
consistent.

**Independent Test**: Post a multipart `/run`-style body (a reference file + the form fields) and
confirm the assembled inputs JSON's `reference_image` points to a real saved file in the run dir
(assert the file exists on disk AND its path is in the JSON), WITHOUT launching paid generation (test
the parse + save + inputs assembly, not the run launch). Free, no model calls.

**Acceptance Scenarios**:

1. **Given** the live-runner page, **When** the designer views the reference field, **Then** it is a
   file picker (file input), not a typed-path text field.
2. **Given** a filled brief and a picked reference file, **When** the designer runs, **Then** the
   uploaded file is saved into the run dir and that saved path is placed into the inputs JSON as
   `reference_image`, and the run consumes it unchanged.
3. **Given** the uploaded reference file, **When** it is saved, **Then** its bytes are preserved exactly
   (binary round-trip), co-located with the run's artifacts (auditable).

### User Story 2 - Missing reference fails loud (Priority: P1)

The designer runs without picking a reference file; the run is rejected with a clear error and nothing
is launched.

**Why this priority**: The reference is REQUIRED in v1 (unchanged from 004). The existing required-string
check moves to a required-upload check; it must stay loud, never silently proceed to a paid run with no
reference.

**Independent Test**: Post a `/run`-style multipart body with NO reference file and confirm the request
fails loud (4xx / raises) and no run is launched (no run dir written, generation never called). Free.

**Acceptance Scenarios**:

1. **Given** a run request with no reference file, **When** it is processed, **Then** it fails loud
   (clear error) and no run is launched.

### User Story 3 - One shared save-upload home; back-half + CLI unchanged (Priority: P1)

The new reference-save and the existing 006 logo-save go through ONE shared save-upload helper (DRY),
and everything downstream (inputs assembly verbatim for the other fields, the conductor, the standalone
CLI) keeps working untouched.

**Why this priority**: This is the correctness + regression guard. The upload is a frontend convenience
that produces a path; the agent-free core must be provably unaffected, and the save-upload logic must
not be duplicated between 004 and 006.

**Independent Test**: (a) The shared `save_upload` helper writes uploaded bytes to a real file under a
dest dir and returns its path, bytes preserved (reuse the multipart round-trip evidence). (b) The 002
verbatim invariant for the OTHER fields (messages / mandatory_elements) still holds through inputs
assembly. (c) `conductor --thin --inputs <json>` with a `reference_image` path still runs end to end
with the frontend absent (the input contract is unchanged). All free, no model calls.

**Acceptance Scenarios**:

1. **Given** an uploaded file and a dest dir, **When** the shared save-upload helper runs, **Then** it
   writes the bytes to a real file under that dir and returns the path, bytes preserved.
2. **Given** the other brief fields (messages, mandatory_elements), **When** the inputs JSON is
   assembled from a multipart run, **Then** those fields pass through verbatim (the 002 invariant holds).
3. **Given** an inputs JSON with a `reference_image` path and the frontend absent, **When**
   `conductor --thin --inputs <json>` runs, **Then** it runs end to end (the contract is unchanged).

### Edge Cases

- No reference file uploaded → fail loud (4xx / raises), no run launched (US2). Same loudness as today's
  required-string check; only the input modality changes.
- A bad / corrupt / non-image uploaded file → accepted in v1; it fails loud at the paid generation step
  (the existing 004 behavior). Tightening to image types is a later enhancement, not v1.
- A `reference_image` that is a FILE LOCATION, not typed brand CONTENT → a server-assigned saved path is
  fine and does NOT violate the 002 faithful-intake invariant (that rule forbids rephrasing typed brand
  content like messages / mandatory_elements, not relocating an input file).
- The standalone CLI run with the frontend absent → unaffected; `reference_image` is still a path, so the
  agent-free core path needs no upload (regression guard, US3).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The live-runner page MUST present the reference image as a real file UPLOAD (a file
  picker), and the typed absolute-path text field MUST be removed entirely (no dual path-or-upload
  input; the dual UX is the inconsistency being removed).
- **FR-002**: The run submission MUST carry the reference file as a real upload; the server MUST parse it
  with the EXISTING `frontend/multipart.py` parser (no new parser, no new dependency).
- **FR-003**: The system MUST save the uploaded reference file INTO the run dir (co-located with the
  run's artifacts) and put THAT saved path into the inputs JSON as `reference_image`.
- **FR-004**: Uploaded reference bytes MUST be preserved exactly when saved (binary round-trip), so the
  saved file is the file the designer picked.
- **FR-005**: A run submitted with NO reference file MUST fail loud (a clear 4xx error / raise) and MUST
  NOT launch a run (reference required in v1, unchanged from 004).
- **FR-006**: The conductor / CLI input contract MUST be UNCHANGED: `reference_image` is still a path on
  disk in the inputs JSON; the conductor, the thin route, `scene_author --ref-image`, and generation are
  untouched. Only the frontend's source of that path changes.
- **FR-007**: The save-upload step (write uploaded bytes to a dest dir, return the path) MUST be factored
  into ONE shared helper used by BOTH the new 004 reference-save and the 006 logo-save (DRY); the
  logic MUST NOT be duplicated between 004 and 006.
- **FR-008**: The 002 faithful-intake invariant MUST still hold for the OTHER fields: typed brand content
  (messages, mandatory_elements) passes through inputs assembly verbatim. A server-assigned saved path
  for `reference_image` (a file location, not typed content) does NOT violate that invariant.
- **FR-009**: The standalone `conductor --thin --inputs <json>` path (with a `reference_image` path) MUST
  still run end to end with the frontend absent; the upload adds no dependency the CLI needs.
- **FR-010**: No paid model calls in any automated test; tests cover the multipart parse + the
  save-upload helper + the inputs assembly + the fail-loud path, never `runner.launch` / generation. The
  one paid sign (the UX eye-gate) folds into 004's pending T016, run AFTER the build.
- **FR-011**: No em-dashes in any user-facing text (Output rule).

### Key Entities

- **Uploaded reference image**: the file the designer picks in the browser; saved into the run dir,
  consumed by the conductor as a path. Replaces the designer-typed absolute path.
- **Run dir**: the per-run artifact directory (`run_*`); now also holds the saved reference, named
  `reference` + the uploaded file's original extension (e.g. `run_*/reference.jpg`), keeping it auditable
  and honestly typed beside the run's other artifacts.
- **Shared save-upload helper**: the one save-upload-to-disk step (uploaded file + dest dir to a saved
  path), called by both the 004 reference-save and the 006 logo-save. [Its LOCATION (a new
  `frontend/uploads.py`, or folding into `frontend/multipart.py`) and whether to refactor 006's
  `/onboard/save` logo-save onto it in the SAME change vs only adding 004's call site is a
  `/speckit-plan` decision.]
- **Inputs JSON**: the 002 inputs contract the conductor reads; `reference_image` stays a path on disk,
  now server-assigned (the saved upload) instead of designer-typed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A designer runs a single-sign brief entirely in the browser, picking the reference file
  from disk (no typed path anywhere), and the sign generates from it. (eye + structural)
- **SC-002**: Given a multipart `/run`-style body with a reference file + the form fields, the assembled
  inputs JSON's `reference_image` points to a REAL saved file in the run dir (the file exists AND the
  path is in the JSON), with no paid generation launched. (structural, falsifiable)
- **SC-003**: The shared save-upload helper writes uploaded bytes to a real file under a dest dir and
  returns its path, bytes preserved (binary round-trip). (structural, falsifiable)
- **SC-004**: A `/run` (or the assembly step) with NO reference file fails loud (4xx / raises) and no
  run is launched. (structural, falsifiable)
- **SC-005**: The 002 verbatim invariant for the other fields (messages / mandatory_elements) still
  holds through inputs assembly. (structural, falsifiable)
- **SC-006**: `conductor --thin --inputs <json>` with a `reference_image` path still runs end to end
  with the frontend absent (the input contract is unchanged). (structural, regression guard)
- **SC-007**: The served live-runner page uses a file input for the reference, not a typed-path text
  field (structural grep). (structural, falsifiable)
- **SC-008**: No paid model calls occur in any automated test; the one paid sign is the UX eye-gate
  folded into 004's pending T016, run after the build. (process)

> The eye-marked criterion (SC-001) is a human-eye judgment per constitution §II; no VLM self-score
> counts as proof. Automated tests assert STRUCTURE only (the save-upload round-trip, inputs points at
> the saved file, fail-loud, the verbatim invariant, the standalone CLI, the file-input grep), never
> pixel quality.

## Assumptions

- The live-runner is the same LOCAL single-designer `frontend/` app extended by 006; the reference
  upload follows the proven 006 upload pattern (stdlib multipart parse + save-to-disk then pass-the-path),
  not a new stack. The UI / route shape follows the 004 + 006 server precedent, confirmed at
  `/speckit-plan`.
- The reference stays REQUIRED in v1 (unchanged from 004); the ref-less thin path remains deferred.
- v1 accepts any uploaded file type; a bad image fails loud at the paid generation step (the existing
  behavior). Tightening to image types is a later enhancement.
- The conductor / CLI input contract is the durable boundary: `reference_image` is a path on disk. The
  frontend adapts to it; the back-half is never changed for this feature.
- `frontend/multipart.py` (006) is the parser of record (3/3 tested, binary bytes preserved); 007 adds no
  parser and no dependency.
- The shared save-upload helper's LOCATION and whether 006's logo-save is refactored onto it in the SAME
  change are OPEN QUESTIONS for `/speckit-plan`, resolved against the 004 + 006 server shapes and the DRY
  + thin-surface rules.
- The one paid sign (the UX eye-gate) folds into 004's pending T016; 007 ships no separate paid run.

## Out of Scope (v1)

- The ref-less thin path (still deferred from 004; the reference is required in v1).
- Multi-file / batch reference upload, drag-and-drop polish, client-side image preview (nice-to-haves).
- Any change to generation, register, prompt assembly, or the conductor input contract.
- Tightened reference / logo file-type or size validation (later enhancement; v1 accepts any file and
  fails loud at the paid step).
- A power-user typed-path option alongside the upload (the dual UX is exactly what is being removed; a
  later enhancement only if ever needed).
- A separate paid run for 007; the one paid sign is folded into 004's pending T016.
