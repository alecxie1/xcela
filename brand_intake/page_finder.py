#!/usr/bin/env python3
"""brand_intake/page_finder.py — deterministic, model-free page-finding heuristic (feature 005, US1).

Replaces the extractors' hardcoded `BRANDS` page dicts with discovery the human CONFIRMS. Scans each
page's TEXT LAYER and ranks: the color page is the one with REAL hex/RGB tokens (not a page that
merely says "color"); font pages match the CJK/EN font-name patterns; brand-name pages are the early
title pages. It REUSES the extractors' own regexes so a suggestion matches what the extractor parses.

All page numbers are 1-INDEXED (the `extract_colors.render_page` footgun: `doc[page_no_1idx - 1]`).
PURE + model-free (the v3 auto-detect disease is rejected; the human confirms the suggestions).
"""

import re
import sys
from pathlib import Path

import fitz

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
# Reuse the EXACT token shapes the extractors use, so page-finding agrees with extraction.
from extract_colors import _HEX_RE, _RGB_RE  # noqa: E402
from extract_text_layer import _CJK_FONT_RE, _EN_FONT_RE, _FONT_STOPLIST, text_layer_ratio  # noqa: E402


def _hex_token_count(text: str) -> int:
    """Count REAL color tokens: explicit hex (with a letter, the extractor's rule) + RGB triples.
    A page that merely contains the word 'color' with no such token scores 0."""
    n = 0
    for m in _HEX_RE.finditer(text):
        if re.search(r"[A-Fa-f]", m.group(1)):  # explicit hex must carry a letter (digits = RGB/CMYK)
            n += 1
    n += len(_RGB_RE.findall(text))
    return n


def _font_token_count(text: str) -> int:
    """Count font-name tokens (CJK display fonts + known EN families), minus section labels."""
    n = 0
    for m in _CJK_FONT_RE.finditer(text):
        tok = m.group(1)
        if tok in _FONT_STOPLIST or "字体" in tok:
            continue
        n += 1
    n += len(_EN_FONT_RE.findall(text))
    return n


def suggest_pages(pdf_path) -> dict:
    """Suggest 1-indexed spec pages from the text layer. The human confirms / corrects.

    Returns {color: [1-idx, ...], fonts: [1-idx, ...], brand_name: [1-idx, ...], text_layer_ratio}.
    Color/font lists are ranked by token count (most tokens first). brand_name is the early page(s).
    """
    doc = fitz.open(str(pdf_path))
    color_scores, font_scores = [], []
    for i in range(doc.page_count):
        page_1idx = i + 1  # 1-INDEXED (the footgun)
        text = doc[i].get_text()
        hc = _hex_token_count(text)
        fc = _font_token_count(text)
        if hc > 0:
            color_scores.append((page_1idx, hc))
        if fc > 0:
            font_scores.append((page_1idx, fc))
    page_count = doc.page_count
    doc.close()

    color = [p for p, _ in sorted(color_scores, key=lambda x: (-x[1], x[0]))]
    fonts = [p for p, _ in sorted(font_scores, key=lambda x: (-x[1], x[0]))]
    # brand name + EN name appear up front; suggest the first page (and page 2 if present).
    brand_name = [p for p in (1, 2) if p <= page_count]

    return {
        "color": color,
        "fonts": fonts,
        "brand_name": brand_name,
        "text_layer_ratio": round(text_layer_ratio(str(pdf_path)), 3),
    }
