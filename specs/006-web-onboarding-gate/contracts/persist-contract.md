# Contract: shared persistence helpers (`brand_intake/persist.py`)

The single home for "place the logo + write the key + check the id", called by BOTH the 005 CLI
(`intake.py`, refactored) and the web gate (`onboard.py`), so they write byte-identical artifacts.

## `key_exists(brand) -> bool`
- True iff `answer_keys/<brand>.json` already exists. The id-collision guard (FR-014); both surfaces
  block a save that would overwrite a committed brand key.

## `place_logo(brand, src) -> dest`
- Copy the logo (`src` = a path or a saved temp file) under gitignored `brands/<brand>/`, return the
  destination path. The returned path is what goes into `logo_path`. NEVER the taichi default.

## `write_key(brand, key) -> path`
- Write `key` (a built + validated lean key) to `answer_keys/<brand>.json`, return the path. Callers
  validate (`validate_lean_key`) BEFORE calling this; `write_key` does not silently accept a degraded key.

## Rules (falsifiable)
1. `intake.py` (the standalone CLI) is refactored to call these and still runs the full flow
   end-to-end with the web gate absent (SC-006).
2. The CLI and the web gate produce the SAME `answer_keys/<brand>.json` shape + the same logo placement
   (one home, no drift).
3. `key_exists` returns True for an existing brand (e.g. `aia`) and False for a fresh id; a save guarded
   by it never overwrites a committed key.
4. `place_logo` writes under `brands/<brand>/` (gitignored); only the JSON under `answer_keys/` is tracked.
