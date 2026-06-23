# Feature Specification: Kit of Parts + Bespoke Per-Message Composition

**Feature Branch**: `001-kit-of-parts-composition`

**Created**: 2026-06-22

**Status**: Draft (starter — refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: The 6/18 reference run produced signs that pass self-tests + font compliance but
FAIL the human eye: text oversized/overflowing, scrub damages graphics, and the signs are
identical behind different text. Root cause is the FRAME: render-and-scrub + dial=`extend`
is a "ONE TEMPLATE, N TEXTS" machine. This feature replaces that frame, for the AIA
flat-graphic event-sign task, with how a human designer actually works.

> **Scope note (constitution §IV, generalize-don't-hand-tune):** this spec is written for
> the AIA event-sign task because that is the task we have ground truth for. The frame
> ("kit of parts + bespoke composition") is the hypothesis; whether it generalizes to other
> brands/asset types is an OPEN question and explicitly out of scope for v1. Do not bake AIA
> literals into shared code.

## The human process we are reverse-engineering (the north star)

From comparing `briefaia.jpg` (a 4-panel ideation thumbnail sheet) to `desiredresultaia.jpg`
(5 finished signs that read as ONE family but are each DISTINCT):

1. **Lock a KIT OF PARTS once** (the constant): palette (crimson + gold + white), the white
   stitched border + gold frame, one bold rounded font, an accent vocabulary (diamonds,
   stars, lightning, dots), the bevel/3D treatment.
2. **For each message, compose bespoke** (the variable):
   a. READ THE MEANING → rhetorical mode (protect / warn / resist).
   b. PICK THE ICON THAT MEANS IT (money bag = guard wallet; megaphone + ❌ = reject scam;
      eyes + fist = stay vigilant).
   c. PICK A LAYOUT FOR THE MODE (warning → white panel + red text for alarm; protect →
      warm solid crimson).
   d. RESERVE THE TEXT ZONE, then FIT type INTO it with margin (composition owns the zone;
      type is sized to fit, never the reverse).
3. **Finish**: vary composition "ever so slightly," polish.

The load-bearing insight: **the kit is the constant, the composition is the variable.** A
human internalizes a STYLE SYSTEM and composes each sign fresh from its message. The
reference image is a style system to INTERNALIZE, not a panel to CLONE.

## Clarifications

### Session 2026-06-22

- Q: How is the per-message meaning→icon choice made, and who owns the vocabulary? → A: The human authors a meaning→icon vocabulary ONCE per brand (that vocabulary IS part of the kit, stored as brand data, never hardcoded). Per message the tool proposes ONE icon by DETERMINISTICALLY matching the message's meaning against that fixed vocabulary (not an open-ended generative guess); the human approves or overrides at the existing approve/nudge taste gate. When no confident match exists, the tool honest-nulls and asks the human to pick, never guessing silently.
- Q: When the style reference and the brand answer key disagree on a kit element, which governs? → A: The answer key always wins on any disagreement. The reference is still internalized into the kit for dimensions where there is no conflict, but the answer key governs every contested element.
- Q: When a message's meaning maps to no icon in the kit, what should happen? → A: Emit an honest null with a note and flag needs_review so the human picks the icon (never auto-substitute, never silently drop the icon role).
- Q: When there are more messages than the kit has distinct layouts, what should happen? → A: The kit holds MULTIPLE distinct layout archetypes (a layout vocabulary). Per message the tool deterministically selects an archetype and, on a collision, picks a different archetype from the kit. Only when the layout vocabulary is genuinely exhausted does it reuse one, and then it flags the reused signs as needs_review for the human to differentiate. No hard cap. The tool does NOT auto-jitter compositions; that slight creative variation is the human finishing layer applied at approve/canvas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each sign is a distinct composition, not a re-texted clone (Priority: P1)

A non-designer gives N messages for one campaign and a style reference. The tool produces N
signs that are visibly DIFFERENT from one another (different icon, different layout suited
to each message's meaning) while unmistakably belonging to one brand family.

**Why this priority**: This is the core failure (c) and the whole point of the reframe. If
signs are still clones, nothing else matters.

**Independent Test**: Generate the 2-sign AIA set (守住钱袋子/护好幸福家 vs 远离非法金融/
抵制高息诱惑) and confirm by the human eye that the two signs differ in composition, not just
text, yet share the kit. [Human-eye gate per constitution §II; no automated pixel score.]

**Acceptance Scenarios**:

1. **Given** two messages with different rhetorical modes, **When** the tool composes them,
   **Then** they receive different icons and different layouts, and a human confirms they
   read as distinct signs in one family.
2. **Given** a message whose meaning implies a specific icon (e.g. 钱袋子 → money bag),
   **When** composed, **Then** the chosen icon matches the meaning, not a default.

### User Story 2 - Headline text fits inside the sign with margin (Priority: P1)

The headline is sized to FIT its reserved zone with comfortable margin; it never overflows
the die-cut or runs off the canvas.

**Why this priority**: Failure (a). A sign with clipped text is unusable regardless of
anything else.

**Independent Test**: Generate any AIA sign and confirm by eye that all characters sit
inside the sign with margin on every edge. [Human-eye gate.]

**Acceptance Scenarios**:

1. **Given** a 2-line headline, **When** placed, **Then** every glyph is within the sign
   boundary with a visible margin on all sides.
2. **Given** a long headline, **When** it cannot fit at full size, **Then** type is scaled
   DOWN to fit the reserved zone (composition owns the zone; honest-null if it truly can't).

### User Story 3 - Graphics are not damaged by text placement (Priority: P2)

Text and graphics are composed into non-colliding zones, so no scrub step is needed to
erase text off an icon, and no icon is left damaged.

**Why this priority**: Failure (b). Lower than P1 because if US1+US2 hold via a
zone-reserving composition, the collision that causes scrub damage largely disappears.

**Independent Test**: Generate an AIA sign with a hero icon and confirm by eye the icon is
intact and text does not overlap it. [Human-eye gate.]

**Acceptance Scenarios**:

1. **Given** a sign with a hero icon, **When** composed, **Then** text occupies its reserved
   zone and the icon occupies its own, with no overlap and no scrub artifact.

### Edge Cases

- A message whose meaning does not map to any known icon in the kit → emit an honest null
  with a note and flag needs_review for the human to pick the icon. Never auto-substitute a
  generic icon and never silently drop the icon role.
- More messages than the kit has distinct layout archetypes → the tool reuses an archetype
  only after the layout vocabulary is genuinely exhausted, and flags every reused sign as
  needs_review so the human differentiates them. No hard cap; the tool does not auto-vary the
  reused composition (that is the human finishing layer).
- A reference that is NOT a clean single-panel style exemplar → out of scope; the human
  supplies a usable reference (constitution §I, human at the input gate).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive a reusable KIT OF PARTS (palette, border/frame
  treatment, font, accent vocabulary) from the brand answer key + the style reference, ONCE
  per campaign, shared across all signs.
- **FR-002**: For each message, the system MUST propose a hero icon by DETERMINISTICALLY
  matching the message's MEANING against the kit's human-authored meaning→icon vocabulary
  (not an open-ended generative guess, not a fixed default). The human approves or overrides
  the proposal at the taste gate. When no confident match exists, the system MUST honest-null
  and flag needs_review rather than guess.
- **FR-003**: The kit MUST hold MULTIPLE distinct layout archetypes (a layout vocabulary).
  For each message the system MUST deterministically select an archetype appropriate to the
  message's rhetorical mode, picking a different archetype when two messages would collide,
  so signs in one campaign differ in composition. The system reuses an archetype only after
  the vocabulary is exhausted and then flags the reused signs as needs_review. The system MUST
  NOT auto-jitter compositions; slight creative variation is the human finishing layer.
- **FR-004**: The system MUST reserve a text zone as part of the composition and FIT the
  headline into that zone with margin, scaling type down as needed.
- **FR-005**: The system MUST keep text and graphics in non-colliding zones (no reliance on
  post-hoc scrubbing to remove text painted over an icon).
- **FR-006**: The system MUST preserve all existing NON-NEGOTIABLE guarantees: licensed-font
  compliance manifest, honest nulls + needs_review, human approve/nudge gate, no em-dashes
  in user-facing text.
- **FR-007**: The reference image MUST be treated as a style system to internalize (feeds
  the kit), NOT a panel to clone. The reference feeds kit dimensions where it does not
  conflict with the brand answer key, but on ANY disagreement the answer key always wins
  (the answer key governs every contested kit element).
- **FR-008**: The system MUST NOT bake AIA-specific literals (icons, colors, layouts) into
  shared/brand-general code; AIA specifics live in data (answer key / kit definition).

### Key Entities

- **Kit of Parts**: the campaign-level constant. Palette, border/frame, font role(s), accent
  vocabulary, treatment. Derived once; consumed by every sign.
- **Message → Composition**: per-sign. Inputs: the message text + its meaning/mode. Outputs:
  chosen icon, chosen layout, a reserved text zone, fitted type spec.
- **Icon vocabulary**: the set of meaning→icon mappings available in the kit (money bag,
  megaphone, shield, eyes, fist, ...). Authored ONCE per brand by the human and stored as
  brand data (never hardcoded). The tool reads it to deterministically PROPOSE a per-message
  icon; the human approves/overrides at the taste gate.
- **Layout vocabulary**: the set of distinct layout archetypes the kit holds (e.g. white
  panel + red text for warn, warm solid crimson for protect). The tool deterministically
  selects one archetype per message, avoiding collisions until the vocabulary is exhausted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the AIA 2-sign set, a human confirms the two signs are DISTINCT compositions
  (different icon AND layout), not re-texted clones. (Primary; the reframe's reason to exist.)
- **SC-002**: On every generated AIA sign, a human confirms all headline text sits inside the
  sign with visible margin on all edges (zero clipping).
- **SC-003**: On every generated AIA sign with a hero icon, a human confirms the icon is
  intact and not overlapped or scrub-damaged.
- **SC-004**: The generated family is judged by the human eye to be closer to the
  `desiredresultaia.jpg` ground truth (distinct-yet-cohesive) than the 6/18 clone output.
- **SC-005**: All NON-NEGOTIABLE guarantees still hold (font compliance, honest nulls, gates).

> All success criteria are HUMAN-EYE judgments per constitution §II. No VLM self-score
> counts as proof. Automated tests assert STRUCTURE only (e.g. distinct icon/layout chosen
> per message, a reserved zone exists, type fits the zone in pixels), never beauty.

## Assumptions

- The human supplies a usable single-panel style reference and the per-message content (the
  input gate stays human, constitution §I).
- AIA is the only brand in scope for v1; brand-generality is designed-in but proven later.
- Much of the existing engine is reusable: `register/` (reconciliation), `composite_text`
  (licensed font + compliance), `measure_canvas` (geometry), and `scene_author`'s tier-3
  path already authors per-sign compositions — the reframe likely ROUTES family jobs through
  composition + a kit, rather than building all-new capability. The plan step must verify
  this reuse against the actual code before proposing new modules.
- The icon-selection-by-meaning step is now specified (see Clarifications 2026-06-22): a
  human-authored meaning→icon vocabulary in brand data, deterministic per-message proposal by
  the tool, human approval/override at the taste gate, honest-null when no confident match.
