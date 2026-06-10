"""
秀才弄 Brand Analysis — ground truth + v3 benchmark
A design proposal (品牌设计方案), not a strict VI manual.
Different structure from 太极堡: more atmospheric, no Pantone, no min-size specs.
"""

import json, os, sys, time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env", override=True)

# ── Ground Truth ──────────────────────────────────────────────────

GROUND_TRUTH = {
    "brand_name_cn": "秀才弄",
    "brand_name_en": "",  # No English name in this brand
    "primary_color": {
        "hex": "#5E6234",
        "rgb": [94, 98, 52],
        "name_cn": "山野绿",
    },
    "secondary_colors": [
        {"hex": "#D99F46", "name_cn": "金盖黄", "pantone": ""},
        {"hex": "#3F2910", "name_cn": "深棕",   "pantone": ""},
        {"hex": "#F4E9DB", "name_cn": "稻米白", "pantone": ""},
    ],
    "chinese_font": "隶书",  # Clerical script style — this is the typographic approach, not a specific digital font
    "english_font": "",  # No English font specified
    "brand_slogan": "砂锅烧香鸡首创品牌",
    "brand_category": "烧香鸡",  # or 砂锅烧香鸡
    "pattern_motifs": [],  # No specific named pattern motifs like 太极堡
    "logo_elements": [
        "cooking pot",  # clay pot / wok with lid
        "golden",       # gold/warm color
        "textured",     # distressed/aged texture
        "lid",          # pot has a lid with knob
        "handles",      # pot has side handles
    ],
}

# ── Page Groups (秀才弄 structure) ────────────────────────────────

PAGES_DIR = "/tmp/xiucainong_pages"

PAGE_GROUPS = {
    "colors":     [3],                # Color palette page
    "typography": [6, 7],             # Font details + font philosophy
    "logo":       [5, 9, 10, 12, 13], # Logo pages + super symbol
    "copy":       [1, 18, 19, 20],    # Cover + brand value/slogan pages
    "patterns":   [16],               # Auxiliary icons/elements
}

# ── Import v3 infrastructure ─────────────────────────────────────

sys.path.insert(0, "/home/alecx/workspace/handyprint-design-tool")

from analyze_brand_v3 import (
    COLORS_SYSTEM, COLORS_USER, TYPOGRAPHY_SYSTEM, TYPOGRAPHY_USER,
    LOGO_SYSTEM, LOGO_USER, COPY_SYSTEM, COPY_USER,
    PATTERNS_SYSTEM, PATTERNS_USER, 
    MODEL_ROUTES, CALLERS, merge_results,
)
from score_brand_analysis import (
    delta_e, hex_to_rgb, fuzzy_match, score_color, find_best_color_match,
)

# ── Custom Scorer for 秀才弄 ──────────────────────────────────────

