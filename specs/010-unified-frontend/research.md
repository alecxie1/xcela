# Phase 0 Research: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

The spec's scope forks were settled (Clarifications: A+C, not a SPA merge; + a UI touch-up). The one flagged
HOW item plus the two wiring choices are resolved here, grounded in code read 2026-06-30. No NEEDS
CLARIFICATION remains.

## Decision 1: nav markup - duplicate vs factor

**Decision**: DUPLICATE a small shared nav snippet in both `index.html` and `onboard.html` (each with the
current view marked active). Do NOT factor it into a served `nav.js` / `app.css`. The polish CSS likewise
lives in each page's existing `<style>` block, applying the same design to both.

**Rationale**:
- `server.py` serves only `/` -> index.html and `/onboard` -> onboard.html (`:106-109`); there is NO generic
  static-file route. A factored `nav.js`/`app.css` would need a NEW route, which the spec locks out (FR-006,
  "no new server route").
- The nav snippet is tiny (a header + two links). Duplication's only real risk is DRIFT (a link added to one
  page but not the other); a structural test asserting BOTH pages carry BOTH links closes that (drift fails
  the test).
- Keeps the change purely in the two HTML files, no new files, no server touch (§VII thin).

**Alternatives considered**:
- *Factor into a served `nav.js` + `app.css`*: rejected for v1. Cleanest for drift, but needs a new
  static-asset route (out of scope) and adds machinery for two small pages. Revisit if the app grows.
- *Server-side inject the nav on GET*: rejected. Touches `server.py` (a route/response change) for a
  cosmetic gain; against the pure-frontend scope.

## Decision 2: brand preselect wiring (the handoff read side)

**Decision**: In `index.html`'s existing `loadBrands()`, AFTER the brand `<option>`s are built from
`/brands`, read `new URLSearchParams(location.search).get("brand")`; if it is one of the returned brands, set
`$("brand").value = it`; otherwise leave the default selection. No error either way.

**Rationale**:
- `loadBrands()` is the single place the dropdown is populated (from the existing `/brands`), so the preselect
  must run AFTER that fetch resolves (avoids a race that silently no-ops).
- Honest-null (§V): an absent or unknown `brand` param falls back to the default (the first option), never an
  error or an invented selection. Unknown covers a typo or a brand not yet in `answer_keys/`.

**Alternatives considered**:
- *Preselect before the list loads*: rejected (race; the value would be set then overwritten by the async
  population).
- *A server route that returns the resolved brand*: rejected (no new route; the client already has `/brands`).

## Decision 3: the handoff link (the write side)

**Decision**: In `onboard.html`'s save-success handler, replace the plain success text with the message + a
link to `/?brand=<data.brand>` (`encodeURIComponent(data.brand)`). The save response already returns
`data.brand` (the saved id) and `data.message`.

**Rationale**:
- `data.brand` is exactly the brand the designer just created, which is the one they want to design with;
  linking to the live-runner with it preselected closes the onboard -> generate loop.
- Local single-designer app; `data.brand` is the designer's chosen id, so `encodeURIComponent` in the href is
  sufficient hygiene.

## Decision 4 (honesty, §II/§III): what the tests can and cannot prove

**Decision**: The automated tests are PRESENCE GREPS (both nav links on both pages; the preselect reads the
query param + references the brand select; the onboard handoff link; no em-dash) + a no-regression run of the
prior suites. They are explicitly the WEAKEST gate. The REAL proof of A+C + the polish (one app, clean, the
onboard -> preselected-generate flow) is the HUMAN EYE (§II). No test asserts an aesthetic.

**Rationale**: The value here is navigational/visual/flow, which a string grep cannot validate. Rather than
dress a token-presence check up as proof (the §III no-op-gate trap), the plan states plainly that the greps
only prove the wiring EXISTS and the eye is the proof. The greps still fail a genuinely wrong build (a
one-directional nav, a missing handoff link, a preselect that never reads the param).

## Reuse map (touched vs untouched)

| Component | 010 disposition |
|-----------|-----------------|
| `frontend/index.html` | CHANGED (nav + `?brand=` preselect in loadBrands + polish + form grouping) |
| `frontend/onboard.html` | CHANGED (shared nav replaces the back-link + save-success handoff link + polish) |
| `frontend/server.py` (`/`, `/onboard`, `/brands`, `/run`, `/onboard/*`) | UNCHANGED (no new route) |
| `inputs_writer`, `runner`, `onboard.py`, conductor, generation | UNCHANGED |
