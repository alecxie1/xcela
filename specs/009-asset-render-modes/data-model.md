# Phase 1 Data Model: Beyond Flat-vector Event Signs (Render Modes)

No database. The shapes are the `render_style` carrier, its mapping to the engine `asset_profile`, the
(asset_profile x register) opener matrix, and the negatives split. The conductor input contract changes only
by adding the `render_style` field.

## render_style (the brief carrier)

- A new top-level brief field `render_style`, user terms: `"flat vector"` | `"photographic"`. Default
  `"flat vector"`. Carried VERBATIM by `inputs_writer.to_inputs` into the inputs JSON.
- Omitted / blank / unrecognized -> treated as flat vector downstream (honest-null).

## render_style -> asset_profile (conductor `normalize_render_style`)

| render_style (input, case/space-insensitive) | asset_profile (engine) |
|----------------------------------------------|------------------------|
| `photographic` | `photo` |
| `flat vector` / `flat_vector` / blank / omitted / anything else | `flat_graphic` |

Mapped once in the conductor; threaded into `_scene_author_thin_argv` (new `asset_profile` param, default
`ASSET_PROFILE`); the run manifest records BOTH `render_style` (raw) and the resolved `asset_profile`.

## Opener matrix (`assemble_thin_prompt`, by asset_profile x register)

`is_graphic = asset_profile == "flat_graphic"`; `is_event_prop = register_profile.inferred_register ==
"event_prop"`. Verbatim text in research.md (Decision 2). `{cn}/{en}` = brand names.

| asset_profile | register | opener |
|---------------|----------|--------|
| flat_graphic | event_prop | the existing die-cut hand-held prop opener, BYTE-UNCHANGED (regression) |
| flat_graphic | marketing / formal | REWRITTEN: rectangular marketing poster (no "hand-held event sign") |
| photo | event_prop | NEW: photographic hand-held event prop |
| photo | marketing / formal | NEW: photographic marketing poster |

## Negatives split (`assemble_thin_prompt`)

- Render-agnostic text guards (BOTH modes): `no gibberish or garbled text, no extra Chinese text beyond the
  headline above, no tagline, no watermark`.
- Flat-only render clause (is_graphic only): `no photographic shading, no 3D realism`.
- flat line = render clause + text guards = BYTE-IDENTICAL to today; photo line = text guards only.

## Deliverable / chroma (unchanged)

Thin route, reference job: deliverable `final.png`, chroma OFF. `chroma_contain_active` already returns
False for any non-`flat_graphic` profile, so a photo job is chroma-free automatically. No measure/composite
on the thin route.

## Validation rules (where each FR is enforced)

| Rule | Where | FR |
|------|-------|----|
| Explicit render-style control, carried as `render_style`, default flat vector | index.html + inputs_writer | FR-001 |
| Chosen style drives the dialect; no leak across modes | assemble_thin_prompt opener + negatives | FR-002 |
| photo mode: photographic language, no flat render negatives, text guards kept | the photo openers + negatives split | FR-003 |
| flat opener register-aware (marketing != "hand-held event sign"; event_prop unchanged) | the opener matrix | FR-004 |
| shape derived from register | register drives the opener branch | FR-005 |
| profile carried to generation; manifest records it; not hard-wired | conductor normalize_render_style + thin argv + manifest | FR-006 |
| omitted render_style -> flat vector, event-sign output unchanged | normalize fallback + byte-identical branch | FR-007 |
| unrecognized -> flat vector, recorded | normalize_render_style fallback + manifest | FR-008 |
| thin route only; kit/legacy/no-ref/measure-composite unchanged | only the thin argv + assemble_thin_prompt change | FR-009 |
