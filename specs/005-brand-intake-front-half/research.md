# Phase 0 Research: Brand-intake Front-half

All decisions are grounded in the ACTUAL code (read this session): `extract_colors.py`
(`extract_colors(pdf, color_pages_1idx)` -> hex records with `needs_review`; `render_page` is
1-INDEXED `doc[page_no_1idx - 1]`; `delta_e`; no role assigned), `extract_text_layer.py`
(`text_layer_ratio`, `page_text(pdf, pages_1idx)`, `parse_fonts`; hardcoded `BRANDS` dict, NO
page-finding), `scene_author.assemble_thin_prompt` (reads `fields.brand_name_cn/en.value` +
`fields.colors.items[].{printed_html,name_cn,name_en,role}` + top-level `logo_path` defaulting to the
taichi `LOGO_PATH`), and `derive_register` (anchors `primary_color`; reads `typography.styles` ->
`font_resolved`).

---

## D1. Page-finding heuristic (FR-002, the genuinely new organ)

**Decision**: A new PURE `brand_intake/page_finder.py` `suggest_pages(pdf) -> {color: [1-idx...],
fonts: [1-idx...], brand_name: [1-idx...]}`. It scans the TEXT LAYER per page (via
`extract_text_layer.page_text` / fitz `get_text`) and ranks:
- color page(s): pages containing REAL hex/RGB tokens (the same `_HEX_RE` / `_RGB_RE` shape
  `extract_colors` already uses), ranked by token count. A page that merely says "color" with no hex
  token is NOT suggested.
- font page(s): pages matching the CJK/EN font-name patterns (`extract_text_layer._CJK_FONT_RE` /
  `_EN_FONT_RE`), minus the section-label stoplist.
- brand-name page(s): the early/title page(s) (the brand name + EN name appear up front).
All suggestions are 1-INDEXED (the `render_page` footgun). The human CONFIRMS or corrects each.

**Rationale**: This replaces the hardcoded `BRANDS` dict with discovery, while keeping the human at
the input gate. The hex-token vs color-mention distinction is the proven signal (the color page is
the one with real hex tokens). Reusing the extractors' own regexes keeps the heuristic consistent
with what the extractor will then parse. Deterministic, no model (the v3 auto-detect disease avoided).

**Falsifiable test**: a synthetic 3-page `fitz` PDF where page 1 says "color palette" (no hex) and
page 2 prints "#31B4E7" -> `suggest_pages` returns page 2 (1-indexed) for color, not page 1.

**Alternatives considered**: a VLM page classifier (REJECTED, §IV/§I, the v3 failure); dumb full-doc
scan (REJECTED, unreliable, no human signal); the existing hardcoded `BRANDS` dict (REJECTED, it is
exactly the no-page-finding gap).

---

## D2. The lean answer_key schema (FR-006, verified against the read surface)

**Decision**: `brand_intake/assemble_key.py` builds ONLY the consumed subset (confirmed by reading
`assemble_thin_prompt` + `derive_register`):
- top-level `brand`, `brand_en`, `logo_path` (REAL path), `source_pdf`, `verified_by`, `verified_date`
- `fields.brand_name_cn.value`, `fields.brand_name_en.value`
- `fields.colors.items[]` each `{name_cn, name_en, role, printed_html (hex no #), rgb}`; at least one
  `role == "primary"` (role assigned by the human at the verify gate; `extract_colors` does NOT assign it)
- `fields.typography.styles` OPTIONAL, left absent in v1 (clarified; honest-null)
Deliberately OMITTED: `type`/`scoring` tags, `_candidates_rejected`/`_provenance`/`_confidence`, the
English fonts, `rules`, `category`, `motifs`, `tone`, `imagery_style`, `logo_appearance`, `slogan`.

**Rationale**: Proven empirically (the brief) and re-verified here: `assemble_thin_prompt` reads only
names + `colors.items[].printed_html/role/name_*`; `derive_register` anchors `primary_color` + reads
`typography.styles`. Nothing else has a code path into the thin prompt. The new key is deliberately
THINNER than AIA's (AIA is fat because it was GRADED).

**Probe finding (run this session, the F1 correction)**: `typography.styles` is NOT a free drop. A
`derive_register` probe on AIA showed the realistic event-prop profile (held-for-photos, formality 2,
playfulness 8, logo omit, expressive, no reference) flexes `font:rounded`, so `font_resolved` is
resolved from `typography.styles` and `assemble_thin_prompt` injects the named family
(`汉仪元隆黑 ... 汉仪元隆黑-75简`). A lean key WITHOUT styles emits the generic fallback
"(rounded library family)" on that one line. So byte-identity is two claims, not one.

**Falsifiable test (the regression guard, TWO parts; PIN the profile above)**: (a) strip aia.json to
the lean subset BUT KEEP `typography.styles` -> `assemble_thin_prompt` (+ `derive_register`) produces
a BYTE-IDENTICAL prompt vs the fat key (proves the dropped graded/legacy fields are zero-effect);
control: a primary-hex change MUST change the prompt. (b) the real new-brand lean key (styles ABSENT)
differs from the fat key ONLY in the font-directive line, which is the generic fallback (the FR-010
honest-null; contained, no other drift).

---

## D3. The two landmines, contained by validation (FR-005 / FR-007)

