#!/usr/bin/env python3
"""harness/scene_author.py — Tier-3 scene-authoring experiment.

Usage:
  .venv/bin/python harness/scene_author.py --brand taichi --out output/scene_author_run1
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path.home() / ".hermes" / ".env", override=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit as kitlib  # noqa: E402  (stdlib-only kit loader; used by the kit reserve-box mode)
import prompt_elements  # noqa: E402  (stdlib mandatory/forbidden clause, feature 002)

TIER2_INTENT = {
    "subject": "new limited-edition garden fresh tomato cheeseburger",
    "asset_type": "wide horizontal poster",
    "occasion": "seasonal limited-time launch (autumn)",
    "headline_message": "限时上新 — 秘制番茄罗勒芝士堡, campaign window 10月17日-10月31日",
    "feeling": "fresh, garden-to-table, premium, NOT the usual heavy red/gold brand look",
    "reference_image": "logo only",
}

# Asset profiles: the rendering mode of the final image. Photo language (depth of
# field, camera angles) poisons flat graphic design and vice versa — the scene
# author must speak the right dialect for the asset type.
ASSET_PROFILES = {
    "photo": (
        "This asset is a PHOTOGRAPHIC scene (food/product/lifestyle photography). "
        "hero_staging should direct a photographer: camera angle, lighting, depth of field, surfaces."
    ),
    "flat_graphic": (
        "This asset is a FLAT VECTOR GRAPHIC DESIGN (sign, banner, infographic-style poster). "
        "NOT a photograph, NOT 3D, NOT realistic. hero_staging should direct a graphic designer: "
        "the hero is a flat illustration/icon; describe its construction, container shape, and visual "
        "weight relative to the text. No camera/lens/DoF language anywhere."
    ),
}

# Field definitions only — no scene hints, no color suggestions, no staging ideas.
# CONTAMINATION RULE: these describe the slot TYPE, never what to put in it for this campaign.
TIER3_FIELD_DEFS = {
    "palette_resolved": (
        "Decide on-VI vs off-VI based on the intent's feeling/occasion. "
        "If off-VI: propose a campaign palette that fits the intent, with gradient hex stops per color. "
        "If on-VI: use brand colors. In both cases list each color as an object with: "
        "name (descriptive label), hex, role (primary/accent/background/text), "
        "and optional gradient_stops (array of hex strings, light to dark or top to bottom)."
    ),
    "background": (
        "The backdrop construction: gradient direction (e.g., top-to-bottom, radial), "
        "color stop hex values and positions, any surface/ground-plane element at the bottom "
        "(what it is, what fraction of frame height)."
    ),
    "hero_staging": (
        "How the subject is physically presented: what surface/prop it rests on, "
        "camera angle in degrees from horizontal, lighting style, depth-of-field description. "
        "Be specific enough to direct a food photographer."
    ),
    "props": (
        "List of supporting scene elements with rough placement. "
        "Derive purely from the subject and the feeling; do not repeat the hero. "
        "Each: item (what it is), placement (e.g., lower-left, scattered foreground, background right)."
    ),
    "text_layout": (
        "All text elements as positioned layers, in render order (background to foreground). "
        "Each: content (exact text string, copy from headline_message or brand fields as needed), "
        "position (precise area, e.g., top-left, center-vertical-left-edge, lower-right), "
        "color_hex, scale (large/medium/small), font_style hint (bold/light/italic etc.)."
    ),
    "composition": (
        "Negative space allocation, focal hierarchy (where the eye lands first, second, third), "
        "and overall visual balance notes. One to three sentences."
    ),
    "container_shape": (
        "FLAT-GRAPHIC ASSETS ONLY (omit for photo). The outer container/card shape of the design. "
        "AVOID default rounded rectangles — prefer expressive organic shapes: speech bubble, cloud/blob, "
        "ticket stub, badge/seal, torn paper, wavy-edge card, arch. Pick ONE that fits the message's "
        "energy and say why in one clause."
    ),
    "text_graphic_hierarchy": (
        "FLAT-GRAPHIC ASSETS ONLY (omit for photo). DESIGN LAW: the TEXT is the host (主), graphics are "
        "the guest (辅) — the message must dominate. State explicitly: approximate % of visual area for "
        "text vs graphics (text should clearly dominate, e.g. 60/25), max size of any icon relative to "
        "the headline (icon must never exceed headline height), and where the icon sits so it supports "
        "rather than competes (e.g. corner accent, behind-text watermark, small side element). "
        "Supporting graphics must nonetheless remain SUBSTANTIAL — each major icon ≥ 8% of canvas "
        "height; text dominance comes from generous TEXT SIZE, never from shrinking the graphics "
        "into invisibility."
    ),
}

# Layer-2 font intelligence (flat_graphic only): the author DESIGNS the type from the
# VI's vocabulary and reserves exactly the space its own text plan needs.
GRAPHIC_TEXT_LAYOUT_DEF = (
    "All text elements as positioned layers, in render order (background to foreground). "
    "Each entry REQUIRES: content (exact text string), position (precise area), "
    "font_role (MUST be one of the answer-key typography roles in the TYPOGRAPHY VOCABULARY — "
    "never invent a font or role), "
    "weight_hint (descriptive register: heavy-display / bold / regular / light — and if a specific "
    "library member fits, name it exactly, e.g. a -75 weight member for a call-to-action headline), "
    "size_px (explicit integer; canvas is 1536x1024), color_hex, "
    "composited (boolean: true for the reserved-area headline text that will be drawn in post with "
    "the real licensed font; false for footer/small text the image model renders itself), "
    "optional letter_spacing_px. "
    "REASON about occasion register: call-to-action sign → heavy display weight; premium/elegant → "
    "lighter face; footer/body → digital/system role."
)

HEADLINE_RESERVATION_DEF = (
    "FLAT-GRAPHIC ASSETS ONLY. Object {x_frac, y_frac, w_frac, h_frac} (fractions of the 1536x1024 "
    "canvas; x_frac/y_frac = top-left corner) — the exact box the composition must keep completely "
    "clear for the composited headline text. COMPUTE it from your own text plan: lines × characters "
    "× size_px plus breathing room. Design the composition AROUND this box as the protagonist — "
    "graphics must NOT bleed past the container edges and must yield this space. "
    "Composition % rules (text dominance) still apply."
)

LOGO_PATH = "/mnt/c/Users/Alecx/Downloads/taichi burger real logo.jpg"

CANVAS = (1536, 1024)

# Chroma-key containment (Root-A fix, proven in proto_root_a.py): gpt-image-2
# does NOT support background=transparent (400 error), so die-cut props are
# generated as ONE object on a flat key-green backdrop; measure_canvas then
# recovers the container mask deterministically by color distance from the key.
CHROMA_KEY_HEX = "#00B140"


def chroma_contain_active(asset_profile: str, register_profile: dict | None,
                          force_flag: bool) -> bool:
    """Chroma-key containment is gated to flat_graphic die-cut props: an
    event_prop register (which always flexes shape:die-cut) or the explicit
    --chroma-contain flag. Poster/photo profiles are never affected."""
    if asset_profile != "flat_graphic":
        return False
    return force_flag or (register_profile or {}).get("inferred_register") == "event_prop"


def _chroma_framing_block(key_hex: str) -> str:
    """The containment directive PREPENDED to the image prompt (adapted from
    proto_root_a.py's CRITICAL FRAMING block, which proved a clean single-object
    recovery: 1 large component, transparent_frac 0.335, solidity 0.83)."""
    return (
        "CRITICAL FRAMING — READ FIRST, OVERRIDES EVERYTHING BELOW THAT CONFLICTS: "
        "Render ONE single die-cut sign as ONE discrete object CENTERED on a perfectly "
        f"flat, uniform CHROMA-KEY backdrop of pure solid {key_hex} (bright chroma green). "
        "The sign occupies about 78% of the frame, CENTERED, surrounded on ALL edges by "
        f"the flat {key_hex} green emptiness. The green is a removable backdrop — like a "
        "green screen. NOTHING may be drawn on the green except the one sign: no scattered "
        "elements, no second panel, no shadows on the green, no full-bleed fill, no other "
        "color touching the green. EVERYTHING (color fill, icons, text, decorations) lives "
        "strictly INSIDE the single die-cut shape. No icon, fill or text color may use or "
        f"approach {key_hex} green, so nothing blends with the backdrop. The entire area "
        f"outside the die-cut shape MUST be pure uniform {key_hex} green with nothing on it."
    )


def typography_vocab(brand_key: dict) -> dict | None:
    """Extract the answer key's typography block as a vocabulary for the scene author:
    roles (the only legal font_role values), VI rules (binding), and the rejected-candidate
    pile's font names as library_members (the library vocabulary with weight suffixes)."""
    typo = brand_key.get("typography") or brand_key.get("fields", {}).get("typography")
    if not typo:
        return None
    roles = {k: v.get("name") for k, v in typo.items()
             if isinstance(v, dict) and "name" in v}
    members = [c["candidate"] for c in typo.get("_candidates_rejected", [])
               if isinstance(c, dict) and "font" in str(c.get("reason", ""))]
    return {"roles": roles, "rules": typo.get("rules", []), "library_members": members}


