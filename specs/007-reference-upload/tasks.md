---
description: "Task list for Reference-image Upload in the Live-runner"
---

# Tasks: Reference-image Upload in the Live-runner

**Input**: Design documents from `specs/007-reference-upload/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D4), data-model.md, contracts/ (uploads + http-run), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests target the PURE `save_upload` helper + the multipart parse-save-assemble path + the fail-loud path over a synthetic multipart body (mirroring `test_multipart.py`); NO paid model calls (never `runner.launch` / generation). The human browser smoke + the one paid sign fold into 004's pending T016.

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project + the existing `frontend/` stdlib web app (the 004 live-runner + the 006 upload machinery). One new tiny module (`frontend/uploads.py`), one changed route (`POST /run`) and one changed input (`index.html`), one refactored call site (`_onboard_save`). Self-test as `test_reference_upload.py` at repo root. The reference lands in the per-run dir `output/run_*/`; the conductor / CLI input contract (`reference_image` = a path) is UNCHANGED.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The shared save-upload helper both the new `/run` reference-save and the refactored 006 logo-save stand on. No route change yet.

- [X] T001 [P] Implement `frontend/uploads.py` (stdlib, small) per `contracts/uploads-contract.md`: `save_upload(file_tuple, dest_dir, name=None) -> str` — take a `(filename, bytes)` multipart tuple, reduce the chosen name (`name` or the uploaded filename) to its BASENAME (no path traversal), `mkdir` the dest dir, write the raw bytes, return the saved path string. Bytes preserved byte-for-byte; no default substitution / no fabrication (a missing tuple is the caller's fail-loud responsibility). Keep `frontend/multipart.py` UNCHANGED (it stays the PURE parser; this is the disk side).
- [X] T002 [P] Create `test_reference_upload.py` (stdlib, no paid calls) with the FIRST check (save-upload round-trip): given `("ref.png", FILE_BYTES)` and a tmp dest dir, `save_upload(...)` returns a path that EXISTS and whose bytes EQUAL `FILE_BYTES` (a truncating / re-encoding build fails this); a crafted `"../evil.png"` name is reduced to its basename inside the dest dir. MUST FAIL before T001 is done (write alongside T001; both [P], different files).

**Checkpoint**: the one save-upload home exists, independently testable; `multipart.py` + `inputs_writer.py` untouched.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None beyond Setup. The single shared prerequisite (`frontend/uploads.py`) is delivered in Phase 1; once its round-trip test is green, the user stories can begin. `frontend/inputs_writer.py` and `frontend/multipart.py` are reused UNCHANGED.

**Checkpoint**: the shared helper is green; user-story work can start.

---

## Phase 3: User Story 1 - Upload the reference instead of typing a path (Priority: P1) 🎯 MVP

**Goal**: The designer picks the reference image from disk in the live-runner; on run, the uploaded file is saved into the run dir and that path drives the conductor. The typed-path field is gone.

**Independent Test**: A synthetic multipart `/run`-style body (a `reference` file + a `form` JSON field) → after parse + save + inject + assemble, the inputs JSON's `reference_image` points at a file that EXISTS in the run dir AND the path is in the JSON, with NO generation launched. Free, no model calls.

### Tests for User Story 1

- [X] T003 [P] [US1] Add to `test_reference_upload.py` two checks: (a) the `/run`-assembly check — build a synthetic multipart body with a `reference` file part + a `form` field (`json.dumps({brand, messages, ...})`), drive the parse → `save_upload` into a tmp run dir → inject `reference_image` → `inputs_writer.write_inputs(form, run_dir/"inputs.json")` (the route's actual call), and assert the written inputs JSON's `reference_image` is a path that EXISTS in that run dir AND the saved bytes match; (b) the file-input grep — `frontend/index.html` contains `<input type="file"` for the reference and NO typed-path text input / `placeholder="/abs/path` (SC-007). MUST FAIL before T004/T005.

### Implementation for User Story 1

- [X] T004 [US1] Change `frontend/server.py` `POST /run` to multipart per `contracts/http-run-endpoint.md`: parse `multipart.parse_multipart(self._read_body(), Content-Type)`; read `form = json.loads(fields["form"] or "{}")`; validate brand (unchanged); acquire single-flight; `mkdir` the run dir; derive the extension from the uploaded filename (`ext = os.path.splitext(files["reference"][0])[1]`, e.g. `.jpg`/`.png`; empty if none) and save as `ref_path = uploads.save_upload(files["reference"], run_dir, name="reference"+ext)` so the saved file preserves the uploaded type; set `form["reference_image"] = ref_path`; then `inputs_writer.write_inputs(form, run_dir/"inputs.json")` (UNCHANGED) and `_launch_async(...)` (UNCHANGED). Keep the response shape. (The missing-reference fail-loud guard is US2/T007.)
- [X] T005 [US1] Update `frontend/index.html`: replace the reference text input (`<input id="reference_image" placeholder="/abs/path...">`) with `<input type="file" id="reference_image">`; remove `reference_image` from `formState()`'s value read; change `startRun` to POST `FormData` (`fd.append("form", JSON.stringify(formState()))`, `fd.append("reference", $("reference_image").files[0], name)`, optional `fd.append("style_notes", note)`) instead of a JSON body; the client-side guard checks a file is PICKED (`files[0]`), not a non-empty string. No em-dashes. The nudge re-run path (`startRun(note)`) reuses the still-selected file.

