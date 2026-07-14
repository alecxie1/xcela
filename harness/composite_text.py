"""composite_text.py — composite real-font text layers onto an image.

gpt-image-2 renders text as pixels that merely *look* like a font; for
font-compliance (licensed brand typefaces) the text must be drawn with the
actual font file. This tool takes any generated image plus a JSON spec of
text layers (font path, size, color, fractional position, anchor, optional
stroke and letter-spacing) and draws them with Pillow. Brand-agnostic:
everything comes from the spec.

Font resolution + compliance: a layer with font_role/brand resolves through
the answer key's typography block. If the role carries a "library_index"
(built by build_font_index.py from real name tables), the requested family +
weight resolve to a licensed file. Every run writes <out>.compliance.json
recording, per layer, exactly which file was used and how it was resolved:
licensed_exact | licensed_family_other_weight | fallback_system | MISSING.
Silent fallback is the cardinal sin — fallbacks WARN loudly, MISSING fails.

CLI:
  .venv/bin/python harness/composite_text.py --image IN.png --out OUT.png --spec SPEC.json
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Valid PIL vertical-anchor characters (second char of a 2-char anchor).
_VERT_ANCHORS = set("atmsbd")

_REPO_ROOT = Path(__file__).resolve().parent.parent
from asset_paths import keys_dir as _keys_dir  # noqa: E402  (019: runtime state)
_FONT_CACHE = Path.home() / ".cache" / "handyprint-fonts"
_NATIVE_FORMATS = {".otf", ".ttf", ".ttc"}
_CONVERT_FORMATS = {".woff", ".woff2"}

# Weight digits inside a request or a library member key: 85简 / 85W / -85 / 55S all = digits.
_WEIGHT_DIGITS = re.compile(r"(\d{2,3})")
# A 汉仪-prefixed family token inside free text (weight_hint), e.g. 汉仪雅酷黑-85简.
_HANYI_TOKEN = re.compile(r"汉仪[一-鿿A-Za-z]+(?:[-\s]?\d{2,3}[A-Za-z]?简?)?")


def _repo_path(p: str) -> Path:
    """Resolve repo-relative paths (e.g. index 'file' entries) against repo root."""
    path = Path(p)
    return path if path.is_absolute() else _REPO_ROOT / path


def _norm(s: str) -> str:
    return re.sub(r"[\s\-_]", "", s or "").lower()


def _strip_weight_tail(name: str) -> str:
    """'汉仪雅酷黑-85简' -> '汉仪雅酷黑'; '汉仪旗黑-40S' -> '汉仪旗黑'."""
    return re.sub(r"[\s\-]*\d{2,3}\s*[A-Za-z]?简?$", "", name).strip()


def _load_typography_entry(role: str, brand: str) -> tuple[dict, Path]:
    key_path = _keys_dir() / f"{brand}.json"
    if not key_path.exists():
        raise FileNotFoundError(f"answer key not found: {key_path}")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    typo = key.get("typography") or key.get("fields", {}).get("typography")
    if not typo:
        raise KeyError(f"{key_path} has no typography block — run extract_typography.py first")
    entry = typo.get(role)
    if not isinstance(entry, dict) or "name" not in entry:
        roles = [k for k, v in typo.items() if isinstance(v, dict) and "name" in v]
        raise KeyError(f"typography role {role!r} not in {key_path} (available: {roles})")
    return entry, key_path


def _match_family(request_text: str, index: dict) -> str | None:
    """Find which index family the request names. Two passes:
    (1) an index family appears verbatim (normalized) inside the request;
    (2) a 汉仪 token in the request, weight-tail stripped, prefix-matches a
        family (handles VI '汉仪旗黑-40S' vs internal '汉仪旗黑经典版').
    Longest match wins."""
    families = [f for f in index if f != "_unmatched"]
    nt = _norm(request_text)
    hits = [f for f in families if _norm(f) and _norm(f) in nt]
    if hits:
        return max(hits, key=lambda f: len(_norm(f)))
    for token in _HANYI_TOKEN.findall(request_text or ""):
        base = _norm(_strip_weight_tail(token))
        if not base:
            continue
        pref = [f for f in families
                if _norm(f).startswith(base) or base.startswith(_norm(f))]
        if pref:
            return max(pref, key=lambda f: len(_norm(f)))
    return None


def _member_weight_digits(weight_key: str) -> int | None:
    m = _WEIGHT_DIGITS.search(weight_key)
    return int(m.group(1)) if m else None


def _pick_weight(members: dict, weight_req: int | None, hint: str) -> tuple[str, bool]:
    """Choose a member weight-key for the request. Returns (weight_key, exact).
    exact=True when the request's weight digits match the member's, or when no
    specific weight was requested (the register-word choice is then by design)."""
    keys = list(members)
    if weight_req is not None:
        exact = [k for k in keys if _member_weight_digits(k) == weight_req]
        if exact:
            # 85W and 85J can coexist (different library releases) — prefer the
            # W series (the current license delivery) deterministically.
            exact.sort(key=lambda k: (0 if k.upper().endswith("W") else 1, k))
            return exact[0], True
        numbered = [k for k in keys if _member_weight_digits(k) is not None]
        if numbered:
            nearest = min(numbered, key=lambda k: abs(_member_weight_digits(k) - weight_req))
            return nearest, False
        return keys[0], False
    # No numeric weight requested: pick by register words, honestly by design.
    h = (hint or "").lower()
    numbered = sorted((k for k in keys if _member_weight_digits(k) is not None),
                      key=_member_weight_digits)
    if numbered:
        if any(w in h for w in ("heavy", "black", "display", "bold")):
            return numbered[-1], True
        if any(w in h for w in ("light", "thin")):
            return numbered[0], True
        return numbered[len(numbered) // 2], True
    return keys[0], True


def resolve_font(layer: dict) -> tuple[str, dict]:
    """Resolve a text layer to a font file + compliance-manifest entry.

    Order: explicit "font" path (back-compat) → library_index family+weight →
    typography "file" → "file_fallback" (LOUD warning) → hard fail (MISSING).
    """
    manifest = {
        "content": layer.get("content", ""),
        "requested": None,
        "resolved_file": None,
        "resolution": None,
        "weight_requested": None,
        "weight_used": None,
    }
    if layer.get("font"):
        manifest["requested"] = layer["font"]
        manifest["resolved_file"] = layer["font"]
        manifest["resolution"] = "explicit_path"
        return layer["font"], manifest

    role, brand = layer.get("font_role"), layer.get("brand")
    if not role or not brand:
        raise ValueError('text layer needs either "font" or both "font_role" and "brand"')
    entry, key_path = _load_typography_entry(role, brand)
    vi_name = entry.get("name")
    hint = str(layer.get("weight_hint") or "")
    manifest["requested"] = hint or vi_name

    idx_rel = entry.get("library_index")
    if idx_rel:
        idx_path = _repo_path(idx_rel)
        if idx_path.exists():
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            family = _match_family(hint or vi_name or "", index)
            if family:
                m = _WEIGHT_DIGITS.search(hint)
                weight_req = int(m.group(1)) if m else None
                weight_key, exact = _pick_weight(index[family], weight_req, hint)
                member = index[family][weight_key]
                manifest["weight_requested"] = str(weight_req) if weight_req is not None else None
                manifest["weight_used"] = weight_key
                manifest["resolved_file"] = member["file"]
                if exact:
                    manifest["resolution"] = "licensed_exact"
                else:
                    manifest["resolution"] = "licensed_family_other_weight"
                    print(f"  [WARN] font weight substitution: requested {family} weight "
                          f"{weight_req}, library has only {sorted(index[family])} — using "
                          f"{weight_key} ({member['file']})", file=sys.stderr)
                return str(_repo_path(member["file"])), manifest
            print(f"  [WARN] library_index {idx_rel} has no family matching request "
                  f"{(hint or vi_name)!r} — falling through resolution chain", file=sys.stderr)
        else:
            print(f"  [WARN] library_index {idx_rel} not found on disk — falling through",
                  file=sys.stderr)

    if entry.get("file"):
        manifest["resolved_file"] = entry["file"]
        manifest["resolution"] = "licensed_exact"
        return str(_repo_path(entry["file"])), manifest

    if entry.get("file_fallback"):
        fb = entry["file_fallback"]
        manifest["resolved_file"] = fb
        manifest["resolution"] = "fallback_system"
        print(
            "\n".join([
                "  " + "=" * 64,
                "  FONT COMPLIANCE WARNING — SYSTEM FALLBACK IN USE",
                f"    VI mandates : {vi_name} (role {role!r}, VI p{entry.get('source_page')})",
                f"    requested   : {manifest['requested']!r}",
                f"    used instead: {fb}",
                "    This output is NOT font-compliant. Supply the licensed file",
                f"    (typography.{role}.file or library_index) in {key_path}.",
                "  " + "=" * 64,
            ]), file=sys.stderr)
        return fb, manifest

    manifest["resolution"] = "MISSING"
    raise FileNotFoundError(
        f"{brand} mandates {vi_name} (VI p{entry.get('source_page')}) — no library_index "
        f"match, no file, no file_fallback. Supply the font: set typography.{role}.file or "
        f"library_index in {key_path}")


def _resolve_font_path(layer: dict) -> str:
    """Back-compat shim: path only, no manifest."""
    return resolve_font(layer)[0]


def _materialize_font(path: str) -> str:
    """Return a path FreeType can load: otf/ttf/ttc pass through; woff/woff2
    are converted once to ~/.cache/handyprint-fonts/<hash>.ttf via fonttools."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext in _NATIVE_FORMATS:
        return str(p)
    if ext in _CONVERT_FORMATS:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        cached = _FONT_CACHE / f"{digest}.ttf"
        if not cached.exists():
            from fontTools.ttLib import TTFont
            _FONT_CACHE.mkdir(parents=True, exist_ok=True)
            font = TTFont(str(p))
            font.flavor = None  # drop the woff wrapper -> plain sfnt ttf
            font.save(str(cached))
        return str(cached)
    raise ValueError(f"unsupported font format {ext!r} ({path}); "
                     "supported: .otf .ttf .ttc .woff .woff2")


