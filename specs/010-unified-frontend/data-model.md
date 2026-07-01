# Phase 1 Data Model: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

No database and no new persisted state. The "entities" are UI constructs + one URL-carried value. The
server routes and the input contract are unchanged.

## Shared nav

- A consistent header/nav present on BOTH pages, with two links: the live-runner view (`/`, label
  "Generate a sign") and the onboarding view (`/onboard`, label "Onboard a brand"), the current view marked
  active.
- Duplicated markup in both `index.html` and `onboard.html` (no served asset, no new route). Invariant: BOTH
  pages carry BOTH links (a structural test enforces this so drift fails).

## Brand handoff (URL-carried, transient)

- On a successful onboard save, the success state renders a link to `/?brand=<saved brand id>`
  (`encodeURIComponent`). The saved id comes from the existing save response (`data.brand`).
- Carried only in the URL query; nothing persisted.

## Brand preselect

- The live-runner reads `brand` from the request query (`URLSearchParams(location.search).get("brand")`) in
  `loadBrands()`, AFTER the brand `<option>`s are built from the existing `/brands`.
- Applied only if the value is one of the returned brands; otherwise the default selection stands (no error).

## UI touch-up (visual only)

- Consistent header/nav, spacing, typography, buttons across both pages; the live-runner's long flat form
  grouped into fieldsets (e.g. asset / brand voice / elements / message); the onboard steps tidied. Vanilla
  CSS in each page's `<style>`. No layout rewrite, no behavior change. Eye-validated (§II).

## Validation rules (where each FR is enforced)

| Rule | Where | FR |
|------|-------|----|
| Consistent header/nav with both links + active view | both HTML headers | FR-001 |
| Bidirectional nav (both links on both pages) | both HTML headers + the drift test | FR-002 |
| Onboard-success handoff link carrying the brand id | onboard.html save-success handler | FR-003 |
| Live-runner reads `?brand=` and preselects after the list loads | index.html loadBrands() | FR-004 |
| Graceful fallback when absent / unknown | index.html loadBrands() (no error path) | FR-005 |
| Pure frontend, no route / back-half / run-flow change | only the two HTML files edited | FR-006 |
| Vanilla-CSS polish, no behavior change | both `<style>` blocks + markup grouping | FR-007 |
| No paid calls; no em-dash | tests + the copy | FR-008 / FR-009 |
