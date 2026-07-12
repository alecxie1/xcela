#!/usr/bin/env python3
"""export_layers.py — feature 016: layered export of an approved run.

gpt-image-2 cannot emit layers or transparent backgrounds natively (verified 2026-07: flat
PNG/JPEG/WebP only; the gpt-image-1.5 transparency option was removed). Layers are therefore
BUILT: one images.edit call per deterministically enumerated design element repaints ONLY that
element on the proven chroma green (scene_author.CHROMA_KEY_HEX), and the EXISTING strip_chroma
(closed_loop_composite.py, unchanged) keys it to a true RGBA layer; plus ONE background call
(elements removed, flagged model-continued). Deliverable: <run_dir>/layers.zip (RGBA cutouts +
white-bg JPG previews + raw outputs for honest-null layers + audit manifest).

Spend contract (015 semantics): this module never spends unless invoked on a gate-done run in
state absent/failed; export_state.json is written BEFORE the first paid call; exporting/done
no-op. The free surfaces are export_plan() and the CLI --plan-only. Gate/state preconditions
live in the orchestrator and in frontend.server.decide_export; export_plan itself only refuses
missing-source and zero-elements (shared by both).

Elements come from the run's OWN artifacts, never model guessing (constitution IV):
  - one text element per verbatim inputs.json signs[0].messages line;
  - the logo, ONLY if the brand key's logo_path was actually in the run's
    run_manifest generation.reference_image list;
  - one product element per inputs.json product_images entry.

CLI:
  .venv/bin/python harness/export_layers.py --run-dir output/run_X [--brand B] [--plan-only]
"""

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_paths import try_resolve_brand_asset  # noqa: E402  (017: portable asset paths)
from scene_author import CHROMA_KEY_HEX, load_brand  # noqa: E402

EXPORT_DIRNAME = "export"
ZIP_NAME = "layers.zip"
STATE_NAME = "export_state.json"
MANIFEST_NAME = "export_manifest.json"
DEFAULT_SIZE = "1536x1024"
PER_IMAGE_USD_DEFAULT = 0.08  # == frontend/server.py PER_RUN_COST_USD (one run = one image
                              # today; identity asserted by test_export_layers check7)

# Honest-null thresholds on strip_chroma's stats (research.md D4). Deterministic and
# falsifiable: a wrong build that always-oks or always-nulls fails the synthetic fixtures.
NULL_OPAQUE_MAX = 0.95     # kept ~everything: the model ignored the chroma directive
NULL_OPAQUE_MIN = 0.001    # kept ~nothing: an empty frame
NULL_RESIDUAL_MAX = 2000   # key green survives in the preview: dirty key field
# The fourth null: strip_chroma keeps only the largest connected component; when the DROPPED
# strays outnumber the kept pixels (a multi-glyph text line keyed down to one glyph), the
# keying could not do its job and the layer must not ship as an unqualified cutout (FR-005).
# dropped > kept  <=>  the majority of the painted content was erased.


# ---------------------------------------------------------------- pure half

def find_source_image(run_dir: Path, sign_id: str = "s1"):
    """The approved image to decompose: final.png (composited) wins over generated.png.
    None = honest null (nothing to export)."""
    sign = Path(run_dir) / f"sign_{sign_id}"
    for name in ("final.png", "generated.png"):
        p = sign / name
        if p.is_file():
            return p
    return None


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def enumerate_elements(run_dir: Path, brand_key: dict) -> list:
    """PURE, deterministic element list from run artifacts (data-model.md). The background is
    the +1 call, never an element. Order and ids are stable: text_1..N, logo, product_1..N."""
    run_dir = Path(run_dir)
    inputs = _read_json(run_dir / "inputs.json")
    manifest = _read_json(run_dir / "sign_s1" / "run_manifest.json")

    elements = []
    signs = inputs.get("signs") or [{}]
    for i, line in enumerate((signs[0].get("messages") or []), 1):
        elements.append({"id": f"text_{i}", "kind": "text", "text": str(line)})

    fed = [str(r) for r in manifest.get("generation", {}).get("reference_image", [])]
    # 017: keys carry brands-relative paths; the manifest records the RESOLVED absolute
    # path the run fed. Soft form on purpose: an unresolvable logo means this run
    # demonstrably did not feed it, so there is no logo element (honest null, not a refusal).
    logo = try_resolve_brand_asset(brand_key.get("logo_path")) or ""
    if logo and any(logo == r or Path(logo).resolve() == Path(r).resolve() for r in fed):
        elements.append({"id": "logo", "kind": "logo", "ref": logo})

    for i, p in enumerate((inputs.get("product_images") or []), 1):
        elements.append({"id": f"product_{i}", "kind": "product", "ref": str(p)})
    return elements