def validate_tier3_typography(tier3: dict, vocab: dict, canvas=CANVAS) -> list[str]:
    """Deterministic post-authoring checks. Returns a list of violation strings (empty = clean)."""
    violations: list[str] = []
    roles = set(vocab["roles"])
    composited = []
    for t in tier3.get("text_layout", []):
        label = str(t.get("content", "?"))[:24]
        if t.get("font_role") not in roles:
            violations.append(
                f"text_layout {label!r}: font_role {t.get('font_role')!r} is not an "
                f"answer-key role (allowed: {sorted(roles)})")
        if not isinstance(t.get("size_px"), (int, float)) or t.get("size_px", 0) <= 0:
            violations.append(f"text_layout {label!r}: size_px missing or not a positive number")
        if t.get("composited"):
            composited.append(t)
    if not composited:
        violations.append("no text_layout entry has composited=true — the reserved headline "
                          "must be marked composited")
    hr = tier3.get("headline_reservation")
    if not isinstance(hr, dict):
        violations.append("headline_reservation missing or not an object")
        return violations
    fracs = {}
    for k in ("x_frac", "y_frac", "w_frac", "h_frac"):
        v = hr.get(k)
        if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
            violations.append(f"headline_reservation.{k}={v!r} is not a float in [0,1]")
        else:
            fracs[k] = float(v)
    if len(fracs) == 4:
        if fracs["x_frac"] + fracs["w_frac"] > 1.0 + 1e-6:
            violations.append("headline_reservation extends past the right edge (x_frac+w_frac > 1)")
        if fracs["y_frac"] + fracs["h_frac"] > 1.0 + 1e-6:
            violations.append("headline_reservation extends past the bottom edge (y_frac+h_frac > 1)")
        if composited:
            needed = sum(len(str(t.get("content", ""))) * float(t.get("size_px") or 0) ** 2
                         for t in composited) * 1.15
            avail = fracs["w_frac"] * fracs["h_frac"] * canvas[0] * canvas[1]
            if avail < needed:
                violations.append(
                    f"headline_reservation area {avail:,.0f}px² < rough text area needed "
                    f"{needed:,.0f}px² (chars × size_px² × 1.15)")
    return violations


def enforce_reservation_cap(tier3: dict, canvas=CANVAS) -> dict:
    """Mechanical post-authoring fixes (no model re-ask). Returns an adjustment record.

    1. SIZE CAP: reservation area must be ≤ needed_area × 1.25 (needed = Σ composited
       lines: chars × size_px² × 1.15). Oversized reservations made the headline float
       and starved the graphics — shrink w_frac/h_frac proportionally, keeping center.
    2. LOGO CONFLICT: warn if the reservation overlaps the typical logo zones (corners).
    """
    record: dict = {}
    composited = [t for t in tier3.get("text_layout", []) if t.get("composited")]
    hr = tier3.get("headline_reservation")
    if not composited or not isinstance(hr, dict):
        return record
    try:
        x0, y0 = float(hr["x_frac"]), float(hr["y_frac"])
        w, h = float(hr["w_frac"]), float(hr["h_frac"])
    except (KeyError, TypeError, ValueError):
        return record
    needed = sum(len(str(t.get("content", ""))) * float(t.get("size_px") or 0) ** 2
                 for t in composited) * 1.15
    avail = w * h * canvas[0] * canvas[1]
    if needed > 0 and avail > needed * 1.25:
        scale = (needed * 1.25 / avail) ** 0.5
        cx, cy = x0 + w / 2, y0 + h / 2
        w, h = w * scale, h * scale
        x0 = min(max(cx - w / 2, 0.0), 1.0 - w)
        y0 = min(max(cy - h / 2, 0.0), 1.0 - h)
        new_hr = {"x_frac": round(x0, 4), "y_frac": round(y0, 4),
                  "w_frac": round(w, 4), "h_frac": round(h, 4)}
        record["size_cap"] = {
            "reason": f"reservation {avail:,.0f}px² > needed {needed:,.0f}px² × 1.25 — "
                      f"shrunk by {scale:.3f} keeping center",
            "before": dict(hr), "after": new_hr,
        }
        hr.update(new_hr)
        print(f"  [fix] reservation oversized ({avail:,.0f}px² for {needed:,.0f}px² of text) "
              f"— shrunk to {new_hr}", file=sys.stderr)
    # Logo-conflict check: corners are where flat-graphic signs put the brand mark.
    corner_w, corner_h = 0.22, 0.18
    corners = {"top-left": (0, 0), "top-right": (1 - corner_w, 0),
               "bottom-left": (0, 1 - corner_h), "bottom-right": (1 - corner_w, 1 - corner_h)}
    overlaps = [name for name, (cx0, cy0) in corners.items()
                if x0 < cx0 + corner_w and x0 + w > cx0 and y0 < cy0 + corner_h and y0 + h > cy0]
    if overlaps:
        record["logo_conflict_warning"] = (
            f"headline_reservation overlaps typical logo zones: {', '.join(overlaps)} — "
            "verify the generated image keeps the brand mark clear of the reservation")
        print(f"  [warn] {record['logo_conflict_warning']}", file=sys.stderr)
    return record


