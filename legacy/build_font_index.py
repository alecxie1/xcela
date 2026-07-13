#!/usr/bin/env python3
"""build_font_index.py — build a brand font index from REAL font name tables.

Scans a fonts/ directory, reads each file's internal `name` table with fonttools
(typographic family nameID 16, subfamily/weight nameID 17, PostScript nameID 6 —
both English and Chinese records), and writes index.json mapping the VI's Chinese
vocabulary names to actual files:

  {"汉仪雅酷黑": {"85W": {"file": "brands/aia/fonts/HYYakuHei-85W.ttf",
                          "ps_name": "HYYakuHei-HEW", "family_zh": "汉仪雅酷黑", ...}}}

Filenames are romanized (HYYakuHei) while VI names are Chinese (汉仪雅酷黑) — the
name table bridges them; nothing here guesses from filenames. Files whose internal
name can't be matched to a known 汉仪 pattern go into "_unmatched" for human review.

CLI:
  .venv/bin/python build_font_index.py brands/aia/fonts [--out brands/aia/fonts/index.json]
"""

import argparse
import json
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parent

# Windows langIDs / Mac langIDs that count as Chinese records.
_ZH_LANGS_WIN = {0x804, 0x404, 0xC04, 0x1004}  # zh-CN, zh-TW, zh-HK, zh-SG
_ZH_LANG_MAC = {0x21, 0x13}                    # Mac langID 33 (zh-simplified), 19 (zh-trad)
_EN_LANGS_WIN = {0x409}
_EN_LANG_MAC = {0x0}

# A trailing weight token: digits + optional letter (85W, 55S, 85J) or a bare
# letter grade (W, J), optionally preceded by space/hyphen.
_WEIGHT_TAIL = re.compile(r"[\s\-]*(\d{2,3}\s*[A-Za-z]?简?|[WJS])$")


def _is_zh(rec) -> bool:
    return (rec.platformID == 3 and rec.langID in _ZH_LANGS_WIN) or \
           (rec.platformID == 1 and rec.langID in _ZH_LANG_MAC)


def _is_en(rec) -> bool:
    return (rec.platformID == 3 and rec.langID in _EN_LANGS_WIN) or \
           (rec.platformID == 1 and rec.langID in _EN_LANG_MAC)


def _pick(names, name_ids, lang_test):
    for nid in name_ids:
        for rec in names:
            if rec.nameID == nid and lang_test(rec):
                try:
                    s = rec.toUnicode().strip()
                except UnicodeDecodeError:
                    continue
                if s:
                    return s
    return None


def read_font_names(path: Path) -> dict:
    """Extract the identity fields we index on, straight from the name table."""
    font = TTFont(str(path), lazy=True, fontNumber=0)
    try:
        names = font["name"].names
        fam_zh = _pick(names, (16, 1), _is_zh)
        fam_en = _pick(names, (16, 1), _is_en)
        sub_zh = _pick(names, (17, 2), _is_zh)
        sub_en = _pick(names, (17, 2), _is_en)
        ps = _pick(names, (6,), _is_en) or _pick(names, (6,), _is_zh)
        full_zh = _pick(names, (4,), _is_zh)
    finally:
        font.close()

    # Weight key: prefer the typographic subfamily (17) which HanYi fills with
    # the real grade (85W / 55S / 85J / W); nameID 2 is often a useless "Regular".
    weight = None
    for cand in (sub_zh, sub_en):
        if cand and cand.lower() != "regular":
            weight = cand
            break
    family_zh = fam_zh
    if family_zh:
        # Some files put the weight inside the family record ("汉仪雅酷黑-85J",
        # "汉仪元隆黑 75W") — strip it, and use it as the weight if 17 was empty.
        m = _WEIGHT_TAIL.search(family_zh)
        if m:
            weight = weight or m.group(1).replace(" ", "")
            family_zh = _WEIGHT_TAIL.sub("", family_zh).strip()
    if not weight:
        weight = "Regular"
    return {
        "family_zh": family_zh,
        "family_en": fam_en,
        "weight": weight.replace(" ", ""),
        "ps_name": ps,
        "full_name_zh": full_zh,
    }


def build_index(fonts_dir: Path) -> dict:
    index: dict = {}
    unmatched = []
    files = sorted(p for p in fonts_dir.iterdir()
                   if p.suffix.lower() in (".ttf", ".otf", ".ttc"))
    for p in files:
        try:
            meta = read_font_names(p)
        except Exception as exc:
            unmatched.append({"file": str(p.relative_to(REPO_ROOT)),
                              "reason": f"name table unreadable: {exc}"})
            continue
        rel = str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p)
        entry = {
            "file": rel,
            "ps_name": meta["ps_name"],
            "family_zh": meta["family_zh"],
            "family_en": meta["family_en"],
            "full_name_zh": meta["full_name_zh"],
        }
        fam = meta["family_zh"]
        # Known-pattern gate: a real HanYi face announces itself as 汉仪… in the
        # zh record (or HY… in the en record as a weaker signal).
        if not fam or not fam.startswith("汉仪"):
            entry["reason"] = (
                f"internal zh family {fam!r} doesn't match the 汉仪 pattern "
                f"(en family: {meta['family_en']!r})")
            unmatched.append(entry)
            continue
        bucket = index.setdefault(fam, {})
        weight = meta["weight"]
        if weight in bucket:
            # duplicate family+weight (e.g. the 雅酷黑-85 re-download) — keep the
            # first, flag the duplicate for human review rather than overwriting.
            entry["reason"] = (f"duplicate of {fam} {weight} "
                               f"(already indexed: {bucket[weight]['file']})")
            unmatched.append(entry)
            continue
        bucket[weight] = entry
    if unmatched:
        index["_unmatched"] = unmatched
    return index


def main():
    ap = argparse.ArgumentParser(description="Build a font index from internal name tables.")
    ap.add_argument("fonts_dir", help="directory of .ttf/.otf files")
    ap.add_argument("--out", default="", help="output index.json (default <fonts_dir>/index.json)")
    args = ap.parse_args()

    fonts_dir = Path(args.fonts_dir)
    out = Path(args.out) if args.out else fonts_dir / "index.json"
    index = build_index(fonts_dir)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    families = [k for k in index if k != "_unmatched"]
    n_faces = sum(len(v) for k, v in index.items() if k != "_unmatched")
    print(f"Indexed {n_faces} faces across {len(families)} families -> {out}")
    for fam in sorted(families):
        weights = ", ".join(sorted(index[fam]))
        print(f"  {fam}: {weights}")
    unmatched = index.get("_unmatched", [])
    if unmatched:
        print(f"\n_unmatched ({len(unmatched)} files, human review):", file=sys.stderr)
        for u in unmatched:
            print(f"  {u['file']}: {u.get('reason')}", file=sys.stderr)
    else:
        print("\n_unmatched: none")


if __name__ == "__main__":
    main()
