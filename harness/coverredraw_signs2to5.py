#!/usr/bin/env python3
"""coverredraw_signs2to5.py — batch cover-and-redraw for AIA signs #2–#5.

Per COVERREDRAW_BATCH_SPEC.md. Reuses the sign-1 text-mask patch approach
(cover_redraw.text_masks) but drives each text run from a per-sign measured
search box instead of global band detection, because:
  - sign2: the red check-shield sits 38px right of line 2 — global column-run
    merging (gap 100) would swallow it into the bbox and patch it away;
  - sign3: the red shield overlaps line 2's column range, so the two lines
    need different masks (red-only vs dark-only regions handled via boxes);
  - signs 4/5: two separate term blocks, each crossed by a red X. STRATEGY B
    (spec fallback): Strategy A was tried first and left artifacts — the
    originals drew the text OVER the X, so the strokes carry glyph-shaped
    holes matching the OLD glyphs; neither re-stamping nor morphological
    hole-filling reconstructed the ragged brush strokes cleanly. So instead:
    full inpaint of the whole term block (text + X, cv2 TELEA), redraw the
    term with the real font, then draw the X programmatically on top — two
    thick strokes with rounded caps, endpoints / stroke width / color all
    measured from the original X.

Outputs per sign: output/coverredraw_signN/{patched.png, redraw_spec.json,
final.png, final.png.compliance.json, ring_check.json}.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from composite_text import composite, _materialize_font, resolve_font
from cover_redraw import text_masks

WEIGHT_HINT = "汉仪雅酷黑-85W"
DILATE_PX = 8  # same as sign-1 run

SIGNS = {
    2: dict(
        base="output/aia_sign2_toolrun/generated.png",
        out="output/coverredraw_sign2",
        runs=[  # box = (x0,y0,x1,y1) search region; both = red|dark ink inside it
            dict(content="远离非法金融", box=(280, 300, 1235, 470)),
            dict(content="抵制高息诱惑", box=(285, 470, 1232, 652)),
        ],
        xmark_boxes=[],
    ),
    3: dict(
        base="output/aia_sign3_toolrun/generated.png",
        out="output/coverredraw_sign3",
        runs=[
            dict(content="珍惜一生血汗", box=(308, 283, 1394, 474)),  # x0>shield right edge 285
            dict(content="远离非法金融", box=(246, 487, 1360, 675)),
        ],
        xmark_boxes=[],
    ),
    4: dict(
        base="output/aia_sign4_toolrun/generated.png",
        out="output/coverredraw_sign4",
        runs=[  # Strategy A: dark-only patch mask; X (red) untouched + re-stamped
            dict(content="金融传销", box=(165, 444, 678, 580), dark_only=True),
            dict(content="虚拟货币骗局", box=(806, 448, 1418, 570), dark_only=True),
        ],
        xmark_boxes=[(135, 284, 740, 712), (810, 284, 1398, 712)],
    ),
    5: dict(
        base="output/aia_sign5_toolrun/generated.png",
        out="output/coverredraw_sign5",
        runs=[
            dict(content="非法集资", box=(143, 319, 708, 478), dark_only=True),
            dict(content="网络金融诈骗", box=(809, 322, 1418, 471), dark_only=True),
        ],
        xmark_boxes=[(238, 221, 648, 562), (897, 224, 1293, 570)],
    ),
}


def dilate(mask: np.ndarray, px: int) -> np.ndarray:
    img = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.MaxFilter(2 * px + 1))) > 0


def tight_bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def ring_bg(arr, bbox, exclude, width=12):
    """Per left/right half medians of a ring around bbox, skipping ink pixels."""
    x0, y0, x1, y1 = bbox
    h, w = arr.shape[:2]
    ring = np.zeros((h, w), bool)
    ring[max(y0 - width, 0):min(y1 + width, h), max(x0 - width, 0):min(x1 + width, w)] = True
    ring[y0:y1, x0:x1] = False
    ring &= ~exclude
    mid = (x0 + x1) // 2
    cols = np.arange(w)[None, :].repeat(h, axis=0)
    out = []
    for half in (ring & (cols < mid), ring & (cols >= mid)):
        px = arr[half]
        out.append(tuple(int(v) for v in np.median(px, axis=0)) if len(px) else (255, 255, 255))
    return out


def fit_size(font_path, content, target_h, target_w):
    """size_px fitting glyph height ≈ target_h, shrunk if width would exceed
    target_w by >2%; letter_spacing to widen back toward target_w (capped)."""
    probe = ImageFont.truetype(font_path, 100)
    l, t, r, b = probe.getbbox(content)
    size = max(int(round(100 * target_h / max(b - t, 1))), 8)
    length = ImageFont.truetype(font_path, size).getlength(content)
    if length > target_w * 1.02:
        size = max(int(size * target_w / length), 8)
        length = ImageFont.truetype(font_path, size).getlength(content)
    spacing = 0.0
    n = len(content)
    if n > 1 and length < target_w * 0.97:
        spacing = min((target_w - length) / (n - 1), 0.22 * size)
    return size, round(spacing, 1)


def measure_x(red: np.ndarray, xbox):
    """Endpoints, stroke width and color geometry of one X from the original
    red mask. Endpoints = red px nearest each xbox corner; width = median
    perpendicular run length sampled along each diagonal away from center/tips."""
    xx0, xy0, xx1, xy1 = xbox
    m = np.zeros(red.shape, bool)
    m[xy0:xy1, xx0:xx1] = red[xy0:xy1, xx0:xx1]
    ys, xs = np.nonzero(m)
    pts = np.stack([xs, ys], axis=1)
    corners = [(xx0, xy0), (xx1, xy1), (xx1, xy0), (xx0, xy1)]  # TL,BR,TR,BL
    ends = []
    for cx, cy in corners:
        d = np.abs(pts[:, 0] - cx) + np.abs(pts[:, 1] - cy)
        ends.append(tuple(int(v) for v in pts[d.argmin()]))
    widths = []
    for a, b in ((ends[0], ends[1]), (ends[2], ends[3])):
        a, b = np.array(a, float), np.array(b, float)
        v = b - a
        L = np.hypot(*v)
        u = v / L
        nrm = np.array([-u[1], u[0]])
        for t in (0.22, 0.3, 0.38, 0.62, 0.7, 0.78):
            p = a + v * t
            run = 0
            for s in range(-90, 91):
                q = p + nrm * s
                xq, yq = int(round(q[0])), int(round(q[1]))
                if 0 <= yq < m.shape[0] and 0 <= xq < m.shape[1] and m[yq, xq]:
                    run += 1
            widths.append(run)
    width = int(np.median(widths))
    return ends, width


def draw_x_overlay(img: Image.Image, ends, width, color, ss=4):
    """Two thick rounded-cap strokes (TL->BR, TR->BL), drawn 4x supersampled
    and downscaled for clean anti-aliased edges, composited over img."""
    w, h = img.size
    ov = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    r = width * ss // 2
    for a, b in ((ends[0], ends[1]), (ends[2], ends[3])):
        # inset endpoints by the cap radius so the rounded cap ends exactly
        # at the measured brush tip instead of overshooting it
        av, bv = np.array(a, float), np.array(b, float)
        u = (bv - av) / np.hypot(*(bv - av))
        av, bv = av + u * width * 0.5, bv - u * width * 0.5
        pa = tuple((av * ss).round().astype(int))
        pb = tuple((bv * ss).round().astype(int))
        d.line([pa, pb], fill=color + (255,), width=width * ss)
        for p in (pa, pb):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color + (255,))
    ov = ov.resize((w, h), Image.LANCZOS)
    out = img.convert("RGBA")
    out.alpha_composite(ov)
    return out.convert("RGB")


def process_sign(n, cfg, font_path):
    print(f"\n{'='*70}\n=== SIGN #{n}: {cfg['base']}\n{'='*70}")
    out_dir = Path(cfg["out"])
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(cfg["base"]).convert("RGB")
    arr0 = np.asarray(img)
    h, w = arr0.shape[:2]
    red, dark = text_masks(arr0)

    arr = arr0.copy()
    is_xsign = bool(cfg["xmark_boxes"])
    report = {"sign": n, "strategy": "B (full inpaint of term+X, programmatic "
              "X redraw on top — A tried first, left stroke artifacts)"
              if is_xsign else "plain text-mask patch (sign-1 method)",
              "runs": []}
    spec = []
    patch_union = None

    for ri, run in enumerate(cfg["runs"]):
        x0, y0, x1, y1 = run["box"]
        ink = dark if run.get("dark_only") else (red | dark)
        boxmask = np.zeros((h, w), bool)
        boxmask[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
        if boxmask.sum() < 1500:
            raise RuntimeError(f"sign{n} {run['content']!r}: ink mask too small ({boxmask.sum()})")
        tb = tight_bbox(boxmask)
        text_color = tuple(int(v) for v in np.median(arr0[boxmask], axis=0))
        bg_halves = ring_bg(arr0, tb, exclude=dilate(red | dark, 3))
        if not is_xsign:
            # patch: dilated ink mask, clipped to the search box, filled per-half
            dil = dilate(boxmask, DILATE_PX)
            clip = np.zeros((h, w), bool)
            clip[max(y0 - DILATE_PX, 0):min(y1 + DILATE_PX, h),
                 max(x0 - DILATE_PX, 0):min(x1 + DILATE_PX, w)] = True
            dil &= clip
            mid = (tb[0] + tb[2]) // 2
            cols = np.arange(w)[None, :].repeat(h, axis=0)
            arr[dil & (cols < mid)] = bg_halves[0]
            arr[dil & (cols >= mid)] = bg_halves[1]
            n_patched = int(dil.sum())
            pu = (max(x0 - DILATE_PX, 0), max(y0 - DILATE_PX, 0),
                  min(x1 + DILATE_PX, w), min(y1 + DILATE_PX, h))
        else:
            # Strategy B: inpaint the WHOLE block — term text + its X — in one
            # region (union of run box and X box), so box edges/bg under the
            # strokes are reconstructed by TELEA instead of flat fills.
            import cv2
            xb = cfg["xmark_boxes"][ri]
            ub = (min(x0, xb[0]) - DILATE_PX, min(y0, xb[1]) - DILATE_PX,
                  max(x1, xb[2]) + DILATE_PX, max(y1, xb[3]) + DILATE_PX)
            full = np.zeros((h, w), bool)
            full[ub[1]:ub[3], ub[0]:ub[2]] = (red | dark)[ub[1]:ub[3], ub[0]:ub[2]]
            full = dilate(full, 5)
            full[:ub[1], :] = False; full[ub[3]:, :] = False
            full[:, :ub[0]] = False; full[:, ub[2]:] = False
            arr = cv2.inpaint(arr, (full * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)
            n_patched = int(full.sum())
            pu = ub

        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        size, spacing = fit_size(font_path, run["content"], th, tw)
        hexcolor = "#%02X%02X%02X" % text_color
        layer = {
            "content": run["content"], "font_role": "chinese_primary", "brand": "aia",
            "weight_hint": WEIGHT_HINT, "size_px": size, "color": hexcolor,
            "anchor_frac": [round((tb[0] + tb[2]) / 2 / w, 4), round((tb[1] + tb[3]) / 2 / h, 4)],
            "anchor": "mm",
        }
        if spacing:
            layer["letter_spacing_px"] = spacing
        spec.append(layer)
        report["runs"].append(dict(content=run["content"], tight_bbox=tb,
                                   text_color=text_color, bg_halves=bg_halves,
                                   size_px=size, letter_spacing_px=spacing,
                                   patched_px=n_patched))
        patch_union = pu if patch_union is None else (
            min(patch_union[0], pu[0]), min(patch_union[1], pu[1]),
            max(patch_union[2], pu[2]), max(patch_union[3], pu[3]))
        print(f"  run {run['content']!r}: bbox={tb} color=rgb{text_color} "
              f"bg={bg_halves} size={size} spacing={spacing} patched={n_patched:,}px")

    patched_path = out_dir / "patched.png"
    Image.fromarray(arr).save(patched_path)
    spec_path = out_dir / "redraw_spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    final_path = out_dir / "final.png"
    composite(str(patched_path), str(spec_path), str(final_path))

    # Strategy B step 2: draw each X programmatically ON TOP of the new text,
    # geometry and color measured from the original X.
    if cfg["xmark_boxes"]:
        fin = Image.open(final_path).convert("RGB")
        report["xmarks"] = []
        for xb in cfg["xmark_boxes"]:
            xx0, xy0, xx1, xy1 = xb
            xmask = np.zeros((h, w), bool)
            xmask[xy0:xy1, xx0:xx1] = red[xy0:xy1, xx0:xx1]
            x_color = tuple(int(v) for v in np.median(arr0[xmask], axis=0))
            ends, width = measure_x(red, xb)
            fin = draw_x_overlay(fin, ends, width, x_color)
            report["xmarks"].append(dict(box=xb, endpoints=ends,
                                         stroke_width=width, color=x_color))
            # the drawn X (caps + AA) is part of the modified region
            ex = [e for e in ends]
            ov = (min(p[0] for p in ex) - 2, min(p[1] for p in ex) - 2,
                  max(p[0] for p in ex) + 2, max(p[1] for p in ex) + 2)
            patch_union = (min(patch_union[0], ov[0]), min(patch_union[1], ov[1]),
                           max(patch_union[2], ov[2]), max(patch_union[3], ov[3]))
            print(f"  X @ {xb}: redrawn, endpoints={ends} width={width} color=rgb{x_color}")
        fin.save(final_path)

    report["patch_union"] = patch_union
    (out_dir / "run_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    sz = final_path.stat().st_size
    with Image.open(final_path) as im:
        dims = im.size
    print(f"  FINAL: {final_path}  {dims[0]}x{dims[1]}  {sz:,} bytes")
    return report


def main():
    probe = {"font_role": "chinese_primary", "brand": "aia", "weight_hint": WEIGHT_HINT}
    resolved, mf = resolve_font(probe)
    font_path = _materialize_font(resolved)
    print(f"font resolution probe: [{mf['resolution']}] {mf['resolved_file']} "
          f"(weight used: {mf['weight_used']})")
    if mf["resolution"] != "licensed_exact":
        raise SystemExit("ABORT: font did not resolve licensed_exact")
    for n, cfg in SIGNS.items():
        process_sign(n, cfg, font_path)


if __name__ == "__main__":
    main()
