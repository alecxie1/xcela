#!/usr/bin/env python3
"""register/reference_style_to_prompt.py — auto-generate the "match this reference
EXACTLY" gpt-image-2 prompt clause FROM a reference image (#20).

This is the missing standalone step. The ref-feed test proved that feeding a cropped
reference panel to gpt-image-2 plus an ALIGNED PROMPT (describing the ref's style and
telling the model to match it) lands far closer to the client final than text-only brand
description. BUT that aligned prompt was hand-written by a human looking at the crop (see
the gold ``PROMPT`` in ``test_reffeed.py``). This module produces an EQUIVALENT prompt
automatically:

  1. ``extract_style_descriptor(image)`` — one structured vision call (reusing the proven
     ``_vision_call`` + MODELS chain from ``calibrate_from_reference``) that captures
     EVERYTHING the gold prompt commits to (colors+roles, font feel, die-cut stroke,
     protruding hero-icon device, negatives, ...).
  2. ``assemble_aligned_prompt(descriptor, message_lines, hero_icon)`` — PURE, deterministic.
     Fixed skeleton mirroring the gold prompt's shape; only descriptor values + message vary.

NO image generation happens here — that is the orchestrator's separate step.

Usage:
  .venv/bin/python register/reference_style_to_prompt.py \
      --image "/mnt/c/Users/Alecx/Downloads/cropped ref 1.png" \
      --message "守住钱袋子" --message "护好幸福家" \
      --hero-icon "a cartoon golden money bag (钱袋子) with a white ¥ symbol, protruding past the edge" \
      --out output/refstyle_crop1
"""

import argparse
import json
import os
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
from runtime_env import load_runtime_env  # noqa: E402  (018: env > .env > legacy ~/.hermes)
load_runtime_env()

# Reuse the proven vision helper + model chain from the sibling calibrator.
# Repo root is on sys.path when run as `.venv/bin/python register/...`; add it
# defensively so `import register...` resolves regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from register.calibrate_from_reference import _vision_call  # noqa: E402


# Extended extraction prompt — a SUPERSET of calibrate_from_reference.STYLE_PROMPT.
# Every key here exists so the assembled prompt can commit to what the gold prompt
# committed to: role-tagged colors, font feel+color, BOTH the type outline and the
# whole-shape die-cut stroke, the container shape, icon style, the protruding hero-icon
# device, overall energy, and the inferred negatives.
EXTRACT_PROMPT = (
    "You are analyzing a single hand-held event sign (手举牌) graphic to extract its EXACT "
    "visual-style DNA, so a generator can reproduce the identical design language with a "
    "different message. Judge from the pixels only. Output STRICT JSON only — no code fences, "
    "no commentary. Use this exact schema:\n"
    "{\n"
    '  "colors": [\n'
    '    {"hex": "#RRGGBB", "role": "field/background"},\n'
    '    {"hex": "#RRGGBB", "role": "primary_accent"},\n'
    '    {"hex": "#RRGGBB", "role": "secondary_accent"},\n'
    '    {"hex": "#RRGGBB", "role": "text"}\n'
    "  ],\n"
    "  (For the \"field/background\" role, give the dominant FILL color of the SIGN itself — "
    "the die-cut sticker's main body color. IGNORE any photo/studio backdrop the sign is "
    "placed on; that backdrop is NOT the field.)\n"
    '  "font_feel": "<weight + roundness of the headline type, e.g. \'bold, heavy, rounded\'>",\n'
    '  "font_color": "<color of the headline characters, e.g. \'white\'>",\n'
    '  "text_treatment": "<describe the TYPE outline (thin/thick outline around the letters, its '
    'color) AND whether the whole shape has a die-cut stroke — name both if present>",\n'
    '  "container_shape": "<the die-cut sticker silhouette + the thick cut-line/border around the '
    'WHOLE sign, e.g. \'rounded die-cut sticker with a thick white cut-line border\'>",\n'
    '  "icon_style": "<illustration style of the icons, e.g. \'playful flat-vector cartoon\'>",\n'
    '  "hero_icon_device": "<does a hero icon PROTRUDE past / break out of the sign edge? Answer '
    'yes/no and DESCRIBE the protruding icon if present>",\n'
    '  "overall_energy": "<short phrase for the vibe, e.g. \'friendly, grabbable photo-prop\'>",\n'
    '  "negatives": ["<what the style is NOT — infer from what is absent. ALWAYS judge these three '
    "axes explicitly: register (is it 'not corporate'/'not formal'?), medium (is it 'not a "
    "photograph'?), and dimensionality (is it 'not 3D'?). Add any other clear negatives too>\"]\n"
    "}\n"
    "Fill EVERY key. For colors use your best hex estimate and assign each role; omit a color "
    "object only if that role is genuinely absent. Be concrete and specific."
)


