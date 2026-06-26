---
description: "Task list for Brand-intake Front-half (PDF to verified answer_key)"
---

# Tasks: Brand-intake Front-half (PDF to verified answer_key)

**Input**: Design documents from `specs/005-brand-intake-front-half/`

**Prerequisites**: plan.md, spec.md (clarified 2026-06-26: honest-null styles + acknowledgment gate), research.md (D1-D6), data-model.md, contracts/ (4 files), quickstart.md

**Tests**: INCLUDED. The constitution (§III Falsifiable tests only) makes falsifiable STRUCTURAL tests mandatory. Tests target the PURE new modules + a synthetic `fitz` PDF fixture; they make NO paid model calls (rapidocr is local, but the tests assert the model-FREE logic). The cold-brand OCR extraction + the one paid sign are the human-run smoke / eye-gate AFTER the build.

**Organization**: Tasks grouped by user story. One module → one falsifiable test → one commit (§VII). Run everything as `.venv/bin/python ...`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single project + a NEW `brand_intake/` package that REUSES the root extractors (`extract_colors.py`, `extract_text_layer.py`) unchanged. Self-tests as `test_*.py` at repo root. Output `answer_keys/<brand>.json` (committed) + the logo under gitignored `brands/<brand>/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Stand up the `brand_intake/` package + a synthetic-PDF test fixture helper the falsifiable tests build on.

- [X] T001 Create the `brand_intake/` package: `brand_intake/__init__.py` (empty) + a short `brand_intake/README.md` noting it is the brand-onboarding FRONT-half that REUSES `extract_colors.py` + `extract_text_layer.py` (NOT `analyze_brand_v3.py`), outputs a LEAN `answer_keys/<brand>.json` the existing thin route consumes unchanged, and is stdlib + the extractors' existing deps (no new dep). Confirm `brand_intake/` is git-tracked.
- [X] T002 [P] Add a synthetic-PDF fixture helper `tests_support/make_pdf.py` (stdlib + `fitz`): build a small multi-page PDF in a temp dir from page text (e.g. page 1 "color palette" with NO hex, page 2 "主色 #31B4E7", a font page "汉仪旗黑 / Helvetica"). Used by the page-finder + (optionally) extractor tests; no external file, no model.

**Checkpoint**: `brand_intake/` exists; tests can synthesize a PDF without an external asset.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm STEP ZERO (the reuse surface the whole feature stands on) before building the body. No new logic.

**⚠️ CRITICAL**: The lean schema + byte-identical guard depend on the verified read surface; the page-finder depends on the 1-indexed footgun.

- [X] T003 Write `tests_support/verify_reuse.py` (a one-shot STEP-ZERO check, no paid calls): assert `extract_colors.render_page` is 1-indexed (`doc[page_no_1idx - 1]`), `extract_colors.extract_colors` + `delta_e` import and run on the synthetic PDF, `extract_text_layer.page_text` / `text_layer_ratio` import, and `harness.scene_author.assemble_thin_prompt` + `register.derive_register.derive_register` import. Documents the exact reused surface so a drift in any of them fails loudly here, not deep in a later task.

**Checkpoint**: The reused organs are confirmed present + shaped as the plan assumes.

---

## Phase 3: User Story 1 - Page-finding suggests, the human confirms (Priority: P1) 🎯 MVP

**Goal**: A deterministic heuristic over the text layer SUGGESTS the color / font / brand-name pages (1-indexed); the human confirms.

**Independent Test**: `test_page_finder.py` green — over a synthetic PDF where page 1 says "color palette" (no hex) and page 2 prints `#31B4E7`, `suggest_pages` returns page 2 (1-indexed) for `color`, NOT page 1. Free, no model calls.

### Tests for User Story 1

- [X] T004 [P] [US1] Write `test_page_finder.py`: build the synthetic PDF (T002 helper); assert `2 in suggest_pages(pdf)["color"]` (the hex-token page, 1-indexed) AND `1 not in suggest_pages(pdf)["color"]` (the color-mention-only page is explicitly ABSENT, the falsifiable negative); assert `fonts` contains the font-name page; assert all returned page numbers are 1-indexed; assert `text_layer_ratio` is reported. MUST FAIL before T005.

### Implementation for User Story 1

- [X] T005 [US1] Implement `brand_intake/page_finder.py` `suggest_pages(pdf_path) -> {color, fonts, brand_name, text_layer_ratio}` per `contracts/page-finder.md`: scan each page's text layer (`extract_text_layer.page_text` / fitz), rank color pages by real hex/RGB token count (reuse the `extract_colors._HEX_RE` / `_RGB_RE` shapes), font pages by `extract_text_layer._CJK_FONT_RE` / `_EN_FONT_RE` minus the stoplist, brand-name by early/title pages. PURE, model-free, 1-INDEXED (the footgun). `test_page_finder.py` passes.

**Checkpoint**: The hardcoded `BRANDS` page dict is replaced by discovery the human confirms. MVP.

---

## Phase 4: User Story 2 - Deterministic extraction on the confirmed pages (Priority: P1)

