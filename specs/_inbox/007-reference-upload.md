# SPEC BRIEF for /speckit-specify - Feature 007: Reference-image upload in the live-runner

Paste the body below as the /speckit-specify description (or point Claude Code at this file).
This is the DECISION MAP. Forks are nearly all settled by the 006 precedent; grounded in the ACTUAL
code (the 004 frontend + the 006 multipart machinery, both confirmed 2026-06-29). Alec drives
/speckit-specify; this is the substrate so the spec fills a known shape.

---

## Problem / why
The 004 live-runner takes the REFERENCE IMAGE as a typed absolute server path (an
`<input placeholder="/abs/path/to/reference.png">`), while the 006 onboarding screen, in the SAME
local `frontend/` app, takes the brand PDF + logo as real file UPLOADS. That seam is inconsistent and
not designer-friendly: a designer will not know or want to type `/abs/path/...`, and a typo silently
becomes a file-not-found at the paid generation step. The 004 path field was a deliberate v1 shortcut,
justified at the time by "the single operator on his own machine"; the tool has since moved toward a
designer-facing surface (the whole point of 006), so that justification no longer holds. 006 already
BUILT and PROVED the upload machinery (`frontend/multipart.py`, 3/3 tested; the save-to-disk ->
pass-the-path pattern), so making 004 consistent is now cheap.

## Goal (scopes "done")
In the live-runner, the designer UPLOADS the reference image (a file picker) instead of typing a path;
the run uses the uploaded file; the typed-path field is gone. Everything downstream (the conductor,
`--ref-image`, generate) is unchanged because it already consumes `reference_image` as a path on disk.
"Done" = a designer runs a single-sign brief in the browser, picking the reference file from disk, and
the sign generates from it, with no typed path anywhere and the standalone CLI unaffected.

## LOCKED decisions (settled by the 006 precedent; do NOT relitigate)

| Decision | Locked value | Rationale |
|---|---|---|
| Input modality | real file UPLOAD of the reference image (file picker), replacing the typed-path text field | consistency with the 006 onboarding upload; designer-facing; removes the absolute-path footgun |
| Reuse | the EXISTING `frontend/multipart.py` parser (006) + the save-upload-to-disk pattern | proven 3/3; no new parser, no new dependency |
| Where the upload lands | save the uploaded reference INTO the run dir (e.g. `run_*/reference.png`); put THAT path into the inputs JSON | co-located with the run's artifacts (auditable); the conductor reads it as a path, unchanged |
| Downstream contract | the conductor / CLI input contract is UNCHANGED: `reference_image` is still a path on disk in the inputs JSON; only the frontend's source of that path changes | the frontend adapts to the back-half, never the reverse (the standing rule) |
| Standalone CLI | the `conductor --thin --inputs <json>` path (with a `reference_image` path) keeps working untouched | the upload is a frontend convenience that produces a path; the agent-free core is unaffected |
| Cost | the change is on the FREE intake surface; the one paid sign is still the human eye-gate (fold into 004's pending T016, so the final UX is tested in one paid run) | cost discipline |

## The change, stage by stage (small; the 006 upload pattern applied to one field)
```
frontend/index.html : swap the reference text input for <input type="file">; the form posts multipart.
frontend/server.py  : POST /run accepts multipart (like the /onboard/* routes); parse via
                      multipart.parse_multipart; save the uploaded reference into the run dir; put that
                      saved path into the form state before inputs_writer.to_inputs(...).
shared helper       : factor a tiny "save_upload(file, dest_dir) -> path" used by BOTH the new 004 /run
                      and 006's logo-save (DRY); location is a /speckit-plan call.
inputs_writer / conductor / generate : UNCHANGED (reference_image is still a path).
```

## Verified codebase state (STEP ZERO - confirm before building)
- 004 today: `frontend/index.html` has `<input id="reference_image" placeholder="/abs/path/...">`; the
  form posts JSON; `frontend/server.py` `POST /run` reads `json.loads(self.rfile.read())` and requires
  a non-empty `reference_image` string. `inputs_writer.to_inputs` requires + passes `reference_image`
  verbatim into the inputs JSON; the conductor reads it as a path -> `scene_author --ref-image` ->
  `generate`.
- 006 already added `import multipart` to `server.py` and proved `parse_multipart` (binary bytes
  preserved). The `/onboard/save` route already does upload -> save-to-temp -> use-the-path; 004 mirrors
  that for the reference.
- No conflict with the 002 faithful-intake invariant: that rule forbids rephrasing TYPED BRAND CONTENT
  (messages, mandatory_elements). `reference_image` is a FILE LOCATION, not content, so a server-assigned
  saved path is fine (state this explicitly in the spec).

## Forks already resolved (do not reopen)
- Upload vs path: UPLOAD (locked). Remove the typed-path field entirely (do not keep a dual path/upload
  input - the dual UX is the inconsistency we are removing). A power-user path option is a later
  enhancement if ever needed.
- Reference still REQUIRED in v1 (unchanged from 004): no reference uploaded -> fail loud (400), same as
  today's required-string check.
- File-type/size validation: v1 accepts any uploaded file (a bad image fails loud at the paid
  generation step, the existing behavior); tightening to image types is a later enhancement, not v1.

## Out of scope (v1)
- The ref-less thin path (still deferred from 004; reference required in v1).
- Multi-file / batch reference upload, drag-and-drop polish, client-side image preview (nice-to-haves).
- Any change to generation, register, prompt assembly, or the conductor input contract.
- Tightened logo/reference file-type validation (later enhancement).

## Falsifiable tests (constitution §III - assert VALUES a wrong build cannot satisfy; NO paid calls)
- The new `save_upload(file_tuple, dest_dir)` helper writes the uploaded bytes to a real file under
  dest_dir and returns its path; binary bytes are preserved (reuse the multipart round-trip evidence).
- Given a multipart `/run`-style body with a reference file + the form fields, the assembled inputs
  JSON's `reference_image` points to a real saved file in the run dir (assert the file exists AND the
  path is in the JSON) - WITHOUT launching paid generation (test the parse + save + inputs assembly,
  not `runner.launch`).
