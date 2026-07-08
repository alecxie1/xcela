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


def check4_assumptions_out():
    """T004 (contracts/assumptions-schema.md): (a) unmatched usage + no calibration emits
    register_lane (reason=unmatched, canonical-pick options) + magnitude (reason=fallback);
    (b) blank usage emits reason=blank; (c) the 173925 defect fixture emits NO register_lane
    row (its usage explicitly matched 'social', a human statement; an always-ask build fails
    here) while still deriving the marketing lane the gate displays; (d) matched usage +
    calibration = ZERO records; (e) sink absent = profile byte-identical to the pin; (f) the
    CLI flag writes the file, and omitting it writes nothing."""
    import subprocess
    import tempfile

    sink = []
    dr.derive_register(_subfields(usage="goes viral on rednote"), {}, assumptions_sink=sink)
    ids = [r["id"] for r in sink]
    lane = next((r for r in sink if r["id"] == "register_lane"), None)
    a = (ids == ["register_lane", "magnitude"]
         and lane["cause"]["reason"] == "unmatched"
         and {"field": "context.usage_context", "value": "marketing"}
         in [o["writes"] for o in lane["options"]]
         and sink[1]["cause"]["reason"] == "fallback"
         and not any("—" in json.dumps(r, ensure_ascii=False) for r in sink))

    sink = []
    dr.derive_register(_subfields(usage=""), {}, assumptions_sink=sink)
    b = sink and sink[0]["id"] == "register_lane" and sink[0]["cause"]["reason"] == "blank"

    sink = []
    p = dr.derive_register(_load(SUBFIELDS_173925), {}, assumptions_sink=sink)
    c = (p["inferred_register"] == "marketing"
         and not any(r["id"] == "register_lane" for r in sink))

    sink = []
    dr.derive_register(_subfields(usage="marketing launch"), {},
                       calibration={"register_target": {"formality": 3, "playfulness": 7}},
                       assumptions_sink=sink)
    d = sink == []

    absent = json.dumps(dr.derive_register(_subfields(), {}), ensure_ascii=False, sort_keys=True)
    e = absent == EXPECTED_PREFEATURE_PROFILE

    with tempfile.TemporaryDirectory() as td:
        sf = Path(td) / "subfields.json"
        sf.write_text(json.dumps(_subfields(usage="goes viral on rednote")), encoding="utf-8")
        ap = Path(td) / "assumptions_register.json"
        r1 = subprocess.run([sys.executable, str(REPO / "register" / "derive_register.py"),
                             "--subfields", str(sf), "--brand", "aia", "--out", td,
                             "--assumptions-out", str(ap)], capture_output=True, text=True)
        with_flag = r1.returncode == 0 and ap.exists() and _load(ap)[0]["id"] == "register_lane"
        ap.unlink()
        r2 = subprocess.run([sys.executable, str(REPO / "register" / "derive_register.py"),
                             "--subfields", str(sf), "--brand", "aia", "--out", td],
                            capture_output=True, text=True)
        f = with_flag and r2.returncode == 0 and not ap.exists()

    passed = all([a, b, c, d, e, f])
    return passed, f"unmatched_emits={a}; blank_reason={b}; explicit_match_asks_nothing={c}; zero_guesses_empty={d}; no_sink_byte_identical={e}; cli_flag={f}"


