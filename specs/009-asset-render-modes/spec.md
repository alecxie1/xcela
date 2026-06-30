# Feature Specification: Beyond Flat-vector Event Signs (Render Modes)

**Feature Branch**: `009-asset-render-modes`

**Created**: 2026-06-30

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief (`specs/_inbox/009-asset-render-modes.md`). THE BIG ONE surfaced while the
designer tested the tool: it only ever produces flat-vector die-cut hand-held event signs, even though
the brief's `asset_type` is free text. Two hard-codings cause it: the conductor hard-wires the render
mode to `flat_graphic` (`conductor.py:62`, `:24`), and the thin prompt opener hard-codes "hand-held event
sign" in both flat branches (`scene_author.py:866-878`), so even a flat poster announces itself as an
event sign. This feature lets the TASK drive the render mode and framing, so a designer can also produce
flat rectangular posters/flyers and PHOTOGRAPHIC posters, on the thin route.

> **Scope note (constitution §IV / §VI):** the bones already exist (both `photo` and `flat_graphic`
> dialects, the `--asset-profile` flag, chroma auto-off for non-flat, a dormant generic opener), so this
> is mostly: stop hard-wiring the profile, let the human pick it, and generalize the opener. It is scoped
> to the THIN route (the live-runner reference job: chroma off, deliverable final.png, no measure /
> composite). The kit / tier-3 / no-reference-cutout / legacy paths, where the flat-vector + chroma + OCR
> assumptions live, are OUT of scope.

> **The thesis this serves (constitution §VI):** brand DNA and task needs DIVERGE. Brand still governs
> color / fonts / logo HARD; the TASK governs the SOFT dimensions (render style, shape, register). The
> tool was frozen to one task (event signs); this lets the task govern its SOFT dimensions per-dimension
> instead, without collapsing the split.

## Clarifications

### Session 2026-06-30

- Q: Generalize on which surface in v1? → A: the THIN route / live-runner ONLY (reference required, chroma
  off, deliverable final.png, no measure / composite). The kit / tier-3 / no-reference-cutout / legacy
  paths are out of scope (their flat-vector + chroma + OCR assumptions are a separate, larger lift).
- Q: How is the render mode chosen? → A: an EXPLICIT human pick at the input gate (a render-style control:
  flat vector / photographic), default flat vector. NO model classifier of the free-text asset_type
  (silent judgment is rejected, constitution §I).
- Q: Is shape (die-cut vs rectangular) a second manual control? → A: No. Shape is DERIVED from the
  register (event_prop -> die-cut hand-held prop; marketing / formal -> rectangular poster / flyer), which
  the human already drives via usage_context. One explicit control (render style) keeps the gate simple.
- Q: v1 beachhead? → A: flat-rectangular + photographic on the reference thin path; the existing flat
  event-sign path stays the default and unchanged.
- Q: Is photographic allowed for any register, or only wall-posted / marketing? → A: ANY register. The
  human deliberately picks both the render style and the usage (which drives the register), so a
  photographic event-prop is an explicit choice, not a silent inference; render style and shape stay
  orthogonal. A photographic event-prop gets a photographic hand-held-prop opener; no restriction.
- Q: How is the render choice carried in the brief? → A: a NEW explicit `render_style` field (user terms:
  flat vector / photographic), default flat vector, mapped to the internal render dialect downstream (NOT
  by overloading the free-text asset_type). The exact mapping LOCATION stays a plan detail.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose a render style and generate in it (Priority: P1)

The designer picks a render style in the live-runner (flat vector or photographic) and generates; the
chosen mode drives the prompt's render dialect, so a photographic brief yields a photographic asset and a
flat brief yields a flat graphic.

**Why this priority**: This is the unlock. Today every output is flat vector regardless of intent. Letting
the human pick the render mode (agent-free) is the core of the feature.

**Independent Test**: The assembled thin prompt for the photographic mode contains photographic language
and does NOT contain the flat-vector negatives ("FLAT VECTOR", "no photographic shading"), while still
keeping the text guards (the verbatim headline, no-extra-Chinese / no-gibberish); the flat mode keeps the
flat dialect. A build that ignores the chosen mode still says flat vector and fails. Free, no model calls
(assert the assembled string).

**Acceptance Scenarios**:

1. **Given** a brief with render style = photographic, **When** the prompt is assembled, **Then** it uses
   photographic language and omits the flat-vector negatives, while the headline-text guards remain.
2. **Given** a brief with render style = flat vector, **When** the prompt is assembled, **Then** it uses
   the flat-vector dialect (including the flat render negatives), as today.
