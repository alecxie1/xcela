# Contract: exactly-one-primary + the 5-role gate (`validate_lean_key` + onboarding pickers)

Enforces a single unambiguous primary at save and makes the full role vocabulary assignable. The
validator is the ONE shared home (CLI + web); the gate surfaces offer all 5 roles, kept in sync by a test.

## `validate_lean_key` (the change, `brand_intake/validate_key.py`)

- Count `fields.colors.items[]` with `role == "primary"` (case-insensitive) AND a `printed_html` hex.
- `0` -> raise `KeyValidationError` (no primary; the existing named message, unchanged).
- `>= 2` -> raise `KeyValidationError` (more than one primary: assign exactly one primary and make the
  others secondary).
- `1` -> pass; then the existing logo_path checks (unchanged).

Callers inherit it unchanged: `onboard.save_draft` (`onboard.py:116`) and `intake.py` (`:141`) both
fail loud at save with NO file written. Existing committed keys are not re-validated at generation.

## Onboarding gate role pickers (the change)

- `frontend/onboard.html`: the role `<select>` offers all 5 roles (add `accent`, `text` to
  primary/secondary/background); add a visible "exactly one primary" instruction near the colors step. No
  em-dashes.
- `brand_intake/intake.py`: the CLI verify-gate role prompt lists all 5 roles; the batch default
  (first=primary, rest=secondary) is unchanged (still one primary).

## Falsifiable tests (no paid calls)

- `validate_lean_key`: raises on 0 primaries (existing); raises on 2 primaries (new) with a named reason;
  passes on exactly 1 (existing single-primary fixture). (`test_brand_key.py`)
- `onboard.save_draft`: a multi-primary verified set fails loud, NO key file written. (`test_onboard.py`)
- Gate-role SYNC: the roles offered by `onboard.html` (the `<select>` options) AND by the `intake.py`
  prompt equal the named roles in `scene_author.ROLE_GUIDANCE` (a wrong build that adds a role to the map
  but not the gate, or vice versa, fails). (`test_palette_roles.py`)
- The served onboarding page contains the "exactly one primary" instruction (structural grep). No em-dash.
