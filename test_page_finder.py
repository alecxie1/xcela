#!/usr/bin/env python3
"""test_page_finder.py — falsifiable self-test for brand_intake/page_finder (feature 005, US1).

No paid calls. Over the synthetic fixture PDF (tests_support/make_pdf): page 1 mentions "color" with
NO hex, page 2 prints "#31B4E7", page 3 is a typography page. Asserts the heuristic SUGGESTS the
hex-token page (1-indexed) for color and explicitly does NOT suggest the color-mention-only page;
finds the font page; returns 1-indexed page numbers; reports text_layer_ratio. A wrong build (color
detection by mention not hex, a 0-indexed return, or a model dependency) fails.

Run:  .venv/bin/python test_page_finder.py
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "brand_intake"))
sys.path.insert(0, str(REPO / "tests_support"))
import page_finder  # noqa: E402
from make_pdf import make_default  # noqa: E402

PDF = make_default(Path(tempfile.mkdtemp()) / "fixture.pdf")
SUGG = page_finder.suggest_pages(PDF)


def check1_hex_page_suggested_not_mention():
    color = SUGG["color"]
    passed = 2 in color and 1 not in color
    return passed, f"color={color}; hex page 2 present={2 in color}; mention-only page 1 ABSENT={1 not in color}"


def check2_font_page_found():
    passed = 3 in SUGG["fonts"]
    return passed, f"fonts={SUGG['fonts']} (font page 3 present={3 in SUGG['fonts']})"


def check3_one_indexed():
    # every suggested page is a 1-indexed page number in [1, page_count]; none is 0.
    all_pages = SUGG["color"] + SUGG["fonts"] + SUGG["brand_name"]
    passed = bool(all_pages) and all(isinstance(p, int) and p >= 1 for p in all_pages)
    return passed, f"all suggested pages 1-indexed (>=1, no 0)={passed}; pages={sorted(set(all_pages))}"


def check4_text_layer_ratio_reported():
    r = SUGG.get("text_layer_ratio")
    passed = isinstance(r, (int, float)) and 0.0 <= r <= 1.0
    return passed, f"text_layer_ratio={r}"


def check5_brand_name_page():
    # the brand-name page is the early/title page(s); page 1 is a reasonable suggestion.
    passed = bool(SUGG["brand_name"]) and 1 in SUGG["brand_name"]
    return passed, f"brand_name={SUGG['brand_name']}"


CHECKS = [
    ("Color = hex-token page (2), NOT mention-only page (1)", check1_hex_page_suggested_not_mention),
    ("Font page (3) found", check2_font_page_found),
    ("All suggested pages are 1-indexed (the footgun)", check3_one_indexed),
    ("text_layer_ratio reported", check4_text_layer_ratio_reported),
    ("Brand-name page suggested (early page)", check5_brand_name_page),
]


def main():
    print("=" * 78)
    print("test_page_finder.py — falsifiable self-test (US1, no paid calls)")
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
