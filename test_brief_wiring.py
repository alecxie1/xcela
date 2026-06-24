#!/usr/bin/env python3
"""test_brief_wiring.py — falsifiable self-test that the dropped fields reach generation (002, US2).

No paid calls. A dry-run of a brief with 分别画叉 + 60x40cm must record the size_resolution +
mandatory_elements in the plan/manifest, the kit prompt must CONTAIN 分别画叉 (FR-004/SC-002), an
absent mandatory list must fabricate nothing (honest null), and a mandatory/forbidden conflict must
raise needs_review (constitution V). The current build drops both fields; that is what this asserts.

Run:  .venv/bin/python test_brief_wiring.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import conductor  # noqa: E402
import scene_author  # noqa: E402  (no API call at import)
import kit as kitlib  # noqa: E402

KIT = kitlib.load_kit("aia")


def _inputs(mandatory, forbidden=None, format_size="60x40cm"):
    return {
        "asset_type": "手举牌 hand-held event sign",
        "format_size": format_size,
        "mandatory_elements": mandatory,
        "forbidden_elements": forbidden or [],
        "context": {"usage_context": "held for photos / posed with",
                    "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
                    "logo_treatment": "omit", "brand_strictness": "expressive departure",
                    "occasion": "anti-fraud"},
        "signs": [{"id": "s1", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": None}],
    }


def _dry_run(inputs_obj):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "in.json").write_text(json.dumps(inputs_obj, ensure_ascii=False), encoding="utf-8")
        out = d / "out"
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "harness" / "conductor.py"), "--dry-run",
             "--inputs", str(d / "in.json"), "--brand", "aia", "--out", str(out), "--no-approve"],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0 or not (out / "plan.json").exists():
            raise RuntimeError(f"dry-run failed (rc={proc.returncode}): {proc.stderr[-300:]}")
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
        comp = json.loads((out / "sign_s1" / "composition.json").read_text(encoding="utf-8"))
        return plan, comp


def check1_size_and_mandatory_in_plan():
    plan, comp = _dry_run(_inputs(["分别画叉", "设计两种样式"]))
    sr = plan["size_resolution"]
    passed = (sr["width"] == 1536 and sr["height"] == 1024 and sr["orientation"] == "landscape"
              and plan["mandatory_elements"] == ["分别画叉", "设计两种样式"]
              and comp["mandatory_elements"] == ["分别画叉", "设计两种样式"])
    return passed, (f"plan size={sr['width']}x{sr['height']} ({sr['orientation']}); "
                    f"plan mandatory={plan['mandatory_elements']}; composition carries it="
                    f"{comp['mandatory_elements'] == ['分别画叉', '设计两种样式']}")


def check2_mandatory_in_kit_prompt():
    _, comp = _dry_run(_inputs(["分别画叉", "设计两种样式"]))
    prompt = scene_author.assemble_kit_prompt(KIT, {}, comp)
    passed = "分别画叉" in prompt and "设计两种样式" in prompt
    return passed, f"分别画叉 in kit prompt={'分别画叉' in prompt}; 设计两种样式 in prompt={'设计两种样式' in prompt}"


def check3_no_mandatory_fabricates_nothing():
    _, comp = _dry_run(_inputs([]))
    prompt = scene_author.assemble_kit_prompt(KIT, {}, comp)
    passed = comp["mandatory_elements"] == [] and "REQUIRED elements" not in prompt
    return passed, f"empty mandatory -> composition={comp['mandatory_elements']}; no REQUIRED clause={'REQUIRED elements' not in prompt}"


def check4_conflict_flags_needs_review():
    plan, _ = _dry_run(_inputs(["分别画叉"], forbidden=["分别画叉"]))
    nrc = plan.get("needs_review_campaign")
    passed = bool(nrc) and "分别画叉" in nrc
    return passed, f"needs_review_campaign={nrc!r}"


CHECKS = [
    ("format_size + mandatory recorded in the plan + composition", check1_size_and_mandatory_in_plan),
    ("mandatory_elements reach the kit prompt verbatim (SC-002)", check2_mandatory_in_kit_prompt),
    ("No mandatory -> nothing fabricated (honest null)", check3_no_mandatory_fabricates_nothing),
    ("mandatory ∩ forbidden conflict -> needs_review (§V)", check4_conflict_flags_needs_review),
]


def main():
    print("=" * 78)
    print("test_brief_wiring.py — falsifiable self-test (US2, no paid calls)")
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
