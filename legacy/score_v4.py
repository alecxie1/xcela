"""
Unified Brand-Analysis Scorer — Step 4.

ONE scorer, driven by per-brand answer-key JSON files (answer_keys/<brand>.json).
Add a brand = drop in a JSON key, no new code.

Scoring is dispatched by FIELD TYPE (the encompassing rubric):
  objective_printed  -> mechanical: delta_e (colors), string/fuzzy/exact (text), set (motifs)
  objective_visual   -> string match, but absence-tolerant (e.g. custom logotype has no font name)
  subjective         -> NOT scored here (logo/tone) — needs human or calibrated judge (bake-off)

Ground truth comes from the human-verified key. Color scoring uses RGB-derived hex
(unambiguous); printed_html is consistency-checked but does NOT drive the ΔE score.

Usage:
  python score_v4.py <brand> <extracted_profile.json>
  python score_v4.py taichi output/taijibao_profile_v3_XXXX.json
"""

import json, sys, math
from pathlib import Path
from difflib import SequenceMatcher

KEYS_DIR = Path(__file__).parent / "answer_keys"

# ── color math (CIE76-ish ΔE, matches extract_colors.py) ──────────

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    r, g, b = rgb[:3]
    return "#%02x%02x%02x" % (int(r), int(g), int(b))

def _lab(r, g, b):
    r, g, b = r/255, g/255, b/255
    f = lambda c: ((c+0.055)/1.055)**2.4 if c > 0.04045 else c/12.92
    r, g, b = f(r), f(g), f(b)
    x = (r*0.4124+g*0.3576+b*0.1805)/0.95047
    y = (r*0.2126+g*0.7152+b*0.0722)/1.0
    z = (r*0.0193+g*0.1192+b*0.9505)/1.08883
    g2 = lambda t: t**(1/3) if t > 0.008856 else 7.787*t+16/116
    return (116*g2(y)-16, 500*(g2(x)-g2(y)), 200*(g2(y)-g2(z)))

def delta_e(hex1, hex2):
    L1,a1,b1 = _lab(*hex_to_rgb(hex1)); L2,a2,b2 = _lab(*hex_to_rgb(hex2))
    return math.sqrt((L1-L2)**2 + (a1-a2)**2 + (b1-b2)**2)

def fuzzy(a, b):
    return SequenceMatcher(None, (a or "").lower().strip(), (b or "").lower().strip()).ratio()

# ── color matching: canonical truth hex = from RGB if present, else printed_html ──

def truth_hex(color_item):
    if color_item.get("rgb"):
        return rgb_to_hex(color_item["rgb"])
    if color_item.get("printed_html"):
        return "#" + color_item["printed_html"].lstrip("#").lower()
    return None

def extracted_hexes(profile):
    """Pull all hex values out of an extracted profile, resolving rgb->hex if needed."""
    out = []
    for c in profile.get("palette", []) or profile.get("colors", []):
        h = c.get("hex")
        if (not h or not str(h).startswith("#")) and c.get("rgb"):
            h = rgb_to_hex(c["rgb"])
        if h and str(h).startswith("#") and len(h) == 7:
            out.append((h.lower(), c))
    return out

def score_color(extracted_hex, th, max_pts):
    de = delta_e(extracted_hex, th)
    if de <= 1:   return max_pts,        f"ΔE={de:.1f} perfect"
    if de <= 3:   return max_pts*0.8,    f"ΔE={de:.1f} very close"
    if de <= 5:   return max_pts*0.53,   f"ΔE={de:.1f} noticeable"
    if de <= 10:  return max_pts*0.27,   f"ΔE={de:.1f} drift"
    return 0, f"ΔE={de:.1f} wrong"

# ── per-field-type scorers ────────────────────────────────────────

def score_colors(field, profile):
    ex = extracted_hexes(profile)
    ex_hexes = [h for h, _ in ex]
    results, total, mx = [], 0.0, 0.0
    per = 15.0 / max(len(field["items"]), 1)  # colors worth 15 pts total, split evenly
    for item in field["items"]:
        th = truth_hex(item)
        mx += per
        if th is None:
            results.append({"truth": item.get("name_cn") or "(unnamed)", "note": "no truth hex (skipped)", "score": 0, "max": round(per,1)})
            continue
        if ex_hexes:
            best = min(ex_hexes, key=lambda h: delta_e(h, th))
            pts, note = score_color(best, th, per)
        else:
            best, pts, note = None, 0, "nothing extracted"
        total += pts
        results.append({"truth": f"{item.get('name_cn') or '?'} {th}", "extracted": best,
                        "score": round(pts,2), "max": round(per,1), "note": note})
    return total, mx, results

