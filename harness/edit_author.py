#!/usr/bin/env python3
"""harness/edit_author.py - feature 023 (改图): the EDIT route's single-sign engine.

The edit counterpart of scene_author's thin driver, deliberately lean: no register, no
calibration, no authoring model call - the prompt is a DETERMINISTIC function of the
designer's verbatim instruction (the 012 lossless principle), so the derive leg is free
by construction. Generation edits the uploaded base image (the first images.edit ref);
a human-drawn region becomes an images.edit mask (transparent = editable), with a
runtime fallback recorded honestly if the API refuses the mask (FR-008: never a silent
full redraw labeled as a region edit).

CLI (mirrors scene_author's 015 flags so the conductor stays symmetric):
  --out <run_dir> [--sign-id s1] [--style-notes ...] [--prompt-only | --verify-prompt]
Exit codes: 0 ok, 2 nothing-to-verify, 3 prompt drift (the conductor's drift contract).
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# SC-003: the outside-region preservation verdict's threshold (mean absolute diff per
# channel, 0..255 scale, over pixels OUTSIDE the region). PROVISIONAL pending the T007
# mask probe (encode round-trips measure a few units of drift even on visually identical
# pixels); the audit always records the RAW stat, so the verdict can be re-judged when
# the probe pins a measured value - update HERE, dated, never silently.
OUTSIDE_REGION_MAD_THRESHOLD = 8.0


def compose_edit_prompt(instruction: str, region=None, has_products: bool = False,
                        style_notes=None) -> str:
    """PURE: the deterministic edit prompt. The instruction rides VERBATIM (never
    rephrased, expanded, or 'improved'); everything else is fixed preservation framing.
    Section order: CHANGE -> REGION (iff set) -> PRODUCT FIDELITY (iff products) ->
    PRESERVE -> OPERATOR NOTE (iff style_notes, the nudge channel)."""
    parts = [
        "EDIT THIS IMAGE. The first attached image is the design being edited (the base image).",
        "\nCHANGE (the designer's verbatim instruction; do exactly this and nothing else):\n"
        + instruction,
    ]
    if region:
        parts.append(
            "\nREGION: alter ONLY the rectangle at normalized coordinates "
            f"x={region['x']:.4f}, y={region['y']:.4f}, "
            f"width={region['w']:.4f}, height={region['h']:.4f} of the base image "
            "(origin top-left). Every pixel outside this rectangle must remain exactly "
            "as in the base image.")
    if has_products:
        parts.append(
            "\nPRODUCT FIDELITY: the additional attached images are real product photos. "
            "Where the CHANGE uses them, reproduce the actual products faithfully - same "
            "shapes, printed branding, label text, and colors; never a generic redraw. "
            "Their backgrounds are discardable.")
    parts.append(
        "\nPRESERVE: everything not named in the CHANGE instruction stays exactly as in "
        "the base image - same composition and layout, same text (every character "
        "identical), same colors, same logo. Do not restyle, re-typeset, or improve "
        "anything outside the instruction.")
    if style_notes:
        parts.append("\nOPERATOR NOTE (binding):\n" + str(style_notes))
    return "\n".join(parts) + "\n"


def edit_size(base_path) -> str:
    """The base image is the size authority: its pixel dimensions ride through the
    EXISTING aspect-preserving map (002 resolve_size) to a valid generation size."""
    from PIL import Image
    import format_size
    with Image.open(base_path) as im:
        w, h = im.size
    return format_size.size_str(format_size.resolve_size(f"{w}x{h}px"))


def _region_px(region: dict, w: int, h: int) -> tuple:
    x0 = round(region["x"] * w)
    y0 = round(region["y"] * h)
    x1 = round((region["x"] + region["w"]) * w)
    y1 = round((region["y"] + region["h"]) * h)
    return x0, y0, x1, y1


def build_region_mask(base_path, region: dict, out_path) -> dict:
    """The images.edit mask at the base image's dimensions: TRANSPARENT inside the
    region (editable), opaque outside (preserved). Returns the pixel geometry for the
    audit record."""
    from PIL import Image
    with Image.open(base_path) as im:
        w, h = im.size
    x0, y0, x1, y1 = _region_px(region, w, h)
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    hole = Image.new("RGBA", (max(x1 - x0, 1), max(y1 - y0, 1)), (0, 0, 0, 0))
    mask.paste(hole, (x0, y0))
    mask.save(out_path)
    return {"size": [w, h], "region_px": [x0, y0, x1, y1]}


FEATHER_PX = 12  # the composite seam: a soft band this wide blends region edge into base


def composite_region(base_path, edited_path, region: dict, out_path) -> dict:
    """023 hard composite (the T007 probe's lesson, 2026-07-21): the API accepts a mask
    but enforces it SOFTLY - the model regenerates the whole canvas (measured outside-mad
    ~25 on the first real run). So the DELIVERABLE is built here: the untouched base with
    ONLY the region pasted from the model output (resized to base dims), a feathered seam
    hiding the boundary. Outside the region + seam band, pixels are byte-identical to the
    base BY CONSTRUCTION - the promise the prompt alone cannot keep."""
    from PIL import Image, ImageDraw, ImageFilter
    base = Image.open(base_path).convert("RGB")
    edited = Image.open(edited_path).convert("RGB")
    if edited.size != base.size:
        edited = edited.resize(base.size)
    w, h = base.size
    x0, y0, x1, y1 = _region_px(region, w, h)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER_PX / 2))
    out = Image.composite(edited, base, mask)
    out.save(out_path)
    return {"feather_px": FEATHER_PX, "region_px": [x0, y0, x1, y1], "size": [w, h]}


def outside_region_stats(base_path, edited_path, region: dict) -> dict:
    """SC-003's auditable stat: mean absolute diff per channel (0..255) over pixels
    OUTSIDE the region, edited resized to base dims when they differ (method recorded).
    A number computed from artifacts on disk - no human judgment, no invented result."""
    from PIL import Image, ImageChops, ImageStat
    base = Image.open(base_path).convert("RGB")
    edited = Image.open(edited_path).convert("RGB")
    resized = edited.size != base.size
    if resized:
        edited = edited.resize(base.size)
    w, h = base.size
    x0, y0, x1, y1 = _region_px(region, w, h)
    diff = ImageChops.difference(base, edited)
    sum_all = sum(ImageStat.Stat(diff).sum)
    sum_inside = sum(ImageStat.Stat(diff.crop((x0, y0, x1, y1))).sum) if x1 > x0 and y1 > y0 else 0.0
    n_outside = (w * h - (x1 - x0) * (y1 - y0)) * 3
    mad = (sum_all - sum_inside) / n_outside if n_outside else None
    return {
        "outside_region_mad": round(mad, 3) if mad is not None else None,
        "threshold": OUTSIDE_REGION_MAD_THRESHOLD,
        "within": (mad is not None and mad <= OUTSIDE_REGION_MAD_THRESHOLD),
        "method": ("edited resized to base dims; " if resized else "")
                  + "mean |diff| per channel outside the region, 0-255 scale",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="023 edit route engine (see module doc)")
    parser.add_argument("--out", required=True, help="the run dir (holds inputs.json)")
    parser.add_argument("--sign-id", default="s1")
    parser.add_argument("--style-notes", default="",
                        help="the nudge channel, VERBATIM as a binding operator note")
    parser.add_argument("--prompt-only", action="store_true",
                        help="015 derive leg: write final_prompt.txt and STOP (zero spend)")
    parser.add_argument("--verify-prompt", action="store_true",
                        help="015 generate leg: exit 3 if the recomposed prompt differs "
                             "from the confirmed final_prompt.txt (drift), else spend")
    args = parser.parse_args()

    out_dir = Path(args.out)
    inputs = json.loads((out_dir / "inputs.json").read_text(encoding="utf-8"))
    if inputs.get("mode") != "edit":
        sys.exit("ERROR: edit_author requires inputs.json with mode == 'edit'.")
    base = inputs["base_image"]
    region = inputs.get("edit_region")
    products = list(inputs.get("product_images") or [])
    sign_dir = out_dir / f"sign_{args.sign_id}"
    sign_dir.mkdir(parents=True, exist_ok=True)

    prompt = compose_edit_prompt(inputs["edit_instruction"], region=region,
                                 has_products=bool(products),
                                 style_notes=args.style_notes.strip() or None)
    prompt_path = sign_dir / "final_prompt.txt"
    if args.verify_prompt:
        if not prompt_path.exists():
            print(f"ERROR: --verify-prompt: {prompt_path} does not exist; nothing was confirmed")
            sys.exit(2)
        if prompt_path.read_text(encoding="utf-8") != prompt:
            print("ERROR: --verify-prompt: the recomposed prompt differs from the confirmed "
                  "final_prompt.txt (drift between confirm and generate); nothing spent")
            sys.exit(3)
    else:
        prompt_path.write_text(prompt, encoding="utf-8")

    manifest = {
        "route": "edit", "mode": "edit", "base_image": base,
        "edit_region": region, "product_images": products,
        "licensed_type": "deferred (raw gpt edit)",
    }
    if args.prompt_only:
        manifest["note"] = "prompt-only (015 gate): generation deferred to operator confirmation"
        (sign_dir / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  final_prompt.txt : {prompt_path.stat().st_size:>8,} bytes")
        print("  [prompt-only] STOP before generation (015 pre-spend gate); no model call")
        return

    # --- the paid leg ---
    from generate import generate_variant
    size = edit_size(base)
    refs = [base] + products
    out_png = sign_dir / "generated.png"
    mask_fallback = None
    if region:
        mask_path = sign_dir / "edit_mask.png"
        mask_geom = build_region_mask(base, region, mask_path)
        manifest["mask"] = mask_geom
        try:
            gen_meta = generate_variant(prompt, refs, str(out_png), size=size,
                                        mask_path=str(mask_path))
        except Exception as exc:  # noqa: BLE001 - only a REJECTED request falls back
            from openai import BadRequestError
            if not isinstance(exc, BadRequestError):
                raise  # network/timeout/etc: propagate, never a second spend
            mask_fallback = (f"mask rejected by the API ({exc}); retried WITHOUT mask - "
                             "outside-region preservation is prompt-level only this run")
            print(f"  [mask fallback] {mask_fallback}")
            gen_meta = generate_variant(prompt, refs, str(out_png), size=size)
    else:
        gen_meta = generate_variant(prompt, refs, str(out_png), size=size)

    manifest["generation"] = gen_meta
    manifest["mask_fallback"] = mask_fallback
    if region and out_png.exists():
        # Hard composite (see composite_region): the model's raw canvas moves aside, the
        # deliverable becomes base-with-region-pasted. Both stats recorded: the model's
        # own outside-drift (drift measurement) and the deliverable's (the promise).
        model_png = sign_dir / "generated_model.png"
        out_png.rename(model_png)
        model_stats = outside_region_stats(base, model_png, region)
        comp = composite_region(base, model_png, region, out_png)
        audit = outside_region_stats(base, out_png, region)
        audit["model_output_mad"] = model_stats["outside_region_mad"]
        audit["hard_composited"] = True
        audit["composite"] = comp
        audit["model_output"] = str(model_png)
        audit["mask_used"] = mask_fallback is None
        audit["mask_fallback"] = mask_fallback
        manifest["hard_composited"] = True
        (sign_dir / "edit_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  edit_audit.json  : deliverable outside_region_mad={audit['outside_region_mad']} "
              f"(model raw {audit['model_output_mad']}; threshold {audit['threshold']}, "
              f"within={audit['within']})")
    (sign_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  generated.png    : {out_png}")


if __name__ == "__main__":
    main()
