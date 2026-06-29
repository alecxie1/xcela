# Contract: the transient onboarding draft (`frontend/onboard.py`)

The wizard orchestration over a transient draft dir, callable WITHOUT HTTP (bytes/paths in, dicts out)
so it is unit-testable over the synthetic fixture. Reuses the 005 pure modules + `brand_intake/persist`.

## `start_draft(pdf_bytes) -> {draft_id, suggestions}`
- Create a draft dir under a scratch path; write `pdf_bytes` to `<draft>/source.pdf`.
- `suggestions = page_finder.suggest_pages(<draft>/source.pdf)` (1-indexed).
- Returns the opaque `draft_id` + suggestions. (No committed artifact written.)

## `extract_draft(draft_id, confirmed_pages) -> {locks, names} | {block}`
- Run `extract_brand_colors(pdf, confirmed_pages.color)` + `read_brand_names(pdf, confirmed_pages.name)`.
- If ZERO colors -> return `{block: "no colors found on these pages"}` (the UI returns to page-confirm).
  Never fabricate a color, never open an empty verify gate (FR-004).
- Else return the color locks (hex + provenance + needs_review, role unset) + the name candidates.

## `save_draft(draft_id, verified, logo_bytes) -> {brand, key_path}` (raises / error on fail)
- `verified` carries: brand id, brand_cn, brand_en, per-color {role, name_cn, name_en, _ack}.
- Block if `unacknowledged_flags(verified.colors)` is non-empty (acknowledgment gate).
- Block (named error, NO write) if `persist.key_exists(brand)` (id collision).
- `build_lean_key(... finalize_items(verified.colors) ...)`; `validate_lean_key(key)` (FAILS LOUD on no
  primary / missing-or-unreal logo).
- `persist.place_logo(brand, logo_bytes-or-temp)` + `persist.write_key(brand, key)`.
- Discard the draft dir. Return the brand + written key path.

## Lifecycle / rules (falsifiable)
1. The draft is TRANSIENT: only `save_draft` writes to `answer_keys/` + `brands/`; abandon leaves no
   committed artifact (the draft dir is scratch, cleaned up).
2. `extract_draft` blocks on zero colors (no fabricated color).
3. `save_draft` FAILS LOUD (no write) on: unacknowledged flag, no primary, missing/unreal logo, or an
   existing brand id.
4. After a successful `save_draft`, the draft dir no longer exists and the key passes `validate_lean_key`.
5. `onboard.py` calls the 005 pure modules + `persist`; it never calls a model or `intake.main()`.
