---
description: "Task list for Designer-facing Web Onboarding Gate"
---

# Tasks: Designer-facing Web Onboarding Gate

**Input**: Design documents from `specs/006-web-onboarding-gate/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-28: transient draft + zero-color block), research.md (D1-D6), data-model.md, contracts/ (4 files), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests target the PURE new modules (`multipart`, `onboard`, `persist`) over the synthetic-PDF fixture; NO paid model calls (the deterministic OCR path is local; the OCR organ is already proven in 005). The human browser smoke + the one paid sign are the eye-gate AFTER the build.

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project + the existing `frontend/` stdlib web app (extended) + the 005 `brand_intake/` package (reused). Self-tests as `test_*.py` at repo root. Output `answer_keys/<brand>.json` (committed) + the logo under gitignored `brands/<brand>/`. Transient draft dirs under a scratch path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The shared write helper + the stdlib upload parser both the CLI and the web gate stand on. No wizard logic yet.

- [X] T001 [P] Implement `brand_intake/persist.py` (shared, CLI + web) per `contracts/persist-contract.md`: `key_exists(brand) -> bool` (answer_keys/<brand>.json exists, the id-collision guard); `place_logo(brand, src) -> dest` (copy under gitignored `brands/<brand>/`, return the path, NEVER the taichi default); `write_key(brand, key) -> path` (write answer_keys/<brand>.json; callers validate first). PURE/IO helpers, no model.
- [X] T002 [P] Implement `frontend/multipart.py` (stdlib, PURE) per `contracts/multipart-contract.md`: `parse_multipart(body: bytes, content_type: str) -> {fields, files}` via hand-rolled boundary parsing (no `cgi`, no new dep); binary file bytes preserved byte-for-byte; malformed/empty body -> empty dicts (no crash).

**Checkpoint**: the write home + the upload parser exist, independently testable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Refactor the 005 CLI onto the shared `persist` helpers (so CLI + web write identically) and prove the upload parser + standalone CLI before any wizard work.

**⚠️ CRITICAL**: `onboard.save_draft` (US3) and the CLI must share ONE write home; confirm it here.

- [X] T003 [P] Write `test_multipart.py`: a synthetic multipart body with one text field + one file part round-trips — `parse_multipart` returns the field value AND the file's filename + EXACT bytes (assert a binary PDF/PNG byte-string survives unmodified); a malformed body yields empty fields/files (no crash). MUST FAIL before T002 is done (write alongside T002; both [P]).
- [X] T004 Refactor `brand_intake/intake.py` to call `persist.place_logo` / `persist.write_key` / `persist.key_exists` for its write tail (replace the inline logo-copy + JSON-write), adding the id-collision block (FR-014). The CLI flow is otherwise UNCHANGED and still runs standalone. Confirm via `tests_support/verify_reuse.py` + a `--no-gate` CLI run on the synthetic fixture that the CLI still writes a valid key end to end.

**Checkpoint**: one shared write home; the CLI is intact on it; multipart parsing proven.

---

## Phase 3: User Story 1 - Upload a PDF, confirm the suggested pages (Priority: P1) 🎯 MVP

**Goal**: The designer uploads a brand PDF in the browser and is shown the deterministically suggested 1-indexed spec pages to confirm or correct.

**Independent Test**: `onboard.start_draft(pdf_bytes)` over the synthetic fixture returns a draft_id + suggestions whose `color` is the hex-token page (1-indexed), not the color-mention page. Free, no model calls.

### Tests for User Story 1

- [X] T005 [P] [US1] Add to `test_onboard.py` the start-draft assertions: `start_draft(pdf_bytes)` (synthetic fixture via `tests_support/make_pdf`) returns a `draft_id` + `suggestions`; `suggestions["color"]` contains the hex-token page (2, 1-indexed) and NOT the color-mention page (1); a draft dir was created holding the PDF on disk. MUST FAIL before T006.

### Implementation for User Story 1

- [X] T006 [US1] Implement `frontend/onboard.py` `start_draft(pdf_bytes) -> {draft_id, suggestions}` per `contracts/draft-model.md`: create a transient draft dir under a scratch path, write the PDF to `<draft>/source.pdf`, return an opaque draft_id + `page_finder.suggest_pages(...)`. PURE-callable (bytes in, dict out); no committed artifact written. `test_onboard.py` start-draft checks pass.
- [X] T007 [US1] Add the upload route to `frontend/server.py`: `GET /onboard` (serve the wizard screen) + `POST /onboard/upload` (multipart PDF -> `parse_multipart` -> `onboard.start_draft` -> `{draft_id, suggestions}`). Thin glue; reuse `_send`. Reject a body with no PDF (fail loud).

**Checkpoint**: a designer can upload a PDF in the browser and see suggested pages. MVP entry.

---

## Phase 4: User Story 2 - Extract and review the brand locks (Priority: P1)

**Goal**: On the confirmed pages, the proven extractors run (loading state, local OCR) and the browser shows each color (hex + provenance + needs_review) + the brand-name candidates; zero colors blocks + returns to page-confirm.

**Independent Test**: `onboard.extract_draft(draft_id, pages)` returns color locks (hex + needs_review) + name candidates; a confirmed page set yielding ZERO colors returns a BLOCK (no fabricated color). Free at the structural level (OCR on the fixture is exercised in the human smoke).

### Tests for User Story 2

- [X] T008 [P] [US2] Add to `test_onboard.py` the extract assertions: `extract_draft(draft_id, {color:[2], name:[1]})` over the fixture returns colors carrying `hex` + `needs_review` and brand-name candidates; `extract_draft(draft_id, {color:[1]})` (the no-hex page) returns a `block` (no colors), NOT an empty success. MUST FAIL before T009.

### Implementation for User Story 2

- [X] T009 [US2] Implement `frontend/onboard.py` `extract_draft(draft_id, confirmed_pages) -> {locks, names} | {block}` per `contracts/draft-model.md`: run `extract.extract_brand_colors` + `read_brand_names` on the confirmed pages; on ZERO colors return `{block: "no colors found on these pages"}` (never fabricate / never empty gate); else return the locks (role unset) + name candidates. `test_onboard.py` extract checks pass.
- [X] T010 [US2] Add the extract route to `frontend/server.py`: `POST /onboard/<id>/extract` (JSON confirmed pages -> `onboard.extract_draft` -> `{locks, names}` or a `{block}` the UI shows + returns to page-confirm). Thin glue.

**Checkpoint**: confirmed pages yield reviewable locks with provenance; a bad page set blocks honestly.

---

## Phase 5: User Story 3 - Verify, validate-loud, and save (Priority: P1)

**Goal**: Assign roles + acknowledge flags + confirm names + upload logo -> validate-loud + save the lean key (or fail loud in-browser); the saved brand appears in the live-runner.

**Independent Test**: `onboard.save_draft(...)` with a primary + real logo + acknowledged flags writes a key that passes `validate_lean_key` and yields the primary hex in a thin prompt; it FAILS LOUD (no file) on missing primary / logo, an unacknowledged flag, or an existing brand id; the saved brand appears in `frontend.server._brands()`. Free, no model calls.

### Tests for User Story 3

- [X] T011 [P] [US3] Add to `test_onboard.py` the save assertions (throwaway brand id, cleaned up): `save_draft` with one primary + a real logo + every flag acknowledged writes `answer_keys/<id>.json` that passes `validate_lean_key` and yields a non-empty thin prompt with the primary hex; the draft dir is gone after save; the brand appears in `frontend.server._brands()`. FAIL-LOUD (no file written): no primary; missing/unreal logo; an unacknowledged needs_review flag; an existing brand id (collision, reuse `aia`). A keep-flagged lock persists `needs_review` in the saved key. ALSO assert the saved key has NO `fields.typography.styles` (FR-010 honest-null is falsifiable, not incidental). MUST FAIL before T012.

### Implementation for User Story 3

- [X] T012 [US3] Implement `frontend/onboard.py` `save_draft(draft_id, verified, logo_bytes) -> {brand, key_path}` per `contracts/draft-model.md`: block on `unacknowledged_flags`; block on `persist.key_exists(brand)` (id collision); `build_lean_key(... finalize_items(verified.colors) ...)`; `validate_lean_key` (fail loud on no primary / missing-or-unreal logo); `persist.place_logo` + `persist.write_key`; discard the draft dir. Raise/return a named error (no write) on any fail. `test_onboard.py` save checks pass.
- [X] T013 [US3] Add the save route to `frontend/server.py`: `POST /onboard/<id>/save` (multipart logo + JSON verified locks/roles/acks/names -> `onboard.save_draft`); 200 + `{brand, key_path}` on success, 4xx + `{error: <named reason>}` and NO write on any fail. Single-flight (reuse `_inflight`).
- [X] T014 [US3] Implement the onboarding wizard screen (`frontend/index.html` onboarding section or a new `frontend/onboard.html` served at `/onboard`): the 3 steps — (1) upload PDF, (2) confirm suggested pages, (3) extract (cost-free loading state) -> verify gate (assign color roles, confirm brand names, acknowledge each needs_review confirm/edit/keep-flagged, upload logo) -> Save. Show in-browser fail-loud errors; on success show "this brand is now available in the live-runner." Inline vanilla JS, no framework, no em-dashes.

**Checkpoint**: a designer onboards a brand end to end in the browser; the key is validated, saved, and visible in the live-runner.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the human browser + paid smoke.

- [ ] T015 [P] Update `SYSTEM_MAP.md` + `CLAUDE.md` in the same commit that makes them stale (§VII): the web onboarding gate is built (3-step wizard over the 005 pure modules + the 004 server pattern); the shared `persist.py`; the transient-draft + zero-color-block + id-collision behavior; the multipart-stdlib choice; onboard -> generate handoff via `/brands`. Note the deferred items (VLM semantic layer, font-pairing widget, brand-management, resumable drafts).
- [ ] T016 [P] Run the free structural suite (`test_multipart`, `test_onboard`, `tests_support/verify_reuse`) and confirm the prior suites stay green (001-005: test_kit/compose_select/fit_to_zone/kit_reserve_box/format_size/faithful_intake/brief_wiring/review/page_finder/brand_key + test_conductor/test_render_and_scrub/test_frontend_*). Server GET smoke: start `frontend/server.py`, fetch `/onboard` + `/brands` (no upload, no paid call). ALSO assert FR-013 structurally: the served `/onboard` page + `frontend/onboard.py` + `frontend/multipart.py` user-facing strings contain NO em-dash (`—`) (a free grep). Paste real output.
- [ ] T017 The human browser smoke + paid eye-gate (SC-001/SC-007, NOT automated): open `http://localhost:<port>/onboard`, upload a real cold-brand PDF, confirm pages, verify locks (assign primary, acknowledge flags, confirm names), upload the logo, and save; confirm the key matches the printed spec and appears in the live-runner dropdown; generate a sign for it (the one paid step) and judge by eye (§II). Record the verdict in `SYSTEM_MAP.md`. Needs spend + the human; left for the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; `persist.py` (T001) ∥ `multipart.py` (T002) are different files.
- **Foundational (Phase 2)**: T004 (CLI refactor) needs `persist.py` (T001); T003 (multipart test) pairs with T002. Blocks US3's save (shared write home) — land before T012.
- **US1 (Phase 3)**: after Setup. `onboard.start_draft` (T006) needs only `page_finder` (005). The MVP entry.
- **US2 (Phase 4)**: after US1 (extends `onboard.py` + needs a draft from start_draft).
- **US3 (Phase 5)**: after US2 (needs the locks) + Foundational (the shared `persist`). The save closes the loop.
- **Polish (Phase 6)**: after US1+US2+US3.

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- `onboard.py` grows across US1->US2->US3 (start_draft -> extract_draft -> save_draft); the server route for each step lands right after its `onboard.py` function.
- US3: `save_draft` (T012) before its route (T013) before the wizard screen save step (T014).
- Commit after each task (§VII).

