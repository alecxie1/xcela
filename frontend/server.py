#!/usr/bin/env python3
"""frontend/server.py - thin local web server for the single-sign live-runner (feature 004).

Stdlib `http.server` only. Glue, NOT logic: it writes the inputs JSON (`inputs_writer`), shells out
to the EXISTING conductor (`runner` + the thin route) in a background thread so stages can be polled
progressively, and reads the run dir (`run_view`). It never calls gpt-image-2 itself and holds no
generation/register/prompt logic. Single-operator, single-flight, single-sign. The standalone CLI
runs fine with this server absent.

  .venv/bin/python frontend/server.py            # serves http://localhost:8765
"""

import json
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

HERE = Path(__file__).resolve().parent
OUTPUT = REPO_ROOT / "output"
ANSWER_KEYS = REPO_ROOT / "answer_keys"
PER_RUN_COST_USD = 0.08  # single-sign gpt-image-2; labeled on the Run button (FR-009)

_inflight = threading.Lock()  # single-flight: one run at a time


def _brands() -> list:
    return sorted(p.stem for p in ANSWER_KEYS.glob("*.json"))


def _launch_async(run_dir: Path, brand: str, inputs_path: Path, style_notes):
    """Run the conductor (the paid step) in a background thread so /stages can poll progressively.
    We append --out <run_dir> (a FRESH dir per call) so the server can address the run while it runs;
    build_conductor_argv stays --out-free (the faithful CLI default)."""
    argv = runner.build_conductor_argv(inputs_path, brand, style_notes=style_notes) + ["--out", str(run_dir)]

    def _work():
        try:
            subprocess.run(argv, cwd=str(REPO_ROOT))
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
                                    "inflight": _inflight.locked()})
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
        # --- Feature 004: the back-half run ---
        if path != "/run":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        try:
            form = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON body"})
        if not str(form.get("reference_image") or "").strip():
            return self._send(400, {"error": "reference_image is required (v1)"})
        brand = str(form.get("brand") or "").strip()
        if brand not in _brands():
            return self._send(400, {"error": f"unknown brand {brand!r}; choose from {_brands()}"})
        if not _inflight.acquire(blocking=False):
            return self._send(409, {"error": "a run is already in flight (single-flight); wait for it"})
        try:
            run_id = f"run_{brand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            run_dir = OUTPUT / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            inputs_path = inputs_writer.write_inputs(form, run_dir / "inputs.json")
            _launch_async(run_dir, brand, inputs_path, form.get("style_notes") or None)
        except Exception as exc:  # noqa: BLE001
            if _inflight.locked():
                _inflight.release()
            return self._send(400, {"error": f"{type(exc).__name__}: {exc}"})
        return self._send(200, {"run_id": run_id, "per_run_cost_usd": PER_RUN_COST_USD})

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
        if logo and logo[1]:  # save the uploaded logo to a temp file for persist.place_logo
            tmp = OUTPUT / ".onboard_tmp"
            tmp.mkdir(exist_ok=True)
            logo_src = str(tmp / logo[0])
            Path(logo_src).write_bytes(logo[1])
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
