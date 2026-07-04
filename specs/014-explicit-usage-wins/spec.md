# Feature Specification: Explicit Usage Wins Over the Vibe Guess

**Feature Branch**: `014-explicit-usage-wins`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Feature 014: explicit usage wins over the vibe guess. Suppress the
vibe marketing -> event_prop promotion when the marketing base came from an EXPLICIT match on the
marketing-keywords row (marketing / social / instagram / promotional), regardless of render
choice; trace the suppression naming the matched keyword. Narrow scoping: other explicit rows
(wall-posted etc.) and the unmatched default keep the pre-014 vibe promotion byte-identical;
explicit event-prop phrases keep absolute precedence; tone retention applies automatically.
Scope: the register inference only, plus a falsifiable self-test. Motivated by
run_CJXQ_20260701_173925: a flat-vector 'promotional social media post' from a playful brand
rendered as a hand-held event sign."

## Context

The register inference resolves each job to an atmosphere (event_prop / marketing / formal). A
usage phrase rule table sets the base; a vibe heuristic from the flat-vector sign era then
promotes a `marketing` base to `event_prop` whenever the brand is playful and informal. Feature
011 gated that promotion for photographic renders, because a photo marketing job mis-framed as a
prop was the observed defect, and 011 also added common marketing words ("marketing", "social",
"instagram", "promotional") as an explicit usage rule.

Those two 011 changes now collide on the flat lane, observed on a real run
(run_CJXQ_20260701_173925): a designer asked for a flat-vector "promotional social media post".
The usage matched the explicit marketing keyword, the trace recorded the match, and then the vibe
heuristic promoted the job to `event_prop` anyway. The result rendered as a hand-held die-cut
event sign, not the marketing post the designer named twice (usage context AND asset type).

This is the same defect class 011 killed, on the other lane: a machine guess (the vibe heuristic)
overriding a human statement (an explicitly matched usage phrase). The constitution's first
principle says the human's stated intent governs; guesses fill gaps, they do not overrule.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A flat marketing post from a playful brand stays a marketing post (Priority: P1)

A designer at a playful, informal brand requests a flat-vector asset and describes its use with
an ordinary marketing word ("promotional social media post", "instagram", "marketing"). The
inferred register is `marketing`: the output is framed as a flat rectangular marketing poster,
not a hand-held event prop, while the brand's playful tone (rounded type, playful accents) is
retained exactly as it already is for photographic marketing jobs.

**Why this priority**: This is the observed defect. The explicit marketing usage was matched,
recorded, and then overridden; every flat brief from a playful brand that says "marketing" or
"social" mis-renders as a sign until this is fixed.

**Independent Test**: Run the register inference for a flat-render job with a playful+informal
vibe and a usage context containing an explicit marketing word; confirm the register is
`marketing`, the trace names the matched keyword as the reason the vibe promotion was suppressed,
and the playful tone cues are present without the die-cut prop shape cue.

**Acceptance Scenarios**:

1. **Given** a flat-render (or render-unspecified) job with a playful+informal vibe whose usage
   context matches an explicit marketing keyword, **When** the register is inferred, **Then** the
   register is `marketing`.
2. **Given** the same job, **When** the register is inferred, **Then** the reasoning trace states
   the vibe promotion was suppressed because the usage explicitly matched a marketing keyword,
   naming the keyword.
3. **Given** the same job, **When** the register is inferred, **Then** the design cues retain the
   playful tone (rounded font, playful accents) and exclude the die-cut/prop shape cue (the
   existing tone-retention behavior extends to this case without new mechanics).

### User Story 2 - Legacy flat behavior outside the marketing keywords is untouched (Priority: P1)

A designer runs any brief whose usage does NOT match the marketing-keywords rule: the sign-era
defaults ("wall-posted", the derived hand-held phrases), other explicit rules, or free text that
matches nothing. Behavior is byte-identical to before this feature: the vibe promotion still
fires where it fired, including the load-bearing wall-posted + playful case.

**Why this priority**: The wall-posted + playful promotion is pinned legacy behavior (the shipped
die-cut sign flow and the existing baseline literal both depend on it). A fix that widens the
suppression beyond the marketing-keywords rule would trade the proven flat path for the fix.

**Independent Test**: Run the inference for a flat playful job with the wall-posted usage and
confirm the profile is byte-identical to the existing pre-feature baseline; run the unmatched
free-text default case and confirm the promotion still fires.

**Acceptance Scenarios**:

1. **Given** a flat playful job whose usage matches the wall-posted rule, **When** the register
   is inferred, **Then** the full profile is byte-identical to the pre-014 output (`event_prop`,
   same cues, same trace).
2. **Given** a flat playful job whose usage matches no rule (the default marketing base), **When**
   the register is inferred, **Then** the vibe promotion still fires (`event_prop`), unchanged.

### User Story 3 - Explicit event-prop usage keeps absolute precedence (Priority: P2)

A designer who genuinely wants a prop says so ("held for photos") even if the phrase also
contains a marketing word ("instagram photo"). The event-prop usage rules sit earlier in the
rule order, so the base is `event_prop` before the marketing row is ever consulted, and this
feature changes nothing about that.

