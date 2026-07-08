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


def _gate_inputs(ref=None):
    return {
        "asset_type": "marketing post", "render_style": "flat vector",
        "format_size": "60x40cm", "reference_image": ref,
        "reference_relationship": "extend these",
        "mandatory_elements": [], "forbidden_elements": [],
        "context": {"usage_context": "wall-posted",
                    "vibe": {"formality": 2, "playfulness": 8, "warmth": 5}},
        "signs": [{"id": "s1", "messages": ["测试标语"]}],
    }


def _run_execute(td, inputs, phase, stub):
    """Call conductor.execute with run_step stubbed; returns (recorded_steps, manifest).
    A minimal register_profile.json is pre-created so the stubbed derive step counts as
    have_profile=True and the executed scene_author argv keeps --register-profile (the
    honest-null drop lane is not what these checks target)."""
    (Path(td) / "register_profile.json").write_text(json.dumps(
        {"inferred_register": "marketing", "brand_anchors_held": [],
         "brand_locks_flexed": [], "_derivation_trace": []}), encoding="utf-8")
    inputs_path = Path(td) / "inputs.json"
    inputs_path.write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    plan = conductor.build_plan(inputs, "aia", td, no_approve=True, thin=True)
    recorded = []

    def fake_run_step(step):
        recorded.append(step)
        return {"label": step["label"], "phase": step["phase"], **stub(step)}

    real = conductor.run_step
    conductor.run_step = fake_run_step
    try:
        manifest = conductor.execute(inputs, "aia", td, inputs_path, True, plan,
                                     thin=True, phase=phase)
    finally:
        conductor.run_step = real
    return recorded, manifest, plan


def check3_conductor_phases():
    """T003 (contracts/cli-phases.md, conductor rows): (a) derive phase executes the PLAN argv
    plus exactly --prompt-only on the sign step, writes gate_state awaiting_confirmation + the
    honest no-spend note, defers the approve gate; (b) a derive re-run with calibration.json
    present records NO calibrate step and PRESERVES answers_applied; (c) generate refuses an
    unconfirmed dir (SystemExit); (d) a confirmed generate runs the sign step with exactly
    --verify-prompt, no register steps, and lands state=done; (e) a drift exit (rc 3) resets
    the gate to awaiting_confirmation with the confirmation cleared."""
    import tempfile
    ok_stub = lambda step: {"ok": True, "returncode": 0}  # noqa: E731

    with tempfile.TemporaryDirectory() as td:
        rec, manifest, plan = _run_execute(td, _gate_inputs(), "derive", ok_stub)
        plan_sa = next(s for s in plan["steps"] if s["label"] == "scene_author")
        exec_sa = next(s for s in rec if s["label"] == "scene_author")
        gs = _load(Path(td) / "gate_state.json")
        a = (exec_sa["argv"] == plan_sa["argv"] + ["--prompt-only"]
             and gs["state"] == "awaiting_confirmation"
             and "derived, awaiting confirmation; no image spend" in manifest["notes"]
             and manifest["approve_status"].startswith("deferred")
             and manifest["phase"] == "derive")

    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.png"
        ref.write_bytes(b"\x89PNGfake")
        (Path(td) / "calibration.json").write_text("{}", encoding="utf-8")
        conductor.write_gate_state(td, "awaiting_confirmation")
        prior = conductor.read_gate_state(td)
        prior["answers_applied"] = [{"assumption_id": "register_lane"}]
        (Path(td) / "gate_state.json").write_text(json.dumps(prior), encoding="utf-8")
        rec, manifest, _ = _run_execute(td, _gate_inputs(str(ref)), "derive", ok_stub)
        gs = _load(Path(td) / "gate_state.json")
        b = (not any(s["label"] == "calibrate" for s in rec)
             and any(s["label"] == "derive_register" for s in rec)
             and gs["answers_applied"] == [{"assumption_id": "register_lane"}]
             and "reused existing calibration.json" in manifest["register"]["calibration_outcome"])

    with tempfile.TemporaryDirectory() as td:
        try:
            _run_execute(td, _gate_inputs(), "generate", ok_stub)
            c = False
        except SystemExit as exc:
            c = "confirmed" in str(exc.code)

    with tempfile.TemporaryDirectory() as td:
        sign_dir = Path(td) / "sign_s1"
        sign_dir.mkdir(parents=True)
        (sign_dir / "final_prompt.txt").write_text("the confirmed prompt", encoding="utf-8")
        conductor.write_gate_state(td, "confirmed",
                                   confirmation={"confirmed_prompt_sha": "x", "cost_stated": "$0.08"})
        rec, manifest, plan = _run_execute(td, _gate_inputs(), "generate", ok_stub)
        plan_sa = next(s for s in plan["steps"] if s["label"] == "scene_author")
        exec_sa = next(s for s in rec if s["label"] == "scene_author")
        gs = _load(Path(td) / "gate_state.json")
        d = (exec_sa["argv"] == plan_sa["argv"] + ["--verify-prompt"]
             and not any(s["label"] in ("calibrate", "derive_register") for s in rec)
             and gs["state"] == "done" and manifest["phase"] == "generate")

    with tempfile.TemporaryDirectory() as td:
        sign_dir = Path(td) / "sign_s1"
        sign_dir.mkdir(parents=True)
        (sign_dir / "final_prompt.txt").write_text("the confirmed prompt", encoding="utf-8")
        conductor.write_gate_state(td, "confirmed",
                                   confirmation={"confirmed_prompt_sha": "x"})
        rec, manifest, _ = _run_execute(td, _gate_inputs(), "generate",
                                        lambda step: {"ok": False, "returncode": 3})
        gs = _load(Path(td) / "gate_state.json")
        e = (gs["state"] == "awaiting_confirmation" and gs["confirmation"] is None
             and "drift" in gs.get("note", ""))

    passed = a and b and c and d and e
    return passed, f"derive_argv_and_state={a}; rederive_skips_calibrate_keeps_answers={b}; unconfirmed_refused={c}; generate_argv_and_done={d}; drift_resets={e}"


CHECKS = [
    ("T001 pre-015 baselines hold (profile pin, thin plan pin, 173925 fixture)",
     check1_baselines_hold),
    ("T002 scene_author --prompt-only stops pre-spend; --verify-prompt drift guard",
     check2_prompt_only_and_drift_guard),
    ("T003 conductor --phase derive/generate/full: seam, resume, refusal, drift reset",
     check3_conductor_phases),
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
