# Feature Specification: Designer-facing Web Onboarding Gate

**Feature Branch**: `006-web-onboarding-gate`

**Created**: 2026-06-28

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief (`specs/_inbox/006-web-onboarding-gate.md`). The brand-onboarding
FRONT-half (feature 005) is built and verified working FROM THE TERMINAL (a cold brand was onboarded
end to end via `brand_intake/intake.py` and the resulting key ran the back-half). But the internal
designer does not live in a terminal: there is no way for them to onboard a cold brand without the
CLI. The capability exists; the designer-facing SURFACE does not. This feature builds that surface,
the same way feature 004 wrapped the back-half thin route in a thin local web gate.

> **Scope note (constitution §IV / §VII):** 006 is a SURFACE over proven organs. It wraps the 005
> PURE modules (`page_finder.suggest_pages`, `extract.extract_brand_colors` / `read_brand_names`,
> `assemble_key.build_lean_key`, `validate_key.validate_lean_key`, the gate helpers
> `intake.unacknowledged_flags` / `finalize_items`) and reuses the 004 local-web pattern. It does NOT
> reimplement extraction, validation, the gate logic, or generation, and it does NOT call the
> stdin-bound `intake.main()`.

> **The thesis this feature serves (constitution §I):** the verify gate IS the input gate, moved to
> the browser. Page-finding only SUGGESTS; the human confirms the pages, assigns color roles, confirms
> brand names, and acknowledges every `needs_review`. The UI auto-decides NO brand lock.

## Clarifications

### Session 2026-06-28

- Q: If the designer abandons the wizard mid-flow (closes the tab, or starts a new PDF) before saving, what happens to the uploaded PDF + in-progress state? → A: DISCARD, no persistence. The uploaded PDF and the draft state are transient (cleaned up); ONLY a successful save writes anything (`answer_keys/<brand>.json` + the logo). There is no resumable / saved draft in v1; to restart, the designer re-uploads.
- Q: How should the gate handle a confirmed color page that yields ZERO extracted colors (bad page pick / image-only page)? → A: BLOCK + let them re-pick. Show an honest "no colors found on these pages" message and send the designer back to the page-confirm step to correct the pages. Never fabricate a color and never silently proceed to an empty gate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload a brand PDF, confirm the suggested spec pages (Priority: P1)

The designer opens the onboarding screen in the browser, uploads a brand-guideline PDF, and is shown
the deterministically SUGGESTED 1-indexed color / font / brand-name pages, which they confirm or
correct.

**Why this priority**: This is the entry to the gate. Without browser upload + page confirmation, the
designer still needs the terminal. The suggestion keeps the human at the input gate without blind
page-number typing; auto-detecting pages with a model is the rejected v3 silent-judgment path.

**Independent Test**: Post a brand PDF to the page-suggest endpoint and confirm it returns the
hex-token page (1-indexed) for color, not a page that merely mentions color (it consumes
`page_finder.suggest_pages`, not a re-implementation). Free, no model calls (synthetic fixture PDF).

**Acceptance Scenarios**:

1. **Given** an uploaded multi-page brand PDF, **When** the page-suggest step runs, **Then** the
   browser shows suggested color / font / brand-name pages (1-indexed) the designer can confirm or
   override.
2. **Given** a page that mentions "color" in prose but has no hex token, **When** suggestions are
   computed, **Then** that page is NOT suggested as the color page.

### User Story 2 - Extract and review the brand locks (Priority: P1)

On the confirmed pages, the deterministic extractors run (showing a loading state, since local OCR
takes seconds) and the browser displays each extracted color (swatch + hex + provenance +
`needs_review`) and the CN/EN brand-name candidates.

**Why this priority**: The designer must SEE what was extracted, with provenance, to verify it. This
is the substance of the gate. The extraction reuses the proven 005 organs.

