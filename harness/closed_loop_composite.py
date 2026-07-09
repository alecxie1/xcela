#!/usr/bin/env python3
"""closed_loop_composite.py — the ACTUATOR of the closed-loop composite.

Open-loop compositing anchored text at the tier-3 PLAN's coordinates, but
gpt-image-2 paints its own geometry: the container interior lands elsewhere,
and the model sometimes paints a ghost headline inside the reserved zone.
This tool closes the loop: MEASURE the painted image (measure_canvas), patch
any ghost headline, then composite anchored to the DETECTED free-space optical
center instead of the planned one.

Flow:
  1. measure_canvas.measure() with expected-text = the spec's composited contents
  2. ghost_text_boxes -> patch them out (mask-based local-bg fill inside the OCR
     quad — neighbors outside the quad are never touched)
  3. re-measure the patched image -> free_space_bbox / optical_center now include
     the reclaimed ghost zone
  4. re-anchor the spec's lines vertically centered on the detected optical
     center, preserving line order, size_px and inter-line gap ratio; shrink
     (>=70%) if the block can't fit the free space
  5. composite via composite_text (compliance manifest kept), with a legibility
     guard against the ACTUAL pixels behind each re-anchored line
  6. write final.png + final.png.compliance.json + placement_report.json

CLI:
  .venv/bin/python harness/closed_loop_composite.py --image gen.png \
      --spec composite_spec.json --brand aia --out final.png
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from composite_text import composite, _materialize_font, resolve_font
from cover_redraw import size_for_height
from measure_canvas import (CHROMA_DEFRINGE_PX, CHROMA_DIST, _fuzzy_match, _hex_rgb,
                            contrast_ratio, measure)

MIN_CONTRAST = 1.8
MIN_SHRINK = 0.70
PATCH_DILATE_PX = 10
QUAD_PAD_FRAC = 0.04   # pad the OCR quad outward by 4% of its size before masking
INK_DIST = 30          # RGB euclidean distance from local bg that counts as ink
                       # (low on purpose: ghost glyphs trail soft glow/AA halos;
                       # over-masking is harmless because the fill interpolates
                       # the local gradient rather than stamping one flat color)
PLATE_DETECT_DIST = 45      # RGB distance from the container BASE fill that flags a
                            # painted plate/panel inside the reserved headline zone
PLATE_MIN_ZONE_FRAC = 0.02  # a connected off-fill region must cover at least this
                            # fraction of the zone to count as a plate (AA specks don't)
OCR_READBACK_MIN_CONF = 0.85   # Fix-3 occlusion gate: per-line OCR confidence floor
OCR_READBACK_MIN_MATCH = 0.80  # ...and similarity floor of the read-back text
OVERLAY_CROSS_PAD_FRAC = 0.08  # cross_x bbox padding (fraction of bbox dim)
OCR_CROSSED_MIN_MATCH = 0.60   # lowered match floor for X-crossed terms (X partially occludes)
OCR_CROSSED_MIN_CONF = 0.45    # lowered confidence floor for X-crossed terms


def _pad_quad(quad_px, pad_frac, w, h):
    """Expand a quad outward from its centroid by pad_frac."""
    cx = sum(p[0] for p in quad_px) / len(quad_px)
    cy = sum(p[1] for p in quad_px) / len(quad_px)
    return [(min(max(cx + (x - cx) * (1 + pad_frac), 0), w - 1),
             min(max(cy + (y - cy) * (1 + pad_frac), 0), h - 1)) for x, y in quad_px]


BORDER_GUARD_CELLS = 5  # grid cells (~20px) of protection around the backdrop


def _interior_mask_fullres(masks, wh) -> np.ndarray | None:
    """Full-resolution mask of the zone a ghost patch may touch: everything
    EXCEPT the backdrop (saturated regions touching the canvas border) dilated
    by ~BORDER_GUARD_CELLS grid cells. The container's white border ring lives
    inside that guard band, so it survives; ghost ink and its white outline
    sit deeper in the interior, so they stay patchable. (Hole-filling the
    container component does NOT work here: a ghost glyph's white outline can
    touch the white border ring, making it border-connected, not a hole.)"""
    if not masks or masks.get("backdrop") is None:
        return None
    guard = masks["backdrop"].copy()
    for _ in range(BORDER_GUARD_CELLS):
        d = guard.copy()
        d[1:, :] |= guard[:-1, :]
        d[:-1, :] |= guard[1:, :]
        d[:, 1:] |= guard[:, :-1]
        d[:, :-1] |= guard[:, 1:]
        guard = d
    img = Image.fromarray((~guard * 255).astype(np.uint8))
    return np.asarray(img.resize(wh, Image.NEAREST)) > 0


def patch_ghosts(img: Image.Image, ghost_boxes: list[dict],
                 container_color, interior_mask=None) -> tuple[Image.Image, list[dict]]:
    """Erase ghost text inside each OCR quad polygon, cover_redraw-style:
    mask only the ink (here: pixels far from the local background color — the
    ghost has BOTH dark-red ink and a white outline, so cover_redraw's
    red|dark color masks would leave the outline behind), dilate, and fill
    with the local background. Pixels outside the quad — and, when an
    interior_mask is given, outside the container interior — are never
    touched, so neighbors (shield icon, container border) survive."""
    w, h = img.size
    arr = np.asarray(img.convert("RGB")).copy()
    fallback_bg = tuple(int(v) for v in (container_color or (255, 255, 255)))
    records = []
    for box in ghost_boxes:
        quad_px = [(p[0] * w, p[1] * h) for p in box["quad_frac"]]
        quad_px = _pad_quad(quad_px, QUAD_PAD_FRAC, w, h)
        poly = Image.new("L", (w, h), 0)
        ImageDraw.Draw(poly).polygon(quad_px, fill=255)
        poly_mask = np.asarray(poly) > 0
        if interior_mask is not None:
            poly_mask &= interior_mask

        # Local background = the container fill visible between glyphs inside
        # the quad: median of quad pixels near the container color.
        region_px = arr[poly_mask]
        near = np.linalg.norm(region_px.astype(np.int16) - np.int16(fallback_bg),
                              axis=1) < INK_DIST
        bg = (tuple(int(v) for v in np.median(region_px[near], axis=0))
              if near.any() else fallback_bg)

        dist = np.linalg.norm(arr.astype(np.int16) - np.int16(bg), axis=2)
        ink = (dist > INK_DIST) & poly_mask
        size = 2 * PATCH_DILATE_PX + 1  # MaxFilter kernel must be odd
        dilated = np.asarray(Image.fromarray((ink * 255).astype(np.uint8))
                             .filter(ImageFilter.MaxFilter(size))) > 0
        fill = dilated & poly_mask  # dilation never escapes the quad

        # Fill = per-row HORIZONTAL interpolation between the surviving pixels
        # left/right of each masked run — reproduces the container's gradient
        # instead of stamping a flat color (which banded visibly). Rows with
        # too few survivors get a row color interpolated vertically from
        # valid neighbor rows.
        ys = np.nonzero(fill.any(axis=1))[0]
        row_bgs = np.full((len(ys), 3), np.nan)
        for i, y in enumerate(ys):
            row_free = poly_mask[y] & ~fill[y]
            if row_free.sum() >= 8:
                row_bgs[i] = np.median(arr[y][row_free], axis=0)
        valid = ~np.isnan(row_bgs[:, 0])
        if valid.any():
            for ch in range(3):
                row_bgs[:, ch] = np.interp(ys, ys[valid], row_bgs[valid, ch])
        else:
            row_bgs[:] = bg
        for i, y in enumerate(ys):
            fx = np.nonzero(fill[y])[0]
            anchor_x = np.nonzero(poly_mask[y] & ~fill[y])[0]
            if len(anchor_x) >= 2:
                row = arr[y].astype(np.float64)
                for ch in range(3):
                    row[fx, ch] = np.interp(fx, anchor_x, row[anchor_x, ch])
                arr[y, fx] = np.clip(row[fx], 0, 255).astype(np.uint8)
            else:
                arr[y, fx] = row_bgs[i].astype(np.uint8)
        records.append({
            "text": box["text"],
            "quad_frac": box["quad_frac"],
            "local_bg_rgb": list(bg),
            "patched_px": int(fill.sum()),
        })
    return Image.fromarray(arr), records


def patch_reserved_zone(img: Image.Image, zone_frac, interior_mask,
                        protect_boxes_frac, fallback_bg) -> tuple[Image.Image, dict]:
    """Fix-2 backstop: ghost-OCR catches painted TEXT in the reserved headline
    zone, but a painted PLATE/PANEL is a shape, not text — it sails through and
    the headline composites on top of it, illegible. Detect it deterministically:
    sample the container's BASE fill from the interior OUTSIDE the zone (the
    plate lives inside the zone, so the outside median is the true fill even
    when the plate dominates the interior), flag large connected regions inside
    the zone that deviate > PLATE_DETECT_DIST from that fill, and flood them
    back to base fill via the same gradient-preserving fill as patch_ghosts.

    Conservative by construction: the patchable area is the zone rect ∩ the
    container interior (border/backdrop guarded by interior_mask) minus every
    protected OCR text box (footer etc.) — icons, mascot, footer and edges
    outside the zone are never touched."""
    w, h = img.size
    arr = np.asarray(img.convert("RGB"))
    x0f, y0f, x1f, y1f = zone_frac
    zone = np.zeros((h, w), bool)
    zone[int(y0f * h):int(np.ceil(y1f * h)), int(x0f * w):int(np.ceil(x1f * w))] = True
    record = {"zone_frac": [round(float(v), 4) for v in zone_frac],
              "intrusion_detected": False, "base_fill_rgb": None,
              "intrusion_px": 0, "patched_px": 0}
    if interior_mask is None:
        record["note"] = "no container interior mask — backstop skipped"
        return img, record
    zone &= interior_mask
    for bx0, by0, bx1, by1 in protect_boxes_frac:
        zone[int(by0 * h):int(np.ceil(by1 * h)),
             int(bx0 * w):int(np.ceil(bx1 * w))] = False
    if not zone.any():
        record["note"] = "reserved zone ∩ container interior is empty — backstop skipped"
        return img, record

    # Base fill = median of the interior OUTSIDE the zone. Mascot/icons/footer
    # are minority pixels out there; the median shrugs them off. (The naive
    # whole-interior median is exactly what the plate poisons.)
    ring = interior_mask & ~zone
    base = (np.median(arr[ring].astype(np.int32), axis=0) if ring.any()
            else np.array(fallback_bg or (255, 255, 255), np.int32))
    record["base_fill_rgb"] = [int(v) for v in base]

    dist = np.sqrt(((arr.astype(np.int32) - base) ** 2).sum(axis=2))
    intr = (dist > PLATE_DETECT_DIST) & zone
    from scipy import ndimage
    labels, n = ndimage.label(intr)
    if n:
        sizes = np.asarray(ndimage.sum(intr, labels, range(1, n + 1)))
        big = np.nonzero(sizes >= PLATE_MIN_ZONE_FRAC * zone.sum())[0] + 1
        intr = np.isin(labels, big)
    record["intrusion_px"] = int(intr.sum())
    if not intr.any():
        return img, record

    record["intrusion_detected"] = True
    # Flood via patch_ghosts' gradient-preserving fill: a synthetic "box" over
    # the zone rect, masked to zone (interior minus protected text already
    # applied above) — only off-base-fill pixels inside the zone get filled.
    bx = _bbox_of_bool(intr)
    quad_frac = [[bx[0] / w, bx[1] / h], [bx[2] / w, bx[1] / h],
                 [bx[2] / w, bx[3] / h], [bx[0] / w, bx[3] / h]]
    synth = {"text": "<reserved-zone plate>", "quad_frac": quad_frac}
    patched, recs = patch_ghosts(img, [synth], tuple(int(v) for v in base),
                                 interior_mask=zone)
    record["patched_px"] = recs[0]["patched_px"] if recs else 0
    return patched, record


def _bbox_of_bool(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _line_metrics(layer: dict, size_px: int) -> tuple[float, float]:
    """Rendered (width, height) in px of a layer's content at size_px,
    including letter spacing and stroke."""
    font_path, _ = resolve_font(layer)
    font = ImageFont.truetype(_materialize_font(font_path), size_px,
                              index=layer.get("ttc_index", 0))
    text = str(layer.get("content", ""))
    spacing = float(layer.get("letter_spacing_px", 0))
    stroke = int(layer.get("stroke_width", 0))
    width = sum(font.getlength(ch) for ch in text) \
        + spacing * max(len(text) - 1, 0) + 2 * stroke
    l, t, r, b = font.getbbox(text)
    return width, (b - t) + 2 * stroke


def reanchor(layers: list[dict], free_bbox, optical_center, canvas_wh) -> dict:
    """Re-derive every layer's anchor_frac from the DETECTED geometry: stack the
    lines vertically centered on optical_center, preserving order, size and the
    original inter-line gap ratio; shrink proportionally (floor 70%) if the
    block can't fit free_space_bbox. Mutates layers in place; returns a record."""
    W, H = canvas_wh
    fx0, fy0, fx1, fy1 = free_bbox
    free_w, free_h = (fx1 - fx0) * W, (fy1 - fy0) * H
    ocx, ocy = optical_center

    planned = [list(t["anchor_frac"]) for t in layers]
    # Inter-line gap (px between consecutive line centers) from the PLAN's
    # anchor deltas — the plan's rhythm survives, only its origin moves.
    gaps = [(planned[i + 1][1] - planned[i][1]) * H for i in range(len(layers) - 1)]
    if gaps and min(gaps) <= 0:
        gaps = [abs(g) or layers[0].get("size_px", 100) * 1.1 for g in gaps]

    orig_sizes = [int(t["size_px"]) for t in layers]
    orig_spacing = [float(t.get("letter_spacing_px") or 0) for t in layers]
    orig_gaps = list(gaps)

    def _block(cur_gaps):
        metrics = [_line_metrics(t, int(t["size_px"])) for t in layers]
        return (max(m[0] for m in metrics),
                sum(cur_gaps) + (metrics[0][1] + metrics[-1][1]) / 2)

    block_w, block_h = _block(gaps)
    block0 = (block_w, block_h)
    # Iterate the shrink: integer size rounding can leave a few px of overflow
    # after one pass, so re-fit until the block fits or the floor is reached.
    scale, shrink_note = 1.0, None
    for _ in range(4):
        if (block_w <= free_w and block_h <= free_h) or scale <= MIN_SHRINK:
            break
        scale = max(scale * min(free_w / block_w if block_w else 1.0,
                                free_h / block_h if block_h else 1.0), MIN_SHRINK)
        for t, s0, sp0 in zip(layers, orig_sizes, orig_spacing):
            t["size_px"] = max(int(round(s0 * scale)), 8)
            if sp0:
                t["letter_spacing_px"] = int(round(sp0 * scale))
        gaps = [g * scale for g in orig_gaps]
        block_w, block_h = _block(gaps)
    if scale < 1.0:
        shrink_note = (f"block {block0[0]:.0f}x{block0[1]:.0f}px exceeded free space "
                       f"{free_w:.0f}x{free_h:.0f}px — shrunk to {scale:.3f}")
        if block_w > free_w or block_h > free_h:
            shrink_note += (f"; STILL overflows at the {MIN_SHRINK:.0%} floor "
                            f"({block_w:.0f}x{block_h:.0f}px)")

    # Clamp the block center so the block stays inside the free box (when it fits).
    cx = ocx if block_w >= free_w else min(max(ocx, fx0 + block_w / 2 / W),
                                           fx1 - block_w / 2 / W)
    cy = ocy if block_h >= free_h else min(max(ocy, fy0 + block_h / 2 / H),
                                           fy1 - block_h / 2 / H)

    # Stack line centers around cy; keep each line's planned x-offset from the
    # plan's mean x (all-centered plans keep x = cx exactly).
    span = sum(gaps)
    mean_px = sum(p[0] for p in planned) / len(planned)
    y = cy - span / 2 / H
    for i, t in enumerate(layers):
        t["anchor_frac"] = [round(cx + (planned[i][0] - mean_px), 4), round(y, 4)]
        if i < len(gaps):
            y += gaps[i] / H
    return {
        "planned_anchors_frac": planned,
        "detected_optical_center": [ocx, ocy],
        "free_space_bbox": list(free_bbox),
        "block_px": [round(block_w, 1), round(block_h, 1)],
        "anchors_frac": [t["anchor_frac"] for t in layers],
        "shifts_frac": [[round(t["anchor_frac"][0] - p[0], 4),
                         round(t["anchor_frac"][1] - p[1], 4)]
                        for t, p in zip(layers, planned)],
        "size_shrink": shrink_note,
    }