3. **Given** a photographic reference job (the v1 live path), **When** it generates, **Then** the chroma
   key stays off and the deliverable is final.png (no cutout).

### User Story 2 - Framing follows the asset, not a hard-coded event sign (Priority: P1)

A flat brief whose use is wall-posted (a poster / flyer) is framed as a rectangular marketing graphic, not
as a hand-held event sign; an event-prop brief is still framed as a die-cut hand-held prop.

**Why this priority**: Even within flat vector, the opener hard-codes "hand-held event sign," so a flat
poster is mislabeled. Generalizing the framing (driven by the register) is half of "flat-vector event
signs" and is required for the render-mode unlock to read correctly.

**Independent Test**: The assembled flat-mode opener for a marketing / wall-posted register does NOT
contain "hand-held event sign" and reads as a rectangular poster / marketing graphic; the flat-mode opener
for an event-prop register is unchanged (die-cut hand-held prop). A build with the hard-coded event-sign
opener fails the first. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** a flat brief in a marketing / wall-posted register, **When** the prompt is assembled, **Then**
   the opener frames a rectangular poster / marketing graphic and does NOT say "hand-held event sign."
2. **Given** a flat brief in an event-prop register, **When** the prompt is assembled, **Then** the opener
   is the die-cut hand-held prop framing, unchanged from today.
3. **Given** the brief's `asset_type` free text, **When** the opener is assembled, **Then** it may use that
   text for specificity without letting other (hallucinated) text appear on the asset.

### User Story 3 - The choice reaches generation; the existing path is unchanged (Priority: P1)

The designer's render choice actually flows from the brief through to generation (the system stops forcing
flat vector), and a brief with no render choice defaults to flat vector with the existing event-sign output
unchanged.

**Why this priority**: The unlock is moot if the choice never reaches generation, and the proven event-sign
path must not regress. This is the plumbing + back-compat guarantee.

**Independent Test**: Building the generation plan for a photographic brief carries the photographic mode
into the generation step (not the hard-wired flat default); a brief with no render choice carries flat
vector and the event-sign output is byte-unchanged. Free, no model calls (assert the plan / argv + the
inputs round-trip).

**Acceptance Scenarios**:

1. **Given** a brief with render style = photographic, **When** the generation plan is built, **Then** the
   generation step is told to render in the photographic mode (not the flat default).
2. **Given** a brief with no render style, **When** the plan is built, **Then** it defaults to flat vector
   and the existing flat event-sign output is unchanged (regression).
3. **Given** an unrecognized render style value, **When** the plan is built, **Then** it falls back to flat
   vector (honest-null) and the choice is recorded.

### Edge Cases

- A brief with no / omitted render style → flat vector (the safe default); the event-sign path is
  byte-unchanged (US3 AS2).
- An unrecognized render-style value → flat vector fallback, recorded (US3 AS3); never a silent guess of a
  different mode.
- A photographic brief in an event-prop register (a photographic hand-held prop) → ALLOWED in v1 (any
  register); it gets a photographic hand-held-prop opener. Render style and shape are orthogonal and the
  human chose both deliberately (no restriction, no warning).
- The thin route paints any Chinese text it sees → the headline-text guards (verbatim headline only, no
  extra Chinese / no tagline / no watermark) apply in BOTH render modes; only the render-specific negatives
  (no photographic shading / 3D) are flat-only.
- A no-reference (chroma on, cutout) job → OUT of scope in v1; the render-mode choice applies on the
  reference thin path only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The live-runner MUST present an EXPLICIT render-style control (flat vector / photographic) at
  the input gate, defaulting to flat vector, carried as a `render_style` field in the brief. The system
  MUST NOT infer the render mode from free-text `asset_type` with a model (agent-free).
- **FR-002**: The chosen render style MUST drive the generation prompt's render dialect; the flat-vector
  dialect MUST NOT leak into the photographic mode and vice versa.
- **FR-003**: In the photographic mode, the prompt MUST use photographic language and MUST NOT include the
  flat-vector render negatives ("no photographic shading", "no 3D realism", "FLAT VECTOR"); the
  render-agnostic text guards (verbatim headline only, no extra Chinese / no gibberish / no tagline / no
  watermark) MUST still apply.
- **FR-004**: In the flat-vector mode, the opener MUST be register-aware: an event-prop register frames a
  die-cut hand-held prop (unchanged from today); a marketing / formal (wall-posted) register frames a
  rectangular poster / marketing graphic and MUST NOT say "hand-held event sign."
- **FR-005**: The asset shape / format MUST be derived from the register (event_prop -> die-cut;
  marketing / formal -> rectangular), NOT a separate manual control.
