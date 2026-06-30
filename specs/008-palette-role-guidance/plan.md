# Implementation Plan: Role-aware Brand Palette + Exactly-one-primary

**Branch**: spec dir `008-palette-role-guidance`; work continues on the existing `006-web-onboarding-gate` git branch by deliberate reuse (as with 007) | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-palette-role-guidance/spec.md`

## Summary

The whole brand palette already reaches the thin generation prompt, but every color is listed with a
bare role label (`name: #hex [role]`, `scene_author.py:884-891`) and only `primary` does any work
(`_primary_color_hex`, `:332`). This feature gives EACH role an operative, confirmed instruction so the
designer's full palette shapes the output (available palette with role guidance, not a rigid must-use),
and it makes the onboarding gate enforce EXACTLY ONE primary plus offer all 5 canonical roles. Brand
identity (the palette) stays the HARD lock; only per-role usage is guidance (constitution §VI).

Three decisions are RESOLVED here, grounded in the code:

1. **The role-to-instruction map is a module constant `ROLE_GUIDANCE` in `scene_author.py`**, next to
   `assemble_thin_prompt`. Its keys ARE the canonical role vocabulary
   (primary/secondary/accent/background/text), and `assemble_thin_prompt` looks up each color's role,
   falling back to a generic palette line for a blank/unknown role. Generation-side is the right home:
   the instruction text is prompt content. The onboarding gate's role options (in `onboard.html` and
   `intake.py`) are kept in sync by a STRUCTURAL TEST that asserts the gate offers exactly the named
   `ROLE_GUIDANCE` roles (the HTML/Python split means the literals live in two places; the test is the
   sync guard).
2. **Exactly-one-primary lives in the shared `validate_lean_key`** (`validate_key.py`), tightening the
   current `>=1` check to `==1` with a named error for the multiple-primary case. Both the web gate
   (`onboard.save_draft`) and the CLI (`intake.py`) already call it, so they enforce identically (DRY) and
   no separate gate pre-check is needed. The onboarding UI adds the instruction text + the role options.
3. **The `background` instruction is guarded by `has_reference`** (already a param of
   `assemble_thin_prompt`). A reference job has chroma OFF, so the background color paints the backdrop; a
   no-reference / chroma job (deferred ref-less path) suppresses the background INSTRUCTION (the color is
   still listed, falling back to the generic palette line) so it never fights the #00B140 chroma key.

No new dependency, no new asset profile, no change to the conductor contract or generation beyond the
thin prompt's color block + the validator + the gate role pickers.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`). Prompt assembly is stdlib string-building; the onboarding
gate is the existing stdlib web app (`onboard.html` vanilla JS + `intake.py` CLI).

**Primary Dependencies**: none new. Touches `harness/scene_author.py` (thin prompt), `brand_intake/
validate_key.py` (validator), `frontend/onboard.html` + `brand_intake/intake.py` (role pickers).

**Storage**: None new. `answer_keys/<brand>.json` `fields.colors.items[].role` already carries the role;
this feature gives each role an effect and constrains primary to one at save.

