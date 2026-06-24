# Feature Specification: Frontend Live-Runner (single-sign)

**Feature Branch**: `004-frontend-live-runner`

**Created**: 2026-06-24

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief authored 2026-06-24 PM (`specs/_inbox/004-frontend-live-runner.md`),
after the thin spine (feature 003) was verified clean by the human eye
(`output/run_aia_20260624_142340/`, route=thin: 6 distinct on-brief signs, zero dupes/blanks,
`分别画叉` rendered as X marks). The pipeline now runs agent-free from one CLI command. What is
missing is a way for the operator to DRIVE it himself without hand-editing JSON and reading a
terminal: type a brief into a form, watch the thin spine execute stage by stage, judge the sign, and
nudge-rerun if needed.

> **Scope note (constitution §IV):** v1 targets the existing single-brand single-sign thin route
> (AIA is the only brand with an answer key today). The frontend is brand-general by reading
> `answer_keys/*.json`, but brand-generality is proven later. No AIA literals in shared code.

> **The thesis this feature serves (constitution §I/§II):** the human stays at the TASTE gate and is
> the ground truth. A viewer that only shows finished pixels would blind the operator to WHY a sign
> came out wrong, so the middle stages (the dial, the assembled prompt) are first-class, not the
> final image alone.

## Clarifications

### Session 2026-06-24

- Q: When does the UI show the run stages (brief → dial → assembled prompt → sign)? → A: PROGRESSIVELY (live). The UI polls the run directory during execution and shows each stage as its artifact lands, so the register/dial + the assembled prompt appear BEFORE the paid gpt-image-2 call returns. This lets the operator catch a wrong dial or a bad prompt before spending the ~$0.08 generation.
- Q: When the operator nudges (binding note → regenerate), how are the attempts stored? → A: Each (re)run writes a NEW `run_*` directory. Prior attempts are preserved and auditable, so the operator can compare the nudge result against the previous sign (no in-place overwrite).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-sign structured intake (Priority: P1)

The operator fills a STRUCTURED typed form (labeled fields, the feature-002 conductor-inputs
schema) for ONE sign, picks a brand from a dropdown over existing answer keys, and supplies a
required reference image. The tool writes a single-sign inputs JSON (002 shape) VERBATIM: no field
rephrased, reordered, or inferred.

**Why this priority**: This is the anti-lossy core. A prose-to-fields parser is exactly the lossy
hand-translation the 002 pivot killed; the form keeps every field byte-for-byte with no parser.

**Independent Test**: Fill the form and confirm the written inputs JSON's fields equal the typed
values byte-for-byte (`messages`, `mandatory_elements`, the three vibe integers), that `signs[]` has
exactly ONE entry, and that the JSON validates against the existing `validate_inputs`. Free, no
model calls.

**Acceptance Scenarios**:

1. **Given** a filled single-sign form, **When** it writes the inputs JSON, **Then** every typed
   value appears byte-for-byte (no rephrase/reorder/inference) and `signs[]` has exactly one entry.
2. **Given** the written JSON, **When** it is handed to the existing conductor, **Then**
   `validate_inputs` accepts it (the form cannot emit a brief the CLI would reject).
3. **Given** the brand dropdown, **When** the operator selects a brand, **Then** the choice is an
   existing `answer_keys/<brand>.json` (the form selects an answer key; it does not author one).

### User Story 2 - Live run with inspectable stages (Priority: P1)

The operator presses Run (labeled with the real per-run paid cost). The thin route executes against
the existing CLI, and the UI surfaces, read from the run directory, each stage: the echoed brief,
the register/dial, the assembled prompt, and the generated sign.

**Why this priority**: This is the operator's TEST instrument: he is checking whether the dial and
the assembled prompt are RIGHT, not only whether the final sign looks good. Surfacing the middle is
how he catches a wrong dial or a bad prompt before blaming the model.

**Independent Test**: Confirm the stage rendering reads the run-dir artifact PATHS
(`register_profile.json`, `sign_s1/final_prompt.txt`, `sign_s1/generated.png`), not a parallel
in-UI computation; that stages appear PROGRESSIVELY as their artifacts land (the dial + prompt
before the image); and that a dry-run / `--explain` path exercises the frontend logic with no paid
generation. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** a running job, **When** the register/dial and assembled-prompt artifacts have been
   written but the image has not, **Then** the UI already shows the dial + the assembled prompt
   (progressive display before the paid gpt-image-2 call returns).
2. **Given** a completed run, **When** the operator views it, **Then** the UI shows the brief echo,
   the register/dial (`inferred_register`, formality/playfulness, `anchors_held`, `locks_flexed`),
   the assembled prompt (`final_prompt.txt`), and the generated sign (`generated.png`).
3. **Given** a run, **When** a stage artifact is missing (e.g. an honest-null blank sign), **Then**
   the UI shows the null plus the manifest note, never a fabricated placeholder.