**Finding (verified)**: (a) `scene_author` reads `brand_key.get("logo_path", LOGO_PATH)` at 3 sites,
defaulting a missing `logo_path` to the hardcoded taichi logo and silently feeding it to gpt
(cross-brand contamination). (b) The conductor only checks the answer_key `.exists()`, never
completeness; a partial key degrades silently (a blank hex becomes "primary brand color  stays").

**Decision**: `brand_intake/validate_key.py` `validate_lean_key(key)` FAILS LOUD (raises a named
error) BEFORE the key is saved on: no color with `role == "primary"`, or a missing / non-existent
`logo_path` file. The front-half validates the COMPLETENESS the back-half never does; it does NOT
change `scene_author` (the front-half adapts to the back-half, §VI/§VII).

**Rationale**: The safety model is "a complete, human-verified key cannot be saved partial," so the
silent-logo-default and blank-hex paths are never reached. Falsifiable: a key missing a primary color
OR a real `logo_path` raises with a named reason and does NOT produce a degraded prompt.

**Alternatives considered**: harden `scene_author` to fail on a missing logo (REJECTED for v1 -- that
edits the back-half; the front-half guarantee is sufficient and keeps the read surface unchanged; a
back-half hardening can be a separate later spec).

---

## D4. The verify gate: acknowledgment, not clearing (FR-008, clarified)

**Decision**: `intake.py` runs an interactive CLI verify gate that shows each extracted lock + its
provenance / `needs_review`, lets the human assign color roles (mark the primary), and requires every
`needs_review` lock to be explicitly ACKNOWLEDGED before save: confirm / edit / keep-flagged. A
kept-flagged lock writes its `needs_review` into the saved key (an honest record). The save proceeds
only when (every flag acknowledged) AND (`validate_lean_key` passes). Hard-fail (no save) only on a
missing primary color / `logo_path`.

**Rationale**: The clarification: block on acknowledgment, not on clearing, so honest-null persists by
explicit choice; color flags must be acknowledged (a wrong hex poisons every sign). This is the input
gate (§I) + honest nulls (§V).

**Alternatives considered**: advisory (save anyway) -- REJECTED (a wrong hex must be looked at);
blocking-until-cleared -- REJECTED (stalls on a benign flag the human cannot resolve).

---

## D5. Placement: a standalone CLI flow for v1 (the brief's open question)

**Decision**: v1 ships a STANDALONE CLI flow (`brand_intake/intake.py --pdf <path> --brand <id>`), NOT
a 004 web screen. The page-finder, assembler, and validator are PURE modules so a future 004-style
screen can wrap them unchanged (the 004 pattern: pure logic + a thin gate).

**Rationale**: Matches the agent-free standalone ethos and gets the designer onboarding brands
fastest, with no UI dependency. Building the UI now would couple this to the 004 server before the
deterministic path is proven on real cold brands. Keeping the modules pure makes the UI a PURE
ADDITION later (its own spec), not a rework.

**Alternatives considered**: a second screen in the 004 live-runner server now (DEFERRED -- valuable,
but premature; wire the UI after the CLI path is validated on real brands).

---

## D6. No paid calls; rapidocr is local (FR-013 / cost discipline)

**Decision**: The deterministic color / name path uses fitz + rapidocr (a LOCAL ONNX model) + PIL --
no paid API. Automated tests target the PURE new modules (page_finder, assemble_key, validate_key) +
`extract_colors.delta_e` (the reconcile math) over a synthetic PDF, so they spend nothing and are not
flaky on OCR. The real cold-brand OCR extraction is a human-run smoke; any VLM fallback (image-only
fonts) is outside the automated tests.

**Rationale**: rapidocr is free/local, but OCR over a synthetic render is non-deterministic, so the
falsifiable tests assert the model-FREE logic (text-layer page-finding, schema assembly, fail-loud
validation, delta_e threshold). The OCR organs are already proven; the new BODY is what is tested.

---

## Reuse summary (verified against code)

| Existing capability | File | Reused for |
|---------------------|------|-----------|
| `extract_colors(pdf, color_pages_1idx)` -> hex records + `needs_review` | `extract_colors.py` | D1/D4 color extraction (role added by the human) |
| `delta_e`, `_HEX_RE` / `_RGB_RE` (the reconcile + hex shape) | `extract_colors.py` | D1 page-finding regex, D6 reconcile test |
| `render_page` (1-INDEXED) | `extract_colors.py` | rendering the confirmed pages (footgun respected) |
| `page_text`, `text_layer_ratio`, `parse_fonts`, `_CJK_FONT_RE` | `extract_text_layer.py` | D1 page-finding + font/name reads |
| `assemble_thin_prompt` + `derive_register` read surface | `harness/scene_author.py` + `register/` | D2 lean schema + the byte-identical guard |
| existing fat key (aia.json) | `answer_keys/` | D2 byte-identical regression fixture |

| Genuinely NEW | Why nothing existing covers it |
|---------------|-------------------------------|
| `brand_intake/page_finder.py` | The extractors have hardcoded `BRANDS` dicts; no PDF page-discovery exists |
| `brand_intake/assemble_key.py` | No lean-key assembler exists (v3 wrote a fat taichi key) |
| `brand_intake/validate_key.py` | The conductor only checks `.exists()`, never completeness |
| `brand_intake/intake.py` | No PDF-to-verified-key flow exists (v3 is a hardcoded scaffold) |