def _rel_luminance(rgb) -> float:
    """WCAG relative luminance of an sRGB color (0..255 channels)."""
    chans = []
    for v in rgb[:3]:
        c = v / 255.0
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = chans
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def check_reservation_legibility(png_path: str, tier3: dict, min_contrast=1.8) -> list[str]:
    """Post-generation check: the headline_reservation zone is blank by construction,
    so its median color in generated.png IS the surface the composited text lands on.
    Silent illegibility (e.g. white text on a white interior) is the same cardinal-sin
    family as silent font fallback — warn LOUDLY if contrast is too low."""
    import numpy as np
    from PIL import Image
    hr = tier3.get("headline_reservation")
    composited = [t for t in tier3.get("text_layout", []) if t.get("composited")]
    if not isinstance(hr, dict) or not composited:
        return []
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    try:
        x0 = int(float(hr["x_frac"]) * w)
        y0 = int(float(hr["y_frac"]) * h)
        x1 = x0 + int(float(hr["w_frac"]) * w)
        y1 = y0 + int(float(hr["h_frac"]) * h)
    except (KeyError, TypeError, ValueError):
        return []
    zone = np.asarray(img)[y0:y1, x0:x1].reshape(-1, 3)
    if not len(zone):
        return []
    bg = np.median(zone, axis=0)
    warnings = []
    for t in composited:
        hexcolor = str(t.get("color_hex", "000000")).lstrip("#")
        try:
            rgb = tuple(int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            continue
        l1, l2 = _rel_luminance(rgb), _rel_luminance(bg)
        ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
        if ratio < min_contrast:
            warnings.append(
                f"composited layer {str(t.get('content', ''))[:24]!r} color #{hexcolor} has "
                f"contrast {ratio:.2f} (<{min_contrast}) against the reservation zone's actual "
                f"surface rgb({int(bg[0])},{int(bg[1])},{int(bg[2])}) — text will be ILLEGIBLE. "
                "The tier-3 color plan contradicts its own background (VI p51: 白色标题 only on 友邦红).")
    return warnings


def load_brand(brand: str) -> dict:
    key_path = Path(__file__).parent.parent / "answer_keys" / f"{brand}.json"
    return json.loads(key_path.read_text(encoding="utf-8"))


def _primary_color_hex(brand_key: dict) -> str:
    for c in brand_key.get("fields", {}).get("colors", {}).get("items", []):
        if c.get("role") == "primary":
            return "#" + str(c.get("printed_html", "")).lstrip("#")
    return ""


_SLIDER_SOURCES = {
    "calibration": "calibrated from the client's reference image",
    "moderated_default": "moderated register default (no reference)",
    "subfields": "from the brief subfields",
}


def _register_target_line(profile: dict) -> str:
    """MAGNITUDE line (CALIBRATOR_SPEC Part 2): only profiles that carry _slider_source
    (new derive_register output) emit it — older profile files render byte-identically.
    The interpretation is rule-coded from the numbers, never hand-written per campaign."""
    f, p = profile.get("formality"), profile.get("playfulness")
    if not profile.get("_slider_source") or f is None or p is None:
        return ""
    src = _SLIDER_SOURCES.get(profile["_slider_source"], profile["_slider_source"])
    qualifiers = []
    if p >= 6:
        qualifiers.append("clearly playful and approachable")
    if f >= 5:
        qualifiers.append("yet still reads as an official, credible piece — SOFTEN the "
                          "corporate register to this level, do NOT abandon it into pure-casual")
    elif f <= 3:
        qualifiers.append("fully casual — no corporate stiffness should survive")
    return (f"Register TARGET ({src}): formality ≈ {f}/10, playfulness ≈ {p}/10 — "
            + "; ".join(qualifiers) + ". Hit these coordinates; overshooting in either "
            "direction is a miss.")


# How each flexed lock translates into an explicit instruction. The register layer
# must carry AUTHORITY (design-note root cause #2): soft observations get crushed by
# the corporate priming, so every flex is phrased as permission AND instruction.
def _register_directive(profile: dict, brand_key: dict) -> str:
    register = profile.get("inferred_register", "unknown")
    anchor_hex = _primary_color_hex(brand_key)
    anchor_lines = []
    for a in profile.get("brand_anchors_held", []):
        if a == "primary_color":
            anchor_lines.append(
                f"primary brand color {anchor_hex} stays the dominant anchor — the design must "
                "still read unmistakably as this brand's")
        else:
            anchor_lines.append(a)
    fr = profile.get("font_resolved") or {}
    flex_instructions = {
        "logo:omit": "logo OMITTED — do NOT place the brand logo anywhere (no logo text layer, no logo prop)",
        "logo:subtle": "logo SUBTLE — small, peripheral placement only",
        "font:rounded": (
            f"font ROUNDED — headline/display type uses the rounded display family "
            f"{fr.get('family', '(rounded library family)')}"
            + (f" (weight_hint MUST name {fr['preferred_member']} exactly)" if fr.get("preferred_member") else "")
            + ", bubbly and friendly, NOT the sharp corporate gothic"),
        "shape:die-cut": (
            f"shape DIE-CUT — container_shape MUST be {profile.get('shape_language_hint', 'die-cut organic')}"),
        "palette:playful-accents": (
            f"palette PLAYFUL ACCENTS — saturated, candy-bright accent colors anchored by {anchor_hex}; "
            "this is NOT a strict-VI corporate palette"),
    }
    flex_lines = [flex_instructions.get(f, f) for f in profile.get("brand_locks_flexed", [])]
    lines = [
        "REGISTER DIRECTIVE (AUTHORITATIVE — this OVERRIDES the corporate brand-studio defaults",
        "wherever they conflict; you have explicit permission AND instruction to depart from them",
        "along the flexed dimensions below):",
        f"  Register: {register} — {profile.get('tone_hint', '')}",
        *([f"  {_register_target_line(profile)}"] if _register_target_line(profile) else []),
        "  HELD brand anchors (never flex):",
        *[f"    - {a}" for a in anchor_lines],
        "  FLEXED locks (depart from corporate defaults here — mandatory, not optional):",
        *[f"    - {f}" for f in flex_lines],
    ]
    if profile.get("icon_style_hint"):
        lines.append(f"  Icon style: {profile['icon_style_hint']}")
    if register == "event_prop":
        lines.append(
            "  Success test: a stranger at the event WANTS to grab this and pose for a photo with it. "
            "If it looks like a corporate sign, you have failed the brief.")
    return "\n".join(lines) + "\n\n"


def author_tier3(brand_key: dict, must_include: list[str] | None = None,
                 intent_override: dict | None = None,
                 asset_profile: str = "photo",
                 style_notes: list[str] | None = None,
                 register_profile: dict | None = None) -> dict:
    """Call Anthropic API to author tier-3. Prompt contains ZERO scene hints per contamination rule.

    must_include: short human-typed phrases (Tier-2 manager input) that the system MUST honor —
    e.g. ['wood pedestal staging', 'teal background']. These are arbitrary creative specifics the
    model cannot infer from intent alone; the human supplies them. This is legitimate Tier-2 input,
    NOT a target crutch — keep each phrase short, the way a non-designer would actually type it.

    intent_override: full Tier-2 intent dict for this campaign (defaults to the built-in
    Taichi TIER2_INTENT for backward compatibility).
    asset_profile: 'photo' (default) or 'flat_graphic' — selects the rendering dialect.
    style_notes: client/stakeholder feedback rules the scene MUST obey (e.g. from a prior
    review round). Injected as binding design constraints, not suggestions.
    register_profile: output of register/derive_register.py. When present, a REGISTER
    DIRECTIVE block is injected WITH AUTHORITY: it overrides the corporate priming along
    the flexed lock dimensions (and re-primes the author entirely for event_prop).
    Absent => behavior is byte-identical to before this feature existed.
    """
    intent = dict(intent_override if intent_override is not None else TIER2_INTENT)
    if must_include:
        intent["must_include"] = must_include

    profile_text = ASSET_PROFILES.get(asset_profile, ASSET_PROFILES["photo"])
    is_graphic = asset_profile == "flat_graphic"
    vocab = typography_vocab(brand_key) if is_graphic else None

    field_defs = dict(TIER3_FIELD_DEFS)
    if vocab:
        field_defs["text_layout"] = GRAPHIC_TEXT_LAYOUT_DEF
        field_defs["headline_reservation"] = HEADLINE_RESERVATION_DEF

    # Trim to identity-relevant fields only; omit verbose subjective notes.
    tier1 = {
        "brand": brand_key.get("brand"),
        "brand_en": brand_key.get("brand_en"),
        "colors": brand_key["fields"]["colors"],
        # older keys carry a free-text "fonts" field; newer ones a structured "typography"
        # block (which, for flat graphics, is also injected as the TYPOGRAPHY VOCABULARY)
        "fonts": brand_key["fields"].get("fonts")
        or {k: v.get("name") for k, v in
            (brand_key["fields"].get("typography") or {}).items()
            if isinstance(v, dict) and "name" in v},
        "slogan": brand_key["fields"]["slogan"],
        "tone": brand_key["fields"]["tone"],
        "imagery_style": brand_key["fields"]["imagery_style"],
        "motifs": brand_key["fields"]["motifs"],
    }

    style_block = ""
    if style_notes:
        style_block = (
            "BINDING DESIGN RULES (client feedback from a prior review — every rule is mandatory):\n"
            + "\n".join(f"  - {n}" for n in style_notes) + "\n\n"
        )

    typo_block = ""
    if vocab:
        typo_block = (
            "TYPOGRAPHY VOCABULARY (the ONLY type that exists for this brand — never invent "
            "font names outside it):\n"
            "  Roles (use these EXACT keys as font_role):\n"
            + "\n".join(f"    {k}: {v}" for k, v in vocab["roles"].items()) + "\n"
            "  Library members (the licensed library's faces; weight suffixes are real — "
            "higher number = heavier, e.g. -75简 is a heavy display weight, 55简 is regular):\n"
            f"    {', '.join(vocab['library_members'])}\n"
            "  VI TYPOGRAPHY RULES (verbatim, binding constraints on your choices):\n"
            + "\n".join(f"    - {r}" for r in vocab["rules"]) + "\n"
        )
        fr = (register_profile or {}).get("font_resolved") or {}
        if fr.get("preferred_member"):
            typo_block += (
                "  REGISTER FONT DIRECTIVE (authoritative for THIS asset): every headline/display "
                f"text layer's weight_hint MUST name {fr['preferred_member']} — the {fr.get('style','')} "
                f"family {fr.get('family','')} from the licensed library. Do NOT pick the default "
                "corporate display face for this asset.\n"
            )
        typo_block += "\n"

    register_block = ""
    priming = "You are an expert art director at a premium brand design studio.\n"
    if register_profile:
        register_block = _register_directive(register_profile, brand_key)
        if register_profile.get("inferred_register") == "event_prop":
            # Re-prime entirely: a soft note cannot out-shout the corporate priming
            # (design-note root cause #2) — the priming itself must change register.
            priming = (
                "You are a fun event/experiential graphic designer who makes playful, eye-catching "
                "photo props people can't resist grabbing at festivals and events.\n"
            )

    meta_prompt = (
        priming +
        "Your task: author the Tier-3 Scene Construction layer for a marketing asset.\n\n"
        f"ASSET PROFILE: {profile_text}\n\n"
        + register_block + style_block + typo_block +
        "You receive:\n"
        "  A) Tier-1 brand identity (locked brand DNA)\n"
        "  B) Tier-2 campaign intent (thin manager brief)\n"
        "  C) Tier-3 field definitions (the slots you must fill)\n\n"
        "Read the intent. Decide on-VI vs off-VI. Then fill every tier-3 slot with enough\n"
        "specificity that a designer can execute the scene without asking you anything.\n\n"
        "If the intent contains a 'must_include' list, every item in it is a NON-NEGOTIABLE\n"
        "requirement from the client — weave each one concretely into the relevant tier-3 slot\n"
        "(background, hero_staging, palette, or props). Do not paraphrase them away or treat them\n"
        "as optional. Everything else in the scene is yours to author around them.\n\n"
        f"=== A) TIER-1 BRAND IDENTITY ===\n{json.dumps(tier1, ensure_ascii=False, indent=2)}\n\n"
        f"=== B) TIER-2 CAMPAIGN INTENT ===\n{json.dumps(intent, ensure_ascii=False, indent=2)}\n\n"
        f"=== C) TIER-3 FIELD DEFINITIONS ===\n{json.dumps(field_defs, ensure_ascii=False, indent=2)}\n\n"
        "OUTPUT RULES:\n"
        "- Output STRICT JSON only. No markdown fences, no text before or after the JSON.\n"
        + (
            "- Root keys: off_vi (bool), palette_resolved, background, hero_staging, props, text_layout, "
            "composition, container_shape, text_graphic_hierarchy"
            + (", headline_reservation" if vocab else "") + ".\n"
            if is_graphic else
            "- Root keys: off_vi (bool), palette_resolved, background, hero_staging, props, text_layout, composition.\n"
        ) +
        "- palette_resolved: array of {name, hex, role, gradient_stops?}.\n"
        "- props: array of {item, placement}.\n"
        + (
            "- text_layout: array of {content, position, font_role, weight_hint, size_px, "
            "color_hex, composited, letter_spacing_px?}.\n"
            "- headline_reservation: {x_frac, y_frac, w_frac, h_frac} floats in [0,1].\n"
            if vocab else
            "- text_layout: array of {content, position, color_hex, scale, font_style}.\n"
        ) +
        "- All other fields: strings.\n"
        "- Poster canvas: 1536 × 1024 px wide horizontal.\n"
    )

    messages = [{"role": "user", "content": meta_prompt}]
    result, raw = _call_author(messages)

    if vocab:
        violations = validate_tier3_typography(result, vocab)
        validation_note = {"round1_violations": violations}
        if violations:
            print("  [warn] tier-3 typography validation failed:", file=sys.stderr)
            for v in violations:
                print(f"    - {v}", file=sys.stderr)
            reask = (
                "VALIDATION FAILED. Your tier-3 JSON violates these deterministic checks:\n"
                + "\n".join(f"  - {v}" for v in violations)
                + "\n\nFix exactly these violations and re-output the FULL corrected JSON "
                "(same root keys, strict JSON only, no fences, nothing else changed unless "
                "a fix requires it)."
            )
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": reask}]
            result, raw = _call_author(messages)
            round2 = validate_tier3_typography(result, vocab)
            validation_note["round2_violations"] = round2
            if round2:
                print("  [warn] violations REMAIN after one re-ask — proceeding best-effort:",
                      file=sys.stderr)
                for v in round2:
                    print(f"    - {v}", file=sys.stderr)
                validation_note["status"] = "best_effort_with_open_violations"
            else:
                validation_note["status"] = "clean_after_one_reask"
        else:
            validation_note["status"] = "clean_first_pass"
        adjustment = enforce_reservation_cap(result)
        if adjustment:
            validation_note["mechanical_adjustments"] = adjustment
        result["_validation"] = validation_note
    return result


def _call_author(messages: list[dict]) -> tuple[dict, str]:
    """One authoring call (model fallback chain). Returns (parsed_json, raw_text)."""
    import anthropic

    client = anthropic.Anthropic()
    for model in ["claude-opus-4-5", "claude-sonnet-4-6"]:
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=messages,
            )
            raw = msg.content[0].text.strip()
            # Strip markdown fences if the model adds them anyway.
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()
            result = json.loads(raw)
            print(f"  Model used: {model}")
            return result, raw
        except Exception as exc:
            print(f"  [warn] {model} failed: {exc}", file=sys.stderr)
    raise RuntimeError("All Anthropic models failed.")


