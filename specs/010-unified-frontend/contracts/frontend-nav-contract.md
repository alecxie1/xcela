# Contract: shared nav + brand handoff/preselect

Pure frontend (two HTML files); no server route change. The value is eye-judged; the contract below is the
WIRING the structural tests grep for.

## Shared nav (both pages)

- `index.html` and `onboard.html` each render a header/nav containing a link to `/` ("Generate a sign") AND a
  link to `/onboard` ("Onboard a brand"), with the current view marked active.
- Duplicated snippet (no served asset). Invariant tested: BOTH pages contain BOTH links.

## Brand handoff (onboard -> live-runner)

- On a successful save, `onboard.html` renders a link `href="/?brand=<encodeURIComponent(data.brand)>"` with
  visible text "Generate a sign for this brand" (alongside the existing saved/message text).

## Brand preselect (live-runner)

- `index.html` `loadBrands()`: after building the brand `<option>`s from `/brands`, read
  `new URLSearchParams(location.search).get("brand")`; if it is in the returned list, set the brand select to
  it; else leave the default. No error on absent / unknown.

## Unchanged

`server.py` routes (`/`, `/onboard`, `/brands`, `/run`, `/onboard/*`), the run flow, the onboarding wizard
steps, `inputs_writer`, the conductor, and generation. No new route, no persisted state.

## Falsifiable tests (`test_frontend_nav.py`, no paid calls; PRESENCE GREPS)

- `index.html` contains `href="/onboard"` AND `onboard.html` contains `href="/"` (both directions; a
  one-directional build fails).
- `index.html` references `URLSearchParams` (or `location.search`) AND reads `"brand"` AND sets the brand
  select (`$("brand").value` / `getElementById("brand")`) - the preselect wiring exists and targets the select.
- `onboard.html` save-success path builds a `"/?brand="` handoff link.
- Neither page's user-facing text contains an em-dash (`—`).

> These are presence-level (the weakest gate, §III); they fail a genuinely wrong build (one-directional nav,
> missing handoff, a preselect that never reads the param) but they do NOT prove the look or the flow. The
> HUMAN EYE is the real proof (§II): one-click nav both ways, onboard -> land in the live-runner with the
> brand preselected, one consistent polished look.
