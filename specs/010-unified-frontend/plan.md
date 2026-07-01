# Implementation Plan: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

**Branch**: spec dir `010-unified-frontend`; work continues on the existing `006-web-onboarding-gate` git branch by deliberate reuse (as with 007/008/009) | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-unified-frontend/spec.md`

## Summary

Make the two `frontend/` pages read and navigate as ONE app, on the thin local web stack. (A) a shared,
consistent header/nav on both pages cross-linking "Generate a sign" (`/`) and "Onboard a brand"
(`/onboard`); (C) a post-onboard HANDOFF - on a successful save, a "Generate a sign for this brand" link to
`/?brand=<id>`, and the live-runner reads `?brand=` and preselects that brand after `/brands` loads (graceful
fallback if absent / unknown); plus a UI touch-up (consistent header/nav, spacing, typography, buttons; the
live-runner's long form grouped into fieldsets; the onboard steps tidied). Pure frontend edits to the two
HTML files; no new server route, no back-half change.

The one flagged decision is RESOLVED here, grounded in the code:

1. **Nav markup is DUPLICATED (a small snippet) in both HTML files**, not factored into a served asset.
   `server.py` serves only `/` and `/onboard` (no generic static-file route), and the spec locks "no new
   route" (FR-006), so a shared `nav.js`/`app.css` would need a new route. Duplicating a tiny nav snippet
   avoids that; the drift risk is closed by a structural test asserting BOTH pages carry BOTH links. Same for
   the polish CSS: each page keeps its own `<style>` (already the case), with the same design applied to both.

Two more wiring decisions (grounded in the code):
- **Preselect** hooks into the existing `loadBrands()` in `index.html`: after the `<option>`s are built from
  `/brands`, read `new URLSearchParams(location.search).get("brand")` and, if it is one of the returned
  brands, set the select value; otherwise leave the default (no error).
- **Handoff** replaces the onboard save-success text (`onboard.html` `$("s3ok")`, which already has
  `data.brand`) with a message + a link to `/?brand=<data.brand>` (`encodeURIComponent`).

## Technical Context

**Language/Version**: Python 3.11 stdlib server (unchanged); the pages are vanilla HTML/CSS/JS (no
framework, no build).

**Primary Dependencies**: none new. Edits only `frontend/index.html` + `frontend/onboard.html`.
`frontend/server.py` serves both from disk each GET (edits show on refresh; no restart for HTML).

**Storage**: None. No new persisted state; the handoff passes the brand id in the URL query.

**Testing**: Falsifiable STRUCTURAL tests are PRESENCE GREPS here (both nav links on both pages; the
`?brand=` preselect wiring referencing the brand select; the onboard handoff link; no em-dash) plus the
no-regression run of the prior suites. Per the spec's honesty note, these greps are the WEAKEST gate; the
REAL proof of "one app, clean, smooth flow" is the HUMAN EYE (§II). No test asserts an aesthetic. NO paid
calls (no generation involved).

**Target Platform**: Localhost single-designer web app (same as 004-009).

**Project Type**: Single project + the thin local web frontend (two static pages edited).

**Performance Goals**: N/A.

**Constraints**: Pure frontend; NO new server route; NO change to generation / register / onboarding logic /
the input contract / the run flow / the wizard steps (FR-006). Vanilla CSS/JS, no framework/build. The
aesthetic is eye-judged, not a structural claim. No em-dashes in user-facing text.

**Scale/Scope**: v1 = symmetric nav + the post-onboard handoff/preselect + a polish pass on the two pages.
No single-page merge, no new routes, no redesign/framework.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | Only improves navigation + flow; the human still drives every input/taste gate. No model, no auto-glue added. | PASS |
| II. Ground truth = the eye | The value (one app, clean, smooth handoff) is explicitly a HUMAN-EYE judgment; SC-001/003/005 are eye-marked. Tests assert only wiring presence + no-regression; no VLM, no aesthetic assertion. | PASS |
| III. Falsifiable tests only | The structural tests assert VALUES a wrong build fails: both nav links present on both pages (a one-directional build fails); the preselect code reads the query param AND references the brand select; the onboard success carries a `/?brand=` link. HONESTLY LABELLED as presence greps (the weakest gate); the eye is the real proof. No no-op token gate is dressed up as proof of the look. | PASS (with honesty note) |
| IV. Generalize, do not hand-tune | Nav + handoff + polish are brand/task-general (no brand/image literals); the preselect works for any brand from `/brands`. | PASS |
| V. Honest nulls, never invented | The preselect falls back to the default when the brand param is absent / unknown (no error, no invented selection). | PASS |
| VI. Reconciliation per-dimension | Untouched (no generation/register change). | PASS |
| VII. Repo is durable; thin / reuse | Pure frontend, no new route/dependency; reuses `/brands` + the existing save response; one falsifiable (grep-level) test + the eye-gate; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid model calls anywhere (nav/handoff/polish only). PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/010-unified-frontend/
├── spec.md              # Feature spec (clarified 2026-06-30: A+C, not a SPA merge; + UI touch-up)
├── plan.md              # This file
├── research.md          # Phase 0: nav-duplicate decision + the preselect/handoff wiring + honesty note
├── data-model.md        # Phase 1: the shared nav, the handoff link, the brand preselect (no persisted data)
├── contracts/
│   └── frontend-nav-contract.md   # the nav links + the /?brand= handoff + the preselect behavior
├── quickstart.md        # Phase 1: free structural greps + the LOAD-BEARING human eye/flow check
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # CHANGED: add the shared header/nav (links / + /onboard, "/" active); in
│                         #   loadBrands(), after building the brand <option>s, read ?brand= and preselect
│                         #   it if in the list (graceful fallback); UI polish (header/nav, spacing,
│                         #   typography, buttons; group the long form into fieldsets). No run-flow change.
└── onboard.html         # CHANGED: replace the bare back-link header with the SAME shared header/nav
                         #   ("/onboard" active); in the save-success handler, render a "Generate a sign for
                         #   this brand" link to /?brand=<data.brand>; the SAME UI polish. No wizard-logic change.

test_frontend_nav.py     # NEW: falsifiable structural self-test (no paid calls) - PRESENCE GREPS: both
                         #   index.html and onboard.html contain nav links to BOTH / and /onboard; index.html
                         #   reads the brand query param (URLSearchParams/location.search) AND references the
                         #   brand select in loadBrands; onboard.html's save-success path builds a /?brand=
                         #   handoff link; neither page's user-facing text has an em-dash. (Presence-level;
                         #   the eye-gate is the real proof, per the spec honesty note.)
```

**Structure Decision**: A pure two-file frontend change. The nav snippet is duplicated in both pages (no new
route/asset, honoring FR-006) with a structural drift guard (both pages must carry both links). The handoff
is a URL query (`/?brand=<id>`) written by onboard-success and read by the live-runner's `loadBrands()`
preselect, reusing the existing `/brands` list; no server route, no persisted state. The UI touch-up applies
the same vanilla-CSS design to both pages' existing `<style>` blocks and groups the live-runner form; it is
eye-validated, with no behavior change. `server.py`, `inputs_writer`, `runner`, `onboard.py`, the conductor,
and generation are all UNCHANGED (FR-006).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