### User Story 3 - Human taste gate (approve or nudge-rerun) (Priority: P1)

After a run, the operator takes ONE of two actions: approve (good, stop) OR nudge-rerun (type a
binding note that triggers a single-sign regeneration with the note as a binding clause).

**Why this priority**: Constitution §I (the human stays at the taste gate). The gate, not the
viewer, is the point: a bad single sign is nudged, not discarded, so reject-without-rerun is cut as
redundant.

**Independent Test**: Confirm a nudge produces a re-run whose generation prompt includes the binding
note, and that approve stops the run. The non-interactive rerun TRIGGER mechanism is resolved at
`/speckit-plan` (the conductor's gate is a terminal `input()` loop today; the UI must not orchestrate
reruns itself). Pixel quality is the human's eye.

**Acceptance Scenarios**:

1. **Given** a generated sign, **When** the operator approves, **Then** the run stops with the sign
   as the deliverable.
2. **Given** a generated sign, **When** the operator nudges with a binding note, **Then** the single
   sign regenerates into a NEW `run_*` directory, the note appears as a binding clause in the new
   assembled prompt, and the prior attempt remains available to compare against.

### Edge Cases

- A stage artifact is missing (honest-null blank sign, or a failed step) → the UI SHOWS the null +
  the manifest note; it never fabricates a placeholder or hides the gap (constitution §V).
- No reference image supplied → v1 requires a reference; the form blocks Run until one is provided
  (ref-less thin runs are deferred, not offered).
- The paid generation fails (model error / timeout) → the UI surfaces the failure + the manifest
  note honestly, rather than showing a stale or fabricated image.
- The brand dropdown over `answer_keys/*.json` finds only `aia` today → the form works for any brand
  with a present answer key (brand-general; no hardcoded brand).
- A run is in flight when the operator triggers another → runs are single-flight (one at a time); the
  Run / nudge control is disabled until the in-flight run reaches the taste gate (the instrument is
  single-operator, single-sign).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present a STRUCTURED typed form (labeled fields) rendering the
  feature-002 conductor-inputs schema for ONE sign (the authoritative contract is
  `specs/002-faithful-brief-intake/contracts/inputs-schema.md`), NOT a natural-language prose box.
  The stale repo-root `brief_schema.json` MUST NOT be used.
- **FR-002**: The form MUST write a single-sign inputs JSON in the 002 shape, byte-for-byte VERBATIM
  (no field rephrased, reordered, or inferred), with exactly ONE entry in `signs[]`.
- **FR-003**: The written JSON MUST validate against the existing conductor `validate_inputs` (the
  form cannot emit a brief the CLI would reject).
- **FR-004**: The brand MUST be selected from a dropdown over existing `answer_keys/*.json`; the form
  selects an answer key and does NOT author or upload one.
- **FR-005**: A reference image MUST be REQUIRED in v1; Run is blocked until a reference is supplied.
- **FR-006**: A live run MUST be the default action. Pressing Run MUST invoke the existing CLI thin
  route (shell out to the conductor) and MUST NOT reimplement generation, register derivation, or
  prompt assembly in the UI.
- **FR-007**: The UI MUST surface, READ FROM THE RUN DIRECTORY, the stages: the brief echo, the
  register/dial (`register_profile.json`), the assembled prompt (`sign_s1/final_prompt.txt`), and the
  generated sign (`sign_s1/generated.png`). Stages MUST appear PROGRESSIVELY as each artifact lands
  (the dial + assembled prompt before the paid image returns), by polling the run dir during
  execution. It MUST NOT show the final image only.
- **FR-008**: The taste gate MUST expose exactly TWO actions: approve (good, stop) OR nudge-rerun (a
  binding note that regenerates the single sign with the note as a binding clause). Each nudge-rerun
  MUST write a NEW `run_*` directory (prior attempts preserved + auditable; no in-place overwrite),
  so the operator can compare the nudge result against the previous sign. Reject-without-rerun is out
  of scope.
- **FR-009**: The Run / rerun control MUST label the real per-run paid cost (~$0.08 single-sign); the
  human triggers the paid call deliberately.
- **FR-010**: Honest nulls: when a stage artifact is missing, the UI MUST show the null + the
  manifest note, never a fabricated placeholder (constitution §V).
- **FR-011**: The standalone CLI core MUST still run the thin route end-to-end from ONE command with
  the frontend absent; the UI MUST add no dependency the core needs (constitution §I/§VII).
- **FR-012**: No paid image generation in ANY automated test; the build + tests use the written-JSON
  surface + dry-run / `--explain`. The one paid single-sign run is the human's eye-gate after build.
- **FR-013**: No em-dashes in any user-facing text (Output rule).

### Key Entities

