# Plan: 023-edit-mode (plan-as-spec, verified against the code 2026-07-20)

Lean plan in the 019/021 convention: the spec is the contract, this file pins the
technical decisions + verified seams so tasks.md can reference them.

## Route shape (US1)

The edit route is a FOURTH conductor route (thin/kit/legacy/edit) selected by
`inputs.mode == "edit"` (absent = design, THE pin). It never touches the register
engine, calibration, kit, or scene_author.

- **inputs contract** (new keys, all top-level): `mode: "edit"`, `base_image: <path>`,
  `edit_instruction: <verbatim str>`, optional `edit_region: {x,y,w,h}` (normalized
  0..1 floats, top-left origin), optional `product_images` (013 semantics unchanged).
  `signs` stays `[{"id":"s1","messages":[]}]` so the `sign_s1/` run-dir layout and
  every existing consumer (run_view, decide_confirm's `sign_s1/final_prompt.txt`
  check at server.py:155, export's refusal) work unchanged.
- **inputs_writer**: `to_edit_inputs(form_state)` (pure, fail-loud on missing
  base/instruction/bad region); `write_inputs` dispatches on `form_state["mode"]`.
  `to_inputs` NEVER emits a `mode` key (the byte-identity pin).
- **conductor**:
  - `validate_inputs` (conductor.py:665): `edit = inputs.get("mode") == "edit"`; the
    empty-messages refusal (line 681-682, exact string preserved) is skipped iff edit;
    edit adds: base_image exists on disk, edit_instruction non-empty, region shape
    valid (0<=x,y<1, 0<w,h<=1, x+w<=1, y+h<=1), context NOT required.
  - `write_glue_artifacts` (conductor.py:1332): first line returns early on edit mode
    (no subfields/intents; the register engine never sees edit runs).
  - `build_plan` (conductor.py:438): early branch returns a lean edit plan carrying
    every key `print_plan` (1313) and `execute` touch: brand, brand_paths, out,
    asset_type ("edit"), asset_profile_v1 ("edit"), asset_type_note, sign_count,
    has_reference (False), route "edit", mode "edit", steps=[one edit_author cmd].
  - `execute` (conductor.py:948): first line branches to `_execute_edit(...)`, which
    mirrors the thin route's 015 machinery exactly: generate-phase preflight
    (gate confirmed + final_prompt.txt exist, conductor.py:962-972), run_step on
    edit_author (`--prompt-only` on derive / `--verify-prompt` on generate, the one
    appended flag, same as conductor.py:1086-1089), derive writes `assumptions.json`
    = `[]` (no guesses: everything is verbatim or measured) + gate
    awaiting_confirmation; generate writes done, or resets to awaiting with the
    existing drift (returncode 3) / failure wording (conductor.py:1223-1234). Lean
    manifest with `"mode": "edit"`, the region, and the notes.
  - `main`: edit + `--phase full` refuses loudly (the pre-spend gate is mandatory for
    edits; the browser only ever sends derive/generate). `--thin` is accepted and
    ignored on the edit route (the runner always passes it).
- **harness/edit_author.py** (NEW, the one new module): CLI
  `--out <run_dir> --sign-id s1 [--style-notes ...] [--prompt-only|--verify-prompt]`,
  reads `<out>/inputs.json`.
  - `compose_edit_prompt(instruction, region, has_products, style_notes)` PURE:
    instruction VERBATIM under a CHANGE header; a PRESERVE preamble (everything not
    named stays identical: composition, every text character, colors, logo, layout);
    REGION section iff region (named as normalized rect, outside must stay
    pixel-identical); the 013-style PRODUCT FIDELITY clause iff products;
    style_notes as a binding operator note iff present (the nudge channel). No
    invented scene/message content, no register vocabulary.
  - `edit_size(base_path)`: PIL reads dimensions -> `format_size.resolve_size(f"{w}x{h}px")`
    -> `size_str` (the existing aspect-preserving map; the base image is the size
    authority).
  - `build_region_mask(base_path, region, out_path)`: RGBA PNG at base dimensions,
    transparent INSIDE the region (editable), opaque outside (preserved) — the
    images.edit mask convention.
  - `outside_region_stats(base_path, edited_path, region)`: edited resized to base
    dims, mean-absolute-diff over outside-region pixels, returns
    {mad, threshold, within, method}; threshold a named constant with provenance
    comment. Written to `sign_s1/edit_audit.json` on region runs (SC-003's auditable
    stat).
  - derive leg: write `final_prompt.txt` + a lean `run_manifest.json` (mode, region,
    prompt-only note). generate leg: `--verify-prompt` recompose-and-compare (exit 3
    on drift, scene_author's contract); refs = [base_image, *product_images];
    region -> build mask, call with mask; if the API refuses the mask, retry ONCE
    without it and record `mask_fallback` in the manifest + audit (FR-008's honest
    fallback, decided at runtime, no capability guessing).
- **generate.py**: `generate_variant` gains `mask_path=None` (additive; default =
  byte-identical call). When set, passes `mask=open(...)` to images.edit.

## Server + form (US1/US2)

- `parse_run_form` (server.py:94): keeps its 3-tuple arity; the second element is the
  PRINCIPAL upload — `reference` part in design mode (existing errors verbatim),
  `base` part when `form["mode"]=="edit"` (loud "a base image is required (edit
  mode)"). Products parse identically in both modes.
- `write_run_inputs` (server.py:119): dispatch on mode — save principal as
  `base.<ext>` + set `form["base_image"]`, vs today's `reference.<ext>` path.
  Products shared. `inputs_writer.write_inputs` dispatches downstream.
- `POST /run` (server.py:534-572): unchanged (brand check, single-flight, run_meta,
  derive launch). Edit runs stay brand-scoped (ownership/meta unchanged) even though
  the key barely matters; decide_confirm/answer/export routes work as-is
  (assumptions=[] renders zero gate rows; export on an edit run hits the existing
  "no elements" refusal).
- **index.html**: a job-mode control (新设计 default / 改图), edit-only fieldset
  (base upload + instruction textarea + region canvas), design-only fields hidden in
  edit mode (reference, W/H/unit, messages, elements, usage/vibe/occasion,
  render_style); `startRun` branches: edit validates base+instruction (loud Chinese)
  and posts `base` + form {mode, brand, edit_instruction, edit_region}; design gains
  the EMPTY-MESSAGES guard (loud Chinese, names the field, hints 改图), placed like
  the 022 size guard (before `fd.append("form"`). Region UI: the picked base image
  previews into a canvas; one drag = one rect; 清除选区 resets; normalized coords into
  formState. Untouched form = design mode = byte-identical POST (THE pin).

## Brand palette (US3)

- `brand_manager.update_brand` (brand_manager.py:132-141): color items carry
  name_cn/name_en from the payload (already read, currently dropped by the UI) and
  `rgb` is COMPUTED from the hex (int triplet) instead of hardcoded None (today every
  page save nukes extracted rgb + names — the wipe wart, both halves).
- `manage.html`: per-color name inputs (CN/EN) + a per-row 删除 button + an 添加颜色
  button per brand card; the save payload sends {hex, role, name_cn, name_en}.
  Validation stays server-side (exactly-one-primary; refusals leave the file
  byte-identical — already the 019 contract).

## Tests (all FREE)

- NEW `test_edit_mode.py`: writer/validate by value (incl. the no-mode-key pin and
  the preserved empty-messages error string), compose_edit_prompt by value
  (verbatim, preserve, region iff set, no scene content), mask + outside-region
  stats on synthetic PIL images by value, `generate_variant` mask-param default pin,
  dry-run plan shape (route edit, no register/calibrate steps), a REAL FREE
  `--phase derive` on a tmp edit fixture (zero model calls by construction: assert
  final_prompt verbatim + gate awaiting + assumptions []), generate-phase preflight
  refusal, parse_run_form/write_run_inputs edit dispatch, form grep pins (mode
  control default, edit controls, both Chinese refusals, the empty-messages guard).
- `test_brand_manager`: names+rgb round-trip by value; add/remove/name-input greps.
- Sweep: every pinned form-grep that names a moved surface moves dated-in-place.

## Human gates (spend)

- Mask probe: ONE real region-edit call (operator-run) — does images.edit accept our
  mask for this model? Either way the code path is already honest (runtime fallback).
- SC-002 eye-gate: the 蒙自源 bowl swap through the browser (base poster + product
  shot + swap instruction), operator-judged: swap done AND rest intact.
- SC-005 flow gate: 蒙自源 palette grown through the page, names survive a role edit.
