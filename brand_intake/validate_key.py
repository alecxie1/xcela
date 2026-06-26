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
    has_primary = any(str(c.get("role", "")).lower() == "primary" and c.get("printed_html")
                      for c in items)
    if not has_primary:
        raise KeyValidationError(
            "no primary color: fields.colors.items[] needs at least one item with role 'primary' "
            "and a printed_html hex (a blank primary becomes 'primary brand color  stays' in the prompt)")

    logo = key.get("logo_path")
    if not logo:
        raise KeyValidationError(
            "missing logo_path: the designer must supply a real logo file (scene_author silently "
            "defaults a missing logo to the taichi logo — cross-brand contamination)")
    if not Path(str(logo)).is_file():
        raise KeyValidationError(f"logo_path does not point to an existing file: {logo!r}")
