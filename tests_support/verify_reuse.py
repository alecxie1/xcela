#!/usr/bin/env python3
"""tests_support/verify_reuse.py — STEP ZERO: confirm the reuse surface 005 stands on (no paid calls).

The whole front-half adapts to organs it does NOT own. If any of them drifts (a renamed function, a
0-indexed render_page, a moved read surface), this one-shot check FAILS LOUD here, not deep in a later
task. Model-free: it imports + exercises the deterministic surface only.

Run:  .venv/bin/python tests_support/verify_reuse.py
"""

import inspect
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "tests_support"))


def main():
    checks = []

    # 1. extract_colors: 1-INDEXED render_page (the footgun), delta_e, extract_colors run on the fixture
    import extract_colors as ec
    src = inspect.getsource(ec.render_page)
    one_indexed = "page_no_1idx - 1" in src or "- 1]" in src
    checks.append(("extract_colors.render_page is 1-indexed", one_indexed,
                   f"source has the -1 deref: {one_indexed}"))
    checks.append(("extract_colors.delta_e(h,h) == 0", ec.delta_e("#31B4E7", "#31B4E7") == 0.0,
                   f"delta_e identity = {ec.delta_e('#31B4E7', '#31B4E7')}"))
    from make_pdf import make_default
    pdf = make_default(Path(tempfile.mkdtemp()) / "fix.pdf")
    recs = ec.extract_colors(pdf, [2])  # the hex page (1-indexed) of the fixture
    got_hex = any(r["value"]["hex"].lower() == "#31b4e7" for r in recs)
    checks.append(("extract_colors.extract_colors runs + finds #31B4E7 on the fixture", got_hex,
                   f"records={[r['value']['hex'] for r in recs]}"))

    # 2. extract_text_layer: page_text + text_layer_ratio import + run
    import extract_text_layer as et
    txt = et.page_text(pdf, [2]).get(2, "")
    checks.append(("extract_text_layer.page_text returns the page text", "#31B4E7".lower() in txt.lower(),
                   f"p2 text len={len(txt)}"))
    checks.append(("extract_text_layer.text_layer_ratio runs", 0.0 <= et.text_layer_ratio(pdf) <= 1.0,
                   f"ratio={et.text_layer_ratio(pdf)}"))

    # 3. the back-half read surface the lean key feeds (import only; no model)
    from scene_author import assemble_thin_prompt  # noqa: F401
    sys.path.insert(0, str(REPO / "register"))
    from derive_register import derive_register  # noqa: F401
    checks.append(("scene_author.assemble_thin_prompt + register.derive_register import", True,
                   "both importable (the lean key's read surface)"))

    print("=" * 78)
    print("verify_reuse.py — STEP ZERO reuse-surface check (no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, ok, detail) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\nCHECK {i}/{len(checks)} — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(checks)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()
