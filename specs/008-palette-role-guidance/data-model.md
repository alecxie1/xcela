# Phase 1 Data Model: Role-aware Brand Palette + Exactly-one-primary

No database. The shapes are the role vocabulary, the role-to-instruction map, the prompt color block, and
the validator rule. The answer_key shape is UNCHANGED (this feature gives the existing `role` field an
effect and constrains primary count at save).

## Canonical role vocabulary

The 5 named roles plus a blank/unknown fallback. This single list is the source of truth, offered by the
onboarding gate (web + CLI) and keyed by the role-to-instruction map.

`primary`, `secondary`, `accent`, `background`, `text` (+ blank / unrecognized -> fallback).

## Role-to-instruction map (`ROLE_GUIDANCE`, in `scene_author.py`)

Confirmed verbatim instruction text per role (do NOT paraphrase):

| Role | Instruction text |
|------|------------------|
| `primary` | `the dominant brand color: use it for the largest, most prominent areas as the main anchor of the design.` |
| `secondary` | `a supporting brand color: use it for secondary areas and blocks that support the primary without competing.` |
| `accent` | `an accent color: use sparingly for highlights, emphasis, and small attention-drawing details (calls to action).` |
| `background` | `the backdrop color: use it to fill the background field behind the content.` |
| `text` | `the text color: use it for legible headline and body text where a brand text color is wanted.` |
| blank / unknown | `part of the brand palette: use where appropriate to keep the design on-brand.` |

## Thin-prompt color block (`assemble_thin_prompt`)

- Header line (replaces `BRAND LOCK COLORS (the design must still read as this brand's):`):
  ```
  BRAND LOCK COLORS (these are the brand's colors and the design must read as
  this brand's; each color's role tells you how to use it, as guidance not a rigid rule):
  ```
- Per-color line: `  name_cn/name_en: #hex [role] - <instruction>`, where `<instruction>` is
  `ROLE_GUIDANCE[role]`, falling back to the blank/unknown text for an unrecognized / empty role.
- **Background guard**: if the role is `background` AND `has_reference` is False (a no-reference / chroma
  job), the line uses the blank/unknown fallback instead of the backdrop instruction (the color is still
  listed). When `has_reference` is True (the v1 reference job), the backdrop instruction is used.
- Every color is listed exactly once; none is dropped (honest-null).

## Validator rule (`validate_lean_key`)

- Count the items with `role == "primary"` (case-insensitive) carrying a `printed_html` hex.
- `count == 0` -> raise `KeyValidationError` (named: no primary, the existing message).
- `count >= 2` -> raise `KeyValidationError` (named: more than one primary; assign one primary and make
  the others secondary).
- `count == 1` -> pass (plus the existing logo_path checks, unchanged).

## Onboarding gate role pickers

- `onboard.html`: the role `<select>` offers all 5 roles (adds `accent`, `text` to the current
  primary/secondary/background); a visible "exactly one primary" instruction near the colors step.
- `intake.py`: the CLI verify-gate role prompt lists all 5 roles; the batch default (first = primary, rest
  = secondary) is unchanged and yields exactly one primary.

## Validation rules (where each FR is enforced)

| Rule | Where | FR |
|------|-------|----|
| Each color listed with hex + role-specific instruction | `assemble_thin_prompt` via `ROLE_GUIDANCE` | FR-001 / FR-002 |
| Palette framed as a hard brand lock | the header line | FR-003 |
| Blank/unknown role still listed (fallback) | `ROLE_GUIDANCE` fallback in the loop | FR-004 |
| `background` instruction only when not chroma | the `has_reference` guard | FR-005 |
| Primary anchor unchanged | `_primary_color_hex` (untouched) | FR-006 |
| Exactly one primary at save (fail loud) | `validate_lean_key` (shared) | FR-007 |
| Gate states exactly-one-primary | `onboard.html` instruction text | FR-008 |
| Gate offers all 5 roles (web + CLI) | `onboard.html` + `intake.py` | FR-008a |
| Scope = thin prompt + validator + gate pickers | the touched files only | FR-009 |
