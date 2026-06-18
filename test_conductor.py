#!/usr/bin/env python3
"""test_conductor.py — falsifiable self-test for harness/conductor.py.

Asserts STRUCTURAL correctness via --dry-run (NO gpt-image-2, NO Anthropic, NO vision
call anywhere). Every check is designed so a WRONG or no-op conductor fails it:
hardcoded brand, ignored inputs, reimplemented generation, fixed sign count, or
missing human gates all produce a red check.

Run:  .venv/bin/python test_conductor.py     (plain python works too; stdlib only)
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CONDUCTOR = REPO_ROOT / "harness" / "conductor.py"
CONDUCTOR_SRC = CONDUCTOR.read_text(encoding="utf-8")

sys.path.insert(0, str(REPO_ROOT / "harness"))
import conductor  # noqa: E402  (stdlib-only module; safe to import without API keys)

ASSET = conductor.ASSET_TYPE_DEFAULT


def make_inputs(messages_per_sign, reference=None):
    """messages_per_sign: list of message-line lists, one per sign."""
    return {
        "asset_type": ASSET,
        "reference_image": reference,
        "reference_relationship": None,
        "context": {
            "usage_context": "held for photos / posed with",
            "audience": "general public",
            "setting": "event / festival",
            "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
            "logo_treatment": "omit",
            "brand_strictness": "expressive departure",
            "occasion": "anti-fraud awareness",
        },
        "signs": [{"id": f"s{i + 1}", "messages": m, "hero_icon": None}
                  for i, m in enumerate(messages_per_sign)],
    }


def dry_run(brand, inputs_obj, no_approve=True):
    """Run the conductor in --dry-run and return its plan.json as a dict.
    Raises with captured stderr if the run fails or writes no plan."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        inputs_path = d / "inputs.json"
        inputs_path.write_text(json.dumps(inputs_obj, ensure_ascii=False), encoding="utf-8")
        out = d / "out"
        argv = [sys.executable, str(CONDUCTOR), "--dry-run",
                "--inputs", str(inputs_path), "--brand", brand, "--out", str(out)]
        if no_approve:
            argv.append("--no-approve")
        proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
        plan_path = out / "plan.json"
        if proc.returncode != 0 or not plan_path.exists():
            raise RuntimeError(f"dry-run failed (rc={proc.returncode})\nSTDERR:\n{proc.stderr}")
        return json.loads(plan_path.read_text(encoding="utf-8"))


def scene_author_steps(plan):
    return [s for s in plan["steps"] if s.get("label") == "scene_author"]


