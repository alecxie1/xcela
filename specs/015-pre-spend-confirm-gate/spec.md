# Feature Specification: Pre-Spend Confirm Gate

**Feature Branch**: `015-pre-spend-confirm-gate`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Pre-spend confirm gate: the tool shows its guesses before you pay. The dimension interview (clarify-style, ambiguity-driven questions whose answers become subfields) scoped to the evidence: split the run at the derive/generate seam, surface every recorded assumption as a confirmable row, answers write back and re-derive free, generation happens only on operator confirmation. Full brief: specs/_inbox/pre-spend-confirm-gate.md."

## Clarifications

### Session 2026-07-08

- Q: When a surfaced assumption stems from a free-text input that matched no known
  pattern, what should the gate's correction control offer? → A: A constrained direct
  pick of the derived dimension's vocabulary (e.g. the register lane), recorded as an
  explicit human statement the engine treats as a hard signal; no free-text retype loop.
- Q: Does the paid rerun launched by a post-image nudge also stop at the pre-spend gate?
  → A: Yes. Every browser-launched run gates, first runs and nudge reruns alike; the
  invariant is "no browser run spends without a confirmed plan."
- Q: Which inputs can the operator change at the gate itself? → A: Assumption rows only.
  The gate edits exactly what the tool guessed; for anything else the operator abandons
  the draft (free, honest) and resubmits the form.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what the tool decided before paying (Priority: P1)

The operator fills the run form and submits. Instead of the tool immediately generating an
image, it stops after working out its plan: the register lane it derived (marketing poster
vs hand-held event prop vs formal piece), which brand rules it held and which it flexed,
the final prompt framing, and, most importantly, an explicit list of every assumption it
made on the operator's behalf (each one naming what was assumed and which blank or
unrecognized input caused it). The expensive image generation runs only when the operator
confirms. Today the operator commits the spend at the moment of submission and discovers a
misframe only in the finished image; every register defect to date (the 011 photo-prop
misframe, the 014 die-cut marketing post) was found by paying for a wrong picture.

**Why this priority**: This is the value core. It converts the recurring failure class
(machine deciding where the human had, or would have had, a statement) from "paid
misrender, then a diagnosis session, then a repair feature" into "caught free at a gate."
It also catches engine bugs on explicit input: a wrong derived lane is visible on the
confirm screen regardless of whether the cause was a guess or a defect.

**Independent Test**: Submit a brief through the browser form; verify the run stops with
the derived plan and assumption list visible and NO image generated; confirm; verify
exactly one generation happens and it uses the confirmed plan.

**Acceptance Scenarios**:

1. **Given** a filled run form, **When** the operator submits, **Then** the run produces
   the derived register profile, the assumption list, and the assembled prompt, and stops
   with zero image generations and a visible confirm action stating the paid cost.
2. **Given** a stopped run at the gate, **When** the operator confirms, **Then** exactly
   one image generation runs, using exactly the derivation the operator saw (no silent
   re-derivation between confirm and generate).
3. **Given** the archived brief that produced the historical die-cut defect (the 014
   defect inputs), **When** it is replayed through the gate, **Then** the wrong lane would
   have been visible pre-spend: the gate shows the derived register by name before any
   generation.

---

### User Story 2 - Fix a wrong assumption without paying (Priority: P2)

