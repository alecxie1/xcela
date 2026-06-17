"""
Source-on-white -> clean transparent-background cutout — a reusable tool primitive.

Clients routinely hand over an IP character (mascot, logo figure) as a .psd, a .pdf,
or a flat image, sitting on a solid white background. Turning that into a clean
cutout PNG with a real alpha channel is a RECURRING capability the brand-design tool
needs, not a one-off script. This module is the parameterized, self-verifying version.

THE CORE INSIGHT (do not lose it): do NOT "remove all white pixels." The character
HAS white parts (white shirt, white socks, eye-whites, white text on the hat). Naive
white-removal punches holes in him. The correct method is EDGE-CONNECTED background
removal: only remove white that is CONNECTED TO THE IMAGE BORDER. The character's
solid outline contains the interior, so interior white components are preserved.

Method, deterministic, no model / no network:
  1. content-crop near-white margins (keep a pad);
  2. build is_white mask (ALL channels >= white_threshold);
  3. scipy.ndimage.label the white mask; background = union of white components that
     touch any border row/col; everything else stays opaque;
  4. emit crisp binary RGBA (no feather);
  5. loud sanity guard on removed-fraction (catches non-white bg / eaten subject).

House style matches extract_colors.py / extract_text_layer.py: small, single-purpose,
argparse-driven, `.venv/bin/python psd_to_cutout.py --args`. Needs NO API key, but
loads .hermes env for structural parity with its sibling extractors.

CLI:
  .venv/bin/python psd_to_cutout.py \
      --input "/mnt/c/Users/Alecx/Downloads/友小规.psd" \
      --output brands/aia/assets/youxiaogui_cutout_auto.png \
      [--white-threshold 240] [--content-pad 30]
"""

import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from PIL import Image

# Structural parity with the sibling extractors (no key actually needed here).
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".hermes" / ".env")
except Exception:
    pass

# psd_tools / fitz are imported lazily inside load_source_as_rgb so that callers who
# only need cutout_on_white (e.g. the self-test on an in-memory array) don't pay for
# the heavyweight deps or fail if one source backend is unavailable.

_RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


# ── Source loading ────────────────────────────────────────────────

