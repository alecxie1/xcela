# Feature Specification: Lossless Brief (Field Honesty on the Thin Route)

**Feature Branch**: `012-lossless-brief`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Feature 012: lossless brief (field honesty on the thin route). Wire
asset_type + occasion into the thin prompt as a scene/subject line; retire the inert form fields
(audience, warmth, hero_icon) from the frontend; reference_relationship becomes a 3-option
dropdown; expose the existing style_notes lever as a first-run design-notes field; rename the
legacy 'Sign message line' label. No new input concepts. Scope: frontend form, conductor
thin-route threading, one scene line in the thin prompt. Not in scope: register engine (011),
kit/legacy routes, multi-reference (013), dimension interview (014)."

## Context

The live-runner form is the tool's INPUT gate: the place the constitution says the human's intent
must enter whole. Today it leaks. An audit of a real run (the CJXQ watermelon post) found that a
user's entire asset description ("marketing post for social media, promoting a line of new fruit
tea products") and occasion line never reached generation: they stop in intermediate artifacts
that only the unused kit/legacy route reads. Three more controls (audience, warmth, hero icon)
are collected and silently unused on the thin route, the only route the form runs. Free text
typed into "reference relationship" is bucketed to one of three lanes by keyword match and the
rest is discarded: a real user's "grab the product hero shots and the brand mascots" survived
only as the default lane. Meanwhile the single strongest free-text lever the pipeline has (the
binding design-rules block) is not on the form at all; it is reachable only as a re-run nudge.

This is silent human-input loss at the input gate: a constitution I and V defect (the human's
words must either drive the output or be visibly declared out of scope, never quietly dropped).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The asset description and occasion reach the generated image (Priority: P1)

A designer describes WHAT the asset is ("marketing post for a new watermelon drink line") and the
occasion it serves. The generation prompt actually carries that scene/subject context, so the
image is composed as the thing they asked for, not merely inferred from the reference image and
register.

**Why this priority**: This is the reported defect and the core value: the two fields where a
non-designer naturally pours their intent currently reach nothing. Every brief benefits.

**Independent Test**: Assemble the thin prompt for a brief with a distinctive asset_type and
occasion; confirm both values appear verbatim in the prompt as scene CONTEXT, framed so they are
never rendered as words on the asset; confirm a brief with both fields blank produces a prompt
byte-identical to the pre-feature prompt.

**Acceptance Scenarios**:

1. **Given** a brief whose asset_type and occasion are non-empty, **When** the thin prompt is
   assembled, **Then** the prompt contains both values verbatim in a scene/subject section.
2. **Given** the same brief, **When** the prompt is assembled, **Then** the scene section
   explicitly marks these as context that must NOT be painted as text, and the existing
   only-the-headline text guard is unchanged.
3. **Given** a brief with blank asset_type and occasion, **When** the prompt is assembled,
   **Then** the prompt is byte-identical to the pre-feature output (zero regression).

### User Story 2 - Design notes on the first run (Priority: P1)

A designer has a compositional instruction ("products realistic, background cartoon collage")
at brief time. They type it into a design-notes field on the form and it lands in the prompt's
binding design-rules block on the FIRST run, not only as a re-run nudge.

**Why this priority**: The binding-rules block is the strongest free-text lever the pipeline has,
and today it is unreachable at brief time. Exposing it costs one field and immediately widens
what a non-designer can ask for. It is also the new, honest home for the nuance users used to
type into the reference-relationship field.

**Independent Test**: Submit the form with a design note; confirm the note reaches the binding
design-rules block verbatim on the first run, and that a later nudge ADDS to (does not replace)
it.

**Acceptance Scenarios**:

1. **Given** a form submission with a design note, **When** the first run's prompt is assembled,
   **Then** the note appears verbatim in the binding design-rules block.
2. **Given** a first-run note and a subsequent nudge, **When** the re-run's prompt is assembled,
   **Then** BOTH the original note and the nudge appear in the block.
