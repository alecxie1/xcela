#!/usr/bin/env python3
"""measure_canvas.py — the SENSOR of the closed-loop composite.

Composite placement was open-loop: anchors came from the tier-3 PLAN, but
gpt-image-2 paints its own geometry (plan frame ≠ painted frame), and sometimes
paints a ghost headline inside the reserved zone. This tool MEASURES the painted
image: OCR every text box (flagging ghost headlines that fuzzy-match the
expected composited text), detect the container interior's free space, and emit
the optical center the compositor should actually anchor to.

Honest nulls: when a detection step fails, the report carries null + a note —
geometry is never invented.

CLI:
  .venv/bin/python harness/measure_canvas.py --image IN.png --out report.json \
      [--expected-text "守住钱袋子;护好幸福家"]
"""

import argparse
import json
import re
import sys
from collections import deque
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from PIL import Image

# Downsample factor for the container/free-space grid work (pure numpy/python,
# no scipy in the venv). 1536x1024 / 4 -> 384x256: fine resolution for geometry,
# cheap enough for BFS labeling.
GRID_DOWN = 4
SAT_MIN = 90        # HSV S (0..255): "saturated" = part of a colored mass, not white/grey
VAL_MIN = 40        # HSV V: exclude near-black
HUE_TOL = 24        # hue distance (0..255 circular) for "same color as container"
EDGE_MARGIN_FRAC = 0.03   # margin kept inside container edges (frac of min canvas dim)
MIN_MASCOT_FRAC = 0.0015  # blobs smaller than this fraction of canvas aren't "large masses"

# Chroma-key container recovery (the Root-A fix, proven in proto_root_a.py):
# the generation paints the die-cut sign on a flat #00B140 backdrop, so the
# container mask is RECOVERED by color distance from the key — not guessed.
CHROMA_DIST = 90            # RGB euclidean distance from the key that counts as backdrop
CHROMA_DEFRINGE_PX = 2      # erode the opaque mask this many px (kills the AA green halo)
CHROMA_MIN_BACKDROP_FRAC = 0.02  # less green than this => key not painted; fall back
CHROMA_FILL_DIST = 60       # RGB distance from the interior's median color that still
                            # counts as "fill" (the chroma container's fill can be
                            # UNSATURATED, e.g. warm white — hue is meaningless there)


def _hex_rgb(hex_str: str) -> tuple[int, int, int]:
    s = str(hex_str).lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rel_luminance(rgb) -> float:
    """WCAG relative luminance of an sRGB color (0..255 channels)."""
    chans = []
    for v in rgb[:3]:
        c = float(v) / 255.0
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = chans
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb_a, rgb_b) -> float:
    l1, l2 = rel_luminance(rgb_a), rel_luminance(rgb_b)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


# ---------------------------------------------------------------- text (OCR)

def _norm_text(s: str) -> str:
    return re.sub(r"[\s\W_]+", "", s or "", flags=re.UNICODE).lower()


def _fuzzy_match(found: str, expected: str) -> float:
    """Similarity of an OCR string to an expected headline (0..1).
    Containment counts as a full match (OCR sometimes glues neighbors on)."""
    nf, ne = _norm_text(found), _norm_text(expected)
    if not nf or not ne:
        return 0.0
    if ne in nf or nf in ne:
        return 1.0
    return SequenceMatcher(None, nf, ne).ratio()


def detect_text(image_path: str, expected: list[str], ghost_threshold=0.6):
    """RapidOCR over the image. Returns (text_boxes, ghost_text_boxes, error).
    Each box: {text, quad_frac, bbox_frac, confidence, matched_expected?}.
    Ghosts = boxes whose text fuzzy-matches an expected composited headline —
    the model painted them despite the reservation."""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        return [], [], f"rapidocr_onnxruntime not importable: {exc}"
    with Image.open(image_path) as im:
        w, h = im.size
    ocr = RapidOCR()
    result, _elapsed = ocr(image_path)
    boxes, ghosts = [], []
    for quad, text, conf in (result or []):
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        box = {
            "text": text,
            "confidence": round(float(conf), 4),
            "quad_frac": [[round(x / w, 4), round(y / h, 4)] for x, y in quad],
            "bbox_frac": [round(min(xs) / w, 4), round(min(ys) / h, 4),
                          round(max(xs) / w, 4), round(max(ys) / h, 4)],
        }
        scores = {e: _fuzzy_match(text, e) for e in expected}
        best = max(scores.values(), default=0.0)
        if best >= ghost_threshold:
            box["matched_expected"] = max(scores, key=scores.get)
            box["match_score"] = round(best, 3)
            ghosts.append(box)
        else:
            boxes.append(box)
    return boxes, ghosts, None


