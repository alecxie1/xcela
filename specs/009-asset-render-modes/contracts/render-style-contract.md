# Contract: the render_style carrier + mapping + thin argv

The designer's explicit render choice, carried as a user-term field and translated to the engine profile at
the conductor boundary. The frontend speaks `render_style`; the engine speaks `asset_profile`.

## `render_style` in the brief (inputs JSON)

- A top-level field `render_style` (user terms: `"flat vector"` | `"photographic"`), default `"flat
  vector"`. `inputs_writer.to_inputs` carries it VERBATIM (pure pass-through; no mapping in the frontend).
- The other fields are unchanged (the 002 verbatim invariant holds).

## `conductor.normalize_render_style(value) -> str`

- Returns the engine `asset_profile`: `"photographic" -> "photo"`; anything else (including `"flat
  vector"`, blank, omitted, unrecognized) `-> "flat_graphic"`. Case / whitespace-insensitive.
- Honest-null: an unrecognized value resolves to `flat_graphic` (the safe default), never an error or a
  silent guess of a different mode; the raw `render_style` and the resolved `asset_profile` are recorded in
  the manifest.

## Threading into generation

- `_scene_author_thin_argv(..., asset_profile=ASSET_PROFILE)` gains an `asset_profile` param (default the
  `ASSET_PROFILE` constant for back-compat). `build_plan` reads `inputs.get("render_style")`, maps via
  `normalize_render_style`, and passes the result, so the thin argv carries `--asset-profile photo` or
  `--asset-profile flat_graphic` instead of the hard-wired constant.
- `run_thin_mode` already forwards `args.asset_profile` to `assemble_thin_prompt` (unchanged).
- The kit / legacy / no-reference argv builders (`conductor.py:188/:219`) keep `ASSET_PROFILE` (out of
  scope).

## Falsifiable tests (no paid calls)

- `normalize_render_style("photographic") == "photo"`; `normalize_render_style("flat vector") == "flat_graphic"`;
  `normalize_render_style("") == normalize_render_style("zzz") == "flat_graphic"` (fallback).
- `build_plan` for a brief with `render_style="photographic"` -> the scene_author thin argv contains
  `--asset-profile photo` (NOT the flat default). A brief with no render_style -> `--asset-profile
  flat_graphic`.
- `inputs_writer.to_inputs({... render_style: "photographic" ...})["render_style"] == "photographic"`
  (carried verbatim); a brief without it defaults to flat vector.
- The served `index.html` has a render-style control (structural grep).
