# Feature Specification: 023-edit-mode

**Feature Branch**: `023-edit-mode` (work happens on master per repo convention)

**Created**: 2026-07-20

**Status**: Draft (written from Richard's 2026-07-17 group ask + the operator's brand-DB
review 2026-07-20; the operator folded the brand-palette story in deliberately)

**Input**: User description: "023 edit mode (改图): edit an existing image on instruction
(Richard's @Alec integration ask, Yibo's 蒙自源 bowl swap as the driving case), plus
brand-palette add/delete/modify on the 品牌管理 page (folded in by the operator
2026-07-20), plus the empty-messages loud guard promised to the team."

## Context (verified against the code and the live deployment 2026-07-20)

Three converging facts drive this feature:

- **The team asked for it.** Richard, 2026-07-17, in the alignment group: "其实一博这个
  替换的需求也有现成的工具可以调用，@Alec 你看看能不能集成进我们的工具里吧。" The "existing
  callable tool" is literally our own generation API: `gpt-image-2`'s edit endpoint is
  what `harness/generate.py` already calls; what is missing is a MODE, not a capability.
  The team-alignment precondition the operator set for this feature is met (Richard chose
  Route A and explicitly requested the integration).
- **The driving case is real.** Yibo's 蒙自源 job (2026-07-17): a finished poster where ONE
  bowl must be swapped for the client's real product. He tried our tool, was blocked by
  `ERROR: sign 's1' has no messages.` (an edit job has no message lines), and fell back to
  ChatGPT, which did the swap but redrew the whole canvas and mangled the
  寻味山野原本天然 slogan. The same empty-messages error also appears in the deployment's
  visible history (`run_aia_20260714_174116`). Two lessons: (a) the blocker is our form
  assuming every job is a from-scratch design with text; (b) full-canvas redraw is the
  competitor's weakness — preserving untouched pixels is our differentiator.
- **The brand DB is writable but not growable from the page.** The live 蒙自源 brand
  (id `1234`) has ONE color because it was renamed into existence via the 019 manage page,
  never onboarded from a VI manual. `brand_manager.update_brand` already accepts a full
  replacement colors list through `validate_lean_key` (add/delete/modify all legal
  server-side), but `manage.html` renders only hex+role controls for EXISTING colors — no
  add or remove. Worse, the page's save payload omits the per-color names, and
  `update_brand` fills them with empty strings: any color edit silently WIPES the
  extracted 天空蓝/Sky Blue-class names (a real data-loss wart, observed in the code
  2026-07-20).

## Deferred (named, so nobody expects them)

