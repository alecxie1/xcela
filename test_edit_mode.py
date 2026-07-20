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


CHECKS = [
    ("023 T001: to_edit_inputs contract by value", check1_writer_edit_contract),
    ("023 T001: design lane emits no mode key (THE pin) + write dispatch", check2_design_lane_no_mode_key),
    ("023 T001: validate_inputs edit branch + preserved design refusal", check3_validate_inputs_edit_branch),
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
