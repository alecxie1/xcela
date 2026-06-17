# BUILD SPEC: Brand Asset Library v1 + Compliance Manifest + A/B Fixes + Real-Font Rerun

## Context (read first)
- Real licensed fonts ARRIVED: 31 HanYi .ttf files in /mnt/c/Users/Alecx/Downloads/
  (HYYakuHei-55/65/75/85/95W.ttf, HYYuanLongHei75W.ttf, HYXuanSong55S.ttf, HYQiHei*, etc.
  plus one duplicate 汉仪雅酷黑-85.ttf). Handyprint has signed license agreements — usage legitimate.
- Prior A/B (output/ab_path1_reservation/, output/ab_path2_coverredraw/) used simhei fallback.
  Alec's grading: all-AI version > Path2 > Path1. Issues: (1) BOTH paths silently used the wrong
  font (simhei, too thin) — compliance failure was SILENT; (2) Path2's white patch box clipped
  graphics (mountain bottom-left, shield bottom-right); (3) Path1 reservation ~2x oversized
  (headline floats, graphics too small).
- Files to study: harness/composite_text.py, harness/scene_author.py, harness/cover_redraw.py,
  answer_keys/aia.json (typography block), docs/FONT_INTELLIGENCE_design_note.md.

## Part 1 — Brand Asset Library v1 (Alec's directive: read each VI once, persist forever)
Create brands/ directory structure:
  brands/aia/
    fonts/            <- COPY (not move) all 31 HanYi ttfs from Downloads here
    fonts/index.json  <- the font index (below)
    assets/           <- copy AIA-logo.png + 'aia real task.png' here
    (answer key stays at answer_keys/aia.json but now points into brands/aia/)
Build `build_font_index.py` (repo root): scans a fonts/ dir, reads each file's REAL internal
name table with fonttools (family name, subfamily, both en + zh records), writes index.json:
  {"汉仪雅酷黑": {"55W": {"file": "brands/aia/fonts/HYYakuHei-55W.ttf", "ps_name": "...", "family_zh": "汉仪雅酷黑"}, ...}, ...}
Run it on brands/aia/fonts/. The index maps VI vocabulary names (汉仪雅酷黑-85简 etc.) to actual
files BY READING THE FONT METADATA, not by guessing from filenames (filenames are romanized,
VI names are Chinese — the name table bridges them). Print the resulting index. Flag any file
whose internal name can't be matched to a known 汉仪 pattern into "_unmatched" for human review.
Update answer_keys/aia.json typography: chinese_primary gains
  "library_index": "brands/aia/fonts/index.json" (file/file_fallback stay for back-compat).

## Part 2 — Compliance manifest (silent fallback is the cardinal sin)
composite_text.py: every run now writes <out_image>.compliance.json alongside the output:
  [{"content": "...", "requested": "汉仪雅酷黑-85简", "resolved_file": "...", "resolution": 
    "licensed_exact" | "licensed_family_other_weight" | "fallback_system" | "MISSING",
    "weight_requested": "85", "weight_used": "85"}]
Resolution order for a font_role/weight request: (1) exact family+weight via library_index →
licensed_exact; (2) same family, nearest weight → licensed_family_other_weight + WARN;
(3) file_fallback → fallback_system + LOUD MULTILINE WARNING to stdout naming what the VI
mandates vs what was used; (4) nothing → hard fail listing what to supply.
Weight parsing: extract digits from weight_hint/library-member names (85简/85W/-85 all = 85).
scene_author's auto-composite step must surface the manifest summary in its stdout.

## Part 3 — the two mechanical fixes
FIX A (Path 1, scene_author validation): headline_reservation area must be ≤ needed_area × 1.25
  (needed = Σ lines (chars × size_px × size_px × 1.15)); if oversized, SHRINK h_frac/w_frac
  proportionally (keep center) rather than re-asking the model. Add logo-conflict check: if
  reservation overlaps the typical logo zones (corners), warn in output. Also add to the
  meta-prompt's tier-3 field defs: supporting graphics should remain substantial (each major
  icon ≥ 8% of canvas height) — text dominance comes from text size, not from shrinking graphics.
FIX B (Path 2, cover_redraw.py): tighten patch bbox — pad 1.5% not 4%; before filling, erode
  the patch region to the actual text-pixel mask (dilate text mask by ~8px) instead of a full
  rectangle, so nearby graphics (mountain, shield) survive; sample fill color per-region
  (left/right halves) to handle gradients.

## Part 4 — the REAL-FONT rerun (the fair fight Alec wants)
RUN A: full Path-1 pipeline rerun, same intent/style-notes/ref as before, out to
  output/ab2_path1_realfont/ — scene-author picks its 雅酷黑 weight, compositor resolves via
  the library index → should be licensed_exact with HYYakuHei-85W.ttf (or whatever weight it
  picks). Verify manifest says licensed_exact.
RUN B: cover-and-redraw rerun on output/aia_sign1_toolrun/generated.png (the all-AI version
  Alec likes) with fixed bbox/patch + real 雅酷黑-85W → output/ab2_path2_realfont/.
Both: print real file sizes + the compliance manifests. If anything resolves to fallback,
that's a bug — find out why before finishing.

## Honest reporting
Show: the font index (or its summary + _unmatched), both compliance manifests, final tier-3
typography choices, real file sizes. If the name-table matching is messy (HanYi naming is
inconsistent), show exactly which files matched which names and which needed filename-based
fallback matching — do not pretend the index is cleaner than it is.

## Conventions
venv .venv; new deps via `uv pip install --python .venv/bin/python <pkg>` (fonttools already in).
Keys via dotenv ~/.hermes/.env. Keep all existing CLI behavior working. No git commits.
