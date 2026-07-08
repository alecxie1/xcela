#!/usr/bin/env python3
"""test_export_layers.py - falsifiable self-test for feature 016 (layered export).

NO paid calls anywhere: the orchestrator takes an injected generate_fn (a recording stub that
writes synthetic chroma PNGs); the REAL strip_chroma keying runs on those synthetic fixtures.
Contract rows refer to specs/016-layered-export/contracts/http-and-cli.md; the record schema
to specs/016-layered-export/data-model.md.

Run:  .venv/bin/python test_export_layers.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

import export_layers as xl  # noqa: E402

CHROMA = (0, 177, 64)  # #00B140, must stay equal to scene_author.CHROMA_KEY_HEX
CANVAS = (1536, 1024)


# ---------------------------------------------------------------- fixtures

def make_chroma_png(path, w=1536, h=1024, content="rect"):
    """Synthetic isolation outputs for the REAL strip_chroma to key.
    rect  - a red rectangle on flat chroma green (the well-behaved layer);
    full  - full-frame non-green noise (the model ignored the chroma directive);
    empty - pure chroma green, nothing else (an empty frame)."""
    if content == "rect":
        img = Image.new("RGB", (w, h), CHROMA)
        px = img.load()
        for x in range(w // 4, 3 * w // 4):
            for y in range(h // 4, 3 * h // 4):
                px[x, y] = (200, 30, 30)
    elif content == "multi":
        # three equal DISCONNECTED blobs (a multi-glyph text line): largest-component keep
        # retains one and drops two, i.e. the majority of the content
        from PIL import ImageDraw
        img = Image.new("RGB", (w, h), CHROMA)
        draw = ImageDraw.Draw(img)
        for i in range(3):
            x0 = w // 8 + i * (w // 4)
            draw.rectangle([x0, h // 3, x0 + w // 8, 2 * h // 3], fill=(200, 30, 30))
    elif content == "full":
        img = Image.new("RGB", (w, h), (180, 160, 140))
        px = img.load()
        for x in range(0, w, 7):        # texture so no "flat backdrop" exists anywhere
            for y in range(h):
                px[x, y] = (40, 60, 200)
    elif content == "empty":
        img = Image.new("RGB", (w, h), CHROMA)
    else:
        raise ValueError(content)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return Path(path)


def make_run_dir(root, messages=3, logo_fed=True, products=1, gate_state="done",
                 brand="CJXQ", size="1536x1024"):
    """A CJXQ-shaped thin-route run dir: exactly the artifacts enumerate_elements and the
    state machine read (inputs.json, sign_s1/run_manifest.json, gate_state.json, run_meta.json,
    sign_s1/generated.png)."""
    run = Path(root)
    sign = run / "sign_s1"
    sign.mkdir(parents=True, exist_ok=True)

    msg_lines = ["瓜田冰爽特供", "“WATERMELON COCONUT”", "现开西瓜100%真果肉",
                 "FOURTH LINE", "FIFTH LINE"][:messages]
    logo_path = str(run / "brand_logo.png")
    Image.new("RGB", (64, 64), (255, 255, 255)).save(logo_path)
    product_paths = []
    for i in range(1, products + 1):
        p = run / f"product_{i}.jpg"
        Image.new("RGB", (64, 64), (10, 10, 10)).save(p)
        product_paths.append(str(p))

    inputs = {"signs": [{"id": "s1", "messages": msg_lines, "hero_icon": None}]}
    if product_paths:
        inputs["product_images"] = product_paths
    (run / "inputs.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    refs = [str(run / "reference.png")]
    if logo_fed:
        refs.append(logo_path)
    refs.extend(product_paths)
    manifest = {"brand": brand, "messages": msg_lines,
                "generation": {"model": "gpt-image-2", "endpoint": "images.edit",
                               "size": size, "quality": "high",
                               "reference_image": refs,
                               "output": str(sign / "generated.png")}}
    (sign / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False),
                                            encoding="utf-8")

    (run / "gate_state.json").write_text(json.dumps({"state": gate_state}), encoding="utf-8")
    (run / "run_meta.json").write_text(json.dumps({"brand": brand}), encoding="utf-8")
    Image.new("RGB", (192, 128), (90, 160, 220)).save(sign / "generated.png")
    return run, {"logo_path": logo_path}


def _tmp(name):
    import tempfile
    d = Path(tempfile.mkdtemp(prefix=f"x016_{name}_"))
    return d


# ---------------------------------------------------------------- checks

def check0_fixtures():
    """T001: the fixtures themselves are trustworthy: the chroma color is EXACTLY #00B140
    (a wrong key would silently pass every later keying check), the run dir carries the
    artifacts by their real names, and the fed-refs list actually contains the logo path."""
    d = _tmp("fix")
    p = make_chroma_png(d / "rect.png", w=192, h=128, content="rect")
    img = Image.open(p).convert("RGB")
    corner = img.getpixel((2, 2))
    center = img.getpixel((96, 64))
    a = corner == CHROMA and center == (200, 30, 30)

    run, key = make_run_dir(d / "run", messages=3, logo_fed=True, products=1)
    inputs = json.loads((run / "inputs.json").read_text(encoding="utf-8"))
    man = json.loads((run / "sign_s1" / "run_manifest.json").read_text(encoding="utf-8"))
    b = (len(inputs["signs"][0]["messages"]) == 3
         and key["logo_path"] in man["generation"]["reference_image"]
         and (run / "sign_s1" / "generated.png").exists()
         and json.loads((run / "gate_state.json").read_text())["state"] == "done")

    run2, key2 = make_run_dir(d / "run2", logo_fed=False, products=0)
    man2 = json.loads((run2 / "sign_s1" / "run_manifest.json").read_text(encoding="utf-8"))
    c = key2["logo_path"] not in man2["generation"]["reference_image"]

    ok = a and b and c
    return ok, (f"chroma corner={corner} center={center}; run artifacts ok={b}; "
                f"unfed-logo excluded={c}")


def check1_enumeration_and_plan():
    """T002 / FR-001, FR-011, SC-003: elements come from the run's own artifacts with stable
    ids; the unfed logo NEVER becomes an element; the plan prices exactly N+1 calls. A build
    that guesses elements, misses the fed-gate, or forgets the +1 background fails here."""
    d = _tmp("enum")
    run, key = make_run_dir(d / "run", messages=3, logo_fed=True, products=1)
    els = xl.enumerate_elements(run, key)
    ids = [e["id"] for e in els]
    a = (ids == ["text_1", "text_2", "text_3", "logo", "product_1"]
         and els[0]["text"] == "瓜田冰爽特供"
         and els[3]["ref"] == key["logo_path"]
         and els[4]["kind"] == "product")

    run2, key2 = make_run_dir(d / "run2", messages=2, logo_fed=False, products=0)
    ids2 = [e["id"] for e in xl.enumerate_elements(run2, key2)]
    b = ids2 == ["text_1", "text_2"]

    plan = xl.export_plan(run, key, per_image_usd=0.08)
    c = (plan["calls"] == 6 and abs(plan["cost_usd"] - 0.48) < 1e-9
         and plan["size"] == "1536x1024"
         and plan["source_image"].endswith("sign_s1/generated.png"))
    ok = a and b and c
    return ok, f"ids={ids}; unfed={ids2}; calls={plan['calls']} cost={plan['cost_usd']}"


def check2_prompts_and_refusals():
    """T002 / FR-002, FR-003, FR-011: value-bearing prompt clauses (constitution III): the
    VERBATIM line appears exactly once; the literal key hex; identical-position/size and
    exact-canvas demands; ONE-element exclusivity; logo/product prompts name the SECOND
    supplied image; the background prompt lists EVERY element's description; zero-element
    and missing-source plans refuse with named SystemExits."""
    d = _tmp("prom")
    run, key = make_run_dir(d / "run", messages=2, logo_fed=True, products=1)
    els = xl.enumerate_elements(run, key)

    line = "瓜田冰爽特供"
    tp = xl.isolation_prompt(els[0])
    a = (tp.count(f'"{line}"') == 1
         and xl.CHROMA_KEY_HEX in tp and "#00B140" in tp
         and "identical position" in tp and "identical size" in tp
         and "exact canvas size" in tp
         and "EXACTLY ONE element" in tp)

    lp = xl.isolation_prompt(els[2])   # logo
    pp = xl.isolation_prompt(els[3])   # product
    b = "SECOND supplied image" in lp and "SECOND supplied image" in pp and line not in lp

    bg = xl.background_prompt(els)
    # the background call passes ONLY the source image, so its element descriptions must
    # never reference a second supplied image (that hint is isolation-call-only)
    b2 = (all(xl._element_desc(e, with_ref_hint=False) in bg for e in els)
          and "SECOND supplied image" not in bg
          and "REMOVED" in bg and "no text" in bg)

    c = False
    run2, key2 = make_run_dir(d / "empty", messages=0, logo_fed=False, products=0)
    try:
        xl.export_plan(run2, key2)
    except SystemExit as exc:
        c = "no enumerable elements" in str(exc)
    e = False
    run3, key3 = make_run_dir(d / "nosrc", messages=2)
    (run3 / "sign_s1" / "generated.png").unlink()
    try:
        xl.export_plan(run3, key3)
    except SystemExit as exc:
        e = "nothing to decompose" in str(exc)

    ok = a and b and b2 and c and e
    return ok, (f"text clauses={a}; second-image={b}; background lists all={b2}; "
                f"zero-el refusal={c}; no-source refusal={e}")


def check3_real_keying():
    """T003 / FR-004, FR-005, US3 acceptance 1-2: the REAL strip_chroma runs on synthetic
    fixtures and key_layer judges honestly. Falsifiable values: alpha probed at exact pixels,
    bbox within the defringe margin of the drawn rect, each null carries its NAMED note.
    An always-ok or always-null build, or one that fabricates a cutout, fails here."""
    d = _tmp("key")

    rect = make_chroma_png(d / "rect.png", content="rect")
    r1 = xl.key_layer(rect, d / "L_rect")
    cut = Image.open(r1["cutout"])
    a = (r1["status"] == "ok" and cut.mode == "RGBA"
         and cut.getpixel((10, 10))[3] == 0                    # green field -> transparent
         and cut.getpixel((768, 512))[3] == 255                # rect center -> opaque
         and Path(r1["preview_jpg"]).is_file()
         and r1["note"] == "")
    # drawn rect: x 384..1151, y 256..767; defringe erodes 2px; getbbox right/lower exclusive
    bx = r1["bbox"]
    b = bx is not None and all(abs(v - e) <= 4 for v, e in zip(bx, [384, 256, 1152, 768]))

    full = make_chroma_png(d / "full.png", content="full")
    r2 = xl.key_layer(full, d / "L_full")
    c = (r2["status"] == "null" and "chroma directive ignored" in r2["note"]
         and r2["bbox"] is None and "preview_jpg" not in r2)

    empty = make_chroma_png(d / "empty.png", content="empty")
    r3 = xl.key_layer(empty, d / "L_empty")
    e = r3["status"] == "null" and "empty frame" in r3["note"]

    # majority-drop honest null: 3 disconnected equal blobs -> largest-component keep
    # erases 2/3 of the content; that layer must NOT ship as an unqualified "ok" cutout
    multi = make_chroma_png(d / "multi.png", content="multi")
    r4 = xl.key_layer(multi, d / "L_multi")
    f = (r4["status"] == "null" and "MAJORITY" in r4["note"]
         and r4["stray_component_px_dropped"] > 0)

    ok = a and b and c and e and f
    return ok, (f"rect ok={a} bbox={bx}; full-null={c} (frac={r2['opaque_frac']}); "
                f"empty-null={e} (frac={r3['opaque_frac']}); majority-drop-null={f} "
                f"(dropped={r4['stray_component_px_dropped']})")


class RecordingStub:
    """Injectable generate_fn: records every call, writes synthetic chroma PNGs so the REAL
    key_layer runs downstream. null_ids get a full-noise frame (forces an honest null).
    manifest_len_at_call proves the manifest grows PROGRESSIVELY (crash = truthful partial)."""

    def __init__(self, run_dir, null_ids=()):
        self.run_dir = Path(run_dir)
        self.null_ids = set(null_ids)
        self.calls = []
        self.manifest_len_at_call = []

    def __call__(self, prompt, refs, out_path, size=None, **kw):
        mpath = self.run_dir / xl.MANIFEST_NAME
        n = len(json.loads(mpath.read_text(encoding="utf-8"))["layers"]) if mpath.is_file() else -1
        self.manifest_len_at_call.append(n)
        self.calls.append({"prompt": prompt, "refs": list(refs), "out": out_path, "size": size,
                           "state_on_disk": (xl.read_state(self.run_dir) or {}).get("state")})
        layer_id = Path(out_path).parent.name
        if layer_id == "background":
            Image.new("RGB", CANVAS, (120, 120, 200)).save(out_path)
        else:
            make_chroma_png(out_path, content="full" if layer_id in self.null_ids else "rect")
        return {"stub": True}


def check4_orchestrator_and_zip():
    """T004 / FR-006, SC-003, SC-004: exactly N+1 calls; refs per contract ([source] for text
    and background, [source, asset] for logo/product); size threaded from run_manifest; the
    manifest grows one entry per layer BETWEEN calls with the EXACT prompt; the zip member set
    EQUALS the expected set; the forced-null layer ships raw + note and NO cutout/preview."""
    import zipfile
    d = _tmp("orch")
    run, key = make_run_dir(d / "run", messages=2, logo_fed=True, products=1)
    stub = RecordingStub(run, null_ids={"product_1"})
    res = xl.export_layers(run, key, generate_fn=stub, per_image_usd=0.08)

    a = res["state"] == "done" and len(stub.calls) == 5   # 4 elements + 1 background
    src = str(run / "sign_s1" / "generated.png")
    c0, c2, c3, c4 = stub.calls[0], stub.calls[2], stub.calls[3], stub.calls[4]
    b = (c0["refs"] == [src] and c0["size"] == "1536x1024"
         and c2["refs"] == [src, key["logo_path"]]
         and c3["refs"] == [src, str(run / "product_1.jpg")]
         and c4["refs"] == [src])
    els = xl.enumerate_elements(run, key)
    c = (all(stub.calls[i]["prompt"] == xl.isolation_prompt(els[i]) for i in range(4))
         and c4["prompt"] == xl.background_prompt(els))
    prog = stub.manifest_len_at_call == [0, 1, 2, 3, 4]   # entry i on disk before call i+1

    zf = zipfile.ZipFile(run / xl.ZIP_NAME)
    expected = {"export_manifest.json", "background.png", "background_preview.jpg",
                "text_1.png", "text_1_preview.jpg", "text_2.png", "text_2_preview.jpg",
                "logo.png", "logo_preview.jpg", "product_1_raw.png"}
    e = set(zf.namelist()) == expected

    man = json.loads((run / xl.MANIFEST_NAME).read_text(encoding="utf-8"))
    null = [l for l in man["layers"] if l["id"] == "product_1"][0]
    f = (null["status"] == "null" and "chroma directive ignored" in null["note"]
         and set(null["files"]) == {"raw"})

    ok = a and b and c and prog and e and f
    return ok, (f"calls={len(stub.calls)} done={a}; refs={b}; prompts exact={c}; "
                f"progressive={prog} ({stub.manifest_len_at_call}); zip set equal={e}; "
                f"null packaging={f}")


def check5_state_machine():
    """T005 / FR-007, SC-003: state ON DISK before the first paid call; done => a second
    invocation makes ZERO calls; a mid-flight crash lands in failed (with the partial
    manifest intact) and failed accepts a retry; an unconfirmed gate refuses with zero
    spend; the decider's reservation (exporting, no started_at) is ADOPTED by the worker;
    an exporting owned by a LIVE pid no-ops while a DEAD-pid exporting (hard-killed worker)
    is reclaimed; KeyboardInterrupt marks failed (never a stranded 'exporting')."""
    import os
    import subprocess
    d = _tmp("state")
    run, key = make_run_dir(d / "run", messages=1, logo_fed=False, products=0)
    stub = RecordingStub(run)
    xl.export_layers(run, key, generate_fn=stub)
    a = stub.calls and stub.calls[0]["state_on_disk"] == "exporting"

    stub2 = RecordingStub(run)
    res2 = xl.export_layers(run, key, generate_fn=stub2)
    b = len(stub2.calls) == 0 and res2["state"] == "done" and "no second spend" in res2["note"]

    run3, key3 = make_run_dir(d / "crash", messages=2, logo_fed=False, products=0)

    class Crash(RecordingStub):
        def __call__(self, *a, **k):
            if len(self.calls) == 1:
                raise RuntimeError("simulated mid-flight crash")
            return super().__call__(*a, **k)

    crash = Crash(run3)
    try:
        xl.export_layers(run3, key3, generate_fn=crash)
        c = False
    except RuntimeError:
        st = xl.read_state(run3)
        man = json.loads((run3 / xl.MANIFEST_NAME).read_text(encoding="utf-8"))
        c = (st["state"] == "failed" and "simulated mid-flight crash" in st["error"]
             and len(man["layers"]) == 1)   # the truthful partial
    retry = RecordingStub(run3)
    res_r = xl.export_layers(run3, key3, generate_fn=retry)
    e = res_r["state"] == "done" and len(retry.calls) == 3

    run4, key4 = make_run_dir(d / "gate", messages=1, gate_state="awaiting_confirmation")
    f = False
    g4 = RecordingStub(run4)
    try:
        xl.export_layers(run4, key4, generate_fn=g4)
    except SystemExit as exc:
        f = "not 'done'" in str(exc) and len(g4.calls) == 0

    run5, key5 = make_run_dir(d / "resv", messages=1, logo_fed=False, products=0)
    plan5 = xl.export_plan(run5, key5)
    xl._write_state(run5, {"state": "exporting", "plan": plan5,
                           "cost_stated": "$0.16", "created": "t"})   # reservation, no started_at
    s5 = RecordingStub(run5)
    res5 = xl.export_layers(run5, key5, generate_fn=s5)
    g = res5["state"] == "done" and len(s5.calls) == 2   # adopted, not no-oped

    run6, key6 = make_run_dir(d / "started", messages=1, logo_fed=False, products=0)
    xl._write_state(run6, {"state": "exporting", "plan": None, "started_at": "t",
                           "pid": os.getpid()})          # a LIVE worker owns this state
    s6 = RecordingStub(run6)
    res6 = xl.export_layers(run6, key6, generate_fn=s6)
    h = len(s6.calls) == 0 and "no second spend" in res6["note"]

    # a hard-killed worker (started_at set, pid DEAD) must be reclaimable, never bricked
    pr = subprocess.Popen(["sleep", "0"]); pr.wait()
    run7, key7 = make_run_dir(d / "deadpid", messages=1, logo_fed=False, products=0)
    xl._write_state(run7, {"state": "exporting", "plan": None, "started_at": "t",
                           "pid": pr.pid})
    s7 = RecordingStub(run7)
    res7 = xl.export_layers(run7, key7, generate_fn=s7)
    i = res7["state"] == "done" and len(s7.calls) == 2   # stuck state reclaimed

    # KeyboardInterrupt (Ctrl-C of the server SIGINTs the child) must land in failed,
    # never strand 'exporting' (a stranded started state was un-retryable pre-review)
    run8, key8 = make_run_dir(d / "sigint", messages=1, logo_fed=False, products=0)

    class Interrupt(RecordingStub):
        def __call__(self, *a, **k):
            raise KeyboardInterrupt()

    j = False
    try:
        xl.export_layers(run8, key8, generate_fn=Interrupt(run8))
    except KeyboardInterrupt:
        st8 = xl.read_state(run8)
        j = st8["state"] == "failed" and "KeyboardInterrupt" in st8["error"]

    ok = a and b and c and e and f and g and h and i and j
    return ok, (f"state-before-call={a}; done-noop={b}; crash->failed+partial={c}; "
                f"failed-retry={e}; gate-refusal={f}; reservation-adopted={g}; "
                f"live-pid-noop={h}; dead-pid-reclaimed={i}; sigint->failed={j}")


def check7_decide_export_and_plan_view():
    """T005 / FR-007, FR-008 contract rows: decide_export + export_plan_view HTTP-free.
    Asserted as (code, payload, launch) VALUES: 404 no run; 409 awaiting gate (zero state
    written); 202 + reservation WITHOUT started_at on accept; an UNADOPTED reservation is
    reclaimed (202 recovered_stuck), a LIVE-worker exporting no-ops (200); failed => retry
    accepted, cost restated, stale export_error.txt cleared; zero elements => 409 named;
    missing source => 404 on BOTH surfaces (shared preflight); the plan view 200 carries
    calls/cost and never writes state; the two cost constants are ONE price (drift guard)."""
    import os
    sys.path.insert(0, str(REPO / "frontend"))
    import server  # noqa: PLC0415

    d = _tmp("decide")
    code, payload, launch = server.decide_export(d / "nope")
    a = code == 404 and not launch

    run, _ = make_run_dir(d / "wait", messages=2, gate_state="awaiting_confirmation")
    code2, payload2, launch2 = server.decide_export(run)
    b = (code2 == 409 and "not 'done'" in payload2["error"] and not launch2
         and xl.read_state(run) is None)

    run3, _ = make_run_dir(d / "ok", messages=2, logo_fed=False, products=0)
    pcode, pview = server.export_plan_view(run3)
    c = (pcode == 200 and pview["calls"] == 3 and pview["export_state"] is None
         and xl.read_state(run3) is None)   # the plan view never writes state

    code3, payload3, launch3 = server.decide_export(run3)
    st3 = xl.read_state(run3)
    e = (code3 == 202 and launch3 and payload3["state"] == "exporting"
         and st3["state"] == "exporting" and "started_at" not in st3
         and payload3["cost_stated"] == st3["cost_stated"])
    # an UNADOPTED reservation (no worker ever ran) is verifiably stuck: repeat decide
    # RECLAIMS it (a crash between reservation and launch must not brick the export)
    code4, payload4, launch4 = server.decide_export(run3)
    f = code4 == 202 and launch4 and payload4["recovered_stuck"] is True
    # once a LIVE worker owns the state (started_at + running pid), repeats no-op
    st3 = xl.read_state(run3)
    st3.update(started_at="t", pid=os.getpid())
    xl._write_state(run3, st3)
    code4b, payload4b, launch4b = server.decide_export(run3)
    f2 = code4b == 200 and not launch4b and "no second spend" in payload4b["note"]

    xl._write_state(run3, {"state": "failed", "error": "boom", "created": "t"})
    (run3 / "export_error.txt").write_text("old failure tail", encoding="utf-8")
    code5, payload5, launch5 = server.decide_export(run3)
    g = (code5 == 202 and launch5 and payload5["retry_after_failure"] is True
         and not (run3 / "export_error.txt").exists())   # a fresh attempt clears the marker

    run6, _ = make_run_dir(d / "zero", messages=0, logo_fed=False, products=0)
    code6, payload6, launch6 = server.decide_export(run6)
    h = code6 == 409 and "no enumerable elements" in payload6["error"] and not launch6

    # contract: 'Preconditions identical to the plan endpoint': missing source = 404 on BOTH
    run7, _ = make_run_dir(d / "nosrc", messages=2, logo_fed=False, products=0)
    (run7 / "sign_s1" / "generated.png").unlink()
    pc7, _pv7 = server.export_plan_view(run7)
    dc7, _dp7, dl7 = server.decide_export(run7)
    i = pc7 == 404 and dc7 == 404 and not dl7

    # the drift guard the export_layers comment promises: one price, asserted
    j = server.PER_RUN_COST_USD == xl.PER_IMAGE_USD_DEFAULT

    ok = a and b and c and e and f and f2 and g and h and i and j
    return ok, (f"404={a}; 409-gate={b}; plan-view={c}; 202+reservation={e}; "
                f"stuck-reclaimed={f}; live-noop={f2}; failed-retry+marker-cleared={g}; "
                f"zero-el-409={h}; no-source-404-both={i}; cost-drift-guard={j}")


def check6_form():
    """T006 / FR-008 (the project's form-grep pattern): the export control exists, is an
    explicit type="button" that starts DISABLED until the FREE plan endpoint labels its cost
    (cost_usd + calls templated into the label), the spending POST appears exactly once (only
    inside doExport), doExport is never auto-invoked (handler assignments only), the zip
    download link targets /layers.zip, and the failed state offers an explicit retry."""
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    a = ('id="exportstage"' in html
         and 'id="exportbtn" type="button" disabled' in html)
    b = ("/export/plan" in html
         and "j.cost_usd.toFixed(2)" in html and "j.calls" in html)
    c = html.count('/export`, { method: "POST" }') == 1
    e = "doExport();" not in html and html.count("= doExport") == 2  # two handlers, no auto-call
    f = "/layers.zip" in html and 'id="exportretry"' in html and "renderExport(v)" in html
    ok = a and b and c and e and f
    return ok, (f"button markup={a}; free-plan label={b}; one spending POST={c}; "
                f"never automatic={e}; zip/retry/poll wiring={f}")


def check9_audit_manifest():
    """T007 / FR-006, US3 acceptance 3-4: the manifest is a COMPLETE audit record. Every
    layer entry (ok AND null) carries the exact data-model.md field set (a build that drops
    a keying stat or the prompt fails); ok files = {cutout, preview} both on disk; null
    files = {raw} only; the background entry is model_continued: true with both files; the
    state file carries plan + cost_stated + timestamps, and error ONLY when failed."""
    d = _tmp("audit")
    run, key = make_run_dir(d / "run", messages=1, logo_fed=True, products=1)
    stub = RecordingStub(run, null_ids={"product_1"})
    xl.export_layers(run, key, generate_fn=stub, per_image_usd=0.08)
    man = json.loads((run / xl.MANIFEST_NAME).read_text(encoding="utf-8"))

    base = {"id", "kind", "prompt", "status", "note", "opaque_frac",
            "stray_component_px_dropped", "despilled_px",
            "green_residual_px_in_preview", "bbox", "files"}
    schema_ok = True
    for layer in man["layers"]:
        want = base | ({"text"} if layer["kind"] == "text" else {"ref"})
        if set(layer.keys()) != want:
            schema_ok = False
    ok_layers = [l for l in man["layers"] if l["status"] == "ok"]
    a = (schema_ok and len(man["layers"]) == 3
         and all(set(l["files"]) == {"cutout", "preview"}
                 and Path(l["files"]["cutout"]).is_file()
                 and Path(l["files"]["preview"]).is_file()
                 and l["bbox"] is not None and l["note"] == "" for l in ok_layers))

    null = next(l for l in man["layers"] if l["status"] == "null")
    b = (set(null["files"]) == {"raw"} and Path(null["files"]["raw"]).is_file()
         and null["bbox"] is None and null["note"] != "")

    bg = man["background"]
    c = (bg["model_continued"] is True and bg["prompt"] == xl.background_prompt(
            xl.enumerate_elements(run, key))
         and Path(bg["files"]["image"]).is_file() and Path(bg["files"]["preview"]).is_file()
         and man["source_image"].endswith("generated.png") and man["size"] == "1536x1024")

    st = xl.read_state(run)
    e = (st["state"] == "done" and st["cost_stated"] == "$0.32"
         and st["plan"]["calls"] == 4 and "created" in st and "updated" in st
         and "error" not in st)
    run2, key2 = make_run_dir(d / "fail", messages=1, logo_fed=False, products=0)

    class Boom(RecordingStub):
        def __call__(self, *a, **k):
            raise RuntimeError("boom")

    try:
        xl.export_layers(run2, key2, generate_fn=Boom(run2))
    except RuntimeError:
        pass
    st2 = xl.read_state(run2)
    f = st2["state"] == "failed" and "boom" in st2["error"]

    ok = a and b and c and e and f
    return ok, (f"schema+ok-files={a}; null-packaging={b}; background-flag={c}; "
                f"state-done={e}; state-failed-error={f}")


def _tree_hash(root):
    import hashlib
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def check10_byte_identity():
    """T008 / FR-009, SC-005, SC-006: a run that never exports is BYTE-IDENTICAL after the
    module import, a run_view render, the free plan view, and a refused decide (tree-hash
    proof); its render gains exactly the ONE honest-null export stage; the real pre-016 run
    dirs on disk (if present) render without a single byte changing either."""
    sys.path.insert(0, str(REPO / "frontend"))
    import run_view as rv
    import server

    d = _tmp("byteid")
    run, key = make_run_dir(d / "run", gate_state="awaiting_confirmation")
    h0 = _tree_hash(run)
    v = rv.run_view(run)
    server.export_plan_view(run)        # 409 (gate awaiting): must not write
    server.decide_export(run)           # 409: must not write
    a = _tree_hash(run) == h0
    b = (v["export"]["present"] is False and "opt-in and paid" in v["export"]["note"]
         and not (run / xl.STATE_NAME).exists() and not (run / xl.ZIP_NAME).exists())

    c = True
    real = sorted((REPO / "output").glob("run_*")) if (REPO / "output").is_dir() else []
    for rd in [p for p in real if not (p / xl.STATE_NAME).exists()][-3:]:
        rh = _tree_hash(rd)
        rv.run_view(rd)
        server.export_plan_view(rd)     # free by contract, whatever its state
        if _tree_hash(rd) != rh:
            c = False

    ok = a and b and c
    return ok, (f"fixture tree-hash stable={a}; honest-null-stage-only={b}; "
                f"real pre-016 dirs untouched={c} ({len(real[-3:])} checked)")


CHECKS = [
    ("T001 fixtures: exact #00B140, real artifact names, fed-refs honesty", check0_fixtures),
    ("T002 enumeration + plan: stable ids, fed-logo gate, N+1 pricing", check1_enumeration_and_plan),
    ("T002 prompts + refusals: verbatim/value clauses, named SystemExits", check2_prompts_and_refusals),
    ("T003 real keying: probed alpha + bbox, named honest nulls", check3_real_keying),
    ("T004 orchestrator: N+1 calls, contract refs, progressive manifest, exact zip", check4_orchestrator_and_zip),
    ("T005 state machine: state-before-spend, live no-op vs stuck reclaim, sigint->failed", check5_state_machine),
    ("T005 decide_export + plan view: contract codes/payloads/launch triples", check7_decide_export_and_plan_view),
    ("T006 form: opt-in cost-labeled button, progress rows, zip link, never automatic", check6_form),
    ("T007 audit manifest: full record schema ok AND null, flagged background, state file", check9_audit_manifest),
    ("T008 byte-identity: unexported dirs untouched by render/plan; honest-null stage only", check10_byte_identity),
]


def main():
    print("=" * 78)
    print("test_export_layers.py - falsifiable self-test (016, no paid calls)")
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
