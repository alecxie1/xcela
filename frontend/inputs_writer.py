#!/usr/bin/env python3
"""frontend/inputs_writer.py - single-sign form state -> 002-shape conductor inputs JSON.

Feature 004, the anti-lossy core. Stdlib-only, PURE. Renders the feature-002 inputs contract
(`specs/002-faithful-brief-intake/contracts/inputs-schema.md`), NOT the stale repo-root
`brief_schema.json`. Literal values (messages, mandatory/forbidden elements, occasion, etc.) pass
through VERBATIM - never rephrased, reordered, or inferred (002 FR-003). Exactly ONE `signs[]` entry
(the single-sign invariant). A reference image is REQUIRED in v1.

Note: `brand` is a CLI arg to the conductor, NOT a field of the inputs JSON; `to_inputs` omits it.
"""

import json
from pathlib import Path


def _str_list(v) -> list:
    """Coerce to a list of strings, VERBATIM (each item kept as typed). Blank -> [] (honest null)."""
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def _int(v, default=5) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def to_inputs(form_state: dict) -> dict:
    """Single-sign form state -> the 002-shape inputs dict (one signs[] entry, verbatim).
    Raises ValueError if no reference image (REQUIRED in v1, FR-005)."""
    fs = form_state or {}
    reference = str(fs.get("reference_image") or "").strip()
    if not reference:
        raise ValueError("reference_image is required (v1): the form must supply a reference image")

    vibe_in = fs.get("vibe") or {}
    sign = {
        "id": "s1",
        "messages": _str_list(fs.get("messages")),
        "hero_icon": fs.get("hero_icon") or None,
    }
    # Optional per-sign elements (002 delta): only attach when present.
    if fs.get("sign_mandatory_elements"):
        sign["mandatory_elements"] = _str_list(fs.get("sign_mandatory_elements"))
    if fs.get("sign_forbidden_elements"):
        sign["forbidden_elements"] = _str_list(fs.get("sign_forbidden_elements"))

    out = {
        "asset_type": str(fs.get("asset_type") or "").strip(),
        "render_style": str(fs.get("render_style") or "flat vector"),  # 009: user term, mapped downstream
        "format_size": (str(fs.get("format_size")).strip() or None) if fs.get("format_size") else None,
        "reference_image": reference,
        "reference_relationship": fs.get("reference_relationship") or None,
        "mandatory_elements": _str_list(fs.get("mandatory_elements")),
        "forbidden_elements": _str_list(fs.get("forbidden_elements")),
        "context": {
            "usage_context": str(fs.get("usage_context") or "").strip(),
            "audience": str(fs.get("audience") or "").strip(),
            "vibe": {
                "formality": _int(vibe_in.get("formality")),
                "playfulness": _int(vibe_in.get("playfulness")),
                "warmth": _int(vibe_in.get("warmth")),
            },
            "logo_treatment": fs.get("logo_treatment") or "",
            "brand_strictness": fs.get("brand_strictness") or "",
            "occasion": str(fs.get("occasion") or "").strip(),
        },
        "signs": [sign],
    }
    # Feature 013: product shots (server-saved paths) pass through VERBATIM when present;
    # absent = key absent (pre-013 inputs byte-identical, honest null).
    if fs.get("product_images"):
        out["product_images"] = [str(p) for p in fs["product_images"]]
    return out


def write_inputs(form_state: dict, path) -> Path:
    """Write the single-sign inputs JSON to `path` and return it."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(to_inputs(form_state), ensure_ascii=False, indent=2), encoding="utf-8")
    return out