- **Patch-based high-resolution compositing** (edit a crop at print resolution, composite
  back into the client's original untouched file — the true high-to-low answer): deferred.
  It is the natural v2 of this mode and the reason the mask geometry is recorded in the
  run dir, but v1 edits at the model's native canvas.
- **Upscaling / low-to-high integration** (Richard's "现成成图工具可以把低质量图片转高质量并
  分层"): deferred; Richard himself deferred it in the group ("这个以后讨论").
- **auto_layer / template-tool integration** (Kevin's tool): a separate conversation with
  Kevin first; nothing here builds toward or against it.
- **Auto-derived masks** (model finds the region from the instruction): deferred. v1 masks
  are human-drawn rectangles — the human is the region-picker, which is exactly the input
  gate the charter wants.
- **Brand-level product library**: stays deferred as recorded 2026-07-08.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The edit run (改图): change THIS image as instructed (Priority: P1)

The designer picks 改图 on the run form, uploads the image to change (the "base image"),
writes a verbatim instruction in Chinese ("把左下角的牛肉粉换成这张实拍图里的酸汤粉"),
optionally attaches product photos (the 013 lanes, reused), and runs. The free derive leg
composes an edit plan (no register, no calibration, no message authoring); the 015 gate
shows the instruction verbatim + the spend before any money moves; confirm is the one
spend; the deliverable is the edited image.

**Why this priority**: it is the team's explicit ask, it unblocks a real client job class
(swap/retouch on finished art), and it converts the tool from "new designs only" to "the
place you bring an image back to".

**Independent Test**: drive a run dir through the edit derive leg (free) and verify by
value: inputs.json carries mode=edit + the base image + the verbatim instruction; the
composed edit prompt contains the instruction verbatim and NO invented message/scene
content; the gate payload states the call count and cost; a 新设计 run's inputs.json and
prompt stay byte-identical to pre-023.

**Acceptance Scenarios**:

1. **Given** the form in 改图 mode with a base image and instruction, **When** the
   designer starts the run, **Then** the free derive leg produces a plan whose prompt
   carries the instruction VERBATIM, and the 015 gate stops the run before any paid call.
2. **Given** the same run, **When** the designer confirms, **Then** exactly the stated
   number of paid calls run and the deliverable is an edited image at the base image's
   aspect (existing size machinery, fed from the base image's dimensions).
3. **Given** 改图 mode with no base image, or a blank instruction, **When** the designer
   tries to start, **Then** the form refuses loudly in Chinese client-side (no launch).
4. **Given** an untouched form (新设计 default), **When** a run starts, **Then** its
   inputs.json is byte-identical to a pre-023 run for the same fields (THE pin).
5. **Given** 新设计 mode with zero message lines, **When** the designer tries to start,
   **Then** the form refuses loudly in Chinese naming the field ("画面上的文字还没填" class),
   BEFORE any POST — the promised fix for the twice-observed `sign 's1' has no messages`
   dead end. (In 改图 mode, zero messages is legal and normal.)

---

### User Story 2 - Region-scoped edit: untouched pixels stay untouched (Priority: P2)

On the uploaded base image, the designer drags a rectangle over the region to change
("this bowl"). Generation is instructed to alter ONLY that region; everything outside is
preserved. This is the anti-ChatGPT property: their full-canvas redraw mangled the
slogan; our edit must be able to promise "the slogan cannot change, it is outside the
box".

**Why this priority**: it is the differentiator, but US1 without it already unblocks the
job class (full-canvas edit with a preservation instruction), so it ships second.

**Independent Test**: free, by value: the drawn rectangle round-trips form → inputs.json
as normalized coordinates; the derived plan records the mask geometry; the preservation
instruction names the region. The pixel-identity property itself is measured on the paid
eye-gate run (SC-003) — a computed diff, not a judgment call.

**Acceptance Scenarios**:

1. **Given** a base image and a drawn rectangle, **When** the run derives, **Then**
   inputs.json carries the region as normalized coordinates and the gate shows that a
   region is set.
2. **Given** a confirmed region edit, **When** the deliverable lands, **Then** the pixels
   outside the region match the base image within a stated numeric threshold, measured by
   the run's own artifacts (an auditable diff stat recorded in the run dir, honest-null
   if the mechanism cannot guarantee it — never a silent full redraw presented as a
   region edit).
3. **Given** no rectangle drawn in 改图 mode, **When** the run derives, **Then** the edit
   is full-canvas with the preservation instruction, and the gate says so (region edits
   are opt-in; the absence of a region is stated, not defaulted silently).

---

### User Story 3 - The brand palette is manageable from the page (Priority: P2)

On 品牌管理, the designer adds colors to a brand, removes wrong ones, edits hex and role,
and names each color — growing 蒙自源's one-green skeleton into its real palette without a
VI manual PDF. Saving never silently destroys data that onboarding extracted.

**Why this priority**: the live deployment's only brand has a one-color palette that the
page cannot grow; the role-guidance engine (008) is starved of the data it was built to
use. Server-side support already exists; this is UI + one data-preservation fix.

**Independent Test**: free, hermetic (the existing test_brand_manager tmp-workspace
pattern): add/remove/modify through the update payload and verify the written key by
value; verify a payload carrying names round-trips them; verify the page renders add and
remove controls and name inputs.

**Acceptance Scenarios**:

1. **Given** a brand with one color, **When** the designer adds a second color with hex,
   role, and a Chinese name, and saves, **Then** the key on disk carries both colors with
   names intact, validated by the existing exactly-one-primary rule.
2. **Given** a brand whose colors carry extracted names (CJXQ-class), **When** the
   designer edits one color's ROLE only and saves, **Then** every name survives on disk
   (the wipe wart is dead, proven by value).
3. **Given** a delete that would remove the last primary, **When** the designer saves,
   **Then** the existing validation refuses loudly and the key file is byte-identical
   (already the 019 contract; the new controls must not bypass it).

---

### Edge Cases

- **Edit of an edit**: v1 supports it by re-uploading the previous deliverable as the new
  run's base image (run dirs stay immutable; no in-place chains). A one-line note near
  the mode control says so.
- **Layered export on edit runs**: the 016 exporter enumerates message lines, which edit
  runs do not have; export on an edit run refuses with the existing loud refusal. Stated,
  not worked around, in v1.
- **Product photos in edit mode**: legal and expected (the bowl swap needs the real bowl
  shot); the 013 cap and fidelity language apply unchanged.
- **Style reference in edit mode**: none. The base image IS the style authority;
  calibration and the register engine are skipped entirely (their subfields are not even
  derived), which also makes the edit derive leg cheaper and faster than the design leg.
- **W/H fields in edit mode**: hidden; output aspect follows the base image (the 022
  fields keep governing 新设计 only).
- **Tiny or degenerate rectangles** (a few px, or zero-area from a stray click): refused
  client-side with a loud Chinese message (a region that small cannot carry an edit).
- **The mask mechanism is unavailable** (the API rejects masks for this model, or the
  provider relay strips them): US2 falls back to full-canvas with the preservation
  instruction and RECORDS the fallback in the run dir + gate copy (honest null, the
  charter rule). US1 remains fully shippable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The run form MUST offer a job-mode control (新设计 / 改图) defaulting to
  新设计; an untouched form MUST produce inputs.json byte-identical to pre-023 (THE pin).
- **FR-002**: 改图 mode MUST take a required base-image upload and a required verbatim
  instruction; blank either MUST refuse loudly client-side in Chinese before any POST.
- **FR-003**: The edit derive leg MUST be free and MUST skip register derivation,
  calibration, and message/scene authoring; the composed edit prompt MUST carry the
  instruction verbatim plus a preservation preamble, and MUST NOT contain invented
  message text or scene content.
- **FR-004**: Edit runs MUST stop at the 015 gate exactly like design runs: plan + spend
  stated free, confirm is the only spending route, idempotent, drift-verified.
- **FR-005**: In 新设计 mode, zero message lines MUST refuse loudly client-side in Chinese
  (the empty-messages guard); in 改图 mode zero messages MUST be legal. The server-side
  English error stays for CLI callers.
- **FR-006**: The deliverable of an edit run MUST land in the standard run-dir layout so
  the existing stages view, image route, and judge/nudge loop work unchanged; the nudge
  loop re-derives free per the existing contract.
- **FR-007** (US2): The form MUST let the designer draw ONE rectangle on the base image;
  the region MUST ride in inputs.json as normalized coordinates; the gate MUST state
  region-set vs full-canvas.
- **FR-008** (US2): A region edit MUST preserve outside-region pixels by construction
  where the mechanism supports it, and MUST record an auditable outside-region diff stat
  in the run dir; if the mechanism cannot guarantee preservation, the run MUST record the
  fallback explicitly (never a silent full redraw labeled as a region edit).
- **FR-009** (US3): 品牌管理 MUST offer add-color and remove-color controls and per-color
  name inputs (CN/EN) alongside the existing hex + role; all writes keep flowing through
  the existing validate-on-copy gate (refusals leave the file byte-identical).
- **FR-010** (US3): Color updates MUST round-trip names: a payload carrying names writes
  them; the page always sends what it renders. The current silent name-wipe MUST be dead,
  proven by a by-value test.
- **FR-011**: All existing suites MUST stay green; any pinned grep that names a changed
  form surface moves WITH the change, dated in place, never weakened. Kit/legacy paths,
  the register engine, calibration, and 新设计 behavior stay byte-identical throughout.

### Key Entities

- **Job mode**: 新设计 (today's flow, unchanged) vs 改图 (this feature) — one field in
  inputs.json, absent = 新设计 (which is what makes the pin hold for legacy briefs).
- **Base image**: the uploaded image an edit run operates on; saved in the run dir like
  the 007 reference; the size authority for edit output.
- **Edit instruction**: the designer's verbatim change request; the only text the edit
  prompt is built from.
- **Region**: one normalized rectangle (optional); the human-drawn boundary between
  "change this" and "do not touch".
- **Brand color entry**: {hex, role, name_cn, name_en} — already the key schema; US3 makes
  the page speak the whole entry instead of a lossy subset.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A 新设计 run from an untouched form produces inputs.json byte-identical to
  pre-023, and the full existing sweep passes — proven free, by value.
- **SC-002**: The Yibo case runs end to end: base poster + real product photo + a
  swap instruction derives free, gates, and (on confirm) delivers an edited image — the
  paid eye-gate, judged by the operator against the question "is the swap done AND is the
  rest of the poster intact?" (the 蒙自源 bowl swap, or a faithful reconstruction of it).
- **SC-003**: On a region edit, the recorded outside-region diff stat is within the
  stated threshold (numeric, computed from artifacts on disk, no human judgment) — or the
  run explicitly records the fallback. Either way, nothing silent.
- **SC-004**: A designer starting a 新设计 run with no message lines gets a loud Chinese
  refusal naming the field, before any run dir exists — the `sign 's1' has no messages`
  dead end is unreachable from the form.
- **SC-005**: Through the page alone, 蒙自源 grows from one color to its real palette with
  named, role-tagged colors, and a subsequent CJXQ-class edit preserves every extracted
  name on disk — proven free, by value, in the hermetic suite.

## Assumptions

- The edit endpoint accepts our existing call shape with a base image and (US2) a mask;
  verified as a plan-phase probe BEFORE any US2 build (one cheap real call, operator-run).
  If masks are unsupported, US2's fallback contract (FR-008) applies and the
  differentiator moves to the patch-compositing v2.
- Per-call cost matches the existing generation cost constant; the gate reuses it.
- The edit instruction is passed through verbatim (the 012 lossless-brief principle);
  translation, expansion, or "prompt improvement" of the designer's words is out of
  scope and unwanted.
- Human-drawn rectangles are sufficient region input for v1 (the human IS the taste
  gate); finer shapes (lasso, multi-region) wait for real demand.
- The brand-palette story deliberately rides in this spec (operator decision 2026-07-20)
  even though it touches a different surface: both stories are "the team's real usage
  hit a wall this week" items, and shipping them together is one deploy + one comms
  message to the team.