def _draw_with_tracking(draw: ImageDraw.ImageDraw, xy, text: str,
                        font: ImageFont.FreeTypeFont, anchor: str,
                        spacing: float, **kwargs) -> None:
    """Draw text char-by-char with manual advance (PIL has no native tracking)."""
    h_anchor, v_anchor = anchor[0], anchor[1]
    if v_anchor not in _VERT_ANCHORS:
        raise ValueError(f"unsupported anchor {anchor!r}")
    advances = [font.getlength(ch) for ch in text]
    total = sum(advances) + spacing * max(len(text) - 1, 0)
    x, y = xy
    if h_anchor == "m":
        x -= total / 2
    elif h_anchor == "r":
        x -= total
    elif h_anchor != "l":
        raise ValueError(f"unsupported anchor {anchor!r}")
    for ch, adv in zip(text, advances):
        draw.text((x, y), ch, font=font, anchor="l" + v_anchor, **kwargs)
        x += adv + spacing


# --------------------------------------------------------------------------- #
# Fit-to-zone clamp (feature 001, US2 — fixes failure (a): oversized text).
# Composition OWNS the reserved zone; type is sized DOWN to fit it with margin,
# never the reverse. A headline that cannot fit even at the floor is an HONEST
# NULL (constitution §V), never a clipped or overflowing render. This is a real
# fit-within-container constraint (generalizes; not tuned to one image).
# --------------------------------------------------------------------------- #

