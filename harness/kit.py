#!/usr/bin/env python3
"""harness/kit.py — Kit of Parts loader/validator + derived kit_profile.

Feature 001-kit-of-parts-composition. Two jobs, both stdlib-only (no numpy/anthropic/
openai), so the stdlib-only conductor can import this without API keys:

  1. load_kit(brand)  — load + VALIDATE kits/<brand>.json against the authored-kit schema
     (specs/.../contracts/kit-schema.md). A kit that breaks any rule raises KitError naming
     the specific rule; there is no silent partial kit (constitution §III/§V).

  2. derive_kit_profile(kit, answer_key, register_profile, calibration) — merge the brand
     answer key (HARD locks: palette, fonts) with the register_profile / reference calibration
     (SOFT dims: frame, register). The ANSWER KEY WINS every conflict (clarified 2026-06-22);
     every clash is recorded in conflict_resolutions so the run is auditable.

CLI (used by the conductor at execute time, after derive_register has produced a profile):
  .venv/bin/python harness/kit.py --brand aia \
      --answer-key answer_keys/aia.json \
      --register-profile <run>/register_profile.json \
      [--calibration <run>/calibration.json] \
      --out <run>/kit_profile.json
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class KitError(ValueError):
    """A kit that violates the authored-kit schema. Carries the specific rule violated."""


# --------------------------------------------------------------------------- #
# Load + validate (the authored layer)
# --------------------------------------------------------------------------- #

def kit_path(brand: str) -> Path:
    return REPO_ROOT / "kits" / f"{brand}.json"


def kit_exists(brand: str) -> bool:
    return kit_path(brand).exists()


def _zone_ok(z) -> bool:
    if not isinstance(z, dict):
        return False
    try:
        x, y = float(z["x_frac"]), float(z["y_frac"])
        w, h = float(z["w_frac"]), float(z["h_frac"])
    except (KeyError, TypeError, ValueError):
        return False
    return w > 0 and h > 0 and 0.0 <= x and 0.0 <= y and (x + w) <= 1.0 and (y + h) <= 1.0


def _zones_overlap(a: dict, b: dict) -> bool:
    ax0, ay0 = a["x_frac"], a["y_frac"]
    ax1, ay1 = ax0 + a["w_frac"], ay0 + a["h_frac"]
    bx0, by0 = b["x_frac"], b["y_frac"]
    bx1, by1 = bx0 + b["w_frac"], by0 + b["h_frac"]
    return (ax0 < bx1 and bx0 < ax1) and (ay0 < by1 and by0 < ay1)


def validate_kit(kit: dict, brand: str) -> dict:
    """Enforce every rule in contracts/kit-schema.md. Raise KitError on the first violation,
    naming the rule. Returns the kit unchanged on success."""
    if not isinstance(kit, dict):
        raise KitError("rule: kit must be a JSON object")

    # Rule 1: brand matches.
    if kit.get("brand") != brand:
        raise KitError(f"rule 1: kit brand {kit.get('brand')!r} != requested brand {brand!r}")

    # Rule 2: modes non-empty; every referenced mode is declared.
    modes = kit.get("modes")
    if not isinstance(modes, list) or not modes:
        raise KitError("rule 2: 'modes' must be a non-empty list")
    mode_set = set(modes)

    icons = kit.get("icon_vocabulary")
    if not isinstance(icons, list) or not icons:
        raise KitError("rule 3: 'icon_vocabulary' must be a non-empty list")

    # Rule 3: unique icon ids, non-empty meaning_cues, declared mode.
    seen_icon_ids = set()
    cue_sets = []
    for e in icons:
        eid = e.get("id")
        if not eid or eid in seen_icon_ids:
            raise KitError(f"rule 3: icon id missing or duplicated: {eid!r}")
        seen_icon_ids.add(eid)
        cues = e.get("meaning_cues")
        if not isinstance(cues, list) or not cues:
            raise KitError(f"rule 3: icon {eid!r} has empty meaning_cues")
        if e.get("mode") not in mode_set:
            raise KitError(f"rule 2: icon {eid!r} mode {e.get('mode')!r} not in declared modes {sorted(mode_set)}")
        cue_sets.append((eid, frozenset(cues)))

    # Rule 4: no two icon entries share an identical meaning_cues set.
    for i in range(len(cue_sets)):
        for j in range(i + 1, len(cue_sets)):
            if cue_sets[i][1] == cue_sets[j][1]:
                raise KitError(f"rule 4: icons {cue_sets[i][0]!r} and {cue_sets[j][0]!r} "
                               "share an identical meaning_cues set (ambiguous)")

    # Rule 5: >= 2 archetypes, unique ids.
    archs = kit.get("layout_vocabulary")
    if not isinstance(archs, list) or len(archs) < 2:
        raise KitError("rule 5: 'layout_vocabulary' must have at least 2 archetypes")
    seen_arch_ids = set()
    served_modes = set()
    for a in archs:
        aid = a.get("id")
        if not aid or aid in seen_arch_ids:
            raise KitError(f"rule 5: archetype id missing or duplicated: {aid!r}")
        seen_arch_ids.add(aid)
        a_modes = a.get("modes")
        if not isinstance(a_modes, list) or not a_modes:
            raise KitError(f"rule 2: archetype {aid!r} has empty modes")
        for m in a_modes:
            if m not in mode_set:
                raise KitError(f"rule 2: archetype {aid!r} mode {m!r} not in declared modes {sorted(mode_set)}")
            served_modes.add(m)
        # Rule 6: zones in-bounds and non-overlapping.
        iz, tz = a.get("icon_zone"), a.get("text_zone")
        if not _zone_ok(iz):
            raise KitError(f"rule 6: archetype {aid!r} icon_zone out of [0,1] or malformed")
        if not _zone_ok(tz):
            raise KitError(f"rule 6: archetype {aid!r} text_zone out of [0,1] or malformed")
        if _zones_overlap(iz, tz):
            raise KitError(f"rule 6: archetype {aid!r} icon_zone and text_zone OVERLAP "
                           "(zones must be disjoint so text never lands on the icon)")

    # Rule 7: every declared mode is served by >= 1 archetype.
    unserved = mode_set - served_modes
    if unserved:
        raise KitError(f"rule 7: modes with no layout archetype: {sorted(unserved)}")

    return kit


def load_kit(brand: str) -> dict:
    """Load + validate kits/<brand>.json. Raises KitError (with the rule) or FileNotFoundError."""
    path = kit_path(brand)
    if not path.exists():
        raise FileNotFoundError(f"no kit for brand {brand!r} (expected {path})")
    kit = json.loads(path.read_text(encoding="utf-8"))
    return validate_kit(kit, brand)


# --------------------------------------------------------------------------- #
# Derive the runtime kit_profile (the derived layer; answer key wins conflicts)
# --------------------------------------------------------------------------- #

def _hex(s):
    if not s:
        return None
    s = str(s).strip()
    return s if s.startswith("#") else f"#{s}"


def _rgb(h):
    h = (h or "").lstrip("#")
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def _rgb_dist(a, b):
    if not a or not b:
        return None
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _answer_key_colors(answer_key: dict) -> list:
    fields = answer_key.get("fields") or answer_key
    items = ((fields.get("colors") or {}).get("items")) or []
    out = []
    for it in items:
        out.append({"role": it.get("role"), "hex": _hex(it.get("printed_html")), "source": "answer_key"})
    return out


def _reference_dominant_hexes(register_profile: dict, calibration: dict | None) -> list:
    """Pull reference dominant colors (if any) from calibration.style_evidence or the
    register_profile's merged reference_style_evidence. Items may be strings or {hex:...}."""
    ev = {}
    if calibration:
        ev = calibration.get("style_evidence") or {}
    if not ev:
        ev = register_profile.get("reference_style_evidence") or {}
    raw = ev.get("dominant_colors") or ev.get("colors") or []
    hexes = []
    for c in raw:
        if isinstance(c, str):
            hexes.append(_hex(c))
        elif isinstance(c, dict):
            hexes.append(_hex(c.get("hex")))
    return [h for h in hexes if h]


