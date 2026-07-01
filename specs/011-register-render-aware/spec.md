# Feature Specification: Render-Aware Register

**Feature Branch**: `011-register-render-aware`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Feature 011: render/asset-aware register. Fix the flat-vector-era heuristic where derive_register promotes marketing -> event_prop on any playful+informal brand vibe, regardless of what is being made. Thread render_style into the register engine and GATE the marketing->event_prop vibe override so it does NOT fire for photographic renders; explicit usage_context event_prop keywords remain a hard signal that still wins. Also add marketing keyword coverage. Record the gate in the derivation trace. Scope: thin route only; do not touch the opener matrix (009) or the legacy/kit paths."

## Context

The tool infers a *register* (event_prop / marketing / formal) for each job. Register decides the
atmosphere of the generated asset: `event_prop` frames a playful, hand-held, die-cut prop that people
grab and pose with; `marketing` frames a polished, on-brand promotional piece.

That inference was written in the event-sign era, when the ONLY thing the tool made was a flat die-cut
hand-held sign. It reasons purely from the brand's vibe (how playful / how formal) plus a usage phrase.
Under that assumption, "playful brand + informal vibe" reliably meant "grabbable event prop."

Since feature 009, the designer can also request a **photographic** asset (e.g. a marketing social
post). A photograph of a person holding a die-cut prop is a completely different deliverable from a
polished marketing photo. But the register inference never learned that render choice exists: a playful,
informal brand asking for a *photographic marketing post* is still pushed into `event_prop`, so the
downstream framing describes a hand-held photo-prop instead of a marketing post. This was observed on a
real run (a watermelon-product Instagram post that came out framed as an event prop).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Photographic marketing keeps a marketing register, playful character intact (Priority: P1)

A designer at a playful, informal brand requests a **photographic** marketing asset (e.g. a new-product
social post). They do not describe an event or a hand-held prop anywhere in the brief. The tool should
treat this as a marketing job, so the *format* reads as a polished promotional poster, not a grabbable
event prop, **while keeping the brand's playful character** (bubbly rounded type, candy-bright accents).
The result is a *playful marketing poster*, not a stiff corporate one.

**Why this priority**: This is the reported defect and the whole reason for the feature. Without it, every
photographic asset from a playful brand is mis-framed, which is the most common brand profile the tool
serves. Fixing only the format while stripping the playful character would swap one wrong output (a prop)
for another (a corporate poster) — so the format fix and the tone preservation ship together.

**The two axes** (why this is the whole game): the old register bundled two separate decisions under one
label. Feature 011 splits them along the constitution's brand-HARD / task-SOFT seam:
- **Format** (prop vs poster, die-cut vs rectangular) is a *task* decision → follows the render choice.
- **Tone** (bubbly-playful vs polished-restrained) is a *brand-vibe* decision → follows the vibe, not the
  register label.

**Independent Test**: Run the register inference for a photographic job with a playful/informal brand vibe
and no event language; confirm (a) the inferred register is `marketing`, not `event_prop`; (b) the trace
names the render choice as the reason the playful-vibe promotion was suppressed; and (c) the resulting
design cues still carry the playful tone (rounded font + playful accents) but NOT the die-cut/prop shape.

**Acceptance Scenarios**:

1. **Given** a job whose render choice is photographic, a playful+informal brand vibe, and a usage context
   with no event/prop language, **When** the register is inferred, **Then** the register is `marketing`.
2. **Given** the same job, **When** the register is inferred, **Then** the recorded reasoning trace states
   that the playful-vibe promotion to `event_prop` was suppressed because the render choice is photographic.
3. **Given** the same job, **When** the register is inferred, **Then** the design carries the playful tone
   cues (rounded display font and playful/candy accent palette) AND does NOT carry the die-cut/hand-held
   prop shape cue (the format is a rectangular poster, the tone stays playful).

### User Story 2 - Flat assets preserve the existing event-prop behavior (Priority: P1)

A designer requests a **flat graphic** asset (the historical default, e.g. a die-cut event sign) for the
same playful, informal brand. The tool must keep behaving exactly as before: this is still an event prop.
The fix must not regress the flat path that is already in production.

