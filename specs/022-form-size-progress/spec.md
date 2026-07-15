# Feature Specification: 022-form-size-progress

**Feature Branch**: `022-form-size-progress` (work happens on master per repo convention)

**Created**: 2026-07-15

**Status**: Draft (written from Richard's designer's preliminary feedback, 公司宣传H5.zip,
items 问题04/05/06; operator-triaged 2026-07-15: 04-06 in scope, 01/02/03 deferred below)

**Input**: User description: "022 form size + progress expectations: px size units,
separate W/H inputs, generation duration expectations (items 4-6 of Richard's designer
feedback; defer long-image/template 01/02 and font-selection 03 pending clarification)"

## Context (verified against the code 2026-07-15)

The feedback comes from a working designer at Richard's agency driving real client work
(the AIA NAVI monthly package) through the tool. Three of their six comments are actionable
now:

- **问题04**: size unit is cm only; online materials are specced in px.
- **问题05**: width and height should be two separate inputs (their screenshot shows a
  design-tool W/H field pair).
- **问题06**: generation feels slow with no expectation set ("提示用户大约需要xx秒").

Ground truth: `harness/format_size.resolve_size` is already unit-AGNOSTIC — it extracts
two numbers and uses only their RATIO (aspect-preserving map to the nearest valid
gpt-image-2 size around ~1.57 MP), so `750x300px` parses correctly TODAY. The cm-only
impression comes from the FORM: one free-text field labeled `尺寸（如 60x40cm，中文单位也可以：
６０×４０厘米）`. The fix is therefore mostly form truth (structured inputs + honest labels),
not pipeline change. The UI already polls `/run/<id>/stages` every second (`poll()` in
`frontend/index.html`), so the waits have a natural place to render elapsed time.

## Deferred (named, so nobody expects them — the operator's triage)

- **问题01 (long-image/H5 projects)** and **问题02 (.ai template re-theming + multi-size
  banner sets)**: deliberately OUT OF SCOPE. They describe compositional production work
  (assemble a ~14,000px page from structured inputs; re-theme one KV into N sizes), not
  better single-image generation; gpt-image-2 cannot emit such images (max edge 3840).
  Revisit as their own feature discussion, likely on top of the 016 layers/composite
  machinery, only if the product decides to go there.
- **问题03 (font selection)**: deferred pending clarification. The question sent back
  through Kevin: 字体选择是指大概的字体风格（如圆体/黑体），还是必须用指定的字体文件精确呈现？
  主要用在哪些文字上？ Style-preference = a form nudge (cheap, probabilistic); exact
  licensed fonts = the composite_text moat (real work). Do not build either until answered.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured size input with real units (Priority: P1)

The designer specifies the deliverable's size as two separate numbers (width, height) plus
a unit (cm or px), exactly like the W/H fields in the design tools they use daily. An
online banner specced as 750×300px is entered as `750` / `300` / `px` and the run derives
at the matching aspect; today's print flow (`60` / `40` / `cm`) works unchanged.

**Why this priority**: it answers two of the three comments (04+05) with one change, and
it removes a real mis-signal — the current label actively tells users px is unsupported
when the engine already handles it.

**Independent Test**: fill the form with W/H/unit combinations and verify (free, no paid
call) that the composed brief string and the resolved aspect are correct by value; verify
the canonical cm case composes the exact pre-022 string.

**Acceptance Scenarios**:

1. **Given** the run form, **When** the designer enters W=750, H=300, unit=px and starts a
   run, **Then** the brief carries `750x300px` and the derived plan's resolved size has
   aspect 2.5 (aspect-preserving, NOT necessarily 750×300 exactly).
2. **Given** the run form's defaults, **When** the designer submits without touching the
   size fields, **Then** the brief carries exactly `60x40cm` — byte-identical to a pre-022
   run's inputs.json for the same form.
3. **Given** W=100, H=1400, unit=px (aspect beyond 1:3), **When** the run derives, **Then**
   the existing honest clamp fires and the 015 pre-spend gate shows its size row (the
   designer sees the clamp BEFORE any spend).
4. **Given** a blank or zero W or H, **When** the designer tries to start, **Then** the
   form refuses loudly client-side (no run launched with silently-defaulted size).

---

### User Story 2 - The wait has stated expectations (Priority: P2)

