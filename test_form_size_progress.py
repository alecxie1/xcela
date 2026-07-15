#!/usr/bin/env python3
"""test_form_size_progress.py - falsifiable self-test for feature 022 (form size units +
wait expectations). NO paid calls.

The compose and the wait rendering live in browser JS (vanilla-HTML surface), so the
automated half is VALUE-BEARING grep pins (the repo convention for this surface, declared
in the plan): the exact compose expression with the exact default values, the exact
refusal, the WAIT_EXPECT constants. The real composed inputs.json on disk is observed at
the T005 human gate (SC-002's stated proof split).

Run:  .venv/bin/python test_form_size_progress.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

def _index() -> str:
    return (REPO / "frontend" / "index.html").read_text(encoding="utf-8")


def check1_size_controls():
    """022 US1/FR-001: the three controls exist with TODAY'S defaults (60 / 40 / cm as
    the selected-by-position first option) and offer exactly the cm + px units; the old
    single free-text field is GONE (a build that keeps both would double-report)."""
    ix = _index()
    a = ('id="size_w" type="number" min="0" step="any" value="60"' in ix
         and 'id="size_h" type="number" min="0" step="any" value="40"' in ix)
    b = ('<select id="size_unit"><option value="cm">' in ix
         and '<option value="px">' in ix and ix.count('id="size_unit"') == 1)
    c = 'id="format_size"' not in ix
    ok = a and b and c
    return ok, f"w/h-defaults={a}; unit-select-cm-first+px={b}; old-field-gone={c}"


def check2_compose_pin():
    """022 FR-002 (SC-002's automated half): formState composes format_size from EXACTLY
    the three controls with the exact expression - untouched defaults (60, 40, cm) can
    only compose the pre-022 literal "60x40cm". A build that reorders, pads, or renames
    the parts fails this by value."""
    ix = _index()
    a = ('format_size: $("size_w").value + "x" + $("size_h").value + $("size_unit").value'
         in ix)
    b = 'value="60"' in ix and 'value="40"' in ix and '<option value="cm">' in ix
    ok = a and b
    return ok, f"compose-expression-exact={a}; default-parts-60/40/cm={b}"


def check3_loud_refusal_and_draft_note():
    """022 FR-004 + FR-005: blank/zero/NaN W or H refuses loudly BEFORE any POST (the
    guard sits in startRun ahead of the form build), and the aspect-only draft
    expectation is stated next to the fields (Chinese, the exact wording pinned)."""
    ix = _index()
    guard = 'if (!(sizeW > 0) || !(sizeH > 0)) { $("formNote").textContent = "请填写有效的宽和高（都要大于 0）。"; return; }'
    a = guard in ix and ix.index(guard) < ix.index('fd.append("form"')
    b = "按此比例生成草稿图（约 150 万像素），不是精确像素稿或印刷分辨率文件" in ix
    ok = a and b
    return ok, f"refusal-before-launch={a}; draft-note={b}"


CHECKS = [
    ("022 US1: W/H/unit controls, defaults, old field gone", check1_size_controls),
    ("022 US1: the compose expression pin (byte-identity by construction)", check2_compose_pin),
    ("022 US1: loud size refusal + the aspect-only draft note", check3_loud_refusal_and_draft_note),
]


def main():
    print("=" * 78)
    print("test_form_size_progress.py - falsifiable self-test (022, no paid calls)")
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
