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


CHECKS = [
    ("T001 fixtures: exact #00B140, real artifact names, fed-refs honesty", check0_fixtures),
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
