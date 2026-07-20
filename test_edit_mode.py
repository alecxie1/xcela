#!/usr/bin/env python3
"""test_edit_mode.py - falsifiable self-test for feature 023 (edit mode 改图 + brand
palette management). NO paid calls: the edit derive leg is deterministic by construction
(no model calls), so even the end-to-end checks are free.

Run:  .venv/bin/python test_edit_mode.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "frontend"))
sys.path.insert(0, str(REPO / "harness"))

import inputs_writer  # noqa: E402


def _tmpdir():
    return Path(tempfile.mkdtemp(prefix="t023_"))


def _png(path: Path, w=8, h=8, color=(255, 0, 0)):
    """A tiny real PNG on disk (PIL: the venv the suite runs under has it)."""
    from PIL import Image
    img = Image.new("RGB", (w, h), color)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)


def check1_writer_edit_contract():
    """023 T001: to_edit_inputs by value - mode/base/instruction verbatim, empty-messages
    single sign, region normalized floats; fail-loud on missing base / blank instruction /
    malformed or out-of-bounds region."""
    fs = {"mode": "edit", "base_image": "/tmp/base.png",
          "edit_instruction": "把左下角的牛肉粉换成酸汤粉  ",
          "edit_region": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4},
          "product_images": ["/tmp/p1.jpg"]}
    out = inputs_writer.to_edit_inputs(fs)
    a = (out["mode"] == "edit" and out["base_image"] == "/tmp/base.png"
         and out["edit_instruction"] == "把左下角的牛肉粉换成酸汤粉"
         and out["signs"] == [{"id": "s1", "messages": []}]
         and out["edit_region"] == {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
         and out["product_images"] == ["/tmp/p1.jpg"])
    fails = []
    for bad in ({"mode": "edit", "edit_instruction": "x"},                       # no base
                {"mode": "edit", "base_image": "b.png"},                          # no instruction
                {"mode": "edit", "base_image": "b.png", "edit_instruction": "x",
                 "edit_region": {"x": 0.9, "y": 0, "w": 0.5, "h": 0.5}},          # x+w > 1
                {"mode": "edit", "base_image": "b.png", "edit_instruction": "x",
                 "edit_region": {"x": 0, "y": 0, "w": 0}}):                       # malformed
        try:
            inputs_writer.to_edit_inputs(bad)
            fails.append(bad)
        except ValueError:
            pass
    b = not fails
    # No-region edit carries NO edit_region key (honest null, full-canvas).
    c = "edit_region" not in inputs_writer.to_edit_inputs(
        {"mode": "edit", "base_image": "b.png", "edit_instruction": "x"})
    ok = a and b and c
    return ok, f"verbatim-contract={a}; fail-loud-4-cases={b}; no-region-no-key={c}"


def check2_design_lane_no_mode_key():
    """023 THE pin: to_inputs (the design lane) NEVER emits a `mode` key, and write_inputs
    dispatches on form_state['mode'] - an untouched design form writes byte-identical
    pre-023 JSON."""
    fs = {"reference_image": "/tmp/ref.png", "messages": ["守住钱袋子"]}
    design = inputs_writer.to_inputs(fs)
    a = "mode" not in design and "base_image" not in design and "edit_instruction" not in design
    d = _tmpdir()
    p1 = inputs_writer.write_inputs(fs, d / "design.json")
    j1 = json.loads(p1.read_text(encoding="utf-8"))
    b = "mode" not in j1 and j1["signs"][0]["messages"] == ["守住钱袋子"]
    p2 = inputs_writer.write_inputs({"mode": "edit", "base_image": "b.png",
                                     "edit_instruction": "换碗"}, d / "edit.json")
    j2 = json.loads(p2.read_text(encoding="utf-8"))
    c = j2["mode"] == "edit" and j2["edit_instruction"] == "换碗"
    ok = a and b and c
    return ok, f"design-no-mode-key={a}; write-dispatch-design={b}; write-dispatch-edit={c}"


def check3_validate_inputs_edit_branch():
    """023 T001: conductor.validate_inputs - empty messages LEGAL iff mode=edit; the exact
    design-lane refusal string preserved; edit's own required fields fail loud (missing
    base on disk, blank instruction, bad region)."""
    import conductor
    d = _tmpdir()
    base = _png(d / "base.png")
    good = {"mode": "edit", "base_image": base, "edit_instruction": "换碗",
            "signs": [{"id": "s1", "messages": []}]}
    v = conductor.validate_inputs(json.loads(json.dumps(good)))
    a = v["signs"][0]["messages"] == []
    # The design lane keeps the EXACT error (the playbook's 对照表 quotes it).
    try:
        conductor.validate_inputs({"context": {}, "signs": [{"id": "s1", "messages": []}]})
        b = False
    except SystemExit as exc:
        b = str(exc) == "ERROR: sign 's1' has no messages."
    errs = []
    for bad, frag in ((dict(good, base_image=str(d / "missing.png")), "not found on disk"),
                      (dict(good, edit_instruction="  "), "edit_instruction"),
                      (dict(good, edit_region={"x": 0.8, "y": 0, "w": 0.5, "h": 0.5}),
                       "out of bounds")):
        try:
            conductor.validate_inputs(json.loads(json.dumps(bad)))
            errs.append(frag)
        except SystemExit as exc:
            if frag not in str(exc):
                errs.append(f"{frag}: wrong message {exc}")
    c = not errs
    # Edit mode needs no context (the register engine never sees edit runs).
    e = "context" not in v
    ok = a and b and c and e
    return ok, f"empty-msgs-legal={a}; design-error-verbatim={b}; edit-fail-loud={c or errs}; no-context-needed={e}"


def check4_compose_edit_prompt():
    """023 T002: compose_edit_prompt by value - instruction VERBATIM exactly once, the
    PRESERVE clause always, REGION iff a region is set, PRODUCT FIDELITY iff products,
    OPERATOR NOTE iff style_notes; never any authored scene/message vocabulary."""
    import edit_author as ea
    instr = "把左下角的牛肉粉换成酸汤粉"
    bare = ea.compose_edit_prompt(instr)
    region = {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
    full = ea.compose_edit_prompt(instr, region=region, has_products=True, style_notes="碗小一点")
    a = bare.count(instr) == 1 and full.count(instr) == 1
    b = "PRESERVE:" in bare and "every character" in bare
    c = ("REGION" not in bare and "REGION: alter ONLY" in full
         and "x=0.1000" in full and "width=0.3000" in full)
    d = "PRODUCT FIDELITY" not in bare and "PRODUCT FIDELITY" in full
    e = "OPERATOR NOTE" not in bare and "OPERATOR NOTE (binding):\n碗小一点" in full
    f = all(t not in bare + full for t in ("SCENE / SUBJECT", "register", "tier-3"))
    # Determinism (the free-derive + verify-prompt drift contract rests on it):
    g = full == ea.compose_edit_prompt(instr, region=region, has_products=True,
                                       style_notes="碗小一点")
    ok = a and b and c and d and e and f and g
    return ok, (f"verbatim-once={a}; preserve={b}; region-iff={c}; products-iff={d}; "
                f"note-iff={e}; no-scene-vocab={f}; deterministic={g}")


def check5_mask_and_size():
    """023 T002: build_region_mask geometry by value (transparent INSIDE, opaque outside,
    base dimensions) + edit_size rides the existing aspect-preserving map."""
    import edit_author as ea
    from PIL import Image
    d = _tmpdir()
    base = _png(d / "base.png", w=100, h=80)
    geom = ea.build_region_mask(base, {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5}, d / "m.png")
    a = geom == {"size": [100, 80], "region_px": [25, 20, 75, 60]}
    with Image.open(d / "m.png") as m:
        b = (m.size == (100, 80)
             and m.getpixel((50, 40))[3] == 0      # inside: transparent (editable)
             and m.getpixel((5, 5))[3] == 255      # outside: opaque (preserved)
             and m.getpixel((80, 70))[3] == 255)
    base2 = _png(d / "b1536.png", w=1536, h=1024)
    c = ea.edit_size(base2) == "1536x1024"
    ok = a and b and c
    return ok, f"geometry-by-value={a}; mask-pixels={b}; size-via-resolve_size={c}"


def check6_outside_region_stats():
    """023 T002 (SC-003's stat): an inside-region-only change measures mad == 0.0 outside
    (within=True); an everywhere change measures mad > threshold (within=False). Computed
    from artifacts on disk, no judgment."""
    import edit_author as ea
    from PIL import Image
    d = _tmpdir()
    region = {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5}
    base = _png(d / "base.png", w=100, h=80, color=(200, 30, 30))
    inside_only = Image.open(base).copy()
    inside_only.paste(Image.new("RGB", (50, 40), (0, 0, 255)), (25, 20))
    inside_only.save(d / "inside.png")
    s1 = ea.outside_region_stats(base, d / "inside.png", region)
    a = s1["outside_region_mad"] == 0.0 and s1["within"] is True
    Image.new("RGB", (100, 80), (30, 200, 30)).save(d / "全变.png")
    s2 = ea.outside_region_stats(base, str(d / "全变.png"), region)
    b = s2["outside_region_mad"] > s2["threshold"] and s2["within"] is False
    c = s1["threshold"] == ea.OUTSIDE_REGION_MAD_THRESHOLD
    ok = a and b and c
    return ok, f"inside-only-zero={a}; everywhere-fails={b}; threshold-named={c}"


def check7_generate_mask_param_additive():
    """023 T002: generate_variant's mask_path defaults to None (pre-023 calls byte-
    identical) and the mask kwarg is guarded - a build that always sends mask fails."""
    import inspect
    import generate
    sig = inspect.signature(generate.generate_variant)
    a = sig.parameters["mask_path"].default is None
    src = inspect.getsource(generate.generate_variant)
    b = 'kwargs = {"mask": mask} if mask else {}' in src
    c = 'if mask_path:' in src  # the manifest key is additive too
    ok = a and b and c
    return ok, f"default-None={a}; guarded-kwarg={b}; additive-manifest={c}"


CHECKS = [
    ("023 T001: to_edit_inputs contract by value", check1_writer_edit_contract),
    ("023 T001: design lane emits no mode key (THE pin) + write dispatch", check2_design_lane_no_mode_key),
    ("023 T001: validate_inputs edit branch + preserved design refusal", check3_validate_inputs_edit_branch),
    ("023 T002: compose_edit_prompt verbatim + section-iff rules", check4_compose_edit_prompt),
    ("023 T002: region mask geometry + size authority", check5_mask_and_size),
    ("023 T002: outside-region stats by value", check6_outside_region_stats),
    ("023 T002: generate_variant mask param additive pin", check7_generate_mask_param_additive),
]


def main():
    print("=" * 78)
    print("test_edit_mode.py - falsifiable self-test (023, no paid calls)")
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
