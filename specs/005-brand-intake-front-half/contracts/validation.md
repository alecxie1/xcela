# Contract: validation + the acknowledgment gate

Two distinct guards before a key is saved: the FAIL-LOUD validation (completeness the conductor never
checks) and the ACKNOWLEDGMENT gate (every `needs_review` flag explicitly acted on).

## `validate_key.validate_lean_key(key) -> None` (raises on failure)

FAILS LOUD with a NAMED reason on:
1. No color with `role == "primary"`.
2. Missing `logo_path`, or a `logo_path` that does not point to an existing file.

It MUST raise (nonzero / exception), never return a degraded-but-OK key. This contains the two
landmines: `scene_author` silently defaults a missing `logo_path` to the taichi logo, and the
conductor only checks the key `.exists()`, never completeness (a blank hex becomes "primary brand
color  stays").

## Acknowledgment gate (in `intake.py`, FR-008, clarified)

Per lock carrying `needs_review`, the human picks exactly one:
- `confirm` (looked, the value is correct) -> flag cleared.
- `edit` (looked, fixed the value) -> flag cleared, value updated.
- `keep-flagged` (looked, cannot verify) -> `needs_review: true` is WRITTEN into the saved key (honest record).

Save proceeds only when: (EVERY `needs_review` flag is acknowledged) AND (`validate_lean_key` passes).
The check is "every flag acknowledged," NOT "every flag cleared" (honest-null persists by explicit
keep-flagged). Color flags MUST be acknowledged (a wrong hex poisons every downstream sign).

## Rules (falsifiable)

1. `validate_lean_key` on a key with no primary color raises with a named reason.
2. `validate_lean_key` on a key with a missing / non-existent `logo_path` raises with a named reason.
3. A degraded key NEVER reaches `assemble_thin_prompt` (validation raised first).
4. Save is blocked while any `needs_review` flag is UNACKNOWLEDGED; a kept-flagged flag is written
   into the key.
