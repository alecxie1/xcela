# Feature Specification: Faithful Self-Service Brief Intake + Review

**Feature Branch**: `002-faithful-brief-intake`

**Created**: 2026-06-23

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Brief authored 2026-06-23 (`specs/_inbox/002-faithful-brief-intake.md`). A control
experiment showed raw gpt-image-2, given the client brief + the reference image, beat the
pipeline's output. Root-causing it against the code + git revealed the pipeline never consumed a
real brief: intake was a lossy hand-translation (6 signs became 2; `分别画叉` / `设计两种样式` /
physical size dropped) AND the conductor contract is under-wired (it never reads
`mandatory_elements` or `format_size`). Prior "pipeline tests" were therefore confounded; the
reconciliation engine was never tested on faithful input. This feature fixes the INTAKE so a
clean, reproducible test becomes possible.

> **Scope note (constitution §IV, generalize-don't-hand-tune):** v1 targets AIA because that is
> the only brand with ground truth. The intake is brand-general by design (it reads per-brand
> data), but brand-generality is proven later. Do not bake AIA literals into shared code.

> **The principle this feature encodes (Richard, confirmed by Alec's own experiment):**
> non-designers do not know what to say. The single instruction that won the raw test ("extend
> these 4 signs, keep the same visual language and DNA") maps exactly to the EXISTING
> `reference_relationship="template"` field the briefer omitted. Structured fields capture what
> free text misses. **Fields are the spine; the human fills them; no agent translates.**

## Clarifications

### Session 2026-06-23

- Q: What modality should the intake + review surface take? → A: Extend the EXISTING conductor CLI question form (`ask_questions`) to cover all `brief_schema_v3` fields; review is a CLI / printed digest of the run artifacts. The thinnest surface over the agent-free core, no new stack.
- Q: How should `设计两种样式` / "two styles" (and similar directives) be handled? → A: Verbatim passthrough ONLY. Such directives are captured as literal `mandatory_elements` text and fed verbatim to generation; the tool does NOT interpret them into N style variants and does NOT multiply generations (no agent inference, constitution §I).
- Q: How should `format_size` drive the output? → A: Derive orientation from the size's aspect ratio, snapping to the nearest supported orientation (landscape / portrait / square); record BOTH the requested size and the chosen orientation in the run manifest.
- Q: Where does v1 scope end with respect to running the pipeline? → A: v1 delivers the PLUMBING only: faithful intake emits the inputs, the dropped fields are wired through, and review reads the `run_*/` artifacts. The actual paid pipeline run is the human's one-command action (the surface does NOT orchestrate it); the clean test (SC-003) is then performed by the human.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Self-service faithful intake (Priority: P1)

The human fills the structured brief fields directly (asset_type, format_size, usage_context,
audience, vibe sliders, logo_treatment, brand_strictness, per-sign messages, mandatory_elements,
forbidden_elements, occasion), drops a reference image, and picks a brand. The tool emits the
conductor inputs with ZERO human-translator loss.

**Why this priority**: This removes the confound at the root. Until the brief reaches the
pipeline intact, no pipeline test is trustworthy and no comparison is honest.

**Independent Test**: Author the full AIA brief through the intake surface and confirm that every
field entered appears VERBATIM in the generated conductor inputs and the run manifest, with
nothing dropped, inferred, or rephrased by an agent. [Structural + human-eye per constitution §II.]

**Acceptance Scenarios**:

1. **Given** a 6-sign brief with messages, mandatory_elements (`分别画叉`), a size (`60x40cm`),
   and a reference relationship, **When** the human completes intake, **Then** the emitted
   conductor inputs contain all 6 signs and every entered field verbatim (none dropped).
2. **Given** free-text the human types into a literal field (a message or a mandatory element),
   **When** the inputs are emitted, **Then** that text appears character-for-character unchanged
   (no rephrasing, reordering, or agent-inferred mapping).
3. **Given** an optional field the human leaves blank, **When** the inputs are emitted, **Then**
   it is recorded as empty (honest null), never invented or back-filled.

### User Story 2 - The previously-dropped fields reach generation (Priority: P1)

`mandatory_elements` (e.g. `分别画叉`) and `format_size` (e.g. `60x40cm`) actually flow through to
the generation prompt / composition and are recorded in the run manifest; `format_size` drives
the output orientation and aspect.

**Why this priority**: These two fields have NO path through the current pipeline. The X-marks the
raw model rendered correctly are exactly the content our pipeline drops. Wiring them is the
substantive fix that makes the engine testable on a complete brief.

**Independent Test**: Run a brief containing `分别画叉` and `60x40cm` and confirm (structurally,
no paid generation) that the generation prompt/spec contains the mandatory-element instruction and
that the size is recorded in the manifest and selects the output orientation. The current build
drops both; that is the property the test asserts. [Falsifiable / structural.]

**Acceptance Scenarios**:

1. **Given** a brief with `mandatory_elements` containing `分别画叉`, **When** a sign is composed,
   **Then** the generation prompt or composition spec for that sign contains that instruction, and
   the manifest records it.
2. **Given** a brief with `format_size = 60x40cm` (a 3:2 landscape), **When** generation is
   planned, **Then** the recorded output orientation is landscape and the chosen aspect matches,
   recorded in the manifest.
3. **Given** a brief with no `mandatory_elements`, **When** a sign is composed, **Then** no
   mandatory-element instruction is fabricated (honest null).

### User Story 3 - Self-service review (Priority: P1)

After a run, the human sees, in one place: the output sign images, the structured inputs the
pipeline ACTUALLY received, the per-sign composition picks (icon, layout archetype, reserved text
zone), and every `needs_review` flag, and judges by eye.

**Why this priority**: The review closes the agent-free loop: the human is the judge
(constitution §II), and seeing the inputs the pipeline received is what makes the test
diagnostic rather than a black box.

**Independent Test**: After a run, open the review surface and confirm it shows the output images,
the exact inputs received, the per-sign composition picks, and all needs_review flags, sufficient
for the human to render an eye verdict. [Human-eye gate.]

**Acceptance Scenarios**:

1. **Given** a completed run, **When** the human opens review, **Then** each sign shows its output
   image alongside its chosen icon, layout archetype, reserved text zone, and any needs_review
   reason.
2. **Given** a run that produced a needs_review flag, **When** the human reviews, **Then** the
   flag and its reason are shown (not hidden), so the human can act on it.

### Edge Cases

- An optional field left blank → recorded as empty (honest null), never invented (US1 AS3).
- A `format_size` aspect that no exact valid pixel size can hit → the resolver computes the CLOSEST
  valid aspect within the gpt-image-2 constraints (edges x16, max edge <= 3840, aspect <= 3:1, pixel
  budget), and RECORDS the requested size, the resolved pixel size, and any aspect delta in the
  manifest (honest), never silently forcing a fixed canvas. An aspect beyond 3:1 (e.g. an extreme
  banner) is clamped to 3:1 with the clamp recorded as needs_review, never distorted; SYMMETRICALLY,
  an extreme-portrait aspect below 1:3 is clamped to 1:3 with the same needs_review record. (The
  resolver therefore clamps the requested aspect into [1/3, 3].)
- `mandatory_elements` that conflict with `forbidden_elements` (e.g. require and forbid the same
  thing) → surface the conflict for the human (needs_review); do not silently resolve it.
- Reference image absent → the prompt-only path still works; the reference feeds both channels
  when present (ref+prompt > ref > prompt is designed-in, not required).
- Frontend / intake surface absent → the agent-free core still runs end-to-end from one CLI
  command (the standalone proof, SC-004).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let the human enter the full structured brief directly through an
  EXTENDED conductor CLI question form (`ask_questions`), covering the `brief_schema_v3` fields
  across bucket A (asset_type, format_size), bucket B (usage_context, audience), bucket C (per-sign
  messages, mandatory_elements, forbidden_elements), bucket D (vibe sliders, logo_treatment,
  brand_strictness), the reference input (image + relationship), occasion, and the brand selection.
- **FR-002**: The system MUST emit the conductor inputs as a LOSSLESS image of the entered brief:
  every entered field appears verbatim in the inputs and the run manifest; the sign count matches
  the brief (no collapsing 6 signs to 2).
- **FR-003**: The system MUST NOT use any agent/LLM to infer, rephrase, reorder, map, or "improve"
  brief content. Literal text (messages, mandatory_elements, forbidden_elements) passes through
  VERBATIM. Free-text is allowed only as verbatim passthrough into literal fields, never as an
  agent-inferred mapping into structured fields. Directives embedded in literal content (e.g.
  `设计两种样式` / "two styles") are passed through VERBATIM as `mandatory_elements`; the system MUST
  NOT interpret them into a structured variant count or multiply the number of generations.
- **FR-004**: The system MUST wire `mandatory_elements` through to the per-sign generation prompt /
  composition spec AND record them in the run manifest (the field currently has no path to
  generation).
- **FR-005**: The system MUST record `format_size` in the run manifest and use it to drive the
  output dimensions. A stdlib resolver derives the aspect ratio from the physical size and computes
  the VALID gpt-image-2 pixel size (both edges multiples of 16px) that PRESERVES that aspect and sits
  NEAREST a TARGET AREA, honoring the real generation constraints (max edge <= 3840px; aspect ratio
  <= 3:1; total pixels between 655,360 and 8,294,400). The target area DEFAULTS to the proven AIA
  operating point 1536x1024 (~1.57 MP) and is configurable; it is NOT the hard pixel floor (anchoring
  to the proven baseline avoids an untested resolution regression and gives every aspect the same
  quality/cost tier). It MUST NOT snap to one of three fixed canvases (that "3 sizes" model is wrong:
  gpt-image-2 accepts a continuum of pixel sizes; the popular 1024x1024 / 1536x1024 / 1024x1536 are
  examples, not the allowed set). With the default target, 3:2 resolves to exactly 1536x1024 as a
  CONSEQUENCE of the target area, never hardcoded; other aspects inherit the same ~1.57 MP budget
  (portrait -> 1024x1536, 1:1 -> ~1248x1248, 3:1 -> ~2160x720). The manifest MUST record the requested
  physical size, the resolved pixel size, and the orientation. Print-resolution output
  is out of reach by design (60x40cm at 300DPI is ~7087x4724, above the pixel cap): the tool emits a
  valid-aspect DRAFT; the print-resolution vector rebuild is the human's downstream step.
- **FR-006**: The reference image MUST be first-class and feed BOTH channels: the visual is FED to
  generation and the semantics are PARSED for register. The precedence ref+prompt > ref > prompt
  MUST hold. **002 scope**: 002's responsibility is to CAPTURE the reference (image + relationship)
  faithfully at intake and pass it through VERBATIM to the conductor. The both-channels routing
  itself is EXISTING pipeline behavior inherited from feature 001 (the kit route internalizes the
  reference into the kit via calibration = the semantic channel; the legacy route feeds it visually),
  not re-built or re-verified in 002. The 002 intake test asserts the reference fields are captured
  verbatim; the routing is covered by the 001 regression suite (T016).
- **FR-007**: Brand assets (answer key, kit, licensed fonts, logo, VI) MUST load per-brand from the
  existing brand data; the human PICKS the brand and does not re-enter assets.
- **FR-008**: The review surface MUST present, in one place per run: the output sign images, the
  structured inputs the pipeline actually received, the per-sign composition picks (icon, layout
  archetype, reserved text zone), and every `needs_review` flag with its reason.
- **FR-009**: The intake and review surfaces MUST be THIN over the agent-free core: they shell out
  to or import the EXISTING CLI (conductor, scene_author, generate). They MUST NOT reimplement
  generation, placement, measurement, or judgment.
- **FR-010**: The agent-free core MUST still run end-to-end from one CLI command with the
  intake/review surface absent (the standalone path stays unbroken and is proven by a test).
- **FR-011**: The system MUST preserve all NON-NEGOTIABLE guarantees: licensed-font compliance
  manifest, honest nulls + needs_review, the human approve/nudge gate, no em-dashes in user-facing
  text, and no paid image generation inside any automated test.
- **FR-012**: The human stays at the INPUT gate (enters fields, drops the reference, picks the
  brand) and the TASTE gate (reviews, approves, nudges). No silent agent glue between them.

### Key Entities

- **Structured Brief**: the human-entered `brief_schema_v3` field set (buckets A-D + reference
  input + per-sign content + brand). The single source of intake truth; authored by the human.
- **Conductor Inputs**: the emitted inputs the existing conductor already accepts; a lossless image
  of the Structured Brief (the artifact FR-002 guarantees).
- **Reference Input**: image + relationship; feeds the visual channel (generation) and the semantic
  channel (register). Precedence ref+prompt > ref > prompt.
- **Mandatory / Forbidden Elements**: literal per-brief content that must (or must not) appear; flows
  verbatim to the generation prompt and the manifest (the currently-dropped bucket C content).
- **Format Size**: the physical size / aspect (e.g. `60x40cm`); recorded in the manifest and mapped
  to an output orientation (the currently-dropped bucket A content).
- **Run Review Bundle**: the per-run review view = output images + inputs received + composition
  picks + needs_review flags, read from the existing `run_*/` artifacts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The human completes the full AIA brief (all 6 signs, `分别画叉`, two styles,
  `60x40cm`) through the intake surface with ZERO agent/translator involvement, and the generated
  conductor inputs contain every item entered (zero dropped). (structural + eye)
- **SC-002**: `mandatory_elements` and `format_size` appear in BOTH the run manifest AND the
  generation prompt/spec for the affected signs. (structural, falsifiable)
- **SC-003**: The human reviews the multi-sign output in the surface and renders an eye verdict
  (the first clean test of the pipeline on a faithful brief finally runs). (eye)
- **SC-004**: With the intake/review surface absent, the pipeline still runs end-to-end from one
  CLI command. (structural, the standalone proof)
- **SC-005**: All NON-NEGOTIABLE guarantees still hold: font-compliance manifest present, honest
  nulls + needs_review surfaced, human gates intact, no em-dashes in user-facing text. (structural)

> All eye-marked criteria are human-eye judgments per constitution §II; no VLM self-score counts as
> proof. Automated tests assert STRUCTURE only (fields present verbatim, mandatory_elements + size
> in the prompt/manifest, standalone CLI path intact), never beauty.

## Assumptions

- v1 targets AIA only (the brand with ground truth); brand-generality is designed-in (per-brand
  data) but proven later (constitution §IV).
- The intake/review surface is an EXTENSION of the existing conductor CLI question form
  (`ask_questions`); review is a CLI / printed digest of the run artifacts (decided in
  Clarifications 2026-06-23). No new UI stack in v1.
- `format_size` is resolved by a stdlib helper that maps physical dimensions to an aspect ratio and
  then computes a VALID gpt-image-2 pixel size (edges x16) that preserves that aspect and sits NEAREST
  a TARGET AREA, honoring the real constraints (max edge <= 3840; aspect <= 3:1; total pixels 655,360
  to 8,294,400). The target area DEFAULTS to the proven 1536x1024 (~1.57 MP) operating point and is
  configurable; it is NOT the hard pixel floor (the floor would land 3:2 at ~1008x672, an untested
  resolution regression below every good AIA run). With the default target, 3:2 lands exactly on
  1536x1024 as a consequence, and other aspects inherit the same ~1.57 MP budget. The manifest records
  requested size + resolved pixel size + orientation. Print-resolution is out of reach by design (the
  tool emits a valid-aspect DRAFT; print-res vector rebuild is the human's downstream step).
- The new 002 code (the size resolver, the field-wiring, the manifest additions, the review digest)
  MUST be asset-profile-AGNOSTIC: it must not assume `flat_graphic` / die-cut / landscape / 3:2.
  Photographic and realistic poster assets ARE in PROJECT scope (e.g. the taichi brand and the AIA
  mother's day poster), so a portrait or square photographic poster is a real future input. 002 still
  WIRES only the existing `flat_graphic` path (the `poster` / `photo` profiles in `scene_author.py`
  stay stubbed; the conductor still emits `flat_graphic`), but 002 MUST capture `asset_type`
  faithfully and bake in no flat-graphic assumptions, so adding the photo/poster dialect later is pure
  addition, not rework.
- The human authors the complete brief; the tool does NOT parse a free-text brief into fields
  (rejected on principle, constitution §I) — see Out of Scope.
- Much of the engine is reusable and the plan MUST verify reuse against the ACTUAL code before
  proposing new modules: `conductor.py` already loads and validates `--inputs` and `signs[]`;
  `brief_schema_v3.json` already defines every field (including the two unwired ones);
  `scene_author` / `composite_text` / `measure_canvas` already exist. The likely work is (1) an
  intake surface that writes the inputs JSON the conductor already accepts, (2) wiring
  `mandatory_elements` + `format_size` from inputs through `build_intent` / `scene_author` into the
  prompt + manifest, (3) a review surface that reads the `run_*/` artifacts already written.

## Out of Scope (v1)

- LLM/agent parsing of a free-text brief into structured fields. REJECTED on principle: it
  re-introduces the exact translator confound this feature removes (constitution §I). Free-text is
  allowed only as verbatim passthrough into literal fields.
- Side-by-side raw-model vs. pipeline comparison on identical inputs. Deferred to a later spec
  (valuable, but v1 is faithful intake + review first).
- The eventual stakeholder / demo frontend (different audience, later spec).
- Brand-generality beyond AIA (designed-in, proven later).
- Orchestrating the paid pipeline run from the surface. v1 emits the inputs and reads the run
  artifacts; the human kicks off the run with one CLI command (the surface does not drive a paid
  run, per cost discipline + the agent-free gate).
- Interpreting literal directives (e.g. `设计两种样式`) into a structured variant count or into
  multiple generations per sign. Such directives are verbatim `mandatory_elements` content only.
- Wiring `asset_type` to actually SELECT an output profile, and building the `poster` / `photo`
  (photographic / realistic) render dialects. Photographic poster output is a WANTED future
  capability (taichi, AIA mother's day are photographic), but 002 only keeps the new code
  profile-agnostic so that path is pure addition later. FUTURE SPEC: `asset_type -> asset_profile`
  selection + the photo/poster generation dialect.
