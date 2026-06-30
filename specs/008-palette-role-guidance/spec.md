# Feature Specification: Role-aware Brand Palette + Exactly-one-primary

**Feature Branch**: `008-palette-role-guidance`

**Created**: 2026-06-30

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief (`specs/_inbox/008-palette-role-guidance.md`). Surfaced while the designer
tested the tool: the whole brand palette is extracted at onboarding and already reaches the generation
prompt, but only ONE color (the primary) does any work. On the thin route the live-runner uses, every
color is listed as `name: #hex [role]` with the role as a BARE LABEL and no instruction, so
`secondary` / `accent` / `background` / `text` are decorative labels with zero operative effect. And
onboarding does not enforce a single primary, so a designer can mark several colors primary and the
prompt silently anchors on the first. Both are silent-judgment / honest-null gaps.

> **Scope note (constitution §IV / §VI):** this feature makes the EXISTING palette FUNCTIONAL on the
> thin route; it does NOT add a new asset profile, change the kit / tier-3 / legacy color paths, or
> generalize beyond flat-vector die-cut event signs (that broader generalization is a separate later
> feature). Brand identity (the palette) stays the HARD lock; only per-role USAGE becomes guidance.

> **The thesis this serves (constitution §VI):** brand governs color HARD (the design must read as this
> brand's colors), while HOW each color is used is soft, human-assigned guidance the tool must honor
> rather than discard. The designer assigns a role to each color; every role must then mean something.

## Clarifications

### Session 2026-06-30

- Q: Strict "must use exactly this color for X" vs "available palette with role guidance"? → A: GUIDANCE.
  Every color reaches the prompt with a role-specific instruction phrased as guidance ("use it for...",
  "use sparingly"), not a rigid must-use, so the model still composes. Brand identity stays the hard lock.
- Q: What happens if a designer assigns more than one primary? → A: Block it. Onboarding enforces EXACTLY
  ONE primary, fail-loud, with a clear in-UI instruction; a co-equal second color is assigned `secondary`.
- Q: Is a reference required right now (does the chroma background path apply)? → A: Yes, reference is
  required in v1 (the live-runner path), so chroma is OFF and a `background` color is safe to paint on the
  deliverable. The background instruction is guarded to defer to the chroma key only on the deferred
  no-reference path (no visible effect today).
- Q: The mapping has 5 roles but the onboarding gate only offers primary/secondary/background. Which role
  vocabulary, and extend the gate? → A: Option A. The canonical vocabulary is the 5 roles
  (primary/secondary/accent/background/text); EXTEND the onboarding gate (the web dropdown AND the CLI
  prompt) to offer all 5, so `accent` and `text` are reachable, not dead branches. Keep the gate and the
  mapping in sync.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every brand color drives real design behavior (Priority: P1)

A designer onboards a brand with several colors and assigns each a role (one primary, plus secondary /
accent / background / text). When they generate, the assembled prompt carries every color WITH a
role-specific instruction, so the whole palette shapes the output, not just the primary.

**Why this priority**: This is the feature. Without it, the designer's role assignments past the primary
are silently dropped (the gap they hit). It makes the palette the designer verified actually functional.

**Independent Test**: Given a brand key with primary + secondary + accent (+ background + text), the
assembled thin prompt contains EACH color's hex AND its role-specific instruction substring (the accent
line says "use sparingly"; the secondary line says it supports the primary; the text line says "legible").
A wrong build that only anchors the primary fails (the other roles' instructions are absent). Free, no
model calls (assert the assembled prompt string).

**Acceptance Scenarios**:

1. **Given** a brand key with colors roled primary / secondary / accent, **When** the generation prompt
   is assembled, **Then** each color appears with its hex AND a role-specific instruction (primary =
   dominant anchor, secondary = supporting, accent = sparing highlights), as guidance not a rigid rule.
2. **Given** a color the designer left unroled (blank / unrecognized role), **When** the prompt is
   assembled, **Then** that color still appears, marked as part of the brand palette (never dropped).
3. **Given** a brand key, **When** the prompt is assembled, **Then** the palette is still framed as a HARD
   brand lock (the design must read as this brand's colors); only the per-role usage is guidance.
4. **Given** a `background`-roled color, **When** the job is a reference job (chroma off, the v1 live
   path), **Then** the background instruction is present; **When** it is a no-reference / chroma job,
   **Then** the background instruction is suppressed (so the brand background does not fight the chroma
   key).

### User Story 2 - Onboarding enforces exactly one primary (Priority: P1)

In the onboarding verify gate, the designer can assign any of the 5 canonical roles
(primary / secondary / accent / background / text) to each color, and is told exactly one color must be
primary. A save with zero primaries OR more than one primary fails loud with a clear in-browser message
and writes no key; a co-equal second color is assigned `secondary`.

**Why this priority**: A single unambiguous primary is what makes the anchor meaningful (the prompt
anchors on the primary). Allowing several primaries silently picks the first and discards the rest, the
exact silent-judgment gap. This guarantees the role mapping in US1 has a clean anchor.

**Independent Test**: The shared key validator RAISES on zero primaries AND on two-or-more primaries, and
PASSES on exactly one; the onboarding save blocks a multi-primary attempt (no file written). The served
onboarding page states the exactly-one-primary rule. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** verified colors with exactly one primary, **When** the designer saves, **Then** the key is
   written and passes validation.
2. **Given** verified colors with zero primaries OR two-or-more primaries, **When** the designer saves,
   **Then** save fails loud with a clear named error and NO key file is written.
3. **Given** the onboarding verify gate, **When** the designer assigns roles, **Then** the UI states that
   exactly one color must be primary (and a co-equal second color goes in as secondary).
4. **Given** the onboarding verify gate (web and CLI), **When** the designer assigns a role, **Then** all
   5 canonical roles are selectable (primary / secondary / accent / background / text), so accent and text
   are reachable and the gate stays in sync with the role mapping.

### Edge Cases

- A color with a blank or unrecognized role → still listed in the prompt as part of the brand palette
  (honest-null; never silently dropped) (US1 AS2).
- A `background` color on a no-reference / chroma job → the background instruction is suppressed so it
  does not contradict the chroma key; today's reference-only live path is unaffected (US1 AS4).
- A save with no primary or several primaries → fail loud, no key written (US2 AS2). Same loudness as the
  existing missing-primary guard, extended to the multiple-primary case.
- An EXISTING committed answer_key that already has multiple primaries → not retroactively rewritten; the
  generation side keeps anchoring on the first primary (the existing fallback). The new rule binds new
  onboarding saves, not historical keys.
- A brand with ONLY a primary (no other roles) → the prompt carries just the primary line, exactly as
  today; the feature adds nothing spurious.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generation prompt on the thin route MUST list every brand color with its hex AND a
  role-specific instruction (not a bare role label), so each role drives real design behavior.
- **FR-002**: The role instructions MUST be GUIDANCE (how to use each color), not a rigid must-use, so the
  model still composes. The exact per-role wording is the confirmed verbatim text recorded in
  `data-model.md` (the role-to-instruction map); the parenthetical here (primary = dominant anchor,
  secondary = supporting, accent = sparing highlights, background = backdrop fill, text = legible type) is
  an illustrative summary, not the literal string.
- **FR-003**: The palette MUST remain framed as a HARD brand lock (the design must read as this brand's
  colors); only the per-role USAGE is guidance (constitution §VI).
- **FR-004**: A color with a blank or unrecognized role MUST still reach the prompt (marked as part of the
  brand palette), never silently dropped (honest-null).
- **FR-005**: The `background` instruction MUST be emitted only when the job is NOT a chroma / no-reference
  job, so a brand background color never contradicts the chroma key (no visible effect on the v1
  reference-only path; a guard for the deferred ref-less path).
- **FR-006**: The single-primary anchor behavior MUST be preserved: the prompt still anchors on the
  primary color (unchanged), now with one unambiguous primary.
- **FR-007**: Onboarding MUST enforce EXACTLY ONE primary at save: zero primaries OR two-or-more primaries
  MUST fail loud (clear in-browser error, no key file written); exactly one primary passes.
- **FR-008**: The onboarding verify gate MUST state that exactly one color is primary (and a co-equal
  second color is assigned secondary).
- **FR-008a**: The onboarding gate MUST let the designer assign any of the 5 canonical roles
  (primary / secondary / accent / background / text) to each color, in BOTH the web dropdown and the CLI
  prompt, so accent and text are reachable and the gate stays in sync with the role-to-instruction
  mapping. (Today the gate offers only primary / secondary / background.)
- **FR-009**: The change is scoped to the thin route, the onboarding validator, and the onboarding gate
  role pickers (web + CLI); the kit / tier-3 / legacy color paths, typography / font roles, and the asset
  profile are UNCHANGED.
- **FR-010**: No paid model calls in any automated test; tests assert the assembled prompt string and the
  validator. The one paid sign remains the human eye-gate (004 / CLI), not part of this feature.
- **FR-011**: No em-dashes in any user-facing text (the onboarding UI, server messages). [The generation
  prompt is model-facing, but is shown in the live-runner prompt stage; keep the new role wording
  em-dash-free for consistency.]

### Key Entities

- **Brand palette color**: an extracted, human-roled color (role + hex + names) in
  `answer_keys/<brand>.json` (`fields.colors.items[]`). Already exists; this feature gives each role an
  operative effect.
- **Role-to-instruction mapping**: the brand-general vocabulary turning a role (primary / secondary /
  accent / background / text / blank) into its confirmed instruction text. The 5 named roles are the
  canonical vocabulary the onboarding gate offers (web + CLI), kept in sync with this mapping. [Its home,
  a small constant near the thin-prompt assembly, is a `/speckit-plan` decision.]
- **Primary-count rule**: the onboarding constraint that exactly one color is primary, enforced by the
  shared key validator. [Whether it lives only in the shared validator or also as a gate pre-check is a
  `/speckit-plan` decision.]

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a brand with primary + secondary + accent (+ background + text), the assembled thin
  prompt contains each color's hex AND its role-specific instruction; a build that anchors only the
  primary fails. (structural, falsifiable)
- **SC-002**: A color with a blank / unrecognized role still appears in the assembled prompt as part of
  the brand palette. (structural, falsifiable)
- **SC-003**: The `background` instruction is present on a reference job and absent on a no-reference /
  chroma job. (structural, falsifiable, both directions)
- **SC-004**: The shared key validator raises on zero primaries and on two-or-more primaries, and passes
  on exactly one; an onboarding save with multiple primaries writes no key. (structural, falsifiable)
- **SC-005**: The served onboarding page states the exactly-one-primary rule. (structural)
- **SC-005a**: The onboarding gate (web dropdown and CLI prompt) offers all 5 canonical roles
  (primary / secondary / accent / background / text), so accent and text are assignable. (structural)
- **SC-006**: The single-primary anchor behavior is unchanged (the prompt still anchors on the primary);
  prior thin-route and brand-key suites stay green. (structural, regression)
- **SC-007**: A designer judges by eye that a generated sign uses the full palette per its roles (accent
  as highlights, etc.), not just the primary. (human eye, §II)
- **SC-008**: No paid model calls occur in any automated test; the one paid sign is the human eye-gate
  after the build. (process)

> The eye-marked criterion (SC-007) is a human-eye judgment per constitution §II; no VLM self-score
> counts as proof. Automated tests assert STRUCTURE only (the assembled prompt string + the validator),
> never pixel quality.

## Assumptions

- The live-runner is reference-required in v1 (feature 007), so generation runs the thin route on a
  reference job with chroma OFF; the role-aware palette (including background) takes effect there. The
  no-reference / chroma path is deferred, and the background guard keeps the mapping correct for it.
- The full palette already reaches the thin prompt (it is listed today with bare role labels); this
  feature adds the per-role instruction text, it does not add a new data source.
- Roles are human-assigned in the onboarding verify gate; extraction leaves role unset. The exactly-one-
  primary rule binds new onboarding saves; existing committed keys are not retroactively rewritten.
- The role-to-instruction wording is the confirmed verbatim text from the 2026-06-30 session; the home of
  the mapping and the exact placement of the primary-count rule are `/speckit-plan` decisions.
- The one paid sign (the eye-gate, SC-007) folds into the existing back-half paid run; this feature ships
  no separate paid run.

## Out of Scope (v1)

- Generalizing beyond flat-vector die-cut event signs (photographic posters / arbitrary materials) - a
  separate later feature; 008 only makes the EXISTING palette functional on the thin route.
- The kit / tier-3 / legacy render-and-scrub color paths - thin route only.
- Re-validating or rewriting existing committed answer_keys that have multiple primaries.
- typography.styles / font-role authoring - untouched (still honest-null).
- The other testing-notes items (merging onboard + live-runner UI, required-field clarity for the message
  line, the scroller layout) - separate from this feature.
- Any new asset profile or rendering mode, and any change to the conductor input contract or generation
  beyond the thin prompt's color block.
