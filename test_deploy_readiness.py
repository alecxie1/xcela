#!/usr/bin/env python3
"""test_deploy_readiness.py - falsifiable self-test for feature 017 (deployment readiness +
Chinese-ready UI).

NO paid calls anywhere. Contract rows refer to specs/017-deployment-readiness/contracts/
surfaces.md; the resolution order and env knobs to data-model.md. Reuses
test_export_layers.make_run_dir (the established cross-test import pattern) for run-dir
fixtures.

Run:  .venv/bin/python test_deploy_readiness.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "register"))
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

from test_export_layers import make_run_dir  # noqa: E402  (shared run-dir fixture)


def _tmp(name):
    return Path(tempfile.mkdtemp(prefix=f"x017_{name}_"))


# ---------------------------------------------------------------- fixtures

def make_brands(tmp):
    """A temp brands base dir with one brand + logo, plus key dicts in BOTH path forms:
    absolute (legacy keys keep working) and brands-relative (the committed form)."""
    base = Path(tmp) / "brands"
    (base / "TESTBRAND").mkdir(parents=True, exist_ok=True)
    logo = base / "TESTBRAND" / "logo file.png"   # space on purpose: real names have them
    Image.new("RGB", (32, 32), (250, 250, 250)).save(logo)
    return base, {"absolute": {"logo_path": str(logo)},
                  "relative": {"logo_path": "TESTBRAND/logo file.png"}}


# ---------------------------------------------------------------- checks

def check0_fixtures():
    """T001: the fixtures are trustworthy: the logo file really exists at both addressings,
    the relative form contains no separator prefix (a leading slash would silently make it
    absolute and bypass the resolution order), and the shared run-dir fixture imports."""
    d = _tmp("fix")
    base, keys = make_brands(d)
    a = (Path(keys["absolute"]["logo_path"]).is_file()
         and (base / keys["relative"]["logo_path"]).is_file()
         and not keys["relative"]["logo_path"].startswith("/"))
    run, key = make_run_dir(d / "run", messages=1)
    b = (run / "inputs.json").is_file() and "logo_path" in key
    ok = a and b
    return ok, f"brands fixture={a}; shared run fixture={b}"


def check1_resolver():
    """T002 / FR-001, FR-002: the resolution order as VALUES: absolute passthrough;
    brands-relative under the env override; repo-relative; None from the soft form; the
    raising form's refusal names EVERY tried path (a build that hides a candidate or
    substitutes a fallback fails here)."""
    import importlib
    import os
    import asset_paths as ap

    d = _tmp("resolve")
    base, keys = make_brands(d)

    a = ap.try_resolve_brand_asset(keys["absolute"]["logo_path"]) == keys["absolute"]["logo_path"]

    os.environ["XCELA_BRANDS_DIR"] = str(base)
    try:
        b = (ap.brands_dir() == base
             and ap.try_resolve_brand_asset("TESTBRAND/logo file.png")
             == str(base / "TESTBRAND" / "logo file.png"))
        c = ap.try_resolve_brand_asset("TESTBRAND/nope.png") is None
        e = False
        try:
            ap.resolve_brand_asset("TESTBRAND/nope.png")
        except SystemExit as exc:
            msg = str(exc)
            e = (str(base / "TESTBRAND" / "nope.png") in msg
                 and str(ap.REPO_ROOT / "TESTBRAND" / "nope.png") in msg
                 and "NO fallback" in msg)
    finally:
        del os.environ["XCELA_BRANDS_DIR"]
    importlib.invalidate_caches()

    # repo-relative fallback: a file that exists under the repo root resolves without env
    f = ap.try_resolve_brand_asset("conductor_inputs_example.json") == str(
        ap.REPO_ROOT / "conductor_inputs_example.json")
    g = ap.try_resolve_brand_asset("") is None and ap.try_resolve_brand_asset(None) is None

    ok = a and b and c and e and f and g
    return ok, (f"absolute={a}; env-base={b}; soft-none={c}; refusal-names-all={e}; "
                f"repo-relative={f}; empty-none={g}")


CHECKS = [
    ("T001 fixtures: dual-form brand key + shared run-dir import", check0_fixtures),
    ("T002 resolver: order, env override, soft None, refusal names every path", check1_resolver),
]


def main():
    print("=" * 78)
    print("test_deploy_readiness.py - falsifiable self-test (017, no paid calls)")
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
