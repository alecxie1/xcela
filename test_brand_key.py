#!/usr/bin/env python3
"""test_brand_key.py — falsifiable self-test for the 005 lean-key path (US2 + US3).

No paid calls; model-free (rapidocr is NOT invoked — the OCR organ is proven elsewhere). Asserts:
  US2: the delta_e reconcile mechanism (needs_review fires deterministically) + read_brand_names
       surfaces text-layer candidates (not inferred).
  US3: validate_lean_key FAILS LOUD (missing primary / unreal logo_path); build_lean_key -> a
       NON-EMPTY thin prompt with the primary hex; the SC-005 TWO-PART invariant (lean-with-styles
       byte-identical to fat; styles-absent differs only in the font-directive line); the
       acknowledgment gate (unacknowledged flag blocks save; keep-flagged writes needs_review).

Run:  .venv/bin/python test_brand_key.py
"""

import copy
import difflib
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
for p in ("brand_intake", "tests_support", "harness", "register", str(REPO)):
    sys.path.insert(0, str(REPO / p) if not p.startswith("/") else p)

import extract_colors as ec          # noqa: E402  (proven organ; delta_e only here)
import extract                        # noqa: E402  (brand_intake/extract.py)
import assemble_key                   # noqa: E402
import validate_key                   # noqa: E402
import intake                         # noqa: E402  (pure gate helper)
from make_pdf import make_pdf         # noqa: E402
from scene_author import assemble_thin_prompt  # noqa: E402
from derive_register import derive_register    # noqa: E402

FAT = json.loads((REPO / "answer_keys" / "aia.json").read_text(encoding="utf-8"))
# PINNED register profile (per SC-005 / T008d): event_prop, flexes font:rounded.
SUBFIELDS = {"usage_context": "held for photos / posed with",
             "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
             "logo_treatment": "omit", "brand_strictness": "expressive departure"}
MSGS = ["守住钱袋子", "护好幸福家"]


def _prompt(key):
    rp = derive_register(SUBFIELDS, key)
    return assemble_thin_prompt(key, MSGS, register_profile=rp)


# ---- US2 ----

def check1_delta_e_reconcile():
    identity = ec.delta_e("#31B4E7", "#31B4E7") == 0.0
    garbled = ec.delta_e("#31B4E7", "#E13B74") > 8.0  # transposed digits -> far in Lab
    return (identity and garbled), f"delta_e identity=={ec.delta_e('#31B4E7','#31B4E7')}; garbled dE={ec.delta_e('#31B4E7','#E13B74'):.1f}>8"


def check2_read_brand_names_from_text_layer():
    pdf = make_pdf(["梅厚泡 MAHOUPAO\nBrand Guidelines 品牌手册"], Path(tempfile.mkdtemp()) / "name.pdf")
    res = extract.read_brand_names(pdf, [1])
    cn_ok = any("梅厚泡" in c for c in res["cn_candidates"])
    en_ok = any(c.upper() == "MAHOUPAO" for c in res["en_candidates"])
    return (cn_ok and en_ok), f"cn_candidates={res['cn_candidates']}; en_candidates={res['en_candidates']}"


# ---- US3: validation fail-loud ----

def _good_color_items():
    return [{"name_cn": "友邦红", "name_en": "AIA Red", "role": "primary", "hex": "#D31145", "rgb": [211, 17, 69]}]


def check3_validate_raises_no_primary():
    logo = Path(tempfile.mkdtemp()) / "logo.png"; logo.write_bytes(b"\x89PNG\r\n")
    items = [{**_good_color_items()[0], "role": "secondary"}]
    key = assemble_key.build_lean_key("友邦保险", "AIA", items, str(logo), "x.pdf", "me", "2026-06-26")
    try:
        validate_key.validate_lean_key(key)
    except Exception as exc:  # noqa: BLE001
        return ("primary" in str(exc).lower()), f"raised: {exc}"
    return False, "did NOT raise on a key with no primary color"


def check4_validate_raises_bad_logo():
    key = assemble_key.build_lean_key("友邦保险", "AIA", _good_color_items(),
                                      "/no/such/logo_xyz.png", "x.pdf", "me", "2026-06-26")
    try:
        validate_key.validate_lean_key(key)
    except Exception as exc:  # noqa: BLE001
        return ("logo" in str(exc).lower()), f"raised: {exc}"
    return False, "did NOT raise on a missing/unreal logo_path"


