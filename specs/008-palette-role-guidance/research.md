# Phase 0 Research: Role-aware Brand Palette + Exactly-one-primary

The spec's design forks were settled in the 2026-06-30 session (recorded in Clarifications). The two HOW
items the brief flagged plus the gate-extension are resolved here, grounded in code read 2026-06-30. No
NEEDS CLARIFICATION remains.

## Decision 1: Home of the role-to-instruction map

**Decision**: A module-level constant `ROLE_GUIDANCE` in `harness/scene_author.py`, beside
`assemble_thin_prompt`. Keys are the canonical roles; the value is the confirmed instruction text. A
blank/unknown role falls back to a generic palette line. The onboarding gate's role options live in
`onboard.html` (HTML `<select>`) and `intake.py` (CLI prompt); a STRUCTURAL TEST asserts the gate's
offered roles equal the named `ROLE_GUIDANCE` roles (the sync guard).

**Rationale**:
- The instruction text IS generation prompt content, consumed only by `assemble_thin_prompt`. Co-locating
  the map with its single consumer keeps it cohesive and testable on the assembled string.
- A single dict makes the wording auditable in one place and trivially testable (assert each role's
  substring appears). No brand/color literals -> brand-general (§IV).
- The gate is HTML + a CLI string, which cannot import a Python constant cleanly into the served page.
  Rather than over-engineer a shared source across languages, keep the literals where they live and bind
  them with a falsifiable SYNC TEST (the gate offers exactly the named roles). That fails loudly if they
  drift, which is the real risk the clarification raised.

**Alternatives considered**:
- *A shared roles module imported by scene_author + intake + injected into onboard.html*: rejected. The
  HTML is static; templating a Python constant into it adds machinery for a 5-item list. The sync test is
  lighter and equally safe.
- *Inline the instructions in the color loop*: rejected. Harder to audit/verify the exact wording; a dict
  is the clean home.

## Decision 2: Where exactly-one-primary lives

**Decision**: Tighten the shared `validate_lean_key` (`brand_intake/validate_key.py`) from "at least one
primary" to "EXACTLY one primary": raise `KeyValidationError` with a named reason on zero primaries AND on
two-or-more primaries; pass on exactly one. No separate onboarding pre-check.

**Rationale**:
- `validate_lean_key` is the ONE shared validator already called by BOTH the web gate
  (`onboard.save_draft`, `onboard.py:116`) and the CLI (`intake.py:141`). Putting the rule there makes
  both enforce identically (DRY, the 006 persist spirit) and fail loud at save with no file written.
- The existing test fixtures use 0 or 1 primary (`test_brand_key` check3 uses role=secondary -> 0
  primaries; `test_onboard._verified` uses one primary), so tightening to ==1 does not break them; only a
  NEW multi-primary case is added.
- Existing committed answer_keys are NOT re-validated at generation (the conductor only checks the key
  exists), so historical keys with multiple primaries are unaffected (spec edge case); the generation
  side keeps `_primary_color_hex` (first primary) as the fallback.

**Alternatives considered**:
- *A pre-check only in the onboarding gate*: rejected. Would leave the CLI able to save multiple
  primaries, splitting the rule across two homes (the opposite of DRY).
- *Enforce in `build_lean_key`*: rejected. `build_lean_key` is a pure assembler that does not judge; the
  validator is the fail-loud gate by design (`validate_key.py` docstring).

## Decision 3: The `background`-vs-chroma guard

**Decision**: In `assemble_thin_prompt`, emit the `background` role's instruction ONLY when
`has_reference` is True (the v1 reference job, chroma OFF). On a no-reference / chroma job, a
`background`-roled color is still LISTED but falls back to the generic palette line (no "fill the
background" instruction), so it cannot contradict the #00B140 chroma key.

**Rationale**:
- `assemble_thin_prompt` already takes `has_reference` (`scene_author.py:831`). Per CLAUDE.md's two-job
  table, a reference job is chroma OFF and a no-reference job is chroma ON, so `has_reference` is the exact
  signal.
- The live-runner is reference-required (007), so `has_reference` is always True there today -> the
  background instruction always shows on the live path. The guard only matters for the deferred ref-less
  thin path, keeping the mapping correct for the future without affecting today (no visible change now).
- Honest-null: the color is never dropped, just de-instructed in the one context where its instruction
  would be a contradiction (§V).

**Alternatives considered**:
- *Always emit the background instruction*: rejected. On a future chroma job it would tell the model to
  paint a backdrop that then gets keyed out, a built-in contradiction.
- *Drop the background color entirely on a chroma job*: rejected. That silently discards a brand color
  (violates honest-null); de-instructing to the generic palette line keeps it present.

## Decision 4: Extending the gate role pickers (from the clarification)

**Decision**: `onboard.html`'s role `<select>` gains `accent` and `text` options (the current options are
primary/secondary/background, `onboard.html:107-110`); `intake.py`'s CLI prompt string gains them too
(`intake.py:119`). The CLI batch default (first=primary, rest=secondary) is unchanged and still yields
exactly one primary. An "exactly one primary" instruction line is added near the colors step.

**Rationale**: Option A from the clarification. Without it, `accent`/`text` in `ROLE_GUIDANCE` are
unreachable dead branches. Adding two `<option>`s + two words to the CLI prompt is trivial and keeps the
gate in sync with the map (enforced by the Decision 1 sync test).

## Reuse map (touched vs untouched)

| Component | 008 disposition |
|-----------|-----------------|
| `scene_author.assemble_thin_prompt` color block | CHANGED (header wording + per-role instruction + bg guard) |
| `scene_author.ROLE_GUIDANCE` | NEW (module constant, the 5 roles + fallback) |
| `scene_author._primary_color_hex` + register directive | UNCHANGED (anchor preserved) |
| `brand_intake/validate_key.py` | CHANGED (>=1 -> ==1 primary, named errors) |
| `frontend/onboard.html` role select + instruction | CHANGED (5 roles + "exactly one primary") |
| `brand_intake/intake.py` CLI role prompt | CHANGED (5 roles; batch default unchanged) |
| kit / tier-3 / legacy color paths, typography, asset profile, conductor contract | UNCHANGED |
