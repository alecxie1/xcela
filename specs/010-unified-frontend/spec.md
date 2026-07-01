# Feature Specification: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

**Feature Branch**: `010-unified-frontend`

**Created**: 2026-06-30

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief (`specs/_inbox/010-unified-frontend.md`). The `frontend/` app is two separate
pages the designer must know by URL: `/` (live-runner) and `/onboard` (brand onboarding wizard). They are
already DATA-connected (a brand onboarded via `/onboard` appears in the live-runner `/brands` dropdown), and
`onboard.html` already links "back to live-runner," but the live-runner has NO link to onboarding, so it is
one-directional and reads as two disconnected tools. The designer wanted "one interface instead of 2 links."
This connects them: (A) symmetric nav so both pages cross-link into one app, and (C) a post-onboard HANDOFF
so after saving a brand the designer jumps straight into generating with it, plus a light UI touch-up so the
two pages look like one polished product.

> **Scope note (constitution §VII):** this is a PURE FRONTEND change to the two HTML files. No new server
> routes; the back-half, generation, register, and onboarding logic are untouched. The preselect is a
> client-side query-param read against the existing `/brands`.

> **Honesty note (constitution §II / §III):** the aesthetic and the flow are HUMAN-EYE judgments, not
> structural claims. Automated tests can only grep that the wiring exists (both nav links; the preselect
> code; the handoff link) - the weakest kind of gate - so the human eye is the real proof of "one app,
> clean and consistent." No test asserts "looks good."

## Clarifications

### Session 2026-06-30

- Q: How far to merge - nav links, tabs, a handoff, or a full single-page merge? → A: A (symmetric nav) + C
  (post-onboard handoff). NOT a full single-page merge (the 2-column runner and the step wizard differ
  enough that a SPA merge is not worth its cost yet).
