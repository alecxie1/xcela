"""extract_typography.py — deterministic typography extraction from a VI PDF text layer.

Walks pages whose text mentions 字体/typeface/font, extracts candidate font
names with regex + role-header heuristics, and emits the answer-key
"typography" block. No LLM calls; ambiguous hits land in _candidates_rejected
for human review instead of being guessed or silently dropped.

CLI: .venv/bin/python extract_typography.py --pdf <VI.pdf> --out <typography.json>
"""

import argparse
import json
import re

import fitz

KEYWORDS = ("字体", "Typeface", "typeface", "Font", "font")

# Latin specimen lines: "AIA Everest Condensed Medium", "Arial Bold Italic" ...
_WEIGHTS = r"(?:Thin|Light|Regular|Medium|Bold|Black|Heavy|Semibold|Extra ?Bold|Italic|Condensed|Oblique|Book)"
_LATIN_WEIGHTED_RE = re.compile(rf"\b([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*?)((?:[ -]{_WEIGHTS})+)\b")
# Latin names embedded in CJK prose near 字体 wording: "...使用Noto Sans字体..."
_LATIN_PROSE_RE = re.compile(r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)")
_LATIN_STOPLIST = {"AIA", "OTF", "Web", "UX", "DDS", "HanyiFonts", "P", "Pantone"}
# section-label words: "Brand Typeface", "Typography" are headers, not font names
_LATIN_LABEL_RE = re.compile(r"\b(?:Typefaces?|Fonts?|Typography)\b", re.I)
# CJK: vendor-prefixed names (汉仪旗黑, 锦华明朝体 ...) and X款字体 library names.
_CJK_LIB_RE = re.compile(r"((?:[一-鿿]+)\s*\d+\s*款字体)")
_CJK_VENDOR_RE = re.compile(
    r"((?:汉仪|方正|思源|华文|锦华)[一-鿿]{1,8}(?:[-－–]?\s*\d+\s*[A-Za-zSs简繁]*)?)")
# Role pages are found by counting role-header phrases per page (a section's
# own title shows up once as the page title AND once in the repeated nav
# sidebar, so its count is strictly higher on its own page).
_ROLE_RES = {
    "english_primary": re.compile(r"主要字体|primary\s+typeface", re.I),
    "english_fallback": re.compile(r"系统字体|system\s+(?:typeface|font)|无法使用", re.I),
    "digital": re.compile(r"数字媒体|数字平台|digital", re.I),
}
# Usage rules kept verbatim: sentence mentions type AND a prescriptive marker.
_RULE_MARK_RE = re.compile(r"不建议|只有在|应选择|不得|禁止|避免")
_RULE_TOPIC_RE = re.compile(r"字体|标题|正文")
_LICENSE_RE = re.compile(r"许可协议|期限为")
_RULE_MAX_LEN = 120  # longer "sentences" are usually license boilerplate + glued specimen text


def _sentences(text):
    """Reflow wrapped lines, then split on 。 (the text layer wraps sentences)."""
    return [s.strip() for s in text.replace("\n", "").split("。") if s.strip()]


def _latin_families(text, rejected):
    """Accepted Latin families on a page (weighted-specimen or prose-near-字体)."""
    found = []
    for m in _LATIN_WEIGHTED_RE.finditer(text):
        fam = m.group(1).strip()
        if fam.isupper() or fam in _LATIN_STOPLIST:
            rejected.append({"candidate": m.group(0),
                             "reason": "all-caps specimen row or stoplisted token"})
            continue
        found.append(fam)
    for line in text.splitlines():
        if "字体" not in line:
            continue
        for m in _LATIN_PROSE_RE.finditer(line):
            tok = m.group(1).strip()
            if tok.isupper() or tok in _LATIN_STOPLIST or (" " not in tok and len(tok) < 4):
                continue
            if _LATIN_LABEL_RE.search(tok):
                continue
            found.append(re.sub(rf"(?:[ -]{_WEIGHTS})+$", "", tok))
    # frequency-ranked unique list
    return sorted(set(found), key=lambda f: -found.count(f))