def check5_lean_key_nonempty_prompt_with_hex():
    logo = Path(tempfile.mkdtemp()) / "logo.png"; logo.write_bytes(b"\x89PNG\r\n")
    key = assemble_key.build_lean_key("友邦保险", "AIA", _good_color_items(), str(logo),
                                      "x.pdf", "me", "2026-06-26")
    validate_key.validate_lean_key(key)
    prompt = _prompt(key)
    passed = bool(prompt.strip()) and "#D31145" in prompt and "color  stays" not in prompt
    return passed, f"prompt non-empty={bool(prompt.strip())}; has #D31145={'#D31145' in prompt}; no blank color={'color  stays' not in prompt}"


# ---- US3: SC-005 two-part invariant ----

def check6_lean_with_styles_byte_identical():
    lean = assemble_key.lean_projection(FAT, keep_styles=True)
    passed = _prompt(FAT) == _prompt(lean)
    # control: changing a primary hex MUST change the prompt
    lean2 = copy.deepcopy(lean)
    for it in lean2["fields"]["colors"]["items"]:
        if it.get("role") == "primary":
            it["printed_html"] = "00FF00"
    control = _prompt(lean2) != _prompt(FAT)
    return (passed and control), f"lean(styles kept)==fat: {passed}; primary-hex-change differs (control): {control}"


def check7_styles_absent_differs_only_font_line():
    lean = assemble_key.lean_projection(FAT, keep_styles=False)
    diff = [l for l in difflib.ndiff(_prompt(FAT).splitlines(), _prompt(lean).splitlines())
            if l.startswith("- ") or l.startswith("+ ")]
    only_font = bool(diff) and all("font" in l.lower() for l in diff)
    return only_font, f"changed lines={len(diff)}; all on the font directive={only_font}: {diff}"


# ---- US3: acknowledgment gate (pure) ----

def check8_gate_blocks_unacknowledged():
    items = [{"role": "primary", "hex": "#D31145", "needs_review": True}]  # flagged, NOT acknowledged
    blocked = intake.unacknowledged_flags(items)
    return bool(blocked), f"unacknowledged flags block save: {bool(blocked)} ({blocked})"


def check9_keep_flagged_writes_needs_review():
    items = [{"role": "primary", "hex": "#D31145", "needs_review": True, "_ack": "keep-flagged"}]
    none_unack = not intake.unacknowledged_flags(items)
    saved = intake.finalize_items(items)
    kept = saved[0].get("needs_review") is True and "_ack" not in saved[0]
    return (none_unack and kept), f"all acknowledged={none_unack}; kept-flag persists in saved item={kept}"


def check10_validate_raises_multiple_primaries():
    # feature 008: exactly ONE primary. Two primaries -> fail loud (the prompt anchors on a single one).
    logo = Path(tempfile.mkdtemp()) / "logo.png"; logo.write_bytes(b"\x89PNG\r\n")
    items = [{"name_cn": "红", "name_en": "Red", "role": "primary", "hex": "#D31145"},
             {"name_cn": "蓝", "name_en": "Blue", "role": "primary", "hex": "#0033A0"}]
    key = assemble_key.build_lean_key("友邦保险", "AIA", items, str(logo), "x.pdf", "me", "2026-06-26")
    try:
        validate_key.validate_lean_key(key)
    except Exception as exc:  # noqa: BLE001
        return ("more than one primary" in str(exc).lower()), f"raised: {exc}"
    return False, "did NOT raise on a key with two primary colors"


CHECKS = [
    ("delta_e reconcile (identity 0; garbled > threshold)", check1_delta_e_reconcile),
    ("read_brand_names surfaces text-layer candidates", check2_read_brand_names_from_text_layer),
    ("validate FAILS LOUD: no primary color", check3_validate_raises_no_primary),
    ("validate FAILS LOUD: missing/unreal logo_path", check4_validate_raises_bad_logo),
    ("lean key -> non-empty prompt with primary hex", check5_lean_key_nonempty_prompt_with_hex),
    ("SC-005(a): lean(styles kept) byte-identical to fat + control", check6_lean_with_styles_byte_identical),
    ("SC-005(b): styles-absent differs ONLY in the font line", check7_styles_absent_differs_only_font_line),
    ("gate blocks an unacknowledged needs_review flag", check8_gate_blocks_unacknowledged),
    ("keep-flagged acknowledges + persists needs_review in the key", check9_keep_flagged_writes_needs_review),
    ("validate FAILS LOUD: more than one primary (008)", check10_validate_raises_multiple_primaries),
]


def main():
    print("=" * 78)
    print("test_brand_key.py — falsifiable self-test (US2+US3, no paid calls)")
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
