# Brand Analysis: Evaluation Framework

## What Success Looks Like

The brand analyzer takes a PDF of brand guidelines and outputs a structured profile
that a downstream image generator can consume. **The profile is only as good as its
accuracy against the source PDF.** If colors are wrong, generation will be wrong.

---

## 1. Information Taxonomy — What Brand PDFs Contain

Based on the 太极堡 32-page VI manual and cross-referenced against public guidelines
(Slack, NASA, ScanSource, Spotify), brand PDFs contain these information categories:

### TIER 1 — Hard Data (machine-verifiable, exact values)
These have ONE correct answer. Extraction is pass/fail.

| Field | Example (太极堡) | Verification Method |
|-------|-------------------|---------------------|
| Brand name (CN) | 太极堡 | Exact string match |
| Brand name (EN) | TAICHI BURGER | Exact string match (case-insensitive) |
| Primary color hex | #D70321 | ΔE ≤ 3 from ground truth |
| Primary color RGB | 215/33/33 | Exact match |
| Primary color CMYK | 0/97/100/3 | Exact match |
| Primary color Pantone | 2035C | Exact string match |
| Secondary color hexes | #D7A569, #000000, #EEE4D8 | ΔE ≤ 3 each |
| Chinese font name | 锦华明朝体 | Fuzzy string match (≥80% similarity) |
| English font name | Helvetica | Exact match (family name) |
| Brand slogan | 手作多汁，东方汉堡 | Exact string match |
| Brand category | 东方汉堡 | Exact string match |
| Logo min print size | 16mm | Numeric match |
| Logo min screen size | 80px | Numeric match |
| Number of pattern motifs | 5 | Exact count |
| Pattern motif names | 八角,花椒,桂皮,胡椒,香叶 | Set match (all 5 present) |

### TIER 2 — Structured Rules (verifiable against source, but require judgment)
These have correct answers but need semantic comparison, not string matching.

| Field | Example (太极堡) | Verification Method |
|-------|-------------------|---------------------|
| Logo description | Circular, red, stylized animal silhouettes, yin-yang flow | Checklist of required elements |
| Logo variations listed | Standalone, horizontal bilingual, vertical bilingual, English-only | Set completeness |
| Color usage rules | Red bg → white logo; other bg → red logo only | Semantic match against source rules |
| Safe distance spec | Measured in logo-width units | Presence + correctness |
| Background rules | Only red background allows reversed (white) logo | Rule extraction accuracy |
| Improper use rules | No stretching, no rotating, no recoloring, no adding elements | Set completeness |
| Pattern usage rules | Crop edges in application, don't scatter randomly | Semantic match |
| Typography hierarchy | Chinese headlines = 锦华明朝体; English = Helvetica weights | Structure match |
| Brand values/voice | Employee-first, respect, growth | Presence + key themes |

### TIER 3 — Subjective/Interpretive (useful but not objectively scorable)
These add value to the profile but don't have a single correct answer.

| Field | Example | Value |
|-------|---------|-------|
| Mood descriptors | "artisanal, bold, culturally rooted" | Guides generation tone |
| Imagery direction | "close-ups of juicy burgers with steam" | Guides photo style |
| Style descriptors | "East-meets-West, high-contrast red/white" | Guides aesthetic |
| Headline suggestions | "一口咬下，东方滋味" | Creative starting points |
| Dos/don'ts (generated) | Design rules inferred beyond what's stated | Bonus value |

---

## 2. Ground Truth — 太极堡 Reference

This is the SINGLE SOURCE OF TRUTH for scoring. Every field verified by direct
visual inspection of the PDF pages.