- A `/run` (or the assembly step) with NO reference file fails loud (4xx / raises), no run launched.
- The 002 verbatim invariant for the OTHER fields still holds (messages / mandatory_elements unchanged
  through `inputs_writer`).
- Standalone: `conductor --thin --inputs <json>` with a `reference_image` path still runs end to end
  with the frontend absent (the input contract is unchanged) - regression guard.
- The served live-runner page uses a file input for the reference, not a typed-path text field
  (structural grep).

## Hard rules
- NO paid model calls in any automated test. Test the multipart parse + the save-upload helper + the
  inputs-assembly; never call `runner.launch` / generation in a test.
- REUSE `frontend/multipart.py`; do NOT add a parser or a dependency. Factor the save-upload helper so
  004 and 006 share ONE home (DRY).
- The conductor / CLI input contract is UNCHANGED (`reference_image` = a path); the frontend adapts.
- The standalone CLI stays runnable with the frontend absent.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII). NO em-dashes in user-facing text.

## Definition of done
- The live-runner takes the reference as a file UPLOAD; the typed-path field is gone; the run uses the
  uploaded file.
- The shared save-upload helper is used by both 004 (reference) and 006 (logo).
- Structural tests green (paste real output): save-upload, inputs-assembly-points-at-the-saved-file,
  fail-loud-on-missing, standalone-CLI-intact, the form-uses-a-file-input grep.
- The one paid sign (the human eye-gate) is folded into 004's pending T016, run AFTER the build.
- Report: files changed, the upload->save->path flow, the shared helper, test output.

## Open question for /speckit-plan (flag, do not solve in the spec)
Where the shared `save_upload` helper lives (e.g. a new `frontend/uploads.py`, or fold into the existing
`frontend/multipart.py`), and whether to refactor 006's `/onboard/save` logo-save onto it in the SAME
change (DRY now) or leave 006 as-is and only add 004's call site. Resolve at /speckit-plan against the
004 + 006 server shapes; do not assume.
```
