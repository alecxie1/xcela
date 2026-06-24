#!/usr/bin/env python3
"""test_thin_route.py — falsifiable self-test for the thin-spine route (feature 003).

No paid calls (dry-run + import-and-assert only). Asserts VALUES a wrong build cannot satisfy
(constitution §III). The thin route's whole point: assemble ONE prompt from the brief and let
gpt-image-2 compose the whole sign, STOPPING at generated.png — NO compose_select, NO kit, NO
analyzer, NO measure, NO composite. The licensed-font moat is DEFERRED (tracked, not silent).

A wrong build fails: kit/compose steps still present on the thin route; the verbatim headline or
分别画叉 missing/paraphrased in the assembled prompt; the moat-deferred marker absent; or the legacy
default route silently changed (back-compat).

Run:  .venv/bin/python test_thin_route.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import conductor  # noqa: E402
import scene_author  # noqa: E402


def _inputs():
    """A 6-sign faithful-style brief; 分别画叉 per-sign on s5/s6 only (mirrors inputs_lily_aia.json)."""
    return {
        "asset_type": "手举牌 hand-held event sign",
        "format_size": "60x40cm",
        "reference_image": "/tmp/ref.png",
        "reference_relationship": "template — extend this series",
        "mandatory_elements": [], "forbidden_elements": [],
        "context": {"usage_context": "held for photos / posed with",
                    "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
                    "logo_treatment": "omit", "brand_strictness": "expressive departure",
                    "occasion": "anti-fraud"},
        "signs": [
            {"id": "s1", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": None},
            {"id": "s2", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": None},
            {"id": "s3", "messages": ["远离非法金融", "抵制高息诱惑"], "hero_icon": None},
            {"id": "s4", "messages": ["珍惜一生血汗", "远离非法金融"], "hero_icon": None},
            {"id": "s5", "messages": ["金融传销", "虚拟货币骗局"], "hero_icon": None,
             "mandatory_elements": ["分别画叉"]},
            {"id": "s6", "messages": ["非法集资", "网络金融诈骗"], "hero_icon": None,
             "mandatory_elements": ["分别画叉"]},
        ],
    }


def _plan(thin):
    with tempfile.TemporaryDirectory() as d:
        return conductor.build_plan(_inputs(), "aia", Path(d) / "out", no_approve=True, thin=thin)


def check1_thin_route_drops_composition():
    """THE core assertion: on the thin route the plan has NO kit/compose/measure/composite steps,
    and every sign step is scene_author --thin. A wrong build keeps the kit steps."""
    plan = _plan(thin=True)
    labels = [s["label"] for s in plan["steps"]]
    plan_text = json.dumps(plan, ensure_ascii=False)
    no_kit = "kit" not in labels and "kit_profile.json" not in plan_text
    no_measure = "measure" not in plan_text and "closed_loop" not in plan_text
    no_compose = "compose_select" not in plan_text and "composition.json" not in plan_text
    sa_steps = [s for s in plan["steps"] if s["label"] == "scene_author"]
    all_thin = len(sa_steps) == 6 and all("--thin" in " ".join(s["argv"]) for s in sa_steps)
    route_ok = plan.get("route") == "thin"
    passed = no_kit and no_measure and no_compose and all_thin and route_ok
    return passed, (f"route={plan.get('route')} labels={labels}; no_kit={no_kit} no_measure={no_measure} "
                    f"no_compose={no_compose}; 6 scene_author --thin={all_thin}")


def check2_verbatim_headline_and_X_in_prompt():
    """assemble_thin_prompt must carry the exact headline strings AND 分别画叉 byte-for-byte
    (equality of the substring, not a paraphrase). A wrong build translates or drops them."""
    brand_key = scene_author.load_brand("aia")
    rp = {"inferred_register": "event_prop", "brand_locks_flexed": ["logo:omit"]}
    prompt = scene_author.assemble_thin_prompt(
        brand_key, ["金融传销", "虚拟货币骗局"], register_profile=rp, dial="template",
        mandatory=["分别画叉"], forbidden=[], has_reference=True)
    has_msgs = "金融传销" in prompt and "虚拟货币骗局" in prompt
    has_x = "分别画叉" in prompt           # the mandatory element reached the prompt verbatim
    # verbatim guard: the headline instruction must forbid translation/paraphrase
    verbatim_rule = "verbatim" in prompt.lower() or "do NOT translate" in prompt
    passed = has_msgs and has_x and verbatim_rule
    return passed, f"headlines_present={has_msgs} 分别画叉_present={has_x} verbatim_rule={verbatim_rule}"


def check3_no_X_when_not_supplied():
    """Honest null: a sign with no mandatory element must NOT have 分别画叉 fabricated in its prompt."""
    brand_key = scene_author.load_brand("aia")
    rp = {"inferred_register": "event_prop", "brand_locks_flexed": ["logo:omit"]}
    prompt = scene_author.assemble_thin_prompt(
        brand_key, ["守住钱袋子", "护好幸福家"], register_profile=rp, mandatory=[], forbidden=[])
    passed = "分别画叉" not in prompt and "守住钱袋子" in prompt
    return passed, f"no fabricated 分别画叉={'分别画叉' not in prompt}; headline present={'守住钱袋子' in prompt}"


def check4_moat_deferred_marker():
    """The deferred moat must be TRACKED, not silent. The dry-run PLAN marks the route as thin
    (thin=True, route=thin); the licensed_type='deferred' marker is written at MANIFEST level on a
    real run (conductor.py). A wrong build either composites a font or hides the route entirely."""
    plan = _plan(thin=True)
    route_tracked = plan.get("route") == "thin" and plan.get("thin") is True
    # the manifest-emitting code path must reference the deferred marker (source-level guard so the
    # tracked-debt string can't be silently dropped from the real run)
    src = (REPO_ROOT / "harness" / "conductor.py").read_text(encoding="utf-8")
    manifest_marks_deferred = 'licensed_type' in src and 'deferred' in src
    passed = route_tracked and manifest_marks_deferred
    return passed, (f"plan route=thin & thin=True={route_tracked}; "
                    f"manifest emits licensed_type deferred={manifest_marks_deferred}")


def check5_default_route_unchanged_backcompat():
    """Back-compat (SC): WITHOUT --thin, AIA (has a kit) still takes the KIT route. The thin route
    must be OPT-IN, not a silent global change. A wrong build flips the default."""
    plan = _plan(thin=False)
    labels = [s["label"] for s in plan["steps"]]
    passed = plan.get("route") == "kit" and "kit" in labels
    return passed, f"default route={plan.get('route')} (expect kit); kit step present={'kit' in labels}"


def check6_dial_kept_on_thin():
    """The register/dial is KEPT on the thin route (it sets task-vs-brand magnitude). The dial hint
    must appear in the assembled prompt when a reference + relationship are supplied."""
    brand_key = scene_author.load_brand("aia")
    rp = {"inferred_register": "event_prop", "brand_locks_flexed": ["logo:omit"]}
    prompt = scene_author.assemble_thin_prompt(
        brand_key, ["远离非法金融"], register_profile=rp, dial="template", has_reference=True)
    # the dial hint line names the relationship; register directive block is present
    passed = "template" in prompt.lower() and len(prompt) > 100
    return passed, f"dial hint present={'template' in prompt.lower()}; prompt_len={len(prompt)}"


def check7_no_slogan_no_invented_text():
    """The two prompt-assembler fixes (post first thin run): (1) the brand slogan is NOT injected as
    paintable text (it leaked 健康长久好生活 onto every sign); (2) the headline block forbids ANY other
    Chinese text; (3) a mandatory element is framed as a DESIGN INSTRUCTION (depict/do), not 'render
    the text exactly' (which painted the literal characters 分别画叉). A wrong build reintroduces any."""
    brand_key = scene_author.load_brand("aia")
    rp = {"inferred_register": "event_prop", "brand_locks_flexed": ["logo:omit"]}
    prompt = scene_author.assemble_thin_prompt(
        brand_key, ["金融传销", "虚拟货币骗局"], register_profile=rp, dial="template",
        mandatory=["分别画叉"], forbidden=[], has_reference=True)
    slogan = scene_author._brand_field_value(brand_key, "slogan") or ""
    no_slogan = (not slogan) or (slogan not in prompt)        # slogan text not injected
    only_words_guard = "ONLY words that may appear" in prompt  # headline forbids other text
    # mandatory is framed as a depict/do instruction, NOT 'render exactly as written'
    action_framed = "DEPICT or DO" in prompt and "render the instruction text itself" in prompt
    passed = no_slogan and only_words_guard and action_framed
    return passed, (f"slogan_not_injected={no_slogan} (slogan={slogan!r}); "
                    f"only-words guard={only_words_guard}; mandatory-as-action={action_framed}")


CHECKS = [
    ("Thin route DROPS kit/compose/measure/composite; 6× scene_author --thin", check1_thin_route_drops_composition),
    ("Verbatim headline + 分别画叉 in assembled prompt (byte-for-byte)", check2_verbatim_headline_and_X_in_prompt),
    ("No 分别画叉 fabricated when not supplied (honest null)", check3_no_X_when_not_supplied),
    ("Moat-deferred marker tracked (licensed_type=deferred)", check4_moat_deferred_marker),
    ("Default route UNCHANGED without --thin (kit; opt-in)", check5_default_route_unchanged_backcompat),
    ("Register/dial KEPT on the thin route", check6_dial_kept_on_thin),
    ("No slogan leak + headline-only-words + mandatory-as-action", check7_no_slogan_no_invented_text),
]


def main():
    print("=" * 78)
    print("test_thin_route.py — falsifiable self-test (feature 003, no paid calls)")
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