def derive_kit_profile(kit: dict, answer_key: dict, register_profile: dict,
                       calibration: dict | None = None) -> dict:
    """Merge answer key (HARD) + register_profile/calibration (SOFT) into kit_profile.
    Answer key wins every conflict; clashes recorded in conflict_resolutions."""
    notes: list[str] = []
    conflicts: list[str] = []

    palette = _answer_key_colors(answer_key)
    primary = next((c for c in palette if c["role"] == "primary"), None)

    # Conflict detection: a reference dominant color diverging from the brand primary.
    ref_hexes = _reference_dominant_hexes(register_profile, calibration)
    if primary and ref_hexes:
        p_rgb = _rgb(primary["hex"])
        # nearest reference dominant to the brand primary
        nearest = min(ref_hexes, key=lambda h: (_rgb_dist(_rgb(h), p_rgb) or 1e9))
        d = _rgb_dist(_rgb(nearest), p_rgb)
        if d is not None and d > 20.0:
            conflicts.append(f"palette.primary: reference dominant {nearest} diverged from "
                             f"answer-key {primary['hex']} (dist {d:.0f}) -> answer key wins")
    if not ref_hexes:
        notes.append("no reference dominant colors available; palette is answer-key only (honest null)")

    typo = answer_key.get("typography") or (answer_key.get("fields") or {}).get("typography") or {}
    font_role = register_profile.get("font_role_hint")
    style_entry = (typo.get("styles") or {}).get(font_role) or {}
    font_resolved = register_profile.get("font_resolved") or {}

    return {
        "brand": kit.get("brand"),
        "register": register_profile.get("inferred_register"),
        "palette": palette,
        "font_role": font_role,
        "font_family": style_entry.get("family") or font_resolved.get("family"),
        "font_index_key": style_entry.get("index_weight_key"),
        "font_file": font_resolved.get("file"),
        "frame_treatment": register_profile.get("shape_language_hint"),
        "anchors_held": register_profile.get("brand_anchors_held") or [],
        "locks_flexed": register_profile.get("brand_locks_flexed") or [],
        "accent_vocabulary": kit.get("accent_vocabulary") or [],
        "conflict_resolutions": conflicts,
        "notes": notes,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a kit + derive kit_profile.json (answer key wins).")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--answer-key", required=True)
    ap.add_argument("--register-profile", required=True)
    ap.add_argument("--calibration", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        kit = load_kit(args.brand)
    except (KitError, FileNotFoundError) as exc:
        sys.exit(f"ERROR: {exc}")

    answer_key = json.loads(Path(args.answer_key).read_text(encoding="utf-8"))
    register_profile = json.loads(Path(args.register_profile).read_text(encoding="utf-8"))
    calibration = (json.loads(Path(args.calibration).read_text(encoding="utf-8"))
                   if args.calibration and Path(args.calibration).exists() else None)

    profile = derive_kit_profile(kit, answer_key, register_profile, calibration=calibration)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"\nSaved {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