One of the surfaced assumptions is wrong (for example: the usage the operator typed
matched no known pattern, so the tool defaulted the job to a marketing base; or the size
could not be parsed, so it fell back to the standard canvas). The operator changes the
answer directly on the gate screen using constrained controls (selects, sliders, direct
picks of the dimension's vocabulary; never a free-text retype loop). The tool re-derives
its plan within seconds at no image cost, and
the gate refreshes to show the updated lane, flexes, assumptions, and prompt. The operator
iterates until it reads right, then confirms and pays once.

**Why this priority**: Seeing a wrong plan is only half the value; the correction loop
must be free, or the operator is back to paying per iteration. Depends on US1's gate
existing.

**Independent Test**: At a gate whose assumption list is non-empty, change one answer;
verify the derivation updates without any generation; verify the updated profile is
identical to what a fresh run would have produced had the form carried that answer from
the start.

**Acceptance Scenarios**:

1. **Given** a gate showing an assumption row, **When** the operator changes that answer,
   **Then** the plan re-derives with zero image generations and the gate shows the updated
   derivation and assumption list.
2. **Given** an answer changed at the gate, **When** the re-derived profile is compared to
   a fresh run whose form had that value from the start, **Then** the two register
   profiles are identical (no path dependence, no residue of the earlier guess).
3. **Given** an invalid answer (out-of-range value, unparseable size), **When** the
   operator applies it, **Then** the gate reports the problem by name, keeps the previous
   derivation, and does not generate.

---

### User Story 3 - No friction when nothing was guessed (Priority: P3)

The operator writes a complete, unambiguous brief: every field filled with recognized
values, nothing defaulted. The gate shows a clean summary (derived lane, held/flexed
rules, prompt) with zero assumption rows and a single confirm action. Scripted and
command-line runs keep their existing one-shot behavior unchanged, so existing workflows
and tests are untouched.

**Why this priority**: Protects the 90% case from interview fatigue and protects every
existing surface from regression. The gate must never invent questions when the
derivation made no guesses.

**Independent Test**: Run a brief whose recorded derivation contains no guess or fallback
markers; verify the gate renders zero assumption rows. Run the existing CLI flow; verify
byte-identical behavior to today.

**Acceptance Scenarios**:

1. **Given** a brief where every dimension was explicit and recognized, **When** the gate
   renders, **Then** it shows zero assumption rows and one confirm action (one extra click
   versus today, nothing more).
2. **Given** the existing command-line one-shot flow (including kit and legacy brands),
   **When** it runs, **Then** its behavior and artifacts are byte-identical to today (the
   gate is a browser-flow feature; explicit one-shot bypass remains).

---

### Edge Cases

- Operator walks away at the gate: the stopped run persists as an auditable draft with an
  honest note (derived, never confirmed), and no image spend ever happens.
- Operator changes an answer that removes the reason for a different assumption (or
  creates a new one): the assumption list is recomputed from the fresh derivation each
  round, never accumulated.
- The reference image already uploaded in phase 1 is reused across re-derivations and at
  confirm; the operator is never asked to re-upload, and the visual magnitude reading is
  not re-run when only answers change.
- Two browser tabs on the same gate: confirmation is idempotent; a second confirm of an
  already-generated run must not trigger a second spend.
- A brief whose derivation contains ONLY benign notes (no guesses): notes may be shown as
  context but must not render as questions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A browser-initiated run MUST stop after deriving its plan (register
  direction and magnitude, held/flexed rules, assembled prompt) and before any image
  generation; generation MUST require an explicit operator confirmation. This applies to
  EVERY browser-launched run, including the rerun a post-image nudge launches: no browser
  run spends without a confirmed plan.
- **FR-002**: The gate MUST display the derived register lane, the anchors held versus
  locks flexed, and the final assembled prompt, as they will actually be used.
- **FR-003**: The gate MUST display every assumption the derivation recorded (defaults,
  unmatched inputs, fallbacks, clamps) as a distinct row naming (a) what was assumed,
  (b) the input whose absence or mismatch caused it, and (c) a control to change it.
  Assumption rows are the ONLY editable surface at the gate; explicitly-supplied inputs
  are shown read-only, and changing them means abandoning the draft and resubmitting the
  form (which costs no image spend).
- **FR-004**: Assumption detection MUST be deterministic, derived solely from the run's
  own recorded derivation trace and manifest notes; no model call and no new judgment
  layer may decide what counts as ambiguous.
- **FR-005**: Changing an answer at the gate MUST write the value back into the run's
  inputs, re-derive the plan without any image generation, and refresh the gate; the
  loop MUST be repeatable. Where the assumption stems from a free-text input that matched
  no known pattern, the control MUST be a constrained pick of the derived dimension's
  vocabulary (not a free-text retype), and the pick MUST be recorded as an explicit human
  statement that the derivation treats as a hard signal (a guess can never override it).
- **FR-006**: A profile re-derived after an answer change MUST be identical to the profile
  of a fresh run whose form carried that value from the start.
- **FR-007**: Confirmation MUST generate from exactly the derivation the operator
  confirmed; if anything about the derivation changes after the gate rendered, the gate
  MUST refresh rather than silently generate from unseen values.
- **FR-008**: When the derivation recorded zero assumptions, the gate MUST render zero
  assumption rows (a plain summary plus confirm; it must not manufacture questions).
- **FR-009**: The existing one-shot command-line flow, including kit and legacy brands,
  MUST remain available and byte-identical; the gate applies to the browser flow, with an
  explicit bypass for scripted use.
- **FR-010**: A run abandoned at the gate MUST persist as an auditable draft with an
  honest manifest note and zero image spend.
- **FR-011**: The confirm action MUST state the paid cost before the operator commits;
  the correction loop MUST be presented as free.
- **FR-012**: Confirmation MUST be idempotent: repeated confirms of the same gate MUST
  NOT trigger repeated spends.
- **FR-013**: All user-facing text introduced by this feature MUST contain no em-dashes
  (project output rule).

### Key Entities

- **Derivation draft**: a stopped run at the gate; carries the operator's inputs, the
  derived register profile with its trace, the assembled prompt, and a state (awaiting
  confirmation / confirmed / abandoned). Persists on disk like any run.
- **Assumption row**: one surfaced guess; carries the dimension it concerns, the assumed
  value, the reason (which input was blank or unrecognized), and a constrained control:
  the same vocabulary the form uses where one exists, otherwise the derived dimension's
  own constrained vocabulary (a direct pick recorded as an explicit human statement).
  Recomputed from the trace on every re-derivation.
- **Confirmation**: the operator's explicit, cost-stated commitment binding one specific
  derivation draft to one generation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On 100% of browser runs, every recorded assumption is visible to the
  operator before any image spend.
- **SC-002**: Correcting a wrong assumption costs zero image generations and completes in
  under 30 seconds per iteration (today: one paid generation and a full rerun per
  correction).
- **SC-003**: Replaying the archived inputs of the historical misframe defects (the 011
  and 014 defect briefs) surfaces the decisive register lane at the gate, pre-spend, in
  both cases.
- **SC-004**: A complete, unambiguous brief costs the operator exactly one additional
  click versus today's flow, and shows zero questions.
- **SC-005**: All existing automated suites pass unchanged, and the one-shot CLI flow's
  artifacts are byte-identical for identical inputs (structural proof, no paid calls).
- **SC-006**: The human eye-gate: in one live browser run, the operator sees the plan and
  at least one assumption, changes an answer, watches the plan update free, confirms,
  pays exactly once, and judges that the image matches the confirmed framing.

## Assumptions

- The reference image remains required for browser runs, and the small visual-analysis
  step (reading style magnitude from the reference) runs in the pre-confirm phase; its
  cost is a few cents and is accepted as part of the free-feeling correction loop. The
  gate exists to protect the expensive step (image generation), not to zero all cost.
- The gate lives in the existing run screen (the progressive stages view); this feature
  adds a stop point and controls there, not a new application or wizard.
- Answer changes never re-run the visual magnitude reading (it depends only on the
  reference image, which answers cannot change).
- The post-generation approve/nudge taste gate is unchanged in role (it remains the taste
  gate); the paid rerun a nudge launches passes through the pre-spend gate like any other
  browser run, so the operator sees how the note changed the plan before paying again.
- Visual pickers (exemplar thumbnails per option), multi-step interview flow, and
  model-authored questions are explicitly deferred (recorded in the inbox brief); they
  layer on only if operators demonstrably struggle with the textual gate.
- Kit and legacy render paths are out of scope; their existing CLI gates stand.
