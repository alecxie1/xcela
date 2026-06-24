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


def dry_run(brand, inputs_obj, no_approve=True, extra_args=None):
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
        argv += list(extra_args or [])
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
    # Kit route (aia has a kit): different human messages must produce DIFFERENT bespoke
    # compositions (icon AND layout), not one re-texted template. A template machine fails this.
    plan_x = dry_run("aia", make_inputs([["守住钱袋子", "护好幸福家"]]))
    plan_y = dry_run("aia", make_inputs([["远离非法金融", "抵制高息诱惑"]]))
    cx = plan_x["compositions"][0]
    cy = plan_y["compositions"][0]
    passed = (bool(cx["chosen_icon"]) and bool(cy["chosen_icon"])
              and cx["chosen_icon"] != cy["chosen_icon"]
              and bool(cx["chosen_archetype"]) and bool(cy["chosen_archetype"]))
    detail = (f"inputs A -> icon={cx['chosen_icon']}/arch={cx['chosen_archetype']}; "
              f"inputs B -> icon={cy['chosen_icon']}/arch={cy['chosen_archetype']}; "
              f"icons differ={cx['chosen_icon'] != cy['chosen_icon']}")
    return passed, detail


def check3_primitive_sequence():
    # AIA has a kit -> KIT ROUTE: calibrate + derive_register -> kit -> scene_author (kit mode).
    # No analyzer/aligned-prompt: the reference feeds the kit, it does NOT clone a prompt (D6).
    # Two distinct-mode signs get DISTINCT archetypes. taichi has NO kit -> LEGACY route
    # (analyzer + aligned-prompt, no kit step), proving the routing is data-driven (kit presence),
    # not hardcoded per brand.
    plan = dry_run("aia", make_inputs([["守住钱袋子", "护好幸福家"], ["远离非法金融", "抵制高息诱惑"]],
                                      reference="/tmp/style_ref.png"))
    labels = [s["label"] for s in plan["steps"]]
    sa0 = scene_author_steps(plan)[0]["argv"]
    plan_text = json.dumps(plan, ensure_ascii=False)

    first_sa = labels.index("scene_author")
    register_before = labels.index("derive_register") < first_sa
    kit_before_sa = "kit" in labels and labels.index("kit") < first_sa
    kit_flags_ok = (all(tok in sa0 for tok in ("flat_graphic", "--kit-profile", "--composition"))
                    and "--aligned-prompt" not in sa0 and "--must-include" not in sa0)
    archs = [c["chosen_archetype"] for c in plan["compositions"]]
    distinct_archetypes = len(archs) == 2 and archs[0] and archs[1] and archs[0] != archs[1]
    no_analyzer_in_kit = "analyzer" not in labels
    delegates = all(name in plan_text for name in
                    ("harness/scene_author.py", "register/derive_register.py", "harness/kit.py"))
    # No-op guard: the conductor must DELEGATE generation, never reimplement it. Assert the real
    # generation CALLS are absent (images.edit(, b64decode() with a paren), not mere token presence —
    # feature 003 added honest comments/help text mentioning gpt-image-2, which is documentation, not
    # a reimplementation. Strip comments so a '# ... gpt-image-2 ...' note never trips this.
    _code_lines = [ln.split("#", 1)[0] for ln in CONDUCTOR_SRC.splitlines()]
    _code_no_comments = "\n".join(_code_lines)
    no_reimpl = not any(tok in _code_no_comments for tok in ("images.edit(", "b64decode("))

    # taichi (no kit) must still take the LEGACY route — falsifies a hardcoded kit route.
    legacy = dry_run("taichi", make_inputs([["一"]], reference="/tmp/style_ref.png"))
    legacy_labels = [s["label"] for s in legacy["steps"]]
    legacy_sa = scene_author_steps(legacy)[0]["argv"]
    legacy_ok = ("analyzer" in legacy_labels and "kit" not in legacy_labels
                 and "--aligned-prompt" in legacy_sa)

    passed = (register_before and kit_before_sa and kit_flags_ok and bool(distinct_archetypes)
              and no_analyzer_in_kit and delegates and no_reimpl and legacy_ok)
    detail = (f"kit order={labels}; register-before-sign={register_before}; "
              f"kit-before-scene_author={kit_before_sa}; kit scene_author flags ok="
              f"{kit_flags_ok}; distinct archetypes={archs} ({bool(distinct_archetypes)}); "
              f"no analyzer in kit route={no_analyzer_in_kit}; delegates by name={delegates}; "
              f"no generation reimplemented={no_reimpl}; taichi legacy route intact={legacy_ok}")
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

    # (b) the input gate actually drives inputs (questions are not ignored). Keyword-matched so it
    # is robust to the 002 question-order changes (format_size / audience / usage / mandatory ...).
    sign_msgs = iter(["守住钱袋子；护好幸福家", ""])
    hero = iter(["money bag"])

    def fake_ask(prompt):
        p = prompt.lower()
        if "message line" in p:
            return next(sign_msgs, "")
        if "hero icon" in p:
            return next(hero, "")
        if "asset type" in p:
            return "CUSTOM-ASSET"
        if "formal" in p:
            return "2"
        if "playful" in p:
            return "8"
        if "logo" in p:
            return "omit"
        return ""  # all other prompts take their default

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