def check5_conductor_assumptions():
    """T005: (a) each conductor record fires on its exact trigger and never on recognized
    input; (b) _dial_unrecognized mirrors normalize_dial (drift guard: recognized values
    never flagged, gibberish flagged AND folded to extend); (c) reasons distinguish blank /
    unparseable / clamped sizes; (d) the derive phase's derive_register argv carries
    --assumptions-out and assumptions.json is the engine+conductor union; (e) recognized
    everything + zero engine records = assumptions.json == []; (f) no em-dash anywhere."""
    import tempfile
    import format_size as fmtsize

    sr_bad = fmtsize.resolve_size("about poster size")
    sr_ok = fmtsize.resolve_size("60x40cm")
    bad = build_gate_inputs = {
        **_gate_inputs("ref.png"), "render_style": "watercolor",
        "reference_relationship": "随便什么 whatever"}
    recs = conductor.build_conductor_assumptions(bad, sr_bad)
    a1 = ([r["id"] for r in recs] == ["render_style", "relationship_dial", "format_size"]
          and all(r["source"] == "conductor" for r in recs))
    recs_ok = conductor.build_conductor_assumptions(_gate_inputs("ref.png"), sr_ok)
    a = a1 and recs_ok == []

    recognized = ["extend", "match_style", "mood", "template series", "style match",
                  "inspiration, loose"]
    b = (all(not conductor._dial_unrecognized(v) for v in recognized)
         and conductor._dial_unrecognized("随便什么 whatever")
         and conductor.normalize_dial("随便什么 whatever") == conductor.DEFAULT_DIAL)

    r_blank = conductor.build_conductor_assumptions(
        {**_gate_inputs(), "format_size": None}, fmtsize.resolve_size(None))
    r_unp = conductor.build_conductor_assumptions(
        {**_gate_inputs(), "format_size": "about poster size"},
        fmtsize.resolve_size("about poster size"))
    r_clamp = conductor.build_conductor_assumptions(
        {**_gate_inputs(), "format_size": "500x40cm"}, fmtsize.resolve_size("500x40cm"))
    c = ([r[-1]["cause"]["reason"] for r in (r_blank, r_unp, r_clamp)]
         == ["blank", "unparseable", "clamped"])

    ok_stub = lambda step: {"ok": True, "returncode": 0}  # noqa: E731
    with tempfile.TemporaryDirectory() as td:
        fake_engine = [{"id": "register_lane", "source": "derive_register", "options": []}]
        (Path(td) / "assumptions_register.json").write_text(
            json.dumps(fake_engine), encoding="utf-8")
        inputs = {**_gate_inputs(), "render_style": "watercolor"}
        rec, manifest, _ = _run_execute(td, inputs, "derive", ok_stub)
        derive_step = next(s for s in rec if s["label"] == "derive_register")
        union = _load(Path(td) / "assumptions.json")
        d = ("--assumptions-out" in derive_step["argv"]
             and [r["id"] for r in union] == ["register_lane", "render_style"]
             and union[0]["source"] == "derive_register")

    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "assumptions_register.json").write_text("[]", encoding="utf-8")
        rec, manifest, _ = _run_execute(td, _gate_inputs(), "derive", ok_stub)
        e = _load(Path(td) / "assumptions.json") == []

    f = "—" not in json.dumps(recs + r_blank + r_unp + r_clamp, ensure_ascii=False)
    passed = all([a, b, c, d, e, f])
    return passed, f"triggers_exact={a}; dial_mirror_guard={b}; size_reasons={c}; union_and_argv={d}; zero_guesses_empty_file={e}; no_emdash={f}"


def check7_gate_stage_and_panel():
    """T007: (a) run_view over a derive-phase run dir returns the gate stage per contract
    (present, state, assumptions, answers_applied); (b) a pre-015 run dir (no gate_state)
    returns present=false with the honest note AND its other stages render exactly as
    before; (c) presence greps (the weakest gate, declared per the 010 precedent): the
    panel, the confirm handler, the cost-stated confirm label, and NO em-dash in the new
    user-facing strings; the run/nudge controls no longer claim the run itself spends."""
    import tempfile
    sys.path.insert(0, str(REPO / "frontend"))
    import run_view as rv

    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "sign_s1").mkdir(parents=True)
        (Path(td) / "sign_s1" / "final_prompt.txt").write_text("p", encoding="utf-8")
        (Path(td) / "assumptions.json").write_text(
            json.dumps([{"id": "register_lane", "dimension": "d", "assumed_value": "v",
                         "cause": {"input": "context.usage_context", "value": None,
                                   "reason": "blank"}, "options": [], "source": "x"}]),
            encoding="utf-8")
        conductor.write_gate_state(td, "awaiting_confirmation")
        v = rv.run_view(td)
        a = (v["gate"]["present"] is True
             and v["gate"]["content"]["state"] == "awaiting_confirmation"
             and v["gate"]["content"]["assumptions"][0]["id"] == "register_lane"
             and v["gate"]["content"]["answers_applied"] == []
             and v["prompt"]["present"] is True and v["image"]["present"] is False)

    with tempfile.TemporaryDirectory() as td:
        v = rv.run_view(td)
        b = (v["gate"]["present"] is False and "pre-015" in (v["gate"]["note"] or "")
             and v["brief"]["present"] is False and "gate" not in v["brief"])

    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    new_bits = ["renderPreGate", "confirmRun", "Confirm and generate (paid",
                'id="pregate"', "free preview"]
    c = (all(s in html for s in new_bits)
         and "Run (paid" not in html
         and "Nudge and rerun" not in html)

    passed = a and b and c
    return passed, f"gate_stage_shape={a}; pre015_honest_null={b}; panel_greps={c}"


