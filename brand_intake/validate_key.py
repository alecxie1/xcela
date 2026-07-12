#!/usr/bin/env python3
"""brand_intake/validate_key.py — FAIL-LOUD completeness validation (feature 005, US3).

PURE. The conductor only checks the answer_key EXISTS, never completeness; `scene_author` silently
defaults a missing `logo_path` to the hardcoded taichi logo. This guard FAILS LOUD (raises) BEFORE a
key is saved, so a degraded key never reaches generation. It is distinct from the acknowledgment gate
(which blocks save until every needs_review flag is acted on).
"""

from pathlib import Path


class KeyValidationError(ValueError):
    """A lean answer_key missing a non-negotiable lock. Carries the named reason."""


def validate_lean_key(key: dict) -> None:
    """Raise KeyValidationError with a NAMED reason on: no color with role == 'primary', OR a
    missing / non-existent logo_path file. Returns None on success. Never returns a degraded key."""
    if not isinstance(key, dict):
        raise KeyValidationError("answer_key must be a JSON object")

    items = (((key.get("fields") or {}).get("colors") or {}).get("items")) or []
    primaries = [c for c in items
                 if str(c.get("role", "")).lower() == "primary" and c.get("printed_html")]
    if len(primaries) == 0:
        raise KeyValidationError(
            "no primary color: fields.colors.items[] needs exactly one item with role 'primary' "
            "and a printed_html hex (a blank primary becomes 'primary brand color  stays' in the prompt)")
    if len(primaries) > 1:
        raise KeyValidationError(
            f"more than one primary color ({len(primaries)}): assign exactly one color the 'primary' "
            "role and make the others 'secondary' (the prompt anchors on a single primary)")

    logo = key.get("logo_path")
    if not logo:
        raise KeyValidationError(
            "missing logo_path: the designer must supply a real logo file (there is NO "
            "fallback asset; a keyless brand cannot feed generation)")
    # 017: keys carry brands-relative paths resolved by harness/asset_paths (absolute legacy
    # paths keep working via the resolver's passthrough).
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
    from asset_paths import try_resolve_brand_asset
    if try_resolve_brand_asset(str(logo)) is None:
        raise KeyValidationError(f"logo_path does not resolve to an existing file: {logo!r} "
                                 "(tried absolute, brands-relative, repo-relative)")
