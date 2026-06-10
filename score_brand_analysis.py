"""
Brand Analysis Scorer — automated Tier 1 scoring + report
Compares extracted brand profile against verified ground truth.
"""

import json, math, sys
from difflib import SequenceMatcher

# ── Ground Truth ──────────────────────────────────────────────────

GROUND_TRUTH = {
    "brand_name_cn": "太极堡",
    "brand_name_en": "TAICHI BURGER",
    "primary_color": {
        "hex": "#D70321",
        "rgb": [215, 33, 33],
        "pantone": "2035C",
        "name_cn": "银朱红",
    },
    "secondary_colors": [
        {"hex": "#D7A569", "name_cn": "大地金", "pantone": "7509C"},
        {"hex": "#000000", "name_cn": "墨湖黑", "pantone": "RICH BLACK"},
        {"hex": "#EEE4D8", "name_cn": "珍珠白", "pantone": "11-0605"},
    ],
    "chinese_font": "锦华明朝体",
    "english_font": "Helvetica",
    "brand_slogan": "手作多汁，东方汉堡",
    "brand_category": "东方汉堡",
    "pattern_motifs": ["八角", "花椒", "桂皮", "胡椒", "香叶"],
    "logo_elements": [
        "circular",
        "red",
        "animal silhouette",
        "white negative space",
        "yin-yang / rotational"
    ],
}


# ── Color Distance (ΔE via simple CIE76 approximation) ───────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_lab_approx(r, g, b):
    """Simple sRGB → Lab approximation (good enough for ΔE scoring)."""
    # Normalize
    r, g, b = r/255.0, g/255.0, b/255.0
    # Gamma correction
    r = ((r + 0.055)/1.055)**2.4 if r > 0.04045 else r/12.92
    g = ((g + 0.055)/1.055)**2.4 if g > 0.04045 else g/12.92
    b = ((b + 0.055)/1.055)**2.4 if b > 0.04045 else b/12.92
    # To XYZ
    x = r*0.4124564 + g*0.3575761 + b*0.1804375
    y = r*0.2126729 + g*0.7151522 + b*0.0721750
    z = r*0.0193339 + g*0.1191920 + b*0.9503041
    # Normalize to D65
    x, y, z = x/0.95047, y/1.0, z/1.08883
    # To Lab
    def f(t): return t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    L = 116*f(y) - 16
    a = 500*(f(x) - f(y))
    b_val = 200*(f(y) - f(z))
    return L, a, b_val

def delta_e(hex1: str, hex2: str) -> float:
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    L1, a1, b1_v = rgb_to_lab_approx(r1, g1, b1)
    L2, a2, b2_v = rgb_to_lab_approx(r2, g2, b2)
    return math.sqrt((L1-L2)**2 + (a1-a2)**2 + (b1_v-b2_v)**2)


# ── String Matching ───────────────────────────────────────────────