```json
{
  "_meta": {
    "source_pdf": "太极堡VI-250303.pdf",
    "pages": 32,
    "verified_by": "Manual inspection, June 4 2026",
    "brand_type": "Fast-casual restaurant chain (Chinese market)"
  },
  "tier1_hard": {
    "brand_name_cn": "太极堡",
    "brand_name_en": "TAICHI BURGER",
    "primary_color": {
      "name_cn": "银朱红",
      "name_en": "VERMILION",
      "hex": "#D70321",
      "rgb": [215, 33, 33],
      "cmyk": [0, 97, 100, 3],
      "pantone": "2035C"
    },
    "secondary_colors": [
      {
        "name_cn": "大地金",
        "name_en": "EARTH GOLD",
        "hex": "#D7A569",
        "rgb": [219, 165, 105],
        "cmyk": [5, 31, 63, 5],
        "pantone": "7509C"
      },
      {
        "name_cn": "墨湖黑",
        "name_en": "INK BLACK",
        "hex": "#000000",
        "rgb": [0, 0, 0],
        "cmyk": [60, 40, 40, 100],
        "pantone": "RICH BLACK"
      },
      {
        "name_cn": "珍珠白",
        "name_en": "PEARL WHITE",
        "hex": "#EEE4D8",
        "rgb": [238, 228, 216],
        "cmyk": [0, 3, 7, 7],
        "pantone": "11-0605"
      }
    ],
    "typography": {
      "chinese_font": "锦华明朝体",
      "english_font": "Helvetica",
      "english_weights": ["Thin", "Light", "Regular"]
    },
    "brand_slogan": "手作多汁，东方汉堡",
    "brand_category": "东方汉堡",
    "logo_min_print_mm": 16,
    "logo_min_screen_px": 80,
    "pattern_motifs": ["八角", "花椒", "桂皮", "胡椒", "香叶"],
    "pattern_motif_count": 5
  },
  "tier2_rules": {
    "logo_elements": [
      "circular shape",
      "red fill",
      "stylized animal silhouette(s)",
      "white negative space",
      "yin-yang / tai-chi rotational composition"
    ],
    "logo_variations": [
      "standalone graphic mark",
      "horizontal bilingual combination (preferred for most contexts)",
      "vertical bilingual combination",
      "horizontal English-only combination",
      "vertical English-only combination"
    ],
    "color_usage_rules": [
      "On red background: logo and wordmark in white (reversed)",
      "On all other backgrounds: logo and wordmark in primary red only",
      "Never change logo colors arbitrarily"
    ],
    "improper_uses": [
      "Do not change element proportions",
      "Do not outline the logo",
      "Do not stretch the logo",
      "Do not rotate/tilt arbitrarily",
      "Do not add other elements to the logo",
      "Do not move graphic or text positions",
      "Do not change logo colors",
      "Do not replace logo elements"
    ],
    "pattern_usage_rules": [
      "Crop pattern edges when applying (don't show full grid boundary)",
      "Use four-square continuous arrangement",
      "Do not scatter pattern elements randomly"
    ],
    "safe_distance": "Defined by logo-width proportional units",
    "brand_values": "Employee-first culture: respect, growth, dignity. Serve employees well so they serve customers well."
  }
}
```

---

## 3. Scoring System

### Tier 1 Score (0-100 points, 60% weight)

| Metric | Points | Scoring |
|--------|--------|---------|
| Brand name CN | 5 | Exact match = 5, partial = 2, wrong = 0 |
| Brand name EN | 5 | Exact match = 5, case-insensitive |
| Primary color hex | 15 | ΔE ≤ 1 = 15, ΔE ≤ 3 = 12, ΔE ≤ 5 = 8, ΔE ≤ 10 = 4, ΔE > 10 = 0 |
| Secondary color hexes (×3) | 15 | 5 pts each, same ΔE scale as primary |
| Primary Pantone code | 5 | Exact = 5, wrong = 0 |
| Chinese font name | 10 | Exact = 10, fuzzy match ≥80% = 7, close = 4, wrong = 0 |
| English font family | 5 | Exact family = 5, wrong = 0 |
| Brand slogan | 10 | Exact = 10, minor diff = 7, paraphrase = 3, wrong = 0 |
| Brand category | 5 | Exact = 5, close = 3, wrong = 0 |
| Pattern motif count | 5 | Exact = 5, off by 1 = 3, off by 2+ = 0 |
| Pattern motif names | 10 | 2 pts each (all 5), partial credit per name |
| Color value format (RGB/CMYK present) | 10 | Full specs = 10, hex only = 5, missing = 0 |
| **Total Tier 1** | **100** | |

