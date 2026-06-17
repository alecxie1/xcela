# BUILD SPEC: harness/composite_text.py — Font-Compliance Compositing (TODAY-4)

## Why this exists
gpt-image-2 renders Chinese text as PIXELS that merely look like a font. The AIA client ask
(用友邦合规字体) requires the REAL licensed typeface. The VI (AIA Brand Standards V2.0)
mandates: English = AIA Everest (licensed OTF, we don't have it yet), Chinese = 汉仪甄选37款
library (licensed, we don't have it yet), fallback Arial / Noto Sans. STRATEGY: build the
compositor to take ANY font file as a parameter; prove it today with system CJK fonts
(SimHei / MSYH Bold at /mnt/c/Windows/Fonts/simhei.ttf and msyhbd.ttc); swap in licensed
files later with zero code change.

## The pipeline being built
1. Generate the sign with the HEADLINE AREA LEFT EMPTY (graphics, footer, logo all rendered
   by gpt-image-2 as usual — only the big headline characters are omitted, clean space reserved).
2. Composite the headline ONTO the image with Pillow using a real font file → pixel-perfect,
   genuinely compliant text.

## Build part A: `harness/composite_text.py` (~120 lines)
CLI:
  .venv/bin/python harness/composite_text.py --image IN.png --out OUT.png --spec SPEC.json

SPEC.json format — list of text layers:
[
  {
    "content": "守住钱袋子",
    "font": "/mnt/c/Windows/Fonts/simhei.ttf",     // any ttf/otf/ttc path; ttc needs index support
    "ttc_index": 0,                                  // optional, for .ttc collections
    "size_px": 150,                                  // glyph size in pixels
    "color": "#D31145",
    "anchor_frac": [0.5, 0.32],                      // position as FRACTION of image w/h
    "anchor": "mm",                                  // PIL anchor (mm=center-middle, la=left-top...)
    "stroke_width": 0,                               // optional outline
    "stroke_color": "#FFFFFF",
    "letter_spacing_px": 8                           // optional tracking — implement by drawing
                                                      // char-by-char with cumulative advance
  }, ...
]

Requirements:
- Pillow (pip install into .venv if missing).
- Handle .ttc via ImageFont.truetype(path, size, index=ttc_index).
- letter_spacing: draw per-character with manual advance (PIL has no native tracking).
- Respect anchor + fractional positioning so specs are resolution-independent.
- Save PNG, print absolute path + dimensions.

## Build part B: blank-headline generation + end-to-end proof on AIA sign #1
1. Read output/aia_sign1_toolrun/final_prompt.txt. Produce a modified prompt:
   - REMOVE the headline text-layout lines for 守住钱袋子 and 护好幸福家 (and any instruction
     to render them), REPLACE with: "Reserve a large clean EMPTY area in the upper-middle
     of the design for a headline to be added later — leave it completely blank, no text,
     no placeholder marks. All other text (footer, logo tagline) renders as specified."
   - Keep everything else (shape, palette, icons, footer, logo) identical.
2. Generate via the same gpt-image-2 images.edit path harness/generate.py uses
   (refs: AIA logo /mnt/c/Users/Alecx/Downloads/AIA-logo.png + style ref
   /mnt/c/Users/Alecx/Downloads/aia real task.png; size 1536x1024, quality high;
   OPENAI_API_KEY via dotenv ~/.hermes/.env). Save output/aia_sign1_composite/blank.png.
3. Write headline_spec.json: 守住钱袋子 line 1 + 护好幸福家 line 2, SimHei
   (/mnt/c/Windows/Fonts/simhei.ttf), AIA red #D31145, sized/positioned to fill the
   reserved area (~140-170px glyphs, centered, letter_spacing ~6-10px, line gap ~1.25x).
4. Run composite_text.py → output/aia_sign1_composite/final.png.
5. VERIFY: final.png exists, >300KB, dimensions 1536x1024. Print all paths + sizes.

## Honest-reporting rules
- The blank-headline generation may FAIL to leave clean space (model might draw text anyway
  or fill the area with graphics). If so: report it plainly, try ONE revised wording, and if
  it still fails, deliver the compositor + composite over the BEST blank attempt and state
  the residual problem. Do NOT claim success if the blank area has stray text/garbage.
- Do not fabricate outputs. Print real file sizes from disk.

## Conventions
- venv: .venv (py3.11), use .venv/bin/python. Keys auto-load from ~/.hermes/.env via dotenv
  (scene_author.py shows the pattern).
- New files only; do not modify existing harness files. No git commits.
- composite_text.py must be brand-agnostic and reusable (nothing AIA-specific hardcoded —
  everything comes from the spec JSON).
