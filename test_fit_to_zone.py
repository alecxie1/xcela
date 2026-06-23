#!/usr/bin/env python3
"""test_fit_to_zone.py — falsifiable self-test for the fit-to-zone clamp (feature 001, US2).

No paid calls. Uses the licensed kit font resolved the same way the real pipeline resolves it.
Asserts VALUES a wrong build cannot satisfy (fixes failure (a)):
  - a LONGER headline gets a strictly SMALLER final_size_px than a short one in the same zone;
  - the fitted block fits inside the zone with margin on every edge (it does not overflow);
  - a headline that cannot fit even at min_size_px honest-nulls (fits=False, size=None),
    never a clipped/overflowing render (constitution §V).

Run:  .venv/bin/python test_fit_to_zone.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import composite_text as ct  # noqa: E402

FONT_PATH, _man = ct.resolve_font({"font_role": "chinese_primary", "brand": "aia",
                                   "weight_hint": "汉仪元隆黑 75"})

ZONE_W, ZONE_H = 900.0, 360.0   # a generous reserved text zone in px
MARGIN = 24
MIN_SIZE = 48


def check1_longer_text_shrinks():
    short = ct.fit_text_to_zone(["守"], ZONE_W, ZONE_H, FONT_PATH, margin_px=MARGIN, min_size_px=MIN_SIZE)
    long = ct.fit_text_to_zone(["守住钱袋子护好幸福家", "平安健康长长久久每一天"],
                               ZONE_W, ZONE_H, FONT_PATH, margin_px=MARGIN, min_size_px=MIN_SIZE)
    passed = (short["fits"] and long["fits"]
              and long["final_size_px"] < short["final_size_px"])
    return passed, (f"short size={short['final_size_px']}; long size={long['final_size_px']}; "
                    f"long<short={long['final_size_px'] < short['final_size_px']}")


def check2_fitted_block_within_zone():
    res = ct.fit_text_to_zone(["守住钱袋子", "护好幸福家"], ZONE_W, ZONE_H, FONT_PATH,
                              margin_px=MARGIN, min_size_px=MIN_SIZE)
    w, h = res["rendered_wh_px"]
    avail_w, avail_h = ZONE_W - 2 * MARGIN, ZONE_H - 2 * MARGIN
    passed = res["fits"] and w <= avail_w and h <= avail_h
    return passed, (f"fitted box={w:.0f}x{h:.0f}px <= avail {avail_w:.0f}x{avail_h:.0f}px "
                    f"(size={res['final_size_px']})")


def check3_impossible_text_honest_null():
    # 12 chars on one line in a tiny zone at a 48px floor cannot fit -> honest null.
    res = ct.fit_text_to_zone(["守住钱袋子护好幸福家平安"], 120.0, 70.0, FONT_PATH,
                              margin_px=12, min_size_px=MIN_SIZE)
    passed = (res["fits"] is False and res["final_size_px"] is None)
    return passed, f"fits={res['fits']} final_size_px={res['final_size_px']} (must be False/None, never clipped)"


def check4_frac_wrapper_box_inside_zone():
    zone = {"x_frac": 0.12, "y_frac": 0.52, "w_frac": 0.76, "h_frac": 0.34}  # protect_solid text_zone
    res = ct.fit_text_in_zone_frac(["守住钱袋子", "护好幸福家"], zone, (1536, 1024), FONT_PATH,
                                   margin_px=MARGIN, min_size_px=MIN_SIZE)
    box = res.get("rendered_box_frac")
    inside = (box and box["x_frac"] >= zone["x_frac"] and box["y_frac"] >= zone["y_frac"]
              and (box["x_frac"] + box["w_frac"]) <= (zone["x_frac"] + zone["w_frac"])
              and (box["y_frac"] + box["h_frac"]) <= (zone["y_frac"] + zone["h_frac"]))
    passed = bool(res["fits"] and inside)
    return passed, f"fits={res['fits']} rendered_box_frac={box} inside_zone={bool(inside)}"


CHECKS = [
    ("Longer headline -> strictly smaller size (fit-to-zone)", check1_longer_text_shrinks),
    ("Fitted block within the zone with margin (no overflow)", check2_fitted_block_within_zone),
    ("Unfittable headline honest-nulls (never clips, §V)", check3_impossible_text_honest_null),
    ("Frac wrapper: rendered box inside the reserved zone", check4_frac_wrapper_box_inside_zone),
]


def main():
    print("=" * 78)
    print("test_fit_to_zone.py — falsifiable self-test (US2, no paid calls)")
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