### Tier 2 Score (0-100 points, 30% weight)

| Metric | Points | Scoring |
|--------|--------|---------|
| Logo description completeness | 20 | 4 pts per required element (5 elements) |
| Logo variations identified | 15 | 3 pts per variation (5 variations) |
| Color usage rules | 15 | 5 pts per rule (3 rules) |
| Improper use rules | 15 | ~2 pts per rule (8 rules) |
| Pattern usage rules | 10 | ~3 pts per rule (3 rules) |
| Typography hierarchy | 10 | Correct structure = 10 |
| Brand values present | 5 | Key themes captured = 5 |
| Safe distance mentioned | 5 | Present + described = 5 |
| Background rules | 5 | Present + correct = 5 |
| **Total Tier 2** | **100** | |

### Tier 3 Score (0-100 points, 10% weight)

| Metric | Points | Scoring |
|--------|--------|---------|
| Mood descriptors (relevant, non-generic) | 25 | Human judgment |
| Imagery direction (actionable) | 25 | Human judgment |
| Style descriptors (specific to this brand) | 25 | Human judgment |
| Headline suggestions (on-brand, in Chinese) | 25 | Human judgment |
| **Total Tier 3** | **100** | |

### Overall Score

```
OVERALL = (Tier1 × 0.60) + (Tier2 × 0.30) + (Tier3 × 0.10)
```

### Grade Thresholds

| Grade | Score | Meaning |
|-------|-------|---------|
| A | ≥ 90 | Production-ready: profile can drive generation without human review |
| B | 75-89 | Usable with spot-checks: review colors and key fields before generation |
| C | 60-74 | Needs correction: human must fix multiple fields before generation |
| D | 40-59 | Major gaps: more wrong than right |
| F | < 40 | Extraction failed: don't use this profile |

---

## 4. Test Protocol

For each brand analyzer run:

1. **Input**: Which PDF pages were sent, what resolution, what model, what prompt
2. **Run**: Execute the analyzer, capture JSON output
3. **Score**: Run automated Tier 1 scoring + manual Tier 2/3 review
4. **Record**: Log run number, parameters, scores, specific errors, and what to change

### Variables to Test

| Variable | Options |
|----------|---------|
| Model | gpt-4o, gpt-4o-mini, gpt-5, gpt-5-mini |
| Page selection | All 32 pages, key 8 pages, minimal 4 pages (logo + color + font + pattern) |
| Page resolution | 100, 150, 200, 300 DPI |
| Prompt style | Strict JSON schema, free-form → JSON, structured checklist |
| Temperature | 0.0, 0.1, 0.3 |
| Number of images per call | All pages in one call vs. grouped calls |

### What We're Optimizing For

1. **Accuracy** — correct extraction (Tier 1 score)
2. **Completeness** — nothing important missed (Tier 2 score)
3. **Cost** — tokens consumed per analysis
4. **Speed** — wall clock time
5. **Robustness** — consistent results across re-runs (run 3× minimum)

---

## 5. Known Failure Modes (from initial tests)

| Failure | Frequency | Root Cause | Fix |
|---------|-----------|------------|-----|
| Hex code OCR errors | Common | Vision model misreads small text on color swatches | Explicitly instruct character-by-character reading; validate RGB→hex math |
| Font name errors | Common | Similar-looking Chinese characters (锦 vs 锐) | Cross-reference with Latin font name on same page |
| Pearl White hex off | Observed | Low-contrast swatch hard to read | Send color page at higher DPI (300+) |
| Logo described as generic yin-yang | Common | Model defaults to known concepts | Request "describe what you SEE, not what you think it represents" |
| Colors counted wrong | Rare | Model confuses primary vs. secondary sections | Separate color pages explicitly in prompt |