def load_source_as_rgb(path: str) -> Image.Image:
    """Load a .psd / .pdf / flat-image source and return a PIL RGB image.

    - .psd -> PSDImage.open(path).composite() (CMYK-safe; composite() returns a PIL
      image already) -> RGB.
    - .pdf -> page 0, extract the LARGEST embedded image; if none, get_pixmap(dpi=300).
    - raster -> open directly.
    Raises ValueError on any other extension.
    """
    ext = Path(path).suffix.lower()

    if ext == ".psd":
        from psd_tools import PSDImage
        psd = PSDImage.open(path)
        img = psd.composite()  # already a PIL image
        if img is None:
            raise ValueError(f"PSD composited to None (empty/unsupported): {path}")
        return img.convert("RGB")

    if ext == ".pdf":
        import fitz
        doc = fitz.open(path)
        if doc.page_count == 0:
            raise ValueError(f"PDF has no pages: {path}")
        page = doc[0]
        # Pick the largest embedded image on page 0 (by pixel area).
        best = None  # (area, xref)
        for info in page.get_images(full=True):
            xref = info[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                area = pix.width * pix.height
            except Exception:
                continue
            if best is None or area > best[0]:
                best = (area, xref)
        if best is not None:
            extracted = doc.extract_image(best[1])
            import io
            img = Image.open(io.BytesIO(extracted["image"]))
            return img.convert("RGB")
        # Fallback: rasterize the page itself.
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img.convert("RGB")

    if ext in _RASTER_EXTS:
        return Image.open(path).convert("RGB")

    raise ValueError(
        f"Unsupported source extension '{ext}'. "
        f"Expected .psd, .pdf, or one of {sorted(_RASTER_EXTS)}."
    )


# ── Geometry helpers ──────────────────────────────────────────────

def _content_bbox(is_white: np.ndarray, pad: int):
    """Bounding box (top, bottom, left, right) of the non-white content, padded.

    is_white is a HxW bool array. Returns inclusive-exclusive slice bounds suitable
    for arr[top:bottom, left:right]. Raises ValueError if everything is near-white.
    """
    content = ~is_white
    rows = np.any(content, axis=1)
    cols = np.any(content, axis=0)
    if not rows.any() or not cols.any():
        raise ValueError(
            "Source is entirely near-white — no content to crop. "
            "Wrong file, or raise --white-threshold."
        )
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    h, w = is_white.shape
    top = max(int(r0) - pad, 0)
    bottom = min(int(r1) + 1 + pad, h)
    left = max(int(c0) - pad, 0)
    right = min(int(c1) + 1 + pad, w)
    return top, bottom, left, right


def _border_labels(labeled: np.ndarray) -> set:
    """Set of component labels (excluding 0/background-of-label) that touch any border."""
    border = np.concatenate([
        labeled[0, :], labeled[-1, :], labeled[:, 0], labeled[:, -1]
    ])
    labs = set(np.unique(border).tolist())
    labs.discard(0)
    return labs


# ── Core cutout ───────────────────────────────────────────────────

def cutout_on_white(img_rgb: Image.Image, white_threshold: int = 240,
                    content_pad: int = 30) -> dict:
    """Edge-connected background removal -> crisp binary RGBA cutout.

    Returns a dict with the output image plus the diagnostic numbers the CLI/report
    need:
      { "image": RGBA PIL.Image, "precrop_size": (W,H), "postcrop_size": (W,H),
        "removed_fraction": float, "interior_white_components": int,
        "border_white_components": int, "opaque_fraction": float, "warnings": [str] }

    Raises ValueError if the image is entirely near-white (nothing to cut out).
    """
    if img_rgb.mode != "RGB":
        img_rgb = img_rgb.convert("RGB")
    arr = np.asarray(img_rgb)  # HxWx3 uint8
    precrop_h, precrop_w = arr.shape[:2]

    # all channels >= threshold => near-white
    is_white_full = np.all(arr >= white_threshold, axis=2)

    # 1. content-crop with pad
    top, bottom, left, right = _content_bbox(is_white_full, content_pad)
    arr = arr[top:bottom, left:right]
    postcrop_h, postcrop_w = arr.shape[:2]

    # 2. white mask on the cropped canvas
    is_white = np.all(arr >= white_threshold, axis=2)

    # 3. edge-connected background detection
    labeled, n_comp = label(is_white)
    border_labs = _border_labels(labeled)
    # background = union of white components touching the border
    background = np.isin(labeled, list(border_labs)) if border_labs else np.zeros_like(is_white)

    interior_white = int(n_comp - len(border_labs))
    border_white = int(len(border_labs))

    # 4. crisp binary alpha
    alpha = np.where(background, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    out = Image.fromarray(rgba, mode="RGBA")

    total = alpha.size
    removed_fraction = float((alpha == 0).sum()) / total
    opaque_fraction = float((alpha == 255).sum()) / total

    # 5. loud sanity guards
    warnings = []
    if removed_fraction < 0.05:
        warnings.append(
            f"ONLY {removed_fraction:.1%} removed — background may NOT be white "
            f"(edge-connected white barely present). Output likely garbage."
        )
    if removed_fraction > 0.95:
        warnings.append(
            f"{removed_fraction:.1%} removed — the subject may have been EATEN "
            f"(near-white character on white?). Inspect output."
        )

    return {
        "image": out,
        "precrop_size": (precrop_w, precrop_h),
        "postcrop_size": (postcrop_w, postcrop_h),
        "removed_fraction": removed_fraction,
        "opaque_fraction": opaque_fraction,
        "interior_white_components": interior_white,
        "border_white_components": border_white,
        "total_white_components": int(n_comp),
        "warnings": warnings,
    }


# ── CLI ───────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Turn a source-on-white (.psd/.pdf/image) into a clean "
                    "transparent-background cutout PNG via edge-connected bg removal."
    )
    ap.add_argument("--input", required=True, help="source .psd / .pdf / image path")
    ap.add_argument("--output", required=True, help="output cutout .png path")
    ap.add_argument("--white-threshold", type=int, default=240,
                    help="a pixel is near-white if ALL channels >= this (default 240)")
    ap.add_argument("--content-pad", type=int, default=30,
                    help="px of margin kept around content after crop (default 30)")
    args = ap.parse_args(argv)

    src_ext = Path(args.input).suffix.lower()
    kind = {".psd": "psd", ".pdf": "pdf"}.get(src_ext, "image")

    print(f"input: {args.input}")
    print(f"detected source kind: {kind}")

    img = load_source_as_rgb(args.input)
    print(f"pre-crop size (WxH): {img.size[0]}x{img.size[1]}")

    res = cutout_on_white(img, white_threshold=args.white_threshold,
                          content_pad=args.content_pad)

    print(f"post-crop size (WxH): {res['postcrop_size'][0]}x{res['postcrop_size'][1]}")
    print(f"removed fraction: {res['removed_fraction']:.4f}")
    print(f"interior white components (preserved): {res['interior_white_components']}")
    print(f"border white components (background): {res['border_white_components']}")
    for w in res["warnings"]:
        print(f"WARNING: {w}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res["image"].save(out_path)
    byte_size = os.path.getsize(out_path)
    print(f"output: {out_path}  ({byte_size} bytes)")

    report = {
        "input": str(args.input),
        "source_kind": kind,
        "white_threshold": args.white_threshold,
        "content_pad": args.content_pad,
        "precrop_size": list(res["precrop_size"]),
        "postcrop_size": list(res["postcrop_size"]),
        "removed_fraction": round(res["removed_fraction"], 6),
        "opaque_fraction": round(res["opaque_fraction"], 6),
        "interior_white_components": res["interior_white_components"],
        "border_white_components": res["border_white_components"],
        "total_white_components": res["total_white_components"],
        "output_path": str(out_path),
        "output_bytes": byte_size,
        "warnings": res["warnings"],
    }
    report_path = str(out_path) + ".report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