def _multiline_box_px(lines, font, spacing: int) -> tuple[int, int]:
    """Pixel (w, h) of the rendered multi-line block at this font size."""
    img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(img)
    text = "\n".join(lines)
    l, t, r, b = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, anchor="la")
    return (r - l, b - t)


def fit_text_to_zone(lines, zone_w_px: float, zone_h_px: float, font_path: str,
                     margin_px: int = 24, min_size_px: int = 48, max_size_px: int = 400,
                     ttc_index: int = 0, spacing_frac: float = 0.15) -> dict:
    """Largest font size whose multi-line text block fits inside the zone with margin on every
    edge. Returns a FitResult (contracts/composition-schema.md): fits, final_size_px,
    rendered_wh_px, margin_px, min_size_px. fits=False + final_size_px=None when it cannot fit
    at min_size_px (honest null — caller flags needs_review, never clips)."""
    avail_w = zone_w_px - 2 * margin_px
    avail_h = zone_h_px - 2 * margin_px
    real_path = _materialize_font(font_path)
    lines = [s for s in (lines or []) if s] or [""]

    def measure(size):
        font = ImageFont.truetype(real_path, size, index=ttc_index)
        w, h = _multiline_box_px(lines, font, int(size * spacing_frac))
        return (w <= avail_w and h <= avail_h), (w, h)

    base = {"margin_px": margin_px, "min_size_px": min_size_px}
    if avail_w <= 0 or avail_h <= 0:
        return {"fits": False, "final_size_px": None, "rendered_wh_px": None, **base}
    ok_min, _ = measure(min_size_px)
    if not ok_min:
        return {"fits": False, "final_size_px": None, "rendered_wh_px": None, **base}

    lo, hi, best, best_wh = min_size_px, max_size_px, min_size_px, None
    while lo <= hi:
        mid = (lo + hi) // 2
        ok, wh = measure(mid)
        if ok:
            best, best_wh, lo = mid, wh, mid + 1
        else:
            hi = mid - 1
    return {"fits": True, "final_size_px": best, "rendered_wh_px": list(best_wh), **base}