- Q: Include a UI touch-up? → A: Yes. Unify + polish the EXISTING styling (shared header/nav, consistent
  spacing / typography / buttons; group the live-runner's long form; tidy the onboard steps). Vanilla CSS,
  no framework/build, no layout rewrite, no behavior change beyond A+C.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Move between the two views in one click (Priority: P1)

From either page (live-runner or onboarding), the designer sees a consistent header/nav and reaches the
other view in one click, so the tool reads as one app rather than two URLs.

**Why this priority**: This is the core of "one interface instead of 2 links." Today the live-runner has no
link to onboarding, so the designer must know the `/onboard` URL. Symmetric nav removes that.

**Independent Test**: The served live-runner page contains a nav link to the onboarding view AND the served
onboarding page contains a nav link to the live-runner view (both directions present). A one-directional
build fails. Free, no model calls (structural grep); the look/consistency is the human eye.

**Acceptance Scenarios**:

1. **Given** the live-runner page, **When** the designer views the header, **Then** it shows a consistent
   nav with a link to the onboarding view (and marks the current view active).
2. **Given** the onboarding page, **When** the designer views the header, **Then** it shows the same nav
   with a link to the live-runner view.

### User Story 2 - Onboard a brand, then generate with it in one flow (Priority: P1)

After the designer successfully onboards (saves) a brand, a "Generate a sign for this brand" action takes
them to the live-runner with that brand already selected, so onboarding then designing is a continuous flow
with no dropdown hunting.

**Why this priority**: This connects the WORKFLOW, not just the navigation. The brand the designer just
created is the one they want to design with; preselecting it removes friction and closes the onboard →
generate loop.

**Independent Test**: The onboarding save-success state contains a handoff link to the live-runner carrying
the saved brand id (`/?brand=<id>`); the live-runner reads the `brand` query param on load and selects that
brand in its dropdown after the brand list loads, with a graceful fallback when the param is absent or the
brand is not in the list. Free, no model calls (structural grep for the wiring + the human eye for the flow).

**Acceptance Scenarios**:

1. **Given** a just-saved brand, **When** the onboarding success state renders, **Then** it offers a
   "Generate a sign for this brand" action linking to the live-runner with that brand id.
2. **Given** the live-runner opened with a brand query param, **When** the brand list has loaded, **Then**
   that brand is preselected in the dropdown.
3. **Given** the live-runner opened with no brand param (or an unknown brand), **When** it loads, **Then**
   it falls back to the default selection with no error.

### User Story 3 - The app looks like one polished product (Priority: P2)

The two pages share a consistent, tidied visual style (header/nav, spacing, typography, buttons; the
live-runner's long form grouped; the onboard steps tidied), so the app reads as one product rather than two
ad-hoc pages.

**Why this priority**: The polish makes A+C feel cohesive. It is valuable but secondary to the navigation +
handoff wiring, and it is validated by the eye, not by tests.

**Independent Test**: Human eye (§II): both pages share the same header/nav and visual language; the
live-runner form is easier to scan; nothing looks broken. No functional change; the prior structural suites
stay green (behavior unchanged). No automated aesthetic assertion.

**Acceptance Scenarios**:

1. **Given** both pages, **When** the designer looks at them, **Then** they share one consistent header/nav
   and visual style (human eye).
2. **Given** the live-runner form, **When** the designer scans it, **Then** the fields are grouped/tidied
   and readable (human eye), with the run behavior unchanged.

### Edge Cases

- The live-runner opened with no `brand` param → default selection, no error (US2 AS3).
- The live-runner opened with a `brand` param not in `/brands` (e.g., a typo, or a brand not yet saved) →
  graceful fallback to the default, no error (US2 AS3).
- The brand list loads asynchronously → the preselect applies AFTER the list is populated (not a race that
  silently no-ops).
- The two pages' nav could drift (a link added to one but not the other) → a structural test asserts BOTH
  pages carry BOTH links, so drift fails the test.
- No functional regression: the run flow, the onboarding wizard steps, and the server routes are unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both frontend pages MUST present a consistent header/nav with links to the live-runner view
  and the onboarding view, and MUST indicate the current (active) view.
- **FR-002**: The nav MUST be bidirectional: the live-runner links to onboarding AND onboarding links to the
  live-runner (both links present on both pages).
- **FR-003**: On a successful onboard save, the success state MUST present a "Generate a sign for this brand"
  action that opens the live-runner carrying the saved brand id.
- **FR-004**: The live-runner MUST read the brand identifier from the request query on load and preselect
  that brand in its dropdown AFTER the brand list has loaded.
- **FR-005**: The preselect MUST fall back gracefully to the default selection when the brand param is
  absent or the brand is not in the list, with no error.
- **FR-006**: The change MUST be pure frontend: NO new server route and NO change to generation, register,
  onboarding logic, or the input contract; the run flow and the onboarding wizard steps are unchanged.
- **FR-007**: The UI touch-up MUST unify + polish the existing styling (shared header/nav, consistent
  spacing / typography / buttons; the live-runner form grouped; the onboard steps tidied) using vanilla CSS
  (no framework/build), with NO layout rewrite and NO behavior change beyond A+C.
- **FR-008**: No paid model calls anywhere in this feature or its tests (it is a nav / handoff / polish
  change; no generation is involved).
- **FR-009**: No em-dashes in any user-facing text (the nav labels, the handoff action, any new copy).

### Key Entities

- **Shared nav**: the consistent header/nav on both pages (links to the live-runner + onboarding views,
  active-view indicator). [Whether the markup is duplicated per page or factored is a `/speckit-plan`
  decision.]
- **Brand handoff link**: the onboard-success action carrying the saved brand id to the live-runner
  (`/?brand=<id>`), consumed by the live-runner's preselect.
- **Brand preselect**: the live-runner's read of the brand query param, applied to the brand dropdown after
  the list loads, with a graceful fallback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From either page, the designer reaches the other view in ONE click. (eye + structural)
- **SC-002**: The served live-runner page links to onboarding AND the served onboarding page links to the
  live-runner (both directions). (structural, presence grep)
- **SC-003**: After onboarding a brand, the "Generate a sign for this brand" action lands the designer in
  the live-runner with that brand preselected. (eye + structural)
- **SC-004**: The live-runner preselects the brand from the query param when present and in the list, and
  falls back to the default otherwise with no error. (structural + eye)
- **SC-005**: The two pages read as one consistent, polished product, and the live-runner form is easier to
  scan, with the run behavior unchanged. (human eye, §II)
- **SC-006**: No functional regression: the prior frontend / thin / conductor structural suites stay green.
  (structural)
- **SC-007**: No paid model calls occur anywhere; no em-dash in user-facing text. (process + structural)

> SC-001, SC-003, and SC-005 are HUMAN-EYE judgments (§II). The structural tests are presence greps for the
> wiring (both nav links, the handoff link, the preselect code) - the weakest gate (§III) - so the eye is the
> real proof of "one app, clean and consistent." No test asserts an aesthetic.

## Assumptions

- The two pages stay TWO static HTML files served by the existing routes (`/`, `/onboard`); this feature
  adds nav + a handoff + polish, not a single-page merge. Whether the shared nav markup is duplicated or
  factored is a `/speckit-plan` decision (default: duplicate the small snippet, with a test that BOTH pages
  carry both links so drift fails).
- The live-runner already loads its brand list from the existing `/brands`; the preselect hooks in after
  that load. No server route is added.
- The onboard save already returns / knows the saved brand id, so the handoff link can carry it.
- The UI touch-up is a polish pass on the existing vanilla CSS, not a redesign, a design system, or a
  framework; the run flow and wizard behavior are unchanged.
- Aesthetic quality and flow smoothness are validated by the human eye (§II); automated tests cover only the
  wiring presence + no-regression.

## Out of Scope (v1)

- A full single-page merge with in-page tab switching (rejected in clarification).
- Any new server route, or any change to generation, register, onboarding logic, or the input contract.
- A visual redesign / design system / CSS framework / build step (stay vanilla CSS; polish the existing).
- A mobile / responsive redesign beyond keeping the existing layout usable.
- Persisting nav state or user preferences across sessions.
