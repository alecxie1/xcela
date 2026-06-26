# Contract: the intake CLI (`brand_intake/intake.py`)

A STANDALONE CLI flow (v1 placement decision). Built from the PURE modules + a thin interactive verify
gate, so a future 004-style web screen can wrap the same modules unchanged.

## Command

```
.venv/bin/python brand_intake/intake.py --pdf <path/to/VI.pdf> --brand <brand_id> \
    --verified-by "<designer>" [--pages-color 24,25] [--pages-name 1] [--logo <path>] [--no-gate]
```

## Flow (stages, each fail-loud or honest-null + note, never green-on-empty)

1. Render + `suggest_pages(pdf)` -> suggested 1-indexed color / font / brand-name pages.
2. Human CONFIRMS / corrects the suggested page numbers (or `--pages-*` overrides for non-interactive).
3. Run the PROVEN extractors on the confirmed pages: `extract_colors.extract_colors(pdf, color_pages)`
   (hex records + `needs_review`) + brand names from the text layer.
4. Designer SUPPLIES the logo (`--logo` or a gate prompt); it is placed/verified under `brands/<brand>/`.
5. Human VERIFY gate: show each lock + provenance / `needs_review`; assign color ROLES (mark the
   primary); ACKNOWLEDGE every flag (confirm / edit / keep-flagged). `--no-gate` (test/batch) skips the
   interactive gate using the supplied roles/pages and still runs validation.
6. `assemble_key.build_lean_key(...)` -> the lean key; `validate_key.validate_lean_key(...)` FAILS LOUD
   on a missing primary / logo_path.
7. On pass + all-acknowledged: write `answer_keys/<brand>.json` and place the logo under `brands/<brand>/`.

## Reuse (do NOT reinvent / do NOT change)

- Extractors: `extract_colors` (1-indexed `render_page`), `extract_text_layer` (`page_text`,
  `parse_fonts`). REUSED unchanged.
- The output key is consumed by the EXISTING conductor / thin route UNCHANGED. The front-half does NOT
  edit `scene_author` / `derive_register`; it validates completeness they do not.

## Test surfaces (free; cost discipline)

```
.venv/bin/python test_page_finder.py    # synthetic PDF -> hex-token page (1-indexed), not color-mention
.venv/bin/python test_brand_key.py      # assemble + fail-loud validate + non-empty prompt + byte-identical
```
NO paid model calls in any test (rapidocr is local; the new modules are model-free). The cold-brand OCR
extraction (real PDF) + the one paid sign are the human-run smoke / eye-gate AFTER the build.

## Rules

1. The whole deterministic flow runs from ONE CLI command on a PDF path with NO paid model calls.
2. `--no-gate` makes the deterministic pipeline non-interactive (for tests / batch) without weakening
   the fail-loud validation.
3. No em-dashes in any user-facing text (prompts, messages).