def assemble_final_prompt(brand_key: dict, tier3: dict, asset_profile: str = "photo",
                          register_profile: dict | None = None,
                          chroma_key_hex: str | None = None,
                          render_headline: bool = False) -> str:
    """Deterministic Python renderer: tier-3 scene + tier-1 lock lines -> flat text prompt.

    register_profile (optional): flexes the lock lines it names — logo:omit drops the
    logo instruction, event_prop reframes the opening + adds a REGISTER section.
    Absent => output identical to before this feature existed.
    chroma_key_hex (optional, flat_graphic die-cut props only): prepends the
    chroma-key containment directive and reframes the backdrop as removable
    key green. Absent => output identical to before this feature existed.
    render_headline (Axis A render-and-scrub): when True, gpt is asked to RENDER the
    headline — the composited text layers are INCLUDED in the text-layout block and the
    RESERVED HEADLINE AREA block is OMITTED. When False (legacy reserve-box mode), the
    composited layers are excluded and a blank reservation is requested. Placement of the
    licensed font then happens by MEASURING gpt's painted headline (place_measured)."""
    f = brand_key["fields"]
    brand_cn = f["brand_name_cn"]["value"]
    brand_en = f.get("brand_name_en", {}).get("value", "")
    slogan = f.get("slogan", {}).get("value", "")
    motifs = f.get("motifs", {}).get("items", [])
    off_vi = tier3.get("off_vi", False)
    vi_tag = "OFF-VI CAMPAIGN — palette intentionally departs from brand standard" if off_vi else "ON-VI CAMPAIGN"
    is_graphic = asset_profile == "flat_graphic"

    def brand_colors_block():
        lines = []
        for c in f.get("colors", {}).get("items", []):
            h = c.get("printed_html") or ""
            lines.append(f"  {c.get('name_cn','')}/{c.get('name_en','')}: #{h}")
        return "\n".join(lines)

    palette = tier3.get("palette_resolved", [])
    palette_lines = []
    for p in palette:
        stops = p.get("gradient_stops", [])
        stop_str = (" → ".join(f"#{s.lstrip('#')}" for s in stops)) if stops else f"#{p.get('hex','').lstrip('#')}"
        palette_lines.append(f"  {p.get('name','')}: {stop_str} [{p.get('role','')}]")

    props = tier3.get("props", [])
    props_lines = [f"  • {p.get('item','')} — {p.get('placement','')}" for p in props]

    reservation = tier3.get("headline_reservation") if is_graphic else None

    texts = tier3.get("text_layout", [])
    text_lines = []
    for t in texts:
        if reservation and t.get("composited") and not render_headline:
            continue  # reserve-box mode: drawn in post with the real font, never in the image prompt
        size_or_scale = t.get("scale") or (f"{t['size_px']}px" if t.get("size_px") else "")
        style = t.get("font_style") or t.get("weight_hint", "")
        text_lines.append(
            f"  • \"{t.get('content','')}\" | {t.get('position','')} | "
            f"#{t.get('color_hex','').lstrip('#')} | {size_or_scale} | {style}"
        )

    reservation_lines = []
    if isinstance(reservation, dict) and not render_headline:
        try:
            x0, y0 = float(reservation["x_frac"]), float(reservation["y_frac"])
            x1 = x0 + float(reservation["w_frac"])
            y1 = y0 + float(reservation["h_frac"])
            reservation_lines = [
                "",
                "RESERVED HEADLINE AREA (mandatory, exact):",
                f"  Reserve a completely blank area spanning x = {x0:.2f} to {x1:.2f} of canvas "
                f"width and y = {y0:.2f} to {y1:.2f} of canvas height (fractions of the full "
                "1536×1024 canvas) — no text, no graphics, no icons, no marks of any kind inside "
                "this box; the headline will be added in post-production. Inside the reserved "
                "headline area render ONLY the container's flat base fill — absolutely no "
                "rectangle, plate, banner, box, panel, ribbon, shadow, frame, or shape of any "
                "different shade or color. Do NOT paint a darker or lighter panel 'behind' the "
                "future headline: the headline is added later and must sit directly on the bare "
                "flat fill. Design the composition so this blank area reads as the intentional "
                "focal zone of the design: graphics stay fully inside the container edges and "
                "yield this space to the (future) headline.",
            ]
        except (KeyError, TypeError, ValueError):
            pass  # malformed reservation already flagged by validation — omit from prompt

    rp = register_profile or {}
    flexed = rp.get("brand_locks_flexed", [])
    logo_omitted = "logo:omit" in flexed
    is_event_prop = rp.get("inferred_register") == "event_prop"
    chroma = chroma_key_hex if (chroma_key_hex and is_graphic) else None

    if is_graphic:
        if is_event_prop:
            opening = [
                f"A FLAT VECTOR GRAPHIC DESIGN: a playful hand-held event photo-prop sign "
                f"({tier3.get('asset_description', 'a die-cut event prop')}) for a {brand_cn} ({brand_en}) "
                f"event. [{vi_tag}]",
                "It is a fun, eye-catching die-cut photo prop — NOT a corporate sign, NOT a photograph, "
                "NOT 3D. Bubbly flat illustration style, festival energy, irresistibly grabbable.",
            ]
        else:
            opening = [
                f"A FLAT VECTOR GRAPHIC DESIGN: {tier3.get('asset_description', 'a designed graphic asset')} "
                f"for {brand_cn} ({brand_en}). [{vi_tag}]",
                "It is a designed flat graphic — NOT a photograph, NOT 3D, NOT photorealistic. "
                "Modern flat illustration style, advertising quality, crisp and clean.",
            ]
    else:
        opening = [
            f"A wide horizontal promotional poster for {brand_cn} ({brand_en}). [{vi_tag}]",
            "Advertising quality, professional, polished. Food photography aesthetic, photorealistic, appetizing.",
        ]

    logo_line = ("NO LOGO: this asset's register omits the brand logo — do NOT render any logo, "
                 "brand mark, or emblem anywhere."
                 if logo_omitted else
                 "USE THE SUPPLIED BRAND LOGO faithfully — place it cleanly as the brand mark. Do not redraw or distort it.")

    register_lines = []
    if rp:
        register_lines = [
            "",
            f"REGISTER: {rp.get('inferred_register', '')} — {rp.get('tone_hint', '')}",
            f"  Shape language: {rp.get('shape_language_hint', '')}",
            f"  Icon style: {rp.get('icon_style_hint', '')}",
        ]
        target_line = _register_target_line(rp)
        if target_line:
            register_lines.insert(2, f"  {target_line}")
        if "palette:playful-accents" in flexed:
            register_lines.append(
                f"  Palette: saturated playful accents anchored by the brand primary color "
                f"{_primary_color_hex(brand_key)}")

    chroma_framing = [_chroma_framing_block(chroma), ""] if chroma else []
    background_lines = [
        "BACKGROUND:",
        f"  {tier3.get('background', '')}",
    ] if not chroma else [
        "BACKGROUND:",
        f"  CHROMA-KEY BACKDROP (overrides any other backdrop idea): the entire area "
        f"outside the single die-cut sign is pure flat {chroma} chroma green with NOTHING "
        "on it. Any background treatment below applies strictly INSIDE the sign's "
        "container fill, never on the green:",
        f"  {tier3.get('background', '')}",
    ]

    sections = chroma_framing + opening + register_lines + [
        "",
        logo_line,
        "",
        "BRAND ANCHOR COLORS (held even in this register):" if rp else
        "BRAND LOCK COLORS (logo mark always uses these):",
        brand_colors_block(),
        "",
        f"CAMPAIGN PALETTE [{vi_tag}]:",
        "\n".join(palette_lines),
        "",
        *background_lines,
        "",
        "HERO STAGING:",
        f"  {tier3.get('hero_staging', '')}",
        "",
        "PROPS:",
        "\n".join(props_lines),
        "",
        "TEXT LAYOUT (render all text exactly as specified, crisply):",
        "\n".join(text_lines),
        *reservation_lines,
        "",
        f"BRAND NAME: {brand_cn} / {brand_en}",
        f"SLOGAN: {slogan}",
        f"BRAND MOTIFS (optional accent use): {', '.join(motifs)}",
        "",
        "COMPOSITION:",
        f"  {tier3.get('composition', '')}",
    ]
    if is_graphic:
        if tier3.get("container_shape"):
            sections += ["", "CONTAINER SHAPE (the outer card/frame of the design):",
                         f"  {tier3['container_shape']}"]
        if tier3.get("text_graphic_hierarchy"):
            sections += ["", "TEXT/GRAPHIC HIERARCHY (mandatory — text is the host, graphics the guest):",
                         f"  {tier3['text_graphic_hierarchy']}"]
        sections += ["", "Render all Chinese characters crisply, correctly, and perfectly legible."]
    return "\n".join(sections).strip()