def flag_value(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


# --------------------------------------------------------------------------- #
# The five checks. Each returns (passed: bool, detail: str with the REAL values).
# --------------------------------------------------------------------------- #

def check1_brand_generality():
    inputs = make_inputs([["A"]])
    plan_a = dry_run("aia", inputs)
    plan_b = dry_run("taichi", inputs)
    ak_a = plan_a["brand_paths"]["answer_key"]
    ak_b = plan_b["brand_paths"]["answer_key"]
    cfg_a = plan_a["brand_paths"]["config"]
    cfg_b = plan_b["brand_paths"]["config"]
    no_hardcoded = "aia" not in CONDUCTOR_SRC.lower()
    passed = (ak_a == "answer_keys/aia.json" and ak_b == "answer_keys/taichi.json"
              and ak_a != ak_b and cfg_a == "config/aia.yaml" and cfg_b == "config/taichi.yaml"
              and no_hardcoded)
    detail = (f"aia -> {ak_a} / {cfg_a}; taichi -> {ak_b} / {cfg_b}; "
              f"brand paths differ={ak_a != ak_b}; no 'aia' literal in conductor.py={no_hardcoded}")
    return passed, detail


def check2_inputs_drive_output():
    plan_x = dry_run("aia", make_inputs([["守住钱袋子", "护好幸福家"]]))
    plan_y = dry_run("aia", make_inputs([["远离非法金融", "抵制高息诱惑"]]))
    mi_x = flag_value(scene_author_steps(plan_x)[0]["argv"], "--must-include")
    mi_y = flag_value(scene_author_steps(plan_y)[0]["argv"], "--must-include")
    passed = (mi_x == "守住钱袋子;护好幸福家" and mi_y == "远离非法金融;抵制高息诱惑" and mi_x != mi_y)
    detail = f"inputs A --must-include={mi_x!r}; inputs B --must-include={mi_y!r}; differ={mi_x != mi_y}"
    return passed, detail


def check3_primitive_sequence():
    # reference present (path need not exist for a dry run) -> calibrate + analyzer appear
    plan = dry_run("aia", make_inputs([["守住钱袋子", "护好幸福家"]], reference="/tmp/style_ref.png"))
    labels = [s["label"] for s in plan["steps"]]
    sa = scene_author_steps(plan)[0]["argv"]
    plan_text = json.dumps(plan, ensure_ascii=False)

    first_sa = labels.index("scene_author")
    register_before = labels.index("calibrate") < first_sa and labels.index("derive_register") < first_sa
    analyzer_before_sa = labels.index("analyzer") == first_sa - 1
    sa_flags_ok = all(tok in sa for tok in
                      ("flat_graphic", "--chroma-contain", "--register-profile",
                       "--must-include", "--ref-image"))
    delegates = ("harness/scene_author.py" in plan_text
                 and "register/derive_register.py" in plan_text)
    no_reimpl = not any(tok in CONDUCTOR_SRC for tok in ("images.edit", "gpt-image-2", "b64decode"))
    passed = register_before and analyzer_before_sa and sa_flags_ok and delegates and no_reimpl
    detail = (f"order={labels}; register-before-sign={register_before}; "
              f"analyzer-immediately-before-scene_author={analyzer_before_sa}; "
              f"scene_author flags present={sa_flags_ok}; delegates by name={delegates}; "
              f"no generation reimplemented in conductor.py={no_reimpl}")
    return passed, detail


def check4_sign_count_generality():
    one = dry_run("aia", make_inputs([["一"]]))
    three = dry_run("aia", make_inputs([["一"], ["二"], ["三"]]))
    n1 = len(scene_author_steps(one))
    n3 = len(scene_author_steps(three))
    passed = n1 == 1 and n3 == 3
    detail = f"1-sign inputs -> {n1} scene_author invocation(s); 3-sign inputs -> {n3}"
    return passed, detail


def check5_human_gates():
    # (a) approve gate present by default, absent with --no-approve
    with_gate = dry_run("aia", make_inputs([["一"]]), no_approve=False)
    without_gate = dry_run("aia", make_inputs([["一"]]), no_approve=True)
    has_approve = any(s.get("label") == "approve" and s.get("kind") == "gate"
                      for s in with_gate["steps"])
    no_approve_when_flagged = not any(s.get("label") == "approve" for s in without_gate["steps"])

    # (b) the input gate actually drives inputs (questions are not ignored)
    answers = iter(["CUSTOM-ASSET", "", "2", "8", "omit", "expressive departure",
                    "anti-fraud", "守住钱袋子；护好幸福家", "money bag", ""])

    def fake_ask(_prompt):
        return next(answers, "")

    gathered = conductor.ask_questions(ask=fake_ask)
    input_drives = (gathered["asset_type"] == "CUSTOM-ASSET"
                    and gathered["context"]["vibe"]["formality"] == 2
                    and gathered["context"]["vibe"]["playfulness"] == 8
                    and gathered["context"]["logo_treatment"] == "omit"
                    and gathered["signs"][0]["messages"] == ["守住钱袋子", "护好幸福家"]
                    and gathered["signs"][0]["hero_icon"] == "money bag")
    passed = has_approve and no_approve_when_flagged and input_drives
    detail = (f"approve gate present by default={has_approve}; "
              f"approve gate absent with --no-approve={no_approve_when_flagged}; "
              f"questions drive inputs (asset_type={gathered['asset_type']!r}, "
              f"formality={gathered['context']['vibe']['formality']}, "
              f"messages={gathered['signs'][0]['messages']})={input_drives}")
    return passed, detail


CHECKS = [
    ("Brand-generality (kills hardcoding)", check1_brand_generality),
    ("Human input drives output (kills input-ignoring)", check2_inputs_drive_output),
    ("Correct primitive sequence + delegates (not reimplements)", check3_primitive_sequence),
    ("Sign-count generality (real N-sign loop)", check4_sign_count_generality),
    ("Human gates present (input + approve)", check5_human_gates),
]


def main():
    print("=" * 78)
    print("test_conductor.py — falsifiable structural self-test (dry-run only, no image gen)")
    print("=" * 78)
    passed_count = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed_count += int(ok)
        print(f"\nCHECK {i}/5 — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed_count}/5 checks passed")
    print("=" * 78)
    sys.exit(0 if passed_count == 5 else 1)


if __name__ == "__main__":
    main()
