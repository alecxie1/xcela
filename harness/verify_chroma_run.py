#!/usr/bin/env python3
"""verify_chroma_run.py — deterministic verification of a chroma-contained run
(CHROMA_SPEC Part 4, checks a-e). Real numbers, honest pass/fail; nothing is
hand-fixed.

  .venv/bin/python harness/verify_chroma_run.py --run output/chroma_sign1
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from measure_canvas import CHROMA_DEFRINGE_PX, CHROMA_DIST, _hex_rgb


def chroma_container_fullres(image_path: str, key_hex: str) -> np.ndarray:
    """Full-res defringed container mask, same recipe as detect_container_chroma."""
    from scipy import ndimage
    arr = np.asarray(Image.open(image_path).convert("RGB")).astype(np.int32)
    key = np.array(_hex_rgb(key_hex), np.int32)
    dist = np.sqrt(((arr - key) ** 2).sum(axis=2))
    opaque = ndimage.binary_erosion(dist > CHROMA_DIST, iterations=CHROMA_DEFRINGE_PX)
    labels, n = ndimage.label(opaque)
    if n == 0:
        return opaque
    sizes = ndimage.sum(opaque, labels, range(1, n + 1))
    return ndimage.binary_fill_holes(labels == (int(np.argmax(sizes)) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run directory (e.g. output/chroma_sign1)")
    args = ap.parse_args()
    run = Path(args.run)

    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    key_hex = manifest["chroma_key_hex"]
    pre = json.loads((run / "measurement_pre.json").read_text(encoding="utf-8"))
    placement = json.loads((run / "placement_report.json").read_text(encoding="utf-8"))
    compliance = json.loads((run / "final.png.compliance.json").read_text(encoding="utf-8"))

    results = {}

    # ---- a. chroma recovery -------------------------------------------------
    ch = pre.get("chroma", {})
    bbox = pre.get("container_bbox")
    a_components = ch.get("opaque_components_large")
    a_backdrop = ch.get("backdrop_frac")
    a_inside = bool(bbox) and 0.02 <= bbox[0] and 0.02 <= bbox[1] \
        and bbox[2] <= 0.98 and bbox[3] <= 0.98
    results["a_chroma_recovery"] = {
        "opaque_components_large": a_components,
        "backdrop_green_frac": a_backdrop,
        "container_bbox": bbox,
        "bbox_inside_[0.02,0.98]": a_inside,
        "pass": a_components == 1 and (a_backdrop or 0) > 0.12 and a_inside,
    }

    # ---- b. headline CONTAINED ---------------------------------------------
    # Text pixels = pixels that changed between the composite base (patched.png
    # if ghosts were patched, else generated.png) and final.png. Every one must
    # lie inside the container mask recovered from the base.
    base = run / ("patched.png" if (run / "patched.png").exists() else "generated.png")
    base_arr = np.asarray(Image.open(base).convert("RGB"))
    final_arr = np.asarray(Image.open(run / "final.png").convert("RGB"))
    text_px = (base_arr != final_arr).any(axis=2)
    container = chroma_container_fullres(str(base), key_hex)
    outside = int((text_px & ~container).sum())
    results["b_headline_contained"] = {
        "composite_base": base.name,
        "text_px_total": int(text_px.sum()),
        "text_px_outside_container": outside,
        "pass": outside == 0,
    }

    # ---- c. centered ---------------------------------------------------------
    re_ = placement.get("reanchor") or {}
    oc = re_.get("detected_optical_center")
    anchors = re_.get("anchors_frac") or []
    if oc and anchors:
        bcx = sum(a[0] for a in anchors) / len(anchors)
        bcy = (anchors[0][1] + anchors[-1][1]) / 2
        dx, dy = bcx - oc[0], bcy - oc[1]
        results["c_centered"] = {
            "block_center": [round(bcx, 4), round(bcy, 4)],
            "detected_optical_center": oc,
            "delta": [round(dx, 4), round(dy, 4)],
            "pass": abs(dx) <= 0.06 and abs(dy) <= 0.06,
        }
    else:
        results["c_centered"] = {"pass": False, "note": "no reanchor record — "
                                 "detection failed or open-loop fallback"}

    # ---- d. compliance --------------------------------------------------------
    results["d_compliance"] = {
        "layers": [{"content": m["content"], "resolution": m["resolution"],
                    "file": m["resolved_file"], "weight_used": m["weight_used"]}
                   for m in compliance],
        "pass": bool(compliance) and all(
            m["resolution"] == "licensed_exact" and
            "HYYuanLongHei" in str(m["resolved_file"]) for m in compliance),
    }

    # ---- e. no green fringe ----------------------------------------------------
    prev = np.asarray(Image.open(run / "preview_white.png").convert("RGB")).astype(np.int32)
    key = np.array(_hex_rgb(key_hex), np.int32)
    fringe = int((np.sqrt(((prev - key) ** 2).sum(axis=2)) <= 40).sum())
    results["e_no_green_fringe"] = {"px_within_40_of_key": fringe, "pass": fringe == 0}

    results["overall_pass"] = all(v.get("pass") for v in results.values()
                                  if isinstance(v, dict))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    (run / "verify_chroma.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