- **Single-sign Brief (form state)**: the feature-002 fields for ONE sign (asset_type, format_size,
  reference image + relationship, vibe sliders, logo_treatment, brand_strictness, occasion,
  usage_context, audience, mandatory/forbidden elements, the one sign's messages + optional per-sign
  elements) + the selected brand.
- **Inputs JSON (002 shape)**: the verbatim artifact the form writes and the conductor consumes;
  exactly one `signs[]` entry; validates against `validate_inputs`.
- **Run Stages**: the artifacts the UI renders PROGRESSIVELY (as each lands), read from the run dir:
  brief echo, `register_profile.json` (the dial), `final_prompt.txt` (the assembled prompt),
  `generated.png` (the sign), plus the `conductor_manifest.json` notes.
- **Run / Attempt**: one `run_*` directory = one (re)run attempt. A nudge produces a new attempt
  dir; prior attempts persist so the operator can compare.
- **Taste Action**: one of {approve (stop), nudge (binding note -> regenerate the single sign)}.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The operator types a single-sign brief, presses Run, watches the register/dial + the
  assembled prompt + the generated sign appear, and approves or nudges, all in the browser, with the
  standalone CLI core unchanged. (eye + structural)
- **SC-002**: The written inputs JSON equals the typed values byte-for-byte (`messages`,
  `mandatory_elements`, the three vibe integers), has exactly ONE `signs[]` entry, and validates
  against the existing `validate_inputs`. (structural, falsifiable)
- **SC-003**: The stages render PROGRESSIVELY from the run-dir artifact PATHS (`register_profile.json`,
  `final_prompt.txt`, `generated.png`) as each lands, proving the UI consumes the agent-free
  artifacts (not a parallel in-UI computation) and surfaces the dial + prompt before the paid image.
  (structural)
- **SC-004**: A nudge regenerates the single sign into a NEW `run_*` dir with the binding note in the
  new assembled prompt, the prior attempt preserved; approve stops the run. (eye + structural)
- **SC-005**: The thin route runs end-to-end from one CLI command with the frontend absent.
  (structural, the standalone proof)
- **SC-006**: No paid generation occurs in any automated test; the one paid single-sign run (~$0.08)
  is the human's eye-gate after the build. (process / cost discipline)

> All eye-marked criteria are human-eye judgments per constitution §II; no VLM self-score counts as
> proof. Automated tests assert STRUCTURE only (verbatim JSON, one-sign invariant, validate_inputs
> acceptance, stage rendering reads run-dir paths, standalone CLI intact), never pixel quality.

## Assumptions

- The frontend is a LOCAL web app on the operator's machine that invokes the existing CLI on the same
  host and reads the run dir; it is the operator's test instrument first, a demo second (not a hosted
  multi-user service). The specific UI framework / stack is deferred to `/speckit-plan`.
- The form renders the feature-002 inputs contract verbatim; the stale repo-root `brief_schema.json`
  (different field names: subject / poster|banner / mood_shift) is explicitly NOT used. Reference
  instance: `inputs_lily_aia.json`.
- The non-interactive single-sign-(re)run-plus-binding-note TRIGGER mechanism is an OPEN QUESTION for
  `/speckit-plan` (the conductor's gate is a terminal `input()` loop today). The likely answer is a
  small non-interactive CLI entry point on the conductor that the UI calls, NOT UI-orchestrated
  reruns (which would violate the thin posture, §I/§VII). The plan resolves it against the real
  `approve.py` + `assemble_thin_prompt(style_notes=...)` code. This spec does not solve it.
- Verified codebase state to confirm at plan/build: `conductor.py --thin` runs the thin route today;
  the single-sign case needs NO conductor change (the per-sign loop runs once for a 1-entry
  `signs[]`); the thin route already writes the full trace to the run dir
  (`subfields.json` -> `calibration.json` -> `register_profile.json` -> `intent_s1.json` ->
  `sign_s1/final_prompt.txt` -> `sign_s1/generated.png` -> `conductor_manifest.json`).
- Brand-general by reading `answer_keys/*.json`; only `aia` is present today (proven later, §IV).

## Out of Scope (v1)

- Campaign / multi-sign output, the grid, parallelism, and the concurrency (K-cap) pool. Single-sign
  deletes that whole sub-project; a user who wants 6 signs runs 6 single-sign briefs for now. A later
  spec handles campaigns (where register coherence across signs must be solved deliberately).
- The brand-intake FRONT HALF: upload logo / VI / refs -> `analyze_brand_v3` -> answer-key authoring
  + human verify. Separate later spec.
- Ref-less thin runs (structurally supported but pixels unjudged; deferred, not offered in v1).
- The licensed-font moat.
- A prose-to-fields natural-language parser. REJECTED on principle: it re-introduces the lossy
  hand-translation the 002 pivot removed (constitution §I).
- Hosted / multi-user deployment; the brand-upload widget.
- The UI orchestrating rerun logic itself (it must call the agent-free CLI surface, not reimplement).