def _strip_fences(raw: str) -> str:
    """Mirror the sibling code's fence-stripping JSON pattern."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        raw = raw[4:] if raw.startswith("json") else raw
        raw = raw.rsplit("```", 1)[0].strip()
    return raw


def _try_parse(raw: str) -> dict | None:
    """Best-effort parse: clean fences, then attempt a light repair of the two
    model glitches seen in practice (a premature top-level '}' closing the object
    right after the colors array, and stray '|' artifacts). Returns None if it
    still won't parse — the caller decides whether to retry the vision call."""
    cleaned = _strip_fences(raw)
    for candidate in (cleaned, _repair_json(cleaned)):
        if candidate is None:
            continue
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _repair_json(s: str) -> str | None:
    """Targeted repairs for observed model glitches. Conservative: only touches
    clear artifacts, never invents content."""
    # Drop stray pipe characters that sometimes appear (e.g. `"not minimalist"|}`).
    s = s.replace("|}", "}").replace("|]", "]")
    # A premature top-level '}' after the colors array: `...]}, "font_feel":` — the
    # model closed the whole object after the array, then kept emitting sibling keys.
    # Splice that '}' out so the remaining keys stay inside the object.
    if "]}," in s and '"font_feel"' in s:
        s = s.replace("]},", "],", 1)
    return s


def extract_style_descriptor(image_path: str, max_attempts: int = 3) -> dict:
    """One structured vision call -> the full style descriptor dict.

    Reuses ``_vision_call`` (pinned MODELS chain) from calibrate_from_reference.
    Vision output is stochastic and occasionally emits slightly malformed JSON; we
    make up to ``max_attempts`` SYNCHRONOUS calls, each with a light repair pass.
    This is a bounded retry-on-bad-output (like the SDK's max_retries / the sibling
    code's MODELS fallback), NOT a polling or monitoring loop. Raises after the last
    attempt fails — the caller reports honestly.
    """
    last_raw = ""
    for attempt in range(1, max_attempts + 1):
        last_raw = _vision_call(image_path, EXTRACT_PROMPT)
        descriptor = _try_parse(last_raw)
        if descriptor is not None:
            return descriptor
        print(f"  [warn] attempt {attempt}/{max_attempts}: vision returned non-JSON; "
              f"{'retrying' if attempt < max_attempts else 'giving up'}", file=sys.stderr)
    raise ValueError(
        f"vision returned non-JSON style descriptor after {max_attempts} attempts\n"
        f"--- last raw ---\n{last_raw}"
    )


def _color_by_role(colors: list, role: str) -> str | None:
    for c in colors or []:
        if c.get("role") == role and c.get("hex"):
            return c["hex"]
    return None


def _has(text: str, *keys: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keys)


# The reference-relationship DIAL (Axis B). Three rungs select the generation-prompt
# WORDING for a reference job; they change only what the prompt SAYS, never the
# render-and-scrub composite (Axis A). ALL THREE instruct gpt to RENDER the headline
# text (Axis A needs painted text to detect, scrub and replace) and NONE reserve a
# blank area. Edit the wording here — this is the ONE place the human tunes it.
#   extend      = make the next one in this campaign, MAX similarity (the PROVEN gold
#                 wording, verbatim shape from test_reffeed.py lines 16-29)
#   match_style = adopt the visual language, compose a FRESH layout, MID similarity
#   mood        = color/energy cue only, design independently, MIN similarity
RELATIONSHIPS = ("extend", "match_style", "mood")
DEFAULT_RELATIONSHIP = "extend"