**Independent Test**: Drive the extract step over the synthetic fixture and confirm the returned locks
carry hex + `needs_review` from `extract_brand_colors` and the name candidates from
`read_brand_names`, surfaced for the human (no model call; OCR is local, exercised only in the human
smoke). Free at the structural level.

**Acceptance Scenarios**:

1. **Given** confirmed color pages, **When** extraction runs, **Then** each extracted color is shown
   with its hex, provenance, and `needs_review` flag, and the brand-name candidates are listed.
2. **Given** extraction is in progress, **When** the designer waits, **Then** a loading state is shown
   (local OCR latency), NOT a paid-cost label (extraction spends nothing).
3. **Given** the confirmed color pages yield ZERO extracted colors, **When** extraction completes,
   **Then** the gate shows an honest "no colors found on these pages" message and returns the designer
   to the page-confirm step to correct the pages (no fabricated color, no empty verify gate).

### User Story 3 - Verify, validate-loud, and save a consumable key (Priority: P1)

The designer assigns a role to each color (one primary), confirms the brand names, uploads the logo,
and acknowledges every `needs_review` (confirm / edit / keep-flagged). On save, the lean key is built,
VALIDATED LOUD (a missing primary color or logo shows a clear in-browser error, never a silent save),
and written to `answer_keys/<brand>.json` with the logo placed under `brands/<brand>/`. The new brand
then appears in the 004 live-runner brand dropdown.

**Why this priority**: This closes the loop, agent-free: a saved, validated key the existing thin route
and the 004 live-runner consume unchanged. The validate-loud + acknowledgment gate is the safety model.

**Independent Test**: Post confirmed pages + verified locks for the synthetic fixture to the save
endpoint and confirm it writes an `answer_keys/<brand>.json` that passes the existing
`validate_lean_key` and yields a non-empty thin prompt with the primary hex; and that save FAILS LOUD
(error, no file written) when the primary color is unassigned or the logo is missing. Free, no model
calls.

**Acceptance Scenarios**:

1. **Given** verified locks with one primary color, a confirmed logo, and every flag acknowledged,
   **When** the designer saves, **Then** `answer_keys/<brand>.json` is written (a kept flag recorded
   in it), the logo is placed under `brands/<brand>/`, and the key passes `validate_lean_key`.
2. **Given** no color is marked primary OR no logo is supplied, **When** the designer saves, **Then**
   the browser shows a clear named error and NO key file is written.
3. **Given** a lock still carries an unacknowledged `needs_review`, **When** the designer attempts to
   save, **Then** save is blocked until every flag is acknowledged (confirm / edit / keep-flagged).
4. **Given** a brand was just saved, **When** the designer opens the 004 live-runner, **Then** the new
   brand appears in its brand dropdown (which lists `answer_keys/*.json`).

### Edge Cases

- A page mentions "color" with no hex token → not suggested as the color page (US1 AS2).
- Local OCR latency on the extract step → a loading state is shown; extraction makes no paid call.
- A `needs_review` lock the designer cannot verify → keep-flagged; the flag is written into the saved
  key as an honest record, never silently dropped.
- Missing primary color or missing/unreal logo → save FAILS LOUD in the browser; no file written
  (never the silent taichi-logo default `scene_author` falls back to).
- An image-only (scanned) PDF → the degraded path 005 documents (colors still OCR off captions; fonts
  route to the existing VLM fallback, more `needs_review`); the gate surfaces the degradation honestly.
  If the confirmed pages yield ZERO colors, the gate blocks and returns the designer to page-confirm
  (US2 AS3), never an empty verify gate.
- The designer abandons the flow mid-wizard (closes the tab / starts a new PDF) → the uploaded PDF and
  draft state are DISCARDED (transient, cleaned up); no partial key is written. Save is the only write;
  there is no resumable draft in v1. To restart, the designer re-uploads.
