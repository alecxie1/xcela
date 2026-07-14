#!/usr/bin/env python3
"""frontend/brand_manager.py - the brand database's PURE half (feature 019).

View / edit / delete the runtime brand keys (asset_paths.keys_dir). HTTP-free and
unit-testable like onboard.py; the server routes are thin glue. Every write goes through
the SAME validate_lean_key gate onboarding uses (fail loud; a refused edit leaves the file
byte-identical); deletes remove the KEY only and say so honestly (assets under
brands/<brand>/ stay on disk). The wizard's key_exists collision guard is untouched: an
UPDATE here is a deliberate overwrite of an existing brand, a different verb.
"""

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "harness"))
sys.path.insert(0, str(_REPO / "brand_intake"))
from asset_paths import keys_dir, try_resolve_brand_asset  # noqa: E402
import persist  # noqa: E402
from validate_key import KeyValidationError, validate_lean_key  # noqa: E402

# gpt-image-2 accepts exactly these (the Kevin "只能识别JPG" report, answered with a guard)
ALLOWED_LOGO_EXT = (".png", ".jpg", ".jpeg", ".webp")
# magic bytes for the cheap header sniff (extension lies are caught loudly)
_MAGIC = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpg", b"RIFF": "webp"}


def validate_logo_format(filename: str, data: bytes):
    """None when acceptable; a NAMED reason string otherwise. Shared by the onboarding
    wizard and the manager's logo replace (ONE guard, never a generation-time surprise)."""
    ext = Path(str(filename or "")).suffix.lower()
    if ext not in ALLOWED_LOGO_EXT:
        return (f"unsupported logo format {ext or '(none)'}: gpt-image-2 accepts only "
                f"{'/'.join(ALLOWED_LOGO_EXT)} (convert SVG/AI/PDF logos to PNG first)")
    if not data or not any(data[:8].startswith(m) for m in _MAGIC):
        return ("the file's content does not look like PNG/JPG/WebP (header check); "
                "re-export the logo as PNG and try again")
    return None


def list_brands_detail() -> list:
    """Every brand in the runtime database with the fields the manager renders. Tolerant:
    a corrupt key file lists with an error note instead of crashing the page."""
    out = []
    for p in sorted(keys_dir().glob("*.json")):
        try:
            key = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            out.append({"brand": p.stem, "error": "key file unreadable (corrupt JSON)"})
            continue
        fields = key.get("fields") or {}
        colors = (((fields.get("colors") or {}).get("items")) or [])
        out.append({
            "brand": p.stem,
            "name_cn": ((fields.get("brand_name_cn") or {}).get("value")
                        if isinstance(fields.get("brand_name_cn"), dict)
                        else fields.get("brand_name_cn")),
            "name_en": ((fields.get("brand_name_en") or {}).get("value")
                        if isinstance(fields.get("brand_name_en"), dict)
                        else fields.get("brand_name_en")),
            "colors": [{"hex": ("#" + str(c.get("printed_html", "")).lstrip("#")),
                        "role": c.get("role")} for c in colors],
            "logo_path": key.get("logo_path"),
            "logo_resolved": try_resolve_brand_asset(key.get("logo_path")) is not None,
            "verified_by": key.get("verified_by"),
            "verified_date": key.get("verified_date"),
        })
    return out


def _load_key(brand: str):
    p = keys_dir() / f"{brand}.json"
    if not p.is_file():
        return None, None
    return p, json.loads(p.read_text(encoding="utf-8"))


def update_brand(brand: str, payload: dict):
    """Apply name/color edits, gated by validate_lean_key. Returns (code, body). A refusal
    leaves the key file byte-identical (validated on a COPY before any write)."""
    p, key = _load_key(brand)
    if key is None:
        return 404, {"error": f"no brand {brand!r} in the database"}
    edited = json.loads(json.dumps(key))   # deep copy: validate before touching the file
    fields = edited.setdefault("fields", {})
    if "name_cn" in payload:
        fields["brand_name_cn"] = {"value": str(payload["name_cn"] or "").strip()}
    if "name_en" in payload:
        fields["brand_name_en"] = {"value": str(payload["name_en"] or "").strip()}
    if "colors" in payload:
        if not isinstance(payload["colors"], list):
            return 400, {"error": "colors must be a list of {hex, role}"}
        items = []
        for c in payload["colors"]:
            hexv = str(c.get("hex", "")).lstrip("#").strip()
            items.append({"printed_html": hexv, "role": c.get("role"),
                          "rgb": None, "name_cn": c.get("name_cn", ""),
                          "name_en": c.get("name_en", "")})
        fields.setdefault("colors", {})["items"] = items
    try:
        validate_lean_key(edited)
    except KeyValidationError as exc:
        return 400, {"error": str(exc)}   # file untouched
    persist.write_key(brand, edited)
    return 200, {"ok": True, "brand": brand}


def replace_logo(brand: str, filename: str, data: bytes):
    """Format-guarded logo replacement: place the file, point the key at it, validate."""
    p, key = _load_key(brand)
    if key is None:
        return 404, {"error": f"no brand {brand!r} in the database"}
    reason = validate_logo_format(filename, data)
    if reason:
        return 400, {"error": reason}
    import shutil
    import tempfile
    # stage under the ORIGINAL basename so place_logo preserves the human-readable name
    staging = Path(tempfile.mkdtemp(prefix="logo_stage_"))
    tmp = staging / Path(filename).name
    tmp.write_bytes(data)
    rel = persist.place_logo(brand, str(tmp))
    shutil.rmtree(staging, ignore_errors=True)
    if not rel:
        return 400, {"error": "logo file could not be placed"}
    edited = json.loads(json.dumps(key))
    edited["logo_path"] = rel
    try:
        validate_lean_key(edited)
    except KeyValidationError as exc:
        return 400, {"error": str(exc)}
    persist.write_key(brand, edited)
    return 200, {"ok": True, "brand": brand, "logo_path": rel}


def delete_brand(brand: str, confirm: str):
    """Delete the KEY file (the brand disappears from every list); assets under
    brands/<brand>/ deliberately remain on disk (stated in the response). The UI requires
    retyping the brand id; the same confirmation is enforced here (never trust the UI)."""
    if confirm != brand:
        return 400, {"error": f"confirmation mismatch: type the brand id {brand!r} exactly"}
    p, key = _load_key(brand)
    if key is None:
        return 404, {"error": f"no brand {brand!r} in the database"}
    p.unlink()
    return 200, {"ok": True, "deleted": brand,
                 "note": f"key removed; asset files under brands/{brand}/ remain on disk"}