RUNG_TEMPLATES = {
    "extend": (
        "Use the ATTACHED reference image as the EXACT visual-style template. Create ONE new "
        "hand-held event sign (手举牌) in the IDENTICAL design language: "
        "{style_commitments}.{neg_sentence}\n\n"
        "CHANGE ONLY THE MESSAGE to {num_words} large centered lines: {lines_join}. "
        "Render these characters big, bold, {font_color}, in the same {font_feel} font as the "
        "reference.\n\n"
        "HERO ICON: {hero_clause}.\n\n"
        "ONE single die-cut sign. NO logo, NO brand mark anywhere. Crisp, saturated."
    ),
    "match_style": (
        "Use the ATTACHED reference image as a STYLE reference. Adopt its visual language "
        "(palette, typography style, icon treatment, shape language, overall energy) — "
        "{style_commitments} — but compose a FRESH layout suited to this message: {lines_join}. "
        "Do not copy its exact composition; design a new arrangement in the same style. "
        "Render the message text big, bold, {font_color}, in the same {font_feel} font as the "
        "reference.{neg_sentence}\n\n"
        "HERO ICON: {hero_clause}.\n\n"
        "ONE single die-cut sign. NO logo, NO brand mark anywhere. Crisp, saturated."
    ),
    "mood": (
        "Use the ATTACHED reference image as LOOSE inspiration for mood and energy only "
        "({energy}). Design an original sign for this message: {lines_join}. Do not replicate "
        "its layout, icons, or composition; let it inform tone only. Render the message text "
        "big, bold, {font_color}.{neg_sentence}\n\n"
        "HERO ICON: {hero_clause}.\n\n"
        "ONE single die-cut sign. NO logo, NO brand mark anywhere. Crisp, saturated."
    ),
}


