"""Assemble a 3x2 contact sheet so Alec's eye (ground truth) can judge the
ref-feed test. Top row = the two fed crops + the client 定稿 (target).
Bottom row = parse-only baseline + the two ref-fed outputs.
Pure layout work (a 'click' task), no judgment baked in.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

CELL_W, IMG_H, LABEL_H = 512, 512, 56
PAD, BG = 24, (245, 245, 245)
TITLE_H = 64

cells = [
    # (path, label)  -- row-major, 3 per row
    ("/mnt/c/Users/Alecx/Downloads/cropped ref 1.png",                         "FED: crop 1 (pizza)"),
    ("/mnt/c/Users/Alecx/Downloads/cropped ref 2.png",                         "FED: crop 2 (money bag)"),
    ("brands/aia/assets/aia real task.png",                                     "TARGET: client 定稿"),
    ("output/chroma_sign1_v2/preview_white.png",                               "OUT: parse-only (beat this)"),
    ("output/reffed_sign1_crop1/generated.png",                                "OUT: ref-fed crop 1"),
    ("output/reffed_sign1_crop2/generated.png",                                "OUT: ref-fed crop 2"),
]

def load_font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

font = load_font(22)
title_font = load_font(30)

def fit(img, w, h):
    img = img.convert("RGB")
    r = min(w / img.width, h / img.height)
    nw, nh = int(img.width * r), int(img.height * r)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    return canvas

cols, rows = 3, 2
sheet_w = PAD + cols * (CELL_W + PAD)
sheet_h = TITLE_H + PAD + rows * (IMG_H + LABEL_H + PAD)
sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
draw = ImageDraw.Draw(sheet)
draw.text((PAD, 18), "REF-FEED TEST  -  top: inputs + target   bottom: outputs", font=title_font, fill=(20, 20, 20))

for i, (path, label) in enumerate(cells):
    r, c = divmod(i, cols)
    x = PAD + c * (CELL_W + PAD)
    y = TITLE_H + PAD + r * (IMG_H + LABEL_H + PAD)
    try:
        im = fit(Image.open(path), CELL_W, IMG_H)
    except Exception as e:
        im = Image.new("RGB", (CELL_W, IMG_H), (220, 200, 200))
        ImageDraw.Draw(im).text((10, 10), f"MISSING:\n{path}\n{e}", font=font, fill=(120, 0, 0))
    sheet.paste(im, (x, y))
    # label strip
    is_target = label.startswith("TARGET")
    strip = (255, 235, 180) if is_target else (235, 235, 235)
    draw.rectangle([x, y + IMG_H, x + CELL_W, y + IMG_H + LABEL_H], fill=strip)
    draw.text((x + 10, y + IMG_H + 14), label, font=font, fill=(20, 20, 20))

out = Path("output/CONTACT_SHEET_reffeed.png")
sheet.save(out)
print(f"saved {out} ({out.stat().st_size:,} bytes) {sheet.size}")