def legibility_guard(img: Image.Image, layers: list[dict]) -> list[dict]:
    """Contrast of each layer's color against the ACTUAL pixels its re-anchored
    line will cover (median of the line's bbox on the patched canvas). Silent
    illegibility is the same cardinal-sin family as silent font fallback."""
    W, H = img.size
    arr = np.asarray(img.convert("RGB"))
    results = []
    for t in layers:
        w_px, h_px = _line_metrics(t, int(t["size_px"]))
        fx, fy = t["anchor_frac"]
        x0, x1 = max(int(fx * W - w_px / 2), 0), min(int(fx * W + w_px / 2), W)
        y0, y1 = max(int(fy * H - h_px / 2), 0), min(int(fy * H + h_px / 2), H)
        zone = arr[y0:y1, x0:x1].reshape(-1, 3)
        if not len(zone):
            continue
        bg = tuple(int(v) for v in np.median(zone, axis=0))
        hexcolor = str(t.get("color", "#000000")).lstrip("#")
        rgb = tuple(int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
        ratio = contrast_ratio(rgb, bg)
        entry = {"content": t.get("content", ""), "color": "#" + hexcolor,
                 "behind_rgb": list(bg), "contrast": round(ratio, 2),
                 "legible": ratio >= MIN_CONTRAST}
        results.append(entry)
        if ratio < MIN_CONTRAST:
            print("  " + "=" * 64, file=sys.stderr)
            print(f"  LEGIBILITY WARNING: {entry['content']!r} #{hexcolor} has contrast "
                  f"{ratio:.2f} (<{MIN_CONTRAST}) against the actual surface rgb{bg} "
                  "behind its re-anchored line — text will be ILLEGIBLE.", file=sys.stderr)
            print("  " + "=" * 64, file=sys.stderr)
    return results


def ocr_readback(final_png: str | Path, layers: list[dict], out_dir: str | Path,
                 min_conf: float = OCR_READBACK_MIN_CONF,
                 min_match: float = OCR_READBACK_MIN_MATCH) -> dict:
    """Fix-3 occlusion/legibility gate: a headline composited onto a plate has
    perfect geometry but is unreadable — no prior gate would catch it. So read
    the FINAL image back: crop each composited line's region, OCR it, and
    require the line text to come back with confidence > min_conf and
    similarity >= min_match. A buried/occluded line OCRs poorly or not at all
    => gate FAILS. Crops are saved next to the final image (readback_lineN.png)
    so the evidence is inspectable.

    Match is a strict SequenceMatcher ratio — deliberately NOT measure_canvas's
    containment-counts-as-1.0 fuzzy match, which would let a half-occluded
    line ("守住钱" of "守住钱袋子") pass. Multiple OCR boxes in one crop are
    also tried concatenated (min of their confidences)."""
    import re
    from difflib import SequenceMatcher
    out = {"min_confidence": min_conf, "min_match": min_match, "lines": [], "pass": False}
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        out["error"] = f"rapidocr_onnxruntime not importable: {exc}"
        return out

    def _norm(s):
        return re.sub(r"[\s\W_]+", "", s or "", flags=re.UNICODE).lower()

    img = Image.open(final_png).convert("RGB")
    W, H = img.size
    ocr = RapidOCR()
    for i, t in enumerate(layers):
        expected = str(t.get("content", ""))
        w_px, h_px = _line_metrics(t, int(t["size_px"]))
        fx, fy = t["anchor_frac"]
        pad_x, pad_y = w_px * 0.15 + 20, h_px * 0.40 + 20
        x0 = max(int(fx * W - w_px / 2 - pad_x), 0)
        x1 = min(int(fx * W + w_px / 2 + pad_x), W)
        y0 = max(int(fy * H - h_px / 2 - pad_y), 0)
        y1 = min(int(fy * H + h_px / 2 + pad_y), H)
        crop_path = Path(out_dir) / f"readback_line{i + 1}.png"
        img.crop((x0, y0, x1, y1)).save(crop_path)
        result, _elapsed = ocr(str(crop_path))
        boxes = [(str(text), float(conf)) for _q, text, conf in (result or [])]
        cands = list(boxes)
        if len(boxes) > 1:  # a line split across boxes: try the concatenation
            cands.append(("".join(b[0] for b in boxes), min(b[1] for b in boxes)))
        best = {"ocr_text": None, "confidence": 0.0, "match": 0.0}
        ne = _norm(expected)
        for text, conf in cands:
            m = SequenceMatcher(None, _norm(text), ne).ratio()
            if (m, conf) > (best["match"], best["confidence"]):
                best = {"ocr_text": text, "confidence": round(conf, 4),
                        "match": round(m, 3)}
        ok = best["match"] >= min_match and best["confidence"] > min_conf
        out["lines"].append({"content": expected, "crop": str(crop_path),
                             "crop_px": [x0, y0, x1, y1], **best, "pass": ok})
    out["pass"] = bool(out["lines"]) and all(l["pass"] for l in out["lines"])
    return out


DESPILL_BAND_PX = 3   # how deep inside the cutout edge green-dominant spill is clamped


def strip_chroma(final_png: str | Path, out_dir: Path,
                 key_hex: str = "#00B140", keep_all_components: bool = False) -> dict:
    """Finalize a chroma-key contained sign: a 手举牌 gets physically die-cut,
    so green must not survive. From the composited RGB image, produce:
      <out_dir>/cutout.png        — RGBA, key backdrop -> alpha 0, defringed
      <out_dir>/preview_white.png — cutout flattened onto white (human-gradeable)
    Defringe = erode the opaque mask CHROMA_DEFRINGE_PX (drops the AA halo) +
    despill (green-dominant pixels in the edge band get G clamped to max(R,B)).
    Returns a record dict for the placement report.

    keep_all_components (016 T009-v2, default False = byte-identical die-cut behavior):
    a die-cut sign is ONE object, so the default keeps only the largest connected
    component (stray specks would survive as floating crumbs in the physical cut). A
    LAYERED-EXPORT element is the opposite: a multi-glyph text line or a logo lockup IS
    many disconnected components, and the largest-only keep erased 'COCONUT"' from a
    two-word line on the first paid export. True keeps every component; the caller's
    preview is the speck check."""
    from scipy import ndimage

    img = Image.open(final_png).convert("RGB")
    w, h = img.size
    arr = np.asarray(img).astype(np.int32)  # int16 overflows: 255²×3 > 32767
    key = _hex_rgb(key_hex)
    dist = np.sqrt(((arr - np.array(key, np.int32)) ** 2).sum(axis=2))
    opaque = ndimage.binary_erosion(dist > CHROMA_DIST, iterations=CHROMA_DEFRINGE_PX)
    # Keep the largest component only: stray non-green specks on the backdrop
    # would otherwise survive as floating crumbs in the die-cut.
    labels, n = ndimage.label(opaque)
    dropped_px = 0
    if n > 1 and not keep_all_components:
        sizes = np.asarray(ndimage.sum(opaque, labels, range(1, n + 1)))
        keep = labels == (int(np.argmax(sizes)) + 1)
        dropped_px = int(opaque.sum() - keep.sum())
        opaque = keep

    # Despill: anti-aliased boundary pixels carry a green cast even after the
    # erode — clamp green-dominant pixels in the edge band to max(R,B).
    rgb = arr.copy()
    edge_band = opaque & ~ndimage.binary_erosion(opaque, iterations=DESPILL_BAND_PX)
    spill = edge_band & (rgb[..., 1] > np.maximum(rgb[..., 0], rgb[..., 2]))
    rgb[..., 1][spill] = np.maximum(rgb[..., 0], rgb[..., 2])[spill]
    rgb = rgb.astype(np.uint8)

    cutout = out_dir / "cutout.png"
    rgba = np.dstack([rgb, (opaque * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(cutout)

    preview = out_dir / "preview_white.png"
    white = Image.new("RGB", (w, h), (255, 255, 255))
    white.paste(Image.fromarray(rgb), mask=Image.fromarray((opaque * 255).astype(np.uint8)))
    white.save(preview)

    # Honest residual check: pixels in the white preview still near the key.
    prev_arr = np.asarray(white).astype(np.int32)
    residual = int((np.sqrt(((prev_arr - np.array(key, np.int32)) ** 2).sum(axis=2))
                    <= 40).sum())
    record = {
        "key_hex": key_hex,
        "cutout": str(cutout),
        "preview_white": str(preview),
        "opaque_frac": round(float(opaque.mean()), 4),
        "stray_component_px_dropped": dropped_px,
        "despilled_px": int(spill.sum()),
        "green_residual_px_in_preview": residual,
    }
    print(f"  cutout -> {cutout} (opaque {record['opaque_frac']:.1%}, "
          f"despilled {record['despilled_px']}px, dropped {dropped_px}px strays)")
    print(f"  preview_white -> {preview} (green residual: {residual}px)")
    if residual:
        print(f"  [warn] {residual} pixels within dist 40 of {key_hex} survive in "
              "preview_white — green fringe not fully removed", file=sys.stderr)
    return record


# =========================================================================== #
# AXIS A: RENDER-AND-SCRUB placement (place_measured).
# gpt renders the COMPLETE sign incl. headline; we MEASURE where/how-big/what-color
# it landed, SCRUB it, and overlay the licensed font at the MEASURED geometry.
# Brand-general, OCR-driven, tier3-INDEPENDENT (lines from the caller, font from the
# answer key/register). Reuses measure + patch_ghosts + size_for_height + composite +
# ocr_readback + strip_chroma. It does NOT call reanchor() (that centers PLANNED-size
# text on FREE SPACE — the opposite of placement-match).
# =========================================================================== #

def _bbox_frac_to_px(bbox_frac, w, h):
    x0, y0, x1, y1 = bbox_frac
    return (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))


def _sample_ink_color(arr: np.ndarray, bbox_px, ring_px: int = 10) -> tuple[int, int, int]:
    """gpt's rendered ink color inside bbox: bg = median of a ring around the box;
    ink = box pixels far (> INK_DIST) from bg; color = median of those ink pixels.
    Brand-general (no hardcoded palette); mirrors cover_redraw.sample_colors' idea
    but uses the generic local-bg distance split, not AIA red/charcoal thresholds."""
    x0, y0, x1, y1 = bbox_px
    h, w = arr.shape[:2]
    rx0, ry0, rx1, ry1 = (max(x0 - ring_px, 0), max(y0 - ring_px, 0),
                          min(x1 + ring_px, w), min(y1 + ring_px, h))
    ring = np.zeros((h, w), bool)
    ring[ry0:ry1, rx0:rx1] = True
    ring[y0:y1, x0:x1] = False
    ring_px_vals = arr[ring]
    bg = (np.median(ring_px_vals, axis=0) if len(ring_px_vals)
          else np.array([255, 255, 255]))
    region = arr[y0:y1, x0:x1].reshape(-1, 3).astype(np.int16)
    if not len(region):
        return tuple(int(v) for v in bg)
    dist = np.linalg.norm(region - bg.astype(np.int16), axis=1)
    ink = region[dist > INK_DIST]
    color = np.median(ink, axis=0) if len(ink) else bg
    return tuple(int(v) for v in color)


def _union_box(boxes: list[dict], text: str) -> dict:
    """Synthetic box covering the union of several OCR boxes (handles OCR SPLITTING
    one rendered line into multiple fragments — we place once over their union)."""
    x0 = min(b["bbox_frac"][0] for b in boxes)
    y0 = min(b["bbox_frac"][1] for b in boxes)
    x1 = max(b["bbox_frac"][2] for b in boxes)
    y1 = max(b["bbox_frac"][3] for b in boxes)
    return {"text": text, "matched_expected": text,
            "bbox_frac": [x0, y0, x1, y1],
            "quad_frac": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def map_lines_to_boxes(lines: list[str], ghost_boxes: list[dict],
                       min_score: float = 0.6):
    """Map each expected line to exactly ONE box (union of all OCR boxes that
    best-match that line, score >= min_score). Returns (mapping, notes) where
    mapping is [(line, box), ...] in line order, or (None, notes) if any line
    has no matching box (e.g. OCR merged two lines into one box, or missed it).
    Honest: never guesses geometry."""
    notes = []
    if not lines:
        return None, ["no headline lines to place"]
    if not ghost_boxes:
        return None, ["OCR found no headline-matching text box (gpt may not have "
                      "rendered the text, or OCR failed) — cannot capture geometry"]
    groups = {ln: [] for ln in lines}
    for b in ghost_boxes:
        best_score, best_line = max((_fuzzy_match(b.get("text", ""), ln), ln) for ln in lines)
        if best_score >= min_score:
            groups[best_line].append(b)
    mapping = []
    for ln in lines:
        bs = groups[ln]
        if not bs:
            notes.append(f"no OCR box matched line {ln!r} — capture failed")
            return None, notes
        mapping.append((ln, _union_box(bs, ln) if len(bs) > 1 else bs[0]))
        if len(bs) > 1:
            notes.append(f"line {ln!r} matched {len(bs)} OCR fragments — merged their bboxes")
    return mapping, notes


def place_measured(image_path: str, lines: list[str], brand: str,
                   font_role: str, weight_hint: str, out_path: str,
                   chroma_key_hex: str | None = None,
                   is_reference_job: bool = False,
                   letter_spacing_frac: float = 0.0) -> dict:
    """Render-and-scrub: measure gpt's rendered headline, scrub it, overlay the
    licensed font at the captured position/size/color. Returns a record dict:
      status='placed'         -> out_path written with the licensed overlay.
      status='capture_failed' -> image NOT modified; caller does the path-specific
                                  honest-null fallback (ref: leave gpt text +
                                  needs_review; no-ref: free-space closed_loop).
    Never calls reanchor; never reads tier3 / write_composite_spec."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    arr = np.asarray(img)
    record = {"mode": "render_and_scrub", "is_reference_job": is_reference_job,
              "lines": lines, "status": None, "captured": [], "capture_notes": []}

    # 1. SENSOR (reuse measure): gpt's rendered headline OCRs and fuzzy-matches the
    #    expected lines, so it comes back as 'ghost_text_boxes' (naming clash: here it
    #    is the INTENDED text, and those boxes carry the geometry we want).
    rep, masks = measure(image_path, lines, want_masks=True, chroma_key_hex=chroma_key_hex)
    ghosts = rep.get("ghost_text_boxes", [])
    record["ghost_box_count"] = len(ghosts)
    if rep.get("ocr_error"):
        record["capture_notes"].append(f"OCR error: {rep['ocr_error']}")

    # 2. map each line -> one box (union of fragments); honest-null if it can't.
    mapping, notes = map_lines_to_boxes(lines, ghosts)
    record["capture_notes"] += notes
    if mapping is None:
        record["status"] = "capture_failed"
        (out.parent / "render_scrub_report.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    # 3. CAPTURE geometry + color per line (UNKNOWN 1: position + pixel size + fill).
    captured = []
    for line, box in mapping:
        bx = _bbox_frac_to_px(box["bbox_frac"], W, H)
        captured.append({
            "content": line, "bbox_px": list(bx),
            "anchor_frac": [round((bx[0] + bx[2]) / 2 / W, 4),
                            round((bx[1] + bx[3]) / 2 / H, 4)],
            "target_h_px": max(bx[3] - bx[1], 1),
            "ink_rgb": list(_sample_ink_color(arr, bx)),
        })
    record["captured"] = captured

    # 4. SCRUB gpt's rendered text (reuse patch_ghosts unchanged). interior_mask keeps
    #    the patch off the container border when a footprint exists (None for a
    #    full-bleed reference sign — then the scrub is constrained to the OCR quad).
    interior = _interior_mask_fullres(masks, img.size)
    scrubbed, patch_records = patch_ghosts(img, [b for _, b in mapping],
                                           rep.get("container_color"), interior_mask=interior)
    record["patch_records"] = patch_records

    # 5. BUILD SPEC from captured geometry. Font from the answer key/register
    #    (font_role + weight_hint), NEVER from tier3.
    try:
        font_path, fmani = resolve_font({"font_role": font_role, "brand": brand,
                                         "weight_hint": weight_hint})
    except Exception as exc:  # noqa: BLE001 — surface a clear font-resolution failure
        record["status"] = "capture_failed"
        record["capture_notes"].append(f"font resolution failed: {exc}")
        return record
    materialized = _materialize_font(font_path)
    spec = []
    for cap in captured:
        size_px = size_for_height(materialized, cap["content"], cap["target_h_px"])
        entry = {"content": cap["content"], "font_role": font_role, "brand": brand,
                 "weight_hint": weight_hint, "size_px": size_px,
                 "color": "#%02X%02X%02X" % tuple(cap["ink_rgb"]),
                 "anchor_frac": cap["anchor_frac"], "anchor": "mm"}
        if letter_spacing_frac:
            entry["letter_spacing_px"] = round(size_px * letter_spacing_frac, 1)
        spec.append(entry)
    record["font_resolution"] = fmani["resolution"]
    record["spec"] = spec

    # 6. COMPOSITE the licensed glyphs (reuse) + the occlusion readback gate (reuse).
    scrubbed_path = out.parent / "_render_scrub_base.png"
    scrubbed.save(scrubbed_path)
    spec_path = out.parent / "render_scrub_spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    final = composite(str(scrubbed_path), str(spec_path), str(out))
    scrubbed_path.unlink()
    record["final"] = str(final)
    print("=== render-and-scrub: OCR-readback occlusion gate ===")
    record["occlusion_readback"] = ocr_readback(final, spec, out.parent)
    for ln in record["occlusion_readback"]["lines"]:
        print(f"  {ln['content']!r}: read back {ln['ocr_text']!r} conf={ln['confidence']} "
              f"match={ln['match']} -> {'PASS' if ln['pass'] else 'FAIL'}")

    # 7. strip chroma for no-ref die-cut jobs (ref jobs pass chroma_key_hex=None).
    if chroma_key_hex:
        record["chroma_strip"] = strip_chroma(final, out.parent, chroma_key_hex)

    record["status"] = "placed"
    (out.parent / "render_scrub_report.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  render-and-scrub placed {len(spec)} line(s) at MEASURED geometry -> {final}")
    return record


def closed_loop(image_path: str, spec_path: str, out_path: str,
                brand: str | None = None,
                chroma_key_hex: str | None = None,
                reserved_zone_frac: list[float] | None = None) -> Path:
    """Run the full measure -> patch -> re-anchor -> composite loop.

    chroma_key_hex: when set, measurement uses deterministic chroma container
    recovery, and after compositing the green is stripped (cutout.png +
    preview_white.png).
    reserved_zone_frac: [x0, y0, x1, y1] of the PLANNED headline reservation —
    enables the Fix-2 backstop that detects and floods any plate/panel painted
    inside the reserved zone before the headline composites onto it."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    layers = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    if isinstance(layers, dict):
        layers = [layers]
    if brand:
        for t in layers:
            t.setdefault("brand", brand)
    expected = [str(t.get("content", "")) for t in layers]

    print("=== Closed loop 1: measure the painted canvas ===")
    pre, pre_masks = measure(image_path, expected, want_masks=True,
                             chroma_key_hex=chroma_key_hex)
    pre_path = out.parent / "measurement_pre.json"
    pre_path.write_text(json.dumps(pre, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ghosts: {len(pre['ghost_text_boxes'])}  optical_center: {pre['optical_center']}"
          f"  -> {pre_path}")
    for n in pre["notes"]:
        print(f"  [note] {n}", file=sys.stderr)

    img = Image.open(image_path).convert("RGB")
    patch_records = []
    measure_input = image_path
    interior = _interior_mask_fullres(pre_masks, img.size)
    dirty = False
    if pre["ghost_text_boxes"]:
        print("=== Closed loop 2: patch ghost headline(s) ===")
        if interior is None:
            print("  [warn] no container footprint available — patch constrained to "
                  "the OCR quad only (border damage possible)", file=sys.stderr)
        img, patch_records = patch_ghosts(img, pre["ghost_text_boxes"],
                                          pre.get("container_color"),
                                          interior_mask=interior)
        dirty = True
        for r in patch_records:
            print(f"  patched {r['text']!r}: {r['patched_px']:,}px filled with "
                  f"rgb{tuple(r['local_bg_rgb'])}")

    plate_record = None
    if reserved_zone_frac:
        # Fix-2 backstop: ghost-OCR only sees painted TEXT — a painted plate/
        # panel in the reserved zone is a shape and sails through, burying the
        # composited headline. Detect + flood it back to base fill BEFORE the
        # re-measure, so free space / container_color aren't poisoned either.
        print("=== Closed loop 2b: reserved-zone plate backstop ===")
        protect = [b["bbox_frac"] for b in pre["text_boxes"]]
        img, plate_record = patch_reserved_zone(img, reserved_zone_frac, interior,
                                                protect, pre.get("container_color"))
        if plate_record["intrusion_detected"]:
            dirty = True
            print(f"  PLATE detected in reserved zone: {plate_record['intrusion_px']:,}px "
                  f"off base fill rgb{tuple(plate_record['base_fill_rgb'])} — "
                  f"patched {plate_record['patched_px']:,}px back to flat fill")
        else:
            print(f"  no plate intrusion in reserved zone "
                  f"(base fill rgb{tuple(plate_record['base_fill_rgb'] or ())}, "
                  f"off-fill px {plate_record['intrusion_px']:,}"
                  + (f"; {plate_record['note']}" if plate_record.get("note") else "") + ")")
    else:
        print("  [note] no reserved zone provided — plate backstop skipped", file=sys.stderr)

    if dirty:
        patched_path = out.parent / "patched.png"
        img.save(patched_path)
        measure_input = str(patched_path)
        print(f"  -> {patched_path}")

    print("=== Closed loop 3: re-measure the clean canvas ===")
    post = measure(measure_input, expected, chroma_key_hex=chroma_key_hex)
    post_path = out.parent / "measurement_post_patch.json"
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  free_space_bbox: {post['free_space_bbox']}  "
          f"optical_center: {post['optical_center']}  -> {post_path}")
    for n in post["notes"]:
        print(f"  [note] {n}", file=sys.stderr)

    report = {
        "input_image": str(image_path),
        "spec": str(spec_path),
        "ghost_patches": patch_records,
        "reserved_zone_patch": plate_record,
        "measurement_pre": str(pre_path),
        "measurement_post_patch": str(post_path),
    }
    if post["optical_center"] and post["free_space_bbox"]:
        print("=== Closed loop 4: re-anchor to the DETECTED optical center ===")
        report["reanchor"] = reanchor(layers, post["free_space_bbox"],
                                      post["optical_center"], img.size)
        for t, s in zip(layers, report["reanchor"]["shifts_frac"]):
            print(f"  {t['content']!r}: anchor {t['anchor_frac']} "
                  f"(shift {s[0]:+.4f}, {s[1]:+.4f})  size_px={t['size_px']}")
        if report["reanchor"]["size_shrink"]:
            print(f"  [note] {report['reanchor']['size_shrink']}")
    else:
        report["reanchor"] = None
        report["fallback"] = ("detection failed (no free_space/optical_center) — "
                              "anchors left at PLANNED positions (open-loop fallback)")
        print(f"  [warn] {report['fallback']}", file=sys.stderr)

    print("=== Closed loop 5: legibility guard (actual pixels behind each line) ===")
    report["legibility"] = legibility_guard(img, layers)
    for entry in report["legibility"]:
        print(f"  {entry['content']!r} {entry['color']} on rgb{tuple(entry['behind_rgb'])}: "
              f"contrast {entry['contrast']} -> {'OK' if entry['legible'] else 'ILLEGIBLE'}")

    print("=== Closed loop 6: composite with the licensed font ===")
    reanchored_spec = out.parent / "reanchored_spec.json"
    reanchored_spec.write_text(json.dumps(layers, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    base = out.parent / "_closed_loop_base.png"
    img.save(base)
    final = composite(str(base), str(reanchored_spec), str(out))
    base.unlink()

    # Fix-3 occlusion gate: read the FINAL image back. A buried headline (e.g.
    # composited onto a plate) has perfect geometry but OCRs poorly — this is
    # the gate that would have caught chroma_sign1's red-plate burial.
    print("=== Closed loop 6b: OCR-readback occlusion gate (final image) ===")
    report["occlusion_readback"] = ocr_readback(final, layers, out.parent)
    for line in report["occlusion_readback"]["lines"]:
        print(f"  {line['content']!r}: read back {line['ocr_text']!r} "
              f"conf={line['confidence']} match={line['match']} -> "
              f"{'PASS' if line['pass'] else 'FAIL'}")
    if not report["occlusion_readback"]["pass"]:
        print("  " + "=" * 64, file=sys.stderr)
        print("  OCCLUSION GATE FAILED: composited headline did not read back "
              f"legibly from {out.name} — it is buried/occluded/illegible.",
              file=sys.stderr)
        print("  " + "=" * 64, file=sys.stderr)

    if chroma_key_hex:
        # Headline composite + ghost patches all happened on the RGB sign above —
        # only NOW does the removable green backdrop get stripped for the die-cut.
        print("=== Closed loop 7: strip the chroma backdrop (die-cut deliverables) ===")
        report["chroma_strip"] = strip_chroma(final, out.parent, chroma_key_hex)

    report_path = out.parent / "placement_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"  placement report -> {report_path}")
    print(f"  Saved {final}  ({final.stat().st_size:,} bytes)")
    return final


def main():
    ap = argparse.ArgumentParser(description="Composite licensed-font text onto a generated "
                                 "sign. Default: closed-loop (measure, patch ghosts, re-anchor "
                                 "to free space). --render-scrub: place at gpt's MEASURED "
                                 "headline geometry (Axis A).")
    ap.add_argument("--image", required=True, help="generated image (painted canvas)")
    ap.add_argument("--out", required=True, help="final png path")
    ap.add_argument("--brand", default=None, help="brand (font resolution / layer fallback)")
    ap.add_argument("--chroma-key", default="",
                    help="chroma key hex (e.g. '#00B140') for chroma-contained generations: "
                    "deterministic container recovery + green-strip deliverables "
                    "(cutout.png, preview_white.png)")
    # Old reserve-box / free-space path:
    ap.add_argument("--spec", default="", help="composite_spec.json (reserve-box/free-space path)")
    # Axis A render-and-scrub path:
    ap.add_argument("--render-scrub", action="store_true",
                    help="place the licensed font at gpt's MEASURED headline geometry "
                    "(requires --lines + --brand)")
    ap.add_argument("--lines", default="",
                    help="semicolon-separated headline lines (render-scrub mode)")
    ap.add_argument("--font-role", default="chinese_primary")
    ap.add_argument("--weight-hint", default="",
                    help="font weight/family request (e.g. from the register profile)")
    ap.add_argument("--reference-job", action="store_true",
                    help="reference job: on capture failure, LEAVE gpt text + needs_review "
                    "(no free-space fallback)")
    ap.add_argument("--letter-spacing-frac", type=float, default=0.0)
    args = ap.parse_args()

    if args.render_scrub:
        if not args.brand:
            ap.error("--render-scrub requires --brand")
        lines = [s.strip() for s in args.lines.split(";") if s.strip()]
        if not lines:
            ap.error("--render-scrub requires --lines")
        rec = place_measured(args.image, lines, args.brand, args.font_role, args.weight_hint,
                             args.out, chroma_key_hex=args.chroma_key or None,
                             is_reference_job=args.reference_job,
                             letter_spacing_frac=args.letter_spacing_frac)
        print(f"status: {rec['status']}")
        if rec["status"] != "placed":
            for n in rec["capture_notes"]:
                print(f"  [capture] {n}", file=sys.stderr)
        return
    if not args.spec:
        ap.error("either --render-scrub (with --lines) or --spec is required")
    closed_loop(args.image, args.spec, args.out, brand=args.brand,
                chroma_key_hex=args.chroma_key or None)


if __name__ == "__main__":
    main()