def assemble_aligned_prompt(
    descriptor: dict, message_lines: list[str], hero_icon: str | None,
    relationship: str = DEFAULT_RELATIONSHIP,
) -> str:
    """PURE, DETERMINISTIC. Fixed skeleton mirroring the gold prompt's shape; only the
    descriptor values + message + hero icon get spliced in. Same input -> same output.

    relationship: which dial rung (RUNG_TEMPLATES) selects the wording — 'extend'
    (max similarity, the proven gold), 'match_style' (fresh layout, same style), or
    'mood' (tone cue only). Unknown values fall back to 'extend'. The rung changes
    ONLY the wording; it never reserves a blank area and always renders the text."""
    colors = descriptor.get("colors", [])
    field_hex = _color_by_role(colors, "field/background")
    primary_hex = _color_by_role(colors, "primary_accent")
    secondary_hex = _color_by_role(colors, "secondary_accent")
    text_hex = _color_by_role(colors, "text")

    font_feel = (descriptor.get("font_feel") or "bold, rounded").strip()
    font_color = (descriptor.get("font_color") or "white").strip()
    text_treatment = (descriptor.get("text_treatment") or "").strip()
    container_shape = (descriptor.get("container_shape") or "").strip()
    icon_style = (descriptor.get("icon_style") or "flat-vector cartoon").strip()
    hero_device = (descriptor.get("hero_icon_device") or "").strip()
    energy = (descriptor.get("overall_energy") or "friendly, grabbable photo-prop").strip()
    negatives = descriptor.get("negatives") or []

    # --- Palette clause: field + accent(s), role-aware (the gold prompt knew which was which) ---
    palette_bits = []
    if field_hex:
        palette_bits.append(f"same {field_hex} field/background")
    accent_hexes = [h for h in (primary_hex, secondary_hex) if h]
    if accent_hexes:
        palette_bits.append(f"{' + '.join(accent_hexes)} accent palette")
    palette_clause = ", ".join(palette_bits) if palette_bits else "same palette as the reference"

    # --- Text-treatment clause: BOTH the type outline and the whole-shape die-cut stroke ---
    treatment_bits = []
    if text_treatment:
        treatment_bits.append(f"same typography treatment ({text_treatment})")
    # Whole-shape die-cut stroke: prefer the container_shape description; ensure it is stated.
    if container_shape:
        treatment_bits.append(f"same die-cut sticker shape with {container_shape}")
    else:
        treatment_bits.append("same thick white die-cut sticker stroke around the whole shape")
    treatment_clause = ", ".join(treatment_bits)

    # --- Hero-icon device clause (the protruding device — one of the 3 graded things) ---
    protrudes = _has(hero_device, "yes", "protrud", "break out", "breaks out", "past the edge",
                     "beyond the edge", "extends past", "sticks out", "overhang")
    if protrudes:
        icon_clause = (
            f"same {icon_style} icon style WITH a hero icon protruding past the sign edge"
        )
    else:
        icon_clause = f"same {icon_style} icon style"

    style_commitments = (
        f"same {font_feel} {font_color} Chinese typography, "
        f"{palette_clause}, {treatment_clause}, {icon_clause}, "
        f"same {energy} energy"
    )

    # --- Negatives ---
    if negatives:
        neg_clause = ". ".join(
            n.strip().rstrip(".").upper() if n.strip().lower().startswith("not ")
            else f"NOT {n.strip().rstrip('.')}"
            for n in negatives
        )
        neg_sentence = f" {neg_clause}."
    else:
        neg_sentence = " NOT corporate, NOT a photograph, NOT 3D."

    # --- Message ---
    n = len(message_lines)
    num_words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}.get(n, str(n))
    lines_join = " / ".join(
        f"{ln} (line {i + 1})" for i, ln in enumerate(message_lines)
    )

    # --- Hero icon (use arg, else derive a sensible default from the descriptor) ---
    if hero_icon:
        hero_clause = (
            f"{hero_icon}"
            + ("" if protrudes else "")
        )
        if protrudes and "protrud" not in hero_icon.lower() and "past the edge" not in hero_icon.lower():
            hero_clause += ", protruding past the edge like the reference's protruding icon"
    else:
        if protrudes and hero_device:
            hero_clause = (
                f"a single {icon_style} hero icon, {hero_device.lstrip('yes').lstrip(',. ').strip() or 'protruding past the sign edge'}"
            )
        elif hero_device:
            hero_clause = f"a single {icon_style} hero icon ({hero_device})"
        else:
            hero_clause = f"a single {icon_style} hero icon relevant to the message"

    template = RUNG_TEMPLATES.get(relationship, RUNG_TEMPLATES[DEFAULT_RELATIONSHIP])
    return template.format(
        style_commitments=style_commitments, neg_sentence=neg_sentence,
        num_words=num_words, lines_join=lines_join, font_color=font_color,
        font_feel=font_feel, hero_clause=hero_clause, energy=energy,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Auto-generate the aligned 'match this reference' prompt from a ref image."
    )
    ap.add_argument("--image", required=True)
    ap.add_argument("--message", action="append", default=[],
                    help="repeatable; one headline line per flag")
    ap.add_argument("--hero-icon", default=None,
                    help="optional explicit hero-icon description")
    ap.add_argument("--relationship", choices=RELATIONSHIPS, default=DEFAULT_RELATIONSHIP,
                    help="reference-relationship dial: selects the prompt wording rung "
                    "(extend=max similarity/proven gold, match_style=fresh layout same style, "
                    "mood=tone cue only)")
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args()

    if not args.message:
        ap.error("at least one --message is required")

    print(f"=== Extracting style descriptor from {Path(args.image).name} ===")
    descriptor = extract_style_descriptor(args.image)
    print(json.dumps(descriptor, ensure_ascii=False, indent=2))

    print(f"\n=== Assembling aligned prompt (relationship: {args.relationship}) ===")
    prompt = assemble_aligned_prompt(descriptor, args.message, args.hero_icon,
                                     relationship=args.relationship)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = out_dir / "aligned_prompt.txt"
    descriptor_path = out_dir / "style_descriptor.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    descriptor_path.write_text(
        json.dumps(descriptor, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(prompt)
    print(f"\nWrote {prompt_path} ({os.path.getsize(prompt_path):,} bytes)")
    print(f"Wrote {descriptor_path} ({os.path.getsize(descriptor_path):,} bytes)")


if __name__ == "__main__":
    main()
