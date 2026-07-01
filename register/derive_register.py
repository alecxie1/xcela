#!/usr/bin/env python3
"""register/derive_register.py — deterministic subfields -> register_profile engine.

The judgment layer of REGISTER_ENGINE_SPEC Part 1: the human supplies cheap FACTS
(guided subfields, brief_schema_v3 buckets B+D); THIS code makes the designer's
LEAP (facts -> register) with a small inspectable rule table — no LLM, every
decision appended to _derivation_trace so the leap is falsifiable.

Usage:
  .venv/bin/python register/derive_register.py \
      --subfields intents/aia_sign1_eventprop_subfields.json \
      --brand aia --out output/eventprop_sign1
"""

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# usage_context keywords -> base register (first matching row wins; checked in order).
USAGE_RULES = [
    (("held for photos", "posed with", "photo", "worn / carried"), "event_prop"),
    (("wall-posted", "read at distance", "outdoor display", "table-placed"), "marketing"),
    (("handed out", "direct mail"), "formal_leaning"),  # resolved by vibe below
    (("scrolled on phone",), "marketing"),
]

# register -> design-language hints (the leap's payload).
REGISTER_HINTS = {
    "event_prop": {
        "font_role_hint": "rounded display",
        "shape_language_hint": "die-cut organic (speech bubble / burst / cloud), thick white stroke outline",
        "icon_style_hint": "cartoon/emoji-style, mascots, exaggerated",
        "tone_hint": "playful, energetic, grabbable photo-prop",
    },
    "marketing": {
        "font_role_hint": "sharp display",
        "shape_language_hint": "clean card or full-bleed, generous margins",
        "icon_style_hint": "flat geometric, restrained",
        "tone_hint": "polished, on-brand, persuasive",
    },
    "formal": {
        "font_role_hint": "sharp display",
        "shape_language_hint": "rectangular, classic margins, no die-cuts",
        "icon_style_hint": "minimal or none",
        "tone_hint": "official, restrained, authoritative",
    },
}


def _render_is_photo(value) -> bool:
    """Feature 011: does the brief's raw render_style mean a PHOTOGRAPHIC render?
    Mirrors harness/conductor.normalize_render_style (subprocess boundary, no import
    path between the packages; drift-guarded by test_register_render_aware.py):
    'photographic'/'photo' (case/whitespace-insensitive) -> True; everything else,
    including absent/blank/unrecognized, -> False (the flat historical default)."""
    return str(value or "").strip().lower() in ("photographic", "photo")


# Moderated slider defaults per register, used when NO calibration exists (CALIBRATOR_SPEC
# Part 2): the old behavior copied the raw subfield vibe (2/8) into the profile, which was
# hand-anchored on contaminated post-hoc images and OVERSHOT. Subfield vibe still sets
# DIRECTION (which register); these set the no-reference MAGNITUDE.
REGISTER_SLIDER_DEFAULTS = {
    "event_prop": {"formality": 5, "playfulness": 7},
}