### Parallel Opportunities

- Setup: T001 ∥ T002. Tests: T003 (multipart) ∥ T005 (start_draft) can be drafted together.
- T015 ∥ T016 in Polish (docs vs running self-tests).
- `persist.py`, `multipart.py` are independent files (different modules).

---

## Parallel Example: kicking off

```bash
# Setup modules + their tests (different files), then the CLI refactor onto the shared write home:
Task: "T001 Implement brand_intake/persist.py"
Task: "T002 Implement frontend/multipart.py"
Task: "T003 Write test_multipart.py"
```

---

## Implementation Strategy

### MVP First (Setup + US1)

1. Phase 1 Setup (`persist.py` + `multipart.py`).
2. Phase 2 Foundational (CLI onto `persist`; multipart proven; standalone CLI intact).
3. Phase 3 US1 (`start_draft` + upload route): the designer uploads a PDF and sees suggested pages.
4. **STOP and VALIDATE**: `test_onboard` start-draft green + a server GET/upload smoke — the browser entry works, all free.

### Incremental Delivery

1. Setup + Foundational → shared write home + upload parsing + intact CLI.
2. US1 → upload + page suggestions (MVP entry).
3. US2 → extract + review locks (zero-color block).
4. US3 → verify + validate-loud + save (the loop closes; brand appears in the live-runner).
5. Polish → durable docs, free suite green, then the human browser + paid eye-gate.

### Notes

- [P] = different files, no incomplete dependencies.
- NO paid model calls in ANY automated test (§ Cost discipline). The deterministic OCR path is local; tests assert the pure `multipart` / `onboard` / `persist` logic over the synthetic fixture. Only T017 (the human browser run + the one paid sign) spends, eye-validated (§II).
- THIN over the agent-free core (§I/§VII): the server delegates to `onboard.py`, which composes the 005 PURE modules; it never reimplements extraction/validation/gate/generation and never calls `intake.main()`.
- The UI auto-decides NO brand lock (pages suggested, roles/names/flags human).
- Fail loud or honest-null at every stage (§V): validate-loud save, zero-color block, id-collision block, kept-flag persists needs_review, abandoned draft discarded, logo real or fail.
- The standalone 005 CLI stays runnable with the web gate absent (T004 / SC-006).
- No em-dashes in any user-facing text (server responses, the wizard screen).