def score_xiucainong(profile: dict) -> dict:
    """Score against 秀才弄 ground truth. Adapted from 太极堡 scorer."""
    gt = GROUND_TRUTH
    report = {"tier1": {}, "tier2": {}}
    tier1_score = 0
    
    # Brand name CN (5 pts)
    name_cn = profile.get("brand_name", "")
    if gt["brand_name_cn"] in name_cn:
        pts, note = 5, "match"
    elif fuzzy_match(name_cn, gt["brand_name_cn"]) >= 0.6:
        pts, note = 3, f"fuzzy ({fuzzy_match(name_cn, gt['brand_name_cn']):.0%})"
    else:
        pts, note = 0, f"got '{name_cn}'"
    tier1_score += pts
    report["tier1"]["brand_name_cn"] = {"score": pts, "max": 5, "note": note}
    
    # Primary color hex (15 pts)
    colors = profile.get("palette", [])
    primary_colors = [c for c in colors if c.get("role") == "primary"]
    if primary_colors:
        ph = primary_colors[0].get("hex", "")
        if not ph or ph == "None":
            rgb = primary_colors[0].get("rgb")
            if rgb: ph = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        pts, note = score_color(ph, gt["primary_color"]["hex"], 15)
    else:
        pts, note = 0, "no primary color"
        ph = None
    tier1_score += pts
    report["tier1"]["primary_color_hex"] = {"score": pts, "max": 15, "note": note, "extracted": ph, "truth": gt["primary_color"]["hex"]}
    
    # Secondary colors (15 pts, 5 each)
    non_primary = [c for c in colors if c.get("role") != "primary"]
    sec_total = 0
    sec_details = []
    for gt_sec in gt["secondary_colors"]:
        best, best_de = find_best_color_match(non_primary, gt_sec["hex"])
        if best:
            resolved = best.get("_resolved_hex", best.get("hex", ""))
            pts, note = score_color(resolved, gt_sec["hex"], 5)
            sec_details.append({"truth": f"{gt_sec['name_cn']} {gt_sec['hex']}", "extracted": resolved, "score": pts, "max": 5, "note": note})
        else:
            sec_details.append({"truth": f"{gt_sec['name_cn']} {gt_sec['hex']}", "score": 0, "max": 5, "note": "not found"})
            pts = 0
        sec_total += pts
    tier1_score += sec_total
    report["tier1"]["secondary_colors"] = {"score": sec_total, "max": 15, "details": sec_details}
    
    # Chinese font (10 pts) — looser matching for 秀才弄 since it uses style names not specific fonts
    typo = profile.get("typography", {})
    cn_font = typo.get("chinese_font", "")
    if gt["chinese_font"] in cn_font or cn_font in gt["chinese_font"]:
        pts, note = 10, "match"
    elif fuzzy_match(cn_font, gt["chinese_font"]) >= 0.5:
        pts, note = 7, f"fuzzy ({fuzzy_match(cn_font, gt['chinese_font']):.0%})"
    elif "隶" in cn_font:  # Contains the key character
        pts, note = 5, "partial — contains 隶"
    else:
        pts, note = 0, f"got '{cn_font}'"
    tier1_score += pts
    report["tier1"]["chinese_font"] = {"score": pts, "max": 10, "note": note}
    
    # Brand slogan (10 pts)
    slogan = profile.get("brand_slogan", "")
    gt_slogan = gt["brand_slogan"]
    if gt_slogan in slogan or slogan in gt_slogan:
        pts, note = 10, "match"
    elif fuzzy_match(slogan, gt_slogan) >= 0.6:
        pts, note = 7, f"fuzzy ({fuzzy_match(slogan, gt_slogan):.0%})"
    elif "砂锅" in slogan or "烧香鸡" in slogan:
        pts, note = 4, "partial — key terms present"
    else:
        pts, note = 0, f"got '{slogan}'"
    tier1_score += pts
    report["tier1"]["brand_slogan"] = {"score": pts, "max": 10, "note": note}
    
    # Brand category (5 pts)
    category = profile.get("brand_category", "")
    if "烧香鸡" in category or "砂锅" in category:
        pts, note = 5, "match"
    elif "鸡" in category:
        pts, note = 3, "partial"
    else:
        pts, note = 0, f"got '{category}'"
    tier1_score += pts
    report["tier1"]["brand_category"] = {"score": pts, "max": 5, "note": note}
    
    # Color value formats (10 pts) — no Pantone in this brand
    profile_str = json.dumps(profile, ensure_ascii=False)
    has_rgb = "rgb" in profile_str.lower() or "94" in profile_str
    has_cmyk = "cmyk" in profile_str.lower()
    if has_rgb and has_cmyk:
        pts, note = 10, "RGB + CMYK present"
    elif has_rgb:
        pts, note = 7, "RGB only"
    else:
        pts, note = 3, "hex only"
    tier1_score += pts
    report["tier1"]["color_formats"] = {"score": pts, "max": 10, "note": note}
    
    # Color names (10 pts — 2.5 each for 4 color names)
    color_names = ["山野绿", "金盖黄", "稻米白", "深棕"]
    name_score = 0
    name_details = []
    for cn in color_names:
        if cn in profile_str:
            name_score += 2.5
            name_details.append(f"✅ {cn}")
        else:
            name_details.append(f"❌ {cn}")
    tier1_score += name_score
    report["tier1"]["color_names"] = {"score": name_score, "max": 10, "details": name_details}
    
    # Remaining points allocated to general extraction (20 pts)
    # Logo described? (10 pts)
    logo_desc = profile.get("logo_description", "").lower()
    logo_pts = 0
    logo_checks = []
    for elem in gt["logo_elements"]:
        if elem.lower() in logo_desc or (elem == "cooking pot" and ("pot" in logo_desc or "wok" in logo_desc or "锅" in logo_desc)):
            logo_pts += 2
            logo_checks.append(f"✅ {elem}")
        else:
            logo_checks.append(f"❌ {elem}")
    tier1_score += logo_pts
    report["tier1"]["logo_elements"] = {"score": logo_pts, "max": 10, "details": logo_checks}
    
    # Sub-brand text (10 pts)
    if "烧香鸡" in profile_str:
        pts, note = 10, "found 烧香鸡"
    elif "鸡" in profile_str:
        pts, note = 5, "partial — 鸡 present"
    else:
        pts, note = 0, "missing sub-brand"
    tier1_score += pts
    report["tier1"]["sub_brand"] = {"score": pts, "max": 10, "note": note}
    
    tier1_max = 100
    tier1_pct = tier1_score / tier1_max * 100
    grade = "A" if tier1_pct >= 90 else "B" if tier1_pct >= 75 else "C" if tier1_pct >= 60 else "D" if tier1_pct >= 40 else "F"
    
    report["summary"] = {
        "tier1_score": round(tier1_score, 1),
        "tier1_max": tier1_max,
        "tier1_pct": round(tier1_pct, 1),
        "grade": grade,
    }
    return report


