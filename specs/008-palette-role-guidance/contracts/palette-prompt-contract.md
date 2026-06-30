# Contract: role-aware palette in the thin prompt (`assemble_thin_prompt` + `ROLE_GUIDANCE`)

Makes every brand color drive real design behavior on the thin route. Generation-side; stdlib string
assembly. The palette identity stays a HARD lock; per-role usage is guidance (constitution §VI).

## `ROLE_GUIDANCE` (module constant in `scene_author.py`)

A dict: role -> confirmed instruction text (verbatim, see data-model.md). A blank/unknown role uses the
fallback text. Brand-general (no brand/color literals). Its named keys are the canonical role vocabulary
the onboarding gate must offer (sync test in roles-gate-contract.md).

## `assemble_thin_prompt` color block (the change)

Input: the brand key's `fields.colors.items[]` (each `{name_cn, name_en, printed_html, role}`), plus the
existing `has_reference` flag.

Behavior:
- Emit the new header line (verbatim, data-model.md): keeps "the design must read as this brand's" (hard
  lock) and frames role as guidance.
- For each color, emit `  name_cn/name_en: #hex [role] - <instruction>` where `<instruction>` is
  `ROLE_GUIDANCE[role]`, or the blank/unknown fallback for an empty/unrecognized role.
- Background guard: if `role == background` and NOT `has_reference`, use the fallback text (the color is
  still listed) so it does not contradict the chroma key. If `has_reference`, use the backdrop instruction.
- Every color appears exactly once; none dropped.

Unchanged: `_primary_color_hex` and `_register_directive` (the primary anchor / magnitude), the headline /
mandatory / forbidden / logo / reference / negatives blocks.

## Falsifiable tests (`test_palette_roles.py`, no paid calls)

- A key with primary + secondary + accent (+ background + text): the assembled prompt contains EACH
  color's hex AND its role-instruction substring (accent line contains "use sparingly"; secondary contains
  "support the primary"; text contains "legible"). A primary-only build fails (other substrings absent).
- A color with role "" or "weird": its line is present with the "part of the brand palette" fallback.
- Background guard BOTH directions: with `has_reference=True` the background line contains "fill the
  background"; with `has_reference=False` it does NOT (uses the fallback), and the color is still listed.
- The single-primary anchor is unchanged: `_primary_color_hex` returns the one primary and the register
  directive still references it (regression).
- The header still asserts the hard brand-color lock (contains "must read as this brand's").
