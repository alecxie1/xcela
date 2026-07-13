"""
Brand Analyzer — Gemini Vision
Same prompt as v2, swapped to Google Gemini API.
Tests multiple Gemini models for comparison.
"""

import base64, json, os, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env", override=True)

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Same system prompt as GPT v2
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

USER_MSG = (
    "These are pages from a Chinese brand's Visual Identity (VI) manual. "
    "Extract the complete brand profile. "
    "READ ALL COLOR VALUES (hex, RGB, CMYK, Pantone) CHARACTER BY CHARACTER from the printed text. "
    "READ THE FONT NAME CHARACTER BY CHARACTER from the typography page. "
    "READ THE BRAND CATEGORY (品类) IN CHINESE from the 品牌品类 page. "
    "For the logo, describe EXACTLY what you see — shapes, animals, negative space, composition."
)


def analyze_brand_gemini(image_paths: list[str], model_name: str, run_id: str = "") -> dict:
    """Analyze brand pages with a Gemini vision model."""
    
    parts = []
    for path in image_paths:
        with open(path, "rb") as f:
            data = f.read()
        parts.append(types.Part.from_bytes(data=data, mime_type="image/png"))
    
    parts.append(types.Part.from_text(text=USER_MSG))
    
    print(f"  [{run_id}] Sending {len(image_paths)} pages to {model_name}...")
    
    import time
    t0 = time.time()
    
    response = client.models.generate_content(
        model=model_name,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0,
            max_output_tokens=4000,
            response_mime_type="application/json",
        ),
    )
    
    elapsed = time.time() - t0
    
    text = response.text.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    # Strip trailing incomplete JSON (Gemini sometimes truncates)
    if not text.endswith("}"):
        # Find the last complete object
        last_brace = text.rfind("}")
        if last_brace > 0:
            text = text[:last_brace + 1]
    
    usage = response.usage_metadata
    print(f"  [{run_id}] Tokens: {usage.prompt_token_count} in / {usage.candidates_token_count} out")
    print(f"  [{run_id}] Time: {elapsed:.1f}s")
    
    import re
    # Fix trailing commas before } or ] (common Gemini issue)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Fix single quotes → double quotes
    # Only do this if standard parse fails
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try ast.literal_eval as fallback for Python-style dicts
        import ast
        try:
            return ast.literal_eval(text)
        except:
            pass
        # Last resort: save raw text for debugging
        debug_path = f"/home/alecx/workspace/handyprint-design-tool/output/debug_{run_id}.txt"
        with open(debug_path, "w") as f:
            f.write(text)
        print(f"  [{run_id}] Raw output saved to {debug_path}")
        raise


def main():
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    pages_dir = "/tmp/taijibao_pages"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    key_pages = [4, 5, 13, 19, 20, 22, 24, 25, 27, 28]
    image_paths = [f"{pages_dir}/page_{p:02d}.png" for p in key_pages]
    
    for p in image_paths:
        if not os.path.exists(p):
            print(f"❌ Missing: {p}")
            sys.exit(1)
    
    # Models to test
    models = [
        ("gemini-2.5-pro", "g25pro"),
        ("gemini-2.5-flash", "g25flash"),
        ("gemini-3.5-flash", "g35flash"),
    ]
    
    from score_brand_analysis import score_profile, print_report
    
    results = []
    
    for model_name, tag in models:
        print(f"\n{'='*60}")
        print(f"  MODEL: {model_name}")
        print(f"  Pages: {key_pages} ({len(key_pages)} pages)")
        print(f"{'='*60}")
        
        try:
            profile = analyze_brand_gemini(image_paths, model_name, run_id=tag)
            
            # Save profile
            profile_path = output_dir / f"taijibao_profile_{tag}_{timestamp}.json"
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            # Quick check
            print(f"\n  Quick check:")
            print(f"  Brand: {profile.get('brand_name')} ({profile.get('brand_name_english')})")
            print(f"  Slogan: {profile.get('brand_slogan')}")
            print(f"  Category: {profile.get('brand_category')}")
            cn_font = profile.get("typography", {}).get("chinese_font", "?")
            print(f"  CN Font: {cn_font}")
            for c in profile.get("palette", []):
                extras = []
                if c.get("rgb"): extras.append(f"RGB:{c['rgb']}")
                if c.get("pantone"): extras.append(f"Ptn:{c['pantone']}")
                print(f"    {c.get('hex')} {c.get('name_cn', c.get('name', ''))} ({c.get('role')}) {' '.join(extras)}")
            
            # Score
            report = score_profile(profile)
            print_report(report)
            
            results.append({
                "model": model_name,
                "tier1_score": report["summary"]["tier1_score"],
                "tier1_pct": report["summary"]["tier1_pct"],
                "grade": report["summary"]["grade"],
                "logo_score": report["summary"]["tier2_logo_score"],
            })
            
            # Save score
            score_path = output_dir / f"taijibao_score_{tag}_{timestamp}.json"
            with open(score_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"\n  ❌ FAILED: {e}")
            results.append({"model": model_name, "tier1_pct": 0, "grade": "FAIL", "error": str(e)})
    
    # ── Comparison Table ──
    print(f"\n{'='*60}")
    print(f"  HEAD-TO-HEAD COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Model':<25} {'Tier1':>6} {'Grade':>6} {'Logo':>6}")
    print(f"  {'─'*50}")
    
    # Add GPT-4o v2 for reference
    print(f"  {'gpt-4o (v2 baseline)':<25} {'96.3':>6} {'A':>6} {'8/20':>6}")
    
    for r in results:
        if "error" in r:
            print(f"  {r['model']:<25} {'FAIL':>6}")
        else:
            print(f"  {r['model']:<25} {r['tier1_pct']:>5.1f}% {r['grade']:>6} {r['logo_score']:>3}/20")


if __name__ == "__main__":
    main()