**Goal**: The proven extractors run on the confirmed pages: colors with hex + `needs_review`, brand names from the text layer; provenance surfaced. (Reuse, do not reinvent.)

**Independent Test**: extraction on a cold brand returns colors whose hex matches the printed spec and flips `needs_review` on OCR-vs-pixel disagreement beyond threshold. The model-free PART (the `delta_e` reconcile mechanism) is asserted in a free test; the real-OCR hex match is the human smoke (T015).

### Tests for User Story 2

- [X] T006 [P] [US2] Add to `test_brand_key.py` the model-free reconcile assertions: `extract_colors.delta_e(h, h) == 0`; `delta_e(garbled_hex, swatch) > reconcile_threshold` (so the `needs_review` mechanism fires deterministically); a `read_brand_names(pdf, name_pages)` helper returns the CN/EN strings from the synthetic PDF's text layer (not inferred). MUST FAIL before T007.

### Implementation for User Story 2

- [X] T007 [US2] Implement `brand_intake/extract.py` thin REUSE wrappers (do NOT reinvent): `extract_brand_colors(pdf, color_pages_1idx)` delegates to `extract_colors.extract_colors` (returns hex records + `needs_review`, role NOT yet assigned) and `read_brand_names(pdf, name_pages_1idx)` reads CN/EN from `extract_text_layer.page_text`. Honest-null + note on empty (never green-on-empty). The reconcile/name assertions in T006 pass.

**Checkpoint**: Colors + names are extracted from the confirmed pages with provenance + needs_review; nothing reinvented.

---

## Phase 5: User Story 3 - Assemble, validate-loud, verify, write a consumable key (Priority: P1)

**Goal**: Assemble the LEAN key, VALIDATE LOUD (primary color + real logo_path), run the acknowledgment-gated human verify, write `answer_keys/<brand>.json` + place the logo. The key runs the EXISTING thin route unchanged.

**Independent Test**: `test_brand_key.py` green — `validate_lean_key` RAISES on a missing primary / logo_path; the lean key yields a NON-EMPTY thin prompt with the primary hex; a fat key stripped to lean WITH styles kept yields a BYTE-IDENTICAL prompt vs the fat key, and the styles-absent key differs only in the font-directive line (SC-005, two-part).

### Tests for User Story 3

- [X] T008 [P] [US3] Write `test_brand_key.py`: (a) `validate_lean_key(key_without_primary)` raises with a named reason; (b) `validate_lean_key(key_with_missing_or_unreal_logo_path)` raises; (c) `build_lean_key(...)` then `assemble_thin_prompt` (+ `derive_register`) yields a NON-EMPTY prompt containing the primary hex and NO blank "color  stays"; (d) REGRESSION GUARD (two parts, per the SC-005 probe finding — PIN the register profile: subfields = held-for-photos / formality 2 / playfulness 8 / logo omit / expressive, NO reference, which yields event_prop + flexes `font:rounded`): (d1) strip `answer_keys/aia.json` to the lean subset BUT KEEP `typography.styles` → BYTE-IDENTICAL prompt vs the fat key (proves the dropped graded/legacy fields are zero-effect), plus a control where changing a primary hex CHANGES the prompt; (d2) the new-brand lean key with styles ABSENT differs from the fat key ONLY in the font-directive line and that line is the generic fallback (e.g. "(rounded library family)") — assert the diff is exactly that one line (the FR-010 honest-null, no other drift). MUST FAIL before T009/T010.

### Implementation for User Story 3

- [X] T009 [P] [US3] Implement `brand_intake/assemble_key.py` `build_lean_key(brand, brand_en, names, color_items_with_roles, logo_path, source_pdf, verified_by, verified_date) -> dict` per `contracts/lean-key-schema.md`: the CONSUMED subset only (names + `fields.colors.items[]` with roles + `printed_html`/`rgb`, top-level `logo_path`, provenance); `typography.styles` ABSENT (honest-null); a kept-flagged color carries `needs_review: true`. Omit all graded/VLM/legacy fields.
- [X] T010 [P] [US3] Implement `brand_intake/validate_key.py` `validate_lean_key(key)` per `contracts/validation.md`: RAISE with a named reason on no `role == "primary"` color OR a missing / non-existent `logo_path` file. Never return a degraded-but-OK key. T008 assertions (a)-(d) pass.
- [X] T011 [US3] Implement `brand_intake/intake.py` CLI orchestrator per `contracts/cli-contract.md`: `--pdf --brand --verified-by [--pages-color --pages-name --logo --no-gate]`; flow = suggest_pages → human CONFIRM pages → extract (US2 wrappers) → supply+place logo under `brands/<brand>/` → VERIFY gate (assign color roles, ACKNOWLEDGE every `needs_review` via confirm/edit/keep-flagged) → `build_lean_key` → `validate_lean_key` (fail loud) → write `answer_keys/<brand>.json`. `--no-gate` runs the deterministic path non-interactively (supplied roles/pages) WITHOUT weakening validation. No em-dashes in any prompt/message.
- [X] T012 [US3] Wire the acknowledgment gate falsifiably: in `test_brand_key.py` (or `test_intake_gate.py`) assert that the gate logic blocks save while a `needs_review` lock is UNACKNOWLEDGED, and that a `keep-flagged` acknowledgment writes `needs_review: true` into the assembled key (honest record). Test the gate decision function directly (pure), not via stdin.

