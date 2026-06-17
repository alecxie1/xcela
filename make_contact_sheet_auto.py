"""Contact sheet for the AUTO vs HAND prompt comparison (#20 falsifiable test).
Top row: the two source crops + client 定稿 (6-panel, the real ground truth).
Middle row: HAND-prompt outputs (Hermes-in-loop, from test_reffeed.py).
Bottom row: AUTO-prompt outputs (analyzer standalone, from test_reffeed_AUTO.py).
Column 1 = crop1 lineage, Column 2 = crop2 lineage, Column 3 = reference targets.
Pure layout. Alec's eye is the judge.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

CELL_W, IMG_H, LABEL_H = 512, 512, 50
PAD, BG, TITLE_H = 22, (245, 245, 245), 60

cells = [
    ("/mnt/c/Users/Alecx/Downloads/cropped ref 1.png",            "FED: crop 1 (pizza)",        False),
    ("/mnt/c/Users/Alecx/Downloads/cropped ref 2.png",            "FED: crop 2 (money bag)",    False),
    ("brands/aia/assets/aia_dinggao_final_6panel.png",            "TARGET: real 定稿 (6-panel)", True),

    ("output/reffed_sign1_crop1/generated.png",                  "HAND-prompt - crop1",        False),
    ("output/reffed_sign1_crop2/generated.png",                  "HAND-prompt - crop2",        False),
    ("output/chroma_sign1_v2/preview_white.png",                 "(parse-only baseline)",      False),

    ("output/reffed_AUTO_crop1/generated.png",                   "AUTO-prompt - crop1",        False),
    ("output/reffed_AUTO_crop2/generated.png",                   "AUTO-prompt - crop2",        False),
    (None,                                                        "",                           False),
]

def load_font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

font, title_font = load_font(21), load_font(28)

def fit(img, w, h):
    img = img.convert("RGB")
    r = min(w / img.width, h / img.height)
    nw, nh = int(img.width * r), int(img.height * r)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    return canvas

cols, rows = 3, 3
sheet_w = PAD + cols * (CELL_W + PAD)
sheet_h = TITLE_H + PAD + rows * (IMG_H + LABEL_H + PAD)
sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
draw = ImageDraw.Draw(sheet)
draw.text((PAD, 16), "AUTO vs HAND prompt  -  row2: Hermes hand-wrote the style clause   row3: analyzer wrote it standalone",
          font=title_font, fill=(20, 20, 20))

for i, (path, label, is_target) in enumerate(cells):
    r, c = divmod(i, cols)
    x = PAD + c * (CELL_W + PAD)
    y = TITLE_H + PAD + r * (IMG_H + LABEL_H + PAD)
    if path is None:
        continue
    try:
        im = fit(Image.open(path), CELL_W, IMG_H)
    except Exception as e:
        im = Image.new("RGB", (CELL_W, IMG_H), (220, 200, 200))
        ImageDraw.Draw(im).text((10, 10), f"MISSING:\n{path}\n{e}", font=font, fill=(120, 0, 0))
    sheet.paste(im, (x, y))
    strip = (255, 235, 180) if is_target else (235, 235, 235)
    draw.rectangle([x, y + IMG_H, x + CELL_W, y + IMG_H + LABEL_H], fill=strip)
    draw.text((x + 10, y + IMG_H + 13), label, font=font, fill=(20, 20, 20))

out = Path("output/CONTACT_SHEET_auto_vs_hand.png")
sheet.save(out)
print(f"saved {out} ({out.stat().st_size:,} bytes) {sheet.size}")
