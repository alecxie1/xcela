# BUILD SPEC: Typography in the Analysis Layer + Brand-Agnostic Font Loading

## Context — the product contract (read first)
The tool's canonical REQUIRED INPUTS per brand are now: (1) logo file, (2) VI manual PDF,
(3) FONT FILES (otf/ttf/ttc/woff2), (4) past posters/material (ideally).
RULE: what font a job mandates comes from the VI ANALYSIS LAYER (extracted from the PDF into
the answer key) — never from the orchestrating agent's internal knowledge. Font FILES are
supplied by the brand (Handyprint is an official partner with signed font license agreements).
Existing code to study before writing: extract_text_layer.py (deterministic extraction
patterns), harness/composite_text.py (the compositor you'll extend), answer_keys/aia.json
and answer_keys/taichi.json (the schema you'll extend).

## Part A — typography extraction into the answer key

### A1. New module: `extract_typography.py` (repo root, ~120 lines)
CLI: .venv/bin/python extract_typography.py --pdf <VI.pdf> --out <typography.json>
- Use fitz (PyMuPDF, already in .venv) to walk the PDF text layer.
- Find typography-related pages/lines: keywords 字体, Typeface, typeface, Font, font.
- Extract CANDIDATE font names with regex + heuristics. Patterns to handle (from real VIs):
  - Latin font names near 字体/font keywords: e.g. "AIA Everest", "Arial", "Open Sans",
    "Noto Sans", "Helvetica" (capture multi-word capitalized names).
  - CJK font-library names: e.g. 汉仪甄选37款字体, 汉仪旗黑, 锦华明朝体, 微软雅黑
    (capture sequences containing 汉仪/方正/思源/华文/锦华 + trailing chars, and
    X款字体 library patterns).
  - Role hints from surrounding text: 主要字体/primary, 系统字体/system, fallback wording
    (无法使用…时), digital/数字平台, 标题/headline, 正文/body.
  - Usage rules worth keeping verbatim: lines about color-on-background (e.g. 友邦红背景上
    的正文应选择白色字体), bans (不建议使用手写字体或草写字体).
- Output JSON shape:
  {
    "typography": {
      "english_primary":  {"name": "...", "source_page": N, "license_note": "...", "file": null},
      "english_fallback": {"name": "...", "source_page": N, "file": null},
      "chinese_primary":  {"name": "...", "source_page": N, "license_note": "...", "file": null},
      "digital":          {"name": "...", "source_page": N, "file": null},
      "rules": ["verbatim rule strings w/ page numbers"],
      "_provenance": "text_layer",
      "_confidence": "high|medium per field",
      "_candidates_rejected": [ ... anything ambiguous, for human review ... ]
    }
  }
- IMPORTANT: this is DETERMINISTIC extraction (regex/heuristics on the text layer), consistent
  with the project's extraction philosophy. No LLM calls. Ambiguous hits go to
  _candidates_rejected for human review, NOT silently dropped or guessed.
- Fields it cannot find → null with _confidence noted. NEVER invent a font name.

### A2. Run it on the real AIA VI and merge into the answer key
- Run: .venv/bin/python extract_typography.py --pdf "/mnt/c/Users/Alecx/Downloads/AIA Brand Standards - V2.0.pdf" --out /tmp/aia_typography.json
- Expected (verify, don't assume): english_primary=AIA Everest, english_fallback=Arial,
  chinese_primary=汉仪甄选37款字体 (library), digital=Noto Sans / Open Sans, plus the
  white-text-on-red rule and no-handwriting-fonts rule.
- MERGE the typography block into answer_keys/aia.json, REPLACING the current placeholder
  "fonts" field (which is {chinese_display: null, english: null}). Keep the key name
  "typography". Set "file" values: null for AIA Everest / 汉仪甄选 (files not yet received
  from brand), and for testing add "file_fallback": "/mnt/c/Windows/Fonts/simhei.ttf" on
  chinese_primary and "/mnt/c/Windows/Fonts/arial.ttf" (verify exists, else null) on english.
- Also run against the Taichi VI if present in Downloads (太极堡 VI pdf) — if found, merge its
  typography block into answer_keys/taichi.json the same way (锦华明朝体, Helvetica, 汉仪旗黑
  are the expected names per earlier analysis). If the PDF isn't found, skip and say so.

## Part B — brand-agnostic font loading in the compositor

### B1. Extend `harness/composite_text.py`
1. NEW: spec layers may reference the answer key instead of a hardcoded path:
   {"content": "...", "font_role": "chinese_primary", "brand": "aia", ...}
   → resolver loads answer_keys/<brand>.json, reads typography[font_role]:
     use "file" if set, else "file_fallback", else FAIL LOUDLY with a clear message
     naming the missing font + the mandated font name from the VI (e.g. "AIA mandates
     汉仪甄选37款字体 — font file not yet supplied by brand; set typography.chinese_primary.file").
   Explicit "font": "/path" still works and wins over font_role (back-compat with existing specs).
2. NEW: format support at load time — accept .otf/.ttf/.ttc natively (ttc honors ttc_index);
   for .woff/.woff2, auto-convert to a cached .ttf via fonttools
   (pip install fonttools into .venv; cache to ~/.cache/handyprint-fonts/<hash>.ttf so
   conversion happens once). Unknown extensions → clear error listing supported formats.
3. Keep everything else (anchor_frac, letter_spacing, stroke) unchanged.

### B2. Prove it end-to-end (REAL run, no image generation needed)
1. Take the existing output/aia_sign1_composite/blank.png.
2. Write a spec using font_role/brand resolution (NOT a hardcoded font path):
   headline 守住钱袋子 / 护好幸福家, font_role chinese_primary, brand aia — which should
   resolve via answer key → file_fallback simhei.ttf.
3. Composite → output/aia_sign1_composite/final_v2_rolebased.png. Verify >300KB, 1536x1024.
4. WOFF2 path test (synthetic but real): convert simhei.ttf to /tmp/test.woff2 with fonttools,
   then run a tiny composite using "font": "/tmp/test.woff2" on any small text onto blank.png
   → /tmp/woff2_test.png. Confirm the auto-conversion+cache works. (If simhei→woff2 conversion
   is slow/large, subset it first with fonttools subset --text="测试" .)
5. Print real file sizes and paths for everything produced.

## Honest reporting
- Show the actual extracted typography JSON (and what landed in _candidates_rejected).
- If the AIA PDF yields messier results than expected, show the raw candidates — do not
  hand-tune the output to match the expectations listed above.
- Any failures: state plainly what failed and what you fell back to.

## Conventions
- venv .venv (py3.11): .venv/bin/python. New deps (fonttools) → pip install into .venv.
- Do not break existing CLI behavior of composite_text.py (old specs with "font" path must
  still run). Do not modify scene_author.py / approve.py / generate.py. No git commits.
