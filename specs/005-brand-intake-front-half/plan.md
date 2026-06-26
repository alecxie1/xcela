# Implementation Plan: Brand-intake Front-half (PDF to verified answer_key)

**Branch**: `005-brand-intake-front-half` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-brand-intake-front-half/spec.md`

## Summary

Onboarding a NEW brand has no working path: `analyze_brand_v3.py` is a hardcoded taichi scaffold that
exits 0 on failure. The working capability is the DETERMINISTIC extractors (`extract_colors.py`,
`extract_text_layer.py`, verified this session: `extract_colors.extract_colors(pdf, color_pages_1idx)`
returns hex records with `needs_review` on OCR-vs-pixel disagreement; both have hardcoded `BRANDS`
dicts and NO PDF page-finding). This feature builds the BODY around those proven organs: a PDF in, a
DETERMINISTIC page-finding heuristic the human confirms, the extractors on the confirmed pages, a
human VERIFY gate, and a LEAN verified `answer_keys/<brand>.json` out that the EXISTING thin route
consumes unchanged.

Placement decision (the brief's flagged open question, resolved here): v1 ships a STANDALONE CLI flow
(matches the agent-free standalone ethos, no UI dependency, fastest to the designer), built from PURE
modules (page-finder, lean-key assembler, validation) plus a thin interactive CLI verify gate. A
future 004-style web screen can wrap the same pure modules, so the UI is a pure addition, not a
rework. The verify gate is ACKNOWLEDGMENT-gated (clarified): every `needs_review` lock is confirmed /
edited / kept-flagged before save; hard-fail (no save) only on a missing primary color or a missing /
unreal `logo_path`. `typography.styles` is left honest-null in v1 (no font-pairing step).

## Technical Context

**Language/Version**: Python 3.11 (`.venv`).

**Primary Dependencies**: REUSE the proven extractors and their existing deps: PyMuPDF (`fitz`),
`rapidocr_onnxruntime` (a LOCAL OCR model, not a paid API), Pillow. stdlib for the new page-finder,
lean-key assembler, validation, and CLI gate. No new dependency, NO paid model calls in the color /
name path.

**Storage**: Files. Output `answer_keys/<brand>.json` (committed brand data) + the logo asset under
gitignored `brands/<brand>/`. Input is a brand-guideline PDF (a local path).

**Testing**: Falsifiable STRUCTURAL self-tests in the `test_*.py` style (stdlib + a tiny synthetic
`fitz` PDF fixture, no external file, no model). NO paid model calls in any test. The cold-brand OCR
extraction + the one paid sign are the human-run smoke / eye-gate AFTER the build.

**Target Platform**: Linux CLI (WSL2). A standalone CLI flow on a PDF path.

**Project Type**: Single project + a new `brand_intake/` package that REUSES the root extractors and
adapts to the back-half's read surface (it does not change the back-half).

**Performance Goals**: Not latency-bound. The deterministic path (fitz text + rapidocr) is local and
fast; no paid call.

**Constraints**: REUSE `extract_colors.py` + `extract_text_layer.py`; do NOT build on
`analyze_brand_v3.py`. The 1-indexed `render_page` footgun (`doc[page_no_1idx - 1]`) MUST be respected
(page-finding returns 1-indexed page numbers). Every stage FAILS LOUD or emits honest-null + a note,
NEVER green-on-empty. `logo_path` MUST be a real path or fail loud (never the silent taichi default
`scene_author` falls back to). The output key MUST be consumable by the EXISTING conductor / thin
route UNCHANGED (no `kits/<brand>.json`, no `config/<brand>.yaml` needed for a new brand). No
em-dashes in user-facing text.

**Scale/Scope**: v1 = the deterministic color / name path + the human verify gate, for a brand with a
text-layer PDF. Image-only (scanned) PDFs are a degraded path (more `needs_review`), not perfected.
The VLM semantic layer and logo auto-crop are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | Page-finding is a DETERMINISTIC heuristic that SUGGESTS; the human CONFIRMS the pages and VERIFIES every lock (the input gate). No LLM auto-detects pages or judges the key (the v3 silent-judgment disease is rejected). | PASS |
| II. Ground truth = the eye | The front-half tests assert STRUCTURE only; the cold-brand extraction + the one paid sign are the human's smoke / eye-gate. No VLM PASS counts as proof. | PASS |
| III. Falsifiable tests only | Page-finder returns the hex-token page (not a color-mention page); validation FAILS LOUD on a missing primary color / logo_path; the lean key yields a prompt BYTE-IDENTICAL to the fat key. Each fails a wrong build. | PASS |
| IV. Generalize, do not hand-tune | Reuse the deterministic extractors (not the taichi-wired v3); the lean key is the CONSUMED subset (no AIA fat shape); no brand literals in the new code. | PASS |
| V. Honest nulls, never invented | Every stage fails loud or emits honest-null + a note (the v3 exit-0-on-failure anti-pattern is forbidden). `logo_path` missing -> fail loud (no silent taichi default). `needs_review` -> acknowledged or kept-flagged (written into the key), never green-on-empty. | PASS |
| VI. Reconciliation per-dimension | Untouched. The key feeds `derive_register` / `assemble_thin_prompt` unchanged; the front-half adapts to that read surface, it does not change reconciliation. | PASS |
| VII. Repo is durable; thin / reuse | Reuse the proven extractors; the output key is consumed by the existing back-half UNCHANGED; one-module-one-test-one-commit; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: The deterministic color / name path is model-free (rapidocr is local). No paid
generation in any test; the cold-brand OCR smoke + the one paid sign are human-run after the build. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/005-brand-intake-front-half/
├── spec.md              # Feature spec (clarified 2026-06-26: honest-null styles + acknowledgment gate)
├── plan.md              # This file
├── research.md          # Phase 0: page-finding, lean schema, the landmines, placement decision
├── data-model.md        # Phase 1: PDF, page suggestions, extracted locks, lean key, validation
├── contracts/
│   ├── lean-key-schema.md      # the consumed-subset answer_key (verified vs the thin route reads)
│   ├── page-finder.md          # suggest_pages heuristic contract (1-indexed)
│   ├── validation.md           # fail-loud rules + the acknowledgment gate
│   └── cli-contract.md         # the intake CLI + verify gate + reuse points
├── quickstart.md        # Phase 1: free structural validation + the cold-brand + paid smoke
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
brand_intake/                  # NEW package: the BODY around the proven extractor ORGANS
├── __init__.py
├── page_finder.py             # PURE: suggest_pages(pdf) -> {color/fonts/brand_name: [1-indexed pages]}
│                              #   regex over the TEXT LAYER for real hex tokens + font-name patterns.
│                              #   NOT a model. Returns 1-indexed (the render_page footgun).
├── assemble_key.py            # PURE: build_lean_key(brand, names, color_records+roles, logo_path,
│                              #   source_pdf) -> the lean answer_key dict (consumed subset only).
├── validate_key.py            # PURE: validate_lean_key(key) -> raises with a NAMED reason on a
│                              #   missing primary color / missing-or-unreal logo_path.
└── intake.py                  # CLI orchestrator: pdf -> suggest pages -> human CONFIRM -> run the
                               #   extractors -> human VERIFY gate (assign roles, acknowledge flags) ->
                               #   validate (fail loud) -> write answer_keys/<brand>.json + place logo.

extract_colors.py              # REUSED unchanged (extract_colors, delta_e, render_page [1-indexed]).
extract_text_layer.py          # REUSED (text_layer_ratio, page_text, parse_fonts). The hardcoded
                               #   BRANDS dict is NOT used by the new path; page_finder replaces it.

test_page_finder.py            # NEW: synthetic fitz PDF -> suggest_pages returns the hex-token page
                               #   (not the color-mention page); 1-indexed; font-page detection.
test_brand_key.py              # NEW: assemble + validate (fail-loud on missing primary / logo) +
                               #   the lean key -> non-empty thin prompt w/ primary hex + BYTE-IDENTICAL
                               #   lean-vs-fat prompt (regression guard) + the reconcile delta_e threshold.
```

**Structure Decision**: A new `brand_intake/` package holds the BODY; the proven extractors stay at
the repo root and are REUSED unchanged. The genuinely new capability is three PURE modules
(`page_finder`, `assemble_key`, `validate_key`) so every falsifiable test runs free (no model, no
external PDF), plus `intake.py` as the thin interactive CLI gate. The 1-indexed `render_page` footgun
is respected by `page_finder` returning 1-indexed pages. Nothing in the back-half changes: the output
key adapts to what `assemble_thin_prompt` + `derive_register` already read, and the byte-identical
test guards that. The `scene_author` silent-logo-default landmine is contained by `validate_key`
failing loud before the key is ever saved (the front-half validates completeness the conductor never
did).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
