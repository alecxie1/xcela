"""
Benchmark runner — runs analyze_brand_v3 N times and reports averages.
"""

import json, sys, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/home/alecx/workspace/handyprint-design-tool")

from analyze_brand_v3 import (
    PAGES_DIR, PAGE_GROUPS, MODEL_ROUTES, CALLERS,
    COLORS_SYSTEM, COLORS_USER, TYPOGRAPHY_SYSTEM, TYPOGRAPHY_USER,
    LOGO_SYSTEM, LOGO_USER, COPY_SYSTEM, COPY_USER,
    PATTERNS_SYSTEM, PATTERNS_USER, merge_results,
)
from score_brand_analysis import score_profile

N_RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5

output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

DOMAINS = [
    ("colors",     COLORS_SYSTEM,     COLORS_USER),
    ("typography", TYPOGRAPHY_SYSTEM,  TYPOGRAPHY_USER),
    ("logo",       LOGO_SYSTEM,       LOGO_USER),
    ("copy",       COPY_SYSTEM,       COPY_USER),
    ("patterns",   PATTERNS_SYSTEM,   PATTERNS_USER),
]

all_scores = []
all_reports = []

print(f"\n{'='*60}")
print(f"  BENCHMARK: v3 Multi-Model × {N_RUNS} runs")
print(f"  Routing: {', '.join(f'{d}→{MODEL_ROUTES[d][1]}' for d in MODEL_ROUTES)}")
print(f"{'='*60}")

for run in range(1, N_RUNS + 1):
    print(f"\n  ── Run {run}/{N_RUNS} ──")
    t0 = time.time()
    
    results = {}
    run_meta = {}
    
    for domain, system_prompt, user_msg in DOMAINS:
        provider, model = MODEL_ROUTES[domain]
        pages = PAGE_GROUPS[domain]
        image_paths = [f"{PAGES_DIR}/page_{p:02d}.png" for p in pages]
        
        try:
            caller = CALLERS[provider]
            result, meta = caller(system_prompt, user_msg, image_paths, model)
            results[domain] = result
            run_meta[domain] = meta
            print(f"    {domain}: ✅ {meta['time']}s")
        except Exception as e:
            print(f"    {domain}: ❌ {e}")
            results[domain] = {}
            run_meta[domain] = {"error": str(e)}
    
    elapsed = time.time() - t0
    
    # Merge and score
    profile = merge_results(results)
    report = score_profile(profile)
    
    t1_score = report["summary"]["tier1_score"]
    t1_pct = report["summary"]["tier1_pct"]
    grade = report["summary"]["grade"]
    logo_score = report["summary"]["tier2_logo_score"]
    
    all_scores.append({
        "run": run,
        "tier1": t1_score,
        "tier1_pct": t1_pct,
        "grade": grade,
        "logo": logo_score,
        "time": round(elapsed, 1),
        "fields": {}
    })
    
    # Capture per-field scores
    for field, data in report["tier1"].items():
        if isinstance(data, dict) and "score" in data:
            all_scores[-1]["fields"][field] = data["score"]
    
    all_reports.append({"run": run, "profile": profile, "report": report, "meta": run_meta})
    
    print(f"    SCORE: {t1_pct}% ({grade}) | Logo: {logo_score}/20 | Time: {elapsed:.1f}s")


# ── Aggregate Stats ───────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  BENCHMARK RESULTS — {N_RUNS} runs")
print(f"{'='*60}")

# Per-run summary
print(f"\n  {'Run':<6} {'Tier1':>7} {'Grade':>6} {'Logo':>6} {'Time':>6}")
print(f"  {'─'*35}")
for s in all_scores:
    print(f"  {s['run']:<6} {s['tier1_pct']:>6.1f}% {s['grade']:>6} {s['logo']:>4}/20 {s['time']:>5.1f}s")

# Averages
avg_t1 = sum(s["tier1_pct"] for s in all_scores) / N_RUNS
avg_logo = sum(s["logo"] for s in all_scores) / N_RUNS
avg_time = sum(s["time"] for s in all_scores) / N_RUNS
min_t1 = min(s["tier1_pct"] for s in all_scores)
max_t1 = max(s["tier1_pct"] for s in all_scores)

print(f"  {'─'*35}")
print(f"  {'AVG':<6} {avg_t1:>6.1f}%        {avg_logo:>4.1f}/20 {avg_time:>5.1f}s")
print(f"  {'MIN':<6} {min_t1:>6.1f}%")
print(f"  {'MAX':<6} {max_t1:>6.1f}%")
print(f"  Spread: {max_t1 - min_t1:.1f}pp")

# Per-field averages
print(f"\n  PER-FIELD AVERAGES (Tier 1)")
print(f"  {'─'*50}")
field_names = list(all_scores[0]["fields"].keys())
for field in field_names:
    vals = [s["fields"].get(field, 0) for s in all_scores]
    avg = sum(vals) / len(vals)
    maxpt = {"brand_name_cn": 5, "brand_name_en": 5, "primary_color_hex": 15,
             "secondary_colors": 15, "pantone": 5, "chinese_font": 10,
             "english_font": 5, "brand_slogan": 10, "brand_category": 5,
             "pattern_count": 5, "pattern_names": 10, "color_formats": 10}.get(field, 10)
    pct = avg / maxpt * 100
    consistency = "✅" if all(v == vals[0] for v in vals) else f"σ={max(vals)-min(vals):.1f}"
    print(f"  {field:<25} {avg:>5.1f}/{maxpt:<3} ({pct:>5.1f}%)  {consistency}")

# Grade distribution
from collections import Counter
grades = Counter(s["grade"] for s in all_scores)
print(f"\n  GRADE DISTRIBUTION: {dict(grades)}")

# Save full benchmark
bench_path = output_dir / f"benchmark_v3_{timestamp}.json"
with open(bench_path, "w", encoding="utf-8") as f:
    json.dump({
        "config": {
            "n_runs": N_RUNS,
            "routes": {d: MODEL_ROUTES[d][1] for d in MODEL_ROUTES},
            "timestamp": timestamp,
        },
        "summary": {
            "avg_tier1_pct": round(avg_t1, 1),
            "min_tier1_pct": round(min_t1, 1),
            "max_tier1_pct": round(max_t1, 1),
            "spread_pp": round(max_t1 - min_t1, 1),
            "avg_logo": round(avg_logo, 1),
            "avg_time_s": round(avg_time, 1),
            "grades": dict(grades),
        },
        "runs": all_scores,
    }, f, indent=2, ensure_ascii=False)

print(f"\n  Benchmark saved: {bench_path}")
