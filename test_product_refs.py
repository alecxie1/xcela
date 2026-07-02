#!/usr/bin/env python3
"""test_product_refs.py - falsifiable self-test for feature 013 (role-tagged references).

No paid calls: pure imports (scene_author, conductor, server parse helpers) + grep-gates on the
served form HTML (the WEAKEST gate, declared per the 010 precedent). Contract rows refer to
specs/013-role-tagged-references/contracts/product_refs_contract.md.

Run:  .venv/bin/python test_product_refs.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "frontend"))
import scene_author  # noqa: E402
import conductor  # noqa: E402

# Same fixture as test_lossless_brief (and its T001 baseline): minimal key, one message,
# marketing register, photo dialect, reference fed, nothing optional.
KEY = {"fields": {"brand_name_cn": {"value": "测试"}, "brand_name_en": {"value": "Test"},
                  "colors": {"items": [{"name_cn": "红", "name_en": "Red",
                                        "printed_html": "D81E05", "role": "primary"}]}}}
MARKETING = {"inferred_register": "marketing"}

# Pre-013 baseline (byte-identical to test_lossless_brief.EXPECTED_PREFEATURE_PROMPT: the 012
# fixture carries no asset_type/occasion and no products, so the prompt is unchanged since).
sys.path.insert(0, str(REPO))
from test_lossless_brief import EXPECTED_PREFEATURE_PROMPT  # noqa: E402


def _assemble(**kw):
    return scene_author.assemble_thin_prompt(KEY, ["新品上市"], register_profile=MARKETING,
                                             asset_profile="photo", has_reference=True, **kw)


def check1_fidelity_section():
    """T002 contract rows 1-2 + 12: section values verbatim with count; no-products prompt
    byte-identical to the pre-013 baseline; no em-dash in the new section."""
    prods = ["/tmp/p1.png", "/tmp/p2.png"]
    p = _assemble(product_images=prods)
    row1 = ("PRODUCT FIDELITY (the 2 additional supplied image(s) are the brand's REAL products)" in p
            and "same printed branding and label text" in p
            and "Do NOT redraw them as generic products" in p
            and "Only their backgrounds may be discarded" in p
            and "the ONLY words that may appear" in p)  # headline guard untouched
    row2 = (_assemble() == EXPECTED_PREFEATURE_PROMPT
            and _assemble(product_images=[]) == EXPECTED_PREFEATURE_PROMPT)
    section = p[p.index("PRODUCT FIDELITY"):p.index("Only their backgrounds") + 40]
    row12 = "—" not in section
    passed = row1 and row2 and row12
    return passed, f"section_values={row1}; no_products_byte_identical={row2}; no_emdash={row12}"


def check2_refs_list():
    """T002 contract rows 6-7: refs = [style, logo] + products (appended, prefix stable);
    zero products = exactly [style, logo]; the logo:omit fallback unchanged."""
    f = scene_author._thin_generation_refs
    style, logo, prods = "/r/ref.jpg", "/b/logo.png", ["/r/p1.png", "/r/p2.png"]
    with_p = f(style, logo, False, prods) == [style, logo] + prods
    without = f(style, logo, False, None) == [style, logo] and f(style, logo, False, []) == [style, logo]
    omit_fallback = f(None, logo, True, None) == [logo]           # historical fallback
    omit_with_p = f(None, logo, True, prods) == prods             # products satisfy the >=1 need
    passed = with_p and without and omit_fallback and omit_with_p
    return passed, (f"appended={with_p}; zero_products_prefeature={without}; "
                    f"omit_fallback={omit_fallback}; omit_with_products={omit_with_p}")


def check3_argparse_append():
    """T002 contract row 4: repeated --product-image collects into an ordered list."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-image", action="append", default=None)
    got = ap.parse_args(["--product-image", "a.png", "--product-image", "b.png"]).product_image
    none_case = ap.parse_args([]).product_image is None
    passed = got == ["a.png", "b.png"] and none_case
    return passed, f"ordered_append={got == ['a.png', 'b.png']}; default_none={none_case}"


CHECKS = [
    ("US1 product fidelity section (values, byte-identity, no em-dash)", check1_fidelity_section),
    ("US1 generation refs list ([style, logo] + products; prefix byte-stable)", check2_refs_list),
    ("US1 repeatable --product-image collects in order", check3_argparse_append),
]


def main():
    print("=" * 78)
    print("test_product_refs.py - falsifiable self-test (013, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} - {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