def fit_text_in_zone_frac(lines, zone_frac: dict, canvas_wh: tuple[int, int], font_path: str,
                          margin_px: int = 24, min_size_px: int = 48, ttc_index: int = 0) -> dict:
    """Convenience wrapper over fit_text_to_zone for a fractional zone on a known canvas.
    Adds rendered_box_frac (the fitted block centered in the zone) when it fits."""
    cw, ch = canvas_wh
    zw, zh = zone_frac["w_frac"] * cw, zone_frac["h_frac"] * ch
    res = fit_text_to_zone(lines, zw, zh, font_path, margin_px=margin_px,
                           min_size_px=min_size_px, ttc_index=ttc_index)
    if res["fits"] and res["rendered_wh_px"]:
        rw, rh = res["rendered_wh_px"]
        cx = zone_frac["x_frac"] + zone_frac["w_frac"] / 2
        cy = zone_frac["y_frac"] + zone_frac["h_frac"] / 2
        res["rendered_box_frac"] = {
            "x_frac": cx - (rw / cw) / 2, "y_frac": cy - (rh / ch) / 2,
            "w_frac": rw / cw, "h_frac": rh / ch,
        }
    else:
        res["rendered_box_frac"] = None
    return res


def composite(image_path: str, spec_path: str, out_path: str) -> Path:
    img = Image.open(image_path).convert("RGBA")
    layers = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    if isinstance(layers, dict):
        layers = [layers]
    draw = ImageDraw.Draw(img)
    w, h = img.size

    manifest = []
    for layer in layers:
        font_path, entry = resolve_font(layer)
        manifest.append(entry)
        font = ImageFont.truetype(_materialize_font(font_path), layer["size_px"],
                                  index=layer.get("ttc_index", 0))
        fx, fy = layer["anchor_frac"]
        xy = (fx * w, fy * h)
        anchor = layer.get("anchor", "mm")
        spacing = layer.get("letter_spacing_px", 0)
        stroke_width = layer.get("stroke_width", 0)
        if stroke_width and layer.get("stroke_is_weight_simulation") \
                and str(entry["resolution"]).startswith("licensed"):
            # stroke was only ever a crutch to fake weight on a single-weight
            # fallback file — a real licensed weight needs no simulation
            stroke_width = 0
        kwargs = {
            "fill": layer.get("color", "#000000"),
            "stroke_width": stroke_width,
            "stroke_fill": layer.get("stroke_color", "#FFFFFF"),
        }
        if spacing:
            _draw_with_tracking(draw, xy, layer["content"], font, anchor,
                                spacing, **kwargs)
        else:
            draw.text(xy, layer["content"], font=font, anchor=anchor, **kwargs)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG")

    manifest_path = Path(str(out) + ".compliance.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"  compliance manifest -> {manifest_path}")
    for m in manifest:
        print(f"    [{m['resolution']}] {m['content']!r}: {m['resolved_file']} "
              f"(weight req={m['weight_requested']} used={m['weight_used']})")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Composite real-font text layers onto an image.")
    ap.add_argument("--image", required=True, help="input image (png/jpg)")
    ap.add_argument("--out", required=True, help="output png path")
    ap.add_argument("--spec", required=True, help="JSON spec: list of text layers")
    args = ap.parse_args()

    out = composite(args.image, args.spec, args.out)
    with Image.open(out) as im:
        print(f"{out.resolve()}  {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