def print_report(report):
    s = report["summary"]
    print(f"\n{'='*60}")
    print(f"  秀才弄 BRAND ANALYSIS SCORECARD")
    print(f"  Grade: {s['grade']}  |  Tier 1: {s['tier1_score']}/{s['tier1_max']} ({s['tier1_pct']}%)")
    print(f"{'='*60}")
    for field, data in report["tier1"].items():
        if isinstance(data, dict) and "score" in data:
            status = "✅" if data["score"] == data["max"] else "⚠️" if data["score"] > 0 else "❌"
            print(f"  {status} {field}: {data['score']}/{data['max']} — {data.get('note', '')}")
            if "details" in data:
                for d in data["details"]:
                    if isinstance(d, str):
                        print(f"      {d}")
                    elif isinstance(d, dict):
                        print(f"      {d.get('truth', '')} → {d.get('extracted', '?')} ({d.get('note', '')})")
    print(f"{'='*60}")


# ── Benchmark Runner ──────────────────────────────────────────────

def run_once(run_id: int) -> dict:
    """Run v3 multi-model analysis on 秀才弄 and score it."""
    
    domains = [
        ("colors",     COLORS_SYSTEM,     COLORS_USER),
        ("typography", TYPOGRAPHY_SYSTEM,  TYPOGRAPHY_USER),
        ("logo",       LOGO_SYSTEM,       LOGO_USER),
        ("copy",       COPY_SYSTEM,       COPY_USER),
        ("patterns",   PATTERNS_SYSTEM,   PATTERNS_USER),
    ]
    
    results = {}
    run_meta = {}
    
    for domain, system_prompt, user_msg in domains:
        provider, model = MODEL_ROUTES[domain]
        pages = PAGE_GROUPS[domain]
        image_paths = [f"{PAGES_DIR}/page_{p:02d}.png" for p in pages]
        
        # Verify all exist
        image_paths = [p for p in image_paths if os.path.exists(p)]
        if not image_paths:
            print(f"    {domain}: ❌ no valid pages")
            continue
        
        try:
            caller = CALLERS[provider]
            result, meta = caller(system_prompt, user_msg, image_paths, model)
            results[domain] = result
            run_meta[domain] = meta
            print(f"    {domain}: ✅ {meta['time']}s")
        except Exception as e:
            print(f"    {domain}: ❌ {e}")
            results[domain] = {}
    
    profile = merge_results(results)
    report = score_xiucainong(profile)
    
    return {
        "profile": profile,
        "report": report,
        "meta": run_meta,
    }


