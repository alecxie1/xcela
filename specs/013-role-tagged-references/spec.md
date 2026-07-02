# Feature Specification: Role-Tagged References (Style + Product)

**Feature Branch**: `013-role-tagged-references`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Feature 013: role-tagged references (style + product). Split the
single do-everything reference into a STYLE reference (exactly one, today's semantics) and
PRODUCT references (zero or more, NEW): real product shots fed to generation as additional input
images with a product-fidelity instruction, so the actual branded products appear in the
composition as supplied facts rather than requested favors. Motivated by the 012 eye-gate run
where realistic regeneration lost the printed brand logos. Absent product refs = byte-identical
behavior. Not in scope: register engine/calibration changes, kit/legacy routes, roles beyond
style/product, the dimension interview (014)."

## Context

The tool accepts exactly ONE reference image, and that image plays every role at once: it sets
how far the design departs from corporate defaults (magnitude), it is the style exemplar shown to
the generator, and it is the only source of truth about what the brand's actual products look
like. Those are different jobs with different fidelity needs: style is atmosphere the task may
flex, but the product IS the brand, as hard a lock as the logo or the primary color.

The conflation has a measured cost. On the 012 eye-gate run (run_CJXQ_20260701_164912), a design
note asking for realistic products made the generator rebuild the cups from imagination instead
of carrying the reference's branded cup shots, and the printed 茶救星球 JO'S CHA logos vanished.
The pipeline had done everything it could: the logo file was supplied and the prompt demanded
faithful logo use. On today's path, product fidelity is a requested favor. A designer cannot hand
the tool a photo of the actual product and say "THIS object, exactly."

This feature adds that input gate. It gives reference images ROLES: one style reference (exactly
today's behavior) and any number of product references (new: supplied product truth, carried into
the composition faithfully). Constitution VI seam: product is brand-HARD content; style stays the
task-SOFT exemplar it already is.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real product shots appear in the composition (Priority: P1)

A designer making a product-launch marketing asset uploads, alongside the style reference, one or
more photos of the actual products (the branded cups). The generated draft composes THOSE
products, with their printed branding, instead of inventing generic look-alikes.

**Why this priority**: This is the whole feature: the measured defect (vanished cup logos) is
fixed by making the product a supplied input instead of a description. It is the difference
between a draft a human can finish and a draft that misrepresents the client's product.

**Independent Test**: Run a brief with a style reference plus product references; confirm the
product images are delivered to the generation step as additional inputs, the prompt carries a
product-fidelity instruction naming them, and the run record lists them. (Whether the pixels
actually carry the products is the deferred eye-gate, SC-006.)

**Acceptance Scenarios**:

1. **Given** a brief with a style reference and two product references, **When** the job runs,
   **Then** the generation step receives the style reference, the product references, and the
   logo as input images, and the prompt contains a product-fidelity section stating the supplied
   product images must be carried into the composition faithfully (not redrawn as generic
   products).
2. **Given** the same brief, **When** the run completes, **Then** the run manifest records each
   product reference (which files, in what role) so the run is auditable.
3. **Given** product references, **When** the register/calibration step runs, **Then** it uses
   ONLY the style reference (product images do not influence magnitude or register).

### User Story 2 - Style-only briefs behave exactly as today (Priority: P1)

A designer who uploads only the style reference (today's workflow, every existing brief) gets
byte-identical behavior: same prompt, same generation inputs, same artifacts.

**Why this priority**: The single-reference flow is the shipped, eye-gate-proven path (011/012
both validated on it). A feature that perturbs it while adding a new input would trade a working
tool for a promise.

**Independent Test**: Assemble the prompt and the generation input list for a brief with no
product references; confirm both are byte-identical to the pre-feature output.

**Acceptance Scenarios**:

1. **Given** a brief with only a style reference, **When** the prompt is assembled, **Then** it
   is byte-identical to the pre-feature prompt (no empty product section, no new wording).
2. **Given** the same brief, **When** generation is invoked, **Then** the input-image list is
   exactly what it is today (style reference + logo).

### User Story 3 - The form captures roles without confusing the old flow (Priority: P2)

A designer sees two clearly labeled upload controls: the existing one now named as the style
reference (how the asset should FEEL), and a new optional multi-file control for product shots
(what must appear IN it). Uploading products is optional; the form works exactly as before when
the new control is left empty.

**Why this priority**: The input gate must make the role split legible to a non-designer, but the
UI is a capture surface for US1; it delivers no value without the threading behind it.

**Independent Test**: Confirm the served form labels the existing upload as the style reference,
offers an optional multi-file product-shots control, and submits runs successfully with zero,
one, or several product files; uploaded product files land in the run folder alongside the
existing reference.

**Acceptance Scenarios**:

1. **Given** the live-runner page, **When** it is served, **Then** the existing reference control
   is labeled as the style reference and a separate optional multi-file product-shots control
   exists, each with a one-line plain-language role description.
2. **Given** a submission with N product files (N >= 0), **When** the run starts, **Then** all N
   files are saved into the run folder and referenced by the brief, and N=0 submits exactly like
   today.

### Edge Cases

- **Product refs without a style reference**: the style reference stays REQUIRED (today's v1
  rule); the form continues to reject a submission without it. Product refs never substitute for
  the style reference.
- **Too many product images**: the generation service accepts a limited number of input images
  per call; the tool enforces a documented cap at the input gate (form + brief validation) and
  tells the user, rather than silently dropping files (honest null).
- **Duplicate or non-image files**: rejected at upload with the existing upload-validation
  behavior (same rules as the current reference upload).
- **A product photo with busy background**: passed through verbatim; the tool does not crop,
  segment, or model-analyze product shots (out of scope; the prompt instructs the generator to
  carry the product, not the photo's background).
- **Legacy briefs / CLI inputs with no product field**: run unchanged (absent list = today's
  path, byte-identical).
- **Product images contain visible text** (labels, printed logos): that is the point; the
  fidelity instruction covers carrying them; the only-the-headline text guard continues to
  govern GENERATED text, not text depicted inside supplied products.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The brief MUST support an ordered list of zero or more product reference images,
  distinct from the single style reference; the style reference remains required and keeps its
  current semantics (calibration magnitude, relationship dial, style exemplar).
- **FR-002**: All supplied product references (up to the documented cap) MUST be delivered to
  the generation step as additional input images in the single existing generation call (no
  extra paid calls).
- **FR-003**: When product references are present, the generation prompt MUST include a
  product-fidelity section instructing that the supplied product images are the brand's real
  products and must be carried into the composition faithfully (same products, same printed
  branding), not regenerated as generic stand-ins.
- **FR-004**: When no product references are supplied, the assembled prompt AND the generation
  input list MUST be byte-identical to the pre-feature behavior.
- **FR-005**: Product references MUST NOT feed the register/calibration step: magnitude and
  register derive from the style reference and brief exactly as today.
- **FR-006**: The run manifest MUST record the product references (files and role) for every
  run that uses them.
- **FR-007**: The form MUST label the existing upload as the style reference and provide a
  separate, optional, multi-file product-shots control with plain-language role descriptions;
  a submission with zero product files MUST behave exactly like today's form.
- **FR-008**: Uploaded product files MUST be stored in the run folder through the same shared
  upload path as the existing reference, subject to the same validation, plus a documented cap
  on count; exceeding the cap is reported to the user, never silently truncated.
- **FR-009**: The brief-to-generation threading MUST hold on BOTH the planned and the executed
  path (the plan/execution drift class caught twice before must be structurally tested on the
  executed path).
- **FR-010**: The change MUST be confined to the reference-capture and generation-feed path on
  the thin route (form, upload handling, brief, conductor threading, thin prompt + generation
  inputs); the register engine, calibration, and kit/legacy routes MUST NOT change behavior.
- **FR-011**: All new user-facing text MUST contain no em-dashes.

### Key Entities

- **Style reference**: the single required reference image; sets style magnitude and serves as
  the visual exemplar; unchanged semantics.
- **Product reference**: a new, optional, repeatable input: a photo of the brand's actual
  product; content-HARD brand truth carried into the composition; never used for calibration.
- **Product-fidelity instruction**: the prompt section that binds the supplied product images to
  the composition (carry these exact products, keep their printed branding).
- **Reference role**: the tag (style | product) that determines which pipeline consumers see an
  image; the existing single-reference flow is the style role.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a brief with N product references (1 <= N <= cap), the generation call
  receives exactly N product images plus the style reference and logo, and the prompt carries
  the product-fidelity section, in 100% of runs (deterministic).
- **SC-002**: For a brief with zero product references, the assembled prompt and the generation
  input list are byte-identical to pre-feature output in 100% of runs.
- **SC-003**: The register/calibration inputs are identical with and without product references
  in 100% of runs (product images provably never reach that step).
- **SC-004**: Every run using product references lists them in its manifest (100% auditable).
- **SC-005**: All existing self-test suites pass unchanged; the form accepts 0..cap product
  files and rejects over-cap with a visible message.
- **SC-006** (deferred, human eye-gate): One paid rerun of the CJXQ watermelon brief WITH the
  branded cup shots supplied as product references, judged by the human eye: the composition
  carries the actual branded cups (printed 茶救星球 JO'S CHA visible) rather than generic
  look-alikes, while the style/scene quality of the 012 run is retained.

## Assumptions

- The generation service already accepts multiple input images in one call (the tool ships two
  today: reference + logo), so adding product images extends a proven mechanism at zero extra
  generation cost; the per-call image cap is the service's documented limit, and the tool's cap
  is set to fit within it (logo + style + products).
- Product references are passed through verbatim: no cropping, segmentation, or model-based
  analysis of product shots (explicitly out of scope; a future feature may add it).
- The style reference remains REQUIRED on the form (the v1 rule); relaxing it is a separate
  decision, not this feature.
- "Product" covers any must-appear-faithfully object supplied as a photo (a cup, a package, a
  dish); the tool does not need to know what kind of object it is.
- The kit and legacy routes never see product references; their briefs simply lack the field.
- The fidelity instruction is a prompt contract, so pixel obedience remains probabilistic; the
  claim this feature makes structurally is that the product truth is SUPPLIED, and SC-006's
  eye-gate judges whether supplying it wins in practice (the same honesty split as 012's scene
  section).
