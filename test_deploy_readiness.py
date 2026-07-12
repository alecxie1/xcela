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


def check2_portable_wiring():
    """T003 / FR-001, FR-002: the rewritten committed keys resolve to the same files as the
    old absolute literals on this machine; scene_author has NO fallback constant and exactly
    the three resolver call sites; export enumeration resolves relative keys (element
    present) and soft-nulls dangling ones; place_logo returns the brands-relative form;
    validate_lean_key accepts the committed relative key and rejects a dangling one."""
    import os
    import asset_paths as ap
    import export_layers as xl017
    sys.path.insert(0, str(REPO / "brand_intake"))
    import persist
    import validate_key as vk

    cjxq = json.loads((REPO / "answer_keys" / "CJXQ.json").read_text(encoding="utf-8"))
    a = (cjxq["logo_path"] == "CJXQ/jos cha logo.png"
         and ap.try_resolve_brand_asset(cjxq["logo_path"])
         == str(REPO / "brands" / "CJXQ" / "jos cha logo.png"))

    src = (REPO / "harness" / "scene_author.py").read_text(encoding="utf-8")
    b = ("LOGO_PATH" not in src.replace("the machine-specific LOGO_PATH fallback", "")
         and src.count("resolve_brand_asset(brand_key") == 3)

    d = _tmp("wire")
    base, _keys = make_brands(d)
    run, runkey = make_run_dir(d / "run", messages=1, logo_fed=True, products=0)
    # the fixture manifest fed the fixture's ABSOLUTE logo; a RELATIVE key must resolve to
    # that same file for the element to appear
    os.environ["XCELA_BRANDS_DIR"] = str(Path(runkey["logo_path"]).parent.parent)
    try:
        rel_key = {"logo_path": f"{Path(runkey['logo_path']).parent.name}/"
                                f"{Path(runkey['logo_path']).name}"}
        els = xl017.enumerate_elements(run, rel_key)
        c = any(e["id"] == "logo" for e in els)
        els2 = xl017.enumerate_elements(run, {"logo_path": "TESTBRAND/dangling.png"})
        e = not any(el["id"] == "logo" for el in els2)   # soft null, no crash
    finally:
        del os.environ["XCELA_BRANDS_DIR"]

    logo_src = base / "TESTBRAND" / "logo file.png"
    rel = persist.place_logo("TESTBRAND", str(logo_src))
    f = rel == "TESTBRAND/logo file.png" and (persist.BRANDS / rel).is_file()

    g = False
    try:
        vk.validate_lean_key(cjxq)   # committed relative key must validate
        g = True
    except Exception:  # noqa: BLE001
        pass
    h = False
    bad = dict(cjxq); bad["logo_path"] = "CJXQ/does-not-exist.png"
    try:
        vk.validate_lean_key(bad)
    except vk.KeyValidationError as exc:
        h = "does not resolve" in str(exc)

    ok = a and b and c and e and f and g and h
    return ok, (f"key-resolves={a}; no-fallback+3-sites={b}; rel-key-element={c}; "
                f"dangling-soft-null={e}; place_logo-relative={f}; committed-validates={g}; "
                f"dangling-rejected={h}")


CHECKS = [
    ("T001 fixtures: dual-form brand key + shared run-dir import", check0_fixtures),
    ("T002 resolver: order, env override, soft None, refusal names every path", check1_resolver),
    ("T003 portable wiring: keys, scene sites, export soft-null, persist, validator", check2_portable_wiring),
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