**Testing**: Falsifiable STRUCTURAL self-tests (`test_*.py`, stdlib). Assert the assembled prompt STRING
(each color's hex + its role instruction; background guard both directions; blank-role fallback) and the
validator (raises on 0 and on >=2 primaries; passes on exactly 1) and the gate-role sync. NO paid model
calls; the one paid sign is the human eye-gate (SC-007) after the build.

**Target Platform**: Localhost web app + CLI on the designer's machine (same as 004/005/006/007).

**Project Type**: Single project; a focused change to the thin prompt + the validator + the gate role
pickers.

**Performance Goals**: N/A (string assembly + a list check).

**Constraints**: GENERALIZES, not hand-tuned (the role map is brand-general, no brand/color literals,
§IV). Brand identity stays the HARD lock; per-role usage is guidance (§VI). Honest-null: an unroled color
still reaches the prompt (§V). The EXACT confirmed wording is verbatim (no paraphrase). Thin route +
validator + gate role pickers only; kit/tier-3/legacy/typography/asset-profile UNCHANGED. No em-dashes in
user-facing text.

**Scale/Scope**: A handful of colors per brand. v1 = the thin route's color block + exactly-one-primary
in the shared validator + the 5-role pickers (web + CLI). No generalization beyond flat-vector signs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The designer assigns each color's role at the human input gate; the tool HONORS those assignments instead of silently discarding all but the primary. No model auto-decides roles. | PASS |
| II. Ground truth = the eye | Tests assert the prompt STRING + the validator only; whether the palette actually reads well per role is the human eye-gate (SC-007). No VLM PASS as proof. | PASS |
| III. Falsifiable tests only | Each color's hex + its role-instruction substring present (a primary-only build fails); blank-role fallback present; background present-with-ref / absent-without-ref; validator raises on 0 and on >=2 primaries, passes on 1; the gate offers exactly the named roles. Each fails a wrong build on a VALUE. | PASS |
| IV. Generalize, do not hand-tune | The role->instruction map is brand-general (no brand/color literals); it helps every brand's palette, not one image. | PASS |
| V. Honest nulls, never invented | An unroled / unknown-role color still reaches the prompt (generic palette line), never dropped; the background guard avoids a fabricated contradiction with the chroma key; the validator fails loud on a bad primary count (no silent first-primary pick). | PASS |
| VI. Reconciliation per-dimension | Brand governs color HARD (the palette stays a hard lock, the header keeps "must read as this brand's"); per-role USAGE is soft guidance. The split is preserved, not collapsed. | PASS |
| VII. Repo is durable; thin / reuse | Stdlib only (no new dep); exactly-one-primary lives in the ONE shared validator (CLI + web identical); the role map is one constant with a sync test; one-module-one-test-one-commit; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid model calls in any automated test; tests assert the assembled string + the
validator. The one paid sign is the human eye-gate after the build. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/008-palette-role-guidance/
├── spec.md              # Feature spec (clarified 2026-06-30: 5-role vocabulary + extend the gate)
├── plan.md              # This file
├── research.md          # Phase 0: the 3 decisions (map home, validator, background guard) + reuse map
├── data-model.md        # Phase 1: the role->instruction map, the color block, the validator rule
├── contracts/
│   ├── palette-prompt-contract.md   # ROLE_GUIDANCE + the assemble_thin_prompt color block + bg guard
│   └── roles-gate-contract.md       # validate_lean_key exactly-one-primary + the 5-role gate sync
├── quickstart.md        # Phase 1: free structural validation + the human eye-gate
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
harness/
└── scene_author.py      # CHANGED: add ROLE_GUIDANCE (module constant, the 5 roles + blank fallback);
                         #   in assemble_thin_prompt's color block (:884-891) replace the header line with
                         #   the confirmed wording and append each color's role instruction; gate the
                         #   `background` instruction on has_reference (else the color falls back to the
                         #   generic palette line). _primary_color_hex anchor UNCHANGED.

brand_intake/
├── validate_key.py      # CHANGED: tighten the primary check from ">=1" to "EXACTLY 1"; a named
│                         #   KeyValidationError on zero primaries AND on two-or-more primaries.
└── intake.py            # CHANGED: the CLI verify-gate role prompt offers all 5 roles
                         #   (primary/secondary/accent/background/text); batch default unchanged
                         #   (first=primary, rest=secondary -> still exactly one primary).

frontend/
└── onboard.html         # CHANGED: the role <select> offers all 5 roles (add accent + text); add the
                         #   "exactly one primary" instruction text near the colors step. No em-dashes.

test_palette_roles.py    # NEW: falsifiable structural self-test (no paid calls). Each role's hex +
                         #   instruction in the assembled prompt; blank-role fallback; background guard
                         #   both directions; the single-primary anchor unchanged; the gate-role sync.
test_brand_key.py        # CHANGED: add the exactly-one-primary cases (raises on >=2 primaries; passes
                         #   on exactly 1). Existing 0-primary + single-primary cases stay green.
                         #   (test_onboard.py fixtures already use one primary; add a multi-primary
                         #   fail-loud case there too.)
```

**Structure Decision**: The generation change is a localized edit to `assemble_thin_prompt`'s color block
plus one module constant (`ROLE_GUIDANCE`) in the same file; the anchor logic (`_primary_color_hex` and
the register directive) is untouched, so the magnitude/register behavior is preserved. The
exactly-one-primary rule goes in the ONE shared validator (`validate_lean_key`) so the CLI and the web
gate enforce identically without a new pre-check. The 5-role vocabulary is offered by both gate surfaces
(`onboard.html` dropdown + `intake.py` prompt), kept honest by a structural sync test against the named
`ROLE_GUIDANCE` keys. Nothing in the kit / tier-3 / legacy color paths, typography, the asset profile, or
the conductor contract changes (FR-009).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
