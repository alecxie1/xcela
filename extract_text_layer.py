"""
Text-layer-first extractor + router — Step 2 of the re-architecture.

Principle: if a field's value is printed in the PDF text layer, parse it there
(exact, free, no model). Only fall back to a VLM when the text layer is absent
(image-only PDF like 秀才弄) or when a field's value lives in display graphics
rather than the text layer (slogan/category, observed on 太极堡).

Each field comes back as a provenance-wrapped dict (see provenance.py). The
router's job is to decide text_layer vs vision_model PER FIELD and stamp it,
so downstream the needs_review flag routes the uncertain minority to a human
or to the VLM stage.

Scope (proven clean in the text layer): fonts, pattern motifs.
Flagged for VLM fallback (value not reliably in text layer): slogan, category.
"""

import re
import fitz

from provenance import field

# ── Text-layer detection ──────────────────────────────────────────

def text_layer_ratio(pdf_path):
    """Fraction of pages that carry extractable text. ~0 => image-only PDF."""
    doc = fitz.open(pdf_path)
    with_text = sum(1 for p in doc if p.get_text().strip())
    return with_text / max(doc.page_count, 1)

def page_text(pdf_path, pages_1idx):
    doc = fitz.open(pdf_path)
    return {pg: doc[pg - 1].get_text() for pg in pages_1idx}

# ── Field parsers (text layer) ────────────────────────────────────

# CJK font names: 2-6 CJK chars, typically ending in a type-family suffix
_CJK = r'[\u4e00-\u9fff]'
_FONT_SUFFIX = r'(?:体|黑|宋|楷|圆|明朝|旗黑|黑体)'
_CJK_FONT_RE = re.compile(rf'\b({_CJK}{{1,5}}{_FONT_SUFFIX})\b')
# Section-heading phrases that end in a type suffix but are NOT font names.
_FONT_STOPLIST = {"品牌专用字体", "品牌字体库", "标准字体", "辅助字体", "专用字体", "品牌字体"}
_EN_FONT_RE = re.compile(r'\b(Helvetica|Arial|Futura|Times|Garamond|Frutiger|Univers|Gotham|Avenir)\b', re.I)
_WEIGHT_RE = re.compile(r'\b(?:Thin|Light|Regular|Medium|Bold|Black|Heavy|Semibold)\b', re.I)

def parse_fonts(text):
    """Extract CJK display/body fonts + English family from typography page text."""
    cjk = []
    for m in _CJK_FONT_RE.finditer(text):
        tok = m.group(1)
        if tok in _FONT_STOPLIST or "字体" in tok:  # skip section labels like 品牌专用字体
            continue
        if tok not in cjk:
            cjk.append(tok)
    en_matches = _EN_FONT_RE.findall(text)
    en = en_matches[0].title() if en_matches else None
    weights = sorted(set(w.title() for w in _WEIGHT_RE.findall(text)))

    display = field(
        cjk[0] if cjk else None, "text_layer",
        evidence={"all_cjk_fonts": cjk, "note": "first standalone CJK font name = display/headline"},
    )
    body = field(
        cjk[1] if len(cjk) > 1 else None, "text_layer",
        evidence={"detail": "second CJK font name, if any"},
    )
    english = field(
        en, "text_layer",
        evidence={"weights_seen": weights},
    )
    return {"chinese_display": display, "chinese_body": body, "english": english}

def parse_motifs(text, page=None):
    """Motif names cluster as short standalone CJK lines before the 纹样/Pattern header."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    motifs = []
    for ln in lines:
        if "纹样" in ln or "Pattern" in ln.lower() or "pattern" in ln:
            break  # header reached; motif list precedes it
        if re.fullmatch(rf'{_CJK}{{2,3}}', ln):  # 2-3 char CJK token, standalone
            motifs.append(ln)
    return field(
        motifs, "text_layer",
        confidence=0.95 if motifs else 0.3,
        evidence={"page": page, "detail": "short CJK lines preceding 纹样 header"},
    )

# ── Router ────────────────────────────────────────────────────────

# Fields whose VALUE is reliably in the text layer vs. those that need the VLM.
# Observed: 太极堡 prints slogan/category only as display graphics, not text.
TEXT_RELIABLE = {"fonts", "motifs"}
VLM_REQUIRED = {"slogan", "category", "logo", "tone"}

def route_fields(pdf_path, page_groups):
    """
    Decide, per field domain, whether the text layer can serve it.
    Returns a routing plan: {domain: "text_layer" | "vision_model"} plus the
    detected text-layer ratio. If the PDF is image-only, everything routes to VLM.
    """
    ratio = text_layer_ratio(pdf_path)
    image_only = ratio < 0.05
    plan = {}
    for domain in list(TEXT_RELIABLE) + list(VLM_REQUIRED):
        if image_only:
            plan[domain] = "vision_model"
        elif domain in TEXT_RELIABLE:
            plan[domain] = "text_layer"
        else:
            plan[domain] = "vision_model"
    return {"text_layer_ratio": round(ratio, 3), "image_only": image_only, "plan": plan}

# ── Demo ──────────────────────────────────────────────────────────

import json, sys

BRANDS = {
    "taichi": {
        "pdf": "/mnt/c/Users/Alecx/Downloads/太极堡VI-250303.pdf",
        "typography_pages": [22], "pattern_pages": [27],
    },
    "xiucai": {
        "pdf": "/mnt/c/Users/Alecx/Downloads/秀才弄品牌设计方案.pdf",
        "typography_pages": [6, 7], "pattern_pages": [16],
    },
}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "taichi"
    cfg = BRANDS[which]
    route = route_fields(cfg["pdf"], cfg)
    print("ROUTING:", json.dumps(route, ensure_ascii=False, indent=2))

    if not route["image_only"]:
        typo_txt = "\n".join(page_text(cfg["pdf"], cfg["typography_pages"]).values())
        pat_txt = "\n".join(page_text(cfg["pdf"], cfg["pattern_pages"]).values())
        fonts = parse_fonts(typo_txt)
        motifs = parse_motifs(pat_txt, page=cfg["pattern_pages"][0])
        print("\nFONTS:", json.dumps(fonts, ensure_ascii=False, indent=2))
        print("\nMOTIFS:", json.dumps(motifs, ensure_ascii=False, indent=2))
    else:
        print("\n(image-only PDF — fonts/motifs would route to VLM stage)")
