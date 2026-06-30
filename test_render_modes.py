#!/usr/bin/env python3
"""test_render_modes.py - falsifiable self-test for render modes (feature 009).

No paid calls. Asserts VALUES a wrong build cannot satisfy (constitution §III), never generates. SC-007
(does the output actually LOOK photographic) is the LOAD-BEARING human eye-gate, NOT here. Covers:
  1. ASSET_PROFILES defines both dialects (sanity).
  2. US1: photo dialect - photographic language, NO flat-vector negatives, text guards kept.
  3. US2: flat marketing opener drops "hand-held event sign" (rectangular); flat event_prop byte-unchanged.
  4. US3: normalize_render_style mapping + fallback; build_plan thin argv carries the brief's profile;
     inputs_writer round-trips render_style; the served page has the control.

Run:  .venv/bin/python test_render_modes.py
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "frontend"))
import scene_author  # noqa: E402
import conductor  # noqa: E402
import inputs_writer  # noqa: E402

EVENT_PROP = {"inferred_register": "event_prop"}
MARKETING = {"inferred_register": "marketing"}


def _key():
    return {"fields": {"brand_name_cn": {"value": "测试"}, "brand_name_en": {"value": "Test"},
                       "colors": {"items": [{"name_cn": "红", "name_en": "Red",
                                             "printed_html": "D81E05", "role": "primary"}]}}}


def _inputs(render_style=None):
    d = {"asset_type": "poster", "format_size": "60x40cm", "reference_image": "/tmp/ref.png",
         "reference_relationship": "match style", "mandatory_elements": [], "forbidden_elements": [],
         "context": {"usage_context": "wall-posted", "vibe": {"formality": 2, "playfulness": 7, "warmth": 7},
                     "logo_treatment": "omit", "brand_strictness": "brand + accents", "occasion": "x"},
         "signs": [{"id": "s1", "messages": ["守住钱袋子"], "hero_icon": None}]}
    if render_style is not None:
        d["render_style"] = render_style
    return d


def _thin_profiles(inputs):
    with tempfile.TemporaryDirectory() as d:
        plan = conductor.build_plan(inputs, "aia", Path(d) / "out", no_approve=True, thin=True)
    sa = [s for s in plan["steps"] if s["label"] == "scene_author"]
    out = []
    for s in sa:
        a = s["argv"]
        out.append(a[a.index("--asset-profile") + 1] if "--asset-profile" in a else None)
    return out


def check1_profiles_exist():
    g = scene_author.ASSET_PROFILES
    ok = "photo" in g and "flat_graphic" in g
    return ok, f"ASSET_PROFILES keys={sorted(g)}"


def check2_photo_dialect():
    prompt = scene_author.assemble_thin_prompt(_key(), ["守住钱袋子"], register_profile=MARKETING,
                                               asset_profile="photo", has_reference=True)
    photo = "PHOTOGRAPHIC" in prompt and "photographic realism" in prompt.lower()
    no_flat = "FLAT VECTOR" not in prompt and "no photographic shading" not in prompt
    guards = "no extra Chinese" in prompt and "no gibberish" in prompt and "守住钱袋子" in prompt
    # photo + event_prop opener also works (photographic + prop framing), no error
    pe = scene_author.assemble_thin_prompt(_key(), ["x"], register_profile=EVENT_PROP,
                                           asset_profile="photo", has_reference=True)
    prop = "PHOTOGRAPHIC" in pe and "prop" in pe.lower()
    passed = photo and no_flat and guards and prop
    return passed, f"photo_lang={photo}; no_flat_leak={no_flat}; text_guards+headline={guards}; photo_event_prop={prop}"


def check3_flat_framing_register_aware():
    mk = scene_author.assemble_thin_prompt(_key(), ["守住钱袋子"], register_profile=MARKETING,
                                           asset_profile="flat_graphic", has_reference=True)
    # flat marketing: drops "hand-held event sign" AND asserts PRESENCE of rectangular-poster language
    # (a pure-absence check is a no-op gate, §III: the event_prop opener says "hand-held event photo-prop
    # sign", a superstring, so absence of the exact substring alone does not distinguish the rewrite).
    mk_ok = ("hand-held event sign" not in mk) and ("rectangular" in mk) and ("poster" in mk or "flyer" in mk)
    ep = scene_author.assemble_thin_prompt(_key(), ["守住钱袋子"], register_profile=EVENT_PROP,
                                           asset_profile="flat_graphic", has_reference=True)
    ep_ok = ("hand-held event photo-prop sign" in ep and "die-cut" in ep
             and "no photographic shading" in ep)
    return mk_ok and ep_ok, f"flat_marketing_rectangular={mk_ok}; flat_event_prop_unchanged={ep_ok}"


def check4_plumbing():
    n = conductor.normalize_render_style
    map_ok = (n("photographic") == "photo" and n("flat vector") == "flat_graphic"
              and n("") == "flat_graphic" and n("zzz") == "flat_graphic" and n(None) == "flat_graphic")
    photo_argv = _thin_profiles(_inputs("photographic"))
    flat_argv = _thin_profiles(_inputs())  # no render_style -> default flat
    argv_ok = bool(photo_argv) and all(p == "photo" for p in photo_argv) \
        and bool(flat_argv) and all(p == "flat_graphic" for p in flat_argv)
    iw = inputs_writer.to_inputs({"reference_image": "/tmp/r.png", "render_style": "photographic",
                                  "messages": ["m"]})
    iw_default = inputs_writer.to_inputs({"reference_image": "/tmp/r.png", "messages": ["m"]})
    iw_ok = iw["render_style"] == "photographic" and iw_default["render_style"] == "flat vector"
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    ctl_ok = 'id="render_style"' in html and 'value="photographic"' in html
    passed = map_ok and argv_ok and iw_ok and ctl_ok
    return passed, (f"map={map_ok}; thin_argv photo={photo_argv} flat={flat_argv} ({argv_ok}); "
                    f"inputs_roundtrip={iw_ok}; control={ctl_ok}")


CHECKS = [
    ("ASSET_PROFILES defines both dialects", check1_profiles_exist),
    ("US1 photo dialect (photographic, no flat negatives, text guards kept)", check2_photo_dialect),
    ("US2 flat framing register-aware (marketing != event sign; event_prop unchanged)", check3_flat_framing_register_aware),
    ("US3 plumbing (mapping + thin argv carries the brief profile + inputs + control)", check4_plumbing),
]


def main():
    print("=" * 78)
    print("test_render_modes.py - falsifiable self-test (009, no paid calls)")
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
