# SPEC BRIEF for /speckit-specify - Feature 008: role-aware brand palette + exactly-one-primary

DECISION MAP. All forks below are SETTLED in conversation (2026-06-30) and grounded in the ACTUAL code.
This is the substrate so the spec fills a known shape.

---

## Problem / why
The whole brand palette is already extracted at onboarding and already reaches the generation prompt,
BUT only ONE color does any work. On the thin route the live-runner uses (`scene_author.assemble_thin_prompt`,
`scene_author.py:884-891`) every color is listed as `name: #hex [role]`, with the role as a BARE LABEL
and no instruction telling the model what to do with it. Only `primary` is reinforced anywhere
(`_primary_color_hex` at `scene_author.py:332`, used by `_register_directive` + the playful-accents
template). So `secondary` / `accent` / `background` / `text` are decorative labels with zero operative
effect. The designer's intent ("this is my accent, this is my text color") is silently dropped. Second,
onboarding does not enforce a single primary: `validate_lean_key` requires only `>=1` primary
(`validate_key.py:24`), so a designer can mark 3 colors primary and the prompt silently anchors on the
FIRST, the rest meaningless. Both are silent-judgment / honest-null violations the user hit while testing.

## Goal (scopes "done")
(1) Every extracted color reaches the thin prompt with a ROLE-SPECIFIC instruction, so each role drives
real design behavior (available palette with role GUIDANCE, not a rigid must-use). (2) Onboarding
enforces EXACTLY ONE primary, fail-loud, with a clear in-UI instruction; a co-equal second color is
assigned `secondary`. "Done" = a brand with 4-5 roled colors produces a thin prompt where each color
carries its instruction, and onboarding blocks a save with zero OR more-than-one primary.

## LOCKED decisions (settled in conversation; do NOT relitigate)

