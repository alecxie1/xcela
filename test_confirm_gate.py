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


def _stub_generate():
    """Inject a fake `generate` module (records calls, writes a fake png). Returns the
    call list; caller must restore sys.modules['generate'] afterwards."""
    import types
    calls = []
    fake = types.ModuleType("generate")

    def generate_variant(prompt, refs, out_png, size="1536x1024", quality="high"):
        calls.append({"prompt": prompt, "refs": list(refs), "out": out_png})
        Path(out_png).write_bytes(b"\x89PNGfake" * 20000)
        return {"stub": True, "size": size}

    fake.generate_variant = generate_variant
    prior = sys.modules.get("generate")
    sys.modules["generate"] = fake
    return calls, prior


def _thin_args(out, prompt_only=False, verify_prompt=False, must="测试标语"):
    import argparse
    return argparse.Namespace(
        brand="aia", out=str(out), must_include=must, register_profile="",
        mandatory_elements="", forbidden_elements="", dial="", ref_image="",
        style_notes="", product_image=None, explain=False, size="1536x1024",
        asset_profile="flat_graphic", asset_type="", occasion="",
        prompt_only=prompt_only, verify_prompt=verify_prompt)


def check2_prompt_only_and_drift_guard():
    """T002 (contracts/cli-phases.md, scene_author rows): a wrong build cannot satisfy all
    four: (a) --prompt-only writes final_prompt.txt + a generation:null manifest and makes
    ZERO generate calls; (b) --verify-prompt over the unchanged prompt proceeds to exactly
    ONE generate call; (c) --verify-prompt over a MUTATED final_prompt.txt fails loud
    (SystemExit, zero new calls); (d) --verify-prompt with no confirmed prompt fails loud."""
    import tempfile
    import scene_author as sa
    calls, prior = _stub_generate()
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sign_s1"
            sa.run_thin_mode(_thin_args(out, prompt_only=True))
            manifest = _load(out / "run_manifest.json")
            a = ((out / "final_prompt.txt").exists()
                 and not (out / "generated.png").exists()
                 and manifest["generation"] is None and len(calls) == 0)

            sa.run_thin_mode(_thin_args(out, verify_prompt=True))
            b = len(calls) == 1 and (out / "generated.png").exists()

            (out / "final_prompt.txt").write_text("tampered", encoding="utf-8")
            try:
                sa.run_thin_mode(_thin_args(out, verify_prompt=True))
                c = False
            except SystemExit as exc:
                c = exc.code != 0 and len(calls) == 1

            fresh = Path(td) / "sign_s2"
            try:
                sa.run_thin_mode(_thin_args(fresh, verify_prompt=True))
                d = False
            except SystemExit as exc:
                d = exc.code != 0 and len(calls) == 1
    finally:
        if prior is not None:
            sys.modules["generate"] = prior
        else:
            sys.modules.pop("generate", None)
    passed = a and b and c and d
    return passed, f"prompt_only_stops={a}; verify_match_generates_once={b}; drift_fails_loud={c}; missing_prompt_fails_loud={d}"


CHECKS = [
    ("T001 pre-015 baselines hold (profile pin, thin plan pin, 173925 fixture)",
     check1_baselines_hold),
    ("T002 scene_author --prompt-only stops pre-spend; --verify-prompt drift guard",
     check2_prompt_only_and_drift_guard),
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