**Why this priority**: The flat die-cut sign is the tool's proven, shipped output. A fix that quietly
changes its register would break the primary use case while fixing the secondary one.

**Independent Test**: Run the register inference for a flat-graphic job with the same playful/informal vibe
and no event language; confirm the inferred register is still `event_prop`, identical to the prior result.

**Acceptance Scenarios**:

1. **Given** a job whose render choice is flat graphic, a playful+informal brand vibe, and a usage context
   with no event language, **When** the register is inferred, **Then** the register is `event_prop` (the
   pre-feature behavior).

### User Story 3 - An explicit event-prop request always wins (Priority: P2)

A designer genuinely wants a *photographed* hand-held prop (a real person holding a die-cut sign for
photos). They say so explicitly in the usage context (e.g. "held for photos"). The render-aware guard must
not override an explicit human instruction: an explicit event/prop usage keeps the event-prop register even
when the render choice is photographic.

**Why this priority**: Honors the constitution's human-at-the-gates principle. The render guard is a guard
against a *guess*, not against an explicit human statement. Lower priority only because it is the rarer path.

**Independent Test**: Run the register inference for a photographic job whose usage context explicitly
contains event-prop language; confirm the register is `event_prop` despite the photographic render.

**Acceptance Scenarios**:

1. **Given** a photographic job whose usage context explicitly says the asset is held for photos, **When**
   the register is inferred, **Then** the register is `event_prop` (the explicit human signal wins over the
   render guard).

### User Story 4 - Common marketing usage phrases are recognized (Priority: P3)

A designer describes the usage in ordinary marketing words ("marketing", "social", "instagram",
"promotional") rather than one of the tool's known usage phrases. The tool should recognize these as
marketing usage explicitly, rather than silently falling back to a default.

**Why this priority**: Defensive robustness. The render guard already fixes the reported bug; this reduces
reliance on the default path and makes the reasoning trace clearer. Lowest priority because it is a
belt-and-suspenders improvement, not the core fix.

**Independent Test**: Run the register inference with a usage context containing a common marketing word and
confirm the reasoning trace shows it matched a marketing rule explicitly (not the fallback default).

**Acceptance Scenarios**:

1. **Given** a usage context containing a common marketing word, **When** the register is inferred, **Then**
   the reasoning trace records that it matched a marketing usage rule explicitly.

### Edge Cases

- **Render choice absent / unknown**: If a job does not carry a render choice (older inputs, other routes),
  the inference MUST behave exactly as before the feature (default to the flat interpretation), so nothing
  regresses.
- **Render photographic + formal vibe**: The photographic guard only concerns the playful-vibe promotion to
  event_prop. A high-formality vibe that resolves to `formal` is unaffected.
- **Explicit event keyword + flat render**: Unchanged, remains `event_prop`.
- **Conflicting signals** (explicit event keyword yet photographic render): resolved in favor of the
  explicit human keyword (User Story 3); the trace records both facts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The register inference MUST receive the job's render choice (photographic vs flat graphic) as
  an input, carried through from the brief to the inference step.
- **FR-002**: The register inference MUST NOT promote a job from `marketing` to `event_prop` on the basis of
  a playful+informal brand vibe alone when the render choice is photographic.
- **FR-003**: The register inference MUST still promote a playful+informal `marketing` job to `event_prop`
  when the render choice is flat graphic, preserving the pre-feature behavior for the flat path.
- **FR-004**: An explicit event-prop usage phrase in the brief MUST result in an `event_prop` register
  regardless of the render choice (explicit human signal overrides the render guard).
- **FR-005**: When the render guard suppresses the playful-vibe promotion, the inference MUST record that
  decision in its human-readable reasoning trace, naming the render choice as the reason.
- **FR-006**: The register inference MUST recognize common marketing usage words ("marketing", "social",
  "instagram", "promotional") as a marketing usage rule, recording the match explicitly in the trace rather
  than relying on the unmatched default.
- **FR-007**: When the render choice is absent or unrecognized, the inference MUST behave exactly as it did
  before this feature (no regression for inputs that carry no render choice).
- **FR-008**: The change MUST be confined to the register inference, the brief-to-inference plumbing, and
  the register-to-design-cue mapping on the thin route. The downstream framing/opener selection (feature
  009) and the legacy/kit generation paths MUST NOT be modified.