**Why this priority**: Guards the other human signal. Rule-table precedence already provides
this; the story exists so a test pins it against future reordering.

**Independent Test**: Run the inference with a usage phrase containing both an event keyword and
a marketing keyword; confirm the register is `event_prop` via the event rule, with no suppression
trace.

**Acceptance Scenarios**:

1. **Given** a usage context matching an event-prop keyword (even alongside marketing words),
   **When** the register is inferred, **Then** the register is `event_prop` and no suppression
   entry appears in the trace.

### Edge Cases

- **Photographic render + explicit marketing keyword**: both suppressions would apply; the
  outcome is the same (`marketing`) and the trace must record exactly one suppression entry with
  a clear reason (no duplicate or contradictory lines). Which reason wins the trace line is an
  implementation choice, but it must name at least one true cause.
- **Formal vibe + marketing keyword**: unaffected; the formality>=8 path to `formal` is not part
  of the promotion being gated.
- **Marketing keyword + non-playful vibe**: no promotion attempts to fire; no suppression line;
  unchanged.
- **Vibe values absent**: the promotion never fired for absent vibe values; unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The register inference MUST NOT promote a `marketing` base to `event_prop` on the
  playful+informal vibe when that base came from an explicit match on the marketing-keywords
  usage rule ("marketing", "social", "instagram", "promotional"), regardless of the render
  choice.
- **FR-002**: When FR-001 suppresses the promotion, the reasoning trace MUST record the decision,
  naming the matched marketing keyword as the reason (a falsifiable, human-readable entry).
- **FR-003**: Bases from every other source MUST keep pre-014 behavior byte-identical: other
  explicit usage rules (including wall-posted and the sign-era phrases) and the unmatched default
  keep their vibe promotion exactly as today.
- **FR-004**: Explicit event-prop usage phrases MUST keep absolute precedence (existing rule
  order): a usage matching an event rule resolves to `event_prop` before the marketing rule is
  consulted, with no suppression entry.
- **FR-005**: The existing playful-tone retention MUST apply to the newly suppressed cases with
  no new mechanics: a `marketing` register with the promoting vibe retains rounded font + playful
  accents and never the die-cut shape cue.
- **FR-006**: When both the render gate (photographic) and the explicit-keyword gate apply, the
  trace MUST contain exactly one suppression entry naming a true cause (no duplicates, no
  contradictions).
- **FR-007**: The change MUST be confined to the register inference module and its self-test; the
  orchestrator, prompt assembly, render openers, calibration, kit/legacy routes, and the frontend
  MUST NOT change.
- **FR-008**: Any new trace text MUST contain no em-dashes.

### Key Entities

- **Explicit marketing match**: a `marketing` base that came from the marketing-keywords usage
  rule; the one base source the vibe promotion may no longer override.
- **Vibe promotion**: the flat-vector-era heuristic (playful+informal promotes marketing to
  event_prop); after this feature it fires only for bases that are NOT explicit marketing
  matches, and (per 011) not for photographic renders.
- **Suppression trace entry**: the named, human-readable record of why the promotion did not
  fire (render choice per 011, or the matched marketing keyword per this feature).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a flat playful job with an explicit marketing-keyword usage, the inferred
  register is `marketing` in 100% of runs (deterministic), with the tone cues retained and no
  die-cut cue.
- **SC-002**: For the flat playful wall-posted job, the full profile is byte-identical to the
  existing pre-feature baseline in 100% of runs; the unmatched-default case still promotes.
- **SC-003**: Every suppression produces exactly one trace entry naming a true cause, including
  the double-gate (photo + keyword) case.
- **SC-004**: All existing register/render/conductor self-tests pass unchanged; no paid calls in
  any test.
- **SC-005** (deferred, human eye-gate): One paid flat-vector marketing-post run from the playful
  brand, judged by the eye as a flat rectangular marketing poster (playful tone, no die-cut
  hand-held sign). MAY be satisfied cheaply: if the operator's next paid run is photographic (e.g.
  the pending 013 product-refs gate), a FREE dry-run trace check (register=marketing, no die-cut
  flex, suppression entry present) plus the eye on the next natural flat run suffices; the
  structural fix is fully proven by SC-001..004 and the flat pixels carry no new mechanism beyond
  the register value.

## Assumptions

- The marketing-keywords rule was added in 011 with no pre-existing behavior depending on its
  interaction with the vibe promotion, so suppressing the promotion for exactly that rule cannot
  regress any shipped flow; the wall-posted promotion, by contrast, is pinned by the existing
  baseline literal and stays.
- Tone retention already keys on register+vibe (not on how the register was reached), so FR-005
  requires no code, only a test.
- The trace's existing "matched <keyword>" entry identifies which rule produced the base, so the
  suppression can name the keyword without new bookkeeping beyond remembering the matched row.
- A single suppression entry in the double-gate case is preferred over two entries because the
  trace is read by a human reviewer; either true cause is acceptable as the named reason.
