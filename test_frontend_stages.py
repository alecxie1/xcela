#!/usr/bin/env python3
"""test_frontend_stages.py — falsifiable self-test for the run-dir stage reader (004, US2/US3).

No paid calls. Over a SYNTHETIC run dir, asserts `frontend/run_view.run_view` surfaces stages
PROGRESSIVELY (register + prompt present while the image is absent), reports a missing artifact as
present:false + the manifest note (honest null, never fabricated), reads the artifact PATHS (SC-003),
does not crash on a nonexistent dir, and reads two distinct attempt dirs independently (US3 compare).

Run:  .venv/bin/python test_frontend_stages.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "frontend"))
import run_view  # noqa: E402


def _make_run(d: Path, with_image=False, note="thin route: honest-null blank avoided"):
    (d / "inputs.json").write_text(json.dumps({"asset_type": "x", "signs": [{"id": "s1"}]}),
                                   encoding="utf-8")
    (d / "register_profile.json").write_text(json.dumps(
        {"inferred_register": "event_prop", "formality": 5, "playfulness": 7,
         "brand_anchors_held": ["primary_color"], "brand_locks_flexed": ["logo:omit"]}),
        encoding="utf-8")
    s1 = d / "sign_s1"
    s1.mkdir(parents=True, exist_ok=True)
    (s1 / "final_prompt.txt").write_text("ONE die-cut sign ... 分别画叉 ...", encoding="utf-8")
    if with_image:
        (s1 / "generated.png").write_bytes(b"\x89PNG\r\n")
    (d / "conductor_manifest.json").write_text(json.dumps({"brand": "aia", "notes": [note]}),
                                               encoding="utf-8")


def check1_progressive_dial_prompt_before_image():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d, with_image=False)
        v = run_view.run_view(d)
    passed = (v["register"]["present"] and v["prompt"]["present"]
              and not v["image"]["present"])
    return passed, (f"register present={v['register']['present']}, prompt present="
                    f"{v['prompt']['present']}, image present={v['image']['present']} (want F)")


def check2_missing_artifact_honest_null():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d, with_image=False, note="sign s1: needs_review")
        v = run_view.run_view(d)
    img = v["image"]
    passed = (img["present"] is False and img["content"] is None
              and img.get("note") and "needs_review" in img["note"])
    return passed, f"image absent={not img['present']}, content={img['content']!r}, note={img.get('note')!r}"


def check3_reads_artifact_paths():
    # The reader's content must come from the files (SC-003): change the file, see the change.
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d, with_image=True)
        v = run_view.run_view(d)
    reg_ok = (v["register"]["content"] or {}).get("inferred_register") == "event_prop"
    prompt_ok = "分别画叉" in (v["prompt"]["content"] or "")
    img_ok = v["image"]["present"] and "generated.png" in str(v["image"]["content"])
    passed = reg_ok and prompt_ok and img_ok
    return passed, f"register from file={reg_ok}, prompt from file={prompt_ok}, image path={img_ok}"


def check4_nonexistent_dir_no_crash():
    v = run_view.run_view(Path("/tmp/does_not_exist_run_xyz"))
    passed = (not v["register"]["present"] and not v["prompt"]["present"]
              and not v["image"]["present"])
    return passed, "nonexistent dir -> all stages absent, no crash"


def check5_two_attempts_independent():
    # US3: two distinct attempt dirs read independently (prior attempt preserved + comparable).
    with tempfile.TemporaryDirectory() as base:
        base = Path(base)
        a, b = base / "run_aia_1", base / "run_aia_2"
        a.mkdir(); b.mkdir()
        _make_run(a, with_image=True)
        _make_run(b, with_image=False)
        va, vb = run_view.run_view(a), run_view.run_view(b)
    passed = va["image"]["present"] and not vb["image"]["present"]
    return passed, f"attempt A image={va['image']['present']}, attempt B image={vb['image']['present']} (independent)"


CHECKS = [
    ("Progressive: dial + prompt present before image", check1_progressive_dial_prompt_before_image),
    ("Missing artifact -> present:false + manifest note (honest null)", check2_missing_artifact_honest_null),
    ("Reads artifact paths / content from files (SC-003)", check3_reads_artifact_paths),
    ("Nonexistent dir -> all absent, no crash", check4_nonexistent_dir_no_crash),
    ("Two attempt dirs read independently (US3 compare)", check5_two_attempts_independent),
]


def main():
    print("=" * 78)
    print("test_frontend_stages.py — falsifiable self-test (US2/US3, no paid calls)")
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
