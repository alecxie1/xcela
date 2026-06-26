# Contract: lean answer_key (the consumed subset)

The output `answer_keys/<brand>.json`. Carries ONLY what the thin route reads (verified against
`assemble_thin_prompt` + `derive_register`). Deliberately THINNER than AIA's fat (graded) key.

## Consumed fields (MUST be present / correct)

| Field | Read by | Rule |
|-------|---------|------|
| `brand`, `brand_en` (top-level) | conductor / provenance | the brand's CN + EN name |
| `fields.brand_name_cn.value`, `fields.brand_name_en.value` | `assemble_thin_prompt._brand_field_value` | the names injected into the prompt |
| `fields.colors.items[]` `{name_cn, name_en, role, printed_html, rgb}` | `assemble_thin_prompt` (color lock lines) | >= 1 with `role == "primary"`; `printed_html` is the hex (no `#`) |
| `logo_path` (top-level, REAL path) | `scene_author` (`brand_key.get("logo_path", LOGO_PATH)`) | REQUIRED; a real file or the build fails loud (never the taichi default) |
| `source_pdf`, `verified_by`, `verified_date` | provenance | human-useful, cheap |

## Optional / honest-null

| Field | Rule |
|-------|------|
| `fields.typography.styles` | OPTIONAL; ABSENT in v1 (no font-pairing step). Absent => `derive_register` omits `font_resolved`, the font directive goes generic, no crash. |
| `fields.colors.items[].needs_review` | present + `true` when a color was kept-flagged at the verify gate (honest record) |

## Deliberately OMITTED (proven zero effect on the image)

`type` / `scoring` tags on fields (feed the benchmark `score_v4.py`), `typography._candidates_rejected`
/ `_provenance` / `_confidence`, the English fonts, `rules`, `category`, `motifs`, `tone`,
`imagery_style`, `logo_appearance`, `slogan` (read but NOT injected, the tagline-hallucination fix).

## Rules (falsifiable)

1. The lean key fed to `assemble_thin_prompt` (+ `derive_register`) yields a NON-EMPTY prompt with the
   primary color hex present (no blank "color  stays").
2. Generalization invariant, TWO parts (a probe confirmed AIA's event-prop profile flexes
   `font:rounded`, so `typography.styles` is consumed via the font directive): (a) a fat key stripped
   to this subset BUT KEEPING `typography.styles` yields a BYTE-IDENTICAL prompt vs the fat key
   (the dropped graded/legacy fields are zero-effect); a primary-hex change DOES change the prompt
   (control). (b) the real new-brand lean key (styles ABSENT) differs ONLY in the font-directive line,
   which is the generic fallback (the FR-010 honest-null) -- no other drift.
3. A new brand needs NO `kits/<brand>.json` (`--thin` bypasses the kit) and NO `config/<brand>.yaml`.
