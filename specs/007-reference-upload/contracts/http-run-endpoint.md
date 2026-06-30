# Contract: `POST /run` (multipart) - the live-runner run submission

Changes the 004 `/run` body from JSON to `multipart/form-data` so the reference image is a real upload.
Mirrors the 006 `/onboard/save` shape (a JSON field + a file part). Everything else about `/run`
(single-flight, the run-dir naming, the async launch, the response) is unchanged.

## Request

`POST /run`, `Content-Type: multipart/form-data`:

| Part | Kind | Content |
|------|------|---------|
| `form` | text field | `JSON.stringify(formState)`: brand, asset_type, format_size, reference_relationship, vibe, logo_treatment, brand_strictness, occasion, usage_context, audience, mandatory_elements, forbidden_elements, messages, ... (every brief field EXCEPT the reference). |
| `reference` | file part | the uploaded reference image. |
| `style_notes` | text field | optional; the nudge note on a re-run. |

The client builds this with `FormData`: `fd.append("form", JSON.stringify(formState))`,
`fd.append("reference", fileInput.files[0], fileInput.files[0].name)`, optional
`fd.append("style_notes", note)`. The client-side guard checks a file is PICKED (not a non-empty
string).

## Server flow

1. Parse: `multipart.parse_multipart(self._read_body(), Content-Type)` -> `{fields, files}`.
2. Read the brief: `form = json.loads(fields["form"] or "{}")`. Invalid JSON -> 400.
3. **Fail loud on missing reference**: if `files.get("reference")` is absent or has empty bytes ->
   `400 {"error": "a reference image is required (v1)"}`. NO run launched (return before mkdir /
   single-flight). (FR-005 / US2)
4. Validate brand: `brand in _brands()` else 400 (unchanged).
5. Acquire single-flight (`_inflight`); 409 if busy (unchanged).
6. `run_dir = output/run_<brand>_<ts>`; `mkdir`.
7. **Save the reference**: `ref_path = uploads.save_upload(files["reference"], run_dir,
   name="reference"+ext)`. Inject: `form["reference_image"] = ref_path`.
8. `inputs_path = inputs_writer.write_inputs(form, run_dir/"inputs.json")` (UNCHANGED; reads
   `reference_image` as a path).
9. `_launch_async(run_dir, brand, inputs_path, form.get("style_notes"))` (UNCHANGED).

## Response

Unchanged: `200 {"run_id": ..., "per_run_cost_usd": ...}`; errors as `4xx {"error": ...}`.

## Invariants preserved

- The conductor / CLI input contract is UNCHANGED: `inputs.json` `reference_image` is still a path on
  disk; only its SOURCE changed (server-saved upload, not designer-typed). (FR-006)
- The 002 verbatim invariant holds: messages / mandatory_elements ride in the `form` JSON field and reach
  `to_inputs` unchanged. (FR-008)
- The standalone `conductor --thin --inputs <json>` path (with a `reference_image` path) runs end to end
  with the frontend absent - this route is a frontend convenience that produces a path. (FR-009)

## Falsifiable tests (no paid calls; never `runner.launch` / generation)

- A synthetic multipart `/run`-style body (a `reference` file + a `form` JSON field) -> after parse +
  save + inject + assemble, the inputs JSON's `reference_image` points at a file that EXISTS in the run
  dir AND the path is in the JSON.
- A body with NO `reference` file -> the assembly path fails loud (raises / 4xx) and no run dir launch.
- The served `index.html` uses `<input type="file">` for the reference, not a typed-path text input
  (structural grep).