- A brand id that already has an answer_key → save is BLOCKED with a clear in-browser error naming the
  collision; the designer picks a new id. v1 is onboard-a-NEW-brand and editing existing keys is out of
  scope, so block (never silently overwrite a committed brand key). Overwrite-with-confirmation is a
  later brand-management concern.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present a designer-facing web onboarding screen in the existing local
  `frontend/` app (a new screen + routes, same local-web pattern), reachable without a terminal.
- **FR-002**: The designer MUST be able to UPLOAD the brand PDF and the logo as real files through the
  browser (not enter a server-side path); the server saves the upload and the existing modules read it.
- **FR-003**: The system MUST suggest the color / font / brand-name spec pages via
  `page_finder.suggest_pages` (1-indexed) and let the designer confirm or correct each. It MUST NOT
  use a model to auto-detect pages.
- **FR-004**: On the confirmed pages, the system MUST run the PROVEN extractors
  (`extract_brand_colors`, `read_brand_names`) and display each color (hex + provenance +
  `needs_review`) and the CN/EN brand-name candidates. It MUST reuse the 005 modules, not reinvent
  extraction. If extraction yields ZERO colors, the system MUST show an honest "no colors found"
  message and return the designer to the page-confirm step (never fabricate a color or open an empty
  verify gate).
- **FR-005**: The verify gate MUST let the designer assign a role to each color (one primary), confirm
  the brand names, and ACKNOWLEDGE every `needs_review` (confirm / edit / keep-flagged) before save; a
  kept flag is written into the saved key. The UI MUST NOT auto-decide any role, name, or flag.
- **FR-006**: On save, the system MUST build the lean key (`build_lean_key`) and VALIDATE LOUD
  (`validate_lean_key`): a missing primary color or a missing / unreal logo MUST produce a clear
  in-browser error and write NO key file (never a silent degraded save).
- **FR-007**: On a valid save, the system MUST write `answer_keys/<brand>.json` AND place the logo
  under `brands/<brand>/` (the same artifacts the 005 CLI writes).
- **FR-008**: The saved key MUST be consumable UNCHANGED by the existing thin route and appear in the
  004 live-runner brand dropdown (which lists `answer_keys/*.json`).
- **FR-009**: The web server MUST reuse the 005 PURE modules + gate helpers and MUST NOT call the
  stdin-bound `intake.main()`, nor reimplement extraction / validation / the gate logic / generation.
- **FR-010**: `typography.styles` MUST remain honest-null in v1 (no font-pairing step); the new
  brand's first sign carries a generic font directive (the documented 005 honest-null).
- **FR-011**: The standalone 005 CLI (`brand_intake/intake.py`) MUST still run the full onboarding
  flow from one command with the web gate absent; the web surface adds no dependency the CLI needs.
- **FR-012**: No paid model calls in any automated test; the deterministic OCR path is local. The one
  paid sign remains the back-half eye-gate (004 / CLI), not part of 006.
- **FR-013**: No em-dashes in any user-facing text (Output rule).
- **FR-014**: If the chosen brand id already has an `answer_keys/<brand>.json`, save MUST be blocked
  with a clear in-browser error (never silently overwrite a committed brand key); the designer chooses
  a new id.

### Key Entities

- **Uploaded brand PDF**: the file the designer uploads; saved server-side, read by the extractors.
- **Page Suggestions**: `page_finder` output (1-indexed color / font / brand-name pages), each
  confirmable / correctable by the designer.
- **Extracted Locks**: colors (hex + provenance + `needs_review`, role unset) + CN/EN brand-name
  candidates, surfaced for verification.
- **Logo Asset**: the designer-uploaded logo file, placed under `brands/<brand>/`.
- **Verify-gate Draft**: the TRANSIENT in-progress state across the wizard steps (uploaded PDF,
  confirmed pages, in-progress verified locks) before the final save. Discarded on abandon; never
  persisted as a resumable draft (only a successful save writes). [The cross-request mechanism for
  holding this transient state, server-side session vs client re-post, is a `/speckit-plan` decision.]