3. **Given** an empty design-notes field, **When** the prompt is assembled, **Then** no
   binding-rules block is added (byte-identical to today).

### User Story 3 - No dead controls on the form (Priority: P2)

A designer looking at the form sees only fields that do something. The audience, warmth, and hero
icon controls (inert on the thin route) are gone. Older saved briefs that still carry those
fields keep working: the values are accepted and recorded as provenance, exactly as today.

**Why this priority**: Honesty and trust. A form that collects dead input trains users to expect
their words to be ignored. Lower than US1/US2 only because removal changes no pixels.

**Independent Test**: Confirm the served form contains no audience, warmth, or hero-icon
controls; confirm an inputs JSON that still carries those fields is accepted, runs, and records
them in the manifest's provenance section unchanged.

**Acceptance Scenarios**:

1. **Given** the live-runner page, **When** it is served, **Then** it contains no audience,
   warmth, or hero-icon input controls.
2. **Given** a legacy inputs JSON carrying audience/warmth/hero_icon, **When** a run executes,
   **Then** the run succeeds and the values appear in the manifest provenance exactly as before.

### User Story 4 - Reference relationship is a choice, not a guess (Priority: P2)

A designer picks how the reference should be used from three clearly described options (extend
the reference as a template / match its style with a fresh layout / loose mood cue). Nothing they
mean can be silently discarded, because there is no free text to discard; nuance belongs in the
design-notes field (US2).

**Why this priority**: Closes the lossy-field trap observed on a real run. P2 because the
default lane happened to work; the loss is real but survivable.

**Independent Test**: Confirm the form offers exactly the three relationship options and each
submits a value that maps 1:1 onto the three existing engine lanes; confirm no free-text entry
path remains for this field.

**Acceptance Scenarios**:

1. **Given** the form, **When** it is served, **Then** the reference-relationship control is a
   fixed choice among exactly three options, each with a plain-language description.
2. **Given** each option, **When** the form is submitted, **Then** the resulting brief value maps
   to the corresponding engine lane deterministically (no keyword guessing on user prose).

### User Story 5 - The message field says what it is (Priority: P3)

A designer making an Instagram post is not asked for a "Sign message line". The field is renamed
to say what it actually is on every asset type: the exact text rendered verbatim on the asset,
the only words allowed to appear.

**Why this priority**: Pure label honesty; no wiring change. Cheap, but it removes a sign-era
confusion for every non-sign brief.

**Independent Test**: Confirm the served form labels the message input with asset-generic,
verbatim-contract wording and contains no "sign message" era label.

**Acceptance Scenarios**:

1. **Given** the live-runner page, **When** it is served, **Then** the message field's label
   describes it as the exact text rendered on the asset (verbatim, the only words allowed) and
   no "Sign message line" label remains.

### Edge Cases

- **Occasion text is renderable Chinese marketing copy** (e.g. 【新品上線】現開西瓜): the scene
  line must be framed as context-not-text, and the existing only-the-headline guard stays; the
  residual risk that the model paints occasion words anyway is explicitly checked at the human
  eye-gate (this is the same failure mode that got the brand slogan removed from the prompt, so
  it must be validated on pixels, not assumed).
- **Both asset_type and occasion blank**: no scene section at all; prompt byte-identical to
  pre-feature (honest null, nothing fabricated).
- **Legacy inputs JSON** (saved briefs, CLI users) with retired fields or free-text
  reference_relationship: accepted unchanged; free text still normalizes through the existing
  keyword fallback; only the FORM stops producing it.
- **Emoji or brackets in occasion**: passed through verbatim as context; never sanitized into
  renderable text.
- **Design note that contradicts a register/render rule**: the binding block already frames
  human notes as mandatory; conflicts are the human's taste call (constitution I), not the
  tool's to resolve.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The thin-route generation prompt MUST include the brief's asset_type and occasion
  values verbatim as a scene/subject context section whenever either is non-empty.
- **FR-002**: The scene section MUST be framed as compositional context that is never to be
  painted as words on the asset, and the existing only-the-headline text guard MUST remain
  unchanged.