**Checkpoint**: a designer picks a reference file in the browser and the run consumes it; the assembled inputs point at the saved file. MVP.

---

## Phase 4: User Story 2 - Missing reference fails loud (Priority: P1)

**Goal**: A run with no reference file is rejected with a clear error and nothing is launched.

**Independent Test**: A `/run`-style multipart body with NO `reference` file → the assembly path fails loud (raises / 4xx) and no run dir launch. Free, no model calls.

### Tests for User Story 2

- [X] T006 [P] [US2] Add to `test_reference_upload.py` the fail-loud check: a synthetic multipart `/run`-style body with a `form` field but NO `reference` file part → the parse-then-guard step raises / returns the 4xx path, and NO run is launched (assert no `_launch_async` / no generation; e.g. the guard returns before the launch step). MUST FAIL before T007.

### Implementation for User Story 2

- [X] T007 [US2] In `frontend/server.py` `POST /run`, add the fail-loud guard (extends T004's route): if `files.get("reference")` is absent or has empty bytes, return `400 {"error": "a reference image is required (v1)"}` (replacing the old typed-path string `"reference_image is required (v1)"` at the current server.py:105-106) BEFORE the run dir is created / single-flight is acquired / launch — so a missing reference launches nothing (FR-005). Invalid `form` JSON → 400. Note: `inputs_writer.to_inputs` already raises on an empty `reference_image` (a backstop); this server 400 must fire FIRST (before `write_inputs`) so the authoritative user-facing message is "a reference image is required (v1)", not the writer's ValueError caught at the generic line-121 handler.

**Checkpoint**: a run with no reference fails loud in-browser; nothing is launched.

---

## Phase 5: User Story 3 - One shared save-upload home; back-half + CLI unchanged (Priority: P1)

**Goal**: The new reference-save and the existing 006 logo-save go through ONE shared helper (DRY), and the downstream (verbatim other fields, the conductor, the standalone CLI) is provably unchanged.

**Independent Test**: `save_upload` is the one home and is used by both call sites; messages/mandatory_elements pass through inputs assembly verbatim; `conductor --thin --inputs <json>` with a `reference_image` path still runs with the frontend absent. Free, no model calls.

### Tests for User Story 3

- [X] T008 [P] [US3] Add to `test_reference_upload.py` two checks: (a) the 002 verbatim invariant — assemble inputs from a multipart `/run` body whose `form` carries `messages` + `mandatory_elements`, and assert those reach the inputs JSON VERBATIM (unchanged ordering/text), proving the other fields are not rephrased; (b) the standalone-CLI regression — assert `test_thin_route.py` stays green AND a hand-written inputs JSON with a `reference_image` PATH still drives `harness/conductor.py --thin --inputs <json> --dry-run --no-approve` (frontend absent) without error, confirming the input contract is unchanged (SC-006). (The `save_upload` round-trip is already asserted in T002.) MUST be meaningful before T009.

### Implementation for User Story 3

- [X] T009 [US3] Refactor `frontend/server.py` `_onboard_save` logo-save onto `uploads.save_upload` (DRY, FR-007): replace the inline `OUTPUT/.onboard_tmp` write (the `Path(logo_src).write_bytes(logo[1])` block) with `logo_src = uploads.save_upload(logo, tmp_dir)`; behavior preserved (the path still feeds `persist.place_logo`). Confirm `test_onboard.py` stays green (the second real call site proves the helper generalizes).

**Checkpoint**: one save-upload home with two call sites; the other fields verbatim; the standalone CLI intact.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the human browser + paid smoke (folded into 004 T016).

- [X] T010 [P] Update `CLAUDE.md` + `SYSTEM_MAP.md` in the same commit that makes them stale (§VII): the live-runner takes the reference as a file UPLOAD (typed path gone); the shared `frontend/uploads.py` `save_upload` used by both `/run` (reference) and `/onboard/save` (logo); `POST /run` is now multipart (a `form` JSON field + a `reference` file); the conductor / CLI input contract is UNCHANGED (`reference_image` = a path); 006's logo-save refactored onto the shared helper. Note the deferred items (file-type validation, batch upload, the ref-less path, a power-user typed-path option).
- [X] T011 [P] Run the free structural suite and paste real output: `test_reference_upload.py` (all checks), `test_multipart.py` + `test_onboard.py` (the refactored logo-save stays green), `test_frontend_intake.py` / `test_frontend_runner.py` / `test_frontend_stages.py`, `test_thin_route.py` (the unchanged contract); confirm the prior 001-005 suites stay green. ALSO assert FR-011 structurally: the served `index.html` user-facing strings contain NO em-dash (`—`) (a free grep). ALSO confirm FR-002 structurally: `frontend/uploads.py` adds no third-party import (stdlib only) and `/run` reuses `multipart.parse_multipart` (grep — no new parser/dep).
- [ ] T012 The human browser smoke + paid eye-gate (SC-001, NOT automated; folds into 004's pending T016): start `frontend/server.py`, open `/`, confirm the reference field is a FILE PICKER (no typed-path field anywhere), fill a single-sign brief, PICK a reference image, Run (paid, about $0.08); confirm the reference is saved into `output/run_*/` and the sign generates from it; judge `output/run_*/sign_*/final.png` by EYE (§II). Confirm a Run with NO file picked is rejected in-browser. Needs spend + the human; left for the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; `uploads.py` (T001) ∥ its test (T002) are different files.
- **Foundational (Phase 2)**: none beyond Setup; the helper (T001) is the only shared prerequisite and blocks both US1's reference-save (T004) and US3's logo refactor (T009).
- **US1 (Phase 3)**: after Setup (needs `save_upload`). The MVP: the multipart `/run` happy path + the file-input UI.
- **US2 (Phase 4)**: after US1 (the fail-loud guard EXTENDS T004's `/run` route — same file, sequential).
- **US3 (Phase 5)**: after Setup (the helper) for the logo refactor; the verbatim + CLI checks are independent of US1/US2 and could be drafted early.
- **Polish (Phase 6)**: after US1+US2+US3.

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- `server.py` `POST /run` is touched by US1 (T004) then US2 (T007) — same file, sequential. `_onboard_save` (T009) is a different region but the same file, so land it after T004/T007.
- Commit after each task (§VII).

### Parallel Opportunities

- Setup: T001 ∥ T002 (different files). 
- The test-first checks T003 / T006 / T008 each precede their implementation; they live in ONE file (`test_reference_upload.py`) so they are added sequentially to that file, not in parallel with each other.
- T010 ∥ T011 in Polish (docs vs running self-tests).

---

## Parallel Example: kicking off

```bash
# The shared helper + its first test (different files), test-first:
Task: "T001 Implement frontend/uploads.py save_upload"
Task: "T002 Create test_reference_upload.py with the save-upload round-trip check"
```

---

## Implementation Strategy

### MVP First (Setup + US1)

1. Phase 1 Setup (`uploads.py` + the round-trip test).
2. Phase 3 US1 (the multipart `/run` happy path + the file-input UI): a designer picks a reference and the run consumes the saved file.
3. **STOP and VALIDATE**: `test_reference_upload.py` assembly + grep checks green; a quick browser GET smoke shows the file picker — all free.

### Incremental Delivery

1. Setup → the one save-upload home.
2. US1 → reference upload works (MVP): file picker + multipart `/run` + saved-file path in the inputs.
3. US2 → missing reference fails loud (nothing launched).
4. US3 → the shared home has two call sites (006 logo refactored); the other fields verbatim; the standalone CLI intact.
5. Polish → durable docs, free suite green, then the human browser + the one paid sign (004 T016).

### Notes

- [P] = different files, no incomplete dependencies.
- NO paid model calls in ANY automated test (§ Cost discipline). Tests assert the pure `save_upload` + the parse-save-assemble path + the fail-loud path over a synthetic multipart body; never `runner.launch` / generation. Only T012 (the human browser run + the one paid sign) spends, eye-validated (§II).
- THIN over the agent-free core (§I/§VII): the frontend adapts to the back-half. The conductor / CLI input contract is UNCHANGED (`reference_image` = a path on disk); `inputs_writer.py` and `multipart.py` are reused unchanged.
- Fail loud, never invent (§V): a missing reference → 400, no run launched, no fabricated path; a bad image still fails loud at the paid step (existing behavior).
- DRY (§IV/§VII): ONE `save_upload` home, two call sites (004 reference + 006 logo).
- The standalone CLI stays runnable with the frontend absent (T008 / SC-006).
- No em-dashes in any user-facing text (the page, server error strings).
