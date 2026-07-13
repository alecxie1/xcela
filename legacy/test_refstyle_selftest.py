#!/usr/bin/env python3
"""test_refstyle_selftest.py — TEXT-ONLY self-test for register/reference_style_to_prompt.py (#20).

Runs the analyzer on BOTH cropped reference panels with the SAME task the gold prompt in
test_reffeed.py uses (message 守住钱袋子 / 护好幸福家, hero icon = golden money bag with ¥), then
diffs each AUTO-generated aligned prompt against the hand-written gold PROMPT at the level of
STYLE COMMITMENTS. Prints a ✓/✗ checklist + a `CAPTURED X/8` line per crop.

NO image generation. Vision calls + text only. One synchronous foreground call per crop.
"""

import re
import sys
from pathlib import Path

from register.reference_style_to_prompt import (
    extract_style_descriptor,
    assemble_aligned_prompt,
)

CROPS = {
    "crop1": "/mnt/c/Users/Alecx/Downloads/cropped ref 1.png",
    "crop2": "/mnt/c/Users/Alecx/Downloads/cropped ref 2.png",
}

MESSAGE_LINES = ["守住钱袋子", "护好幸福家"]
HERO_ICON = "a cartoon golden money bag (钱袋子) with a white ¥ symbol, protruding past the edge"


def _hex_to_rgb(h: str):
    h = h.strip().lstrip("#")
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _field_hex(descriptor: dict) -> str | None:
    for c in descriptor.get("colors", []):
        if c.get("role") == "field/background":
            return c.get("hex")
    return None


def _any_hex_is(descriptor: dict, predicate) -> bool:
    for c in descriptor.get("colors", []):
        rgb = _hex_to_rgb(c.get("hex", ""))
        if rgb and predicate(*rgb):
            return True
    return False


def _is_red(r, g, b) -> bool:
    # includes dark/crimson reds like #8B0000 (139,0,0) and #C41E3A
    return r >= 120 and r - g >= 60 and r - b >= 60


def _is_gold(r, g, b) -> bool:
    # gold/amber: strong red+green, low-ish blue, green not far below red
    return r >= 170 and g >= 120 and b <= 150 and (r - b) >= 60 and (g - b) >= 30


def register_inverted(descriptor: dict, prompt: str) -> bool:
    """True if the analyzer flipped register toward official/corporate — the DANGEROUS miss.
    The reference signs are PLAYFUL event props; an 'official/authoritative/formal' read is
    inverted and is exactly what caused the early 太标识类 direct-feed failure. This is the
    early-warning signal for the case where the fed image might NOT rescue a bad text read."""
    energy = (descriptor.get("overall_energy") or "").lower()
    return any(w in energy for w in
               ("official", "authoritative", "formal", "corporate", "serious", "sober"))


def evaluate(prompt: str, descriptor: dict) -> list[tuple[str, bool]]:
    """Return [(label, captured?)] for each of the 8 gold-prompt style commitments."""
    p = prompt.lower()
    checks: list[tuple[str, bool]] = []

    # 1. protruding hero icon device
    checks.append((
        "protruding hero icon device",
        ("protrud" in p) or ("past the edge" in p) or ("breaks out" in p),
    ))

    # 2. thick WHITE die-cut sticker stroke around the whole shape.
    #    HONEST: the stroke must be WHITE, not merely "a stroke exists". A charcoal/black
    #    border must FAIL here (the old check counted token presence and false-greened crop1).
    container = (descriptor.get("container_shape") or "").lower()
    treatment = (descriptor.get("text_treatment") or "").lower()
    has_diecut = ("die-cut" in p or "die cut" in p)
    has_stroke_word = any(k in (container + " " + treatment + " " + p)
                          for k in ("stroke", "cut-line", "border"))
    stroke_is_white = ("white" in container or "white" in treatment
                       or "thick white" in p or "white die-cut" in p or "white cut-line" in p)
    stroke_is_dark = any(k in container for k in ("charcoal", "black", "dark "))
    checks.append((
        "thick WHITE die-cut sticker stroke around whole shape",
        has_diecut and has_stroke_word and stroke_is_white and not stroke_is_dark,
    ))

    # 3. crimson/red field color (role = field/background, reddish hex)
    field = _field_hex(descriptor)
    field_rgb = _hex_to_rgb(field) if field else None
    checks.append((
        f"crimson/red field color (field hex {field})",
        bool(field_rgb and _is_red(*field_rgb)),
    ))

    # 4. gold accent color present among colors
    checks.append((
        "gold accent color",
        _any_hex_is(descriptor, _is_gold),
    ))

    # 5. bold + rounded font weight
    feel = (descriptor.get("font_feel") or "").lower()
    checks.append((
        f"bold + rounded font weight (font_feel={descriptor.get('font_feel')!r})",
        ("bold" in feel or "heavy" in feel) and ("round" in feel or "soft" in feel),
    ))

    # 6. white headline type
    fc = (descriptor.get("font_color") or "").lower()
    checks.append((
        "white headline type",
        ("white" in fc) or bool(re.search(r"big, bold, white", p)),
    ))

    # 7. NOT corporate / NOT photo / NOT 3D negatives
    has_corp = "not corporate" in p
    has_photo = "not a photograph" in p or "not photo" in p
    has_3d = "not 3d" in p
    checks.append((
        "NOT corporate / NOT photo / NOT 3D negatives",
        has_corp and has_photo and has_3d,
    ))

    # 8. correct message
    checks.append((
        "correct message (守住钱袋子 / 护好幸福家)",
        all(line in prompt for line in MESSAGE_LINES),
    ))

    return checks


def main() -> int:
    overall_ok = True
    crop1_prompt_for_report = None

    for tag, path in CROPS.items():
        print(f"\n{'=' * 70}\n[{tag}] {path}\n{'=' * 70}")
        if not Path(path).exists():
            print(f"[{tag}] MISSING IMAGE — cannot run", flush=True)
            overall_ok = False
            continue

        descriptor = extract_style_descriptor(path)  # one foreground vision call
        prompt = assemble_aligned_prompt(descriptor, MESSAGE_LINES, HERO_ICON)
        if tag == "crop1":
            crop1_prompt_for_report = prompt

        checks = evaluate(prompt, descriptor)
        captured = sum(1 for _, ok in checks if ok)
        for label, ok in checks:
            print(f"  [{'✓' if ok else '✗'}] {label}")
        print(f"CAPTURED {captured}/8 style commitments  ({tag})")

        missed = [label for label, ok in checks if not ok]
        if missed:
            print(f"  MISSED ({tag}): " + "; ".join(missed))
        if captured < 6:
            print(f"  *** {tag} FELL SHORT of the 6/8 bar ***")
            overall_ok = False

    if crop1_prompt_for_report is not None:
        print(f"\n{'=' * 70}\nFULL crop1 aligned_prompt.txt:\n{'=' * 70}")
        print(crop1_prompt_for_report)

    print(f"\nSELF-TEST {'PASSED' if overall_ok else 'DID NOT PASS'} (>=6/8 required for each crop)")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
