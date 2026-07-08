#!/usr/bin/env python3
"""test_confirm_gate.py - falsifiable self-test for feature 015 (pre-spend confirm gate).

No paid calls anywhere: derive_register is imported pure; conductor/scene_author phases are
exercised with STUBBED run_step / generate_variant (the 009/012 drift-guard pattern). The
pre-015 baselines pinned here (T001) are the byte-identity references every later check
compares against:
  - the wall-posted register profile literal (imported from test_register_render_aware,
    the same pin 011/014 hold);
  - tests_support/fixtures/plan_thin_baseline.json (build_plan thin argv, frozen pre-015);
  - tests_support/fixtures/subfields_173925.json (the archived defect brief for SC-003).

Contract rows refer to specs/015-pre-spend-confirm-gate/contracts/.

Run:  .venv/bin/python test_confirm_gate.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "register"))
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO))
import derive_register as dr  # noqa: E402
import conductor  # noqa: E402
from test_register_render_aware import EXPECTED_PREFEATURE_PROFILE, _subfields  # noqa: E402

FIXTURES = REPO / "tests_support" / "fixtures"
PLAN_BASELINE = FIXTURES / "plan_thin_baseline.json"
SUBFIELDS_173925 = FIXTURES / "subfields_173925.json"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check1_baselines_hold():
    """T001: the pre-015 references are live properties of TODAY'S code, not stale copies.
    (a) the wall-posted profile still matches the pinned literal on both legacy lanes;
    (b) build_plan --thin over conductor_inputs_example.json equals the frozen fixture
        (--phase full must keep this byte-identity, checked again post-feature);
    (c) the archived 173925 defect subfields still derive marketing via ONE explicit
        suppression (the 014 behavior the gate builds on)."""
    absent = json.dumps(dr.derive_register(_subfields(), {}), ensure_ascii=False, sort_keys=True)
    flat = json.dumps(dr.derive_register(_subfields("flat vector"), {}),
                      ensure_ascii=False, sort_keys=True)
    a = absent == EXPECTED_PREFEATURE_PROFILE and flat == EXPECTED_PREFEATURE_PROFILE

    inputs = _load(REPO / "conductor_inputs_example.json")
    plan = conductor.build_plan(inputs, "aia", "/tmp/pin015", no_approve=True, thin=True)
    b = (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True)
         == PLAN_BASELINE.read_text(encoding="utf-8"))

    p = dr.derive_register(_load(SUBFIELDS_173925), {})
    sup = [t for t in p["_derivation_trace"] if "SUPPRESSED" in t]
    c = p["inferred_register"] == "marketing" and len(sup) == 1

    passed = a and b and c
    return passed, f"profile_pin={a}; plan_pin={b}; fixture_173925_marketing={c}"


CHECKS = [
    ("T001 pre-015 baselines hold (profile pin, thin plan pin, 173925 fixture)",
     check1_baselines_hold),
]


def main():
    print("=" * 78)
    print("test_confirm_gate.py - falsifiable self-test (015, no paid calls)")
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