def _element_desc(element: dict, with_ref_hint: bool = True) -> str:
    """with_ref_hint=True is for ISOLATION prompts, whose calls really do pass the original
    asset as a second reference. The background call passes ONLY the source image, so its
    descriptions must never mention a second supplied image that does not exist."""
    kind = element["kind"]
    if kind == "text":
        return f'the text "{element["text"]}" with its exact typography'
    if kind == "logo":
        # T009-v2 hardening: the first paid export repainted the logo as large brand-name
        # TEXT instead of the lockup. The desc now demands a literal COPY of the asset.
        return ("the brand logo lockup, copied EXACTLY from the SECOND supplied image "
                "(that image IS the logo: reproduce its exact artwork, lettering, colors "
                "and proportions; do NOT redraw it, restyle it, translate it, or "
                "substitute any other brand text for it), at the same position and the "
                "same size it occupies in the finished design"
                if with_ref_hint else "the brand logo")
    if kind == "product":
        return ("the product shown in the SECOND supplied image, as it appears in the "
                "finished design" if with_ref_hint else "the branded product")
    raise ValueError(f"unknown element kind {kind!r}")


def isolation_prompt(element: dict, key_hex: str = CHROMA_KEY_HEX) -> str:
    """One element, exactly as painted, on a pure chroma field (research.md D2)."""
    return (
        "CRITICAL FRAMING, READ FIRST: The FIRST supplied image is a finished design. "
        f"Repaint EXACTLY ONE element from it: {_element_desc(element)}. "
        "Reproduce that element EXACTLY as it appears in the finished design: identical "
        "position on the canvas, identical size, identical colors, styling and details. "
        "Everything else on the canvas must be a perfectly flat, uniform backdrop of pure "
        f"solid {key_hex} (bright chroma green), like a green screen. NOTHING may be drawn "
        "on the green: no shadows, no glow, no reflections, no other elements, no scene. "
        f"The element itself must not contain any color close to {key_hex}. "
        "Keep the exact canvas size."
    )


def background_prompt(elements: list) -> str:
    descs = "; ".join(_element_desc(e, with_ref_hint=False) for e in elements)
    return (
        "The supplied image is a finished design. Repaint it with these foreground elements "
        f"REMOVED: {descs}. Continue the background scene naturally behind where they were, "
        "matching the surrounding textures, colors and lighting. Change NOTHING else: "
        "identical canvas size, identical remaining composition. Add no new elements and "
        "no text."
    )


def export_plan(run_dir: Path, brand_key: dict,
                per_image_usd: float = PER_IMAGE_USD_DEFAULT) -> dict:
    """The FREE pre-spend statement (data-model.md). Refuses loudly (FR-011) on a missing
    source image or zero elements: a background-only export is a paid no-op, never offered."""
    run_dir = Path(run_dir)
    source = find_source_image(run_dir)
    if source is None:
        raise SystemExit(f"export refused: no final.png/generated.png under {run_dir}/sign_s1 "
                         "(nothing to decompose; generate + confirm first)")
    elements = enumerate_elements(run_dir, brand_key)
    if not elements:
        raise SystemExit("export refused: no enumerable elements (no message lines, no fed "
                         "logo, no product images); a layered export would be a paid no-op")
    manifest = _read_json(run_dir / "sign_s1" / "run_manifest.json")
    size = manifest.get("generation", {}).get("size") or DEFAULT_SIZE
    calls = len(elements) + 1
    return {"elements": elements, "calls": calls,
            "per_image_usd": per_image_usd,
            "cost_usd": round(calls * per_image_usd, 2),
            "source_image": str(source), "size": size}