def derive_register(subfields: dict, brand_key: dict, calibration: dict | None = None) -> dict:
    """Pure function: subfields dict + brand answer_key (+ optional reference calibration)
    -> register_profile (with trace). Subfields set DIRECTION (which register, logo or not,
    strictness); a calibration's register_target sets MAGNITUDE (the slider coordinates)."""
    trace: list[str] = []
    vibe = subfields.get("vibe") or {}
    formality = vibe.get("formality")
    playfulness = vibe.get("playfulness")
    usage = str(subfields.get("usage_context") or "").lower()

    # --- 1. base register from usage_context (rule table) ---
    base = None
    for keywords, reg in USAGE_RULES:
        hit = next((k for k in keywords if k in usage), None)
        if hit:
            base = reg
            trace.append(f"usage_context={subfields.get('usage_context')!r} matched {hit!r} => {reg} base")
            break
    if base is None:
        base = "marketing"
        trace.append(f"usage_context={subfields.get('usage_context')!r} matched no rule => marketing base (default)")

    # --- 2. vibe resolves/confirms the tier ---
    if base == "formal_leaning":
        base = "formal" if (formality is not None and formality >= 7) else "marketing"
        trace.append(f"handed-out + formality={formality} => {base}")
    if base == "event_prop":
        if formality is not None and playfulness is not None and (formality >= 7 or playfulness <= 3):
            base = "marketing"
            trace.append(f"vibe contradicts event_prop (formality={formality}, playfulness={playfulness}) "
                         "=> demoted to marketing")
        else:
            trace.append(f"vibe confirms event_prop (formality={formality} low, playfulness={playfulness} high)")
    elif base == "marketing" and formality is not None and playfulness is not None:
        if formality <= 3 and playfulness >= 7:
            # Feature 011: the promotion was written in the flat-vector era, when a playful
            # vibe reliably meant a grabbable prop. A PHOTOGRAPHIC render is a different
            # deliverable (a marketing photo, not a die-cut prop), so the vibe alone must
            # not promote; an explicit event-prop usage phrase (rule table above) still wins
            # because it never reaches this branch. Flat/absent/unrecognized: unchanged.
            render_style = subfields.get("render_style")
            if _render_is_photo(render_style):
                trace.append(f"vibe would promote to event_prop (formality={formality}<=3, "
                             f"playfulness={playfulness}>=7) but render_style={render_style!r} "
                             "is photographic, a marketing photo rather than a flat prop "
                             "=> promotion SUPPRESSED, register stays marketing")
            else:
                base = "event_prop"
                trace.append(f"vibe overrides (formality={formality}<=3, playfulness={playfulness}>=7) => event_prop")
        elif formality >= 8:
            base = "formal"
            trace.append(f"formality={formality}>=8 => formal")
    register = base

    # --- 2b. slider MAGNITUDE: calibration > moderated register default > subfield vibe ---
    # (subfield vibe above already set DIRECTION; raw extremes must not become the target)
    target = (calibration or {}).get("register_target") or {}
    if calibration and "formality" in target and "playfulness" in target:
        out_formality, out_playfulness = target["formality"], target["playfulness"]
        slider_source = "calibration"
        trace.append(f"MAGNITUDE from calibration register_target: formality={out_formality}, "
                     f"playfulness={out_playfulness} (subfield vibe {formality}/{playfulness} "
                     "kept as DIRECTION only)")
    elif register in REGISTER_SLIDER_DEFAULTS:
        d = REGISTER_SLIDER_DEFAULTS[register]
        out_formality, out_playfulness = d["formality"], d["playfulness"]
        slider_source = "moderated_default"
        trace.append(f"MAGNITUDE: no calibration => moderated {register} defaults "
                     f"formality={out_formality}, playfulness={out_playfulness} "
                     f"(raw subfield vibe {formality}/{playfulness} NOT copied — overshoot fix)")
    else:
        out_formality, out_playfulness = formality, playfulness
        slider_source = "subfields"
        trace.append(f"MAGNITUDE from subfield vibe: formality={out_formality}, "
                     f"playfulness={out_playfulness} (no calibration, no register default)")

    # --- 3. brand anchors: ALWAYS hold primary color (client kept AIA red even in playful refs) ---
    anchors = ["primary_color"]
    strictness = subfields.get("brand_strictness")
    reference_diff = subfields.get("reference_diff")  # only a ref-diff may release the anchor
    # a calibration IS a reference diff: its cross-check verdict on primary_color governs
    cal_color_flexed = any("primary_color" in s for s in (calibration or {}).get("locks_flexed", []))
    cal_color_held = next((s for s in (calibration or {}).get("anchors_held", [])
                           if "primary_color" in s), None)
    if strictness == "expressive departure" and (
            (reference_diff and reference_diff.get("primary_color_flexed")) or cal_color_flexed):
        anchors = []
        trace.append("brand_strictness=expressive AND reference diff releases primary_color => no color anchor")
    elif cal_color_held:
        trace.append(f"primary_color HELD with calibration evidence: {cal_color_held}")
    else:
        trace.append(f"primary_color HELD (brand_strictness={strictness!r}, "
                     f"reference_diff={'present' if reference_diff else 'absent'} — anchor stands)")

    # --- 4. flexed locks from logo_treatment + register ---
    flexed: list[str] = []
    if subfields.get("logo_treatment") == "omit":
        flexed.append("logo:omit")
        trace.append("logo_treatment=omit => logo lock flexed (logo:omit)")
        if calibration is not None:
            if calibration.get("logo_present_in_ref"):
                trace.append("CONFLICT: subfields say logo omit but reference SHOWS a logo — "
                             "subfields (direction) win; flag for human review")
            else:
                trace.append("subfields say logo omit + ref shows no logo => consistent")
    elif subfields.get("logo_treatment") == "subtle":
        flexed.append("logo:subtle")
        trace.append("logo_treatment=subtle => logo lock relaxed (logo:subtle)")
    if register == "event_prop":
        flexed += ["font:rounded", "shape:die-cut", "palette:playful-accents"]
        trace.append("register=event_prop => flex font:rounded + shape:die-cut + palette:playful-accents")

    hints = dict(REGISTER_HINTS[register])
    # Feature 011 tone retention: a playful brand's MARKETING job keeps the playful TONE
    # (rounded font, playful accents) but never the PROP FORMAT (no shape:die-cut flex, the
    # shape_language_hint stays the marketing default). Keyed on the VIBE, not the render
    # choice, so it applies wherever marketing meets the promoting vibe (constitution VI:
    # tone follows the brand vibe, format follows the task, decided independently).
    if (register == "marketing" and formality is not None and playfulness is not None
            and formality <= 3 and playfulness >= 7):
        flexed += ["font:rounded", "palette:playful-accents"]
        hints["font_role_hint"] = "rounded display"
        hints["tone_hint"] = ("playful, energetic, candy-bright, yet a polished on-brand "
                              "marketing piece (a rectangular poster, not a photo-prop)")
        trace.append(f"register=marketing with playful vibe (formality={formality}<=3, "
                     f"playfulness={playfulness}>=7) => TONE retained: flex font:rounded + "
                     "palette:playful-accents, font_role_hint='rounded display', playful "
                     "tone_hint; FORMAT stays marketing (no shape:die-cut, "
                     "shape_language_hint unchanged)")
    trace.append(f"register={register} => font_role_hint={hints['font_role_hint']!r}")

    # --- 4b. merge calibration style_evidence into the hints (CONCRETE reference evidence) ---
    evidence = (calibration or {}).get("style_evidence") or {}
    if evidence:
        ev_map = [
            ("shape_language_hint", evidence.get("shape_language")),
            ("icon_style_hint", evidence.get("icon_style")),
        ]
        if evidence.get("text_effects"):
            ev_map.append(("shape_language_hint", f"text effects: {evidence['text_effects']}"))
        for hint_key, ev in ev_map:
            if ev:
                hints[hint_key] = f"{hints[hint_key]} | REFERENCE EVIDENCE: {ev}"
                trace.append(f"calibration style_evidence merged into {hint_key}: {ev!r}")

    profile = {
        "inferred_register": register,
        "formality": out_formality,
        "playfulness": out_playfulness,
        "_slider_source": slider_source,
        "brand_anchors_held": anchors,
        "brand_locks_flexed": flexed,
        **hints,
        "_derivation_trace": trace,
    }
    if evidence:
        profile["reference_style_evidence"] = evidence

    # --- 5. resolve font_role_hint -> licensed family via the answer key styles map ---
    typo = brand_key.get("typography") or brand_key.get("fields", {}).get("typography") or {}
    style_entry = (typo.get("styles") or {}).get(hints["font_role_hint"])
    if style_entry:
        resolved = {
            "style": style_entry.get("style"),
            "family": style_entry.get("family"),
            "preferred_member": style_entry.get("preferred_member"),
        }
        idx_rel = (typo.get("chinese_primary") or {}).get("library_index")
        idx_path = _REPO_ROOT / idx_rel if idx_rel else None
        if idx_path and idx_path.exists():
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            member = (index.get(style_entry["family"]) or {}).get(style_entry.get("index_weight_key", ""))
            if member:
                resolved["file"] = member["file"]
                trace.append(f"styles[{hints['font_role_hint']!r}] -> {style_entry['family']} "
                             f"{style_entry.get('index_weight_key')} -> {member['file']} (licensed)")
            else:
                trace.append(f"styles[{hints['font_role_hint']!r}] -> {style_entry['family']} "
                             f"but index has no weight {style_entry.get('index_weight_key')!r} — family-level resolve only")
        profile["font_resolved"] = resolved
    else:
        trace.append(f"answer key typography has no styles[{hints['font_role_hint']!r}] entry — "
                     "font resolution left to composite-time role lookup")
    return profile


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive a register_profile from brief subfields.")
    ap.add_argument("--subfields", required=True, help="JSON file: guided-subfields dict (buckets B+D)")
    ap.add_argument("--brand", required=True, help="brand key name under answer_keys/")
    ap.add_argument("--out", required=True, help="output directory for register_profile.json")
    ap.add_argument("--calibration", default="",
                    help="optional calibration.json (register/calibrate_from_reference.py output): "
                    "its register_target sets slider MAGNITUDE; subfields still set DIRECTION")
    args = ap.parse_args()

    subfields = json.loads(Path(args.subfields).read_text(encoding="utf-8"))
    brand_key = json.loads((_REPO_ROOT / "answer_keys" / f"{args.brand}.json").read_text(encoding="utf-8"))
    calibration = (json.loads(Path(args.calibration).read_text(encoding="utf-8"))
                   if args.calibration else None)

    profile = derive_register(subfields, brand_key, calibration=calibration)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "register_profile.json"
    out_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== DERIVATION TRACE ===")
    for i, step in enumerate(profile["_derivation_trace"], 1):
        print(f"  {i}. {step}")
    print("\n=== REGISTER PROFILE ===")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"\nSaved {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
