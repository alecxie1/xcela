# Contract: page-finding heuristic (`brand_intake/page_finder.py`)

PURE, deterministic, model-free. Replaces the hardcoded `BRANDS` page dicts with discovery the human
confirms. Reuses the extractors' own regexes so the suggestion matches what the extractor then parses.

## `suggest_pages(pdf_path) -> dict`

```
{
  "color":      [<1-indexed pages with real hex/RGB tokens, ranked by count>],
  "fonts":      [<1-indexed pages with CJK/EN font-name patterns>],
  "brand_name": [<1-indexed early/title pages>],
  "text_layer_ratio": <float>,   # < 0.05 => image-only (degraded; colors still OCR off captions)
}
```

- Scans each page's TEXT LAYER (`extract_text_layer.page_text` / fitz `get_text`).
- `color`: pages containing real hex tokens (the `extract_colors._HEX_RE` shape: a 6-hex token with a
  letter) or RGB triples (`_RGB_RE`); ranked by token count. A page that merely contains the word
  "color" with NO hex token is NOT suggested.
- `fonts`: pages matching `extract_text_layer._CJK_FONT_RE` / `_EN_FONT_RE`, minus the `_FONT_STOPLIST`
  section labels.
- ALL page numbers are 1-INDEXED (the `extract_colors.render_page` footgun: `doc[page_no_1idx - 1]`).

## Rules (falsifiable)

1. Given a PDF where page 1 says "color palette" (no hex) and page 2 prints `#31B4E7`, `color`
   contains 2 (1-indexed) and NOT 1.
2. Page numbers are 1-indexed (a 0-indexed bug would render the wrong page and return nothing).
3. It uses NO model (deterministic regex over the text layer); the human confirms/corrects the result.
4. An image-only PDF (`text_layer_ratio < 0.05`) is reported as such (the font path then degrades to
   the existing VLM fallback; colors still OCR off the swatch captions).