def write_composite_spec(tier3: dict, brand: str, out_dir: Path) -> Path | None:
    """Derive composite_spec.json from the tier-3 plan (the single source of truth for
    type — no hand-written specs). One entry per composited=true text layer, anchored
    centered in its row of the headline_reservation box. Returns None if nothing to
    composite."""
    layers = [t for t in tier3.get("text_layout", []) if t.get("composited")]
    if not layers:
        return None
    hr = tier3.get("headline_reservation") or {}
    try:
        x0, y0 = float(hr["x_frac"]), float(hr["y_frac"])
        w, h = float(hr["w_frac"]), float(hr["h_frac"])
    except (KeyError, TypeError, ValueError):
        # validation already flagged this; fall back to a generous center box (honest best effort)
        x0, y0, w, h = 0.1, 0.2, 0.8, 0.4
    n = len(layers)
    spec = []
    for i, t in enumerate(layers):
        hint = str(t.get("weight_hint", "")).lower()
        heavy = any(k in hint for k in ("heavy", "bold", "75", "85", "95", "display"))
        color = "#" + str(t.get("color_hex", "000000")).lstrip("#")
        entry = {
            "content": t.get("content", ""),
            "font_role": t.get("font_role"),
            "brand": brand,
            "weight_hint": t.get("weight_hint"),
            "size_px": int(t.get("size_px") or 100),
            "color": color,
            "anchor_frac": [round(x0 + w / 2, 4), round(y0 + h * (i + 0.5) / n, 4)],
            "anchor": "mm",
            "letter_spacing_px": int(t.get("letter_spacing_px") or 0),
        }
        if heavy:
            # single-weight fallback file (e.g. SimHei) can't honor a heavy display
            # request — simulate weight with a same-color stroke (crude but honest).
            # Marked so the compositor DROPS it when a real licensed weight resolves.
            entry["stroke_width"] = 2
            entry["stroke_color"] = color
            entry["stroke_is_weight_simulation"] = True
        spec.append(entry)
    path = out_dir / "composite_spec.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _lines_fallback_spec(lines: list[str], brand: str, weight_hint: str,
                         base_size_px: int = 140, font_role: str = "chinese_primary") -> list[dict]:
    """Minimal stacked-center composite spec built from headline LINES (NOT tier3),
    used ONLY as the no-reference render-and-scrub capture-failure fallback: the
    closed_loop/reanchor pass then re-fits anchors + size to the detected free space,
    so base_size_px is just a seed. tier3 is not consulted."""
    n = max(len(lines), 1)
    return [{
        "content": line, "font_role": font_role, "brand": brand, "weight_hint": weight_hint,
        "size_px": base_size_px, "color": "#000000",
        "anchor_frac": [0.5, round((i + 0.5) / n, 4)], "anchor": "mm",
    } for i, line in enumerate(lines)]


# --------------------------------------------------------------------------- #
# Kit reserve-box mode (feature 001, US3). Paint panel + chosen icon in the icon
# zone, keep the text zone CLEAR, then composite the fitted licensed headline into
# it. Zones are disjoint by construction (kit schema rule 6), so no scrub is needed
# and the icon is never overpainted. Composition OWNS the zone (US2 fit clamp sizes
# type to it). No render-and-scrub, no clone (D4/D5).
# --------------------------------------------------------------------------- #

def _find(seq, key, val):
    return next((x for x in (seq or []) if x.get(key) == val), None)