def main():
    N_RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*60}")
    print(f"  BENCHMARK: 秀才弄 v3 Multi-Model × {N_RUNS} runs")
    print(f"  Routing: {', '.join(f'{d}→{MODEL_ROUTES[d][1]}' for d in MODEL_ROUTES)}")
    print(f"{'='*60}")
    
    all_scores = []
    
    for run in range(1, N_RUNS + 1):
        print(f"\n  ── Run {run}/{N_RUNS} ──")
        t0 = time.time()
        result = run_once(run)
        elapsed = time.time() - t0
        
        s = result["report"]["summary"]
        print(f"    SCORE: {s['tier1_pct']}% ({s['grade']}) | Time: {elapsed:.1f}s")
        
        all_scores.append({
            "run": run, "tier1_pct": s["tier1_pct"], "grade": s["grade"], "time": round(elapsed, 1),
            "fields": {k: v["score"] for k, v in result["report"]["tier1"].items() if isinstance(v, dict) and "score" in v}
        })
    
    # ── Results ──
    print(f"\n{'='*60}")
    print(f"  BENCHMARK RESULTS — 秀才弄 × {N_RUNS} runs")
    print(f"{'='*60}")
    
    print(f"\n  {'Run':<6} {'Tier1':>7} {'Grade':>6} {'Time':>6}")
    print(f"  {'─'*30}")
    for s in all_scores:
        print(f"  {s['run']:<6} {s['tier1_pct']:>6.1f}% {s['grade']:>6} {s['time']:>5.1f}s")
    
    avg_t1 = sum(s["tier1_pct"] for s in all_scores) / N_RUNS
    min_t1 = min(s["tier1_pct"] for s in all_scores)
    max_t1 = max(s["tier1_pct"] for s in all_scores)
    avg_time = sum(s["time"] for s in all_scores) / N_RUNS
    
    print(f"  {'─'*30}")
    print(f"  {'AVG':<6} {avg_t1:>6.1f}%        {avg_time:>5.1f}s")
    print(f"  {'MIN':<6} {min_t1:>6.1f}%")
    print(f"  {'MAX':<6} {max_t1:>6.1f}%")
    print(f"  Spread: {max_t1 - min_t1:.1f}pp")
    
    # Per-field averages
    print(f"\n  PER-FIELD AVERAGES")
    print(f"  {'─'*50}")
    field_names = list(all_scores[0]["fields"].keys())
    for field in field_names:
        vals = [s["fields"].get(field, 0) for s in all_scores]
        avg = sum(vals) / len(vals)
        consistency = "✅" if all(v == vals[0] for v in vals) else f"varies {min(vals):.1f}-{max(vals):.1f}"
        print(f"  {field:<25} avg={avg:>5.1f}  {consistency}")
    
    from collections import Counter
    grades = Counter(s["grade"] for s in all_scores)
    print(f"\n  GRADES: {dict(grades)}")
    
    # Print one detailed report
    print(f"\n  ── Detailed report from last run ──")
    print_report(all_scores[-1]["fields"] and result["report"])
    
    # Save
    bench_path = output_dir / f"benchmark_xiucainong_v3_{timestamp}.json"
    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump({
            "brand": "秀才弄",
            "config": {"n_runs": N_RUNS, "routes": {d: MODEL_ROUTES[d][1] for d in MODEL_ROUTES}},
            "summary": {"avg": round(avg_t1, 1), "min": round(min_t1, 1), "max": round(max_t1, 1), "spread": round(max_t1-min_t1, 1), "grades": dict(grades)},
            "runs": all_scores,
        }, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {bench_path}")


if __name__ == "__main__":
    main()