# ------------------------------------------------------- container geometry

def _label_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connected component labeling via BFS (no scipy). mask: 2-D bool.
    Returns (labels int array, n_labels); label 0 = background."""
    h, w = mask.shape
    labels = np.zeros((h, w), np.int32)
    nxt = 0
    for sy in range(h):
        row = mask[sy]
        for sx in np.nonzero(row & (labels[sy] == 0))[0]:
            nxt += 1
            q = deque([(sy, int(sx))])
            labels[sy, sx] = nxt
            while q:
                y, x = q.popleft()
                for ny, nx_ in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < h and 0 <= nx_ < w and mask[ny, nx_] \
                            and labels[ny, nx_] == 0:
                        labels[ny, nx_] = nxt
                        q.append((ny, nx_))
    return labels, nxt


def _hue_dist(h1, h2):
    """Circular hue distance on the 0..255 PIL HSV wheel."""
    d = np.abs(h1.astype(np.int16) - np.int16(h2)) % 256
    return np.minimum(d, 256 - d)


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """mask with interior holes filled: a hole is an inverse-component that does
    NOT touch the grid border. (A container's white border ring touches the
    backdrop, which touches the canvas edge — so the ring is NOT a hole; the
    white-outlined ghost glyphs inside the container ARE.)"""
    inv_labels, inv_n = _label_components(~mask)
    if not inv_n:
        return mask
    border_labels = set(np.unique(np.concatenate([
        inv_labels[0, :], inv_labels[-1, :], inv_labels[:, 0], inv_labels[:, -1]])))
    holes = (inv_labels > 0) & ~np.isin(inv_labels, list(border_labels))
    return mask | holes


def _bbox_of(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _max_rectangle(free: np.ndarray):
    """Largest all-True axis-aligned rectangle in a bool grid (histogram-stack,
    O(rows*cols)). Returns (x0, y0, x1, y1) in grid coords or None."""
    h, w = free.shape
    heights = np.zeros(w, np.int32)
    best = (0, None)
    for y in range(h):
        heights = np.where(free[y], heights + 1, 0)
        stack = []  # (start_x, height)
        for x in range(w + 1):
            cur = heights[x] if x < w else 0
            start = x
            while stack and stack[-1][1] >= cur:
                sx, sh = stack.pop()
                area = sh * (x - sx)
                if area > best[0]:
                    best = (area, (sx, y - sh + 1, x, y + 1))
                start = sx
            stack.append((start, cur))
    return best[1]


def detect_container(image_path: str, text_boxes_frac: list[list[float]],
                     fit_wh_frac: tuple[float, float] | None = None,
                     want_masks: bool = False):
    """Container interior free-space geometry. Returns a dict with honest nulls.

    Strategy: on a downsampled grid, mask saturated pixels; 4-connected
    components are split naturally by the white container border, so the
    container = the largest saturated component that does NOT touch the canvas
    border (the backdrop does). Interior free space = container-colored cells
    minus OCR text boxes, minus non-container-hue blobs (mascot/icons), minus
    an edge margin. Optical center = center of the largest free rectangle
    (exact optimality not required — robustness is)."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    small = img.resize((w // GRID_DOWN, h // GRID_DOWN), Image.BILINEAR)
    gw, gh = small.size
    hsv = np.asarray(small.convert("HSV"))
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    sat = (S >= SAT_MIN) & (V >= VAL_MIN)

    report = {"container_bbox": None, "container_color": None, "free_space_bbox": None,
              "optical_center": None, "mascot_bbox": None, "notes": []}
    masks = {"grid_wh": (gw, gh), "container": None, "container_filled": None,
             "backdrop": None}

    def _ret():
        return (report, masks) if want_masks else report

    labels, n = _label_components(sat)
    if n == 0:
        report["notes"].append("no saturated component found — container detection failed")
        return _ret()
    # Component sizes + border contact. Border-touching saturated components are
    # the BACKDROP (the canvas behind the container) — kept as a mask so patch
    # callers can stay clear of the container's border ring next to it.
    border = np.zeros_like(sat)
    border[0, :] = border[-1, :] = True
    border[:, 0] = border[:, -1] = True
    backdrop = np.zeros_like(sat)
    best_label, best_size = 0, 0
    for lab in range(1, n + 1):
        comp = labels == lab
        size = int(comp.sum())
        if (comp & border).any():
            backdrop |= comp
        elif size > best_size:
            best_label, best_size = lab, size
    masks["backdrop"] = backdrop
    if best_label == 0:
        report["notes"].append("every saturated component touches the canvas border — "
                               "cannot tell container from backdrop; container=null")
        return _ret()
    container = labels == best_label
    masks["container"] = container
    masks["container_filled"] = _fill_holes(container)
    cb = _bbox_of(container)
    report["container_bbox"] = [round(cb[0] / gw, 4), round(cb[1] / gh, 4),
                                round(cb[2] / gw, 4), round(cb[3] / gh, 4)]

    _interior_geometry(small, container, text_boxes_frac, fit_wh_frac, report)
    return _ret()


