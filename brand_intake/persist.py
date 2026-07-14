#!/usr/bin/env python3
"""brand_intake/persist.py - the shared write home for an onboarded brand (feature 006).

ONE place to "check the id + place the logo + write the key", called by BOTH the 005 CLI
(`intake.py`) and the 006 web gate (`frontend/onboard.py`), so they produce byte-identical artifacts
and the silent-logo / id-collision landmines are guarded in exactly one spot. Stdlib only.

  answer_keys/<brand>.json   RUNTIME brand data (gitignored since 019; demo keys for
  the suites live in tests_support/demo_keys/)
  brands/<brand>/<logo>      the logo asset (gitignored)
"""

import json
import shutil
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "harness"))
from asset_paths import brands_dir, keys_dir  # noqa: E402  (019: BOTH stores are runtime
# state with env-overridable locations; the fixed BRANDS constant was a 017 leftover)


def key_path(brand: str) -> Path:
    return keys_dir() / f"{brand}.json"


def key_exists(brand: str) -> bool:
    """True iff answer_keys/<brand>.json already exists (the id-collision guard, FR-014).
    Both surfaces block a save that would overwrite a committed brand key."""
    return key_path(brand).exists()


def place_logo(brand: str, src) -> str:
    """Copy the logo `src` (a path) under gitignored brands/<brand>/ and return the
    BRANDS-RELATIVE destination "<brand>/<basename>" (017: keys are born portable and
    resolve through harness/asset_paths on any machine; absolute paths in legacy keys keep
    working via the resolver's passthrough). Returns "" if `src` is falsy / not a file (the
    caller validate-louds on an empty logo_path). NEVER substitutes a default (the
    taichi-logo landmine)."""
    src = str(src or "").strip()
    if not src or not Path(src).is_file():
        return ""
    brand_dir = brands_dir() / brand
    brand_dir.mkdir(parents=True, exist_ok=True)
    dest = brand_dir / Path(src).name
    if Path(src).resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    return f"{brand}/{dest.name}"


def write_key(brand: str, key: dict) -> Path:
    """Write the (already built + validated) lean key to answer_keys/<brand>.json; return the path.
    Callers MUST validate_lean_key BEFORE calling this; write_key does not re-validate."""
    out = key_path(brand)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
