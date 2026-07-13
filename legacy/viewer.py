"""
viewer.py — READ-ONLY viewer for harness runs. No inputs, no regenerate button.

    python viewer.py            # serves latest run on http://localhost:8790
    python viewer.py <run_dir>  # serve a specific run
"""

import json
import sys
from pathlib import Path

from flask import Flask, send_from_directory

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"

app = Flask(__name__)


def latest_run() -> Path | None:
    runs = sorted(OUTPUT.glob("run_*"), key=lambda p: p.name, reverse=True)
    return runs[0] if runs else None


RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_run()


@app.route("/")
def index():
    if RUN_DIR is None or not RUN_DIR.exists():
        return "<h1>No harness runs found. Run: python harness/run_harness.py aia</h1>"
    manifest = json.loads((RUN_DIR / "manifest.json").read_text(encoding="utf-8"))
    cards = ""
    for v in manifest["variants"]:
        img = f"variant_{v['id']}.png"
        badge = "✅" if v["status"] == "ok" else "❌"
        low = ", ".join(v.get("low_confidence_slots", [])) or "none"
        cards += f"""
        <div class="card">
          <h3>{badge} {v['id']}</h3>
          <img src="/img/{img}" onerror="this.style.display='none'">
          <p class="mod">{v['modifier']}</p>
          <p class="meta">prompt {v['prompt_chars']} chars · {v['elapsed_s']}s · low-conf slots: {low}</p>
        </div>"""
    return f"""<!doctype html>
<html><head><title>Harness — {manifest['brand_id']} {manifest['timestamp']}</title>
<style>
 body {{ font-family: -apple-system, sans-serif; background:#111; color:#eee; margin:2rem; }}
 .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:1.5rem; }}
 .card {{ background:#1c1c1c; border-radius:12px; padding:1rem; }}
 .card img {{ width:100%; border-radius:8px; }}
 .mod {{ color:#9ad; font-size:.9rem; }}
 .meta {{ color:#888; font-size:.8rem; }}
 .hdr {{ color:#888; font-size:.85rem; }}
</style></head>
<body>
<h1>{manifest['brand_id']} — run {manifest['timestamp']}</h1>
<p class="hdr">template sha {manifest['template_sha256']} · reference: {manifest['reference_selection']}<br>
READ-ONLY viewer. To change anything: edit config/template, re-run from terminal. Every change is a diff.</p>
<div class="grid">{cards}</div>
</body></html>"""


@app.route("/img/<name>")
def img(name):
    return send_from_directory(RUN_DIR, name)


if __name__ == "__main__":
    print(f"serving {RUN_DIR} on http://localhost:8790 (read-only)")
    app.run(port=8790, debug=False)
