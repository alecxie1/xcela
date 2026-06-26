# Feature Specification: Brand-intake Front-half (PDF to verified answer_key)

**Feature Branch**: `005-brand-intake-front-half`

**Created**: 2026-06-26

**Status**: Draft (refine with `/speckit-clarify` then `/speckit-plan`)

**Input**: Decision-map brief authored 2026-06-26 (`specs/_inbox/005-brand-intake-front-half.md`),
grounded in a live code audit + an independent review (14/14 claims confirmed, 5 integration gaps
surfaced). The back-half (brief to sign, thin route) is built and validated, but onboarding a NEW
brand has no working path: the thing branded the "analyzer" (`analyze_brand_v3.py`) is a HARDCODED
taichi scaffold that takes no arguments, reads pre-rendered taichi PNGs, and EXITS 0 ON TOTAL
FAILURE. The working capability is the DETERMINISTIC extractors (`extract_colors.py`,
`extract_text_layer.py`), proven this session on a cold brand at delta-E < 1, model-free, with a
self-check that flags `needs_review` on disagreement. This feature builds the BODY around those
proven organs: PDF in, human-gated extraction, a LEAN verified answer_key out.

> **Scope note (constitution §IV):** the output key carries ONLY the fields the thin route consumes
> (proven: a key stripped to that subset yields a BYTE-IDENTICAL gpt prompt vs the fat AIA key). The
> new key is deliberately THINNER than AIA's; AIA is fat because it was built to be GRADED, this is
> built to be CONSUMED. Do not copy AIA's shape, copy its consumed subset.

> **The thesis this feature serves (constitution §I/§V):** the same intake to process to HUMAN-GATE
> pattern as the back-half. Here the gate is VERIFY-the-extraction: a deterministic heuristic
> SUGGESTS, the human CONFIRMS, and every brand lock is human-verified before it is saved. Every
> stage fails loud or emits honest-null + a note, never green-on-empty (the v3 anti-pattern).

## Clarifications

### Session 2026-06-26

- Q: Is font-to-register-lane pairing (writing `fields.typography.styles`) in scope for v1? → A: NOT in v1. `typography.styles` is left honest-null; the thin route works without it (the register derivation omits `font_resolved`, the font directive goes generic, no crash). There is NO font-pairing step in onboarding; the designer hand-authors `styles` in the JSON later.
- Q: When a lock still carries a `needs_review` flag, can the human approve + save the key, or must it be resolved first? → A: Block on ACKNOWLEDGMENT, not on clearing. Each `needs_review` lock MUST be explicitly acted on before save: confirm (looked, correct), edit (looked, fixed), or keep-flagged (looked, cannot verify; the flag is written into the saved key as an honest record). The save check is "every flag acknowledged," not "every flag cleared," so honest-null can persist by explicit choice. Color flags MUST be acknowledged (a wrong hex silently poisons every downstream sign). Hard-fail (no save) only on a missing primary color or a missing `logo_path`. Relaxing benign secondary-color flags to advisory is a later call, not a v1 guess.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Page-finding suggests, the human confirms (Priority: P1)

The designer points at a brand-guideline PDF. A DETERMINISTIC heuristic over the text layer SUGGESTS
which pages hold the color / font / brand-name spec (the color page is the one with real hex tokens,
not the pages that merely mention color), and the designer CONFIRMS or corrects the suggested page
numbers.

**Why this priority**: This is the intake gate. Auto-detecting the pages with a model is the v3
silent-judgment disease; dumb full-document scanning is unreliable. A heuristic the human confirms
keeps the designer at the input gate (§I) without blind page-number typing.

**Independent Test**: Run the heuristic on a real multi-page VI PDF and confirm it returns the page
that actually contains hex tokens (e.g. the chajiuxingqiu color page), NOT a page that merely
mentions color. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** a multi-page VI PDF, **When** the heuristic runs, **Then** it suggests the page(s) with
   real hex/RGB tokens for color and the page(s) with font-name patterns for typography, and the
   designer can confirm or override each suggested page number.
2. **Given** a page that mentions "color" in prose but has no hex tokens, **When** the heuristic
   runs, **Then** that page is NOT suggested as the color page.

### User Story 2 - Deterministic extraction on the confirmed pages (Priority: P1)

The PROVEN deterministic extractors run on the confirmed pages: colors are extracted with their hex
(one marked primary), brand names are read from the text layer, and provenance + `needs_review`
surface per lock. The designer supplies the logo file.