def _zone_words(zone: dict) -> str:
    if not zone:
        return "center"
    cx = zone["x_frac"] + zone["w_frac"] / 2
    cy = zone["y_frac"] + zone["h_frac"] / 2
    vert = "upper" if cy < 0.38 else ("lower" if cy > 0.62 else "middle")
    horiz = "left" if cx < 0.38 else ("right" if cx > 0.62 else "center")
    return f"{vert}-{horiz}"


def _kit_headline_color(kit_profile: dict, archetype: dict) -> str:
    """White headline on a solid/crimson field; brand-primary headline on a white panel."""
    pal = {c.get("role"): c.get("hex") for c in (kit_profile.get("palette") or [])}
    treat = (archetype or {}).get("panel_treatment", "").lower()
    if "white panel" in treat:
        return pal.get("primary") or "#D31145"
    return pal.get("background") or "#FFFFFF"


def assemble_kit_prompt(kit: dict, kit_profile: dict, composition: dict) -> str:
    """Deterministic generation prompt for the kit route: paint the archetype panel + the chosen
    icon in the icon zone, and keep the reserved text zone CLEAR (the headline is composited
    later with the licensed font). No headline characters are requested in the image."""
    arch = _find(kit.get("layout_vocabulary"), "id", composition.get("chosen_archetype")) or {}
    icon = _find(kit.get("icon_vocabulary"), "id", composition.get("chosen_icon"))
    icon_desc = ((icon or {}).get("icon_description")
                 or composition.get("human_hero_icon")
                 or "a simple kit-consistent emblem")
    iz = arch.get("icon_zone") or {}
    tz = composition.get("text_zone") or arch.get("text_zone") or {}
    pal = ", ".join(f"{c.get('role')} {c.get('hex')}" for c in (kit_profile.get("palette") or []))
    accents = ", ".join(kit_profile.get("accent_vocabulary") or [])
    frame = kit_profile.get("frame_treatment") or ""
    lines = [
        "Create ONE die-cut hand-held event sign as a FLAT VECTOR GRAPHIC (not a photo, not 3D, "
        "no camera/lens/depth-of-field language): a single discrete object centered on a plain, "
        "uniform neutral background.",
        f"PANEL / LAYOUT: {arch.get('panel_treatment', '')}.",
        f"BRAND PALETTE (use these exact colors): {pal}.",
    ]
    if frame:
        lines.append(f"FRAME / EDGE TREATMENT: {frame}.")
    if accents:
        lines.append(f"ACCENT VOCABULARY (use sparingly, on-brand): {accents}.")
    lines.append(
        f"HERO ICON: {icon_desc}. Place it in the {_zone_words(iz)} region "
        f"(about x {iz.get('x_frac')} to {round(iz.get('x_frac', 0) + iz.get('w_frac', 0), 2)}, "
        f"y {iz.get('y_frac')} to {round(iz.get('y_frac', 0) + iz.get('h_frac', 0), 2)} of the canvas).")
    lines.append(
        f"RESERVED TEXT ZONE: keep the {_zone_words(tz)} region COMPLETELY CLEAR. Render NO text, "
        "NO characters, NO lettering anywhere on the sign; the headline is added afterward by "
        "compositing the licensed font. Leave that band empty.")
    if "logo:omit" in (kit_profile.get("locks_flexed") or []):
        lines.append("Do NOT render any logo or wordmark.")
    # Feature 002: the brief's mandatory/forbidden elements, VERBATIM (e.g. 分别画叉). Profile-agnostic
    # clause builder so the future photo/poster assembler reuses it unchanged.
    clause = prompt_elements.elements_clause(composition.get("mandatory_elements"),
                                             composition.get("forbidden_elements"))
    if clause:
        lines.append(clause)
    lines.append("NEGATIVES: no photographic shading, no 3D realism, no gibberish text, no "
                 "watermark, no characters of any language anywhere on the sign.")
    return "\n".join(lines)


def compose_kit_headline(kit: dict, kit_profile: dict, composition: dict, brand: str,
                         generated_png: str, out_png: str, canvas_wh=CANVAS) -> dict:
    """Fit the headline to the reserved zone (US2 clamp) and composite the licensed font into it.
    Returns {status, fit, final}. status 'unfit' is an honest null (no clipped render)."""
    from composite_text import resolve_font, fit_text_in_zone_frac, composite as _composite
    lines = [s for s in (composition.get("message") or []) if s]
    zone = composition.get("text_zone")
    if not zone or not lines:
        return {"status": "no_text", "fit": None, "final": None}
    arch = _find(kit.get("layout_vocabulary"), "id", composition.get("chosen_archetype")) or {}
    base = {"font_role": "chinese_primary", "brand": brand,
            "weight_hint": f"{kit_profile.get('font_family', '')} "
                           f"{kit_profile.get('font_index_key') or ''}".strip()}
    font_path, _m = resolve_font(base)
    fit = fit_text_in_zone_frac(lines, zone, canvas_wh, font_path)
    if not fit["fits"]:
        return {"status": "unfit", "fit": fit, "final": None}
    box = fit["rendered_box_frac"]
    n = len(lines)
    line_h = box["h_frac"] / n
    cx = zone["x_frac"] + zone["w_frac"] / 2
    color = _kit_headline_color(kit_profile, arch)
    spec = []
    for i, line in enumerate(lines):
        cy = box["y_frac"] + (i + 0.5) * line_h
        spec.append({**base, "content": line, "size_px": fit["final_size_px"],
                     "anchor_frac": [cx, cy], "anchor": "mm", "color": color})
    spec_path = Path(out_png).parent / "composite_spec.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    final = _composite(generated_png, str(spec_path), out_png)
    return {"status": "placed", "fit": fit, "final": str(final), "spec": spec, "color": color}


def _parse_size(s, default=CANVAS) -> tuple:
    """'WxH' -> (w, h); feature 002 resolved output size. Falls back to the default canvas."""
    try:
        w, h = str(s).lower().split("x")
        return (int(w), int(h))
    except (ValueError, AttributeError):
        return default


