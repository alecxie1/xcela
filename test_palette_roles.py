#!/usr/bin/env python3
"""test_palette_roles.py - falsifiable self-test for role-aware brand palette (feature 008).

No paid calls. Asserts VALUES a wrong build cannot satisfy (constitution §III), never generates. Covers:
  1. ROLE_GUIDANCE defines exactly the 5 canonical roles, each with its verbatim instruction + a fallback.
  2. the thin prompt lists EACH color with its hex AND its role instruction (a primary-only build fails).
  3. a blank / unknown-role color still appears, via the fallback (honest-null, never dropped).
  4. the background instruction is present with a reference and absent (fallback) without one, color still
     listed both ways (the chroma guard).
  5. the header keeps the hard brand-color lock; the single-primary anchor is unchanged.
  6. the onboarding gate (onboard.html + intake.py) offers exactly the named ROLE_GUIDANCE roles, states
     the exactly-one-primary rule, and uses no em-dash (the gate stays in sync with the map).

Run:  .venv/bin/python test_palette_roles.py
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
import scene_author  # noqa: E402


def _key(items):
    return {"fields": {"brand_name_cn": {"value": "测试"}, "brand_name_en": {"value": "Test"},
                       "colors": {"items": items}}}


_FULL = [
    {"name_cn": "红", "name_en": "Red", "printed_html": "D81E05", "role": "primary"},
    {"name_cn": "灰", "name_en": "Grey", "printed_html": "888888", "role": "secondary"},
    {"name_cn": "金", "name_en": "Gold", "printed_html": "C8A24B", "role": "accent"},
    {"name_cn": "白", "name_en": "White", "printed_html": "FFFFFF", "role": "background"},
    {"name_cn": "黑", "name_en": "Black", "printed_html": "1A1A1A", "role": "text"},
]


def check1_role_map_coverage():
    g = scene_author.ROLE_GUIDANCE
    expected = {"primary", "secondary", "accent", "background", "text"}
    keys_ok = set(g) == expected
    subs = {"primary": "dominant", "secondary": "support the primary", "accent": "use sparingly",
            "background": "fill the background", "text": "legible"}
    subs_ok = all(subs[r] in g[r] for r in expected)
    fb_ok = bool(scene_author.ROLE_GUIDANCE_FALLBACK.strip())
    return keys_ok and subs_ok and fb_ok, f"keys={sorted(g)}; subs_ok={subs_ok}; fallback_nonempty={fb_ok}"


def check2_each_color_has_instruction():
    prompt = scene_author.assemble_thin_prompt(_key(_FULL), ["守住钱袋子"], has_reference=True)
    up = prompt.upper()
    checks = {
        "primary_hex": "D81E05" in up, "secondary_hex": "888888" in prompt,
        "accent_hex": "C8A24B" in up, "background_hex": "FFFFFF" in up, "text_hex": "1A1A1A" in up,
        "primary_instr": "dominant" in prompt, "secondary_instr": "support the primary" in prompt,
        "accent_instr": "use sparingly" in prompt, "text_instr": "legible" in prompt,
    }
    return all(checks.values()), str(checks)


def check3_blank_role_fallback():
    items = [{"name_cn": "红", "name_en": "Red", "printed_html": "D81E05", "role": "primary"},
             {"name_cn": "X", "name_en": "X", "printed_html": "123456", "role": ""},
             {"name_cn": "Y", "name_en": "Y", "printed_html": "654321", "role": "weird"}]
    prompt = scene_author.assemble_thin_prompt(_key(items), ["m"], has_reference=True)
    listed = "123456" in prompt and "654321" in prompt
    fb = scene_author.ROLE_GUIDANCE_FALLBACK in prompt
    return listed and fb, f"both_listed={listed}; fallback_present={fb}"


def check4_background_guard():
    items = [{"name_cn": "红", "name_en": "Red", "printed_html": "D81E05", "role": "primary"},
             {"name_cn": "白", "name_en": "White", "printed_html": "FFFFFF", "role": "background"}]
    with_ref = scene_author.assemble_thin_prompt(_key(items), ["m"], has_reference=True)
    no_ref = scene_author.assemble_thin_prompt(_key(items), ["m"], has_reference=False)
    bg = "fill the background"
    on = bg in with_ref
    off = bg not in no_ref
    listed = "FFFFFF" in with_ref.upper() and "FFFFFF" in no_ref.upper()
    fb_off = scene_author.ROLE_GUIDANCE_FALLBACK in no_ref
    return on and off and listed and fb_off, \
        f"bg_with_ref={on}; bg_absent_no_ref={off}; color_listed_both={listed}; fallback_when_off={fb_off}"


def check5_header_lock_and_anchor():
    key = _key(_FULL)
    prompt = scene_author.assemble_thin_prompt(key, ["m"], has_reference=True)
    header_ok = "must read as this brand's" in prompt
    anchor = scene_author._primary_color_hex(key)
    anchor_ok = anchor.upper() == "#D81E05"
    return header_ok and anchor_ok, f"header_hard_lock={header_ok}; anchor={anchor}"


def check6_gate_role_sync():
    expected = set(scene_author.ROLE_GUIDANCE)
    html = (REPO / "frontend" / "onboard.html").read_text(encoding="utf-8")
    m = re.search(r"<select data-role.*?</select>", html, re.S)
    html_roles = set(re.findall(r'value="([^"]+)"', m.group(0))) if m else set()
    intake = (REPO / "brand_intake" / "intake.py").read_text(encoding="utf-8")
    pm = re.search(r"role \[([^\]]+)\]", intake)
    cli_roles = {s.strip() for s in pm.group(1).split("/")} if pm else set()
    sync = html_roles == expected and cli_roles == expected
    instr = "只指定一个 primary" in html  # 017: the rule is stated in Chinese
    no_emdash = "—" not in html
    return sync and instr and no_emdash, \
        f"html_roles={sorted(html_roles)}; cli_roles={sorted(cli_roles)}; one_primary_instr={instr}; no_emdash={no_emdash}"


CHECKS = [
    ("ROLE_GUIDANCE covers the 5 roles + fallback (verbatim)", check1_role_map_coverage),
    ("each color carries its hex + role instruction in the prompt", check2_each_color_has_instruction),
    ("blank / unknown role still listed via fallback", check3_blank_role_fallback),
    ("background guard: present with ref, absent without ref", check4_background_guard),
    ("header keeps the hard brand-color lock; anchor unchanged", check5_header_lock_and_anchor),
    ("gate (web + CLI) offers exactly the named roles + states one-primary", check6_gate_role_sync),
]


def main():
    print("=" * 78)
    print("test_palette_roles.py - falsifiable self-test (008, no paid calls)")
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
