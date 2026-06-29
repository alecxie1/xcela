#!/usr/bin/env python3
"""brand_intake/persist.py - the shared write home for an onboarded brand (feature 006).

ONE place to "check the id + place the logo + write the key", called by BOTH the 005 CLI
(`intake.py`) and the 006 web gate (`frontend/onboard.py`), so they produce byte-identical artifacts
and the silent-logo / id-collision landmines are guarded in exactly one spot. Stdlib only.

  answer_keys/<brand>.json   committed brand data (tracked)
  brands/<brand>/<logo>      the logo asset (gitignored)
"""

import json
import shutil
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
ANSWER_KEYS = _REPO / "answer_keys"
BRANDS = _REPO / "brands"


def key_path(brand: str) -> Path:
    return ANSWER_KEYS / f"{brand}.json"


def key_exists(brand: str) -> bool:
    """True iff answer_keys/<brand>.json already exists (the id-collision guard, FR-014).
    Both surfaces block a save that would overwrite a committed brand key."""
    return key_path(brand).exists()


def place_logo(brand: str, src) -> str:
    """Copy the logo `src` (a path) under gitignored brands/<brand>/ and return the destination path.
    Returns "" if `src` is falsy / not a file (the caller validate-louds on an empty logo_path).
    NEVER substitutes a default (the taichi-logo landmine)."""
    src = str(src or "").strip()
    if not src or not Path(src).is_file():
        return ""
    brand_dir = BRANDS / brand
    brand_dir.mkdir(parents=True, exist_ok=True)
    dest = brand_dir / Path(src).name
    if Path(src).resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    return str(dest)


def write_key(brand: str, key: dict) -> Path:
    """Write the (already built + validated) lean key to answer_keys/<brand>.json; return the path.
    Callers MUST validate_lean_key BEFORE calling this; write_key does not re-validate."""
    out = key_path(brand)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
