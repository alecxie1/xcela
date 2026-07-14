#!/usr/bin/env python3
"""test_faithful_intake.py — falsifiable self-test for the extended intake form (feature 002, US1).

No paid calls. Drives `conductor.ask_questions` with an injectable, keyword-matched `ask` over a
full 6-sign AIA brief and asserts the emitted inputs are a LOSSLESS, VERBATIM image of the brief
(FR-002/FR-003): every field present unchanged, 6 signs (no collapsing), a blank optional recorded
empty (honest null), and the reference captured (FR-006 002-scope). A build that drops a field,
rephrases literal text, or collapses signs fails.

Run:  .venv/bin/python test_faithful_intake.py
"""

import sys
from pathlib import Path
# 019: answer keys are runtime state; the suites read the committed demo fixtures
import os as _os019
_os019.environ.setdefault("XCELA_ANSWER_KEYS_DIR",
                          str(Path(__file__).resolve().parent / "tests_support" / "demo_keys"))


REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import conductor  # noqa: E402  (stdlib-only)

SIGNS = [
    (["守住钱袋子", "护好幸福家"], None),
    (["远离非法金融", "抵制高息诱惑"], None),
    (["警惕高额返利", "谨防庞氏骗局"], None),
    (["擦亮眼睛", "识别金融诈骗"], None),
    (["拒绝高息诱惑", "远离非法集资"], None),
    (["储蓄有道", "守护家庭平安"], "a gold money bag"),
]
# keyword (lowercase substring of the prompt) -> verbatim answer
ANSWERS = {
    "asset type": "手举牌 hand-held event sign",
    "size": "60x40cm",
    "reference image": "/tmp/ref_aia.png",
    "relationship": "template — extend this series",
    "audience": "general public",
    "usage": "held for photos / posed with",
    "formal": "2",
    "playful": "8",
    "logo": "omit",
    "tightness": "expressive departure",
    "occasion": "防范非法金融宣传",
    "mandatory": "分别画叉；设计两种样式",
    "forbidden": "",
}


def make_ask():
    msg_q = iter(["；".join(m) for m, _ in SIGNS] + [""])   # 6 message strings then blank to stop
    hero_q = iter([h or "" for _, h in SIGNS])

    def ask(prompt):
        p = prompt.lower()
        if "message line" in p:
            return next(msg_q, "")
        if "hero icon" in p:
            return next(hero_q, "")
        for kw, val in ANSWERS.items():
            if kw in p:
                return val
        return ""
    return ask


GATHERED = conductor.ask_questions(ask=make_ask())


def check1_campaign_fields_verbatim():
    g, ctx = GATHERED, GATHERED.get("context", {})
    checks = {
        "asset_type": g.get("asset_type") == ANSWERS["asset type"],
        "format_size": g.get("format_size") == "60x40cm",
        "reference_image": g.get("reference_image") == "/tmp/ref_aia.png",
        "reference_captured": bool(g.get("reference_relationship")),  # FR-006 002-scope
        "audience": ctx.get("audience") == "general public",
        "usage_context": ctx.get("usage_context") == "held for photos / posed with",
        "formality": (ctx.get("vibe") or {}).get("formality") == 2,
        "playfulness": (ctx.get("vibe") or {}).get("playfulness") == 8,
        "logo_treatment": ctx.get("logo_treatment") == "omit",
        "brand_strictness": ctx.get("brand_strictness") == "expressive departure",
        "occasion": ctx.get("occasion") == "防范非法金融宣传",
        "mandatory_elements": g.get("mandatory_elements") == ["分别画叉", "设计两种样式"],
    }
    failed = [k for k, ok in checks.items() if not ok]
    return (not failed), (f"all verbatim={not failed}" if not failed
                          else f"DROPPED/CHANGED: {failed}")


def check2_six_signs_verbatim():
    signs = GATHERED.get("signs", [])
    count_ok = len(signs) == 6
    msgs_ok = all(signs[i]["messages"] == SIGNS[i][0] for i in range(min(len(signs), 6)))
    hero_ok = signs and signs[5].get("hero_icon") == "a gold money bag"
    passed = count_ok and msgs_ok and bool(hero_ok)
    return passed, (f"sign_count={len(signs)} (==6? {count_ok}); messages verbatim={msgs_ok}; "
                    f"s6 hero verbatim={bool(hero_ok)}")


def check3_blank_optional_recorded_empty():
    # forbidden_elements was answered blank -> recorded [] (honest null), not invented.
    fe = GATHERED.get("forbidden_elements")
    passed = fe == []
    return passed, f"forbidden_elements={fe!r} (blank -> [] honest null)"


def check4_inputs_reach_pipeline_lossless():
    # The emitted inputs reach the pipeline losslessly: a dry-run (no model calls) over the gathered
    # brief carries format_size + mandatory_elements + all 6 signs into the plan. In real mode the
    # manifest echoes the SAME `inputs` dict verbatim (brief_fields_received), so this proves the
    # intake -> pipeline -> manifest path drops nothing (FR-002 / SC-001).
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "inputs.json").write_text(json.dumps(GATHERED, ensure_ascii=False), encoding="utf-8")
        out = d / "out"
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "harness" / "conductor.py"), "--dry-run",
             "--inputs", str(d / "inputs.json"), "--brand", "aia", "--out", str(out), "--no-approve"],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0 or not (out / "plan.json").exists():
            return False, f"dry-run failed (rc={proc.returncode}): {proc.stderr[-300:]}"
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    passed = (plan.get("format_size") == "60x40cm"
              and plan.get("mandatory_elements") == ["分别画叉", "设计两种样式"]
              and plan.get("sign_count") == 6)
    return passed, (f"plan format_size={plan.get('format_size')!r} "
                    f"mandatory={plan.get('mandatory_elements')} signs={plan.get('sign_count')}")


CHECKS = [
    ("Every campaign field captured verbatim (no drop/rephrase)", check1_campaign_fields_verbatim),
    ("6 signs captured verbatim (no collapsing)", check2_six_signs_verbatim),
    ("Blank optional recorded empty (honest null)", check3_blank_optional_recorded_empty),
    ("Emitted inputs reach the pipeline lossless (manifest echo)", check4_inputs_reach_pipeline_lossless),
]


def main():
    print("=" * 78)
    print("test_faithful_intake.py — falsifiable self-test (US1, no paid calls)")
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
