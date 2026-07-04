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


CHECKS = [
    ("US1 explicit marketing usage beats the vibe promotion (all keywords, non-photo lanes)",
     check1_explicit_marketing_wins),
    ("US1 double gate: exactly one suppression line, photo gate first",
     check2_double_gate_single_entry),
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
