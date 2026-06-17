# BUILD SPEC: Cover-and-Redraw Batch — AIA Signs #2–#5 (real fonts)

## Context
Cover-and-redraw (Path 2) just WON Alec's three-way grading on sign #1 — it beat the all-AI
version. Now apply the same treatment to the other four signs' existing all-AI bases:
  output/aia_sign2_toolrun/generated.png — headline 远离非法金融，抵制高息诱惑
  output/aia_sign3_toolrun/generated.png — headline 珍惜一生血汗，远离非法金融
  output/aia_sign4_toolrun/generated.png — TWO crossed-out terms: 金融传销 + 虚拟货币骗局 (each has a red X over it)
  output/aia_sign5_toolrun/generated.png — TWO crossed-out terms: 非法集资 + 网络金融诈骗 (each has a red X over it)
Working code: harness/cover_redraw.py (text-mask patch version that preserved nearby graphics
on sign #1), harness/composite_text.py (font_role/brand resolution + compliance manifest →
licensed 汉仪雅酷黑 via brands/aia/fonts/index.json).

## Task per sign
LOOK AT EACH IMAGE FIRST (you can open them with PIL and inspect, or use your Read tool on
the PNG if vision-capable). Identify: headline text location, current layout (one line? two
lines? two separate blocks?), text color(s), and for #4/#5 where the X-marks sit.

### Signs #2 and #3 (straightforward)
- Detect/patch the headline text (text-mask approach from sign #1 — do NOT clip nearby graphics).
- Redraw with composite_text.py: font_role chinese_primary, brand aia, weight 85 (汉仪雅酷黑-85W
  should resolve licensed_exact), match the original text's color(s) and approximate size/position.
- IMPORTANT from sign-1 learnings: if the original had two different text colors (e.g. one line
  red one navy, or white-on-red block), match per-line colors sampled BEFORE patching.
- Output: output/coverredraw_sign2/final.png (+ .compliance.json), same for sign3.

### Signs #4 and #5 (the X-mark problem — handle explicitly)
The crossed-out terms have a red X drawn OVER the text. Naive patch erases the X too.
Strategy (try in this order):
  A) SELECTIVE MASK: build the patch mask from DARK text pixels only (the terms are dark
     navy/charcoal; the X is AIA red). Mask by color: patch only pixels matching the text
     color range, leaving red X strokes untouched. Then redraw the term text UNDER the
     existing X (composite text first... actually the X is already in the image — redraw
     text into the patched gaps; the X strokes remain on top visually since they were never
     removed). Check the result: the X must still read as crossing out the NEW text.
  B) If A leaves artifacts (X strokes with halo gaps where they crossed old text glyphs):
     full patch of the whole term block (text + X), redraw term with real font, then DRAW
     the X programmatically — two thick red strokes (rounded caps, color sampled from the
     other X in the image, stroke width matched, slight rotation) over the new text.
  Pick per-sign whichever looks cleaner. State which strategy each sign used.
- Each term gets its own compliance entry. Output: output/coverredraw_sign4/final.png, sign5 same.

## Verification (each sign)
- final.png exists, 1536x1024, >300KB.
- Compliance manifest = licensed_exact for every redrawn text run (investigate any fallback).
- Visual self-check with PIL: confirm no clipped graphics at patch borders (compare a 20px
  ring around the patch region between original and final — large diffs outside the text
  area = clipping bug).
- For #4/#5: X-marks present and crossing the redrawn terms.

## Honest reporting
Per sign: strategy used, patch bbox(es), colors sampled, compliance resolution, and any
residual artifacts you can see. If a sign's layout makes cover-redraw fail (e.g. text over
gradient or texture that can't be patched cleanly), say so and deliver the best attempt with
the issue named. Do not hand-retouch.

## Conventions
venv .venv (deps via uv pip install --python .venv/bin/python). Keys via dotenv. No API image
generation needed (bases exist) — only Anthropic calls if you need them (you shouldn't).
No git commits.