def check6_server_confirm_flow():
    """T006 (contracts/server-routes.md): (a) runner argv legacy shape byte-identical with
    phase=None, --phase appended otherwise; (b) decide_confirm: pre-015 dir -> 404 no launch;
    awaiting+prompt+meta -> 200 + launch + state confirmed with the prompt sha BEFORE launch;
    repeat -> 200 no-op no launch (FR-012, zero second spends); missing prompt -> 409 and the
    gate STAYS awaiting; missing run_meta -> 409 (the generate argv could not be reproduced)."""
    import hashlib
    import tempfile
    sys.path.insert(0, str(REPO / "frontend"))
    import runner as runner_mod
    import server as server_mod

    legacy = runner_mod.build_conductor_argv("in.json", "aia", style_notes="note")
    a = (legacy == [sys.executable, "harness/conductor.py", "--brand", "aia", "--thin",
                    "--no-approve", "--inputs", "in.json", "--style-notes", "note"]
         and runner_mod.build_conductor_argv("in.json", "aia", phase="derive")
         == legacy[:-2] + ["--phase", "derive"])

    with tempfile.TemporaryDirectory() as td:
        b = server_mod.decide_confirm(Path(td), "$0.08")[0] == 404

        (Path(td) / "sign_s1").mkdir(parents=True)
        (Path(td) / "sign_s1" / "final_prompt.txt").write_text("the prompt", encoding="utf-8")
        (Path(td) / "run_meta.json").write_text(
            json.dumps({"brand": "aia", "style_notes": "note"}), encoding="utf-8")
        conductor.write_gate_state(td, "awaiting_confirmation")
        code, payload, launch = server_mod.decide_confirm(Path(td), "$0.08")
        gs = _load(Path(td) / "gate_state.json")
        c = (code == 200 and launch and launch["brand"] == "aia"
             and launch["style_notes"] == "note"
             and gs["state"] == "confirmed"
             and gs["confirmation"]["confirmed_prompt_sha"]
             == hashlib.sha256(b"the prompt").hexdigest()
             and gs["confirmation"]["cost_stated"] == "$0.08")

        code2, payload2, launch2 = server_mod.decide_confirm(Path(td), "$0.08")
        d = code2 == 200 and launch2 is None and payload2.get("state") == "confirmed"

    with tempfile.TemporaryDirectory() as td:
        conductor.write_gate_state(td, "awaiting_confirmation")
        (Path(td) / "run_meta.json").write_text(json.dumps({"brand": "aia"}), encoding="utf-8")
        code, _, launch = server_mod.decide_confirm(Path(td), "$0.08")
        e = (code == 409 and launch is None
             and _load(Path(td) / "gate_state.json")["state"] == "awaiting_confirmation")

    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "sign_s1").mkdir(parents=True)
        (Path(td) / "sign_s1" / "final_prompt.txt").write_text("p", encoding="utf-8")
        conductor.write_gate_state(td, "awaiting_confirmation")
        f = server_mod.decide_confirm(Path(td), "$0.08")[0] == 409

    passed = all([a, b, c, d, e, f])
    return passed, f"argv_shapes={a}; pre015_404={b}; confirm_launches_once={c}; repeat_noop={d}; no_prompt_409_stays_awaiting={e}; no_meta_409={f}"