- **Lean answer_key**: the saved consumable output (`answer_keys/<brand>.json`), the 005 consumed
  subset; consumed unchanged by the thin route + the 004 live-runner.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A designer onboards a never-seen brand entirely in the browser (upload PDF → confirm
  pages → verify locks → upload logo → save a validated lean key), with NO terminal. (eye + structural)
- **SC-002**: The page-suggest step returns the hex-token page (1-indexed) for color, not a
  color-mention page, over the synthetic fixture. (structural, falsifiable)
- **SC-003**: The save endpoint writes an `answer_keys/<brand>.json` that passes `validate_lean_key`
  and yields a non-empty thin prompt with the primary hex. (structural, falsifiable)
- **SC-004**: Save FAILS LOUD (in-browser error, no file written) on a missing primary color or
  logo, AND is blocked while any `needs_review` flag is unacknowledged. (structural, falsifiable)
- **SC-005**: A brand saved by the web gate appears in the 004 live-runner brand dropdown (the
  onboard → generate handoff). (structural)
- **SC-006**: The standalone 005 CLI still runs the full onboarding flow from one command with the web
  gate absent. (structural)
- **SC-007**: No paid model calls occur in any automated test; the deterministic path is local. The
  one paid sign is the human's back-half eye-gate after the build. (process)

> All eye-marked criteria are human-eye judgments per constitution §II; no VLM self-score counts as
> proof. Automated tests assert STRUCTURE only (the hex-token page, save-writes-valid-key, fail-loud,
> the acknowledgment gate, the dropdown handoff, the standalone CLI), never pixel quality.

## Assumptions

- The onboarding gate is a LOCAL single-designer web app, an extension of the 004 `frontend/` local
  app (one tool the designer opens for both onboarding and generation); not a hosted / multi-user
  service. The specific UI stack follows the 004 pattern (stdlib local server + a static page) and is
  confirmed at `/speckit-plan`.
- The deterministic color / name path is model-free / local (rapidocr); the extract step has latency
  but spends nothing. Image-only PDFs are a degraded path (more `needs_review`), not perfected.
- The web server reuses the 005 PURE modules + gate helpers, never `intake.main()`. Whether the 005
  linear flow is refactored into a shared pure orchestration function both the CLI and server call is
  a `/speckit-plan` decision.
- The wizard's draft state is TRANSIENT (discarded on abandon; only a successful save writes, clarified
  2026-06-28); the cross-request MECHANISM for holding it (server-side session vs stateless client
  re-post) is an OPEN QUESTION for `/speckit-plan`, resolved against the 004 server shape and the
  thin-surface rule.
- `brands/<brand>/` is gitignored (the logo lands there); `answer_keys/<brand>.json` is committed
  brand data. The web gate writes the identical artifacts the 005 CLI writes.
- The cold-brand CLI onboarding is verified working (005 T015), so 006's premise (the capability
  exists, the surface does not) holds.

## Out of Scope (v1)

- The VLM SEMANTIC layer (tone / imagery_style / motifs / category / logo description) — still
  deferred; the thin route reads none of it.
- Logo EXTRACTION / auto-crop from the PDF — the designer uploads the logo.
- A font-to-register-lane pairing widget (`typography.styles` authoring) — stays honest-null in v1.
- Multi-user / authentication / hosted deployment — a local single-designer tool.
- A brand-management dashboard (edit / delete existing keys); re-onboarding an existing brand id is a
  flagged edge case, not a v1 management surface.
- Resumable / saved drafts: an abandoned wizard is discarded (transient state only); persisting and
  resuming an in-progress onboarding is a later enhancement, not v1.
- Any change to the back-half, the 005 extraction logic, or generation — 006 is a surface that adapts
  to them.
- Calling `intake.main()` from the server, or the server reimplementing extraction / validation /
  gate / generation logic.