def key_layer(isolated_png: Path, layer_dir: Path, keep_all_components: bool = True) -> dict:
    """Key one isolation output to a layer via the REAL strip_chroma, then judge it honestly
    (research.md D4): a layer is OK only when the keying stats say a clean chroma field
    surrounded real content. On ok: preview.jpg (white-flattened, the JPG deliverable) + the
    opaque bbox (position-drift measurement). On null: a named note; the caller ships the
    raw output, NEVER a cutout (constitution V).

    keep_all_components defaults True here (T009-v2): an element is legitimately MULTI-part
    (a multi-glyph line, a logo lockup), unlike a die-cut sign; the first paid export lost
    'COCONUT"' to the largest-only keep. The die-cut path keeps its own default (False)."""
    from closed_loop_composite import strip_chroma  # lazy: pulls numpy/scipy

    layer_dir = Path(layer_dir)
    layer_dir.mkdir(parents=True, exist_ok=True)
    rec = dict(strip_chroma(isolated_png, layer_dir, key_hex=CHROMA_KEY_HEX,
                            keep_all_components=keep_all_components))

    frac = rec["opaque_frac"]
    residual = rec["green_residual_px_in_preview"]
    if frac > NULL_OPAQUE_MAX:
        rec.update(status="null", bbox=None,
                   note=f"chroma directive ignored: opaque_frac {frac} > {NULL_OPAQUE_MAX} "
                        "(the model painted a full frame, not one element on green)")
        return rec
    if frac < NULL_OPAQUE_MIN:
        rec.update(status="null", bbox=None,
                   note=f"empty frame: opaque_frac {frac} < {NULL_OPAQUE_MIN}")
        return rec
    if residual > NULL_RESIDUAL_MAX:
        rec.update(status="null", bbox=None,
                   note=f"dirty key field: {residual}px green residual > {NULL_RESIDUAL_MAX}")
        return rec
    from PIL import Image
    with Image.open(isolated_png) as _im:
        _w, _h = _im.size
    kept_px = frac * _w * _h
    dropped = rec["stray_component_px_dropped"]
    if dropped > kept_px:   # the majority of the painted content was erased as "strays"
        rec.update(status="null", bbox=None,
                   note=f"largest-component keep dropped the MAJORITY of the content "
                        f"({dropped}px dropped vs ~{int(kept_px)}px kept); a multi-part "
                        "element (detached glyphs/marks) cannot ship as a cutout")
        return rec
    preview_jpg = layer_dir / "preview.jpg"
    Image.open(rec["preview_white"]).convert("RGB").save(preview_jpg, quality=90)
    bbox = Image.open(rec["cutout"]).getchannel("A").getbbox()
    rec.update(status="ok", note="", preview_jpg=str(preview_jpg),
               bbox=list(bbox) if bbox else None)
    return rec


def _brand_from_run(run_dir: Path) -> str:
    meta = Path(run_dir) / "run_meta.json"
    if meta.is_file():
        return str(_read_json(meta).get("brand") or "")
    return ""


# ---------------------------------------------------------------- state + orchestrator

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_state(run_dir: Path):
    p = Path(run_dir) / STATE_NAME
    return _read_json(p) if p.is_file() else None


def _pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
    except (OSError, TypeError, ValueError):
        return False
    return True


