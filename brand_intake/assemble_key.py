#!/usr/bin/env python3
"""brand_intake/assemble_key.py — build the LEAN answer_key (feature 005, US3).

PURE. Emits ONLY the consumed subset (verified against assemble_thin_prompt + derive_register):
names + fields.colors.items[] (role + printed_html + rgb) + top-level logo_path + provenance.
`typography.styles` is honest-null (absent) in v1. Deliberately omits the graded / VLM / legacy
fields (type/scoring tags, _candidates_rejected/_provenance/_confidence, English fonts, rules,
category, motifs, tone, imagery_style, logo_appearance, slogan).
"""


def _hex_no_hash(h):
    return str(h or "").lstrip("#").upper()


def _color_item(c):
    """A human-verified color (dict with role + hex, optional name_cn/name_en/rgb/needs_review)
    -> the lean colors.items[] shape (printed_html without '#'). VERBATIM; nothing invented."""
    item = {
        "name_cn": c.get("name_cn", ""),
        "name_en": c.get("name_en", ""),
        "role": c.get("role"),
        "printed_html": _hex_no_hash(c.get("hex") or c.get("printed_html")),
    }
    if c.get("rgb") is not None:
        item["rgb"] = list(c["rgb"])
    if c.get("needs_review"):  # a kept-flagged color records its flag (honest record)
        item["needs_review"] = True
    return item


def build_lean_key(brand, brand_en, color_items, logo_path, source_pdf, verified_by, verified_date,
                   styles=None):
    """Assemble the lean answer_key dict. color_items: human-verified colors (role assigned, >=1
    primary expected — enforced by validate_key, not here). styles: OPTIONAL typography.styles map
    (honest-null / absent in v1)."""
    typography = {}
    if styles:
        typography["styles"] = styles
    fields = {
        "brand_name_cn": {"value": brand},
        "brand_name_en": {"value": brand_en},
        "colors": {"items": [_color_item(c) for c in (color_items or [])]},
    }
    if typography:
        fields["typography"] = typography
    return {
        "brand": brand,
        "brand_en": brand_en,
        "logo_path": logo_path,
        "source_pdf": source_pdf,
        "verified_by": verified_by,
        "verified_date": verified_date,
        "fields": fields,
    }


def lean_projection(fat_key, keep_styles=False):
    """Project an EXISTING fat answer_key down to the lean consumed subset (the SC-005 regression
    fixture). keep_styles=True retains fields.typography.styles (proves the OTHER dropped fields are
    zero-effect); keep_styles=False is the real new-brand shape (styles absent -> the font directive
    goes generic, the FR-010 honest-null)."""
    f = fat_key.get("fields", {})
    items = (f.get("colors", {}) or {}).get("items", [])
    lean_items = []
    for c in items:
        lean_items.append(_color_item({
            "name_cn": c.get("name_cn", ""), "name_en": c.get("name_en", ""),
            "role": c.get("role"), "hex": c.get("printed_html"), "rgb": c.get("rgb"),
            "needs_review": c.get("needs_review"),
        }))
    styles = None
    if keep_styles:
        styles = ((f.get("typography") or {}).get("styles"))
    return build_lean_key(
        fat_key.get("brand"),
        fat_key.get("brand_en"),
        # pass the already-lean items straight through (they carry printed_html already)
        [{"name_cn": it["name_cn"], "name_en": it["name_en"], "role": it["role"],
          "hex": it["printed_html"], "rgb": it.get("rgb"), "needs_review": it.get("needs_review")}
         for it in lean_items],
        fat_key.get("logo_path"),
        fat_key.get("source_pdf", ""),
        fat_key.get("verified_by", ""),
        fat_key.get("verified_date", ""),
        styles=styles,
    )