def extract(pdf_path):
    doc = fitz.open(pdf_path)
    pages = {i + 1: doc[i].get_text() for i in range(doc.page_count)
             if any(k in doc[i].get_text() for k in KEYWORDS)}
    rejected, rules, confidence = [], [], {}

    def role_page(role):
        scores = {pg: len(_ROLE_RES[role].findall(t)) for pg, t in pages.items()}
        best = max(scores, key=scores.get, default=None)
        return (best, scores[best]) if best and scores[best] else (None, 0)

    def license_note(pg):
        # line-based: license facts print as short standalone lines
        for line in pages.get(pg, "").splitlines():
            if _LICENSE_RE.search(line):
                return line.split("。")[0].strip() + "。"
        return None

    out = {}
    ep_pg, ep_score = role_page("english_primary")
    ep_fams = _latin_families(pages.get(ep_pg, ""), rejected) if ep_pg else []
    ep_name = ep_fams[0] if ep_fams else None
    out["english_primary"] = {"name": ep_name, "source_page": ep_pg,
                              "license_note": license_note(ep_pg), "file": None}
    confidence["english_primary"] = "high" if ep_name and ep_score >= 2 else ("medium" if ep_name else "none")

    ef_pg, ef_score = role_page("english_fallback")
    ef_fams = [f for f in (_latin_families(pages.get(ef_pg, ""), rejected) if ef_pg else []) if f != ep_name]
    ef_name = ef_fams[0] if ef_fams else None
    out["english_fallback"] = {"name": ef_name, "source_page": ef_pg, "file": None}
    confidence["english_fallback"] = "high" if ef_name and ef_score >= 2 else ("medium" if ef_name else "none")

    dg_pg, dg_score = role_page("digital")
    dg_fams = [f for f in (_latin_families(pages.get(dg_pg, ""), rejected) if dg_pg else []) if f != ep_name]
    dg_name = " / ".join(dg_fams) if dg_fams else None
    out["digital"] = {"name": dg_name, "source_page": dg_pg, "file": None}
    confidence["digital"] = "high" if dg_name and dg_score >= 2 else ("medium" if dg_name else "none")

    # Latin families on keyword pages that no role header claimed: if there is
    # exactly one and english_primary is empty, it is the VI's sole Latin font
    # (medium confidence); otherwise they go to human review, never dropped.
    assigned = {ep_name, ef_name} | set(dg_fams)
    unassigned = {}
    for pg, t in sorted(pages.items()):
        for fam in _latin_families(t, []):
            if fam not in assigned and fam not in unassigned:
                unassigned[fam] = pg
    if ep_name is None and len(unassigned) == 1:
        fam, pg = next(iter(unassigned.items()))
        out["english_primary"].update({
            "name": fam, "source_page": pg,
            "_note": "no 主要字体/primary header found; sole Latin family on typography pages"})
        confidence["english_primary"] = "medium"
        ep_name = fam
    else:
        for fam, pg in unassigned.items():
            rejected.append({"candidate": fam, "page": pg,
                             "reason": "Latin font with no role header to attribute"})

    # chinese_primary: prefer an X款字体 library name; else first vendor-prefixed CJK name.
    cp_name, cp_pg = None, None
    lib_hits = {pg: _CJK_LIB_RE.findall(t) for pg, t in pages.items()}
    lib_pages = [pg for pg, hits in lib_hits.items() if hits]
    if lib_pages:
        cp_pg = max(lib_pages, key=lambda pg: len(lib_hits[pg]))
        cp_name = re.sub(r"\s+", "", lib_hits[cp_pg][0])
        confidence["chinese_primary"] = "high" if len(lib_hits[cp_pg]) >= 2 else "medium"
    else:
        for pg, t in sorted(pages.items()):
            vend = _CJK_VENDOR_RE.findall(t)
            if vend:
                cp_name, cp_pg = re.sub(r"\s+", "", vend[0]), pg
                confidence["chinese_primary"] = "medium"
                break
    if cp_name is None:
        confidence["chinese_primary"] = "none"
    out["chinese_primary"] = {"name": cp_name, "source_page": cp_pg,
                              "license_note": license_note(cp_pg), "file": None}
    # vendor names that are NOT the chosen chinese_primary → human review
    for pg, t in sorted(pages.items()):
        for v in _CJK_VENDOR_RE.findall(t):
            v = re.sub(r"\s+", "", v)
            if v != cp_name and v not in [r["candidate"] for r in rejected]:
                rejected.append({"candidate": v, "page": pg,
                                 "reason": "vendor-prefixed CJK font (library member / not assigned a role)"})

    # verbatim usage rules; over-length hits go to human review, not the rules list
    seen = set()
    for pg, t in sorted(pages.items()):
        for s in _sentences(t):
            if not (_RULE_MARK_RE.search(s) and _RULE_TOPIC_RE.search(s)) or s in seen:
                continue
            seen.add(s)
            if len(s) > _RULE_MAX_LEN:
                rejected.append({"candidate": s[:80] + "…", "page": pg,
                                 "reason": "rule-like sentence over length cap (license boilerplate + glued specimen text?) — human review"})
            else:
                rules.append(f"[p{pg}] {s}。")
    out["rules"] = rules
    out["_provenance"] = "text_layer"
    out["_confidence"] = confidence
    out["_candidates_rejected"] = rejected
    return {"typography": out}


def main():
    ap = argparse.ArgumentParser(description="Deterministic typography extraction from a VI PDF.")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = extract(args.pdf)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