def score_fonts(field, profile):
    typo = profile.get("typography", {}) or {}
    total, mx, results = 0.0, 0.0, []
    checks = [("chinese_display", typo.get("chinese_font") or typo.get("chinese_display"), 6),
              ("english",         typo.get("english_font") or typo.get("english"), 4)]
    for key, got, pts_max in checks:
        want = field.get(key)
        if not want:
            continue
        mx += pts_max
        r = fuzzy(got or "", want)
        if want in (got or "") or r >= 0.95: pts = pts_max
        elif r >= 0.6: pts = pts_max*0.6
        else: pts = 0
        total += pts
        results.append({"field": key, "want": want, "got": got, "score": round(pts,1), "max": pts_max, "ratio": round(r,2)})
    return total, mx, results

def score_string(field, profile, profile_key, max_pts):
    got = profile.get(profile_key, "") or ""
    want = field["value"]
    if want is None:
        return 0, 0, [{"note": "no truth value"}]
    if want in got or got in want and got:
        pts, note = max_pts, "match"
    elif fuzzy(got, want) >= 0.8:
        pts, note = max_pts*0.7, f"fuzzy {fuzzy(got,want):.0%}"
    else:
        pts, note = 0, f"got '{got[:30]}'"
    return pts, max_pts, [{"want": want, "got": got, "score": round(pts,1), "max": max_pts, "note": note}]

def score_set(field, profile, max_pts):
    truth = field["items"]
    blob = json.dumps(profile, ensure_ascii=False)
    hit = [m for m in truth if m in blob]
    pts = max_pts * len(hit) / max(len(truth), 1)
    return pts, max_pts, [{"found": hit, "missing": [m for m in truth if m not in hit],
                           "score": round(pts,1), "max": max_pts}]

# ── main ──────────────────────────────────────────────────────────

def score(brand, profile):
    key = json.loads((KEYS_DIR / f"{brand}.json").read_text(encoding="utf-8"))
    fields = key["fields"]
    report = {"brand": key["brand"], "objective": {}, "subjective_deferred": [], "consistency_flags": []}
    obj_total, obj_max = 0.0, 0.0

    # consistency check: printed_html vs RGB-derived hex
    for item in fields.get("colors", {}).get("items", []):
        if item.get("rgb") and item.get("printed_html"):
            derived = rgb_to_hex(item["rgb"]).lstrip("#").lower()
            printed = item["printed_html"].lstrip("#").lower()
            if derived != printed:
                report["consistency_flags"].append(
                    f"{item.get('name_cn')}: printed_html={printed} but RGB={item['rgb']}=>{derived} (MISMATCH — human ruling)")

    for fname, fdef in fields.items():
        ftype = fdef.get("type")
        if ftype == "subjective":
            report["subjective_deferred"].append(fname)
            continue
        if fname == "colors":
            t, m, det = score_colors(fdef, profile)
        elif fname == "fonts":
            t, m, det = score_fonts(fdef, profile)
        elif fname == "motifs":
            t, m, det = score_set(fdef, profile, 10)
        elif fname in ("slogan", "category"):
            pk = "brand_slogan" if fname == "slogan" else "brand_category"
            t, m, det = score_string(fdef, profile, pk, 10 if fname=="slogan" else 5)
        elif fname == "brand_name_cn":
            t, m, det = score_string(fdef, profile, "brand_name", 5)
        elif fname == "brand_name_en":
            t, m, det = score_string(fdef, profile, "brand_name_english", 5)
        else:
            continue
        obj_total += t; obj_max += m
        report["objective"][fname] = {"score": round(t,2), "max": round(m,1), "detail": det}

    pct = obj_total / obj_max * 100 if obj_max else 0
    report["summary"] = {"objective_score": round(obj_total,1), "objective_max": round(obj_max,1),
                         "objective_pct": round(pct,1),
                         "grade": "A" if pct>=90 else "B" if pct>=75 else "C" if pct>=60 else "D" if pct>=40 else "F"}
    return report

def print_report(r):
    s = r["summary"]
    print(f"\n{'='*60}\n  {r['brand']} — UNIFIED SCORER (objective fields only)")
    print(f"  Grade {s['grade']} | {s['objective_score']}/{s['objective_max']} ({s['objective_pct']}%)\n{'='*60}")
    for f, d in r["objective"].items():
        mark = "✅" if d["score"] >= d["max"]*0.99 else "⚠️" if d["score"]>0 else "❌"
        print(f"  {mark} {f}: {d['score']}/{d['max']}")
        for x in d["detail"]:
            print(f"      {x}")
    if r["consistency_flags"]:
        print("\n  ⚠️  CONSISTENCY FLAGS (human ruling needed):")
        for c in r["consistency_flags"]: print(f"      {c}")
    print(f"\n  Subjective fields deferred to bake-off: {r['subjective_deferred']}")
    print('='*60)

if __name__ == "__main__":
    brand = sys.argv[1]
    profile = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    rep = score(brand, profile)
    print_report(rep)
    out = Path(sys.argv[2]).with_suffix(".v4score.json")
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")