def fuzzy_match(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


# ── Scoring Functions ─────────────────────────────────────────────

def score_color(extracted_hex: str, truth_hex: str, max_pts: int) -> tuple[float, str]:
    """Score a color extraction by ΔE distance."""
    if not extracted_hex or not extracted_hex.startswith("#"):
        return 0, f"Missing or invalid hex (got: {extracted_hex})"
    de = delta_e(extracted_hex, truth_hex)
    if de <= 1:
        return max_pts, f"ΔE={de:.1f} — perfect"
    elif de <= 3:
        return max_pts * 0.8, f"ΔE={de:.1f} — very close"
    elif de <= 5:
        return max_pts * 0.53, f"ΔE={de:.1f} — noticeable"
    elif de <= 10:
        return max_pts * 0.27, f"ΔE={de:.1f} — significant drift"
    else:
        return 0, f"ΔE={de:.1f} — wrong color"


def find_best_color_match(extracted_colors: list, truth_hex: str) -> tuple[dict, float]:
    """Find the extracted color closest to a ground truth color."""
    best = None
    best_de = 999
    for c in extracted_colors:
        h = c.get("hex", "")
        # If hex is missing/null but RGB is present, compute hex from RGB
        if (not h or h == "None" or not h.startswith("#")) and c.get("rgb"):
            r, g, b = c["rgb"][:3]
            h = f"#{r:02X}{g:02X}{b:02X}"
        if h and h.startswith("#") and len(h) == 7:
            de = delta_e(h, truth_hex)
            if de < best_de:
                best_de = de
                best = c
                best["_resolved_hex"] = h  # store for reporting
    return best, best_de


def score_profile(profile: dict) -> dict:
    """Score an extracted profile against ground truth. Returns detailed report."""
    gt = GROUND_TRUTH
    report = {"tier1": {}, "tier2": {}, "details": []}
    tier1_score = 0
    tier1_max = 100
    
    # ── Brand Name CN (5 pts) ──
    name_cn = profile.get("brand_name", "")
    if name_cn == gt["brand_name_cn"]:
        pts = 5
        note = "exact match"
    elif gt["brand_name_cn"] in name_cn:
        pts = 4
        note = "contained in output"
    else:
        pts = 0
        note = f"got '{name_cn}', expected '{gt['brand_name_cn']}'"
    tier1_score += pts
    report["tier1"]["brand_name_cn"] = {"score": pts, "max": 5, "note": note}
    
    # ── Brand Name EN (5 pts) ──
    name_en = profile.get("brand_name_english", "")
    if name_en.upper() == gt["brand_name_en"].upper():
        pts = 5
        note = "exact match"
    elif fuzzy_match(name_en, gt["brand_name_en"]) >= 0.8:
        pts = 3
        note = f"fuzzy match ({fuzzy_match(name_en, gt['brand_name_en']):.0%})"
    else:
        pts = 0
        note = f"got '{name_en}', expected '{gt['brand_name_en']}'"
    tier1_score += pts
    report["tier1"]["brand_name_en"] = {"score": pts, "max": 5, "note": note}
    
    # ── Primary Color Hex (15 pts) ──
    colors = profile.get("palette", [])
    primary_colors = [c for c in colors if c.get("role") == "primary"]
    if primary_colors:
        primary_hex = primary_colors[0].get("hex", "")
        pts, note = score_color(primary_hex, gt["primary_color"]["hex"], 15)
    else:
        pts, note = 0, "no primary color found in palette"
    tier1_score += pts
    report["tier1"]["primary_color_hex"] = {"score": pts, "max": 15, "note": note, 
                                             "extracted": primary_hex if primary_colors else None,
                                             "truth": gt["primary_color"]["hex"]}
    
    # ── Secondary Colors (15 pts, 5 each) ──
    non_primary = [c for c in colors if c.get("role") != "primary"]
    sec_total = 0
    sec_details = []
    for gt_sec in gt["secondary_colors"]:
        best, best_de = find_best_color_match(non_primary, gt_sec["hex"])
        if best:
            resolved_hex = best.get("_resolved_hex", best.get("hex", ""))
            pts, note = score_color(resolved_hex, gt_sec["hex"], 5)
            sec_details.append({
                "truth": f"{gt_sec['name_cn']} {gt_sec['hex']}",
                "extracted": f"{best.get('name_cn', best.get('name', '?'))} {resolved_hex}",
                "score": pts, "max": 5, "note": note
            })
        else:
            pts = 0
            sec_details.append({
                "truth": f"{gt_sec['name_cn']} {gt_sec['hex']}",
                "extracted": None,
                "score": 0, "max": 5, "note": "not found"
            })
        sec_total += pts
    tier1_score += sec_total
    report["tier1"]["secondary_colors"] = {"score": sec_total, "max": 15, "details": sec_details}
    
    # ── Pantone (5 pts) ──
    if primary_colors:
        # Check if pantone info is anywhere in the profile
        profile_str = json.dumps(profile).upper()
        if gt["primary_color"]["pantone"].upper() in profile_str:
            pts = 5
            note = f"found {gt['primary_color']['pantone']}"
        else:
            pts = 0
            note = f"Pantone {gt['primary_color']['pantone']} not found"
    else:
        pts = 0
        note = "no primary color"
    tier1_score += pts
    report["tier1"]["pantone"] = {"score": pts, "max": 5, "note": note}
    
    # ── Chinese Font (10 pts) ──
    typo = profile.get("typography", {})
    cn_font = typo.get("chinese_font", typo.get("feel", ""))
    ratio = fuzzy_match(cn_font, gt["chinese_font"])
    if ratio >= 0.95:
        pts = 10
        note = f"exact/near-exact ({ratio:.0%})"
    elif ratio >= 0.8:
        pts = 7
        note = f"fuzzy match ({ratio:.0%})"
    elif ratio >= 0.6:
        pts = 4
        note = f"partial match ({ratio:.0%})"
    else:
        pts = 0
        note = f"got '{cn_font}', expected '{gt['chinese_font']}' ({ratio:.0%})"
    tier1_score += pts
    report["tier1"]["chinese_font"] = {"score": pts, "max": 10, "note": note}
    
    # ── English Font (5 pts) ──
    en_font = typo.get("english_font", "")
    if gt["english_font"].lower() in en_font.lower():
        pts = 5
        note = "correct family"
    else:
        pts = 0
        note = f"got '{en_font}', expected '{gt['english_font']}'"
    tier1_score += pts
    report["tier1"]["english_font"] = {"score": pts, "max": 5, "note": note}
    
    # ── Brand Slogan (10 pts) ──
    slogan = profile.get("brand_slogan", "")
    if gt["brand_slogan"] in slogan or slogan in gt["brand_slogan"]:
        pts = 10
        note = "exact match"
    elif fuzzy_match(slogan, gt["brand_slogan"]) >= 0.8:
        pts = 7
        note = f"fuzzy match ({fuzzy_match(slogan, gt['brand_slogan']):.0%})"
    elif fuzzy_match(slogan, gt["brand_slogan"]) >= 0.5:
        pts = 3
        note = f"partial ({fuzzy_match(slogan, gt['brand_slogan']):.0%})"
    else:
        pts = 0
        note = f"got '{slogan}'"
    tier1_score += pts
    report["tier1"]["brand_slogan"] = {"score": pts, "max": 10, "note": note}
    
    # ── Brand Category (5 pts) ──
    category = profile.get("brand_category", "")
    if gt["brand_category"] in category:
        pts = 5
        note = "exact match"
    elif fuzzy_match(category, gt["brand_category"]) >= 0.6:
        pts = 3
        note = f"close ({fuzzy_match(category, gt['brand_category']):.0%})"
    else:
        pts = 0
        note = f"got '{category}'"
    tier1_score += pts
    report["tier1"]["brand_category"] = {"score": pts, "max": 5, "note": note}
    
    # ── Pattern Motifs Count (5 pts) ──
    patterns = profile.get("pattern_elements", [])
    if len(patterns) == gt["pattern_motifs"].__len__():
        pts = 5
        note = f"correct count ({len(patterns)})"
    elif abs(len(patterns) - len(gt["pattern_motifs"])) <= 1:
        pts = 3
        note = f"off by 1 (got {len(patterns)}, expected {len(gt['pattern_motifs'])})"
    else:
        pts = 0
        note = f"got {len(patterns)}, expected {len(gt['pattern_motifs'])}"
    tier1_score += pts
    report["tier1"]["pattern_count"] = {"score": pts, "max": 5, "note": note}
    
    # ── Pattern Motif Names (10 pts, 2 each) ──
    pattern_str = json.dumps(patterns, ensure_ascii=False).lower()
    motif_score = 0
    motif_details = []
    for motif in gt["pattern_motifs"]:
        if motif in pattern_str:
            motif_score += 2
            motif_details.append(f"✅ {motif}")
        else:
            motif_details.append(f"❌ {motif}")
    tier1_score += motif_score
    report["tier1"]["pattern_names"] = {"score": motif_score, "max": 10, "details": motif_details}
    
    # ── Color Value Formats (10 pts) ──
    profile_str = json.dumps(profile, ensure_ascii=False)
    has_rgb = "rgb" in profile_str.lower() or "/33/" in profile_str
    has_cmyk = "cmyk" in profile_str.lower()
    has_pantone = "pantone" in profile_str.lower() or "2035" in profile_str
    if has_rgb and has_cmyk and has_pantone:
        pts = 10
        note = "all formats present"
    elif has_rgb and (has_cmyk or has_pantone):
        pts = 7
        note = f"RGB + {'CMYK' if has_cmyk else 'Pantone'}"
    elif has_rgb or has_pantone:
        pts = 5
        note = "hex only or partial"
    else:
        pts = 2
        note = "minimal color data"
    tier1_score += pts
    report["tier1"]["color_formats"] = {"score": pts, "max": 10, "note": note}
    
    # ── Tier 2: Logo Description (20 pts) ──
    logo_desc = profile.get("logo_description", "").lower()
    logo_pts = 0
    logo_checks = []
    for element in gt["logo_elements"]:
        keywords = element.lower().split(" / ")
        found = any(kw in logo_desc for kw in keywords)
        if found:
            logo_pts += 4
            logo_checks.append(f"✅ {element}")
        else:
            logo_checks.append(f"❌ {element}")
    report["tier2"] = {"logo_description": {"score": logo_pts, "max": 20, "details": logo_checks}}
    
    # ── Summary ──
    tier1_pct = tier1_score / tier1_max * 100
    
    if tier1_pct >= 90:
        grade = "A"
    elif tier1_pct >= 75:
        grade = "B"
    elif tier1_pct >= 60:
        grade = "C"
    elif tier1_pct >= 40:
        grade = "D"
    else:
        grade = "F"
    
    report["summary"] = {
        "tier1_score": tier1_score,
        "tier1_max": tier1_max,
        "tier1_pct": round(tier1_pct, 1),
        "grade": grade,
        "tier2_logo_score": logo_pts,
        "tier2_logo_max": 20,
    }
    
    return report


def print_report(report: dict):
    """Pretty-print the scoring report."""
    s = report["summary"]
    print(f"\n{'='*60}")
    print(f"  BRAND ANALYSIS SCORECARD")
    print(f"  Grade: {s['grade']}  |  Tier 1: {s['tier1_score']}/{s['tier1_max']} ({s['tier1_pct']}%)")
    print(f"{'='*60}")
    
    print(f"\n  TIER 1 — Hard Data (exact values)")
    print(f"  {'─'*50}")
    for field, data in report["tier1"].items():
        if isinstance(data, dict) and "score" in data:
            status = "✅" if data["score"] == data["max"] else "⚠️" if data["score"] > 0 else "❌"
            print(f"  {status} {field}: {data['score']}/{data['max']} — {data.get('note', '')}")
            if "details" in data and isinstance(data["details"], list):
                for d in data["details"]:
                    if isinstance(d, str):
                        print(f"      {d}")
                    elif isinstance(d, dict):
                        s2 = "✅" if d["score"] == d["max"] else "⚠️" if d["score"] > 0 else "❌"
                        print(f"      {s2} {d.get('truth', '')} → {d.get('extracted', '?')} ({d.get('note', '')})")
    
    print(f"\n  TIER 2 — Structured Rules")
    print(f"  {'─'*50}")
    logo = report["tier2"].get("logo_description", {})
    print(f"  Logo description: {logo.get('score', 0)}/{logo.get('max', 20)}")
    for d in logo.get("details", []):
        print(f"      {d}")
    
    print(f"\n{'='*60}")


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_brand_analysis.py <profile.json>")
        print("Scoring last GPT profile...")
        path = "/home/alecx/workspace/handyprint-design-tool/output/taijibao_brand_profile_gpt.json"
    else:
        path = sys.argv[1]
    
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    report = score_profile(profile)
    print_report(report)
    
    # Save report
    report_path = path.replace(".json", "_score.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved: {report_path}")