- **FR-006**: The system MUST carry the chosen render mode from the brief through to the generation step on
  the thin route (it MUST stop hard-wiring flat vector) and MUST record the chosen mode in the run manifest.
- **FR-007**: A brief with no render style MUST default to flat vector, and the existing flat event-sign
  output MUST be unchanged (back-compat / regression).
- **FR-008**: An unrecognized render-style value MUST fall back to flat vector (honest-null) and be
  recorded, never silently rendered as a different mode.
- **FR-009**: The change MUST be scoped to the thin route (reference job: chroma off, deliverable
  final.png, no measure / composite); the kit / tier-3 / no-reference-cutout / legacy render-and-scrub
  paths MUST be UNCHANGED.
- **FR-010**: No paid model calls in any automated test; tests assert the assembled prompt string, the
  generation plan / argv, and the inputs round-trip. The one paid sign (a real photographic poster) is the
  human eye-gate.
- **FR-011**: No em-dashes in any user-facing text (the live-runner control / labels, server messages).
- **FR-012**: The render-mode generalization MUST be task-general (driven by render style + register), not
  tuned to one image (generalize, do not hand-tune).

### Key Entities

- **Render style**: the designer's explicit choice (flat vector / photographic), carried as a new
  `render_style` field in the brief, defaulting to flat vector; mapped to the internal render dialect
  downstream. [WHERE the user-term to dialect mapping happens is a `/speckit-plan` decision.]
- **Render dialect (asset profile)**: the rendering mode the prompt speaks (flat-vector graphic vs
  photographic). Both dialects already exist; this feature makes the choice reachable.
- **Register-derived shape**: the asset shape / framing implied by the register (event_prop -> die-cut
  hand-held prop; marketing / formal -> rectangular poster / flyer), derived not manually chosen.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A designer generates a PHOTOGRAPHIC poster AND a flat rectangular flyer through the
  live-runner, not just a die-cut event sign. (eye + structural)
- **SC-002**: The photographic-mode prompt contains photographic language and omits the flat-vector
  negatives, while retaining the text guards. (structural, falsifiable)
- **SC-003**: The flat-mode opener for a marketing / wall-posted register does NOT say "hand-held event
  sign"; the event-prop opener is unchanged. (structural, falsifiable)
- **SC-004**: The generation plan for a photographic brief carries the photographic mode to the generation
  step (not the hard-wired flat default); a default brief carries flat vector. (structural, falsifiable)
- **SC-005**: A brief with no render style yields a byte-unchanged flat event-sign output (regression).
  (structural, falsifiable)
- **SC-006**: The served live-runner page has a render-style control. (structural)
- **SC-007**: A generated photographic poster actually reads as photographic (not flat vector) by the human
  eye, and a flat rectangular flyer reads as a rectangular poster, not a die-cut sign. (human eye, §II)
- **SC-008**: No paid model calls occur in any automated test; the one paid sign is the human eye-gate.
  (process)

> SC-007 is the LOAD-BEARING criterion: structural tests prove the dialect SWITCHED, but only the human eye
> on a real generated photographic poster confirms it actually looks photographic (constitution §II). No
> VLM self-score counts. Automated tests assert STRUCTURE only.

## Assumptions

- The live-runner is reference-required (feature 007); generation runs the thin route on a reference job
  (chroma off, deliverable final.png), so a photographic poster needs no cutout. The render-mode choice
  applies on this path; the no-reference / chroma / cutout path is deferred.
- Both render dialects already exist in the engine and the chroma key already auto-disables for the
  non-flat mode; this feature makes the choice reachable and generalizes the opener, it does not add a new
  rendering engine.
- Shape / format follows the register the human already drives via usage_context; no second control.
- WHERE the `render_style` user term maps to the internal dialect, the EXACT photographic opener wording,
  and the negatives regrouping are `/speckit-plan` decisions. (Settled: the carrier is a new `render_style`
  brief field; photographic is allowed for any register.)
- The one paid sign (SC-007) folds into the existing back-half paid run; this feature ships no separate
  paid run, but its value is genuinely eye-validated, not structural.

## Out of Scope (v1)

- The kit / tier-3 / no-reference-cutout / legacy render-and-scrub paths and the measure / composite OCR
  pipeline (where the flat-vector + chroma assumptions are baked).
- The no-reference (chroma on, cutout.png) job in any render mode.
- Auto-classifying `asset_type` into a render mode (the human picks).
- New physical print specs, bleed / format presets, or social-tile sizes beyond what the existing
  format-size handling does.
- typography / font roles, the palette work (feature 008), and any conductor input-contract change beyond
  adding the render-style carrier.
- Quality-tuning the photographic dialect to one specific image (generalize, do not hand-tune).