**Checkpoint**: A PDF becomes a human-verified lean key that fails loud on missing locks and drives the existing thin route. All three P1 stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update durable context, run the free surfaces, then the human-run cold-brand + paid smoke.

- [X] T013 [P] Update `SYSTEM_MAP.md` + `CLAUDE.md` in the same commit that makes them stale (§VII): the brand-intake front-half is built (PDF → page-finder → reused extractors → acknowledgment-gated verify → lean key); reuse of the deterministic extractors (NOT v3); the validate-loud landmine containment (logo_path); placement = standalone CLI v1 (UI later); the deferred VLM semantic layer + font-pairing.
- [X] T014 [P] Run the free structural suite (`test_page_finder`, `test_brand_key`, `tests_support/verify_reuse`) and confirm the prior suites stay green (001/002/003/004 + the thin route via `test_conductor`/`test_render_and_scrub`). Paste real output. No paid calls.
- [ ] T015 The human-run smoke (SC-003/SC-007, NOT automated): run `brand_intake/intake.py --pdf <cold_brand_VI.pdf> --brand <id> --verified-by "<you>"` on a real never-seen brand; confirm the extracted hex matches THAT brand's printed spec (for chajiuxingqiu specifically: #31B4E7 / #73C900 / #94D4EB; for any other brand, match its own printed hexes) and a garbled read flips needs_review; then run the lean key through the EXISTING thin back-half (`conductor.py --brand <id> --thin --no-approve --inputs <single_sign>.json`) and judge the sign by eye (§II). The cold-brand OCR + the one paid sign are the human's gate AFTER the build. Record the verdict in `SYSTEM_MAP.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup (uses the fixture). Confirms the reuse surface; blocks nothing hard but should run first to catch drift early.
- **US1 (Phase 3)**: After Setup. Independent (pure `page_finder`). The MVP.
- **US2 (Phase 4)**: After Setup. The extract wrappers + reconcile test are independent of US1 (parallelizable).
- **US3 (Phase 5)**: After US2 (consumes the extracted color records + names) and Setup. `assemble_key` (T009) + `validate_key` (T010) are independent pure modules (parallel); `intake.py` (T011) needs page_finder (US1) + the extract wrappers (US2) + assemble/validate (T009/T010).
- **Polish (Phase 6)**: After US1+US2+US3.

### Within Each User Story

- The test task ([P], test-first) is written and MUST FAIL before its implementation tasks.
- US3: `test_brand_key` (T008) before `assemble_key` (T009) + `validate_key` (T010); both before `intake.py` (T011); the gate test (T012) closes the story.
- Commit after each task (§VII).

### Parallel Opportunities

- T002 (fixture) is [P] vs T001.
- The story test files — T004 (page_finder), T006 (reconcile/names), T008 (brand_key) — are all [P] and can be drafted together.
- `page_finder.py` (T005) ∥ `extract.py` (T007) ∥ `assemble_key.py` (T009) ∥ `validate_key.py` (T010) are different files.
- T013 ∥ T014 in Polish (docs vs running self-tests).

---

## Parallel Example: kicking off after Setup

```bash
# The independent test files first (each MUST FAIL), then implement each pure module:
Task: "T004 Write test_page_finder.py (US1)"
Task: "T006 Write the reconcile/name assertions (US2)"
Task: "T008 Write test_brand_key.py (US3)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup (`brand_intake/` + the synthetic-PDF fixture).
2. Phase 2 Foundational (confirm the reuse surface).
3. Phase 3 US1 (`page_finder` + test): discovery replaces the hardcoded page dict, validated free.
4. **STOP and VALIDATE**: `test_page_finder` green — the hex-token page is found, not the color-mention page, 1-indexed.

### Incremental Delivery

1. Setup + Foundational → `brand_intake/` + confirmed reuse surface.
2. US1 → page-finding (MVP).
3. US2 → deterministic extraction wrappers (reuse the proven organs).
4. US3 → assemble + validate-loud + acknowledgment-gated verify + write the lean key.
5. Polish → durable docs, free suite green, then the human cold-brand + paid eye-gate.

### Notes

- [P] = different files, no incomplete dependencies.
- NO paid model calls in ANY automated test (§ Cost discipline). rapidocr is local, but the tests assert the model-FREE logic (text-layer page-finding, schema assembly, fail-loud validation, the `delta_e` threshold). Only T015 (cold-brand OCR + the one paid sign) is human-run, eye-validated (§II).
- REUSE the proven extractors (`extract_colors`, `extract_text_layer`); do NOT build on `analyze_brand_v3.py`; do NOT change the back-half (the front-half adapts to the read surface, §VI/§VII).
- Fail loud or honest-null + note at every stage; never green-on-empty (the v3 anti-pattern). `logo_path` missing → fail loud (never the silent taichi default).
- 1-INDEXED page numbers everywhere (the `extract_colors.render_page` footgun).
- No em-dashes in any user-facing text (Output rule).