| Decision | Locked value | Rationale |
|---|---|---|
| Strictness | available palette with role GUIDANCE ("use it for...", not "must use exactly this for X") | the model still composes; brand identity is the hard lock, role usage is soft (constitution VI) |
| Palette identity | stays a HARD lock (the design must read as this brand's colors) | brand governs color HARD (VI); only the per-role USAGE is guidance |
| Primary count | EXACTLY ONE primary, enforced fail-loud at onboarding save; a second co-equal color is `secondary` | kills the silent first-primary pick; one unambiguous anchor |
| Where roles take effect | the THIN prompt (`assemble_thin_prompt`), the route the live-runner runs | that is the live path; reference is required in v1 so this is what generates |
| Unroled / blank role | still reaches the prompt as palette ("part of the brand palette") | honest-null: never silently drop a color the designer left unroled (V) |
| `background` vs chroma | the background instruction is emitted ONLY when NOT a chroma/no-reference job | a brand background must not fight the #00B140 chroma key; today's live path is reference-only (chroma off) so it is safe now, guard keeps it correct for the deferred ref-less path |
| Scope of generation change | the thin route ONLY; no kit/tier-3/legacy change, no new asset profile | the live-runner is reference-only thin; broader generalization (photographic posters) is a SEPARATE later feature |

## EXACT prompt wording (CONFIRMED verbatim - do NOT paraphrase)
Header line (replaces `BRAND LOCK COLORS (the design must still read as this brand's):`):
```
BRAND LOCK COLORS (these are the brand's colors and the design must read as
this brand's; each color's role tells you how to use it, as guidance not a rigid rule):
```
Per-color line format: `name_cn/name_en: #hex [role] - <instruction>`
Per-role instruction text:
- primary: `the dominant brand color: use it for the largest, most prominent areas as the main anchor of the design.`
- secondary: `a supporting brand color: use it for secondary areas and blocks that support the primary without competing.`
- accent: `an accent color: use sparingly for highlights, emphasis, and small attention-drawing details (calls to action).`
- background: `the backdrop color: use it to fill the background field behind the content.`
- text: `the text color: use it for legible headline and body text where a brand text color is wanted.`
- blank / unrecognized: `part of the brand palette: use where appropriate to keep the design on-brand.`

Rendered example:
```
BRAND LOCK COLORS (these are the brand's colors and the design must read as
this brand's; each color's role tells you how to use it, as guidance not a rigid rule):
  红色/Red: #D81E05 [primary] - the dominant brand color: use it for the largest, most prominent areas as the main anchor of the design.
  灰色/Grey: #888888 [secondary] - a supporting brand color: use it for secondary areas and blocks that support the primary without competing.
  金色/Gold: #C8A24B [accent] - an accent color: use sparingly for highlights, emphasis, and small attention-drawing details (calls to action).
  白色/White: #FFFFFF [background] - the backdrop color: use it to fill the background field behind the content.
  黑色/Black: #1A1A1A [text] - the text color: use it for legible headline and body text where a brand text color is wanted.
```

## Verified codebase state (STEP ZERO - confirm before building)
- `scene_author.py:884-891`: the thin prompt already lists all colors as `name_cn/name_en: #hex [role]`;
  this is the block to extend with the per-role instruction. The header at :888 is the line to replace.
- `scene_author.py:332`: `_primary_color_hex` returns the FIRST color with role == primary; used by
  `_register_directive` (:372) + the playful-accents template (:393, :745). Keep as the anchor; with
  exactly-one-primary there is no ambiguity.
- `validate_key.py:24`: `has_primary = any(role==primary ...)` -> only >=1 enforced. CHANGE to exactly-one.
- `assemble_key.py` / `onboard.py finalize_items`: roles are human-assigned in the verify gate; the lean
  key carries `fields.colors.items[].role`. The onboarding UI must say "exactly one primary".
- The live-runner is reference-required (v1, 007); chroma is OFF on the reference job, so `background`
  is safe on the current path. No-reference/chroma is the deferred ref-less path (guard for later).

## Forks already resolved (do not reopen)
- Strictness: GUIDANCE not must-use (locked). Verbs stay "use it for / use sparingly".
- primary firmness: keep "use it for the largest, most prominent areas as the main anchor" (not changed to "must dominate").
- accent restraint: KEEP "use sparingly".
- header: KEEP "must read as this brand's" (hard palette lock).
- Exactly-one-primary lives in the shared `validate_lean_key` (so CLI + web enforce identically), with the
  onboarding UI instruction; this is a /speckit-plan placement detail, flagged below.

## Out of scope (v1)
- Generalizing beyond flat-vector die-cut event signs (photographic posters / arbitrary materials) - a
  SEPARATE later feature; this one only makes the EXISTING palette functional on the thin route.
- The kit / tier-3 / legacy render-and-scrub color paths - thin route only.
- Re-validating or rewriting EXISTING committed answer_keys with multiple primaries - the rule applies at
  onboarding save for new brands; the generation side keeps the first-primary anchor as the fallback.
- Merging onboard + live-runner UI, required-field clarity for the message line, the scroller layout -
  separate UI items from the same testing-notes batch.
- typography.styles / font roles - untouched (still honest-null).

## Falsifiable tests (constitution III - assert VALUES a wrong build cannot satisfy; NO paid calls)
- Given a brand key with primary+secondary+accent(+background+text), `assemble_thin_prompt` output
  contains EACH color's hex AND its role-specific instruction substring (e.g. the accent line contains
  "use sparingly"; the secondary line contains "support the primary"; the text line contains "legible").
  A wrong build that only anchors the primary FAILS (the secondary/accent instructions are absent).
- A color with a blank/unknown role still appears with the "part of the brand palette" fallback line
  (never dropped).
- The `background` instruction is PRESENT on a reference job (chroma off) and ABSENT on a
  no-reference/chroma job (the guard) - assert both directions.
- The primary anchor is unchanged: `_primary_color_hex` still returns the single primary; the register
  directive still anchors on it (regression).
- `validate_lean_key` RAISES on zero primaries AND on >=2 primaries; PASSES on exactly one (a build that
  allows multiple primaries fails). `onboard.save_draft` blocks a multi-primary save (no file written).
- The served onboarding page states "exactly one primary" (structural grep).

## Hard rules
- NO paid model calls in any automated test (assert the assembled prompt STRING + the validator, never generate).
- GENERALIZES, not hand-tuned: the role->instruction map is brand-general; no brand/color literals (IV).
- Brand identity stays the HARD lock; only per-role usage is guidance (VI).
- Honest-null: an unroled color still reaches the prompt; never silently dropped (V).
- The EXACT confirmed wording above is verbatim; do not paraphrase the role instructions.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (VII). NO em-dashes in user-facing text.

## Open question for /speckit-plan (flag, do not solve in the spec)
The home of the role->instruction map (a small dict in `scene_author.py` next to `assemble_thin_prompt`,
vs a shared constant), and whether exactly-one-primary lives in `validate_lean_key` (shared CLI+web) or
additionally as an onboarding-gate pre-check. Resolve at /speckit-plan against the scene_author +
validate_key + onboard shapes.
