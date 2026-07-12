#!/usr/bin/env python3
"""harness/format_size.py — physical brief size -> a valid gpt-image-2 pixel size.

Feature 002. Stdlib-only, brand- and ASSET-PROFILE-agnostic (pure aspect math; any orientation
falls out of the constraints). The conductor never read `format_size` before; this resolves it.

resolve_size(format_size, target_area) computes the valid pixel size that PRESERVES the brief's
aspect and sits NEAREST a configurable TARGET AREA (default the proven 1536x1024 ~1.57 MP operating
point), honoring the real gpt-image-2 constraints: both edges multiples of 16; max edge <= 3840;
aspect <= 3:1; total pixels in [655_360, 8_294_400]. It does NOT snap to three fixed canvases (the
allowed set is a continuum; the popular sizes are examples). Print resolution is out of reach by
design (the cap is ~8.29 MP): the tool emits a valid-aspect DRAFT.

Honest nulls (constitution V): an aspect beyond 3:1 (or below 1:3) is CLAMPED to 3:1 (or 1:3) with
needs_review; an unparseable size returns a default valid size with a note.
"""

import re

DEFAULT_TARGET_AREA = 1_572_864          # 1536 * 1024 (~1.57 MP), the proven AIA operating point
MIN_PIXELS, MAX_PIXELS = 655_360, 8_294_400
MAX_EDGE, STEP = 3840, 16
MIN_ASPECT, MAX_ASPECT = 1 / 3, 3.0
_NUM = re.compile(r"\d+(?:\.\d+)?")


def _round16(x: float) -> int:
    """Nearest positive multiple of 16, clamped into [16, MAX_EDGE]."""
    v = int(round(x / STEP)) * STEP
    return max(STEP, min(MAX_EDGE, v))


def _default(note: str) -> dict:
    """A valid default size (the proven landscape operating point) + an honest-null note."""
    w, h = 1536, 1024
    return {"requested_size": None, "width": w, "height": h, "orientation": "landscape",
            "aspect_requested": w / h, "aspect_resolved": w / h, "aspect_delta": 0.0,
            "pixels": w * h, "target_area": DEFAULT_TARGET_AREA, "note": note, "needs_review": False}


# 017: Chinese IME typography -> the ASCII the parser already understands. IDENTITY on pure
# ASCII input (every pre-017 parse is byte-identical, pinned); a string still unparseable
# after normalization takes the existing honest default + note.
_FULLWIDTH = str.maketrans("０１２３４５６７８９×Ｘｘ＊．", "0123456789xxx*.")


def _normalize_size_text(s: str) -> str:
    s = s.translate(_FULLWIDTH).replace("　", " ")   # ASCII input passes through UNCHANGED
    for zh, unit in (("厘米", "cm"), ("公分", "cm"), ("毫米", "mm"), ("英寸", "in")):
        s = s.replace(zh, unit)
    return s


def resolve_size(format_size, target_area: int = DEFAULT_TARGET_AREA) -> dict:
    """Resolve a physical size string (e.g. '60x40cm', '６０×４０厘米') to a valid
    gpt-image-2 pixel size dict. See module docstring for the contract.
    Unparseable -> default + note (honest null)."""
    format_size = _normalize_size_text(str(format_size or ""))
    nums = _NUM.findall(str(format_size or ""))
    if len(nums) < 2:
        return _default(f"could not parse a WxH size from {format_size!r}; defaulted to 1536x1024")
    w_phys, h_phys = float(nums[0]), float(nums[1])
    if w_phys <= 0 or h_phys <= 0:
        return _default(f"non-positive size in {format_size!r}; defaulted to 1536x1024")

    aspect = w_phys / h_phys
    needs_review, note = False, None
    if aspect > MAX_ASPECT:
        note = (f"requested aspect {aspect:.2f} exceeds 3:1; clamped to 3:1 "
                "(emit a valid-aspect draft, never distorted)")
        aspect, needs_review = MAX_ASPECT, True
    elif aspect < MIN_ASPECT:
        note = (f"requested aspect {aspect:.3f} is below 1:3; clamped to 1:3 "
                "(emit a valid-aspect draft, never distorted)")
        aspect, needs_review = MIN_ASPECT, True

    # Size the SHORTER edge to the target area, then derive the longer edge preserving the aspect
    # (keeps common aspects exact: 3:2 -> 1536x1024, 1:1 -> 1248x1248, 3:1 -> 2160x720).
    if aspect >= 1.0:  # landscape or square: height is the short edge
        h = _round16((target_area / aspect) ** 0.5)
        w = _round16(aspect * h)
    else:              # portrait: width is the short edge
        w = _round16((target_area * aspect) ** 0.5)
        h = _round16(w / aspect)

    # Keep within the pixel budget (the default target sits comfortably inside it; this guards
    # custom target areas / extreme aspects).
    pixels = w * h
    if pixels < MIN_PIXELS or pixels > MAX_PIXELS:
        scale = (MIN_PIXELS / pixels) ** 0.5 if pixels < MIN_PIXELS else (MAX_PIXELS / pixels) ** 0.5
        w, h = _round16(w * scale), _round16(h * scale)

    aspect_resolved = w / h
    orientation = "square" if w == h else ("landscape" if w > h else "portrait")
    return {
        "requested_size": str(format_size),
        "width": w, "height": h, "orientation": orientation,
        "aspect_requested": round(aspect, 4), "aspect_resolved": round(aspect_resolved, 4),
        "aspect_delta": round(abs(aspect_resolved - aspect), 4),
        "pixels": w * h, "target_area": target_area, "note": note, "needs_review": needs_review,
    }


def size_str(resolution: dict) -> str:
    """'WxH' for the gpt-image-2 size arg / scene_author --size."""
    return f"{resolution['width']}x{resolution['height']}"


if __name__ == "__main__":
    import json
    import sys
    for arg in (sys.argv[1:] or ["60x40cm", "40x60cm", "50x50cm", "300x100cm", "400x100cm", "garbage"]):
        print(arg, "->", json.dumps(resolve_size(arg), ensure_ascii=False))
