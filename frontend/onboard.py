#!/usr/bin/env python3
"""frontend/onboard.py - the web onboarding wizard orchestration (feature 006).

Composes the proven 005 PURE modules across the 3 wizard steps over a TRANSIENT draft dir. Callable
WITHOUT HTTP (bytes/paths in, dicts out) so it is unit-testable. NEVER calls intake.main(), never
reimplements extraction/validation/the gate logic, never calls a model. Writes the committed key +
logo (via brand_intake/persist) ONLY on a successful save_draft; the draft is discarded on save (the
clarified transient-draft / discard-on-abandon).

  start_draft(pdf_bytes)                 -> {draft_id, suggestions, _pdf_path, _draft_dir}
  extract_draft(draft_id, pages)         -> {locks, names} | {block}
  save_draft(draft_id, verified, logo)   -> {brand, key_path}   (raises on any fail; no write)
"""

import shutil
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "brand_intake"))
import page_finder
import extract as extract_mod
import assemble_key
import validate_key
import persist
from intake import unacknowledged_flags, finalize_items  # the 005 gate helpers (pure)

_DRAFT_ROOT = Path(tempfile.gettempdir()) / "handyprint_onboard_drafts"


class OnboardError(ValueError):
    """A wizard step that must fail loud (bad draft id, zero colors, validation, id collision)."""


def _draft_dir(draft_id: str) -> Path:
    return _DRAFT_ROOT / draft_id


# ---- Step 1: upload -> draft + page suggestions ----

def start_draft(pdf_bytes: bytes) -> dict:
    """Create a transient draft dir, save the uploaded PDF to it, suggest the spec pages.
    No committed artifact is written."""
    if not pdf_bytes:
        raise OnboardError("no PDF uploaded")
    draft_id = uuid.uuid4().hex
    d = _draft_dir(draft_id)
    d.mkdir(parents=True, exist_ok=True)
    pdf_path = d / "source.pdf"
    pdf_path.write_bytes(pdf_bytes)
    return {
        "draft_id": draft_id,
        "suggestions": page_finder.suggest_pages(str(pdf_path)),
        "_pdf_path": str(pdf_path),
        "_draft_dir": str(d),
    }


# ---- Step 2: confirmed pages -> extracted locks (or a block) ----

def extract_draft(draft_id: str, confirmed_pages: dict) -> dict:
    """Run the proven extractors on the confirmed pages. ZERO colors -> {block} (return to
    page-confirm; never fabricate a color or open an empty gate). Else {locks, names}."""
    d = _draft_dir(draft_id)
    pdf = d / "source.pdf"
    if not pdf.is_file():
        raise OnboardError(f"unknown or expired draft: {draft_id}")
    color_pages = confirmed_pages.get("color") or []
    name_pages = confirmed_pages.get("name") or []
    col = extract_mod.extract_brand_colors(str(pdf), color_pages)
    records = col["records"]
    if not records:
        return {"block": "no colors found on these pages; go back and correct the color page(s)",
                "note": col["note"]}
    locks = [{"hex": r["value"]["hex"], "rgb": r["value"].get("rgb"),
              "needs_review": r.get("needs_review", False), "role": None,
              "name_cn": "", "name_en": "", "evidence": r.get("evidence")} for r in records]
    names = extract_mod.read_brand_names(str(pdf), name_pages)
    return {"locks": locks, "names": names}


# ---- Step 3: verified locks + logo -> validate-loud + save ----

def save_draft(draft_id: str, verified: dict, logo_src) -> dict:
    """Build + validate-loud + write the lean key, place the logo, discard the draft. Raises
    OnboardError (no write) on: unacknowledged flag, id collision, or validation failure
    (no primary / missing-or-unreal logo)."""
    d = _draft_dir(draft_id)
    pdf = d / "source.pdf"
    if not pdf.is_file():
        raise OnboardError(f"unknown or expired draft: {draft_id}")

    brand = str(verified.get("brand") or "").strip()
    if not brand:
        raise OnboardError("no brand id")
    if persist.key_exists(brand):
        raise OnboardError(f"answer_keys/{brand}.json already exists; choose a new brand id "
                           "(editing an existing key is out of scope)")

    items = verified.get("colors") or []
    blocked = unacknowledged_flags(items)
    if blocked:
        raise OnboardError(f"{len(blocked)} color flag(s) not acknowledged "
                           "(confirm / edit / keep-flagged each before saving)")

    logo_dest = persist.place_logo(brand, logo_src)
    key = assemble_key.build_lean_key(
        verified.get("brand_cn") or brand, verified.get("brand_en") or "",
        finalize_items(items), logo_dest, "uploaded.pdf",
        verified.get("verified_by") or "web", date.today().isoformat())

    validate_key.validate_lean_key(key)  # FAILS LOUD on no primary / missing-or-unreal logo

    path = persist.write_key(brand, key)
    discard_draft(draft_id)
    return {"brand": brand, "key_path": str(path)}


def discard_draft(draft_id: str) -> None:
    """Remove the transient draft dir (on save, or on abandon)."""
    shutil.rmtree(_draft_dir(draft_id), ignore_errors=True)
