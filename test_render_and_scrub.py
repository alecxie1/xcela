#!/usr/bin/env python3
"""test_render_and_scrub.py — falsifiable self-test for the two-axis change.

AXIS A render-and-scrub (universal) + AXIS B dial-driven prompt (per-task reference jobs).
NO paid calls: dial wording is a pure function; the prompt SOURCE / mode is proven via
scene_author --explain (which exits before any model call) and conductor --dry-run plans.
The actual image fidelity / scrub cleanliness / placement-match is NOT testable here — it
is the human's paid run + eye. Every check fails for a wrong/no-op implementation.

Run:  .venv/bin/python test_render_and_scrub.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
# 019: answer keys are runtime state; the suites read the committed demo fixtures
import os as _os019
_os019.environ.setdefault("XCELA_ANSWER_KEYS_DIR",
                          str(Path(__file__).resolve().parent / "tests_support" / "demo_keys"))


REPO_ROOT = Path(__file__).resolve().parent
CONDUCTOR = REPO_ROOT / "harness" / "conductor.py"
SCENE_AUTHOR = REPO_ROOT / "harness" / "scene_author.py"
CONDUCTOR_SRC = CONDUCTOR.read_text(encoding="utf-8")

sys.path.insert(0, str(REPO_ROOT / "harness"))
sys.path.insert(0, str(REPO_ROOT))
from register.reference_style_to_prompt import assemble_aligned_prompt, RELATIONSHIPS  # noqa: E402
from scene_author import assemble_final_prompt  # noqa: E402  (no API call at import)

DESCRIPTOR = {
    "colors": [{"hex": "#E2231A", "role": "field/background"},
               {"hex": "#FFD200", "role": "primary_accent"},
               {"hex": "#FFFFFF", "role": "text"}],
    "font_feel": "bold, heavy, rounded", "font_color": "white",
    "text_treatment": "thick white outline", "container_shape": "rounded die-cut sticker",
    "icon_style": "playful flat-vector cartoon",
    "hero_icon_device": "yes, a money bag protrudes past the edge",
    "overall_energy": "friendly, grabbable photo-prop",
    "negatives": ["not corporate", "not a photograph", "not 3D"],
}
LINES = ["守住钱袋子", "护好幸福家"]
RESERVE_TERMS = ("reserve a completely blank", "blank area", "reserved headline area",
                 "leave a blank", "blank box", "reserve a blank")


def scene_author_explain(extra_args):
    """Resolve scene_author's gen-prompt source + mode WITHOUT any model call (--explain)."""
    argv = [sys.executable, str(SCENE_AUTHOR), "--brand", "aia", "--out", "/tmp/_explain",
            "--asset-profile", "flat_graphic"] + extra_args + ["--explain"]
    proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"--explain failed (rc={proc.returncode}): {proc.stderr}")
    return json.loads(proc.stdout)


