# SPEC BRIEF for /speckit-specify - Feature 010: connect onboard + live-runner (one app) + UI touch-up

DECISION MAP. Scope settled in conversation (2026-06-30) and grounded in the ACTUAL code. Connect the two
`frontend/` pages into ONE app (symmetric nav + a post-onboard handoff) and give the shared UI a polish
pass. Pure frontend (the two HTML files); no new server routes, no back-half change.

---

## Problem / why
The `frontend/` app is two separate pages the user must know by URL: `/` (live-runner) and `/onboard`
(brand onboarding wizard). They are already DATA-connected (a brand onboarded via `/onboard` appears in
the live-runner `/brands` dropdown), and `onboard.html` already links "back to live-runner" (`:30`), but
the live-runner (`index.html:32`, a bare `<header>` with no nav) has NO link to onboarding, so it is
one-directional and reads as two disconnected tools. The designer wanted "one interface instead of 2
links." Two moves fix it: (A) symmetric nav so both pages cross-link into one app, and (C) a post-onboard
HANDOFF so after saving a brand the designer can jump straight into generating with it. Plus a light UI
touch-up so the two pages look like one polished product.

## Goal (scopes "done")
The two pages read and navigate as ONE app: a consistent header/nav on both links to "Generate a sign"
(`/`) and "Onboard a brand" (`/onboard`); after a successful onboard save, a "Generate a sign for this
brand" action opens the live-runner with that brand PRESELECTED (`/?brand=<id>`); and the shared UI gets a
polish pass (consistent header/nav, spacing, typography, buttons; the live-runner's long form tidied into
groups) with NO functional change beyond A+C. "Done" = from either page the designer reaches the other in
one click, onboarding a brand then generating with it is a continuous flow (no dropdown hunting), and the
app looks consistent and clean by the human eye.

## LOCKED decisions (settled in conversation; do NOT relitigate)

| Decision | Locked value | Rationale |
|---|---|---|
| Scope | A (symmetric nav) + C (post-onboard handoff) + a UI touch-up | the designer's pick; A+C removes the navigation + workflow friction, the touch-up makes it one product |
| NOT in scope | a full single-page merge (one shell with in-page tab switching) | the two layouts (2-column runner vs step wizard) differ enough that a SPA merge is not worth its cost yet |
| Nav | a shared, consistent header/nav on BOTH pages with links to `/` ("Generate a sign") and `/onboard` ("Onboard a brand"); the current page marked as active | one app, both directions; `onboard.html` already has a back-link to extend into a real nav |
| Handoff | on a SUCCESSFUL onboard save, show a "Generate a sign for this brand" link/button to `/?brand=<id>`; the live-runner reads `?brand=` and PRESELECTS that brand in its dropdown | connects the flow (onboard -> generate the brand just made); a graceful fallback if the param is absent / the brand is not in the list |
| Server | NO new routes; A+C are pure frontend (`/` + `/onboard` already exist; the preselect is a client-side query-param read against the existing `/brands`) | thin: the frontend adapts; the back-half is untouched |
| UI touch-up | unify + polish the EXISTING styling (shared header/nav, consistent spacing / typography / buttons; group the live-runner's long flat form; tidy the onboard steps). Vanilla CSS, no framework/build. NO layout rewrite, NO behavior change beyond A+C | make it look like one product; the aesthetic is a human-eye judgment (§II), not a structural claim |
| Validation | structural greps for the WIRING (both nav links; the `?brand=` preselect code; the handoff link) + the HUMAN EYE for the look/flow | honest: UI polish is eye-judged; the greps are presence-checks (the weakest gate), so the eye-gate is the real proof (§II/§III) |

## The change, stage by stage (pure frontend)
```
frontend/index.html  : add a shared header/nav (links to / and /onboard, active state); read ?brand= on
                       load and preselect it in the brand dropdown (after /brands loads; graceful if
                       absent / not found); apply the UI polish (spacing, typography, buttons, form
                       grouping). No functional change to the run flow.
frontend/onboard.html: extend the existing back-link into the SAME shared header/nav; on a successful save,
                       render a "Generate a sign for this brand" link to /?brand=<savedBrandId>; apply the
                       same UI polish. No change to the wizard steps' logic.
(server.py, inputs_writer, conductor, onboard.py: UNCHANGED)
```

## Verified codebase state (STEP ZERO - confirm before building)
- `server.py:106-109` serves `/` -> index.html and `/onboard` -> onboard.html (read from disk each GET, so
  edits show on refresh; no restart needed for HTML). `/brands` lists `answer_keys/*.json`.
- `index.html:32` is a bare `<header>Handyprint Live Runner ...</header>` with NO nav; `loadBrands()`
  populates `$("brand")` from `/brands` (the preselect hooks in after this).
- `onboard.html:30` already has `<header>Brand Onboarding <a href="/">back to live-runner</a></header>`
  (extend into the shared nav); the save success path shows an in-browser success message (add the handoff
  link there). The save response returns the brand id.
- Both pages share the same header color (`#2a2a2e`) and system-ui font, so a shared nav/polish is
  low-friction.

## Forks already resolved (do not reopen)
- A+C, not a full SPA merge (D) — locked.
- Nav is a shared header on both pages (not a separate route/page).
- Preselect is a client-side `?brand=` read (no server route).
- The UI touch-up is a polish pass, NOT a redesign or a framework introduction.

## Out of scope (v1)
- A full single-page merge with in-page tab switching (option D).
- Any new server route, back-half, generation, register, onboarding-logic, or input-contract change.
- A visual redesign / design system / CSS framework / build step (stay vanilla CSS, polish the existing).
- Mobile / responsive redesign beyond keeping the existing layout usable.
- Persisting nav state or user preferences.

## Falsifiable tests (constitution §III - assert VALUES a wrong build cannot satisfy; NO paid calls)
- `index.html` contains a nav link to `/onboard` AND `onboard.html` contains a nav link to `/` (both
  directions present - a one-directional build fails).
- `index.html` reads the `brand` query param (URLSearchParams / location.search) AND applies it to the
  brand `<select>` after `/brands` loads (assert the preselect wiring exists AND references the select).
- `onboard.html`'s save-success path contains a handoff link to `/?brand=` (the flow connection).
- No em-dash in either page's user-facing text (a free grep).
- NOTE (honesty, §III): these are presence greps (the weakest gate). The REAL proof of A+C + the polish is
  the HUMAN EYE (§II): from each page reach the other in one click; onboard a brand then land in the
  live-runner with it preselected; the app looks consistent and clean. Record the eye verdict.

## Hard rules
- NO paid model calls anywhere (this is a nav/handoff/polish change; no generation involved in the tests).
- Pure frontend: NO new server route, NO back-half / generation / onboarding-logic change; the frontend
  adapts (§VII thin).
- Agent-free unchanged (§I): the human still drives every gate; this only improves navigation + flow.
- The aesthetic is a human-eye judgment (§II), not a structural claim; do not assert "looks good" in a test.
- Vanilla CSS/JS only (no framework, no build step).
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII). NO em-dashes in user-facing text.

## Open question for /speckit-plan (flag, do not solve in the spec)
Whether the shared header/nav markup is DUPLICATED in the two HTML files (simplest, stdlib-static) or
factored to avoid drift (e.g., a tiny shared snippet injected by the server on GET, or a JS-rendered nav
component). Resolve at /speckit-plan against the two-static-file reality; default is duplicate-the-small-
snippet with a structural test that BOTH pages carry both links (so drift fails the test).
