#!/usr/bin/env python3
"""test_compose_select.py — falsifiable self-test for harness/compose_select.py (feature 001, US1).

No paid calls. Asserts VALUES a wrong build cannot satisfy:
  - a money-meaning message resolves to the money_bag icon (meaning-driven, not a default);
  - a zero-cue message honest-nulls the icon + needs_review (the floor rejects score 0, A1);
  - a message tying two entries at the top score honest-nulls (ambiguous, A1);
  - two different-mode messages get DIFFERENT archetypes (US1 distinctness);
  - exhausting the layout vocabulary for a mode reuses + flags needs_review (D3).

Run:  .venv/bin/python test_compose_select.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import compose_select as cs  # noqa: E402
import kit as kitlib  # noqa: E402

KIT = kitlib.load_kit("aia")


def check1_meaning_drives_icon():
    comp = cs.compose_message(KIT, "s1", ["守住钱袋子", "护好幸福家"], [])
    passed = comp["chosen_icon"] == "money_bag" and comp["detected_mode"] == "protect" and not comp["needs_review"]
    return passed, f"chosen_icon={comp['chosen_icon']!r} mode={comp['detected_mode']!r} score={comp['icon_match_score']} needs_review={comp['needs_review']}"


def check2_zero_cue_honest_null():
    comp = cs.compose_message(KIT, "s1", ["abcdef无关词条"], [])
    passed = comp["chosen_icon"] is None and comp["needs_review"] and "no icon match" in (comp["needs_review_reason"] or "")
    return passed, f"chosen_icon={comp['chosen_icon']!r} score={comp['icon_match_score']} reason={comp['needs_review_reason']!r}"


def check3_ambiguous_tie_honest_null():
    # A message that hits exactly one cue of money_bag AND one cue of family_shield (both protect,
    # score 1 each) -> ambiguous tie -> honest null.
    comp = cs.compose_message(KIT, "s1", ["钱袋", "护好"], [])
    passed = comp["chosen_icon"] is None and comp["needs_review"] and "ambiguous" in (comp["needs_review_reason"] or "")
    return passed, f"chosen_icon={comp['chosen_icon']!r} score={comp['icon_match_score']} reason={comp['needs_review_reason']!r}"


def check4_distinct_archetypes_for_distinct_modes():
    comps = cs.compose_campaign(KIT, [
        {"id": "s1", "messages": ["守住钱袋子", "护好幸福家"]},   # protect
        {"id": "s2", "messages": ["远离非法金融", "抵制高息诱惑"]},  # resist
    ])
    a1, a2 = comps[0]["chosen_archetype"], comps[1]["chosen_archetype"]
    passed = bool(a1 and a2 and a1 != a2 and comps[0]["text_zone"] and comps[1]["text_zone"])
    return passed, f"s1 icon={comps[0]['chosen_icon']} arch={a1}; s2 icon={comps[1]['chosen_icon']} arch={a2}; distinct={a1 != a2}"


def check5_exhaustion_reuses_and_flags():
    # protect mode is served by exactly one archetype (protect_solid). Two protect signs ->
    # the second must reuse and flag needs_review.
    comps = cs.compose_campaign(KIT, [
        {"id": "s1", "messages": ["守住钱袋子"]},   # protect -> protect_solid
        {"id": "s2", "messages": ["护好幸福家", "家庭平安"]},  # protect -> only protect_solid left
    ])
    second = comps[1]
    passed = (second["chosen_archetype"] == comps[0]["chosen_archetype"]
              and second["archetype_reused"] is True and second["needs_review"] is True)
    return passed, (f"s1 arch={comps[0]['chosen_archetype']}; s2 arch={second['chosen_archetype']} "
                    f"reused={second['archetype_reused']} needs_review={second['needs_review']}")


CHECKS = [
    ("Meaning drives the icon (money_bag)", check1_meaning_drives_icon),
    ("Zero-cue message honest-nulls (A1 floor)", check2_zero_cue_honest_null),
    ("Ambiguous tie honest-nulls (A1)", check3_ambiguous_tie_honest_null),
    ("Distinct modes -> distinct archetypes (US1)", check4_distinct_archetypes_for_distinct_modes),
    ("Vocabulary exhaustion reuses + flags (D3)", check5_exhaustion_reuses_and_flags),
]


def main():
    print("=" * 78)
    print("test_compose_select.py — falsifiable self-test (US1, no paid calls)")
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
