#!/usr/bin/env python3
"""frontend/runner.py - build + launch the conductor run the UI triggers (feature 004, US2/US3).

THIN: the UI shells out to the EXISTING agent-free conductor; it never reimplements generation. The
argv builder is PURE (testable free); `launch` is the side effect (the paid step on a human click).
Each call carries `--thin --no-approve --inputs` and NO `--out`, so the conductor makes a NEW
timestamped run dir per attempt (clarified: prior attempts preserved). A nudge adds `--style-notes`.
"""

import subprocess
import sys
from pathlib import Path

PY = sys.executable
REPO_ROOT = Path(__file__).resolve().parent.parent
CONDUCTOR = "harness/conductor.py"


def build_conductor_argv(inputs_path, brand: str, style_notes=None, phase=None) -> list:
    """Pure: the conductor CLI invocation for a (re)run. `style_notes` (a nudge) is added verbatim
    as a binding clause; absent/empty omits it. No `--out` => a new run dir per call.
    Feature 015: `phase` appends `--phase <derive|generate>`; None keeps the pre-015 argv
    byte-identical (the faithful CLI default). The browser launches derive (zero spend) and,
    on operator confirmation, generate."""
    argv = [PY, CONDUCTOR, "--brand", brand, "--thin", "--no-approve", "--inputs", str(inputs_path)]
    if style_notes:
        argv += ["--style-notes", str(style_notes)]
    if phase:
        argv += ["--phase", str(phase)]
    return argv


def launch(argv: list) -> dict:
    """Run the conductor (the paid step) and return the newest output/run_* dir. Not used by tests."""
    proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out_root = REPO_ROOT / "output"
    runs = sorted((p for p in out_root.glob("run_*") if p.is_dir()),
                  key=lambda p: p.stat().st_mtime) if out_root.exists() else []
    run_dir = runs[-1] if runs else None
    return {"ok": proc.returncode == 0, "run_dir": str(run_dir) if run_dir else None,
            "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