def _interior_geometry(small: Image.Image, container: np.ndarray,
                       text_boxes_frac: list[list[float]],
                       fit_wh_frac: tuple[float, float] | None,
                       report: dict,
                       blob_exclude: np.ndarray | None = None,
                       fill_rgb_dist: float | None = None) -> dict:
    """Shared interior machinery for both container-detection paths: container
    fill color, mascot/icon blobs, interior free space (minus OCR text boxes,
    blobs and an edge margin), optical center. Mutates and returns `report`.

    blob_exclude: grid cells never counted as mascot blobs (the chroma path
    passes the green backdrop, whose hue is trivially off-fill).
    fill_rgb_dist: None => legacy hue logic (the container component IS the
    saturated fill, so hue matching works). When set (chroma path), the die-cut
    interior's dominant fill may be UNSATURATED (e.g. warm white) — hue is
    meaningless and the saturated cells may be ghost ink, not fill — so the
    fill reference is the median RGB over ALL container cells, and fill
    membership is RGB distance <= fill_rgb_dist."""
    gw, gh = small.size
    hsv = np.asarray(small.convert("HSV"))
    H = hsv[..., 0]
    sat = (hsv[..., 1] >= SAT_MIN) & (hsv[..., 2] >= VAL_MIN)
    rgb_small = np.asarray(small)

    if fill_rgb_dist is not None:
        fill_color = np.median(rgb_small[container].astype(np.int32), axis=0)
        report["container_color"] = [int(v) for v in fill_color]
        cdist = np.sqrt(((rgb_small.astype(np.int32) - fill_color) ** 2).sum(axis=2))
        is_fill = cdist <= fill_rgb_dist
        off_fill = sat & ~is_fill
    else:
        # Container reference color = median hue/RGB of the component (the
        # dominant fill; ghost ink shares the hue, which is fine — text boxes
        # are removed below).
        fill_ref = container & sat
        if not fill_ref.any():
            fill_ref = container
        cont_hue = int(np.median(H[fill_ref]))
        report["container_color"] = [int(v) for v in np.median(rgb_small[fill_ref], axis=0)]
        is_fill = _hue_dist(H, cont_hue) <= HUE_TOL
        off_fill = sat & ~is_fill

    # Large non-fill masses (mascot, icons).
    if blob_exclude is not None:
        off_fill &= ~blob_exclude
    off_labels, off_n = _label_components(off_fill)
    min_cells = MIN_MASCOT_FRAC * gw * gh
    blob_mask = np.zeros_like(sat)
    blobs = []
    for lab in range(1, off_n + 1):
        comp = off_labels == lab
        if comp.sum() >= min_cells:
            blob_mask |= comp
            blobs.append((int(comp.sum()), _bbox_of(comp)))
    if blobs:
        mb = max(blobs)[1]
        report["mascot_bbox"] = [round(mb[0] / gw, 4), round(mb[1] / gh, 4),
                                 round(mb[2] / gw, 4), round(mb[3] / gh, 4)]
    else:
        report["notes"].append("no large off-container-hue blob found — mascot_bbox=null")

    # Free space: container-colored cells of the container component...
    free = container & is_fill
    # ...minus an edge margin (erode by iterating neighbor-AND; cheap, grid-level)
    margin_cells = max(int(EDGE_MARGIN_FRAC * min(gw, gh)), 1)
    er = container.copy()
    for _ in range(margin_cells):
        er[1:, :] &= er[:-1, :].copy()
        er[:-1, :] &= er[1:, :].copy()
        er[:, 1:] &= er[:, :-1].copy()
        er[:, :-1] &= er[:, 1:].copy()
    free &= er
    # ...minus every OCR text box (ghost or not) and the icon/mascot blobs
    for x0f, y0f, x1f, y1f in text_boxes_frac:
        free[int(y0f * gh):int(np.ceil(y1f * gh)),
             int(x0f * gw):int(np.ceil(x1f * gw))] = False
    free &= ~blob_mask

    if free.sum() < 0.005 * gw * gh:
        report["notes"].append(f"free interior is only {int(free.sum())} grid cells — "
                               "free-space detection unreliable; free_space_bbox=null")
        return report

    rect = _max_rectangle(free)
    if rect is None:
        report["notes"].append("max-rectangle scan found nothing — free_space_bbox=null")
        return report
    rx0, ry0, rx1, ry1 = (int(v) for v in rect)
    report["free_space_bbox"] = [round(rx0 / gw, 4), round(ry0 / gh, 4),
                                 round(rx1 / gw, 4), round(ry1 / gh, 4)]
    report["optical_center"] = [round((rx0 + rx1) / 2 / gw, 4),
                                round((ry0 + ry1) / 2 / gh, 4)]
    if fit_wh_frac:
        fw, fh = fit_wh_frac
        if (rx1 - rx0) / gw < fw or (ry1 - ry0) / gh < fh:
            report["notes"].append(
                f"requested fit {fw:.3f}x{fh:.3f} does not fit the largest free rect "
                f"{(rx1 - rx0) / gw:.3f}x{(ry1 - ry0) / gh:.3f} — caller must shrink")
    return report


