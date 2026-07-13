#!/usr/bin/env python3
"""register/calibrate_from_reference.py — derive register CALIBRATION from one reference image.

CALIBRATOR_SPEC Part 1. The reference sets register MAGNITUDE (target coordinates);
subfields set DIRECTION (derive_register.py). Three steps:
  1. BLIND-score the ref on the Step-0 rubric (one vision call, no brand context).
  2. Extract register-relevant style attributes (second, structured vision call).
  3. Cross-check attributes vs brand DNA (answer key) -> HELD / FLEXED dimensions.

Usage:
  .venv/bin/python register/calibrate_from_reference.py \
      --image "/mnt/c/Users/Alecx/Downloads/aia real task.png" --brand aia --out <dir>
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
from runtime_env import load_runtime_env  # noqa: E402  (018: env > .env > legacy ~/.hermes)
load_runtime_env()

_REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS = ["claude-opus-4-5", "claude-sonnet-4-6"]

# Step-0 rubric, EXACT format (energy/grab recorded but not used as targets).
BLIND_PROMPT = (
    "You are scoring a single graphic-design image, completely blind — no context about who "
    "made it, for which brand, or why. Judge from the pixels only. Reply in EXACTLY this format:\n"
    "FORMALITY: <0-10>  (0 = casual/playful register, 10 = official/corporate register)\n"
    "PLAYFULNESS: <0-10>  (0 = serious/sober, 10 = fun/whimsical)\n"
    "ENERGY: <0-10>  (0 = static/calm, 10 = loud/dynamic)\n"
    "GRAB: <0-10>  (would someone at an event grab this and pose for a photo with it?)\n"
    "LOGO: <Y or N>  (is a brand logo/mark visible?)\n"
    "TOP FEATURES: <the visual features that drove your scores, 12 words max>"
)

STYLE_PROMPT = (
    "Describe this graphic design's register-relevant style attributes. Output STRICT JSON only, "
    "no fences, no extra text:\n"
    '{"dominant_colors": [{"hex": "#RRGGBB", "where": "<role in the design>"}, ...],\n'
    ' "shape_language": "<die-cut/organic vs rectangular card — describe the container shapes>",\n'
    ' "icon_style": "<cartoon / flat geometric / none — describe>",\n'
    ' "font_feel": "<rounded / sharp / script — describe the display type>",\n'
    ' "text_effects": "<white stroke outline? drop shadow? plain? describe>",\n'
    ' "logo_present": <true/false>}'
)


def _vision_call(image_path: str, prompt: str) -> str:
    import anthropic
    data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    media = "image/png" if image_path.lower().endswith("png") else "image/jpeg"
    client = anthropic.Anthropic()
    last_exc = None
    for model in MODELS:
        try:
            msg = client.messages.create(
                model=model, max_tokens=768,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                    {"type": "text", "text": prompt},
                ]}],
            )
            print(f"  [model: {model}]", file=sys.stderr)
            return msg.content[0].text.strip()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"  [warn] {model} failed: {exc}", file=sys.stderr)
    raise RuntimeError(f"all models failed: {last_exc}")


def parse_blind(raw: str) -> dict:
    out = {}
    for axis in ("FORMALITY", "PLAYFULNESS", "ENERGY", "GRAB"):
        m = re.search(rf"{axis}\s*[:：]\s*(\d+)", raw, re.I)
        if not m:
            raise ValueError(f"blind score missing {axis} in: {raw!r}")
        out[axis.lower()] = int(m.group(1))
    m = re.search(r"LOGO\s*[:：]\s*([YN])", raw, re.I)
    if not m:
        raise ValueError(f"blind score missing LOGO Y/N in: {raw!r}")
    out["logo"] = m.group(1).upper() == "Y"
    m = re.search(r"TOP FEATURES\s*[:：]\s*(.+)", raw, re.I)
    out["top_features"] = m.group(1).strip() if m else ""
    return out


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def cross_check(style: dict, blind: dict, brand_key: dict) -> tuple[list[str], list[str]]:
    """(reference − brand DNA) diff: each dimension HELD (matches brand) or FLEXED (diverges)."""
    held, flexed = [], []
    fields = brand_key.get("fields", {})

    # primary color: any dominant ref color within reasonable RGB distance of brand primary?
    primary = next((c for c in fields.get("colors", {}).get("items", []) if c.get("role") == "primary"), None)
    if primary:
        p_rgb = tuple(primary["rgb"]) if primary.get("rgb") else _hex_to_rgb(primary["printed_html"])
        best = None
        for c in style.get("dominant_colors", []):
            try:
                rgb = _hex_to_rgb(c["hex"])
            except (KeyError, ValueError):
                continue
            d = sum((a - b) ** 2 for a, b in zip(p_rgb, rgb)) ** 0.5
            if best is None or d < best[1]:
                best = (c["hex"], d)
        if best and best[1] <= 90:  # generous: VLM hex estimates are approximate
            held.append(f"primary_color: ref dominant {best[0]} ≈ brand #{primary['printed_html']} "
                        f"(ΔRGB {best[1]:.0f}) — brand DNA held")
        else:
            closest = f"closest {best[0]}, ΔRGB {best[1]:.0f}" if best else "no colors extracted"
            flexed.append(f"primary_color: no ref dominant color near brand "
                          f"#{primary['printed_html']} ({closest}) — diverges")

    # logo: brand mark is normally mandatory; absence in the ref is an instruction.
    logo_in_ref = bool(style.get("logo_present")) or blind["logo"]
    if logo_in_ref:
        held.append("logo: present in ref — brand mark held")
    else:
        flexed.append("logo: ABSENT in ref (brand mark normally mandatory) — droppable")

    # font feel: brand corporate default is the sharp display family (answer-key styles map).
    feel = str(style.get("font_feel", "")).lower()
    if any(k in feel for k in ("round", "bubbl", "script", "soft")):
        flexed.append(f"font: ref display type is {style.get('font_feel')!r} vs brand sharp corporate default")
    else:
        held.append(f"font: ref display type {style.get('font_feel')!r} matches brand sharp default")

    # shape language: corporate baseline = rectangular card.
    shape = str(style.get("shape_language", "")).lower()
    if any(k in shape for k in ("die-cut", "die cut", "organic", "bubble", "burst", "cloud", "irregular")):
        flexed.append(f"shape: ref uses {style.get('shape_language')!r} vs brand rectangular corporate baseline")
    else:
        held.append(f"shape: ref shape language {style.get('shape_language')!r} stays rectangular/corporate")

    # icon style: brand imagery is geometric/minimal; cartoon = register flex.
    icon = str(style.get("icon_style", "")).lower()
    if any(k in icon for k in ("cartoon", "emoji", "mascot", "playful", "hand-drawn")):
        flexed.append(f"icon: ref icons are {style.get('icon_style')!r} vs brand geometric/minimal imagery")
    elif "none" not in icon and icon:
        held.append(f"icon: ref icon style {style.get('icon_style')!r} within brand norm")

    # text effects: stroke outlines / shadows are off-VI playful devices.
    fx = str(style.get("text_effects", "")).lower()
    if any(k in fx for k in ("stroke", "outline", "shadow")):
        flexed.append(f"text_effects: ref uses {style.get('text_effects')!r} — playful device, not VI standard")
    return held, flexed


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate register magnitude from a reference image.")
    ap.add_argument("--image", required=True)
    ap.add_argument("--brand", required=True, help="brand key name under answer_keys/")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    brand_key = json.loads((_REPO_ROOT / "answer_keys" / f"{args.brand}.json").read_text(encoding="utf-8"))

    print("=== Call 1: blind Step-0 score ===")
    blind_raw = _vision_call(args.image, BLIND_PROMPT)
    print(blind_raw)
    blind = parse_blind(blind_raw)

    print("\n=== Call 2: style-evidence extraction ===")
    style_raw = _vision_call(args.image, STYLE_PROMPT)
    if style_raw.startswith("```"):
        style_raw = style_raw.split("```", 2)[1]
        style_raw = style_raw[4:] if style_raw.startswith("json") else style_raw
        style_raw = style_raw.rsplit("```", 1)[0].strip()
    style = json.loads(style_raw)
    print(json.dumps(style, ensure_ascii=False, indent=2))

    print("\n=== Cross-check vs brand DNA ===")
    held, flexed = cross_check(style, blind, brand_key)
    for h in held:
        print(f"  HELD   {h}")
    for f in flexed:
        print(f"  FLEXED {f}")

    calibration = {
        "register_target": {"formality": blind["formality"], "playfulness": blind["playfulness"]},
        "anchors_held": held,
        "locks_flexed": flexed,
        "style_evidence": style,
        "logo_present_in_ref": bool(style.get("logo_present")) or blind["logo"],
        "_energy_recorded": blind["energy"],
        "_grab_recorded": blind["grab"],
        "_source_image": args.image,
        "_blind_score_raw": blind_raw,
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "calibration.json"
    out_path.write_text(json.dumps(calibration, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nregister_target = formality {blind['formality']} / playfulness {blind['playfulness']} "
          f"(energy {blind['energy']}, grab {blind['grab']} recorded, not targets)")
    print(f"Saved {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