def state_blocks_new_export(state) -> bool:
    """The ONE definition of 'a new export must no-op' (the orchestrator, decide_export and
    the server's pre-lock check all call this; encode it nowhere else). done blocks forever.
    exporting blocks only while a LIVE worker owns it (started_at set AND its recorded pid
    is running). A reservation never adopted, or an exporting whose worker died without
    marking failed (kill -9, reboot), does NOT block: those are verifiably-stuck states and
    the retry path reclaims them instead of bricking the run's only export."""
    if not state:
        return False
    s = state.get("state")
    if s == "done":
        return True
    return (s == "exporting" and bool(state.get("started_at"))
            and _pid_alive(state.get("pid")))


def _write_state(run_dir: Path, state: dict) -> dict:
    state["updated"] = _now()
    (Path(run_dir) / STATE_NAME).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def _write_manifest(run_dir: Path, manifest: dict) -> None:
    (Path(run_dir) / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _layer_entry(element: dict, prompt: str, rec: dict, isolated_png: Path) -> dict:
    """One manifest layer record, exactly the data-model.md schema."""
    entry = {"id": element["id"], "kind": element["kind"],
             "prompt": prompt, "status": rec["status"], "note": rec["note"],
             "opaque_frac": rec["opaque_frac"],
             "stray_component_px_dropped": rec["stray_component_px_dropped"],
             "despilled_px": rec["despilled_px"],
             "green_residual_px_in_preview": rec["green_residual_px_in_preview"],
             "bbox": rec.get("bbox")}
    if element["kind"] == "text":
        entry["text"] = element["text"]
    else:
        entry["ref"] = element["ref"]
    if rec["status"] == "ok":
        entry["files"] = {"cutout": rec["cutout"], "preview": rec["preview_jpg"]}
    else:
        entry["files"] = {"raw": str(isolated_png)}   # manual salvage; NEVER a cutout
    return entry


def build_zip(run_dir: Path, manifest: dict) -> Path:
    """layers.zip per data-model.md: manifest + background pair + per ok-layer
    <id>.png + <id>_preview.jpg + per null-layer <id>_raw.png."""
    run_dir = Path(run_dir)
    zip_path = run_dir / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(run_dir / MANIFEST_NAME, MANIFEST_NAME)
        bg = manifest["background"]["files"]
        zf.write(bg["image"], "background.png")
        zf.write(bg["preview"], "background_preview.jpg")
        for layer in manifest["layers"]:
            if layer["status"] == "ok":
                zf.write(layer["files"]["cutout"], f"{layer['id']}.png")
                zf.write(layer["files"]["preview"], f"{layer['id']}_preview.jpg")
            else:
                zf.write(layer["files"]["raw"], f"{layer['id']}_raw.png")
    return zip_path


def export_layers(run_dir: Path, brand_key: dict, generate_fn=None,
                  per_image_usd: float = PER_IMAGE_USD_DEFAULT) -> dict:
    """The orchestrator. 015 spend semantics: no-op on done and on an exporting owned by a
    LIVE worker (zero calls, even mid-flight); retry accepted from failed AND from
    verifiably-stuck exporting states (unadopted reservation, dead worker pid: a crash must
    not brick the run's only export); refuses unless the run's confirm gate reached done;
    export_state.json state="exporting" is on disk BEFORE the first paid call; the manifest
    is appended progressively so a crash leaves a truthful partial; ANY interruption after
    spend starts, KeyboardInterrupt included, = state "failed" + error, fail loud.

    The reservation handoff: frontend.server.decide_export writes state="exporting" WITHOUT
    `started_at` (state-before-launch) and then launches this module as a subprocess; the
    worker ADOPTS that reservation (sets started_at + its pid). Liveness is the recorded
    pid: state_blocks_new_export is the single arbiter."""
    run_dir = Path(run_dir)

    try:
        state = read_state(run_dir)
    except Exception:
        raise SystemExit("export refused: export_state.json exists but is unreadable; "
                         "delete it to start over") from None
    if state_blocks_new_export(state):
        return {"state": state["state"],
                "note": "already exporting/exported; no second spend"}

    if state and state.get("state") == "exporting":   # reservation or stuck: reclaim it
        plan = state.get("plan") or export_plan(run_dir, brand_key,
                                                per_image_usd=per_image_usd)
        state.update(plan=plan, started_at=_now(), pid=os.getpid())
        state = _write_state(run_dir, state)
    else:                                             # absent or failed: the full CLI path
        gate_path = run_dir / "gate_state.json"
        gate = _read_json(gate_path).get("state") if gate_path.is_file() else None
        if gate != "done":
            raise SystemExit(f"export refused: gate_state is {gate!r}, not 'done' "
                             "(export decomposes a confirmed, generated, judged run)")
        plan = export_plan(run_dir, brand_key, per_image_usd=per_image_usd)
        state = _write_state(run_dir, {"state": "exporting", "plan": plan,
                                       "cost_stated": f"${plan['cost_usd']:.2f}",
                                       "created": _now(), "started_at": _now(),
                                       "pid": os.getpid()})    # BEFORE any paid call

    manifest = {"source_image": plan["source_image"], "size": plan["size"],
                "layers": [], "background": None}
    try:
        # EVERYTHING that can fail after the started_at write lives inside this try, the
        # lazy paid-client import and the first manifest write included: a failure anywhere
        # past this point must land in "failed", never strand "exporting".
        if generate_fn is None:
            from generate import generate_variant as generate_fn  # lazy: the paid client
        _write_manifest(run_dir, manifest)
        source = plan["source_image"]
        for element in plan["elements"]:
            prompt = isolation_prompt(element)
            refs = [source] + ([element["ref"]] if element["kind"] in ("logo", "product")
                               else [])
            layer_dir = run_dir / EXPORT_DIRNAME / element["id"]
            layer_dir.mkdir(parents=True, exist_ok=True)
            isolated = layer_dir / "isolated.png"
            generate_fn(prompt, refs, str(isolated), size=plan["size"])
            rec = key_layer(isolated, layer_dir)
            manifest["layers"].append(_layer_entry(element, prompt, rec, isolated))
            _write_manifest(run_dir, manifest)   # progressive: crash = truthful partial

        bg_prompt = background_prompt(plan["elements"])
        bg_dir = run_dir / EXPORT_DIRNAME / "background"
        bg_dir.mkdir(parents=True, exist_ok=True)
        bg_png = bg_dir / "background.png"
        generate_fn(bg_prompt, [source], str(bg_png), size=plan["size"])
        from PIL import Image
        bg_jpg = bg_dir / "background_preview.jpg"
        Image.open(bg_png).convert("RGB").save(bg_jpg, quality=90)
        manifest["background"] = {"prompt": bg_prompt, "model_continued": True,
                                  "files": {"image": str(bg_png), "preview": str(bg_jpg)}}
        _write_manifest(run_dir, manifest)

        zip_path = build_zip(run_dir, manifest)
        state.update(state="done")
        _write_state(run_dir, state)
        return {"state": "done", "zip": str(zip_path),
                "layers": [{"id": l["id"], "status": l["status"]} for l in manifest["layers"]]}
    except BaseException as exc:   # incl. KeyboardInterrupt/SystemExit: NEVER strand "exporting"
        state.update(state="failed", error=f"{type(exc).__name__}: {exc}")
        _write_state(run_dir, state)
        raise


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="016 layered export (chroma repaint per element)")
    ap.add_argument("--run-dir", required=True, help="the run directory to export")
    ap.add_argument("--brand", default=None,
                    help="brand id (default: run_meta.json of the run dir)")
    ap.add_argument("--plan-only", action="store_true",
                    help="print the export plan JSON and exit: ZERO paid calls")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise SystemExit(f"export refused: run dir {run_dir} does not exist")
    brand = args.brand or _brand_from_run(run_dir)
    if not brand:
        raise SystemExit("export refused: no --brand and no run_meta.json brand")
    brand_key = load_brand(brand)

    if args.plan_only:
        plan = export_plan(run_dir, brand_key)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    result = export_layers(run_dir, brand_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