def detect_container_chroma(image_path: str, text_boxes_frac: list[list[float]],
                            fit_wh_frac: tuple[float, float] | None = None,
                            key_hex: str = "#00B140",
                            want_masks: bool = False):
    """Deterministic container recovery for chroma-key framed generations
    (Root-A fix, proto_root_a.py). The sign was generated as ONE die-cut object
    on a flat key_hex backdrop, so the container mask is RECOVERED by color
    distance from the key — no HSV guessing. Returns the SAME report shape as
    detect_container (plus a 'chroma' diagnostics block).

    DEFRINGE: the opaque mask is eroded CHROMA_DEFRINGE_PX so the anti-aliased
    green/white boundary halo never enters the container mask.
    Honest fallback: if the key backdrop is absent (<CHROMA_MIN_BACKDROP_FRAC
    of the canvas), say so in notes and run the legacy HSV path instead."""
    from scipy import ndimage

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.asarray(img).astype(np.int32)  # int16 overflows: 255²×3 > 32767
    key = _hex_rgb(key_hex)
    dist = np.sqrt(((arr - np.array(key, np.int32)) ** 2).sum(axis=2))
    green = dist <= CHROMA_DIST
    green_frac = float(green.mean())

    chroma_diag = {"key_hex": key_hex, "backdrop_frac": round(green_frac, 4),
                   "dist_threshold": CHROMA_DIST, "defringe_px": CHROMA_DEFRINGE_PX}
    if green_frac < CHROMA_MIN_BACKDROP_FRAC:
        note = (f"chroma key {key_hex} backdrop not found (frac {green_frac:.4f} < "
                f"{CHROMA_MIN_BACKDROP_FRAC}) — falling back to legacy HSV detection")
        print(f"  [note] {note}", file=sys.stderr)
        res = detect_container(image_path, text_boxes_frac, fit_wh_frac,
                               want_masks=want_masks)
        rep = res[0] if want_masks else res
        rep["notes"].append(note)
        rep["chroma"] = {**chroma_diag, "fallback_legacy": True}
        return res

    report = {"container_bbox": None, "container_color": None, "free_space_bbox": None,
              "optical_center": None, "mascot_bbox": None, "notes": [],
              "chroma": chroma_diag}
    gw, gh = w // GRID_DOWN, h // GRID_DOWN
    masks = {"grid_wh": (gw, gh), "container": None, "container_filled": None,
             "backdrop": None, "container_fullres": None}

    def _ret():
        return (report, masks) if want_masks else report

    # Opaque (non-green) mask, defringed, largest connected component, holes filled.
    opaque = ndimage.binary_erosion(dist > CHROMA_DIST, iterations=CHROMA_DEFRINGE_PX)
    labels, n = ndimage.label(opaque)
    if n == 0:
        report["notes"].append("chroma backdrop found but no opaque object survives "
                               "defringe — container=null")
        return _ret()
    sizes = ndimage.sum(opaque, labels, range(1, n + 1))
    large = int((np.asarray(sizes) > 0.01 * w * h).sum())
    chroma_diag["opaque_components_total"] = int(n)
    chroma_diag["opaque_components_large"] = large
    if large != 1:
        report["notes"].append(
            f"chroma containment not clean: {large} large opaque components "
            "(expected exactly 1 die-cut object) — using the largest")
    container_full = ndimage.binary_fill_holes(labels == (int(np.argmax(sizes)) + 1))
    masks["container_fullres"] = container_full
    cb = _bbox_of(container_full)
    report["container_bbox"] = [round(cb[0] / w, 4), round(cb[1] / h, 4),
                                round(cb[2] / w, 4), round(cb[3] / h, 4)]

    # Grid-level masks for the shared interior machinery (and for callers that
    # keep ghost patches off the container border — same contract as legacy).
    small = img.resize((gw, gh), Image.BILINEAR)
    container = np.asarray(Image.fromarray(container_full.astype(np.uint8) * 255)
                           .resize((gw, gh), Image.NEAREST)) > 0
    backdrop = np.asarray(Image.fromarray(green.astype(np.uint8) * 255)
                          .resize((gw, gh), Image.NEAREST)) > 0
    masks["container"] = container
    masks["container_filled"] = container
    masks["backdrop"] = backdrop
    if not container.any():
        report["notes"].append("container vanished at grid resolution — free-space "
                               "detection skipped")
        return _ret()

    _interior_geometry(small, container, text_boxes_frac, fit_wh_frac, report,
                       blob_exclude=backdrop, fill_rgb_dist=CHROMA_FILL_DIST)
    return _ret()


