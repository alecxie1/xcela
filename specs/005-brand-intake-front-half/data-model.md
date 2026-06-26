# Phase 1 Data Model: Brand-intake Front-half

Flow: PDF -> page suggestions (human-confirmed) -> extracted locks -> human verify gate (roles +
acknowledge) -> lean answer_key -> validation -> write. "Lean" = ONLY the fields the thin route reads.

---

## Entity: Brand-guideline PDF (input)

The brand VI PDF the designer points at (a local path). May be text-layer (the proven path) or
image-only (degraded, more `needs_review`).

---

## Entity: Page Suggestions (`page_finder.suggest_pages` output)

| Field | Type | Rule |
|-------|------|------|
| `color` | list[int] | 1-INDEXED pages with REAL hex/RGB tokens, ranked by token count |
| `fonts` | list[int] | 1-INDEXED pages matching font-name patterns (minus the section-label stoplist) |
| `brand_name` | list[int] | 1-INDEXED early/title pages where the brand + EN name appear |
| `text_layer_ratio` | float | from `extract_text_layer.text_layer_ratio`; `< 0.05` => image-only (degraded) |

**Rules (falsifiable)**: a page that merely mentions "color" with no hex token is NOT in `color`. All
page numbers are 1-indexed (the `render_page` footgun). The human confirms/corrects each before extraction.

---

## Entity: Extracted Locks

- **Colors** (`extract_colors.extract_colors` records): each `{value.hex, source, confidence,
  evidence{page, dE_to_nearest_swatch, ...}, needs_review}`. ROLE is NOT set by the extractor; the
  human assigns it at the verify gate (at least one "primary").
- **Brand names**: CN + EN, read from the text layer (`page_text` / fitz), not inferred.
- **Logo asset**: the designer-supplied logo FILE (a real path), placed/verified under `brands/<brand>/`.

---

## Entity: Lean answer_key (`assemble_key.build_lean_key` output)

The consumed subset only (verified against `assemble_thin_prompt` + `derive_register`).

```json
{
  "brand": "<CN name>",
  "brand_en": "<EN name>",
  "logo_path": "/abs/path/brands/<brand>/logo.png",
  "source_pdf": "<pdf name>",
  "verified_by": "<designer>",
  "verified_date": "2026-06-26",
  "fields": {
    "brand_name_cn": { "value": "<CN name>" },
    "brand_name_en": { "value": "<EN name>" },
    "colors": { "items": [
      { "name_cn": "...", "name_en": "...", "role": "primary", "printed_html": "31B4E7", "rgb": [49,180,231],
        "needs_review": false }
    ] }
  }
}
```

**Rules (falsifiable)**:
- At least one color has `role == "primary"`.
- `logo_path` is a real, existing file path.
- `typography.styles` is ABSENT in v1 (honest-null; `derive_register` omits `font_resolved`).
- A kept-flagged color carries `needs_review: true` in the saved key (honest record).
- DELIBERATELY OMITTED: type/scoring tags, `_candidates_rejected`/`_provenance`/`_confidence`, English
  fonts, `rules`, `category`, `motifs`, `tone`, `imagery_style`, `logo_appearance`, `slogan`.

---

## Entity: Validation Result (`validate_key.validate_lean_key`)

| Outcome | Trigger |
|---------|---------|
| pass | a primary color present AND `logo_path` is a real existing file |
| FAIL LOUD (raise, named reason) | no color with `role == "primary"`, OR missing / non-existent `logo_path` |

**Rule**: validation NEVER returns a degraded-but-OK result; it raises. It is distinct from the
acknowledgment gate (which blocks save until every `needs_review` flag is acknowledged).

---

## Entity: Verify Gate state (acknowledgment, clarified)

Per `needs_review` lock, one acknowledgment: `confirm` (looked, correct) | `edit` (looked, fixed) |
`keep-flagged` (looked, cannot verify; flag written into the key). Save proceeds only when EVERY flag
is acknowledged AND validation passes. Hard-fail (no save) only on the validation triggers above.

---

## Falsifiable properties (seed the tests; constitution §III)

- `suggest_pages(synthetic_pdf)` returns the page with `#31B4E7` (1-indexed) for `color`, NOT the page
  that merely says "color".
- `validate_lean_key(key_without_primary)` raises with a named reason; `validate_lean_key(key_with_bad
  _logo_path)` raises; neither produces a degraded prompt.
- the lean key fed to `assemble_thin_prompt` (+ `derive_register`) yields a NON-EMPTY prompt with the
  primary hex present and NO blank "color  stays".
- a fat key (aia.json) stripped to the lean subset BUT KEEPING `typography.styles` yields a
  BYTE-IDENTICAL prompt vs the fat key; the real new-brand lean key (styles ABSENT) differs ONLY in
  the font-directive line (the FR-010 honest-null generic fallback), no other drift;
  changing a primary hex changes the prompt (the control).
- `extract_colors.delta_e(h, h) == 0`; `delta_e(garbled, swatch) > reconcile_threshold` (the
  `needs_review` mechanism fires deterministically).
