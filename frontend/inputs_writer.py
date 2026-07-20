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


def to_edit_inputs(form_state: dict) -> dict:
    """Feature 023 (改图): edit-mode form state -> the edit inputs dict. The instruction and
    region pass through VERBATIM (the 012 lossless principle; no rephrasing, no expansion).
    `signs` keeps the single-sign shape with EMPTY messages (legal in edit mode only) so the
    sign_s1/ run-dir layout and every existing consumer work unchanged. Fail-loud on a
    missing base image / blank instruction / malformed region (never a silent default)."""
    fs = form_state or {}
    base = str(fs.get("base_image") or "").strip()
    if not base:
        raise ValueError("base_image is required (edit mode): upload the image to change")
    instruction = str(fs.get("edit_instruction") or "").strip()
    if not instruction:
        raise ValueError("edit_instruction is required (edit mode): state the change verbatim")
    out = {
        "mode": "edit",
        "base_image": base,
        "edit_instruction": instruction,
        "signs": [{"id": "s1", "messages": []}],
    }
    region = fs.get("edit_region")
    if region:
        try:
            r = {k: float(region[k]) for k in ("x", "y", "w", "h")}
        except (KeyError, TypeError, ValueError):
            raise ValueError("edit_region must be {x, y, w, h} normalized numbers (0..1)")
        if not (0 <= r["x"] < 1 and 0 <= r["y"] < 1 and 0 < r["w"] <= 1 and 0 < r["h"] <= 1
                and r["x"] + r["w"] <= 1 and r["y"] + r["h"] <= 1):
            raise ValueError("edit_region out of bounds: x,y in [0,1), w,h in (0,1], "
                             "x+w and y+h at most 1")
        out["edit_region"] = r
    if fs.get("product_images"):
        out["product_images"] = [str(p) for p in fs["product_images"]]
    return out


def write_inputs(form_state: dict, path) -> Path:
    """Write the single-sign inputs JSON to `path` and return it. Feature 023: an edit-mode
    form state (mode == "edit") writes the edit contract; anything else writes the 002 shape
    via to_inputs, which never emits a `mode` key (the design-lane byte-identity pin)."""
    fs = form_state or {}
    builder = to_edit_inputs if fs.get("mode") == "edit" else to_inputs
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(builder(form_state), ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def apply_answer(inputs: dict, field: str, value):
    """Feature 015 (pre-spend gate): apply ONE gate write-back into an inputs dict. `field`
    is a dotted path into the 002-shape inputs ("context.usage_context", "context.vibe",
    "render_style", "format_size", "reference_relationship"). Dict values MERGE into an
    existing dict leaf (context.vibe keeps warmth); everything else is set verbatim.
    Mutates and returns `inputs` (the caller persists)."""
    parts = str(field).split(".")
    node = inputs
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    leaf = parts[-1]
    if isinstance(value, dict) and isinstance(node.get(leaf), dict):
        node[leaf].update(value)
    else:
        node[leaf] = value
    return inputs
