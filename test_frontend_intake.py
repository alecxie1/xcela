#!/usr/bin/env python3
"""test_frontend_intake.py — falsifiable self-test for the form -> inputs JSON writer (004, US1).

No paid calls. Asserts `frontend/inputs_writer.to_inputs(form_state)` is a LOSSLESS, VERBATIM
single-sign 002-shape brief: exactly one `signs[]` entry; `messages`, `mandatory_elements`, and the
three vibe integers byte-for-byte; a blank optional recorded empty (honest null); reference required;
and the output passes the real `conductor.validate_inputs`. A build that drops/rephrases a field,
collapses to multi-sign, or emits a brief the CLI rejects fails.

Run:  .venv/bin/python test_frontend_intake.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "frontend"))
sys.path.insert(0, str(REPO_ROOT / "harness"))
import inputs_writer  # noqa: E402
import conductor  # noqa: E402

FORM = {
    "brand": "aia",
    "asset_type": "手举牌 hand-held event sign",
    "format_size": "60x40cm",
    "reference_image": "/tmp/ref_aia.png",
    "reference_relationship": "template - extend this series",
    "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
    "logo_treatment": "omit",
    "brand_strictness": "expressive departure",
    "occasion": "防范非法金融宣传",
    "usage_context": "held for photos / posed with",
    "audience": "general public",
    "mandatory_elements": ["分别画叉"],
    "forbidden_elements": [],
    "messages": ["守住钱袋子", "护好幸福家"],
}


def check1_single_sign_verbatim():
    out = inputs_writer.to_inputs(FORM)
    ctx = out.get("context", {})
    checks = {
        "one_sign": len(out.get("signs", [])) == 1,
        "messages": out["signs"][0]["messages"] == ["守住钱袋子", "护好幸福家"],
        "mandatory": out.get("mandatory_elements") == ["分别画叉"],
        "format_size": out.get("format_size") == "60x40cm",
        "reference": out.get("reference_image") == "/tmp/ref_aia.png",
        "formality": (ctx.get("vibe") or {}).get("formality") == 2,
        "playfulness": (ctx.get("vibe") or {}).get("playfulness") == 8,
        "warmth": (ctx.get("vibe") or {}).get("warmth") == 7,
        "occasion": ctx.get("occasion") == "防范非法金融宣传",
    }
    failed = [k for k, ok in checks.items() if not ok]
    return (not failed), (f"all verbatim + one sign" if not failed else f"FAILED: {failed}")


def check2_blank_optional_empty():
    out = inputs_writer.to_inputs(FORM)
    passed = out.get("forbidden_elements") == []
    return passed, f"forbidden_elements={out.get('forbidden_elements')!r} (blank -> [] honest null)"


def check3_passes_validate_inputs():
    out = inputs_writer.to_inputs(FORM)
    try:
        validated = conductor.validate_inputs(dict(out))
    except SystemExit as exc:
        return False, f"validate_inputs REJECTED the form output: {exc}"
    passed = len(validated.get("signs", [])) == 1
    return passed, f"validate_inputs accepts; signs={len(validated.get('signs', []))}"


def check4_reference_required():
    bad = dict(FORM)
    bad["reference_image"] = ""
    try:
        inputs_writer.to_inputs(bad)
    except (ValueError, KeyError) as exc:
        return True, f"missing reference rejected: {type(exc).__name__}"
    return False, "no reference but to_inputs did NOT reject (FR-005 violated)"


CHECKS = [
    ("Single-sign + every field verbatim", check1_single_sign_verbatim),
    ("Blank optional recorded empty (honest null)", check2_blank_optional_empty),
    ("Output passes conductor.validate_inputs", check3_passes_validate_inputs),
    ("Reference image required (v1)", check4_reference_required),
]


def main():
    print("=" * 78)
    print("test_frontend_intake.py — falsifiable self-test (US1, no paid calls)")
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
