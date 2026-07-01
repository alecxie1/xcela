---
description: "Task list for Connect Onboard + Live-runner Into One App (+ UI Touch-up)"
---

# Tasks: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

**Input**: Design documents from `specs/010-unified-frontend/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-30: A+C not a SPA merge; + UI touch-up), research.md (D1-D4), data-model.md, contracts/ (frontend-nav), quickstart.md

**Tests**: INCLUDED, but HONESTLY LABELLED. The automated tests are PRESENCE GREPS (both nav links on both pages; the `?brand=` preselect wiring; the onboard handoff link; no em-dash) + a no-regression run - the WEAKEST gate (§III). They fail a genuinely wrong build (one-directional nav, missing handoff, a preselect that never reads the param) but they do NOT prove the look or the flow. The REAL proof is the HUMAN EYE (§II), and here it is FREE (nav + flow + look, no generation). No test asserts an aesthetic. NO paid calls anywhere.

**Organization**: Tasks grouped by user story. Pure frontend (the two HTML files). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project + the thin local web frontend. Only `frontend/index.html` + `frontend/onboard.html` are edited (server + back-half UNCHANGED). Self-test as `test_frontend_nav.py` at repo root. Nav snippet duplicated per page (no new route/asset), drift-guarded by a both-pages-both-links test.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The test scaffold + the cross-cutting no-em-dash guard. No page edit yet.

- [X] T001 [P] Create `test_frontend_nav.py` (stdlib, no paid calls) that reads `frontend/index.html` + `frontend/onboard.html`; first check (cross-cutting FR-009): neither page's user-facing text contains an em-dash (`—`). (The per-story wiring checks land in T002/T004.)

**Checkpoint**: the test scaffold exists; the em-dash guard is in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None beyond Setup. The change is two static HTML files; the nav snippet is duplicated per page (no shared prerequisite, no new route/asset). US1/US2/US3 all edit those two files (sequential on them).

**Checkpoint**: user-story work can start.

---

## Phase 3: User Story 1 - Move between the two views in one click (Priority: P1) 🎯 MVP

**Goal**: A consistent header/nav on both pages cross-links the live-runner and onboarding, so the tool reads as one app and each view is one click from the other.

**Independent Test**: `index.html` contains a nav link to `/onboard` AND `onboard.html` contains a nav link to `/` (both directions). A one-directional build fails. Free, no model calls (presence grep); the look is the human eye.

### Tests for User Story 1

- [X] T002 [US1] Add to `test_frontend_nav.py` the both-directions nav check: `frontend/index.html` contains a nav link `href="/onboard"` AND `frontend/onboard.html` contains a nav link `href="/"` (assert BOTH pages carry BOTH links, so nav drift fails the test). MUST FAIL before T003.

### Implementation for User Story 1

- [X] T003 [US1] Add a shared header/nav to BOTH `frontend/index.html` (replace the bare `<header>` at `:32`) and `frontend/onboard.html` (replace the back-link header at `:30`): a consistent header with links to `/` ("Generate a sign") and `/onboard` ("Onboard a brand"), the current view marked active (live-runner active on index, onboard active on onboard). Duplicate the small snippet per page. No em-dash. No functional change. `test_frontend_nav.py` US1 check passes.

**Checkpoint**: both pages cross-link in one click; the app reads as one. MVP.

---

## Phase 4: User Story 2 - Onboard a brand, then generate with it in one flow (Priority: P1)

**Goal**: After a successful onboard save, a "Generate a sign for this brand" action opens the live-runner with that brand preselected, closing the onboard -> generate loop.

**Independent Test**: `onboard.html`'s save-success path builds a `/?brand=<id>` handoff link; `index.html`'s `loadBrands()` reads the `brand` query param and applies it to the brand select after `/brands` loads, with a graceful fallback. Free, no model calls (presence grep for the wiring + the human eye for the flow).

### Tests for User Story 2

- [X] T004 [US2] Add to `test_frontend_nav.py`: (a) `frontend/onboard.html`'s save-success handler builds a handoff link containing `"/?brand="`; (b) `frontend/index.html` references `URLSearchParams` (or `location.search`) AND `"brand"` AND the brand select (`getElementById("brand")` / `$("brand")`), i.e. the preselect wiring exists and targets the select. MUST FAIL before T005/T006.

### Implementation for User Story 2

- [X] T005 [US2] In `frontend/onboard.html` save-success handler (`$("s3ok")`, `:140`): render the saved/message text PLUS a "Generate a sign for this brand" link to `/?brand=<encodeURIComponent(data.brand)>` (data.brand is the saved id from the save response). No em-dash.
- [X] T006 [US2] In `frontend/index.html` `loadBrands()`: after building the brand `<option>`s from `/brands`, read `new URLSearchParams(location.search).get("brand")` and, if it is one of the returned brands, set `$("brand").value` to it; otherwise leave the default (no error). No run-flow change.

**Checkpoint**: onboard a brand, click through, and the live-runner opens with it preselected; unknown/absent falls back cleanly.

---

## Phase 5: User Story 3 - The app looks like one polished product (Priority: P2)

**Goal**: The two pages share one consistent, tidied visual style; the live-runner's long form is grouped and scannable; nothing looks broken and behavior is unchanged.

**Independent Test**: HUMAN EYE (§II) - both pages share the header/nav + visual language; the live-runner form is easier to scan. No automated aesthetic assertion; the prior structural suites stay green (behavior unchanged).

### Implementation for User Story 3

- [X] T007 [US3] Apply the UI touch-up to BOTH `frontend/index.html` and `frontend/onboard.html` (vanilla CSS in each page's `<style>`, no framework/build): a consistent header/nav, spacing, typography, and button styling; group the live-runner's long flat form into fieldsets (e.g. asset / brand voice + vibe / elements / message); tidy the onboard steps. NO layout rewrite, NO behavior change beyond A+C, no em-dash. Eye-validated (no structural test asserts the look; `test_frontend_nav.py` + the prior suites must stay green to prove no regression).

**Checkpoint**: one consistent, polished product; the run flow + wizard unchanged.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the FREE human eye/flow check.

- [X] T008 [P] Update `CLAUDE.md` + `SYSTEM_MAP.md` in the same commit that makes them stale (§VII): the two frontend pages are now one app (shared nav on both; the onboard -> `/?brand=` handoff + the live-runner preselect in `loadBrands`; the UI touch-up); pure frontend, no new route; the value is eye-judged (the greps only prove the wiring). Note the deferred item (a full single-page merge).
- [X] T009 [P] Run the free structural suite and paste real output: `test_frontend_nav.py` (all checks) + no-regression `test_frontend_intake.py` / `test_frontend_runner.py` / `test_frontend_stages.py` / `test_reference_upload.py` / `test_onboard.py`; confirm the prior 001-009 suites stay green (behavior unchanged).
- [ ] T010 The human eye/flow gate (SC-001/003/005, NOT automated - but FREE, no paid generation): `pkill -f frontend/server.py; .venv/bin/python frontend/server.py`, hard-refresh the browser, then confirm by EYE: nav both ways in one click; onboard a brand -> "Generate a sign for this brand" -> the live-runner opens with it preselected; `/?brand=unknown` falls back to the default with no error; both pages read as one consistent, polished product and the run flow still works. Record the verdict in `SYSTEM_MAP.md`. No spend required.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; the test scaffold + em-dash guard.
- **Foundational (Phase 2)**: none beyond Setup.
- **US1 (Phase 3)**: after Setup. The shared nav on both pages. MVP.
- **US2 (Phase 4)**: after Setup; independent of US1's nav (different regions: save-success + loadBrands). Can proceed alongside US1.
- **US3 (Phase 5)**: after US1 (it polishes the nav US1 adds) + US2 (polishes the handoff success state); a pass over both files.
- **Polish (Phase 6)**: after US1 + US2 + US3.

### Within Each User Story

- The test task (test-first) is written and MUST FAIL before its implementation.
- Both HTML files are touched across US1 (nav) / US2 (handoff + preselect) / US3 (polish) - sequential on the two files; land US1, then US2, then US3's polish over the top.
- Commit after each task (§VII).

### Parallel Opportunities

- Setup: T001 alone.
- US2: T005 (onboard.html save-success) ∥ T006 (index.html loadBrands) are different regions/files.
- Polish: T008 ∥ T009 (docs vs running self-tests).
- The per-story checks share `test_frontend_nav.py`, so they are added sequentially to that file.

---

## Parallel Example: kicking off

```bash
# Setup, then the nav (US1) and the handoff/preselect (US2) can be built together (different regions):
Task: "T001 Create test_frontend_nav.py scaffold + em-dash guard"
Task: "T003 Add the shared header/nav to both HTML pages"          # US1
Task: "T005 Add the /?brand= handoff link to onboard save-success" # US2
```

---

## Implementation Strategy

### MVP First (Setup + US1)

1. Phase 1 Setup (the test scaffold + em-dash guard).
2. Phase 3 US1 (the shared nav): both pages cross-link in one click.
3. **STOP and VALIDATE**: `test_frontend_nav.py` US1 check green + a browser click both ways (free) - the app reads as one.

### Incremental Delivery

1. Setup → the test scaffold.
2. US1 → symmetric nav (MVP: one interface).
3. US2 → the onboard -> preselected-generate handoff (the flow).
4. US3 → the UI touch-up (one polished product).
5. Polish → durable docs, free suite green, then the FREE human eye/flow check.

### Notes

- [P] = different files/regions, no incomplete dependencies.
- NO paid model calls anywhere (nav / handoff / polish). The tests are PRESENCE GREPS (the weakest gate, §III) + no-regression; they prove the wiring EXISTS, not the look or the flow. The eye is the real proof (§II), and here it is FREE (T010, no generation).
- Pure frontend (§VII thin): NO new server route; NO change to generation / register / onboarding logic / the input contract / the run flow / the wizard steps.
- Agent-free unchanged (§I): only navigation + flow + look improve.
- Honest-null (§V): the preselect falls back to the default on an absent / unknown brand param (no error, no invented selection).
- Vanilla CSS/JS only (no framework/build). No em-dashes in any user-facing text.