While the free derivation runs, and again while the paid generation runs, the designer
sees how long they have been waiting and what a typical wait is ("免费推导中，已等待 42 秒，
通常约 1 分钟"). No frozen screens, no fake progress bars.

**Why this priority**: 问题06 verbatim. It is pure expectation management: the actual
durations do not change, but an anchored wait reads as "working" instead of "broken",
which is what the designer was reporting.

**Independent Test**: drive the stages view against a run dir mid-derive (free) and
verify the elapsed counter ticks and the expectation copy is present for both wait kinds;
verify a finished run shows neither.

**Acceptance Scenarios**:

1. **Given** a run just started (derive leg), **When** the designer watches the stages
   panel, **Then** an elapsed-seconds counter is visible and ticking alongside copy
   stating the typical derive duration.
2. **Given** a confirmed run (paid generation in flight), **When** the designer watches,
   **Then** the same counter pattern shows with the generation's typical duration.
3. **Given** the run finishes (image present) or fails (error surfaced), **When** the
   panel updates, **Then** the counter and expectation copy disappear (never a stale
   timer over a finished run).
4. **Given** any wait, **Then** no percentage or progress bar is shown anywhere (we
   cannot measure real progress; showing one would be an invented result).

---

### Edge Cases

- Decimal sizes (`2.5` cm) are legal today (the parser accepts decimals) and must stay
  legal through the numeric fields.
- Swapped orientation (H > W) is just portrait; no special handling, no warning.
- Changing the unit select does NOT rescale the numbers (px and cm only feed aspect; a
  unit flip on 60/40 means "60x40px", same aspect, same resolution result).
- Legacy briefs: inputs.json written by hand or by the CLI keeps the free-text
  `format_size` field working unchanged (the field's CONTRACT is a string; only the
  form's way of composing it changes).
- Resume paths (017 URL-hash resume, the recent-runs picker): a client reopening a
  mid-flight run did not observe its start, so the counter starts from the moment THIS
  client began observing the wait. An understated elapsed time is accepted honest
  behavior (we display what we measured, never a reconstructed guess); pre-022 and
  finished runs render exactly as today, with no counter.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The run form MUST present the size as two numeric inputs (width, height)
  plus a unit selector offering at least `cm` and `px`, prefilled with today's default
  (60 / 40 / cm) so the untouched-form brief is unchanged.
- **FR-002**: The form MUST compose the canonical brief string `"<W>x<H><unit>"` from the
  three controls; for identical inputs the composed inputs.json MUST be byte-identical to
  pre-022 (THE compatibility pin — downstream parsing, the 015 size-assumption gate row,
  and the CLI contract are untouched).
- **FR-003**: px sizes MUST resolve through the existing aspect-preserving math, proven by
  a pinned value test (e.g. `750x300px` resolves to aspect 2.5 within the existing delta
  bounds); `像素` MUST normalize like the existing `厘米`-class units (identity on ASCII
  input, pinned).
- **FR-004**: Blank, zero, or non-numeric W/H MUST refuse loudly at the form (no launch);
  the server-side honest default for unparseable strings stays as-is for non-form callers.
- **FR-005**: The form MUST state, adjacent to the size fields, that output is an
  aspect-preserving DRAFT at roughly 1.5 megapixels — not an exact-pixel or print-ready
  file (the draft charter, stated where the px expectation is set).
- **FR-006**: During the free derive wait, the paid generation wait, AND the layered-
  export wait (016 — the longest wait the app has, with its own poller), the stages panel
  MUST show a ticking elapsed-time counter plus static copy stating the typical duration
  for that wait kind (all three from the ONE constants map).
- **FR-007**: The typical-duration copy MUST come from observed real-run timings (stated
  as approximate ranges), MUST be maintained as named constants in one place, and MUST
  never render as a percentage/progress bar (honest nulls: we cannot measure progress).
- **FR-008**: The counter and expectation copy MUST clear when the wait ends (image
  present, gate reached, or error surfaced) and MUST NOT appear on finished/pre-022 runs.
- **FR-009**: All existing suites MUST stay green; any pinned form-grep that names the
  old single size field moves WITH the change, dated in place, never weakened.

### Key Entities

- **Size brief string** (`format_size`): the canonical `"<W>x<H><unit>"` string riding in
  inputs.json — the unchanged contract between the form and `resolve_size`.
- **Wait expectation**: a (wait kind → typical duration copy) mapping, the one place the
  stated expectations live.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A designer can spec an online banner in px (e.g. 750×300) using separate
  W/H fields, and the derived plan's aspect matches the request within the existing
  resolve_size delta bounds (delta 0.0 for the 750×300 exemplar, verified 2026-07-15) —
  verified free, by value, without a paid call.
- **SC-002**: An untouched form composes a brief byte-identical to pre-022. Proof method
  (the compose runs in browser JS, outside the Python tests): a value-bearing pin on the
  form's compose expression and its default values in the automated suite, plus the T005
  human gate observing the real composed inputs.json on disk.
- **SC-003**: Every wait the app has (derive, generation, layered export) that runs
  longer than a few seconds shows elapsed time + a stated typical duration; a designer
  watching a normal run never sees a frozen, unannotated screen (the 问题06 complaint,
  directly).
- **SC-004**: The full test sweep passes; the one human gate is a single FREE derive
  driven through the new fields with the operator judging the form flow and the gate's
  size row (no paid eye-gate: no pixel-affecting change beyond what 015 already surfaces).

## Assumptions

- Static, observed typical-duration ranges are acceptable for v1 (per-run prediction from
  history is out of scope; the ranges are copy, maintained as constants, not computed).
- `cm` stays the default unit: the primary proven flow (手举牌 print drafts) is cm-based,
  and defaults must keep the untouched form byte-identical.
- px inputs promise ASPECT fidelity only, per the draft charter; exact-pixel export is a
  designer finishing step (or a future feature), and FR-005 states this where the user
  forms the expectation.
- The unit selector offers cm and px only; mm/英寸 remain reachable through the CLI's
  free-text field (the parser already normalizes them) but are not form options until
  someone asks.
- Items 问题01/02/03 stay deferred exactly as recorded in the Deferred section; nothing
  in this feature builds toward them.