# --------------------------------------------------------------------- main

def measure(image_path: str, expected_text: list[str],
            fit_wh_frac: tuple[float, float] | None = None,
            want_masks: bool = False,
            chroma_key_hex: str | None = None):
    """Full measurement report for one painted image. With want_masks=True,
    returns (report, masks) — masks carry the grid-level container footprint
    for callers that must keep patches off the container border.

    chroma_key_hex: when set, the image was generated in chroma-key containment
    mode — the container is recovered deterministically by color distance from
    the key (detect_container_chroma); else the legacy HSV path runs."""
    text_boxes, ghost_boxes, ocr_error = detect_text(image_path, expected_text)
    all_boxes_frac = [b["bbox_frac"] for b in text_boxes + ghost_boxes]
    if chroma_key_hex:
        geo = detect_container_chroma(image_path, all_boxes_frac, fit_wh_frac,
                                      key_hex=chroma_key_hex, want_masks=want_masks)
    else:
        geo = detect_container(image_path, all_boxes_frac, fit_wh_frac,
                               want_masks=want_masks)
    geo, masks = geo if want_masks else (geo, None)
    report = {
        "image": str(image_path),
        "expected_text": expected_text,
        "ocr_error": ocr_error,
        "text_boxes": text_boxes,
        "ghost_text_boxes": ghost_boxes,
        **geo,
    }
    if ocr_error:
        report["notes"].append("OCR failed — ghost detection unavailable; text boxes "
                               "NOT subtracted from free space")
    return (report, masks) if want_masks else report


def main():
    ap = argparse.ArgumentParser(description="Measure a painted canvas: OCR + container geometry.")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True, help="measurement report JSON path")
    ap.add_argument("--expected-text", default="",
                    help="semicolon-separated headline strings expected to be COMPOSITED "
                    "(OCR hits matching these are ghost headlines)")
    ap.add_argument("--chroma-key", default="",
                    help="chroma key hex (e.g. '#00B140') if the image was generated in "
                    "chroma-key containment mode — container recovered deterministically "
                    "by color distance from the key instead of HSV guessing")
    args = ap.parse_args()

    expected = [s.strip() for s in args.expected_text.split(";") if s.strip()]
    report = measure(args.image, expected, chroma_key_hex=args.chroma_key or None)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"text boxes: {len(report['text_boxes'])}  ghost boxes: {len(report['ghost_text_boxes'])}")
    for b in report["ghost_text_boxes"]:
        print(f"  GHOST {b['text']!r} (conf {b['confidence']}, match {b['match_score']} "
              f"-> {b['matched_expected']!r}) bbox_frac={b['bbox_frac']}")
    print(f"container_bbox: {report['container_bbox']}")
    print(f"free_space_bbox: {report['free_space_bbox']}")
    print(f"optical_center: {report['optical_center']}")
    print(f"mascot_bbox: {report['mascot_bbox']}")
    for note in report["notes"]:
        print(f"  [note] {note}", file=sys.stderr)
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
