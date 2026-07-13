"""
Brand Analyzer v2 — improved prompt targeting known failure modes.
Runs GPT-4o Vision, outputs structured JSON, scores against ground truth.
"""

import base64, json, os, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env", override=True)

from openai import OpenAI
client = OpenAI()

# ── IMPROVED SYSTEM PROMPT ────────────────────────────────────────

SYSTEM_PROMPT = """You are a brand identity extraction system. Your job is to read brand guideline pages 
and extract a machine-readable profile with EXACT values from the document.

CRITICAL RULES:
1. COLOR VALUES: Read EVERY character of hex codes, RGB values, CMYK values, and Pantone codes 
   DIRECTLY from the printed text in the images. Do NOT estimate colors from the swatch appearance.
   If the page shows "RGB: 215/33/33", report exactly {"rgb": [215, 33, 33]}.
   If the page shows "HTML: D70321", report exactly {"hex": "#D70321"}.
   If the page shows "PANTONE: 2035C", report exactly {"pantone": "2035C"}.
   Include ALL color specification formats shown (hex, RGB, CMYK, Pantone).

2. TYPOGRAPHY: Read the EXACT font name as printed. Chinese font names often contain 
   rare characters — read them stroke by stroke. If the page shows a font sample with 
   its name, copy that name exactly. Do not substitute a different font name.

3. BRAND CATEGORY (品类/品牌品类): This will be in CHINESE. Read the exact Chinese text 
   shown on the 品牌品类 page. Do NOT translate it to English.

4. LOGO DESCRIPTION: Describe what you literally SEE in the logo image:
   - The outer shape (circle, square, shield, etc.)
   - What is depicted INSIDE (animals, objects, abstract forms)
   - How negative space is used (white areas that form shapes)
   - The visual composition (symmetry, rotation, balance)
   Do NOT default to generic descriptions. Be specific to THIS logo.

5. SLOGAN (品牌广告语): Read the exact Chinese text. Include punctuation.

Return ONLY a JSON object — no markdown fences, no explanation:

{
  "brand_name": "Chinese name exactly as shown",
  "brand_name_english": "English name exactly as shown",
  "palette": [
    {
      "hex": "#RRGGBB",
      "rgb": [R, G, B],
      "cmyk": [C, M, Y, K],
      "pantone": "code as printed",
      "name_cn": "Chinese color name",
      "name_en": "English color name", 
      "role": "primary|secondary|neutral|background"
    }
  ],
  "typography": {
    "chinese_font": "exact font name as printed on the page",
    "english_font": "exact font family name",
    "english_weights": ["weight names listed"]
  },
  "brand_slogan": "exact slogan text in Chinese with punctuation",
  "brand_category": "exact category text in Chinese as shown on the 品类 page",
  "logo_description": "detailed literal description of what you see in the logo",
  "pattern_elements": ["each motif with its Chinese name and visual description"],
  "mood": ["3-6 brand personality adjectives"],
  "style_descriptors": ["3-6 visual style descriptions specific to this brand"],
  "imagery_direction": "1-2 sentences on photo/illustration style based on the guidelines",
  "dos": ["3-4 concrete design rules extracted from the manual"],
  "donts": ["3-4 concrete prohibitions extracted from the manual"],
  "headline_treatments": [{"text": "sample headline in Chinese", "rationale": "why"}],
  "confidence": "high|medium|low"
}"""


def analyze_brand(image_paths: list[str], run_id: str = "") -> dict:
    content = []
    for path in image_paths:
        with open(path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}
        })
    
    content.append({
        "type": "text",
        "text": (
            "These are pages from a Chinese brand's Visual Identity (VI) manual. "
            "Extract the complete brand profile. "
            "READ ALL COLOR VALUES (hex, RGB, CMYK, Pantone) CHARACTER BY CHARACTER from the printed text. "
            "READ THE FONT NAME CHARACTER BY CHARACTER from the typography page. "
            "READ THE BRAND CATEGORY (品类) IN CHINESE from the 品牌品类 page. "
            "For the logo, describe EXACTLY what you see — shapes, animals, negative space, composition."
        )
    })
    
    print(f"  [{run_id}] Sending {len(image_paths)} pages to GPT-4o Vision...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        max_tokens=3000,
        temperature=0.0,  # deterministic
    )
    
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    
    tokens = response.usage
    cost_in = tokens.prompt_tokens * 2.5 / 1_000_000  # gpt-4o input
    cost_out = tokens.completion_tokens * 10 / 1_000_000  # gpt-4o output
    print(f"  [{run_id}] Tokens: {tokens.prompt_tokens} in / {tokens.completion_tokens} out")
    print(f"  [{run_id}] Est. cost: ${cost_in + cost_out:.4f}")
    
    return json.loads(text)


def main():
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    pages_dir = "/tmp/taijibao_pages"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Key pages: overview, logo, logo colors, typography, primary color, secondary colors, 
    # category, slogan, patterns, pattern continuous
    key_pages = [4, 5, 13, 19, 20, 22, 24, 25, 27, 28]
    image_paths = [f"{pages_dir}/page_{p:02d}.png" for p in key_pages]
    
    # Verify pages exist
    for p in image_paths:
        if not os.path.exists(p):
            print(f"❌ Missing: {p}")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  BRAND ANALYSIS v2 — {timestamp}")
    print(f"  Pages: {key_pages} ({len(key_pages)} pages)")
    print(f"  Model: gpt-4o, temp=0.0")
    print(f"{'='*60}")
    
    # Run analysis
    profile = analyze_brand(image_paths, run_id="v2")
    
    # Save profile
    profile_path = output_dir / f"taijibao_profile_v2_{timestamp}.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    print(f"\n  Profile saved: {profile_path}")
    
    # Print key extractions
    print(f"\n  Quick check:")
    print(f"  Brand: {profile.get('brand_name')} ({profile.get('brand_name_english')})")
    print(f"  Slogan: {profile.get('brand_slogan')}")
    print(f"  Category: {profile.get('brand_category')}")
    cn_font = profile.get("typography", {}).get("chinese_font", "?")
    print(f"  CN Font: {cn_font}")
    for c in profile.get("palette", []):
        extras = []
        if c.get("rgb"): extras.append(f"RGB:{c['rgb']}")
        if c.get("cmyk"): extras.append(f"CMYK:{c['cmyk']}")
        if c.get("pantone"): extras.append(f"Pantone:{c['pantone']}")
        print(f"  Color: {c.get('hex')} {c.get('name_cn', c.get('name', ''))} ({c.get('role')}) {' '.join(extras)}")
    
    # Score it
    print(f"\n  Running scorer...")
    from score_brand_analysis import score_profile, print_report
    report = score_profile(profile)
    print_report(report)
    
    # Save score
    score_path = output_dir / f"taijibao_score_v2_{timestamp}.json"
    with open(score_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
