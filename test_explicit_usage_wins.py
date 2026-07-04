#!/usr/bin/env python3
"""test_explicit_usage_wins.py - falsifiable self-test for feature 014.

No paid calls: pure derive_register imports. The vibe marketing->event_prop promotion must not
override an EXPLICIT marketing-keyword usage match (the human statement beats the machine guess,
the same principle as the 011 photo gate, applied to the flat lane where run_CJXQ_20260701_173925
exposed the leak). Contract rows refer to
specs/014-explicit-usage-wins/contracts/explicit_usage_contract.md.

Run:  .venv/bin/python test_explicit_usage_wins.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "register"))
sys.path.insert(0, str(REPO))
import derive_register as dr  # noqa: E402
from test_register_render_aware import EXPECTED_PREFEATURE_PROFILE, _subfields  # noqa: E402


def _suppressed(profile):
    return [t for t in profile["_derivation_trace"] if "SUPPRESSED" in t]


def check1_explicit_marketing_wins():
    """T002 contract row 1: flat/absent/unrecognized render + promoting vibe + EACH marketing
    keyword => marketing, ONE suppression line naming that keyword, tone retained, no die-cut,
    no em-dash in the new line. An unfixed build returns event_prop and fails every keyword."""
    failures = []
    for kw in dr.MARKETING_USAGE_KEYWORDS:
        for render in (None, "flat vector", "watercolor"):
            p = dr.derive_register(_subfields(render, usage=f"a {kw} piece for the launch"), {})
            sup = _suppressed(p)
            ok = (p["inferred_register"] == "marketing"
                  and len(sup) == 1 and f"'{kw}'" in sup[0] and "—" not in sup[0]
                  and "font:rounded" in p["brand_locks_flexed"]
                  and "palette:playful-accents" in p["brand_locks_flexed"]
                  and "shape:die-cut" not in p["brand_locks_flexed"]
                  and p["font_role_hint"] == "rounded display")
            if not ok:
                failures.append((kw, render, p["inferred_register"], sup))
    passed = not failures
    return passed, f"all 4 keywords x 3 non-photo renders suppressed+toned: {passed} (failures={failures[:2]})"


def check2_double_gate_single_entry():
    """T002 contract row 5 (FR-006): photographic + marketing keyword => marketing with EXACTLY
    one SUPPRESSED line, and it names the RENDER (photo gate first, 011 trace byte-unchanged)."""
    p = dr.derive_register(_subfields("photographic", usage="instagram feed"), {})
    sup = _suppressed(p)
    passed = (p["inferred_register"] == "marketing" and len(sup) == 1
              and "'photographic'" in sup[0] and "instagram" not in sup[0])
    return passed, f"register=marketing:{p['inferred_register'] == 'marketing'}; one_line={len(sup) == 1}; names_render={bool(sup) and 'photographic' in sup[0]}"


def check3_legacy_untouched():
    """T003 contract rows 2-3: the wall-posted + promoting-vibe profile is byte-identical to
    the pre-feature literal on BOTH the absent AND explicit flat lanes (the flat lane writes no
    render trace line, so the profiles are identical; over-suppression or new flat tracing
    fails); an unmatched free-text usage still promotes via the default (zero suppression)."""
    absent = json.dumps(dr.derive_register(_subfields(), {}), ensure_ascii=False, sort_keys=True)
    flat = json.dumps(dr.derive_register(_subfields("flat vector"), {}),
                      ensure_ascii=False, sort_keys=True)
    row2 = absent == EXPECTED_PREFEATURE_PROFILE and flat == EXPECTED_PREFEATURE_PROFILE
    p = dr.derive_register(_subfields(usage="random gibberish nobody typed"), {})
    row3 = (p["inferred_register"] == "event_prop"
            and any("matched no rule" in t for t in p["_derivation_trace"])
            and any("vibe overrides" in t for t in p["_derivation_trace"])
            and not _suppressed(p))
    passed = row2 and row3
    return passed, f"wall_posted_byte_identical_both_lanes={row2}; default_still_promotes={row3}"


def check4_event_precedence():
    """T004 contract rows 4 + 6: 'instagram photo' (event keyword + marketing keyword in one
    phrase) resolves event_prop via the event row on BOTH lanes with ZERO suppression entries;
    photographic + wall-posted keeps the 011 photo suppression line byte-unchanged."""
    parts = []
    for render in ("photographic", None):
        p = dr.derive_register(_subfields(render, usage="instagram photo"), {})
        parts.append(p["inferred_register"] == "event_prop"
                     and any("matched 'photo'" in t and "event_prop base" in t
                             for t in p["_derivation_trace"])
                     and not _suppressed(p))
    row4 = all(parts)
    p6 = dr.derive_register(_subfields("photographic"), {})  # wall-posted default usage
    sup6 = _suppressed(p6)
    row6 = (p6["inferred_register"] == "marketing" and len(sup6) == 1
            and "'photographic'" in sup6[0])
    passed = row4 and row6
    return passed, f"event_precedence_both_lanes={row4}; photo_wall_posted_lane_unchanged={row6}"


CHECKS = [
    ("US1 explicit marketing usage beats the vibe promotion (all keywords, non-photo lanes)",
     check1_explicit_marketing_wins),
    ("US1 double gate: exactly one suppression line, photo gate first",
     check2_double_gate_single_entry),
    ("US2 legacy untouched: wall-posted byte-identical (both lanes), default still promotes",
     check3_legacy_untouched),
    ("US3 event-row precedence (both lanes) + 011 photo lane pinned",
     check4_event_precedence),
]


def main():
    print("=" * 78)
    print("test_explicit_usage_wins.py - falsifiable self-test (014, no paid calls)")
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
