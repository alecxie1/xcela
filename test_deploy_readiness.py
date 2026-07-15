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
# 019: answer keys are runtime state; the suites read the committed demo fixtures
import os as _os019
_os019.environ.setdefault("XCELA_ANSWER_KEYS_DIR",
                          str(Path(__file__).resolve().parent / "tests_support" / "demo_keys"))


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

    cjxq = json.loads((REPO / "tests_support" / "demo_keys" / "CJXQ.json").read_text(encoding="utf-8"))
    # brands/ is provisioned out-of-band (gitignored, dockerignored): where the logo file
    # exists, assert full resolution; in an unprovisioned context (fresh clone, container
    # without volumes) the committed-string pin is the checkable half
    _cjxq_logo = REPO / "brands" / "CJXQ" / "jos cha logo.png"
    a = cjxq["logo_path"] == "CJXQ/jos cha logo.png" and (
        not _cjxq_logo.is_file()
        or ap.try_resolve_brand_asset(cjxq["logo_path"]) == str(_cjxq_logo))

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
    import asset_paths as _ap019
    f = rel == "TESTBRAND/logo file.png" and (_ap019.brands_dir() / rel).is_file()

    g = False
    if not _cjxq_logo.is_file():
        g = True   # unprovisioned context: validation needs the real asset (vacuous)
    else:
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


def check5_resume_wiring():
    """T006 / FR-008 (form greps, value-bearing): the hash is read on load behind the
    #run_ guard (absent hash = the untouched pre-017 startup); every currentRun assignment
    goes through setCurrentRun (which replaceStates the hash: a stray raw assignment would
    silently break resume); the picker fetches /runs and renders into its container."""
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    a = 'if (location.hash.startsWith("#run_")) openRun(location.hash.slice(1));' in html
    b = ('history.replaceState' in html
         and html.count("currentRun = ") <= 2   # only inside setCurrentRun + declaration
         and html.count("setCurrentRun(") >= 3)  # def + startRun + viewAttempt
    # 2026-07-14 (021): the picker fetch goes through the jf() 401 wrapper now; the pinned
    # value moved WITH the call, never weakened (jf is fetch + login-bounce, same request)
    c = 'jf("/runs")' in html and 'id="recentruns"' in html and "openRun(" in html
    ok = a and b and c
    return ok, f"hash-guard={a}; one-assignment-home={b}; picker={c}"


def check6_chinese_input():
    """T007 / FR-009, FR-010, SC-002, SC-003: 朋友圈推广海报 derives marketing AS the 014
    explicit-statement (suppression trace, zero usage assumptions in the sink); 手举牌 beats
    营销 in one phrase (event row precedence); the MIXED context 上墙+\"marketing\" derives
    via the wall row; the wall-posted baseline is byte-identical to the imported 011 literal;
    ６０×４０厘米 resolves byte-identically to 60x40cm; current ASCII parses are
    byte-identical; post-normalization garbage still defaults with the honest note."""
    import derive_register as dr
    import format_size as fmtsize
    from test_register_render_aware import EXPECTED_PREFEATURE_PROFILE, _subfields

    sink = []
    p = dr.derive_register(_subfields(usage="朋友圈推广海报"), {}, assumptions_sink=sink)
    sup = [t for t in p["_derivation_trace"] if "SUPPRESSED" in t]
    a = (p["inferred_register"] == "marketing" and len(sup) == 1
         and not any(r.get("dimension") == "register" for r in sink))

    p2 = dr.derive_register(_subfields(usage="活动现场手举牌，用于品牌营销"), {})
    b = p2["inferred_register"] == "event_prop"   # event row precedence over 营销

    # MIXED language: 上墙 (wall row, earlier) must be the matched keyword, not 海报 or
    # "marketing" (both in the later marketing row); the final register may still promote
    # on the playful vibe exactly like the pinned English wall-posted baseline
    p3 = dr.derive_register(_subfields(usage="海报上墙 marketing"), {})
    c = any("上墙" in t for t in p3["_derivation_trace"])

    absent = json.dumps(dr.derive_register(_subfields(), {}), ensure_ascii=False,
                        sort_keys=True)
    e = absent == EXPECTED_PREFEATURE_PROFILE   # English baseline byte-identical

    zh = fmtsize.resolve_size("６０×４０厘米")
    en = fmtsize.resolve_size("60x40cm")
    f = {k: v for k, v in zh.items() if k != "requested_size"} \
        == {k: v for k, v in en.items() if k != "requested_size"} \
        and zh["width"] == en["width"] and zh["pixels"] == en["pixels"]
    r6040 = fmtsize.resolve_size("60x40cm")
    g = ((r6040["width"], r6040["height"]) == (1536, 1024)   # the documented 3:2 anchor
         and all(fmtsize.resolve_size(s)["note"] is None
                 for s in ("60x40cm", "40x60cm", "8.5x11in")))
    h = "could not parse" in (fmtsize.resolve_size("尺寸随意")["note"] or "")

    ok = a and b and c and e and f and g and h
    return ok, (f"marketing+suppress+no-row={a}; event-precedence={b}; mixed-wall={c}; "
                f"english-baseline-identical={e}; fullwidth==ascii={f}; ascii-parses={g}; "
                f"garbage-honest-default={h}")


