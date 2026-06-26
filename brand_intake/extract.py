#!/usr/bin/env python3
"""brand_intake/extract.py — thin REUSE wrappers over the proven extractors (feature 005, US2).

Do NOT reinvent color/text extraction. `extract_brand_colors` delegates to
`extract_colors.extract_colors` (OCR caption + pixel-cluster reconcile -> hex records with
`needs_review`; the human assigns ROLE later at the verify gate). `read_brand_names` pulls CN/EN
CANDIDATES from the name page(s) text layer -- the brand name is a human-confirmed field (you cannot
reliably know which CJK token IS the brand name), so these are candidates the gate confirms, not an
inference. Honest-null + a note on empty (never green-on-empty).
"""

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
from extract_colors import extract_colors  # noqa: E402
from extract_text_layer import page_text  # noqa: E402

_CJK_RUN = re.compile(r"[一-鿿]{2,8}")
_EN_RUN = re.compile(r"\b[A-Z][A-Za-z]{1,}\b")  # Title/upper Latin tokens, len >= 2


def extract_brand_colors(pdf_path, color_pages_1idx):
    """Reuse extract_colors on the CONFIRMED 1-indexed color pages. Returns
    {records: [...], note: str|None}. records carry value.hex + needs_review; role is unset
    (assigned by the human at the verify gate). Honest-null note when nothing is found."""
    records = extract_colors(str(pdf_path), list(color_pages_1idx))
    note = None
    if not records:
        note = (f"no color records extracted from pages {list(color_pages_1idx)} "
                "(no hex/RGB token read); confirm the page numbers or expect a degraded path")
    return {"records": records, "note": note}


def read_brand_names(pdf_path, name_pages_1idx):
    """Pull CN/EN brand-name CANDIDATES from the name page(s) text layer (verbatim, not inferred).
    The human confirms the actual brand / brand_en at the verify gate. Honest-null note when the
    page text is empty."""
    text = "\n".join(page_text(str(pdf_path), list(name_pages_1idx)).values())
    cn = []
    for m in _CJK_RUN.finditer(text):
        tok = m.group(0)
        if tok not in cn:
            cn.append(tok)
    en = []
    for m in _EN_RUN.finditer(text):
        tok = m.group(0)
        if tok not in en:
            en.append(tok)
    note = None
    if not text.strip():
        note = (f"no text on pages {list(name_pages_1idx)} (image-only?); supply the brand names "
                "at the verify gate")
    return {"cn_candidates": cn, "en_candidates": en, "raw": text, "note": note}
