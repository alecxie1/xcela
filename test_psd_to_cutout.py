"""
Deterministic, pixel-level self-test for psd_to_cutout on the 友小规 PSD fixture.

NO API calls, NO image generation, NO network. Imports the functions from
psd_to_cutout, runs the cutout, and asserts FALSIFIABLE intrinsic properties:

  1. Output is RGBA, alpha extrema == (0, 255).
  2. All four corner pixels have alpha == 0 (background removed at corners).
  3. INTERIOR PRESERVED (the key test): label the SOURCE white mask; there must be
     MANY interior white components (>= 50; fixture ~137) not touching the border,
     and EVERY pixel in them must be OPAQUE in the output. A naive remove-all-white
     regression makes these transparent and this MUST fail.
  4. No border-disconnected transparent holes: every transparent component touches
     the border (structural guarantee of edge-connected fill).
  5. Sane opaque fraction: 20%–90% of the cropped canvas.

Prints the real numbers behind every assertion and a ✓/✗ table + PASSED/FAILED line.

Run: .venv/bin/python test_psd_to_cutout.py
"""

import sys

import numpy as np
from scipy.ndimage import label
from PIL import Image

from psd_to_cutout import load_source_as_rgb, cutout_on_white, _content_bbox, _border_labels

FIXTURE = "/mnt/c/Users/Alecx/Downloads/友小规.psd"
WHITE_THRESHOLD = 240
CONTENT_PAD = 30


def main():
    print(f"Loading source: {FIXTURE}")
    img = load_source_as_rgb(FIXTURE)
    print(f"  pre-crop size (WxH): {img.size[0]}x{img.size[1]}")

    res = cutout_on_white(img, white_threshold=WHITE_THRESHOLD, content_pad=CONTENT_PAD)
    out = res["image"]
    print(f"  post-crop size (WxH): {res['postcrop_size'][0]}x{res['postcrop_size'][1]}")
    for w in res["warnings"]:
        print(f"  WARNING: {w}")

    # Reproduce the SAME crop the module used, so source-mask coords align with output.
    arr_full = np.asarray(img)
    is_white_full = np.all(arr_full >= WHITE_THRESHOLD, axis=2)
    top, bottom, left, right = _content_bbox(is_white_full, CONTENT_PAD)
    arr = arr_full[top:bottom, left:right]
    is_white = np.all(arr >= WHITE_THRESHOLD, axis=2)

    alpha = np.asarray(out.split()[-1])  # HxW uint8 alpha
    assert alpha.shape == is_white.shape, (alpha.shape, is_white.shape)

    results = []  # (name, passed, detail)

    # ── Test 1: RGBA with real alpha, extrema (0, 255) ──
    a_img = out.split()[-1]
    extrema = a_img.getextrema()
    t1 = (out.mode == "RGBA") and (extrema == (0, 255))
    results.append(("RGBA + alpha extrema == (0,255)", t1,
                    f"mode={out.mode}, alpha.getextrema()={extrema}"))

    # ── Test 2: corners removed (alpha == 0) ──
    H, W = alpha.shape
    corners = {
        "TL": int(alpha[0, 0]), "TR": int(alpha[0, W - 1]),
        "BL": int(alpha[H - 1, 0]), "BR": int(alpha[H - 1, W - 1]),
    }
    t2 = all(v == 0 for v in corners.values())
    results.append(("Corners removed (alpha==0)", t2, f"corner alphas={corners}"))

    # ── Test 3: interior preserved (THE key test) ──
    labeled, n_comp = label(is_white)
    border_labs = _border_labels(labeled)
    interior_labs = [l for l in range(1, n_comp + 1) if l not in border_labs]
    n_interior = len(interior_labs)
    # mask of all pixels belonging to interior white components
    interior_mask = np.isin(labeled, interior_labs) if interior_labs else np.zeros_like(is_white)
    n_interior_px = int(interior_mask.sum())
    # how many of those interior-white pixels are NOT opaque in the output? (must be 0)
    interior_not_opaque = int(np.count_nonzero(interior_mask & (alpha != 255)))
    t3 = (n_interior >= 50) and (interior_not_opaque == 0)
    results.append((
        "Interior white preserved (>=50 comps, all opaque)", t3,
        f"interior_components={n_interior} (need>=50), interior_px={n_interior_px}, "
        f"interior_px_not_opaque={interior_not_opaque} (need 0), "
        f"border_white_components={len(border_labs)}, total_white_components={n_comp}",
    ))

    # ── Test 4: no border-disconnected transparent holes ──
    transparent = (alpha == 0)
    tlab, t_n = label(transparent)
    t_border_labs = _border_labels(tlab)
    interior_transparent_comps = t_n - len(t_border_labs)
    t4 = (interior_transparent_comps == 0)
    results.append((
        "No interior transparent holes", t4,
        f"transparent_components={t_n}, touching_border={len(t_border_labs)}, "
        f"fully_interior={interior_transparent_comps} (need 0)",
    ))

    # ── Test 5: sane opaque fraction (20%–90%) ──
    opaque_frac = float((alpha == 255).sum()) / alpha.size
    t5 = 0.20 <= opaque_frac <= 0.90
    results.append((
        "Opaque fraction in [20%,90%]", t5,
        f"opaque_fraction={opaque_frac:.4f}",
    ))

    # ── Report ──
    print("\n" + "=" * 78)
    print("SELF-TEST RESULTS (友小规 PSD fixture, deterministic, pixel-level)")
    print("=" * 78)
    for name, ok, detail in results:
        mark = "✓" if ok else "✗"
        print(f"[{mark}] {name}")
        print(f"      {detail}")

    all_pass = all(ok for _, ok, _ in results)
    print("-" * 78)
    print("PASSED" if all_pass else "FAILED")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
