# Feature Specification: Layered Export (per-element layers.zip)

**Feature Branch**: `016-layered-export`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Layered export. After a browser run's final image is generated and
the operator has eye-judged it, an OPT-IN Export layers button on the run view produces a layered
decomposition of the approved design: one paid gpt-image-2 edit call per design element repaints
ONLY that element on the proven chroma green #00B140, the existing strip_chroma keying converts
each to a true RGBA PNG layer, plus ONE background call (the scene repainted with the foreground
elements removed), all packaged as layers.zip in the run dir with white-background JPG previews
(Richard's ask: 在选定画面的最后一步增加分层输出文件, 把画面的每个设计元素分层, 输出一个zip包文件)."

## Why this feature (context that binds the design)

The tool's charter is a handoff-quality DRAFT a human finishes. Today the handoff is ONE flat
image; the finishing human (Handyprint's designer) must manually re-separate text, logo, and
products in an editor before they can adjust anything. A layered decomposition makes the draft
actually finishable: each design element arrives as its own transparent layer that can be moved,
recolored, or replaced.

**The load-bearing constraint:** gpt-image-2 CANNOT output layered files or transparent
backgrounds natively (the API emits only flat PNG/JPEG/WebP; the transparency option that existed
in gpt-image-1.5 was removed). "Native autolayer" is not available. Layers must therefore be
BUILT: one edit call per element repaints only that element on the tool's proven chroma green
(#00B140, the same key the die-cut path already uses), and the existing deterministic keying
converts green to alpha. This is model output keyed by model-free code, consistent with the
tool's existing chroma machinery, and every layer's quality is measurable and honestly nullable.

Richard's literal ask names JPGs; JPG has no alpha channel, so JPG-only layers could not be
recomposited. The deliverable therefore carries BOTH: the true RGBA PNG layer (the compositable
artifact) and a white-background JPG preview per layer (the literal ask, and the operator's
quick-look surface).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export a judged run as layers (Priority: P1)

The operator has run a brief through the browser, confirmed the pre-spend gate, and eye-judged
the generated image as good. They click "Export layers" on the run view. The tool derives the
layer list from the run's own plan (each verbatim message line, the brand logo if it was actually
fed to generation, each supplied product photo), repaints each element in isolation on chroma
green, keys each to a transparent layer, repaints the background with the elements removed, and
packages everything as layers.zip in the run directory with a download link. The finishing human
opens the zip in an image editor and has the draft as movable pieces.

**Why this priority**: This IS the feature: it converts the flat deliverable into a finishable
one. Everything else guards how it spends and how honestly it reports.

**Independent Test**: With generation stubbed (free), exporting a fixture run yields exactly the
expected zip members (one RGBA PNG + one JPG preview per element, background pair, manifest) and
exactly N+1 generation calls with the right prompts and reference lists. The pixel truth is
judged only by the human eye-gate (SC-007).

**Acceptance Scenarios**:

1. **Given** a run with 3 message lines, a fed logo, and 1 product photo, **When** the operator
   exports, **Then** exactly 6 generation calls occur (5 elements + 1 background) and layers.zip
   contains 5 layer PNGs, 5 layer previews, the background pair, and the manifest.
2. **Given** a run whose logo was NOT fed to generation (logo_treatment omit), **When** the
   operator exports, **Then** no logo layer is planned, called, or shipped.
3. **Given** an element isolation whose keying succeeds, **Then** its zip entry is a true RGBA
   PNG whose transparent region is the keyed green field, plus a white-background JPG preview.
4. **Given** a run directory produced before this feature, **When** the run view renders it,
   **Then** it renders exactly as before plus an honest "not exported" stage note.

---

### User Story 2 - The export spends only on an explicit, informed click (Priority: P2)

Export costs real money (about N+1 paid images). Before the click, the button states the exact
call count and cost, computed free. The click is the ONLY trigger: export never runs
automatically, never piggybacks on generation, and never re-spends. Repeat clicks (double-click,
impatient reload, second browser tab) do nothing after the first, even while the export is still
running. A crashed export may be retried explicitly, with the cost restated. A server restart
changes nothing: the export's state lives on disk.

**Why this priority**: The 015 gate established the contract "no browser spend without an
explicit confirmed click"; a paid exporter that violated it would undo that feature.

**Independent Test**: All free: the plan endpoint returns count and cost with zero generation
calls; state is on disk before the first (stubbed) call; a second invocation makes zero calls;
retry is accepted only from the failed state; export is refused while the run's gate is not done.

**Acceptance Scenarios**:

1. **Given** a judged run, **When** the operator views it, **Then** the export control shows the
   exact number of paid calls and the cost BEFORE any click, computed without spending.
2. **Given** an export in progress, **When** the operator clicks export again, **Then** no second
   export starts and no additional spend occurs, and the response says so.
3. **Given** an export that failed mid-flight, **When** the operator clicks export again, **Then**
   a fresh export is accepted (cost restated), because a crash must not brick the run's only
   export.
4. **Given** a run that has not passed the 015 confirm gate (no generated image yet), **When**
   export is requested, **Then** it is refused with a named reason and zero spend.
5. **Given** a server restart mid-export or post-export, **When** the run view reloads, **Then**
   the export stage renders correctly from disk.

---

### User Story 3 - Honest per-layer nulls and a full audit trail (Priority: P3)

The model may ignore the chroma directive (painting a full scene instead of one element on
green), return an empty frame, or leave a dirty key field. Deterministic thresholds on the
keying stats mark such a layer NULL: the zip then ships the raw model output for manual salvage
plus a manifest note naming the failure, and NEVER a fabricated cutout. The manifest records,
per layer, the prompt used, the keying statistics, the kept-content bounding box (so position
drift is measurable), and any null note; the background entry is flagged as a model-continued
scene, not ground truth.

**Why this priority**: Honest nulls are constitutional (principle V). A silently wrong layer is
worse than a named failure, and the manifest is what makes the paid export auditable.

**Independent Test**: Drive the REAL keying with synthetic images (free): a clean element on
flat #00B140 keys to a correct RGBA layer; a full-scene image (no green) and a near-empty green
frame each produce status null with the correct named note, a shipped raw image, and no cutout.

**Acceptance Scenarios**:

1. **Given** an isolation where keying keeps nearly the whole frame opaque, **Then** the layer is
   null ("model ignored the chroma directive"), the raw output ships, no cutout ships.
2. **Given** an isolation where keying keeps almost nothing, **Then** the layer is null ("empty
   frame") with the same honest packaging.
3. **Given** a successful layer, **Then** its manifest entry carries the prompt, the keying
   stats (including dropped stray components and green residual), and the opaque bounding box.
4. **Given** any export, **Then** the manifest's background entry is flagged as model-continued
   scene (content behind removed elements is plausible, not recovered truth).

---

### Edge Cases

- A run with zero enumerable elements (no messages, no fed logo, no products) refuses to plan an
  export, loudly: an export of only a background is a paid no-op and is never offered.
- The source image is missing (no generated.png/final.png): the plan surface and the CLI refuse
  with a named reason, zero spend.
- An element that is itself green (near #00B140) cannot be keyed; the isolation prompt forbids
  key-colored elements, and the null thresholds catch non-compliance (dirty key field note).
- Detached marks in one element (a multi-glyph text line, a logo with separate symbols): the
  keying's largest-component behavior may drop pieces; when the dropped pixels OUTNUMBER the
  kept pixels the layer is an honest null (the raw output ships for salvage, per FR-005);
  a minority drop stays visible via the dropped-pixels stat in the manifest. The keying itself
  is unchanged in v1 (the die-cut path stays byte-identical); a keep-all-components option is
  a possible v2.
- Every isolation call fails or nulls: the export completes honestly (state done, zip with raw
  images + notes); the operator judges whether anything is salvageable. Money spent is recorded
  either way.
- Two runs exporting concurrently: each export writes only inside its own run directory; the
  server serializes launches the same way it serializes generations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST enumerate design elements DETERMINISTICALLY from the run's own
  artifacts, never by model guessing: one element per verbatim message line, one logo element
  only if the logo file was actually part of the run's generation references, one element per
  supplied product image. The background is the +1 call, not an element.
- **FR-002**: Each element isolation MUST be one edit call whose prompt demands: exactly that
  one element, reproduced at its position, size, colors, and styling from the approved image,
  on a perfectly flat backdrop of pure #00B140, with nothing else on the green, at the run's
  exact generation canvas size. Logo and product isolations MUST pass the original asset as an
  additional reference to disambiguate the element.
- **FR-003**: The background MUST be one edit call repainting the approved image with all
  enumerated elements removed and the scene continued behind them, delivered as an unkeyed
  full-bleed image plus a JPG preview, flagged in the manifest as model-continued scene.
- **FR-004**: Keying MUST reuse the existing proven chroma machinery unchanged; each successful
  layer ships as a true RGBA PNG plus a white-background JPG preview.
- **FR-005**: Deterministic thresholds on the keying statistics MUST mark a layer null (kept
  fraction too high = chroma directive ignored; too low = empty; green residual = dirty key
  field; dropped stray pixels outnumbering kept pixels = the largest-component keep erased
  the majority of a multi-part element). A null layer MUST ship the raw model output plus a
  manifest note naming the failure, and MUST NOT ship a fabricated cutout.
- **FR-006**: The export MUST produce layers.zip in the run directory containing exactly: the
  manifest, the background pair, and per element either (cutout PNG + preview JPG) or (raw PNG +
  null note in the manifest). The manifest MUST record per layer: the element identity, the
  prompt, the keying statistics, the opaque bounding box, and any null note.
- **FR-007**: Export MUST follow the 015 pre-spend contract: a free plan surface states the
  exact call count and cost BEFORE any click; export state is written to disk BEFORE the first
  paid call; repeat requests no-op with no second spend while a live worker owns the state;
  retry is accepted from the failed state AND from verifiably-stuck exporting states (a
  reservation no worker ever adopted, or a worker whose recorded process is dead): no crash,
  interrupt, or hard kill may ever brick a run's only export; export is refused unless the
  run's confirm gate reached done; a server restart re-renders the export stage purely from
  disk.
- **FR-008**: The run view MUST offer export as a labeled opt-in control (call count + cost),
  never automatic and never pre-selected, with per-layer progress (ok / null with note) and a
  download link when done. Failures surface in the UI, never silently.
- **FR-009**: Byte-identity for the untouched world: a run that never exports MUST be
  byte-identical everywhere (no new files, no changed prompts, no changed behavior on any
  existing path); run directories from before this feature MUST render as before plus only the
  honest not-exported stage.
- **FR-010**: The exporter MUST be independently invocable from the command line against any run
  directory, with a free plan-only mode that spends nothing, and MUST accept an injected
  generation function so every self-test runs free. No paid call may ever run inside a self-test.
- **FR-011**: A zero-element run MUST refuse to plan an export, loudly, at both the plan surface
  and the CLI (never a paid background-only export).

### Key Entities

- **Element**: one deterministically enumerated piece of the approved design (a message line, the
  fed logo, a product photo), with a stable id, a kind, and for logo/product the original asset
  reference.
- **Export plan**: the free pre-spend statement: the element list, the call count (elements + 1),
  the per-call and total cost, the source image, the canvas size.
- **Export state**: the on-disk lifecycle record (exporting / done / failed) written before the
  first paid call; the idempotency and restart-safety anchor.
- **Layer record** (manifest entry): element identity, prompt, keying statistics, opaque bounding
  box, status ok/null, note.
- **layers.zip**: the deliverable: manifest, background pair, per-layer artifacts as in FR-006.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a judged run, the operator reaches a downloaded layers.zip with exactly one
  informed click (plus the download), and the zip opens as individually editable pieces.
- **SC-002**: The exact number of paid calls and the cost are visible before the click, computed
  with zero spend (provable free).
- **SC-003**: N enumerated elements yield exactly N+1 paid calls, never more; repeated export
  requests after the first yield exactly zero additional calls (provable free with a stub).
- **SC-004**: Every zip member is accounted for: each layer is either a true transparent layer
  with its preview, or an explicitly null raw image named in the manifest. Zero fabricated
  layers, ever (provable free: synthetic chroma fixtures drive the real keying).
- **SC-005**: A run that never exports is byte-identical to today across every artifact and
  every existing test suite (provable free).
- **SC-006**: Pre-feature run directories render unchanged plus one honest stage line (provable
  free).
- **SC-007**: HUMAN EYE-GATE (the one paid step, never automated): on a real judged CJXQ run,
  the operator exports, stacks the layers over the background in an image editor, and judges:
  each layer reads as its element, position drift is acceptable for a draft decomposition, and
  every null is honest. The verdict is recorded in SYSTEM_MAP.

## Assumptions

- gpt-image-2 cannot emit layered or transparent output; per-element chroma repaint + local
  keying is the chosen route (verified against current API behavior, 2026-07).
- Position drift between a repainted element and the original is probabilistic and ACCEPTED for
  v1: the zip is a layered DRAFT decomposition per the tool's charter, not a pixel-exact
  separation. v1 measures (bounding boxes in the manifest) and lets the operator judge via the
  previews; silent auto-correction is out of scope.
- Layer granularity v1: one layer per message line (the finisher's editable unit, deterministic
  from the brief), revisable if the eye-gate shows per-line drift is too costly.
- The existing chroma keying is reused as-is, including its largest-component behavior; its
  stats make any dropped pieces visible. Changing the keying is out of scope for v1.
- Per-image cost is assumed at the same rate the 015 gate states for generation (one shared
  constant; if pricing changes, one place moves).
- The export writes only new files (export state, manifest, per-layer directories, layers.zip)
  inside the run directory; it never rewrites any artifact an earlier phase produced.
- Brand-key enrichment (the deferred product library) is unrelated; if it ships later, exports
  pick up its product elements automatically through FR-001 (products come from the run's
  inputs, wherever they were sourced from).
