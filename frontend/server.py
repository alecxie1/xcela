#!/usr/bin/env python3
"""frontend/server.py - thin local web server for the single-sign live-runner (feature 004).

Stdlib `http.server` only. Glue, NOT logic: it writes the inputs JSON (`inputs_writer`), shells out
to the EXISTING conductor (`runner` + the thin route) in a background thread so stages can be polled
progressively, and reads the run dir (`run_view`). It never calls gpt-image-2 itself and holds no
generation/register/prompt logic. Single-operator, single-flight, single-sign. The standalone CLI
runs fine with this server absent.

  .venv/bin/python frontend/server.py            # serves http://localhost:8765
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import inputs_writer  # noqa: E402
import run_view as run_view_mod  # noqa: E402
import runner  # noqa: E402
import onboard as onboard_mod  # noqa: E402  (feature 006: the web onboarding wizard)
import multipart  # noqa: E402  (feature 006: stdlib multipart upload parsing)
import uploads  # noqa: E402  (feature 007: the shared save-upload home, 004 reference + 006 logo)
sys.path.insert(0, str(REPO_ROOT / "harness"))
import export_layers as export_mod  # noqa: E402  (feature 016: the layered exporter)

HERE = Path(__file__).resolve().parent
OUTPUT = REPO_ROOT / "output"
ANSWER_KEYS = REPO_ROOT / "answer_keys"
PER_RUN_COST_USD = 0.08  # single-sign gpt-image-2; labeled on the Run button (FR-009)
MAX_PRODUCT_IMAGES = 6   # feature 013: mirrors conductor.MAX_PRODUCT_IMAGES (drift-guarded by test)

_inflight = threading.Lock()  # single-flight: one run at a time


def _brands() -> list:
    return sorted(p.stem for p in ANSWER_KEYS.glob("*.json"))


def parse_run_form(body: bytes, content_type: str):
    """Parse a multipart /run body into (form_dict, reference_tuple, product_tuples). HTTP-free, so
    it is unit-testable without launching a run (feature 007). The brief rides as ONE JSON field
    `form` (mirroring /onboard/save's `verified` field); the STYLE reference is the `reference` file
    part; product shots (feature 013, optional) ride as DISTINCT parts product_1..product_N (the
    parser is last-wins per part name, so same-named parts would silently drop files). Raises
    ValueError (fail loud) on a missing / empty reference file, invalid form JSON, or more than
    MAX_PRODUCT_IMAGES product parts (over-cap is a visible error, never a silent truncation)."""
    parsed = multipart.parse_multipart(body, content_type)
    try:
        form = json.loads(parsed["fields"].get("form") or "{}")
    except json.JSONDecodeError:
        raise ValueError("invalid 'form' JSON field")
    ref = parsed["files"].get("reference")
    if not ref or not ref[1]:
        raise ValueError("a reference image is required (v1)")
    prod_keys = sorted((k for k in parsed["files"] if re.fullmatch(r"product_\d+", k)),
                       key=lambda k: int(k.split("_")[1]))
    products = [parsed["files"][k] for k in prod_keys if parsed["files"][k][1]]
    if len(products) > MAX_PRODUCT_IMAGES:
        raise ValueError(f"at most {MAX_PRODUCT_IMAGES} product shots are supported "
                         f"(got {len(products)}); remove some and rerun")
    return form, ref, products


def write_run_inputs(form: dict, reference, run_dir: Path, products=None) -> Path:
    """Save the uploaded reference INTO run_dir (preserving its extension), inject that saved path as
    `reference_image`, and write the 002-shape inputs JSON (feature 007). HTTP-free, testable. The
    conductor / CLI input contract is UNCHANGED: `reference_image` stays a path on disk (only its
    SOURCE changes, a server-saved upload instead of a designer-typed string). Feature 013: product
    shots (optional) save through the SAME shared upload home as product_<i>.<ext> and their paths
    ride as form["product_images"]; zero products = no key (pre-013 inputs byte-identical)."""
    ext = os.path.splitext(reference[0])[1]
    ref_path = uploads.save_upload(reference, run_dir, name="reference" + ext)
    form["reference_image"] = ref_path
    saved = [uploads.save_upload(p, run_dir, name=f"product_{i}{os.path.splitext(p[0])[1]}")
             for i, p in enumerate(products or [], 1)]
    if saved:
        form["product_images"] = saved
    return inputs_writer.write_inputs(form, run_dir / "inputs.json")


def decide_confirm(run_dir: Path, cost_label: str):
    """HTTP-free confirm decision (feature 015, contracts/server-routes.md; unit-testable).
    Returns (status_code, payload, launch): `launch` is None (nothing to start) or
    {brand, inputs_path, style_notes} for a --phase generate run. When launch is set, the
    gate state has ALREADY been written to 'confirmed' (state-before-launch: a crashed
    launch never leaves an unguarded awaiting gate, and a repeat confirm no-ops)."""
    gs_path = Path(run_dir) / "gate_state.json"
    if not Path(run_dir).exists() or not gs_path.exists():
        return 404, {"error": "no gated run here (pre-015 runs have no pre-spend gate)"}, None
    try:
        gs = json.loads(gs_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 409, {"error": "gate_state.json unreadable; re-run the derive phase"}, None
    state = gs.get("state")
    if state in ("confirmed", "generating", "done"):
        return 200, {"ok": True, "state": state,
                     "note": "already confirmed; no second spend"}, None
    if state != "awaiting_confirmation":
        return 409, {"error": f"gate state {state!r} does not accept confirm"}, None
    prompt_path = Path(run_dir) / "sign_s1" / "final_prompt.txt"
    if not prompt_path.exists():
        return 409, {"error": "no assembled prompt to confirm; the derive phase has not "
                              "finished (or failed, see run_error.txt)"}, None
    meta_path = Path(run_dir) / "run_meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 409, {"error": "run_meta.json missing/unreadable; cannot reproduce the "
                              "derive argv for the generate phase"}, None
    now = datetime.now().isoformat(timespec="seconds")
    gs["state"] = "confirmed"
    gs["updated"] = now
    gs["confirmation"] = {
        "confirmed_prompt_sha": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
        "cost_stated": cost_label,
        "confirmed_at": now,
    }
    gs_path.write_text(json.dumps(gs, ensure_ascii=False, indent=2), encoding="utf-8")
    launch = {"brand": meta["brand"], "inputs_path": Path(run_dir) / "inputs.json",
              "style_notes": meta.get("style_notes")}
    return 200, {"ok": True, "state": "confirmed", "cost_stated": cost_label}, launch


def _resolve_option_writes(option: dict, provided):
    """015 (US2): an option's writes, with slider-template values ('<int 0-10>') filled from
    the request. Raises ValueError (fail loud, US2 scenario 3) on missing/out-of-range
    numbers; a plain option ignores `provided` entirely (only shipped values are writable)."""
    w = option["writes"]
    val = w["value"]
    if isinstance(val, dict) and any(isinstance(v, str) and v.startswith("<int") for v in val.values()):
        if not isinstance(provided, dict):
            raise ValueError('this answer needs numeric values, e.g. {"formality": 4, "playfulness": 6}')
        filled = {}
        for k in val:
            v = provided.get(k)
            if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 10:
                raise ValueError(f"{k} must be an integer 0-10 (got {v!r})")
            filled[k] = v
        return {"field": w["field"], "value": filled}
    return {"field": w["field"], "value": val}


def decide_answer(run_dir: Path, payload: dict):
    """HTTP-free answer decision (feature 015, contracts/server-routes.md; unit-testable).
    Returns (status_code, body, relaunch): `relaunch` is None or {brand, inputs_path,
    style_notes} for the FREE --phase derive re-run. On success the write-back has been
    applied to the run dir's inputs.json and the provenance appended to gate_state.json;
    every refusal leaves both files untouched (the previous derivation stands)."""
    run_dir = Path(run_dir)
    gs_path = run_dir / "gate_state.json"
    if not gs_path.exists():
        return 404, {"error": "no gated run here (pre-015 runs have no pre-spend gate)"}, None
    try:
        gs = json.loads(gs_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 409, {"error": "gate_state.json unreadable; re-run the derive phase"}, None
    if gs.get("state") != "awaiting_confirmation":
        return 409, {"error": f"gate state {gs.get('state')!r} does not accept answers"}, None
    try:
        assumptions = json.loads((run_dir / "assumptions.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 409, {"error": "assumptions.json missing/unreadable; re-run the derive phase"}, None
    rec = next((r for r in assumptions if r.get("id") == payload.get("assumption_id")), None)
    if rec is None:
        return 400, {"error": f"unknown assumption_id {payload.get('assumption_id')!r}; "
                              f"this gate has: {[r.get('id') for r in assumptions]}"}, None
    opt = next((o for o in rec.get("options", []) if o.get("label") == payload.get("label")), None)
    if opt is None:
        return 400, {"error": f"unknown option {payload.get('label')!r} for "
                              f"{rec['id']}; offered: {[o.get('label') for o in rec.get('options', [])]}"}, None
    try:
        writes = _resolve_option_writes(opt, payload.get("value"))
    except ValueError as exc:
        return 400, {"error": str(exc)}, None
    inputs_path = run_dir / "inputs.json"
    try:
        inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
        meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 409, {"error": "inputs.json/run_meta.json missing; cannot apply the answer"}, None
    inputs_writer.apply_answer(inputs, writes["field"], writes["value"])
    inputs_path.write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
    now = datetime.now().isoformat(timespec="seconds")
    gs.setdefault("answers_applied", []).append({
        "assumption_id": rec["id"], "chosen_label": opt["label"], "written": writes, "at": now})
    gs["updated"] = now
    gs_path.write_text(json.dumps(gs, ensure_ascii=False, indent=2), encoding="utf-8")
    return 200, {"ok": True, "applied": writes}, {
        "brand": meta["brand"], "inputs_path": inputs_path,
        "style_notes": meta.get("style_notes")}


def _gate_state(run_dir: Path):
    p = Path(run_dir) / "gate_state.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("state")
    except Exception:  # noqa: BLE001
        return None


def _read_export_state(run_dir: Path):
    """(state, error) wrapper over export_mod.read_state: the module fails LOUD on a corrupt
    state file (a silent None would let the orchestrator re-spend), the server instead turns
    it into a named refusal. Returns (None, msg) on corruption."""
    try:
        return export_mod.read_state(run_dir), None
    except Exception:  # noqa: BLE001
        return None, ("export_state.json exists but is unreadable; fix or delete it "
                      "to export this run again")


def _export_preflight(run_dir: Path, per_image_usd: float):
    """Feature 016: the ONE precondition chain the free plan view AND the spending decide
    share (contract: 'Preconditions identical to the plan endpoint'). Returns
    ((status_code, payload), None) on refusal or (None, plan) on success; NEVER raises
    (a corrupt brand key / run artifact is a named 409, not a socket abort)."""
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        return (404, {"error": "no such run"}), None
    gate = _gate_state(run_dir)
    if gate != "done":
        return (409, {"error": "export needs a generated, judged image: the run's gate is "
                               f"{gate!r}, not 'done'"}), None
    if export_mod.find_source_image(run_dir) is None:
        return (404, {"error": "no final.png/generated.png in this run "
                               "(nothing to decompose)"}), None
    brand = export_mod._brand_from_run(run_dir)
    if not brand:
        return (409, {"error": "run_meta.json missing/unreadable; cannot resolve "
                               "the brand"}), None
    try:
        plan = export_mod.export_plan(run_dir, export_mod.load_brand(brand),
                                      per_image_usd=per_image_usd)
    except SystemExit as exc:   # zero elements: a layered export would be a paid no-op
        return (409, {"error": str(exc)}), None
    except Exception as exc:    # missing/corrupt brand key or run artifact: named, not a 500
        return (409, {"error": f"cannot plan the export: {type(exc).__name__}: {exc}"}), None
    return None, plan


def export_plan_view(run_dir: Path, per_image_usd: float = PER_RUN_COST_USD):
    """Feature 016: the FREE pre-spend plan for the export button label (contracts/
    http-and-cli.md). HTTP-free, zero paid calls, zero writes. Returns (status_code, payload)."""
    err, plan = _export_preflight(run_dir, per_image_usd)
    if err:
        return err
    state, serr = _read_export_state(run_dir)
    payload = {**plan, "export_state": state.get("state") if state else None}
    if serr:
        payload["state_note"] = serr
    return 200, payload


def decide_export(run_dir: Path, per_image_usd: float = PER_RUN_COST_USD):
    """Feature 016: HTTP-free export decision, mirroring decide_confirm. Returns
    (status_code, payload, launch: bool). When launch is True, export_state.json has
    ALREADY been written as an "exporting" RESERVATION (state-before-launch, WITHOUT
    started_at: the launched worker adopts it, recording its pid). No-ops with no second
    spend while a LIVE worker owns the state (export_mod.state_blocks_new_export, the one
    arbiter); retry is accepted from failed AND from verifiably-stuck exporting states
    (unadopted reservation, dead worker pid): a crash must not brick the run's only export."""
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        return 404, {"error": "no such run"}, False
    state, serr = _read_export_state(run_dir)
    if serr:
        return 409, {"error": serr}, False
    if export_mod.state_blocks_new_export(state):
        return 200, {"ok": True, "state": state["state"],
                     "note": "already exporting/exported; no second spend"}, False
    err, plan = _export_preflight(run_dir, per_image_usd)
    if err:
        return (*err, False)
    cost = f"${plan['cost_usd']:.2f}"
    retrying = bool(state and state.get("state") == "failed")
    recovered = bool(state and state.get("state") == "exporting")  # stuck state reclaimed
    (run_dir / "export_error.txt").unlink(missing_ok=True)  # a fresh attempt clears the old marker
    export_mod._write_state(run_dir, {"state": "exporting", "plan": plan,
                                      "cost_stated": cost,
                                      "created": datetime.now().isoformat(timespec="seconds")})
    return 202, {"ok": True, "state": "exporting", "cost_stated": cost,
                 "calls": plan["calls"], "retry_after_failure": retrying,
                 "recovered_stuck": recovered}, True


def _spawn_worker(argv: list, run_dir: Path, error_name: str = "run_error.txt"):
    """The ONE background-subprocess worker (015 generation and 016 export both launch
    through it): crash isolation via subprocess, the fail-loud tail written to error_name
    (§V: surface it, never hang silently), the _inflight release owned by the worker.
    016 uses error_name='export_error.txt' so an export failure NEVER masquerades as a
    run failure (run_error.txt is the conductor's marker and poisons the run view)."""

    def _work():
        try:
            proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip()
                tail = "\n".join(err.splitlines()[-12:]) or f"worker exited {proc.returncode}"
                (run_dir / error_name).write_text(tail, encoding="utf-8")
        finally:
            _inflight.release()

    threading.Thread(target=_work, daemon=True).start()


def _launch_export_async(run_dir: Path):
    """Feature 016: the exporter subprocess. Failures land in export_error.txt (NOT
    run_error.txt) and in export_state.json (the module marks failed itself when it got
    far enough; an earlier death leaves an unstarted reservation the retry path reclaims)."""
    _spawn_worker([sys.executable, "harness/export_layers.py", "--run-dir", str(run_dir)],
                  run_dir, error_name="export_error.txt")


def _launch_async(run_dir: Path, brand: str, inputs_path: Path, style_notes, phase=None):
    """Run the conductor via the shared worker so /stages can poll progressively. We append
    --out <run_dir> so the server can address the run while it runs; build_conductor_argv
    stays --out-free (the faithful CLI default). Feature 015: phase='derive' is the ZERO-SPEND
    first leg every browser run takes; phase='generate' is the confirmed paid leg."""
    argv = runner.build_conductor_argv(inputs_path, brand, style_notes=style_notes,
                                       phase=phase) + ["--out", str(run_dir)]
    _spawn_worker(argv, run_dir)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            return self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/onboard":
            return self._send(200, (HERE / "onboard.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/brands":
            return self._send(200, {"brands": _brands(), "per_run_cost_usd": PER_RUN_COST_USD})
        if path.startswith("/run/") and path.endswith("/stages"):
            run_id = path[len("/run/"):-len("/stages")]
            return self._send(200, {**run_view_mod.run_view(OUTPUT / run_id),
                                    "inflight": _inflight.locked(),
                                    "per_run_cost_usd": PER_RUN_COST_USD})
        if path.startswith("/run/") and path.endswith("/image"):
            run_id = path[len("/run/"):-len("/image")]
            img = OUTPUT / run_id / "sign_s1" / "generated.png"
            if not img.exists():
                return self._send(404, {"error": "image not ready"})
            return self._send(200, img.read_bytes(), "image/png")
        # --- Feature 016: the layered exporter's free surfaces ---
        if path.startswith("/run/") and path.endswith("/export/plan"):
            run_id = path[len("/run/"):-len("/export/plan")]
            code, payload = export_plan_view(OUTPUT / run_id)
            return self._send(code, payload)
        if path.startswith("/run/") and path.endswith("/layers.zip"):
            run_id = path[len("/run/"):-len("/layers.zip")]
            zp = OUTPUT / run_id / export_mod.ZIP_NAME
            state, serr = _read_export_state(OUTPUT / run_id)
            if serr or not zp.is_file() or not state or state.get("state") != "done":
                return self._send(404, {"error": serr or "layers.zip not ready (export not done)"})
            return self._send(200, zp.read_bytes(), "application/zip")
        return self._send(404, {"error": "not found"})

    def _read_body(self):
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        # --- Feature 006: onboarding wizard routes ---
        if path == "/onboard/upload":
            return self._onboard_upload()
        if path.startswith("/onboard/") and path.endswith("/extract"):
            return self._onboard_extract(path[len("/onboard/"):-len("/extract")])
        if path.startswith("/onboard/") and path.endswith("/save"):
            return self._onboard_save(path[len("/onboard/"):-len("/save")])
        # --- Feature 015: the pre-spend gate's routes ---
        if path.startswith("/run/") and path.endswith("/confirm"):
            return self._run_confirm(path[len("/run/"):-len("/confirm")])
        if path.startswith("/run/") and path.endswith("/answer"):
            return self._run_answer(path[len("/run/"):-len("/answer")])
        # --- Feature 016: the layered exporter's spending route ---
        if path.startswith("/run/") and path.endswith("/export"):
            return self._run_export(path[len("/run/"):-len("/export")])
        # --- Feature 004: the back-half run ---
        if path != "/run":
            return self._send(404, {"error": "not found"})
        # Feature 007: the reference is a real file UPLOAD now (multipart), not a typed path. Parse +
        # require the reference here; a missing reference fails loud BEFORE any run dir / single-flight.
        try:
            form, reference, products = parse_run_form(self._read_body(),
                                                       self.headers.get("Content-Type", ""))
        except ValueError as exc:
            return self._send(400, {"error": str(exc)})  # fail loud; no run launched (FR-005)
        brand = str(form.get("brand") or "").strip()
        if brand not in _brands():
            return self._send(400, {"error": f"unknown brand {brand!r}; choose from {_brands()}"})
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a run is already in flight (single-flight); wait for it"})
        try:
            run_id = f"run_{brand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            run_dir = OUTPUT / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            inputs_path = write_run_inputs(form, reference, run_dir,  # saves the uploads into the run dir
                                           products=products)
            style_notes = form.get("style_notes") or None
            # Feature 015: persist what the confirm leg needs to reproduce the derive argv
            # exactly (style_notes is an argv-only channel; a mismatch would trip the
            # --verify-prompt drift guard).
            (run_dir / "run_meta.json").write_text(json.dumps(
                {"brand": brand, "style_notes": style_notes}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            # Feature 015: every browser run starts with the ZERO-SPEND derive phase; the paid
            # generate phase runs only through POST /run/<id>/confirm (nudge reruns included).
            _launch_async(run_dir, brand, inputs_path, style_notes, phase="derive")
        except Exception as exc:  # noqa: BLE001
            if _inflight.locked():
                _inflight.release()
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        return self._send(200, {"run_id": run_id, "per_run_cost_usd": PER_RUN_COST_USD})

    def _run_answer(self, run_id):
        """Feature 015 (US2): apply ONE gate answer, then re-derive FREE (--phase derive on
        the SAME run dir: calibration.json present means the vision calls are skipped)."""
        try:
            payload = json.loads(self._read_body() or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON body"})
        run_dir = OUTPUT / run_id
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a run is already in flight (single-flight); wait"})
        launched = False
        try:
            code, body, relaunch = decide_answer(run_dir, payload)
            if relaunch:
                _launch_async(run_dir, relaunch["brand"], relaunch["inputs_path"],
                              relaunch["style_notes"], phase="derive")
                launched = True  # the worker releases the lock
            return self._send(code, body)
        except Exception as exc:  # noqa: BLE001
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        finally:
            if not launched and _inflight.locked():
                _inflight.release()

    def _locked_spend(self, decide_fn, launch_fn, wrap=None):
        """The ONE acquire/decide/launch/release scaffold both spending handlers use
        (015 confirm and 016 export): single-flight 409, launched-flag lock handoff to the
        worker, fail-loud 400, conditional release. Encoding it once keeps the two spend
        routes' locking discipline identical by construction."""
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a run is already in flight (single-flight); wait"})
        launched = False
        try:
            code, payload, launch = decide_fn()
            if launch:
                launch_fn(launch)   # the worker releases the lock
                launched = True
            return self._send(code, wrap(payload) if wrap else payload)
        except Exception as exc:  # noqa: BLE001
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        finally:
            if not launched and _inflight.locked():
                _inflight.release()

    def _run_export(self, run_id):
        """Feature 016 (FR-007): opt-in, cost-stated layered export with the 015 spend
        semantics. The no-op states answer BEFORE the single-flight lock (via the shared
        state_blocks_new_export arbiter), so a repeat click mid-export gets the graceful
        no-op, not a 409; a corrupt state file is a named 409, never a socket abort."""
        run_dir = OUTPUT / run_id
        state, serr = _read_export_state(run_dir) if run_dir.is_dir() else (None, None)
        if serr:
            return self._send(409, {"error": serr})
        if export_mod.state_blocks_new_export(state):
            return self._send(200, {"ok": True, "state": state["state"],
                                    "note": "already exporting/exported; no second spend"})
        return self._locked_spend(lambda: decide_export(run_dir),
                                  lambda _launch: _launch_export_async(run_dir))

    def _run_confirm(self, run_id):
        """Feature 015 (FR-012): idempotent, cost-stated confirm. State is written BEFORE the
        launch; a repeat confirm sees confirmed/generating/done and never spends twice. The
        no-op states answer BEFORE the single-flight lock, so a repeat confirm during the
        generation itself gets the graceful no-op, not a 409."""
        run_dir = OUTPUT / run_id
        gs_path = run_dir / "gate_state.json"
        if gs_path.exists():
            try:
                state = json.loads(gs_path.read_text(encoding="utf-8")).get("state")
            except Exception:  # noqa: BLE001
                state = None
            if state in ("confirmed", "generating", "done"):
                return self._send(200, {"ok": True, "state": state,
                                        "note": "already confirmed; no second spend",
                                        "per_run_cost_usd": PER_RUN_COST_USD})
        return self._locked_spend(
            lambda: decide_confirm(run_dir, f"${PER_RUN_COST_USD:.2f}"),
            lambda launch: _launch_async(run_dir, launch["brand"], launch["inputs_path"],
                                         launch["style_notes"], phase="generate"),
            wrap=lambda payload: {**payload, "per_run_cost_usd": PER_RUN_COST_USD})

    # --- Feature 006 onboarding handlers (thin glue over onboard.py; no model, never intake.main) ---

    def _onboard_upload(self):
        parsed = multipart.parse_multipart(self._read_body(), self.headers.get("Content-Type", ""))
        pdf = parsed["files"].get("pdf")
        if not pdf or not pdf[1]:
            return self._send(400, {"error": "a PDF file is required"})
        try:
            res = onboard_mod.start_draft(pdf[1])
        except Exception as exc:  # noqa: BLE001
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        return self._send(200, {"draft_id": res["draft_id"], "suggestions": res["suggestions"]})

    def _onboard_extract(self, draft_id):
        try:
            pages = json.loads(self._read_body() or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON body"})
        try:
            res = onboard_mod.extract_draft(draft_id, pages)
        except onboard_mod.OnboardError as exc:
            return self._send(400, {"error": str(exc)})
        return self._send(200, res)  # {locks, names} or {block}

    def _onboard_save(self, draft_id):
        parsed = multipart.parse_multipart(self._read_body(), self.headers.get("Content-Type", ""))
        try:
            verified = json.loads(parsed["fields"].get("verified") or "{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid 'verified' JSON field"})
        logo = parsed["files"].get("logo")
        logo_src = ""
        if logo and logo[1]:  # land the uploaded logo on disk for persist.place_logo (feature 007: the
            logo_src = uploads.save_upload(logo, OUTPUT / ".onboard_tmp")  # ONE shared save-upload home
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a job is already in flight (single-flight); wait for it"})
        try:
            res = onboard_mod.save_draft(draft_id, verified, logo_src)
        except onboard_mod.OnboardError as exc:
            return self._send(400, {"error": str(exc)})  # fail loud, no file written
        except Exception as exc:  # noqa: BLE001
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        finally:
            if _inflight.locked():
                _inflight.release()
        return self._send(200, {**res, "message": "this brand is now available in the live-runner"})

    def log_message(self, *args):  # quiet
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    OUTPUT.mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"live-runner on http://localhost:{port}  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