def check8_us1_end_to_end_free():
    """T008: the REAL (subprocess, zero paid calls) US1 flow. A no-reference thin derive run
    produces register_profile + final_prompt + assumptions.json + gate_state awaiting + the
    honest no-spend manifest note and NO generated.png; decide_confirm flips it to confirmed
    with a generate launch; a generate phase over TAMPERED inputs trips --verify-prompt
    BEFORE any generation (free), resetting the gate with the confirmation cleared. A build
    that generates during derive, or generates despite drift, fails here."""
    import subprocess
    import tempfile
    sys.path.insert(0, str(REPO / "frontend"))
    import server as server_mod

    with tempfile.TemporaryDirectory() as td:
        inputs = {"asset_type": "marketing post", "render_style": "flat vector",
                  "format_size": "60x40cm", "mandatory_elements": [], "forbidden_elements": [],
                  "context": {"usage_context": "goes viral on rednote",
                              "vibe": {"formality": 2, "playfulness": 8, "warmth": 5}},
                  "signs": [{"id": "s1", "messages": ["测试标语"]}]}
        ip = Path(td) / "inputs.json"
        ip.write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(REPO / "harness" / "conductor.py"),
                            "--brand", "aia", "--thin", "--no-approve", "--phase", "derive",
                            "--inputs", str(ip), "--out", td],
                           capture_output=True, text=True, cwd=str(REPO))
        gs = _load(Path(td) / "gate_state.json")
        assumptions = _load(Path(td) / "assumptions.json")
        manifest = _load(Path(td) / "conductor_manifest.json")
        a = (r.returncode == 0
             and (Path(td) / "register_profile.json").exists()
             and (Path(td) / "sign_s1" / "final_prompt.txt").exists()
             and not (Path(td) / "sign_s1" / "generated.png").exists()
             and gs["state"] == "awaiting_confirmation"
             and any(rec["id"] == "register_lane" for rec in assumptions)
             and "derived, awaiting confirmation; no image spend" in manifest["notes"])

        (Path(td) / "run_meta.json").write_text(
            json.dumps({"brand": "aia", "style_notes": None}), encoding="utf-8")
        code, _, launch = server_mod.decide_confirm(Path(td), "$0.08")
        b = code == 200 and launch is not None and _load(Path(td) / "gate_state.json")["state"] == "confirmed"

        tampered = dict(inputs)
        tampered["signs"] = [{"id": "s1", "messages": ["完全不同的标语"]}]
        ip.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        r2 = subprocess.run([sys.executable, str(REPO / "harness" / "conductor.py"),
                             "--brand", "aia", "--thin", "--no-approve", "--phase", "generate",
                             "--inputs", str(ip), "--out", td],
                            capture_output=True, text=True, cwd=str(REPO))
        gs2 = _load(Path(td) / "gate_state.json")
        c = (not (Path(td) / "sign_s1" / "generated.png").exists()
             and gs2["state"] == "awaiting_confirmation"
             and gs2["confirmation"] is None
             and "drift" in gs2.get("note", ""))

    passed = a and b and c
    return passed, f"real_derive_no_spend={a}; confirm_flips={b}; tampered_generate_blocked_free={c}"


def check9_formal_hard_row():
    """T009: (a) each new formal keyword derives register=formal as a HARD base even under a
    maximally playful vibe (formality 0, playfulness 10), on flat AND absent render lanes,
    with zero suppression lines (the statement never fights the promotion; a vibe-resolved
    formal_leaning build fails this); (b) event rows keep precedence ('official notice photo'
    -> event_prop via 'photo'); (c) the pinned wall-posted baseline stays byte-identical (the
    row is inert for every input lacking the phrases; also re-proven by checks 1/4 each run);
    (d) REGISTER_LANE_OPTIONS now carries the formal pick with the canonical write-back."""
    failures = []
    for kw in ("formal document", "official notice"):
        for render in (None, "flat vector"):
            sf = _subfields(render, usage=f"an {kw} for the branch")
            sf["vibe"] = {"formality": 0, "playfulness": 10, "warmth": 5}
            p = dr.derive_register(sf, {})
            sup = [t for t in p["_derivation_trace"] if "SUPPRESSED" in t]
            if not (p["inferred_register"] == "formal" and not sup):
                failures.append((kw, render, p["inferred_register"]))
    a = not failures

    p = dr.derive_register(_subfields(usage="official notice photo"), {})
    b = (p["inferred_register"] == "event_prop"
         and any("matched 'photo'" in t for t in p["_derivation_trace"]))

    absent = json.dumps(dr.derive_register(_subfields(), {}), ensure_ascii=False, sort_keys=True)
    c = absent == EXPECTED_PREFEATURE_PROFILE

    d = ({"field": "context.usage_context", "value": "formal document"}
         in [o["writes"] for o in dr.REGISTER_LANE_OPTIONS])

    passed = a and b and c and d
    return passed, f"formal_hard_despite_vibe={a} (failures={failures[:2]}); event_precedence={b}; pinned_inert={c}; option_shipped={d}"


CHECKS = [
    ("T001 pre-015 baselines hold (profile pin, thin plan pin, 173925 fixture)",
     check1_baselines_hold),
    ("T002 scene_author --prompt-only stops pre-spend; --verify-prompt drift guard",
     check2_prompt_only_and_drift_guard),
    ("T003 conductor --phase derive/generate/full: seam, resume, refusal, drift reset",
     check3_conductor_phases),
    ("T004 derive_register --assumptions-out: structured guesses, explicit matches ask nothing",
     check4_assumptions_out),
    ("T005 conductor assumption aggregation: exact triggers, dial mirror, engine+conductor union",
     check5_conductor_assumptions),
    ("T006 server: derive-first launch, idempotent cost-stated confirm (decide_confirm)",
     check6_server_confirm_flow),
    ("T007 gate stage in run_view + gate panel present in index.html",
     check7_gate_stage_and_panel),
    ("T008 US1 end to end, free: real derive stops pre-spend; tampered generate blocked",
     check8_us1_end_to_end_free),
    ("T009 formal lane hard row: deterministic despite vibe, inert for pinned inputs",
     check9_formal_hard_row),
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