def check7_chinese_chrome():
    """T008 / FR-011: the load-bearing labels are simplified Chinese; every select that lost
    its English display text kept its canonical VALUE via an explicit value= attribute (a
    build that translates option text without value attrs silently changes submitted briefs
    and fails here); formState still submits the same keys; every REGISTER_LANE_OPTIONS
    label has a ZH entry (drift guard: a new lane option without a translation fails)."""
    import re
    import derive_register as dr
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    ob = (REPO / "frontend" / "onboard.html").read_text(encoding="utf-8")

    a = ("付费前确认" in html and "确认并生成" in html and "分层导出" in html
         and "风格参考图" in html and "画面上的文字" in html and "满意（就用这张）" in html)
    b = ('<option value="omit">' in html and '<option value="faithful">' in html
         and '<option value="expressive departure">' in html
         and '<option value="strict VI">' in html
         and '<option value="flat vector">' in html
         and '<option value="photographic">' in html
         and '<option value="extend">' in html and '<option value="mood">' in html)
    keys = ["brand:", "asset_type:", "render_style:", "format_size:",
            "reference_relationship:", "logo_treatment:", "brand_strictness:",
            "occasion:", "usage_context:", "mandatory_elements:", "messages:"]
    form = html[html.index("function formState"):html.index("function renderStage")]
    c = all(k in form.replace(" $", "$").replace(": $", ":$") or k.rstrip(":") in form
            for k in keys)

    zh_block = html[html.index("const ZH = {"):html.index("function zh(")]
    e = all(f'"{o["label"]}"' in zh_block for o in dr.REGISTER_LANE_OPTIONS)

    f = ("上传品牌 VI 手册" in ob and "校验并保存" in ob
         and '<option value="primary">primary</option>' in ob   # role VALUES stay canonical
         and '<option value="keep-flagged">' in ob)
    g = html.count('href="/playbook"') == 1 and ob.count('href="/playbook"') == 1

    ok = a and b and c and e and f and g
    return ok, (f"labels-zh={a}; option-values-kept={b}; formState-keys={c}; "
                f"lane-dict-complete={e}; onboard-zh={f}; playbook-nav={g}")


def check8_playbook():
    """T009 / FR-012: the served playbook carries the VALUE-bearing content: both cost
    figures, the single-flight etiquette naming the actual 409 string, at least three
    common-message rows quoting the REAL server strings (a table of invented messages
    fails), the draft charter, the feedback placeholder, and the docs/ pointer; the route
    is wired in server.py."""
    pb = (REPO / "frontend" / "playbook.html").read_text(encoding="utf-8")
    a = "$0.08" in pb and "$0.5" in pb and "不点确认就永远不收费" in pb
    b = "a run is already in flight" in pb and "一次只能跑一个" in pb
    real_msgs = ["already confirmed; no second spend",
                 "already exporting/exported; no second spend",
                 "export needs a generated, judged image",
                 "brand asset not found"]
    c = sum(m in pb for m in real_msgs) >= 3
    e = "给设计师收尾的草案" in pb and "[待定：反馈渠道确认后填写]" in pb

    srv = (REPO / "frontend" / "server.py").read_text(encoding="utf-8")
    f = 'path == "/playbook"' in srv and 'playbook.html' in srv
    g = "frontend/playbook.html" in (REPO / "docs" / "PLAYBOOK.md").read_text(encoding="utf-8")

    ok = a and b and c and e and f and g
    return ok, (f"costs={a}; etiquette-409={b}; real-message-rows={c}; charter+placeholder={e}; "
                f"route={f}; docs-pointer={g}")


