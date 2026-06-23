#!/usr/bin/env python3
"""test_kit.py — falsifiable self-test for harness/kit.py (feature 001).

No paid calls. Asserts VALUES a wrong build cannot satisfy:
  - a valid kits/aia.json loads and every declared mode is served by an archetype;
  - each schema violation (dup id, identical cue sets, overlapping zones, unserved mode)
    RAISES KitError naming the rule (a no-op validator would let them pass);
  - on a seeded reference-vs-answer-key palette clash, the derived kit_profile carries the
    ANSWER-KEY hex and records the clash in conflict_resolutions (answer key wins, D6).

Run:  .venv/bin/python test_kit.py
"""

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import kit  # noqa: E402  (stdlib-only)

ANSWER_KEY = json.loads((REPO_ROOT / "answer_keys" / "aia.json").read_text(encoding="utf-8"))
AIA_PRIMARY = "#D31145"  # answer_keys/aia.json colors.primary printed_html


def _expect_raise(mutate, rule_substr):
    """Apply mutate() to a copy of the valid aia kit; expect KitError mentioning rule_substr."""
    bad = copy.deepcopy(VALID_KIT)
    mutate(bad)
    try:
        kit.validate_kit(bad, "aia")
    except kit.KitError as exc:
        return (rule_substr in str(exc)), f"raised: {exc}"
    return False, "NO KitError raised (wrong/no-op validator)"


VALID_KIT = json.loads((REPO_ROOT / "kits" / "aia.json").read_text(encoding="utf-8"))


def check1_valid_kit_loads():
    k = kit.load_kit("aia")
    modes = set(k["modes"])
    served = set()
    for a in k["layout_vocabulary"]:
        served |= set(a["modes"])
    passed = bool(modes) and modes <= served and len(k["icon_vocabulary"]) >= 1
    return passed, f"modes={sorted(modes)} all served by archetypes={modes <= served}; icons={len(k['icon_vocabulary'])}"


def check2_duplicate_icon_id_rejected():
    def mut(k):
        k["icon_vocabulary"][1]["id"] = k["icon_vocabulary"][0]["id"]
    return _expect_raise(mut, "rule 3")


def check3_identical_cuesets_rejected():
    def mut(k):
        k["icon_vocabulary"][1]["meaning_cues"] = list(k["icon_vocabulary"][0]["meaning_cues"])
    return _expect_raise(mut, "rule 4")


def check4_overlapping_zones_rejected():
    def mut(k):
        # make the first archetype's text_zone sit on top of its icon_zone
        k["layout_vocabulary"][0]["text_zone"] = dict(k["layout_vocabulary"][0]["icon_zone"])
    return _expect_raise(mut, "rule 6")


def check5_unserved_mode_rejected():
    def mut(k):
        k["modes"].append("celebrate")  # declared but no archetype serves it
        k["icon_vocabulary"][0]["mode"] = "celebrate"  # keep icon-mode rule satisfied
    return _expect_raise(mut, "rule 7")


def check6_answer_key_wins_palette_conflict():
    # Seed a calibration whose reference dominant color diverges sharply from AIA red.
    register_profile = {
        "inferred_register": "event_prop",
        "font_role_hint": "rounded display",
        "brand_anchors_held": ["primary_color"],
        "brand_locks_flexed": ["logo:omit", "shape:die-cut"],
        "shape_language_hint": "die-cut organic, thick white stroke",
    }
    calibration = {"style_evidence": {"dominant_colors": ["#1133EE", "#22CC55"]}}  # nothing near AIA red
    profile = kit.derive_kit_profile(VALID_KIT, ANSWER_KEY, register_profile, calibration=calibration)
    primary = next((c for c in profile["palette"] if c["role"] == "primary"), None)
    held_answer_key = primary and primary["hex"].upper() == AIA_PRIMARY
    recorded = any("answer key wins" in c for c in profile["conflict_resolutions"])
    passed = bool(held_answer_key) and recorded
    return passed, (f"kit_profile primary={primary and primary['hex']} (==answer-key {AIA_PRIMARY}? {held_answer_key}); "
                    f"conflict_resolutions={profile['conflict_resolutions']}")


CHECKS = [
    ("Valid kit loads; every mode served by an archetype", check1_valid_kit_loads),
    ("Duplicate icon id rejected (rule 3)", check2_duplicate_icon_id_rejected),
    ("Identical meaning_cues sets rejected (rule 4)", check3_identical_cuesets_rejected),
    ("Overlapping icon/text zones rejected (rule 6)", check4_overlapping_zones_rejected),
    ("Unserved declared mode rejected (rule 7)", check5_unserved_mode_rejected),
    ("Answer key wins a palette conflict (D6)", check6_answer_key_wins_palette_conflict),
]


def main():
    print("=" * 78)
    print("test_kit.py — falsifiable self-test for harness/kit.py (no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
