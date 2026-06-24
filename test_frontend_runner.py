#!/usr/bin/env python3
"""test_frontend_runner.py — falsifiable self-test for the run trigger argv builder (004, US2/US3).

No paid calls (argv builder is pure; nothing is executed). Asserts the UI shells out to the EXISTING
conductor with the gate off and a new run dir per call: `--thin --no-approve --inputs`, never `--out`;
a nudge adds `--style-notes <note>` verbatim (the US3 trigger), and approve produces no extra call.

Run:  .venv/bin/python test_frontend_runner.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "frontend"))
import runner  # noqa: E402


def _val(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def check1_first_run_argv():
    argv = runner.build_conductor_argv("/tmp/in.json", "aia")
    passed = ("--thin" in argv and "--no-approve" in argv
              and _val(argv, "--inputs") == "/tmp/in.json"
              and _val(argv, "--brand") == "aia"
              and "--out" not in argv and "--style-notes" not in argv
              and "harness/conductor.py" in " ".join(argv))
    return passed, f"argv={argv[1:]}"


def check2_nudge_adds_style_notes_new_dir():
    argv = runner.build_conductor_argv("/tmp/in.json", "aia", style_notes="make it bolder")
    has_note = _val(argv, "--style-notes") == "make it bolder"
    no_out = "--out" not in argv   # no --out => conductor makes a NEW run dir per attempt (clarified)
    still_thin = "--thin" in argv and "--no-approve" in argv
    passed = has_note and no_out and still_thin
    return passed, f"--style-notes={_val(argv, '--style-notes')!r}; no --out={no_out}; thin+no-approve={still_thin}"


def check3_empty_note_omits_flag():
    # Approve / no-note path: an empty or None note must NOT add --style-notes (no fabricated nudge).
    a = runner.build_conductor_argv("/tmp/in.json", "aia", style_notes=None)
    b = runner.build_conductor_argv("/tmp/in.json", "aia", style_notes="")
    passed = "--style-notes" not in a and "--style-notes" not in b
    return passed, f"None -> no flag={'--style-notes' not in a}; '' -> no flag={'--style-notes' not in b}"


CHECKS = [
    ("First-run argv: --thin --no-approve --inputs, no --out", check1_first_run_argv),
    ("Nudge adds --style-notes (verbatim), no --out (new run dir)", check2_nudge_adds_style_notes_new_dir),
    ("Empty/None note omits --style-notes (no fabricated nudge)", check3_empty_note_omits_flag),
]


def main():
    print("=" * 78)
    print("test_frontend_runner.py — falsifiable self-test (US2/US3, no paid calls)")
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