def check9_guards():
    """T010 / FR-005, FR-006, FR-007, SC-005: defaults byte-identical (empty env + argv =
    127.0.0.1:8765; env knobs + argv precedence honored); a real oversize POST answers 413
    with the pinned wording BEFORE any lock or run dir (the lock stays free, output/ gains
    nothing); a wedged worker is killed at the wall clock, writes the named timeout error,
    and FREES the single-flight lock; a killed worker's pid no longer blocks a new export
    (the 016 stuck-state composition)."""
    import http.client
    import os
    import time
    os.environ["XCELA_MAX_UPLOAD_MB"] = "1"      # must be set BEFORE the server import
    os.environ["XCELA_WORKER_TIMEOUT_S"] = "1"
    sys.path.insert(0, str(REPO / "frontend"))
    import server
    import export_layers as xl
    try:
        a = (server._bind_config(["server.py"], {}) == ("127.0.0.1", 8765)
             and server._bind_config(["server.py"], {"XCELA_BIND": "0.0.0.0",
                                                     "XCELA_PORT": "9000"}) == ("0.0.0.0", 9000)
             and server._bind_config(["server.py", "7000"],
                                     {"XCELA_PORT": "9000"}) == ("127.0.0.1", 7000)
             and server.MAX_UPLOAD_BYTES == 1024 * 1024 and server.WORKER_TIMEOUT_S == 1)

        # real oversize POST against an ephemeral instance: 413 pinned, lock free, no run dir
        from http.server import ThreadingHTTPServer
        import threading
        srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        before = set(p.name for p in server.OUTPUT.glob("run_*")) if server.OUTPUT.is_dir() else set()
        # raw socket on purpose: the server answers 413 EARLY without draining the body,
        # so the client's body send may hit EPIPE; that is the designed behavior, and the
        # response must still be readable
        import socket
        sk = socket.create_connection(("127.0.0.1", port), timeout=10)
        sk.sendall((f"POST /run HTTP/1.1\r\nHost: t\r\n"
                    f"Content-Type: multipart/form-data; boundary=x\r\n"
                    f"Content-Length: {2 * 1024 * 1024}\r\n\r\n").encode())
        try:
            sk.sendall(b"x" * (256 * 1024))
        except (BrokenPipeError, ConnectionResetError):
            pass   # the early 413 already ended the exchange
        data = b""
        try:
            sk.settimeout(5)
            while len(data) < 4096:
                chunk = sk.recv(65536)
                if not chunk:
                    break
                data += chunk
        except (TimeoutError, OSError):
            pass
        sk.close()
        srv.shutdown()
        after = set(p.name for p in server.OUTPUT.glob("run_*")) if server.OUTPUT.is_dir() else set()
        b = (data.startswith(b"HTTP/1.0 413") or data.startswith(b"HTTP/1.1 413")) \
            and "exceeds the 1MB cap".encode() in data \
            and not server._inflight.locked() and before == after

        # wedged worker: killed at the 1s wall clock, named error, lock freed
        d = _tmp("timeout")
        server._inflight.acquire()
        server._spawn_worker(["sleep", "30"], d, error_name="run_error.txt")
        deadline = time.time() + 10
        while time.time() < deadline and not (d / "run_error.txt").is_file():
            time.sleep(0.2)
        err = (d / "run_error.txt").read_text(encoding="utf-8") if (d / "run_error.txt").is_file() else ""
        deadline = time.time() + 3
        while time.time() < deadline and server._inflight.locked():
            time.sleep(0.1)
        c = ("timed out after 1s" in err and "paid calls may already have completed" in err
             and not server._inflight.locked())

        # composition: a killed worker's dead pid does not block a new export
        import subprocess
        pr = subprocess.Popen(["sleep", "0"]); pr.wait()
        e = not xl.state_blocks_new_export({"state": "exporting", "started_at": "t",
                                            "pid": pr.pid})
    finally:
        del os.environ["XCELA_MAX_UPLOAD_MB"]
        del os.environ["XCELA_WORKER_TIMEOUT_S"]

    ok = a and b and c and e
    return ok, (f"bind-config={a}; 413-pinned+lock-free+no-dir={b}; "
                f"timeout-error+lock-freed={c}; dead-pid-retryable={e}")


