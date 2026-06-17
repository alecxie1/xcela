#!/usr/bin/env python3
"""cover_redraw.py — Path 2 of the font A/B: cover-and-redraw.

Take an all-AI flat-graphic sign whose composition is good but whose headline is
look-alike (not the licensed font): detect the headline bbox by color-thresholding
brand-red + charcoal text tones in the center band, patch it with the local
background color, and redraw the headline lines with composite_text.py using the
real font file.

CLI:
  .venv/bin/python harness/cover_redraw.py --image IN.png --out-dir OUT \
      --lines 守住钱袋子 护好幸福家 --brand aia --font-role chinese_primary
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from composite_text import composite, _materialize_font, resolve_font


def text_masks(arr: np.ndarray):
    """Boolean masks for AIA-red and dark-charcoal text pixels."""
    r = arr[..., 0].astype(np.int16)
    g = arr[..., 1].astype(np.int16)
    b = arr[..., 2].astype(np.int16)
    red = (r > 130) & (g < 90) & (b < 120) & ((r - g) > 70)
    dark = (r < 110) & (g < 110) & (b < 120)
    return red, dark


def _runs(profile: np.ndarray, threshold: int, merge_gap: int):
    """Contiguous index runs where profile >= threshold, merging runs separated
    by < merge_gap (character/letter spacing gaps within a text block)."""
    idx = np.nonzero(profile >= threshold)[0]
    if len(idx) == 0:
        return []
    runs = []
    start = prev = idx[0]
    for i in idx[1:]:
        if i - prev >= merge_gap:
            runs.append((start, prev))
            start = i
        prev = i
    runs.append((start, prev))
    return runs


def detect_headline_bbox(img: Image.Image, band=(0.18, 0.665, 0.02, 0.95), pad_frac=0.015):
    """Largest red+dark text mass inside the center band → padded bbox.

    band = (y0_frac, y1_frac, x0_frac, x1_frac): excludes the logo (top), footer
    line (bottom) and any brand-red icon at the right edge. Inside the band, thin
    container-border strokes also survive the color threshold, so the bbox comes
    from ink PROFILES, not raw extremes: the widest contiguous column run is the
    text block (the border is a narrow run); row bands are then recomputed within
    those columns only. Pad 1.5% of bbox dims (was 4% — the loose pad clipped
    nearby graphics; patching is mask-based now so the box only needs to contain
    the ink).
    Returns (bbox, per-line row bands, masks) — bbox in pixel coords (x0,y0,x1,y1).
    """
    arr = np.asarray(img.convert("RGB"))
    h, w = arr.shape[:2]
    red, dark = text_masks(arr)
    mask = np.zeros((h, w), bool)
    y0b, y1b = int(band[0] * h), int(band[1] * h)
    x0b, x1b = int(band[2] * w), int(band[3] * w)
    mask[y0b:y1b, x0b:x1b] = (red | dark)[y0b:y1b, x0b:x1b]
    if mask.sum() < 2000:
        raise RuntimeError(f"headline mask too small ({mask.sum()} px) — detection unreliable")

    col_runs = _runs(mask.sum(axis=0), threshold=50, merge_gap=100)
    if not col_runs:
        raise RuntimeError("no column run cleared the ink threshold — detection unreliable")
    x0, x1 = max(col_runs, key=lambda r: r[1] - r[0])

    row_profile = mask[:, x0:x1 + 1].sum(axis=1)
    row_runs = [r for r in _runs(row_profile, threshold=30, merge_gap=12)
                if r[1] - r[0] > 40]  # drop slivers (icon edges, stray accents)
    if not row_runs:
        raise RuntimeError("no row band cleared the ink threshold — detection unreliable")
    y0, y1 = row_runs[0][0], row_runs[-1][1]

    pw, ph = int(pad_frac * (x1 - x0)), int(pad_frac * (y1 - y0))
    bbox = (max(x0 - pw, 0), max(y0 - ph, 0), min(x1 + pw, w), min(y1 + ph, h))
    return bbox, row_runs, (red, dark, mask)


def sample_colors(arr: np.ndarray, bbox, lines, masks):
    """bg = per-half (left/right) medians of a 10px ring around the bbox — handles
    horizontal gradients; per-line text color = median of that line's red-or-dark
    pixels (sampled BEFORE patching)."""
    red, dark, mask = masks
    x0, y0, x1, y1 = bbox
    h, w = arr.shape[:2]
    ring = np.zeros((h, w), bool)
    rx0, ry0, rx1, ry1 = max(x0 - 10, 0), max(y0 - 10, 0), min(x1 + 10, w), min(y1 + 10, h)
    ring[ry0:ry1, rx0:rx1] = True
    ring[y0:y1, x0:x1] = False
    mid = (x0 + x1) // 2
    cols = np.arange(w)[None, :].repeat(h, axis=0)
    bg_halves = []
    for half in (ring & (cols < mid), ring & (cols >= mid)):
        px = arr[half]
        bg_halves.append(tuple(int(v) for v in np.median(px, axis=0)) if len(px)
                         else (255, 255, 255))
    line_colors = []
    for ly0, ly1 in lines:
        sub = mask[ly0:ly1 + 1, x0:x1]
        px = arr[ly0:ly1 + 1, x0:x1][sub]
        line_colors.append(tuple(int(v) for v in np.median(px, axis=0)))
    return bg_halves, line_colors


def patch_text_mask(img: Image.Image, bbox, masks, bg_halves, dilate_px=8):
    """Erase ONLY the text ink inside bbox: dilate the red|dark text mask by
    ~dilate_px (PIL MaxFilter) and fill those pixels with the local background —
    per left/right half, so nearby graphics (mountain, shield) and gradients
    survive instead of being wiped by a full white rectangle."""
    arr = np.asarray(img).copy()
    red, dark, _band_mask = masks
    x0, y0, x1, y1 = bbox
    sub = (red | dark)[y0:y1, x0:x1]
    mask_img = Image.fromarray((sub * 255).astype(np.uint8))
    size = 2 * dilate_px + 1  # MaxFilter kernel must be odd
    dilated = np.asarray(mask_img.filter(ImageFilter.MaxFilter(size))) > 0
    mid = (x0 + x1) // 2 - x0
    region = arr[y0:y1, x0:x1]
    cols = np.arange(region.shape[1])[None, :]
    region[dilated & (cols < mid)] = bg_halves[0]
    region[dilated & (cols >= mid)] = bg_halves[1]
    return Image.fromarray(arr), int(dilated.sum())


def size_for_height(font_path: str, sample: str, target_h: int) -> int:
    """Pick size_px so the rendered glyph height of `sample` ≈ target_h."""
    probe = ImageFont.truetype(font_path, 100)
    l, t, r, b = probe.getbbox(sample)
    return max(int(round(100 * target_h / max(b - t, 1))), 8)


def main():
    ap = argparse.ArgumentParser(description="Cover-and-redraw headline with the real font.")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--lines", nargs="+", required=True, help="headline lines, top to bottom")
    ap.add_argument("--brand", default="aia")
    ap.add_argument("--font-role", default="chinese_primary")
    ap.add_argument("--stroke-width", type=int, default=3,
                    help="same-color stroke to compensate single-weight font thinness "
                    "(auto-dropped when a real licensed weight resolves)")
    ap.add_argument("--weight-hint", default="",
                    help="weight/family request passed to font resolution, e.g. "
                    "'汉仪雅酷黑-85简' — resolves through the brand library index")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(args.image).convert("RGB")
    arr = np.asarray(img)
    w, h = img.size

    print("=== Step 1: Detect headline bbox (color threshold, center band) ===")
    bbox, lines, masks = detect_headline_bbox(img)
    if len(lines) != len(args.lines):
        print(f"  [warn] detected {len(lines)} row bands but {len(args.lines)} lines given — "
              "merging/splitting to match", file=sys.stderr)
        # Best effort: split the full ink rows evenly.
        y0, y1 = lines[0][0], lines[-1][1]
        n = len(args.lines)
        step = (y1 - y0 + 1) / n
        lines = [(int(y0 + i * step), int(y0 + (i + 1) * step) - 1) for i in range(n)]
    print(f"  bbox (padded 1.5%): {bbox}   canvas: {w}x{h}")
    for i, (ly0, ly1) in enumerate(lines):
        print(f"  line {i + 1} rows: y {ly0}..{ly1}  (height {ly1 - ly0 + 1}px)")

    print("\n=== Step 2: Sample colors (before patching) ===")
    bg_halves, line_colors = sample_colors(arr, bbox, lines, masks)
    print(f"  background (10px ring median, left half): rgb{bg_halves[0]}")
    print(f"  background (10px ring median, right half): rgb{bg_halves[1]}")
    for i, c in enumerate(line_colors):
        print(f"  line {i + 1} text color (median of ink px): rgb{c}")

    # Debug overlay: bbox + line bands on a copy.
    dbg = img.copy()
    d = ImageDraw.Draw(dbg)
    d.rectangle(bbox, outline=(0, 200, 0), width=4)
    for ly0, ly1 in lines:
        d.rectangle((bbox[0], ly0, bbox[2], ly1), outline=(0, 120, 255), width=2)
    dbg.save(out_dir / "detection_debug.png")

    print("\n=== Step 3: Patch text-pixel mask with local background ===")
    patched, n_patched = patch_text_mask(img, bbox, masks, bg_halves)
    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    print(f"  patched {n_patched:,} px (dilated text mask) of {bbox_area:,} px bbox "
          f"({n_patched / max(bbox_area, 1):.0%}) — graphics outside the mask survive")
    patched_path = out_dir / "patched.png"
    patched.save(patched_path)
    print(f"  Saved {patched_path}  ({patched_path.stat().st_size:,} bytes)")

    print("\n=== Step 4: Redraw lines with the real font ===")
    probe_layer = {"font_role": args.font_role, "brand": args.brand,
                   "weight_hint": args.weight_hint}
    resolved_path, probe_manifest = resolve_font(probe_layer)
    font_path = _materialize_font(resolved_path)
    print(f"  font file: {font_path}  [{probe_manifest['resolution']}]")
    spec = []
    cx = (bbox[0] + bbox[2]) / 2 / w
    for content, (ly0, ly1), color in zip(args.lines, lines, line_colors):
        size = size_for_height(font_path, content, ly1 - ly0 + 1)
        hexcolor = "#%02X%02X%02X" % color
        spec.append({
            "content": content,
            "font_role": args.font_role,
            "brand": args.brand,
            "weight_hint": args.weight_hint,
            "size_px": size,
            "color": hexcolor,
            "anchor_frac": [round(cx, 4), round((ly0 + ly1) / 2 / h, 4)],
            "anchor": "mm",
            "stroke_width": args.stroke_width,
            "stroke_color": hexcolor,
            "stroke_is_weight_simulation": True,
        })
        print(f"  '{content}': size_px={size} color={hexcolor} "
              f"anchor_frac=({cx:.3f}, {(ly0 + ly1) / 2 / h:.3f}) stroke={args.stroke_width}")
    spec_path = out_dir / "redraw_spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    final = composite(str(patched_path), str(spec_path), str(out_dir / "final.png"))
    print(f"\n  Saved {final}  ({final.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
