#!/usr/bin/env python3
"""test_format_size.py — falsifiable self-test for the size resolver (feature 002, US2).

No paid calls. Asserts the gpt-image-2 size INVARIANTS for every brief size (edges multiples of 16,
max edge <= 3840, pixels in [655_360, 8_294_400], aspect preserved) AND the default-target landings
(3:2 -> 1536x1024, 2:3 -> 1024x1536, 1:1 -> ~1248x1248, 3:1 -> ~2160x720), the symmetric >3:1 / <1:3
clamps with needs_review, portrait+square landing (profile-agnostic, D8), and the honest-null default
on unparseable input. A wrong build (3-fixed-canvas snap, no clamp, or a non-16 edge) fails.

Run:  .venv/bin/python test_format_size.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import format_size as fs  # noqa: E402

MIN_PX, MAX_PX, MAX_EDGE = 655_360, 8_294_400, 3840


def _invariants(r):
    w, h = r["width"], r["height"]
    return (w % 16 == 0 and h % 16 == 0 and 16 <= max(w, h) <= MAX_EDGE
            and MIN_PX <= w * h <= MAX_PX)


def check1_landscape_3_2():
    r = fs.resolve_size("60x40cm")
    passed = _invariants(r) and r["width"] == 1536 and r["height"] == 1024 and r["orientation"] == "landscape"
    return passed, f"60x40cm -> {r['width']}x{r['height']} ({r['orientation']}); invariants={_invariants(r)}"


def check2_portrait_2_3():
    r = fs.resolve_size("40x60cm")
    passed = _invariants(r) and r["width"] == 1024 and r["height"] == 1536 and r["orientation"] == "portrait"
    return passed, f"40x60cm -> {r['width']}x{r['height']} ({r['orientation']})"


def check3_square_1_1():
    r = fs.resolve_size("50x50cm")
    passed = (_invariants(r) and r["orientation"] == "square" and r["width"] == r["height"]
              and abs(r["width"] - 1248) <= 16)
    return passed, f"50x50cm -> {r['width']}x{r['height']} ({r['orientation']}); ~1248={abs(r['width']-1248)<=16}"


def check4_banner_3_1():
    r = fs.resolve_size("300x100cm")
    passed = (_invariants(r) and r["orientation"] == "landscape"
              and abs(r["aspect_resolved"] - 3.0) < 0.05 and not r["needs_review"])
    return passed, f"300x100cm (3:1) -> {r['width']}x{r['height']} aspect={r['aspect_resolved']:.2f} nr={r['needs_review']}"


def check5_clamp_beyond_3_1_symmetric():
    wide = fs.resolve_size("400x100cm")   # 4:1 -> clamp to 3:1
    tall = fs.resolve_size("100x400cm")   # 1:4 -> clamp to 1:3
    wide_ok = (_invariants(wide) and wide["needs_review"] and abs(wide["aspect_resolved"] - 3.0) < 0.1
               and wide["orientation"] == "landscape")
    tall_ok = (_invariants(tall) and tall["needs_review"] and abs(tall["aspect_resolved"] - (1 / 3)) < 0.02
               and tall["orientation"] == "portrait")
    passed = wide_ok and tall_ok
    return passed, (f"4:1 -> {wide['width']}x{wide['height']} nr={wide['needs_review']} ({wide_ok}); "
                    f"1:4 -> {tall['width']}x{tall['height']} nr={tall['needs_review']} ({tall_ok})")


def check6_unparseable_honest_null():
    r = fs.resolve_size("garbage")
    passed = _invariants(r) and r["note"] is not None and not r["needs_review"]
    return passed, f"garbage -> {r['width']}x{r['height']} note={r['note']!r} (default + honest null)"


def check7_target_area_recorded_and_in_budget():
    r = fs.resolve_size("60x40cm")
    passed = r.get("target_area") == 1_572_864 and MIN_PX <= r["pixels"] <= MAX_PX
    return passed, f"target_area={r.get('target_area')} pixels={r['pixels']}"


CHECKS = [
    ("3:2 lands on 1536x1024 (consequence of default target)", check1_landscape_3_2),
    ("2:3 lands portrait 1024x1536 (not landscape-only, D8)", check2_portrait_2_3),
    ("1:1 lands square ~1248x1248 (D8)", check3_square_1_1),
    ("3:1 lands ~2160x720, aspect preserved", check4_banner_3_1),
    ("Beyond 3:1 / below 1:3 clamps symmetrically + needs_review", check5_clamp_beyond_3_1_symmetric),
    ("Unparseable -> default size + honest-null note", check6_unparseable_honest_null),
    ("Target area recorded; pixels in budget", check7_target_area_recorded_and_in_budget),
]


def main():
    print("=" * 78)
    print("test_format_size.py — falsifiable self-test (US2, no paid calls)")
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