def check10_env_loader():
    """018 T001 / FR-001, FR-002, SC-001: hermetic precedence proof BY VALUE (a real env var
    beats a conflicting repo .env; the repo .env beats the legacy home file; a
    home-file-only var still loads); ZERO override=True dotenv loads outside legacy/; all
    six live call sites import the loader; .env.example documents every variable the live
    code reads and is NOT gitignored."""
    import os
    import re
    import subprocess
    from runtime_env import load_runtime_env

    d = _tmp("env")
    (d / "repo").mkdir(); (d / "home" / ".hermes").mkdir(parents=True)
    (d / "repo" / ".env").write_text("X18_A=repofile\nX18_B=repofile\n", encoding="utf-8")
    (d / "home" / ".hermes" / ".env").write_text("X18_B=homefile\nX18_C=homefile\n",
                                                 encoding="utf-8")
    os.environ["X18_A"] = "realenv"
    try:
        load_runtime_env(_repo=d / "repo", _home=d / "home")
        a = (os.environ["X18_A"] == "realenv"       # real env beats the repo file
             and os.environ["X18_B"] == "repofile"  # repo file beats the legacy home file
             and os.environ["X18_C"] == "homefile") # legacy fallback still loads
    finally:
        for k in ("X18_A", "X18_B", "X18_C"):
            os.environ.pop(k, None)

    live = subprocess.run(["grep", "-rn", "override=True", "harness", "register",
                           "frontend", "brand_intake"], cwd=REPO, capture_output=True,
                          text=True).stdout
    b = live.strip() == ""

    sites = ["harness/approve.py", "harness/generate.py", "harness/scene_author.py",
             "register/blind_score.py", "register/calibrate_from_reference.py",
             "register/reference_style_to_prompt.py"]
    c = all("load_runtime_env" in (REPO / s).read_text(encoding="utf-8") for s in sites)

    example = (REPO / ".env.example").read_text(encoding="utf-8")
    read_vars = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
    for f in ((REPO / "frontend" / "server.py"), (REPO / "harness" / "asset_paths.py"),
              (REPO / "harness" / "model_client.py")):
        read_vars |= set(re.findall(r'environ\.get\("(XCELA_[A-Z_]+)"', f.read_text(encoding="utf-8")))
    e = all(v in example for v in read_vars)
    # gitless contexts (the Docker image excludes .git) cannot check ignore rules; that is
    # a property of the working copy, not the image, so it passes vacuously there
    f2 = (not (REPO / ".git").exists()
          or subprocess.run(["git", "check-ignore", "-q", ".env.example"],
                            cwd=REPO).returncode == 1)

    ok = a and b and c and e and f2
    return ok, (f"precedence-by-value={a}; no-override-live={b}; six-sites={c}; "
                f"example-covers={sorted(read_vars) if not e else True}; example-tracked={f2}")


CHECKS = [
    ("T001 fixtures: dual-form brand key + shared run-dir import", check0_fixtures),
    ("T002 resolver: order, env override, soft None, refusal names every path", check1_resolver),
    ("T003 portable wiring: keys, scene sites, export soft-null, persist, validator", check2_portable_wiring),
    ("T004 requirements + deploy artifacts: pins, syntax, placeholders, no secrets", check3_deploy_artifacts),
    ("T005 run listing: newest-first flags, pre-015 nulls, corrupt tolerance, limit", check4_run_listing),
    ("T006 resume wiring: hash guard, replaceState sync, /runs picker, default path", check5_resume_wiring),
    ("T007 Chinese input: lanes + suppression + byte-identity + fullwidth sizes", check6_chinese_input),
    ("T008 Chinese chrome: labels, unchanged submit values, ZH dict drift guard", check7_chinese_chrome),
    ("T009 playbook: served route, costs, etiquette, message table, placeholder", check8_playbook),
    ("T010 guards: default bind, env knobs, 413 cap pre-lock, worker timeout frees lock", check9_guards),
    ("018 env loader: precedence by value, no override=True, six sites, .env.example", check10_env_loader),
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
