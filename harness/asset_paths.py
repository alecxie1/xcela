#!/usr/bin/env python3
"""asset_paths.py — feature 017: portable brand-asset resolution (stdlib-only, import-light).

Committed answer keys carry brands-relative asset paths ("CJXQ/jos cha logo.png") so the repo
runs wherever it is cloned; legacy local keys with absolute paths keep working. Resolution
order (research D1): absolute-and-exists > <brands base>/p > <repo>/p. The brands base is the
env XCELA_BRANDS_DIR, else <repo>/brands (the licensed/IP content provisioned out-of-band).

Never a silent substitute (constitution V): the raising form names EVERY tried path. The old
machine-specific LOGO_PATH fallback this module replaces silently fed a WSL Downloads file.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def brands_dir() -> Path:
    return Path(os.environ.get("XCELA_BRANDS_DIR") or (REPO_ROOT / "brands"))


def _candidates(p: str) -> list:
    path = Path(p)
    if path.is_absolute():
        return [path]
    return [brands_dir() / path, REPO_ROOT / path]


def try_resolve_brand_asset(p: str):
    """Non-raising form: the resolved absolute path string, or None. For callers whose
    honest null is 'this asset is not available' rather than a refusal (e.g. the layered
    export's fed-logo check)."""
    if not p:
        return None
    for cand in _candidates(str(p)):
        if cand.is_file():
            return str(cand)
    return None


def resolve_brand_asset(p: str) -> str:
    """Raising form: refuse LOUDLY, naming every tried path (FR-002)."""
    resolved = try_resolve_brand_asset(p)
    if resolved is None:
        tried = [str(c) for c in _candidates(str(p))] if p else ["(empty logo_path)"]
        raise SystemExit("brand asset not found: tried " + " | ".join(tried) +
                         " (provision the brands dir, or fix the key's logo_path; "
                         "there is NO fallback asset)")
    return resolved
