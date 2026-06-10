"""
run_harness.py — the ONLY entrypoint. Zero interactive input.

    python harness/run_harness.py aia

Loads config/<brand>.yaml, assembles N prompts from the frozen template +
answer key (pure function), generates N variants via gpt-image-2 with the
brand logo as reference, and writes everything to a timestamped run folder:

    output/run_<brand>_<timestamp>/
        variant_<id>.png
        prompts.txt
        manifest.json     <- field->slot provenance, config, template hash

No human judgment between command and output. If you want to change anything,
edit the YAML/template and re-run — every intervention is a recorded diff.
"""

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT))

from assemble_prompt import assemble_prompt  # noqa: E402
from generate import generate_variant        # noqa: E402


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main():
    if len(sys.argv) < 2:
        print("usage: python harness/run_harness.py <brand_id>")
        sys.exit(1)
    brand_id = sys.argv[1]

    cfg_path = ROOT / "config" / f"{brand_id}.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    key_path = ROOT / cfg["answer_key"]
    answer_key = json.loads(key_path.read_text(encoding="utf-8"))

    template_path = ROOT / "harness" / "templates" / "poster.txt.j2"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "output" / f"run_{brand_id}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "brand_id": brand_id,
        "timestamp": timestamp,
        "config_file": str(cfg_path),
        "answer_key": str(key_path),
        "template": str(template_path),
        "template_sha256": file_sha(template_path),
        "config_sha256": file_sha(cfg_path),
        "answer_key_sha256": file_sha(key_path),
        "reference_selection": "stubbed/manual (logo path hard-coded in config)",
        "excluded_capabilities": [
            "real-poster reading (brand-behavior analysis) — not coded, deliberately excluded",
            "auto reference-image selection",
            "logo compositing/paste-over (run separately if needed)",
        ],
        "variants": [],
    }

    prompts_log = []
    print(f"\n=== HARNESS RUN: {brand_id} @ {timestamp} ===")
    print(f"template sha: {manifest['template_sha256']}")

    for v in cfg["variants"]:
        vid = v["id"]
        prompt, provenance = assemble_prompt(answer_key, cfg["asset_type"], v["modifier"])
        out_path = run_dir / f"variant_{vid}.png"
        print(f"\n--- variant '{vid}' ---")
        print(f"prompt chars: {len(prompt)}")
        t0 = time.time()
        try:
            meta = generate_variant(prompt, cfg["logo"], str(out_path),
                                    size=cfg.get("size", "1536x1024"),
                                    quality=cfg.get("quality", "high"))
            elapsed = round(time.time() - t0, 1)
            print(f"saved {out_path.name} ({elapsed}s)")
            status = "ok"
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            meta = {"error": f"{type(e).__name__}: {e}"}
            status = "failed"
            print(f"FAILED: {meta['error']}")

        low_conf = [s for s, p in provenance.items() if p.get("needs_review")]
        manifest["variants"].append({
            "id": vid,
            "modifier": v["modifier"],
            "status": status,
            "elapsed_s": elapsed,
            "generation": meta,
            "prompt_chars": len(prompt),
            "low_confidence_slots": low_conf,
            "slot_provenance": provenance,
        })
        prompts_log.append(f"===== variant: {vid} =====\n{prompt}\n")

    (run_dir / "prompts.txt").write_text("\n".join(prompts_log), encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ok = sum(1 for v in manifest["variants"] if v["status"] == "ok")
    print(f"\n=== DONE: {ok}/{len(manifest['variants'])} variants ok ===")
    print(f"run folder: {run_dir}")
    low = set()
    for v in manifest["variants"]:
        low.update(v["low_confidence_slots"])
    if low:
        print(f"⚠️  prompt rests on low-confidence (needs_review) slots: {sorted(low)}")
    print("view: python viewer.py  (read-only)")


if __name__ == "__main__":
    main()