**Why this priority**: The extractors are the proven, model-free, self-checking organs (delta-E < 1).
This is the substance the key is built from. Reuse, never reinvent.

**Independent Test**: Extraction on a cold brand returns colors whose hex matches the printed spec
(e.g. chajiuxingqiu yields #31B4E7 / #73C900 / #94D4EB), and flips `needs_review` when the OCR
caption and the pixel-clustered swatch disagree beyond threshold. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** the confirmed color page, **When** the extractor runs, **Then** it returns each color
   with a hex and a role, at least one role is "primary", and the hex matches the printed spec.
2. **Given** an OCR read that disagrees with the pixel-clustered swatch beyond threshold, **When**
   the color is extracted, **Then** its `needs_review` flag is set and surfaced.
3. **Given** the brand-name page, **When** extraction runs, **Then** the CN and EN brand names are
   read from the text layer (not inferred).

### User Story 3 - Assemble, validate-loud, verify, and write a consumable key (Priority: P1)

The lean answer_key is assembled from the extracted locks + the supplied logo, VALIDATED LOUD
(primary color present, logo_path real, else fail with a named reason), shown to the human at a
VERIFY gate (each lock + its provenance/needs_review, editable), and on approval written to
`answer_keys/<brand>.json` with the logo placed under `brands/<brand>/`. The key runs the EXISTING
thin route unchanged.

**Why this priority**: A key that is incomplete or silently defaulted degrades the image invisibly
(the conductor only checks the key EXISTS, never completeness; `scene_author` silently defaults a
missing `logo_path` to a hardcoded taichi logo). Failing loud + human verify is the whole safety
model.

**Independent Test**: Validation FAILS LOUD (raises / nonzero) on a key missing a primary color OR a
real logo_path; the assembled lean key fed to the thin prompt assembler yields a NON-EMPTY prompt
with the primary hex present; and the lean key's prompt is BYTE-IDENTICAL to the same brand's
fat-key prompt. Free, no model calls.

**Acceptance Scenarios**:

1. **Given** an assembled key missing a primary color (or a missing/unreal logo_path), **When**
   validation runs, **Then** it FAILS LOUD with a named reason and does NOT produce a degraded prompt.
2. **Given** a complete verified lean key, **When** it is fed to the thin prompt assembler + the
   register derivation, **Then** the prompt is non-empty, contains the primary color hex (no blank
   "color  stays"), and is byte-identical to the fat-key prompt for that brand.
3. **Given** the verify gate with a `needs_review` color flag, **When** the human acknowledges every
   flag (confirm / edit / keep-flagged) and no hard-fail lock is missing, **Then** the key is written
   to `answer_keys/<brand>.json` (a kept flag recorded in it) and the logo is placed/verified under
   `brands/<brand>/`. An unacknowledged flag blocks save.

### Edge Cases

- A page mentions "color" in prose but carries no hex tokens → not suggested as the color page (US1 AS2).
- The proven `extract_colors.render_page` is 1-INDEXED (`doc[page_no - 1]`); page-finding MUST return
  1-indexed page numbers, or a 0-indexed caller renders the wrong page and returns nothing.
- OCR caption vs pixel-clustered swatch disagree → `needs_review` set + surfaced (US2 AS2). At the
  verify gate the human MUST acknowledge each flag (confirm / edit / keep-flagged); a kept flag the
  human cannot verify is written into the saved key as an honest record, never silently dropped.
- Logo file missing / `logo_path` unreal → FAIL LOUD; never silently default to the taichi logo
  (cross-brand contamination, §V).
- Missing primary color → FAIL LOUD with a named reason.
- `typography.styles` skipped (hand-authored, not PDF-extractable) → honest-null: the register
  derivation omits `font_resolved` and the font directive goes generic. No crash, lesser font control.
- A fully image-only (scanned) PDF → colors still OCR off the caption; fonts/motifs route to the VLM
  fallback (degraded, more `needs_review`); not a hard v1 requirement to perfect.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render an arbitrary brand-guideline PDF's pages to images (nothing
  ingests an arbitrary PDF today; the v3 scaffold reads pre-rendered taichi PNGs only).
- **FR-002**: A DETERMINISTIC page-finding heuristic MUST SUGGEST the color / font / brand-name spec
  pages (regex over the text layer for real hex/RGB tokens + font-name patterns), and the designer
  MUST be able to CONFIRM or correct the suggested page numbers. It MUST NOT use a model to
  auto-detect the pages. Suggested page numbers MUST be 1-indexed (the extractor footgun).
