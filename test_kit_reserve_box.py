#!/usr/bin/env python3
"""test_kit_reserve_box.py — falsifiable self-test for scene_author kit mode (feature 001, US3).

No paid image generation. Asserts VALUES a wrong build cannot satisfy (fixes failures b + a):
  - --explain reports kit reserve-box mode: headline NOT rendered in the image, composite is
    'kit_reserve_box', and the icon_zone / text_zone are DISJOINT (text never lands on the icon);
  - the kit composite places the licensed headline INSIDE the reserved text_zone and emits a
    compliance manifest with every layer LICENSED (FR-006 / SC-005, the non-negotiable);
  - an unfittable headline honest-nulls (status 'unfit', no final.png), never a clipped render.

The compliance check composites onto a LOCAL fixture PNG (no gpt-image-2 call).

Run:  .venv/bin/python test_kit_reserve_box.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import kit as kitlib  # noqa: E402
import compose_select as cs  # noqa: E402
import scene_author as sa  # noqa: E402

KIT = kitlib.load_kit("aia")
ANSWER_KEY = json.loads((REPO_ROOT / "answer_keys" / "aia.json").read_text(encoding="utf-8"))
REGISTER_PROFILE = {
    "inferred_register": "event_prop", "font_role_hint": "rounded display",
    "brand_anchors_held": ["primary_color"], "brand_locks_flexed": ["logo:omit", "shape:die-cut"],
    "shape_language_hint": "die-cut organic, thick white stroke",
    "font_resolved": {"family": "汉仪元隆黑", "preferred_member": "汉仪元隆黑-75简",
                      "file": "brands/aia/fonts/HYYuanLongHei75W.ttf"},
}
KIT_PROFILE = kitlib.derive_kit_profile(KIT, ANSWER_KEY, REGISTER_PROFILE)


def check1_explain_reports_kit_reserve_box():
    comp = cs.compose_message(KIT, "s1", ["守住钱袋子", "护好幸福家"], [])
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "kit_profile.json").write_text(json.dumps(KIT_PROFILE, ensure_ascii=False), encoding="utf-8")
        (d / "composition.json").write_text(json.dumps(comp, ensure_ascii=False), encoding="utf-8")
        argv = [sys.executable, str(REPO_ROOT / "harness" / "scene_author.py"), "--brand", "aia",
                "--asset-profile", "flat_graphic", "--kit-profile", str(d / "kit_profile.json"),
                "--composition", str(d / "composition.json"), "--out", str(d / "out"), "--explain"]
        proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            return False, f"explain failed rc={proc.returncode}\n{proc.stderr}"
        info = json.loads(proc.stdout)
    passed = (info["mode"] == "kit_reserve_box" and info["headline_rendered_in_image"] is False
              and info["composite"] == "kit_reserve_box" and info["icon_text_zones_disjoint"] is True)
    return passed, (f"mode={info['mode']} headline_in_image={info['headline_rendered_in_image']} "
                    f"composite={info['composite']} disjoint={info['icon_text_zones_disjoint']}")


def check2_composite_in_zone_and_licensed():
    from PIL import Image
    comp = cs.compose_message(KIT, "s1", ["守住钱袋子", "护好幸福家"], [])
    tz = comp["text_zone"]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        gen = d / "generated.png"
        Image.new("RGB", sa.CANVAS, (200, 30, 60)).save(gen)  # fixture panel, no gpt call
        rec = sa.compose_kit_headline(KIT, KIT_PROFILE, comp, "aia", str(gen), str(d / "final.png"))
        if rec["status"] != "placed":
            return False, f"composite status={rec['status']} (expected placed)"
        # all headline anchors inside the reserved text zone
        inside = all(tz["x_frac"] <= s["anchor_frac"][0] <= tz["x_frac"] + tz["w_frac"]
                     and tz["y_frac"] <= s["anchor_frac"][1] <= tz["y_frac"] + tz["h_frac"]
                     for s in rec["spec"])
        comp_manifest = json.loads((d / "final.png.compliance.json").read_text(encoding="utf-8"))
        all_licensed = bool(comp_manifest) and all(
            str(m["resolution"]).startswith("licensed") for m in comp_manifest)
        final_exists = (d / "final.png").exists()
    passed = inside and all_licensed and final_exists
    return passed, (f"headline anchors inside text_zone={inside}; layers={len(comp_manifest)} "
                    f"all licensed={all_licensed}; final.png exists={final_exists}")


def check3_unfit_headline_honest_null():
    from PIL import Image
    # A long headline forced into a tiny text_zone cannot fit at the floor -> honest null.
    comp = {"sign_id": "s1", "message": ["守住钱袋子护好幸福家平安健康"],
            "chosen_icon": "money_bag", "chosen_archetype": "protect_solid",
            "text_zone": {"x_frac": 0.40, "y_frac": 0.45, "w_frac": 0.12, "h_frac": 0.06}}
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        gen = d / "generated.png"
        Image.new("RGB", sa.CANVAS, (200, 30, 60)).save(gen)
        rec = sa.compose_kit_headline(KIT, KIT_PROFILE, comp, "aia", str(gen), str(d / "final.png"))
        passed = rec["status"] == "unfit" and rec["final"] is None and not (d / "final.png").exists()
    return passed, f"status={rec['status']} final={rec['final']} (must be unfit/None, never clipped)"


CHECKS = [
    ("--explain reports kit reserve-box (disjoint zones, no scrub)", check1_explain_reports_kit_reserve_box),
    ("Headline composited inside zone + all licensed (SC-005)", check2_composite_in_zone_and_licensed),
    ("Unfittable headline honest-nulls (never clips)", check3_unfit_headline_honest_null),
]


def main():
    print("=" * 78)
    print("test_kit_reserve_box.py — falsifiable self-test (US3, no paid image generation)")
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