def check6_brief_fields_carried():
    # Feature 002: the conductor accepts + CARRIES the 3 previously-dropped fields from a
    # pre-written inputs JSON with NO intake form (the SC-004 standalone proof + FR-002 carry),
    # and stays BACK-COMPAT when they are absent.
    base = make_inputs([["守住钱袋子", "护好幸福家"], ["远离非法金融"]])
    with_fields = dict(base, format_size="60x40cm",
                       mandatory_elements=["分别画叉", "设计两种样式"], forbidden_elements=[])
    plan_w = dry_run("aia", with_fields)
    plan_wo = dry_run("aia", base)  # back-compat: no new fields
    carried = (plan_w.get("format_size") == "60x40cm"
               and plan_w.get("mandatory_elements") == ["分别画叉", "设计两种样式"])
    back_compat = (plan_wo.get("format_size") is None
                   and plan_wo.get("mandatory_elements") == []
                   and plan_wo["sign_count"] == 2)
    passed = carried and back_compat
    detail = (f"with fields -> format_size={plan_w.get('format_size')!r} "
              f"mandatory={plan_w.get('mandatory_elements')}; carried={carried}; "
              f"without fields -> format_size={plan_wo.get('format_size')!r} "
              f"mandatory={plan_wo.get('mandatory_elements')} (back-compat={back_compat})")
    return passed, detail


def check7_style_notes_threads_thin():
    # Feature 004: a top-level --style-notes (campaign) threads into the THIN scene_author argv,
    # so the browser taste gate's nudge reaches generation non-interactively. Back-compat: a thin
    # run without --style-notes omits it (the standalone thin route is unchanged).
    plan = dry_run("aia", make_inputs([["守住钱袋子"]]),
                   extra_args=["--thin", "--style-notes", "make it bolder"])
    sa = scene_author_steps(plan)[0]["argv"]
    threaded = flag_value(sa, "--style-notes") == "make it bolder" and "--thin" in sa
    plan2 = dry_run("aia", make_inputs([["守住钱袋子"]]), extra_args=["--thin"])
    sa2 = scene_author_steps(plan2)[0]["argv"]
    back_compat = "--style-notes" not in sa2 and "--thin" in sa2
    passed = threaded and back_compat
    detail = (f"thin argv --style-notes={flag_value(sa, '--style-notes')!r} (threaded={threaded}); "
              f"no-notes thin omits it={back_compat}")
    return passed, detail


CHECKS = [
    ("Brand-generality (kills hardcoding)", check1_brand_generality),
    ("Human input drives output (kills input-ignoring)", check2_inputs_drive_output),
    ("Correct primitive sequence + delegates (not reimplements)", check3_primitive_sequence),
    ("Sign-count generality (real N-sign loop)", check4_sign_count_generality),
    ("Human gates present (input + approve)", check5_human_gates),
    ("Brief fields carried + back-compat (002 / SC-004 standalone)", check6_brief_fields_carried),
    ("Style-notes threads to thin scene_author (004 nudge surface)", check7_style_notes_threads_thin),
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
        print(f"\nCHECK {i}/{len(CHECKS)} — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed_count}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed_count == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
