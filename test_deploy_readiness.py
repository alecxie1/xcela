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


def check3_deploy_artifacts():
    """T004 / FR-003, FR-004: requirements.txt pins every core dep with == (a build that
    ships a loose or missing pin fails); bootstrap.sh parses (bash -n); the unit carries
    LANG=C.UTF-8 + TimeoutStopSec=30; the Caddyfile carries BOTH placeholders; the README
    names BOTH out-of-band items; nothing secret-shaped anywhere in deploy/."""
    import re
    import subprocess
    req = (REPO / "requirements.txt").read_text(encoding="utf-8")
    core = ["openai", "anthropic", "pillow", "numpy", "scipy", "pymupdf",
            "python-dotenv", "opencv-python"]
    a = all(re.search(rf"^{re.escape(d)}==[\d.]+", req, re.M) for d in core) \
        and "3.11" in req and "libgl1" in req

    b = subprocess.run(["bash", "-n", str(REPO / "deploy" / "bootstrap.sh")],
                       capture_output=True).returncode == 0
    unit = (REPO / "deploy" / "xcela.service").read_text(encoding="utf-8")
    c = ("LANG=C.UTF-8" in unit and "TimeoutStopSec=30" in unit
         and "Restart=on-failure" in unit and "XCELA_BIND=127.0.0.1" in unit)
    caddy = (REPO / "deploy" / "Caddyfile").read_text(encoding="utf-8")
    e = ("YOUR_DOMAIN" in caddy and "HASHED_PASSWORD" in caddy
         and "reverse_proxy 127.0.0.1:8765" in caddy)
    readme = (REPO / "deploy" / "README.md").read_text(encoding="utf-8")
    f = "~/.hermes/.env" in readme and "brands/" in readme and "restart" in readme.lower()

    secretish = re.compile(r"sk-[A-Za-z0-9]{10,}|api[_-]?key\s*=\s*['\"][A-Za-z0-9]{8,}")
    g = not any(secretish.search((REPO / "deploy" / n).read_text(encoding="utf-8"))
                for n in ("bootstrap.sh", "xcela.service", "Caddyfile", "README.md"))

    ok = a and b and c and e and f and g
    return ok, (f"pins={a}; bash-n={b}; unit={c}; caddy-placeholders={e}; "
                f"readme-handoff={f}; no-secrets={g}")


def check4_run_listing():
    """T005 / FR-008: list_runs over a fixture output dir: newest-first by id timestamp;
    exact per-entry flags (gated done+image, pre-015 dir with null gate, exported run);
    a corrupt gate_state lists with null instead of crashing; empty dir = []; limit
    honored. GET /runs wiring exercised HTTP-free via the pure function the route calls."""
    import shutil
    sys.path.insert(0, str(REPO / "frontend"))
    import run_view as rv

    d = _tmp("list")
    out = d / "output"
    out.mkdir()
    # newest (exported), middle (pre-015: no gate/meta), oldest (gated, corrupt gate later)
    r_new, _ = make_run_dir(out / "run_CJXQ_20260712_120000", messages=1)
    (r_new / "export_state.json").write_text('{"state": "done"}', encoding="utf-8")
    r_mid = out / "run_aia_20260711_110000"
    (r_mid / "sign_s1").mkdir(parents=True)
    Image.new("RGB", (8, 8)).save(r_mid / "sign_s1" / "generated.png")
    r_old, _ = make_run_dir(out / "run_CJXQ_20260710_100000", messages=1)
    (r_old / "gate_state.json").write_text("{corrupt", encoding="utf-8")

    runs = rv.list_runs(out)
    a = [r["id"] for r in runs] == ["run_CJXQ_20260712_120000", "run_aia_20260711_110000",
                                    "run_CJXQ_20260710_100000"]
    new, mid, old = runs
    b = (new["brand"] == "CJXQ" and new["gate_state"] == "done" and new["image"] is True
         and new["export_state"] == "done" and new["created"] == "2026-07-12T12:00:00")
    c = mid["brand"] is None and mid["gate_state"] is None and mid["image"] is True
    e = old["gate_state"] is None and old["export_state"] is None   # corrupt tolerated

    f = rv.list_runs(d / "does-not-exist") == [] and rv.list_runs(out, limit=2) == runs[:2]
    shutil.rmtree(d)
    ok = a and b and c and e and f
    return ok, f"order={a}; gated-flags={b}; pre015-nulls={c}; corrupt-null={e}; empty+limit={f}"


CHECKS = [
    ("T001 fixtures: dual-form brand key + shared run-dir import", check0_fixtures),
    ("T002 resolver: order, env override, soft None, refusal names every path", check1_resolver),
    ("T003 portable wiring: keys, scene sites, export soft-null, persist, validator", check2_portable_wiring),
    ("T004 requirements + deploy artifacts: pins, syntax, placeholders, no secrets", check3_deploy_artifacts),
    ("T005 run listing: newest-first flags, pre-015 nulls, corrupt tolerance, limit", check4_run_listing),
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
