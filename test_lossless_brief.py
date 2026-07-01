#!/usr/bin/env python3
"""test_lossless_brief.py - falsifiable self-test for feature 012 (lossless brief).

No paid calls: pure imports (scene_author, conductor, inputs_writer) + grep-gates on the served
form HTML (the WEAKEST gate, declared per the 010 precedent). Contract rows refer to
specs/012-lossless-brief/contracts/lossless_brief_contract.md.

Run:  .venv/bin/python test_lossless_brief.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "frontend"))
import scene_author  # noqa: E402
import conductor  # noqa: E402
import inputs_writer  # noqa: E402

# The exact T001 fixture (reused verbatim): minimal key, one message, marketing register,
# photo dialect, reference fed, no notes.
KEY = {"fields": {"brand_name_cn": {"value": "测试"}, "brand_name_en": {"value": "Test"},
                  "colors": {"items": [{"name_cn": "红", "name_en": "Red",
                                        "printed_html": "D81E05", "role": "primary"}]}}}
MARKETING = {"inferred_register": "marketing"}

# T001 pre-feature baseline: assemble_thin_prompt output captured on the UNMODIFIED engine for
# the fixture above. FR-003: with asset_type and occasion both absent the prompt must stay
# byte-identical. (Injected as repr; em-dashes inside are pre-existing engine text.)
EXPECTED_PREFEATURE_PROMPT = 'A PHOTOGRAPHIC marketing poster for 测试 (Test): a real photographed scene composed as a full rectangular poster. Photographic realism, natural lighting, depth of field, advertising photography quality. NOT a flat illustration, NOT a cartoon.\n\nHEADLINE TEXT (render these Chinese characters EXACTLY as written — copy them verbatim, do NOT translate, paraphrase, transliterate, or alter a single character; render crisply and perfectly legible as the dominant element of the sign). These are the ONLY words that may appear on the sign — do NOT add, invent, or render any other Chinese text, tagline, slogan, caption, label, or watermark anywhere:\n  • "新品上市"\n\nREGISTER DIRECTIVE (AUTHORITATIVE — this OVERRIDES the corporate brand-studio defaults\nwherever they conflict; you have explicit permission AND instruction to depart from them\nalong the flexed dimensions below):\n  Register: marketing — \n  HELD brand anchors (never flex):\n  FLEXED locks (depart from corporate defaults here — mandatory, not optional):\n\nBRAND LOCK COLORS (these are the brand\'s colors and the design must read as this brand\'s; each color\'s role tells you how to use it, as guidance not a rigid rule):\n  红/Red: #D81E05 [primary] - the dominant brand color: use it for the largest, most prominent areas as the main anchor of the design.\nLOGO: use the supplied brand logo faithfully — place it cleanly; do not redraw or distort it.\n\nA reference image is provided as a visual exemplar — use it as designed-in guidance for style and composition (reference + prompt), not to copy verbatim.\nNEGATIVES: no gibberish or garbled text, no extra Chinese text beyond the headline above, no tagline, no watermark.'


def _assemble(**kw):
    return scene_author.assemble_thin_prompt(KEY, ["新品上市"], register_profile=MARKETING,
                                             asset_profile="photo", has_reference=True, **kw)


def check1_scene_section():
    """T002 contract rows 1-3: values verbatim + framing; no empty scaffolding; blank case
    byte-identical to the pre-feature baseline."""
    at = "marketing post for social media, new fruit tea line"
    oc = "【新品上線】現開西瓜"
    p = _assemble(asset_type=at, occasion=oc)
    row1 = (f"  Asset: {at}" in p and f"  Occasion: {oc}" in p
            and "SCENE / SUBJECT (compositional context ONLY, not text" in p
            and "no words from this section may be painted" in p
            and "the ONLY words that may appear" in p)  # HEADLINE guard untouched
    # row 2: asset only, no empty Occasion scaffolding
    p2 = _assemble(asset_type=at)
    row2 = f"  Asset: {at}" in p2 and "Occasion:" not in p2
    # row 3: both blank (omitted AND explicit empties) => byte-identical to pre-feature
    row3 = (_assemble() == EXPECTED_PREFEATURE_PROMPT
            and _assemble(asset_type="", occasion="  ") == EXPECTED_PREFEATURE_PROMPT)
    passed = row1 and row2 and row3
    return passed, f"verbatim+framing={row1}; no_empty_scaffolding={row2}; blank_byte_identical={row3}"


def _inputs(asset_type=None, occasion=None):
    d = {"asset_type": asset_type or "", "format_size": "60x40cm",
         "reference_image": "/tmp/ref.png", "reference_relationship": "extend",
         "render_style": "photographic", "mandatory_elements": [], "forbidden_elements": [],
         "context": {"usage_context": "wall-posted", "occasion": occasion or "",
                     "vibe": {"formality": 2, "playfulness": 7},
                     "logo_treatment": "omit", "brand_strictness": "brand + accents"},
         "signs": [{"id": "s1", "messages": ["新品上市"], "hero_icon": None}]}
    return d


def _flag_vals(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag]


def check2_conductor_threading():
    """T003 contract row 4: --asset-type/--occasion in the scene_author argv at BOTH call sites
    (build_plan AND the stubbed execute), exactly when non-empty. A plan-only build (the 009
    drift) fails the execute half; a build that threads empties fails the omission half."""
    import contextlib
    import io
    import json as _json
    import tempfile

    AT, OC = "social media post, fruit tea", "new watermelon line launch"

    def plan_argvs(inputs):
        with tempfile.TemporaryDirectory() as d:
            plan = conductor.build_plan(inputs, "aia", Path(d) / "o", no_approve=True, thin=True)
        return [s["argv"] for s in plan["steps"] if s["label"] == "scene_author"]

    def exec_argvs(inputs):
        captured = []

        def stub(step):
            captured.append(step)
            return {"label": step["label"], "phase": step["phase"], "ok": False, "returncode": 1}

        orig = conductor.run_step
        conductor.run_step = stub
        try:
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "run"
                out.mkdir()
                ip = Path(d) / "inputs.json"
                ip.write_text(_json.dumps(inputs), encoding="utf-8")
                plan = conductor.build_plan(inputs, "aia", out, no_approve=True, thin=True)
                with contextlib.redirect_stdout(io.StringIO()):
                    conductor.execute(inputs, "aia", out, ip, True, plan, thin=True)
        finally:
            conductor.run_step = orig
        return [s["argv"] for s in captured if s["label"] == "scene_author"]

    full = _inputs(AT, OC)
    blank = _inputs()
    ok_parts = []
    for name, get in (("plan", plan_argvs), ("execute", exec_argvs)):
        with_argvs, blank_argvs = get(full), get(blank)
        carried = (bool(with_argvs)
                   and all(_flag_vals(a, "--asset-type") == [AT] for a in with_argvs)
                   and all(_flag_vals(a, "--occasion") == [OC] for a in with_argvs))
        omitted = (bool(blank_argvs)
                   and all("--asset-type" not in a and "--occasion" not in a for a in blank_argvs))
        ok_parts.append((name, carried and omitted, f"{name}: carried={carried} omitted={omitted}"))
    passed = all(ok for _, ok, _ in ok_parts)
    return passed, "; ".join(msg for _, _, msg in ok_parts)


CHECKS = [
    ("US1 scene/subject section (verbatim, context-not-text, blank byte-identical)",
     check1_scene_section),
    ("US1 conductor threads asset_type+occasion at BOTH call sites (009 drift guard)",
     check2_conductor_threading),
]


def main():
    print("=" * 78)
    print("test_lossless_brief.py - falsifiable self-test (012, no paid calls)")
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