- **FR-003**: The system MUST run the PROVEN deterministic extractors (`extract_colors`,
  `extract_text_layer`) on the CONFIRMED pages to extract colors (each with a role + hex; at least
  one "primary") and the CN/EN brand names. It MUST reuse them, not reinvent color/text extraction,
  and MUST NOT build on `analyze_brand_v3.py`.
- **FR-004**: The system MUST surface provenance + `needs_review` per extracted lock (e.g. the
  delta-E OCR-vs-pixel disagreement) to the human.
- **FR-005**: The designer MUST supply the logo file at the input gate; `logo_path` MUST be written
  with a real brand-correct path or the build MUST FAIL LOUD. It MUST NEVER silently default a
  missing logo to the hardcoded taichi logo.
- **FR-006**: The system MUST assemble a LEAN answer_key carrying ONLY the fields the thin route
  consumes: `brand` / `brand_en` (+ `fields.brand_name_cn.value` / `brand_name_en.value`),
  `fields.colors.items[]` (role + hex), `logo_path`, OPTIONAL `fields.typography.styles`, and
  provenance (`source_pdf`, `verified_by`, `verified_date`). It MUST deliberately omit the
  graded / VLM / legacy fields (type/scoring tags, `_candidates_rejected` / `_provenance` /
  `_confidence`, the English fonts, `rules`, `category`, `motifs`, `tone`, `imagery_style`,
  `logo_appearance`, `slogan`).
- **FR-007**: The system MUST VALIDATE the assembled key and FAIL LOUD on a missing primary color or
  a missing / unreal `logo_path`, with a named reason. It MUST NOT silently produce a degraded prompt.
- **FR-008**: A HUMAN VERIFY GATE MUST show each extracted lock + its provenance / `needs_review`
  flag; the human edits or approves each before the key is saved (constitution §I input gate). Every
  lock carrying `needs_review` MUST be explicitly ACKNOWLEDGED before save via one of: confirm
  (looked, correct), edit (looked, fixed), or keep-flagged (looked, cannot verify; the flag is
  written into the saved key as an honest record). The save check is "every flag acknowledged," NOT
  "every flag cleared," so an honest-null flag can persist by explicit choice. Color flags MUST be
  acknowledged (a wrong hex poisons every downstream sign). This acknowledgment gate is distinct from
  the hard-fail validation (FR-007), which blocks save only on a missing primary color or `logo_path`.
- **FR-009**: On approval, the system MUST write `answer_keys/<brand>.json` AND place/verify the logo
  asset under `brands/<brand>/` (not only the JSON).
- **FR-010**: `fields.typography.styles` is NOT authored in v1 (clarified): it is left honest-null.
  The system MUST run without it (the register derivation omits `font_resolved`, the font directive
  goes generic, no crash). There is NO font-to-register-lane pairing step in the v1 onboarding path;
  the designer hand-authors `styles` in the JSON later.
