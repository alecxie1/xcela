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


def _launch_async(run_dir: Path, brand: str, inputs_path: Path, style_notes, phase=None):
    """Run the conductor in a background thread so /stages can poll progressively. We append
    --out <run_dir> so the server can address the run while it runs; build_conductor_argv
    stays --out-free (the faithful CLI default). Feature 015: phase='derive' is the ZERO-SPEND
    first leg every browser run takes; phase='generate' is the confirmed paid leg."""
    argv = runner.build_conductor_argv(inputs_path, brand, style_notes=style_notes,
                                       phase=phase) + ["--out", str(run_dir)]

    def _work():
        try:
            proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
            if proc.returncode != 0:
                # Surface the conductor's fail-loud to the human (§V) instead of hanging silently at
                # 'brief': write an error marker run_view + the UI read. (capture_output buffers the
                # subprocess streams; the conductor still writes its stage artifacts to disk live.)
                err = (proc.stderr or proc.stdout or "").strip()
                tail = "\n".join(err.splitlines()[-12:]) or f"conductor exited {proc.returncode}"
                (run_dir / "run_error.txt").write_text(tail, encoding="utf-8")
        finally:
            _inflight.release()

    threading.Thread(target=_work, daemon=True).start()


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
        # --- Feature 015: the pre-spend gate's confirm (the ONLY route that spends) ---
        if path.startswith("/run/") and path.endswith("/confirm"):
            return self._run_confirm(path[len("/run/"):-len("/confirm")])
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
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a run is already in flight (single-flight); wait"})
        launched = False
        try:
            code, payload, launch = decide_confirm(run_dir, f"${PER_RUN_COST_USD:.2f}")
            if launch:
                _launch_async(run_dir, launch["brand"], launch["inputs_path"],
                              launch["style_notes"], phase="generate")
                launched = True  # _launch_async's worker releases the lock
            return self._send(code, {**payload, "per_run_cost_usd": PER_RUN_COST_USD})
        except Exception as exc:  # noqa: BLE001
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        finally:
            if not launched and _inflight.locked():
                _inflight.release()

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