- **FR-009**: When a job resolves to the `marketing` register but carries a playful+informal brand vibe
  (the same vibe that would have promoted it to `event_prop`), the design cues MUST retain the *playful
  tone* — a rounded/bubbly display font and playful/candy accent palette — so a playful brand's marketing
  asset does not collapse into a restrained corporate register.
- **FR-010**: The playful-tone cues retained under FR-009 MUST NOT include the *prop-format* cue: a
  `marketing` job MUST NOT be given the die-cut / hand-held-prop shape (a marketing asset is a rectangular
  poster). Format follows the task; tone follows the vibe; the two are decided independently.
- **FR-011**: The playful-tone retention MUST be driven by the brand vibe, not by the render choice, so it
  applies wherever a `marketing` register meets a playful+informal vibe; and it MUST be recorded in the
  reasoning trace (which cues were retained and why).

### Key Entities *(include if feature involves data)*

- **Register**: The inferred atmosphere of a job: one of `event_prop`, `marketing`, `formal`. Consumed
  downstream to choose framing language.
- **Render choice**: The designer's requested rendering style for the asset (photographic vs flat graphic),
  set in the brief and now also an input to register inference.
- **Usage context**: A short human phrase describing how the asset is used; may contain explicit event/prop
  or marketing language that acts as a hard signal.
- **Brand vibe**: The brand's playfulness/formality sliders; a soft signal that sets direction but must no
  longer, on its own, override the render choice. It independently governs the *tone* cues (playful vs
  restrained) regardless of the format the register selects.
- **Design cues**: The concrete, per-dimension design instructions the register produces — split into
  *format* cues (prop/die-cut vs rectangular poster; task-driven) and *tone* cues (rounded/playful font +
  accents vs sharp/restrained; vibe-driven). Feature 011 decides these two independently.
- **Reasoning trace**: The human-readable, step-by-step record of why a register and its cues were chosen;
  must remain falsifiable and now must record both the render-guard decision and the retained tone cues.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a photographic job with a playful+informal vibe and no event language, the inferred
  register is `marketing` in 100% of runs (deterministic).
- **SC-002**: For the equivalent flat-graphic job, the inferred register remains `event_prop` in 100% of
  runs, identical to the pre-feature result (zero regressions on the flat path).
- **SC-003**: For a photographic job with an explicit event-prop usage phrase, the inferred register is
  `event_prop` in 100% of runs.
- **SC-004**: Every register inference that suppresses the playful-vibe promotion produces a reasoning trace
  entry naming the render choice; a reviewer can read the trace and see exactly why the register was chosen
  (no silent decisions).
- **SC-005**: For a photographic + playful/informal `marketing` job, the resulting design cues include the
  playful tone (rounded font + playful accents) and exclude the die-cut/prop shape, in 100% of runs
  (deterministic) — a playful brand's marketing asset stays playful without becoming a prop.
- **SC-006**: All existing register and render-mode self-tests continue to pass (no regressions), verified
  without any paid model calls.
- **SC-007** (deferred, human eye-gate): One photographic marketing job from a playful brand, judged by the
  human eye, reads as a *playful marketing poster* — a polished promotional piece that still feels on-brand
  and energetic, rather than either a hand-held event prop or a stiff corporate poster.

## Assumptions

- The render choice is already captured in the brief on the thin route (feature 009) and is available to the
  step that assembles inputs for register inference; this feature threads it one layer further.
- "Photographic" is the only render choice that should suppress the playful-vibe event-prop promotion; all
  other/unknown render choices are treated as flat (the historical default), preserving current behavior.
- The explicit-usage hard signals already recognized by the tool (event/prop phrases) remain the correct way
  for a human to request a photographed prop; this feature does not add new usage vocabulary for that.
- The downstream framing already distinguishes photographic vs flat and marketing vs event_prop correctly
  (feature 009); the format defect is that it was being fed the wrong register. The separate tone concern
  (a playful brand's marketing asset should stay playful) is handled inside the register-to-design-cue
  mapping, not by changing the 009 framing.
- No change to the legacy render-and-scrub or kit paths, which always produce flat graphics and are out of
  scope.