- **FR-011**: The resulting key MUST be consumable by the EXISTING conductor / thin route UNCHANGED
  (the front-half adapts to the back-half's read surface, not vice versa). A new brand MUST need NO
  `kits/<brand>.json` (`--thin` bypasses the kit) and NO `config/<brand>.yaml`.
- **FR-012**: Every stage MUST FAIL LOUD or emit honest-null + a recorded note; NEVER green-on-empty
  (the v3 exit-0-on-total-failure anti-pattern is forbidden, §V).
- **FR-013**: The deterministic color / name path MUST make NO paid model calls; any VLM fallback
  (image-only fonts) MUST be outside the automated tests (human-run smoke only).
- **FR-014**: No em-dashes in any user-facing text (Output rule).

### Key Entities

- **Brand-guideline PDF**: the input the designer points at.
- **Page Suggestions**: the heuristic's output, candidate 1-indexed page numbers per lock type
  (color / font / brand-name), each confirmable / correctable by the human.
- **Extracted Locks**: colors (role + hex + provenance + `needs_review`), CN/EN brand names, and
  OPTIONAL font-to-lane pairings.
- **Logo Asset**: the designer-supplied logo file, placed/verified under `brands/<brand>/`.
- **Lean answer_key**: the consumable output (`answer_keys/<brand>.json`), only the consumed subset.
- **Validation Result**: pass, or fail-loud with a named reason (missing primary color / logo_path).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A designer onboards a brand the system has never seen, from its PDF to a human-verified
  `answer_keys/<brand>.json`, then runs the back-half on it end to end. (eye + structural)
- **SC-002**: The page-finding heuristic returns the page that actually contains hex tokens, NOT a
  page that merely mentions color. (structural, falsifiable)
- **SC-003**: Extraction on a cold brand returns colors whose hex matches the printed spec (e.g.
  chajiuxingqiu #31B4E7 / #73C900 / #94D4EB) and flips `needs_review` on an OCR-vs-pixel
  disagreement beyond threshold. (structural, falsifiable)
- **SC-004**: Validation FAILS LOUD on a key missing a primary color OR a real `logo_path`; it does
  NOT silently produce a degraded prompt. Save is also blocked while any `needs_review` lock is
  UNACKNOWLEDGED (confirm / edit / keep-flagged); a kept flag is written into the saved key.
  (structural, falsifiable)
- **SC-005**: The lean key (names + colors + logo + styles only) yields a prompt BYTE-IDENTICAL to
  the same brand's fat-key prompt (the generalization invariant / regression guard). (structural)
- **SC-006**: The whole deterministic front-half runs from ONE CLI command on a PDF path with NO
  model calls in the color / name path; the build + tests spend nothing. (process)
- **SC-007**: The resulting key runs through the EXISTING thin back-half (the one paid sign is the
  human eye-gate AFTER the build, not inside it). (eye)

> All eye-marked criteria are human-eye judgments per constitution §II; no VLM self-score counts as
> proof. Automated tests assert STRUCTURE only (the hex-token page, the extracted hex + needs_review
> flip, fail-loud validation, the byte-identical-prompt regression, the standalone CLI), never
> pixel quality.

## Assumptions

- The deterministic color / name path is model-free (the proven extractors use fitz + rapidocr + PIL,
  no LLM). Image-only (scanned) PDFs are a DEGRADED path (more `needs_review`; fonts/motifs via the
  existing VLM fallback), not a hard v1 requirement to perfect.
- The extractors are REUSED as-is; the build does NOT build on `analyze_brand_v3.py` (a hardcoded
  taichi scaffold that exits 0 on failure). The 1-indexed `render_page` footgun is respected
  (page-finding returns 1-indexed page numbers).
- `fields.typography.styles` is hand-authored human judgment; the verify gate may let the designer
  pair fonts to register lanes, but it is OPTIONAL (honest-null when skipped).
- The output key is consumable by the existing thin route UNCHANGED; new brands need no
  `kits/<brand>.json` (`--thin` bypasses the kit route) and no `config/<brand>.yaml` (legacy-only).
- WHERE the front-half lives relative to the 004 live-runner frontend (a second screen in the same
  server vs. a separate CLI/flow now, UI wired later) is an OPEN QUESTION for `/speckit-plan`,
  resolved against the 004 server shape. This spec does not assume one.
- A real cold-brand extraction (e.g. chajiuxingqiu or mahoupao) is the evidence the build reports.

## Out of Scope (v1)

- The VLM SEMANTIC layer (tone, imagery_style, motifs, category, logo_appearance / description). The
  thin route reads NONE of these; extracting them re-enters the VLM-semantic territory v3 fails at.
- Logo EXTRACTION / auto-crop from the PDF. The designer supplies the logo file; auto-crop is a later
  enhancement.
- Building on or fixing `analyze_brand_v3.py` (it MAY be cannibalized for its VLM prompts only IF the
  deferred semantic layer is ever revived, not now).
- The FAT graded-key shape: type / scoring tags, `_candidates_rejected` / `_provenance` /
  `_confidence`, the English fonts, `rules`, and `slogan` injection (the tagline-hallucination fix).
  These feed the benchmark (`score_v4.py`) or legacy authors, not generation.
- Perfecting fully image-only (scanned) brands.
- Font-to-register-lane pairing (authoring `typography.styles`) inside onboarding. v1 leaves it
  honest-null; the designer hand-authors `styles` in the JSON later (clarified).
- Relaxing benign secondary-color `needs_review` flags to advisory (skip acknowledgment). A later
  call driven by real designer use, not a v1 guess; in v1 every flag must be acknowledged.
- Wiring the front-half into the 004 frontend UI (the placement is a `/speckit-plan` decision; v1 may
  ship a CLI flow first).