- **FR-003**: When asset_type and occasion are both empty, the assembled prompt MUST be
  byte-identical to the pre-feature prompt (no empty scaffolding, no regression).
- **FR-004**: The form MUST provide a free-text design-notes field whose content reaches the
  prompt's binding design-rules block verbatim on the first run.
- **FR-005**: A re-run nudge MUST append to, not replace, the first-run design notes; both MUST
  appear in the re-run's binding block.
- **FR-006**: The form MUST NOT render audience, warmth, or hero-icon controls; briefs that
  carry those fields (legacy JSON, CLI) MUST still be accepted and recorded as provenance in the
  manifest exactly as today.
- **FR-007**: The form's reference-relationship control MUST offer exactly three fixed options
  mapping 1:1 onto the engine's three lanes, with plain-language descriptions; the form MUST NOT
  offer a free-text path for this field. Engine-side keyword normalization stays for legacy
  inputs.
- **FR-008**: The message field's label MUST describe it as the exact text rendered verbatim on
  the asset (the only words allowed) with no sign-era wording; any sibling sign-era labels
  touched by this feature follow the same rule.
- **FR-009**: All new user-facing text (labels, descriptions, prompt section headers) MUST
  contain no em-dashes.
- **FR-010**: The change MUST be confined to the brief-to-prompt path on the thin route (form,
  brief assembly, thin prompt) plus label text; the register engine (011), the render-dialect
  openers (009), and the kit/legacy routes MUST NOT change behavior.

### Key Entities

- **Brief**: the structured intent the form produces; gains no new concepts, loses three dead
  fields from the form surface, keeps full back-compat at the JSON level.
- **Scene/subject section**: the new prompt section carrying asset_type + occasion verbatim as
  context-not-text.
- **Binding design-rules block**: the existing mandatory human-feedback section of the prompt;
  now reachable at brief time, and the union of first-run notes and nudges.
- **Reference-relationship lane**: one of exactly three ways the reference is used (template
  extend / style match / mood cue); a choice, never inferred from prose on the form path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any brief with non-empty asset_type or occasion, the assembled thin prompt
  contains those values verbatim, in 100% of runs (deterministic).
- **SC-002**: For briefs with both fields empty, the assembled prompt is byte-identical to the
  pre-feature output in 100% of runs.
- **SC-003**: A design note typed at brief time appears verbatim in the first run's binding
  block in 100% of runs; after a nudge, both the note and the nudge appear.
- **SC-004**: The served form contains zero inert input controls on the thin route (audience,
  warmth, hero icon gone), zero free-text entry for reference relationship, and zero sign-era
  message labels.
- **SC-005**: A legacy inputs JSON from before this feature runs unchanged with identical
  manifest provenance (zero back-compat breaks).
- **SC-006**: All existing self-test suites pass unchanged (no regressions), verified without
  paid calls.
- **SC-007** (deferred, human eye-gate): One paid run of a real brief (e.g. the CJXQ watermelon
  post re-brief), judged by the human eye: the image's subject matches the asset description
  better than the pre-012 run of the same brief, AND no occasion/scene words leak onto the asset
  as painted text.

## Assumptions

- The thin route is the only route the frontend runs, so retiring form fields cannot starve the
  kit/legacy routes (which have their own CLI inputs and continue to read intent files).
- asset_type and occasion are injected verbatim (no model-based rewriting or translation): the
  tool passes human words through, it does not paraphrase them (constitution V; also the
  deterministic-test requirement).
- The three relationship lanes (extend / match style / mood) are the complete, correct
  vocabulary; this feature changes their capture, not their semantics.
- The design-notes field reuses the existing binding-block channel end to end; no second
  free-text channel is created.
- The label rename is frontend-only wording; the underlying brief field name stays (JSON
  contract unchanged).
- The slogan-hallucination lesson applies: any human text newly placed in the prompt is a
  leakage risk until proven clean on pixels, which is why SC-007 explicitly checks for painted
  scene text.