def conductor_plan(inputs_obj):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        f = d / "inputs.json"
        f.write_text(json.dumps(inputs_obj, ensure_ascii=False), encoding="utf-8")
        out = d / "out"
        proc = subprocess.run(
            [sys.executable, str(CONDUCTOR), "--dry-run", "--inputs", str(f),
             "--brand", inputs_obj.get("_brand", "aia"), "--out", str(out), "--no-approve"],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        plan_path = out / "plan.json"
        if proc.returncode != 0 or not plan_path.exists():
            raise RuntimeError(f"dry-run failed (rc={proc.returncode}): {proc.stderr}")
        return json.loads(plan_path.read_text(encoding="utf-8"))


def _inputs(reference=None, relationship=None, brand="aia"):
    return {
        "_brand": brand,
        "asset_type": "手举牌 hand-held event sign",
        "reference_image": reference,
        "reference_relationship": relationship,
        "context": {"usage_context": "held for photos / posed with",
                    "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
                    "logo_treatment": "omit", "brand_strictness": "expressive departure",
                    "occasion": "anti-fraud"},
        "signs": [{"id": "s1", "messages": LINES, "hero_icon": "a money bag"}],
    }


def scene_author_steps(plan):
    return [s for s in plan["steps"] if s.get("label") == "scene_author"]


def has_reserve(text):
    t = text.lower()
    return any(term in t for term in RESERVE_TERMS)


# --------------------------------------------------------------------------- #

def check1_dial_selects_wording():
    outs = {r: assemble_aligned_prompt(DESCRIPTOR, LINES, "a money bag", relationship=r)
            for r in RELATIONSHIPS}
    distinct = len(set(outs.values())) == 3
    extend_shape = ("EXACT visual-style template" in outs["extend"]
                    and "CHANGE ONLY THE MESSAGE" in outs["extend"])
    match_fresh = "FRESH layout" in outs["match_style"]
    mood_loose = "LOOSE inspiration" in outs["mood"]
    none_reserve = not any(has_reserve(outs[r]) for r in RELATIONSHIPS)
    all_render = all("render" in outs[r].lower() for r in RELATIONSHIPS)
    passed = distinct and extend_shape and match_fresh and mood_loose and none_reserve and all_render
    detail = (f"3 distinct prompts={distinct}; extend has proven 'EXACT template'/'CHANGE ONLY "
              f"THE MESSAGE' shape={extend_shape}; match_style=FRESH layout({match_fresh}); "
              f"mood=LOOSE inspiration({mood_loose}); none reserve a blank box={none_reserve}; "
              f"all render the text={all_render}")
    return passed, detail


def check2_aligned_prompt_injected():
    # (a) the conductor PLAN injects the aligned prompt for a reference job.
    # NOTE (feature 001): the aligned-prompt route is the LEGACY path, now used only for brands
    # WITHOUT an authored kit (a kit brand routes through bespoke composition instead, see
    # test_conductor check3). taichi has no kit, so it still exercises the legacy aligned-prompt route.
    plan = conductor_plan(_inputs(reference="/tmp/ref.png", relationship="extend", brand="taichi"))
    sa = scene_author_steps(plan)[0]["argv"]
    plan_injects = "--aligned-prompt" in sa
    # (b) scene_author actually USES it as the generation prompt (source), tier-3 skipped
    ex = scene_author_explain(["--aligned-prompt", "/tmp/whatever.txt", "--ref-image", "/tmp/ref.png"])
    uses_aligned = ex["generation_prompt_source"] == "aligned_prompt_file" and ex["uses_tier3"] is False
    # (c) the OLD discard behavior is gone: conductor no longer prints "NOT injected
    #     into generation", and it flips the record to injected on success.
    discard_gone = "NOT injected into generation" not in CONDUCTOR_SRC
    flips_true = "injected_into_generation=True" in CONDUCTOR_SRC
    passed = plan_injects and uses_aligned and discard_gone and flips_true
    detail = (f"plan passes --aligned-prompt to scene_author={plan_injects}; scene_author "
              f"--explain source={ex['generation_prompt_source']!r} uses_tier3={ex['uses_tier3']} "
              f"-> uses aligned={uses_aligned}; old 'NOT injected' discard removed={discard_gone}; "
              f"conductor flips injected=true on success={flips_true}")
    return passed, detail


def check3_render_and_scrub_universal():
    # no-ref default prompt (assemble_final_prompt, render_headline=True): no reserve box, headline IN
    bk = json.loads((REPO_ROOT / "tests_support" / "demo_keys" / "aia.json").read_text(encoding="utf-8"))
    tier3 = {"off_vi": False, "palette_resolved": [{"name": "r", "hex": "E2231A", "role": "primary"}],
             "background": "flat", "hero_staging": "x", "props": [], "composition": "centered",
             "container_shape": "die-cut", "text_graphic_hierarchy": "text dominates",
             "headline_reservation": {"x_frac": 0.2, "y_frac": 0.3, "w_frac": 0.6, "h_frac": 0.3},
             "text_layout": [{"content": "守住钱袋子", "position": "center", "composited": True,
                              "size_px": 120, "color_hex": "FFFFFF", "weight_hint": "heavy"}]}
    noref_default = assemble_final_prompt(bk, tier3, asset_profile="flat_graphic", render_headline=True)
    noref_legacy = assemble_final_prompt(bk, tier3, asset_profile="flat_graphic", render_headline=False)
    noref_ok = (not has_reserve(noref_default)) and "守住钱袋子" in noref_default
    legacy_still_reserves = has_reserve(noref_legacy)   # old path stays available behind the flag
    # ref default prompt (extend rung): no reserve box
    ref_default = assemble_aligned_prompt(DESCRIPTOR, LINES, "a money bag", relationship="extend")
    ref_ok = not has_reserve(ref_default)
    # --explain confirms BOTH default paths run render_and_scrub mode
    ex_noref = scene_author_explain(["--chroma-contain"])
    ex_ref = scene_author_explain(["--aligned-prompt", "/tmp/w.txt"])
    mode_ok = ex_noref["mode"] == "render_and_scrub" and ex_ref["mode"] == "render_and_scrub"
    passed = noref_ok and ref_ok and mode_ok and legacy_still_reserves
    detail = (f"no-ref default prompt: reserve-box absent + headline present={noref_ok}; "
              f"ref default prompt reserve-box absent={ref_ok}; both --explain mode="
              f"render_and_scrub={mode_ok}; legacy --reserve-headline-box still reserves "
              f"(rollback intact)={legacy_still_reserves}")
    return passed, detail


def check4_no_ref_planned_end_to_end():
    # The no-reference render-and-scrub conductor route is the LEGACY path (feature 001), now used
    # only for brands WITHOUT a kit. taichi has no kit, so it still plans register + render-and-scrub.
    plan = conductor_plan(_inputs(reference=None, brand="taichi"))
    labels = [s["label"] for s in plan["steps"]]
    sa = scene_author_steps(plan)[0]["argv"]
    ex = scene_author_explain(["--chroma-contain"])
    passed = ("derive_register" in labels and "scene_author" in labels
              and "analyzer" not in labels and "--chroma-contain" in sa
              and "--aligned-prompt" not in sa
              and ex["uses_tier3"] is True and ex["composite"] == "place_measured"
              and ex["chroma_key_hex"] == "#00B140")
    detail = (f"no-ref steps={labels}; scene_author keeps --chroma-contain + no --aligned-prompt; "
              f"--explain uses_tier3={ex['uses_tier3']} composite={ex['composite']!r} "
              f"chroma={ex['chroma_key_hex']!r} (register prompt + render-and-scrub)")
    return passed, detail


def check5_brand_generality():
    plan_aia = conductor_plan(_inputs(reference=None, brand="aia"))
    plan_tai = conductor_plan(_inputs(reference=None, brand="taichi"))
    ak_differ = (plan_aia["brand_paths"]["answer_key"] == "answer_keys/aia.json"
                 and plan_tai["brand_paths"]["answer_key"] == "answer_keys/taichi.json")
    sa_aia = scene_author_steps(plan_aia)[0]["argv"]
    sa_tai = scene_author_steps(plan_tai)[0]["argv"]
    brand_in_argv = ("aia" in sa_aia and "taichi" in sa_tai)
    no_literal = "aia" not in CONDUCTOR_SRC.lower()
    passed = ak_differ and brand_in_argv and no_literal
    detail = (f"answer keys differ by brand={ak_differ}; --brand in scene_author argv differs "
              f"(aia/taichi)={brand_in_argv}; no 'aia' literal in conductor.py={no_literal}")
    return passed, detail


CHECKS = [
    ("Dial selects wording (3 distinct; extend=proven; none reserve; all render)", check1_dial_selects_wording),
    ("Aligned prompt is INJECTED (plan + scene_author uses it, tier-3 skipped)", check2_aligned_prompt_injected),
    ("Render-and-scrub is the default (no reserve box, both ref + no-ref)", check3_render_and_scrub_universal),
    ("No-reference job planned end-to-end (register prompt + render-and-scrub)", check4_no_ref_planned_end_to_end),
    ("Brand-generality preserved (aia vs taichi; no brand literal)", check5_brand_generality),
]


def main():
    print("=" * 80)
    print("test_render_and_scrub.py — Axis A + B structural self-test (no paid calls)")
    print("=" * 80)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/5 — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/5 checks passed")
    print("=" * 80)
    sys.exit(0 if passed == 5 else 1)


if __name__ == "__main__":
    main()