def run_kit_mode(args) -> None:
    out_dir = Path(args.out)
    canvas_wh = _parse_size(getattr(args, "size", None))
    kit = kitlib.load_kit(args.brand)
    kit_profile = (json.loads(Path(args.kit_profile).read_text(encoding="utf-8"))
                   if args.kit_profile and Path(args.kit_profile).exists() else {})
    composition = json.loads(Path(args.composition).read_text(encoding="utf-8"))
    arch = _find(kit.get("layout_vocabulary"), "id", composition.get("chosen_archetype")) or {}
    iz = arch.get("icon_zone")
    tz = composition.get("text_zone") or arch.get("text_zone")

    if args.explain:
        disjoint = bool(iz and tz and not kitlib._zones_overlap(iz, tz))
        print(json.dumps({
            "mode": "kit_reserve_box",
            "generation_prompt_source": "assemble_kit_prompt",
            "uses_tier3": False,
            "headline_rendered_in_image": False,
            "composite": "kit_reserve_box",
            "chosen_icon": composition.get("chosen_icon"),
            "chosen_archetype": composition.get("chosen_archetype"),
            "icon_zone": iz, "text_zone": tz,
            "icon_text_zones_disjoint": disjoint,
            "needs_review": composition.get("needs_review"),
            "asset_profile": args.asset_profile,
            "output_size": f"{canvas_wh[0]}x{canvas_wh[1]}",
            "mandatory_elements": composition.get("mandatory_elements") or [],
            "forbidden_elements": composition.get("forbidden_elements") or [],
            "mandatory_in_prompt": bool(prompt_elements.elements_clause(
                composition.get("mandatory_elements"), composition.get("forbidden_elements"))),
        }, ensure_ascii=False, indent=2))
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    brand_key = load_brand(args.brand)
    print("=== KIT MODE: bespoke per-message composition ===")
    print(f"  icon={composition.get('chosen_icon')} archetype={composition.get('chosen_archetype')} "
          f"needs_review={composition.get('needs_review')}")
    prompt = assemble_kit_prompt(kit, kit_profile, composition)
    (out_dir / "final_prompt.txt").write_text(prompt, encoding="utf-8")

    print("\n=== Step 4: Generate panel + icon via gpt-image-2 (text zone left clear) ===")
    sys.path.insert(0, str(Path(__file__).parent))
    from generate import generate_variant
    out_png = str(out_dir / "generated.png")
    logo_path = brand_key.get("logo_path", LOGO_PATH)
    gen_meta = generate_variant(prompt, [logo_path], out_png,
                                size=f"{canvas_wh[0]}x{canvas_wh[1]}", quality="high")

    print("\n=== Step 5: Composite the fitted licensed headline into the reserved zone ===")
    rec = compose_kit_headline(kit, kit_profile, composition, args.brand, out_png,
                               str(out_dir / "final.png"), canvas_wh=canvas_wh)
    needs_review = bool(composition.get("needs_review"))
    review_reason = composition.get("needs_review_reason")
    if rec["status"] == "unfit":
        needs_review = True
        review_reason = ((review_reason + "; " if review_reason else "")
                         + "headline does not fit the reserved text zone at min size (honest null)")
        print(f"  [needs_review] {review_reason}", file=sys.stderr)

    manifest_run = {
        "brand": args.brand,
        "asset_profile": args.asset_profile,
        "mode": "kit_reserve_box",
        "kit_profile": args.kit_profile or None,
        "composition": {"chosen_icon": composition.get("chosen_icon"),
                        "chosen_archetype": composition.get("chosen_archetype"),
                        "archetype_reused": composition.get("archetype_reused")},
        "fit": rec.get("fit"),
        "composite_status": rec["status"],
        "generation": gen_meta,
        "needs_review": needs_review,
        "needs_review_reason": review_reason,
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest_run, ensure_ascii=False, indent=2), encoding="utf-8")
    final_png = rec.get("final")
    if final_png and Path(final_png).exists():
        print(f"  Saved {final_png}")
    print("\n=== OUTPUTS (kit mode) ===")
    print(f"  generated.png : {Path(out_png).stat().st_size:>8,} bytes")
    if final_png and Path(final_png).exists():
        print(f"  final.png     : {Path(final_png).stat().st_size:>8,} bytes")
    if needs_review:
        print(f"  needs_review  : TRUE — {review_reason}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", default="taichi")
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--must-include",
        default="",
        help="Semicolon-separated human-typed must-include phrases (Tier-2 manager input), "
        "e.g. 'wood pedestal staging; teal background'. Each is a non-negotiable requirement.",
    )
    parser.add_argument("--intent-file", default="",
                        help="Path to a JSON file containing the Tier-2 intent dict for this campaign "
                        "(defaults to the built-in Taichi intent).")
    parser.add_argument("--asset-profile", default="photo", choices=["photo", "flat_graphic"],
                        help="Rendering dialect: photo (default) or flat_graphic (signs/banners).")
    parser.add_argument("--style-notes", default="",
                        help="Semicolon-separated binding design rules from client feedback, "
                        "e.g. 'varied organic container shapes; text dominates, icons secondary'.")
    parser.add_argument("--ref-image", default="",
                        help="Optional extra reference image path (style reference) passed to "
                        "images.edit alongside the logo.")
    parser.add_argument("--register-profile", default="",
                        help="Path to a register_profile.json (register/derive_register.py output). "
                        "Injects an authoritative REGISTER DIRECTIVE that relaxes the named brand "
                        "locks. Absent => prior behavior, unchanged.")
    parser.add_argument("--chroma-contain", action="store_true",
                        help="Force chroma-key containment mode (flat_graphic only): the "
                        "die-cut sign is generated as ONE object on a flat #00B140 backdrop "
                        "and the container is recovered deterministically downstream. "
                        "Auto-enabled for event_prop registers.")
    parser.add_argument("--no-closed-loop", action="store_true",
                        help="Escape hatch (reserve-box mode only): composite blindly at the "
                        "PLANNED anchors instead of measuring + re-anchoring. For A/B.")
    parser.add_argument("--aligned-prompt", default="",
                        help="REFERENCE JOB: path to a dial-selected aligned prompt "
                        "(register/reference_style_to_prompt.py). Its contents become the "
                        "generation prompt; tier-3 authoring + assemble_final_prompt are "
                        "SKIPPED and chroma is DISABLED (ref-feed wins over chroma).")
    parser.add_argument("--reserve-headline-box", action="store_true",
                        help="Legacy reserve-and-fill path: reserve a blank headline box and "
                        "composite at the detected FREE-SPACE center. DEFAULT (flag absent) is "
                        "render-and-scrub: gpt renders the headline and the licensed font is "
                        "placed at gpt's MEASURED geometry. For A/B + rollback.")
    parser.add_argument("--kit-profile", default="",
                        help="KIT JOB: path to kit_profile.json (harness/kit.py output). With "
                        "--composition, switches to kit reserve-box composition mode.")
    parser.add_argument("--composition", default="",
                        help="KIT JOB: path to this sign's composition.json (compose_select output). "
                        "Triggers kit reserve-box mode: paint panel + chosen icon, keep the text "
                        "zone clear, then composite the fitted licensed headline into it.")
    parser.add_argument("--size", default="1536x1024",
                        help="Output pixel size WxH (feature 002: resolved from the brief format_size; "
                        "drives both generation and the fit-clamp canvas). Default 1536x1024.")
    parser.add_argument("--explain", action="store_true",
                        help="Print the resolved generation-prompt SOURCE + mode + chroma as "
                        "JSON and EXIT before any model call (free structural test surface).")
    args = parser.parse_args()

    # --- Kit reserve-box mode (feature 001, US3): a fully separate route. ---
    if args.composition:
        run_kit_mode(args)
        return

    must_include = [s.strip() for s in args.must_include.split(";") if s.strip()] or None
    style_notes = [s.strip() for s in args.style_notes.split(";") if s.strip()] or None
    intent_override = None
    if args.intent_file:
        intent_override = json.loads(Path(args.intent_file).read_text(encoding="utf-8"))
    register_profile = None
    if args.register_profile:
        register_profile = json.loads(Path(args.register_profile).read_text(encoding="utf-8"))

    # --- Mode resolution (Axis A render-and-scrub default + Axis B reference jobs) ---
    is_reference_job = bool(args.aligned_prompt)
    reserve_box_mode = bool(args.reserve_headline_box) and not is_reference_job
    render_and_scrub = not reserve_box_mode
    if args.reserve_headline_box and is_reference_job:
        print("  [note] --reserve-headline-box ignored on a reference job (a full-bleed ref has "
              "no green field / free-space box) — using render-and-scrub", file=sys.stderr)
    # Reference + chroma cannot coexist: the ref sign is rendered on the reference's OWN
    # background, so there is no key-green field to recover. ref-feed wins; chroma OFF.
    if is_reference_job:
        chroma_key = None
    else:
        chroma_key = (CHROMA_KEY_HEX if chroma_contain_active(
            args.asset_profile, register_profile, args.chroma_contain) else None)

    if args.explain:
        is_graphic = args.asset_profile == "flat_graphic"
        print(json.dumps({
            "is_reference_job": is_reference_job,
            "generation_prompt_source": "aligned_prompt_file" if is_reference_job else "assemble_final_prompt",
            "aligned_prompt_path": args.aligned_prompt or None,
            "uses_tier3": not is_reference_job,
            "mode": "render_and_scrub" if render_and_scrub else "reserve_headline_box",
            "headline_rendered_in_image": render_and_scrub,
            "chroma_key_hex": chroma_key,
            "chroma_disabled_for_reference": is_reference_job,
            "asset_profile": args.asset_profile,
            "composite": ("place_measured" if (is_graphic and render_and_scrub)
                          else "closed_loop_reserve_box" if is_graphic else "none"),
        }, ensure_ascii=False, indent=2))
        return

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== Step 1: Load brand identity ===")
    brand_key = load_brand(args.brand)
    print(f"  {brand_key.get('brand')} / {brand_key.get('brand_en')}")
    print(f"  mode: {'render-and-scrub' if render_and_scrub else 'reserve-headline-box'}"
          + (" | REFERENCE JOB (aligned prompt, chroma OFF)" if is_reference_job else ""))
    if must_include:
        print(f"  must_include (human Tier-2 input): {must_include}")
    if register_profile:
        print(f"  register profile: {register_profile.get('inferred_register')} "
              f"(held: {register_profile.get('brand_anchors_held')}, "
              f"flexed: {register_profile.get('brand_locks_flexed')})")

    tier3 = None
    tier3_path = None
    if is_reference_job:
        print("\n=== Step 2+3: REFERENCE JOB — generation prompt = aligned prompt (tier-3 SKIPPED) ===")
        final_prompt = Path(args.aligned_prompt).read_text(encoding="utf-8")
        print(f"  aligned prompt: {args.aligned_prompt}  ({len(final_prompt)} chars)")
    else:
        print("\n=== Step 2: Author tier-3 via Anthropic ===")
        tier3 = author_tier3(brand_key, must_include=must_include,
                             intent_override=intent_override,
                             asset_profile=args.asset_profile,
                             style_notes=style_notes,
                             register_profile=register_profile)
        tier3_path = out_dir / "tier3_scene.json"
        tier3_path.write_text(json.dumps(tier3, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved {tier3_path}  ({tier3_path.stat().st_size} bytes)")
        if chroma_key:
            print(f"  chroma-key containment ACTIVE (key {chroma_key})")
        print("\n=== Step 3: Assemble final prompt "
              f"({'render-full-text' if render_and_scrub else 'reserve-box'}) ===")
        final_prompt = assemble_final_prompt(brand_key, tier3, asset_profile=args.asset_profile,
                                             register_profile=register_profile,
                                             chroma_key_hex=chroma_key,
                                             render_headline=render_and_scrub)
    prompt_path = out_dir / "final_prompt.txt"
    prompt_path.write_text(final_prompt, encoding="utf-8")
    print(f"  Saved {prompt_path}  ({prompt_path.stat().st_size} bytes)")

    # Legacy reserve-box mode derives a composite spec from tier3; render-and-scrub does NOT
    # (place_measured builds its spec from the MEASURED geometry + must_include lines, so tier3
    # is never a dependency of the composite). write_composite_spec(tier3) is never reached on a
    # reference job (tier3 is None there).
    spec_path = None
    if args.asset_profile == "flat_graphic" and reserve_box_mode and tier3 is not None:
        spec_path = write_composite_spec(tier3, args.brand, out_dir)
        if spec_path:
            print(f"  Saved {spec_path}  ({spec_path.stat().st_size} bytes)")

    print("\n=== Step 4: Generate image via gpt-image-2 ===")
    sys.path.insert(0, str(Path(__file__).parent))
    from generate import generate_variant
    out_png = str(out_dir / "generated.png")
    logo_path = brand_key.get("logo_path", LOGO_PATH)
    refs = [logo_path] + ([args.ref_image] if args.ref_image else [])
    if register_profile and "logo:omit" in register_profile.get("brand_locks_flexed", []):
        if args.ref_image:
            refs = [args.ref_image]
            print("  register flexes logo:omit — logo NOT passed as reference (ref image only)")
        else:
            print("  [warn] logo:omit flexed but no --ref-image — logo file still passed as "
                  "the required reference; prompt forbids rendering it", file=sys.stderr)
    gen_meta = generate_variant(final_prompt, refs, out_png, size="1536x1024", quality="high")
    png_size = Path(out_png).stat().st_size
    print(f"  Saved {out_png}  ({png_size:,} bytes)")
    manifest_run = {
        "brand": args.brand,
        "asset_profile": args.asset_profile,
        "register": (register_profile or {}).get("inferred_register"),
        "mode": "render_and_scrub" if render_and_scrub else "reserve_headline_box",
        "is_reference_job": is_reference_job,
        "aligned_prompt": args.aligned_prompt or None,
        "chroma_contain": bool(chroma_key),
        "chroma_key_hex": chroma_key,
        "chroma_disabled_for_reference": is_reference_job,
        "generation": gen_meta,
    }
    manifest_run_path = out_dir / "run_manifest.json"
    manifest_run_path.write_text(json.dumps(manifest_run, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    if png_size < 100_000:
        print("  WARNING: PNG is suspiciously small (<100 KB)", file=sys.stderr)

    if args.asset_profile == "flat_graphic" and reserve_box_mode and tier3 is not None:
        for warning in check_reservation_legibility(out_png, tier3):
            print("  " + "=" * 64, file=sys.stderr)
            print(f"  LEGIBILITY WARNING: {warning}", file=sys.stderr)
            print("  " + "=" * 64, file=sys.stderr)

    # --- Step 5: composite the licensed font ---
    final_png = None
    needs_review, review_reason = False, None
    if args.asset_profile == "flat_graphic":
        lines = must_include or []
        weight_hint = (((register_profile or {}).get("font_resolved") or {})
                       .get("preferred_member") or "")
        if reserve_box_mode and spec_path:
            if args.no_closed_loop:
                print("\n=== Step 5: Composite (OPEN-LOOP, planned anchors) ===")
                from composite_text import composite as _composite
                final_png = _composite(out_png, str(spec_path), str(out_dir / "final.png"))
            else:
                print("\n=== Step 5: Closed-loop composite (reserve-box / free-space) ===")
                from closed_loop_composite import closed_loop
                hr = (tier3 or {}).get("headline_reservation") or {}
                reserved = ([hr["x_frac"], hr["y_frac"], hr["x_frac"] + hr["w_frac"],
                             hr["y_frac"] + hr["h_frac"]]
                            if all(k in hr for k in ("x_frac", "y_frac", "w_frac", "h_frac"))
                            else None)
                final_png = closed_loop(out_png, str(spec_path), str(out_dir / "final.png"),
                                        brand=args.brand, chroma_key_hex=chroma_key,
                                        reserved_zone_frac=reserved)
        elif render_and_scrub and lines:
            print("\n=== Step 5: Render-and-scrub composite (licensed font at MEASURED geometry) ===")
            from closed_loop_composite import place_measured
            rec = place_measured(out_png, lines, args.brand, "chinese_primary", weight_hint,
                                 str(out_dir / "final.png"), chroma_key_hex=chroma_key,
                                 is_reference_job=is_reference_job)
            if rec["status"] == "placed":
                final_png = Path(rec["final"])
            elif is_reference_job:
                # Path-specific honest-null (guardrail): reanchor is UNDEFINED on a full-bleed
                # ref. LEAVE gpt's rendered text in place; flag for human review. Never guess.
                import shutil
                final_png = out_dir / "final.png"
                shutil.copyfile(out_png, final_png)
                needs_review = True
                review_reason = ("reference job: OCR could not map one box per headline line; "
                                 "gpt's rendered text LEFT IN PLACE (not scrubbed/overlaid)")
                print(f"  [needs_review] {review_reason}", file=sys.stderr)
            else:
                # No-ref capture failure: free-space fallback is valid (the container has free
                # space; reanchor is defined). Seed a lines spec, let closed_loop re-anchor.
                print("  [note] capture ambiguous on a no-ref job — free-space closed-loop fallback",
                      file=sys.stderr)
                from closed_loop_composite import closed_loop
                fb_path = out_dir / "fallback_spec.json"
                fb_path.write_text(json.dumps(_lines_fallback_spec(lines, args.brand, weight_hint),
                                              ensure_ascii=False, indent=2), encoding="utf-8")
                final_png = closed_loop(out_png, str(fb_path), str(out_dir / "final.png"),
                                        brand=args.brand, chroma_key_hex=chroma_key)
        else:
            print("\n=== Step 5: no --must-include headline lines — leaving the generated image as-is ===")

    manifest_run["needs_review"] = needs_review
    manifest_run["needs_review_reason"] = review_reason
    if is_reference_job:
        manifest_run["cutout"] = "deferred (reference job, no chroma backdrop — final.png is the deliverable)"
    manifest_run_path.write_text(json.dumps(manifest_run, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    print(f"  Saved {manifest_run_path}  ({manifest_run_path.stat().st_size} bytes)")

    if final_png and Path(final_png).exists():
        print(f"  Saved {final_png}  ({Path(final_png).stat().st_size:,} bytes)")
        comp_path = Path(str(final_png) + ".compliance.json")
        if comp_path.exists():
            mani = json.loads(comp_path.read_text(encoding="utf-8"))
            non_licensed = [m for m in mani if not str(m["resolution"]).startswith("licensed")]
            print(f"  COMPLIANCE SUMMARY: {len(mani)} layer(s), "
                  f"{len(mani) - len(non_licensed)} licensed, {len(non_licensed)} NON-COMPLIANT")
            for m in non_licensed:
                print(f"    !! {m['content']!r}: {m['resolution']} -> {m['resolved_file']}")

    print("\n=== OUTPUTS ===")
    print(f"  final_prompt.txt : {prompt_path.stat().st_size:>8,} bytes")
    print(f"  generated.png    : {Path(out_png).stat().st_size:>8,} bytes")
    if tier3_path:
        print(f"  tier3_scene.json : {tier3_path.stat().st_size:>8,} bytes")
    if spec_path:
        print(f"  composite_spec.json : {spec_path.stat().st_size:>5,} bytes")
    if final_png and Path(final_png).exists():
        print(f"  final.png        : {Path(final_png).stat().st_size:>8,} bytes")
    if needs_review:
        print(f"  needs_review     : TRUE — {review_reason}")


if __name__ == "__main__":
    main()
