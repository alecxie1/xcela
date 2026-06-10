"""
Brand Analyzer v3 — Modular Sub-Call Architecture

Splits brand analysis into focused domains, each with:
- Its own prompt (optimized for that extraction task)
- Its own page selection (only relevant pages)
- Its own model routing (best model per domain)

Domains:
1. COLORS   — extract palette with all formats (hex, RGB, CMYK, Pantone)
2. TYPOGRAPHY — extract font names and hierarchy
3. LOGO     — describe the logo mark precisely
4. COPY     — slogan, category, brand values
5. PATTERNS — decorative motifs and usage rules

Then merges into a single profile and scores.
"""

import base64, json, os, sys, time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env", override=True)

from openai import OpenAI
from google import genai
from google.genai import types
import anthropic

oai = OpenAI()
gem = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
anth = anthropic.Anthropic()

# ── Image Helpers ─────────────────────────────────────────────────

def load_images_oai(paths: list[str]) -> list[dict]:
    """Build OpenAI vision content parts."""
    parts = []
    for p in paths:
        with open(p, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()
        parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}})
    return parts

def load_images_gemini(paths: list[str]) -> list:
    """Build Gemini content parts."""
    parts = []
    for p in paths:
        with open(p, "rb") as f:
            data = f.read()
        parts.append(types.Part.from_bytes(data=data, mime_type="image/png"))
    return parts

def load_images_claude(paths: list[str]) -> list[dict]:
    """Build Claude vision content parts."""
    parts = []
    for p in paths:
        with open(p, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()
        parts.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}})
    return parts


# ── Model Callers ─────────────────────────────────────────────────

def call_gpt(system: str, user_text: str, image_paths: list[str], model: str = "gpt-4o") -> tuple[dict, dict]:
    content = load_images_oai(image_paths)
    content.append({"type": "text", "text": user_text})
    t0 = time.time()
    resp = oai.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
        max_tokens=2000, temperature=0.0,
    )
    elapsed = time.time() - t0
    text = resp.choices[0].message.content.strip()
    text = _clean_json(text)
    meta = {"model": model, "tokens_in": resp.usage.prompt_tokens, "tokens_out": resp.usage.completion_tokens, "time": round(elapsed, 1)}
    return json.loads(text), meta

def call_gemini(system: str, user_text: str, image_paths: list[str], model: str = "gemini-2.5-flash") -> tuple[dict, dict]:
    parts = load_images_gemini(image_paths)
    parts.append(types.Part.from_text(text=user_text))
    t0 = time.time()
    resp = gem.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            system_instruction=system, temperature=0.0, max_output_tokens=2000,
            response_mime_type="application/json",
        ),
    )
    elapsed = time.time() - t0
    text = _clean_json(resp.text.strip())
    meta = {"model": model, "tokens_in": resp.usage_metadata.prompt_token_count, "tokens_out": resp.usage_metadata.candidates_token_count, "time": round(elapsed, 1)}
    return json.loads(text), meta

def call_claude(system: str, user_text: str, image_paths: list[str], model: str = "claude-sonnet-4-5") -> tuple[dict, dict]:
    content = load_images_claude(image_paths)
    content.append({"type": "text", "text": user_text})
    t0 = time.time()
    resp = anth.messages.create(
        model=model, max_tokens=2000, system=system,
        messages=[{"role": "user", "content": content}],
    )
    elapsed = time.time() - t0
    text = _clean_json(resp.content[0].text.strip())
    meta = {"model": model, "tokens_in": resp.usage.input_tokens, "tokens_out": resp.usage.output_tokens, "time": round(elapsed, 1)}
    return json.loads(text), meta

def _clean_json(text: str) -> str:
    import re
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"): text = text[4:]
        text = text.strip()
    if not text.endswith("}"):
        last = text.rfind("}")
        if last > 0: text = text[:last + 1]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


# ── Domain Prompts ────────────────────────────────────────────────

COLORS_SYSTEM = """You are a color specification extraction system. You read brand guideline pages 
and extract EXACT color values as printed in the document.

CRITICAL: Read the PRINTED TEXT on each color swatch — the hex code, RGB values, CMYK values, 
and Pantone code. Do NOT estimate colors from the visual appearance of the swatch.

Process:
1. Find each color swatch on the page
2. Read the label/name next to it (in Chinese and English)
3. Read the PANTONE code character by character
4. Read the RGB values as three numbers
5. Read the CMYK values as four numbers  
6. Read the HTML/hex code character by character — verify: if RGB is 215/33/33, 
   then hex MUST be D72121 (R=215→D7, G=33→21, B=33→21). If the printed hex disagrees 
   with the printed RGB, report BOTH and flag the discrepancy.
7. Determine role: the first/main color is "primary", others are "secondary"

Return ONLY JSON:
{
  "colors": [
    {
      "hex": "#RRGGBB as printed",
      "rgb": [R, G, B],
      "cmyk": [C, M, Y, K],
      "pantone": "code as printed",
      "name_cn": "Chinese name",
      "name_en": "English name",
      "role": "primary|secondary"
    }
  ]
}"""

COLORS_USER = "These are the color specification pages from a brand guidelines document. Extract EVERY color with ALL its printed values. Read each hex digit, RGB number, CMYK number, and Pantone code individually from the text on the page."

TYPOGRAPHY_SYSTEM = """You are a typography extraction system. You read brand guideline pages and extract 
the EXACT font names as printed.

CRITICAL for Chinese font names: Read each Chinese character individually, stroke by stroke. 
Chinese font names are often 4-6 characters and may contain rare characters. 
Common mistakes: confusing 锦(jǐn, brocade) with 锐(ruì, sharp), or 朝(cháo) with other similar characters.

Look for:
1. The Chinese font name — usually displayed large with a sample sentence
2. The English/Latin font name — usually a well-known typeface family
3. Weight variations listed (Thin, Light, Regular, Medium, Bold, etc.)
4. Any hierarchy notes (which font for headlines vs body text)

Return ONLY JSON:
{
  "chinese_font": "exact Chinese font name as printed — read character by character",
  "english_font": "exact English font family name",
  "english_weights": ["list of weight names shown"],
  "hierarchy_notes": "any notes about which font is used where"
}"""

TYPOGRAPHY_USER = "This is the typography/font specification page from a brand guidelines document. Read the EXACT font names printed on the page. For the Chinese font name, read each character individually."

LOGO_SYSTEM = """You are a logo analysis system. You describe brand logos with extreme precision 
so that an AI image generator could recreate them.

RULES:
- Describe ONLY what you literally see — shapes, silhouettes, colors, composition
- Do NOT interpret meaning or symbolism unless it's visually obvious
- Do NOT default to saying "yin-yang" unless you can describe the SPECIFIC forms that create the yin-yang effect
- Focus on: what ANIMALS, OBJECTS, or ABSTRACT FORMS are depicted
- Describe NEGATIVE SPACE: where white/empty areas form distinct shapes
- Describe the OUTER BOUNDARY: circle, square, rounded rectangle, etc.
- Note any ASYMMETRY, ROTATION, or DIRECTIONAL FLOW

Return ONLY JSON:
{
  "outer_shape": "the boundary shape",
  "fill_color": "the dominant color of the mark",
  "inner_elements": ["list of distinct visual elements inside, described precisely"],
  "negative_space": "how white/empty space is used — what shapes does it form?",
  "composition": "overall layout — symmetry, rotation, balance, direction of movement",
  "full_description": "complete 2-3 sentence description combining all the above, precise enough for recreation"
}"""

LOGO_USER = "This is the logo page from a brand guidelines document. Describe EXACTLY what you see in the logo — every shape, every silhouette, every use of negative space. What specific forms (animals? objects? abstract shapes?) are depicted inside the circle? Don't just say 'yin-yang' — describe the actual visual elements that create the composition."

COPY_SYSTEM = """You are a brand copy extraction system. You read brand guideline pages and extract 
the exact text of slogans, category names, and brand values.

RULES:
- Read text EXACTLY as printed, in the ORIGINAL LANGUAGE (Chinese)
- Include original punctuation (commas, periods, exclamation marks)
- Do NOT translate Chinese text to English
- The brand category (品类/品牌品类) will be a short Chinese phrase
- The slogan (广告语/品牌广告语) will be a memorable Chinese phrase
- Brand values may be longer text explaining the company's philosophy

Return ONLY JSON:
{
  "brand_name_cn": "Chinese brand name exactly as shown",
  "brand_name_en": "English brand name exactly as shown",
  "brand_slogan": "exact slogan with original punctuation",
  "brand_category": "exact category name in Chinese",
  "brand_values": "summary of stated brand values/philosophy"
}"""

COPY_USER = "These are the brand name, slogan, category, and values pages from a brand guidelines document. Read each text EXACTLY as printed in Chinese. Do not translate."

PATTERNS_SYSTEM = """You are a pattern/motif extraction system. You read brand guideline pages showing 
decorative patterns and describe each motif individually.

For each motif:
1. Read its Chinese name label
2. Describe the visual form (shape, symmetry, style)
3. Note whether it's geometric, organic, illustrative, etc.

Also note any usage rules shown (how patterns should be applied, cropped, etc.)

Return ONLY JSON:
{
  "motifs": [
    {"name_cn": "Chinese name", "visual_description": "what it looks like"}
  ],
  "usage_rules": ["any application rules shown"],
  "arrangement": "how motifs are arranged together (grid, scatter, etc.)"
}"""

PATTERNS_USER = "These are the pattern/motif pages from a brand guidelines document. Identify each individual motif by its Chinese name and describe its visual form."


# ── Page Groups ───────────────────────────────────────────────────

PAGES_DIR = "/tmp/taijibao_pages"

PAGE_GROUPS = {
    "colors":     [24, 25],           # Primary + secondary color pages only
    "typography": [22],               # Typography page only
    "logo":       [4, 5, 7, 13],      # Overview, logo graphic, combinations, logo colors
    "copy":       [4, 19, 20, 18],    # Overview, category, slogan, brand values
    "patterns":   [27, 28, 29],       # Pattern motifs, continuous pattern, usage rules
}

# ── Model Routing ─────────────────────────────────────────────────
# Based on head-to-head results:
# GPT-4o: best OCR (font names, exact text reading) 
# Gemini 2.5 Pro: best color perception (Pearl White ΔE=3.5)
# Gemini 2.5 Flash: best logo description (12/20)
# Claude: untested — let's see on logo (known for detailed descriptions)

MODEL_ROUTES = {
    "colors":     ("gpt",    "gpt-4o"),             # Best OCR for printed color values
    "typography": ("gpt",    "gpt-4o"),             # Best OCR for Chinese chars
    "logo":       ("claude", "claude-sonnet-4-5"),  # Test Claude for detailed description
    "copy":       ("gpt",    "gpt-4o"),             # Best exact text reading
    "patterns":   ("gemini", "gemini-2.5-flash"),   # Good enough, cheapest
}

CALLERS = {
    "gpt": call_gpt,
    "gemini": call_gemini,
    "claude": call_claude,
}


# ── Merge ─────────────────────────────────────────────────────────

def merge_results(results: dict) -> dict:
    """Merge domain-specific results into a single brand profile."""
    colors = results.get("colors", {})
    typo = results.get("typography", {})
    logo = results.get("logo", {})
    copy = results.get("copy", {})
    patterns = results.get("patterns", {})
    
    # Build palette in standard format
    palette = []
    for c in colors.get("colors", []):
        palette.append({
            "hex": c.get("hex"),
            "rgb": c.get("rgb"),
            "cmyk": c.get("cmyk"),
            "pantone": c.get("pantone"),
            "name_cn": c.get("name_cn", ""),
            "name_en": c.get("name_en", ""),
            "role": c.get("role", "secondary"),
        })
    
    # Build pattern elements
    pattern_elements = []
    for m in patterns.get("motifs", []):
        pattern_elements.append(f"{m.get('name_cn', '')}: {m.get('visual_description', '')}")
    
    profile = {
        "brand_name": copy.get("brand_name_cn", ""),
        "brand_name_english": copy.get("brand_name_en", ""),
        "palette": palette,
        "typography": {
            "chinese_font": typo.get("chinese_font", ""),
            "english_font": typo.get("english_font", ""),
            "english_weights": typo.get("english_weights", []),
        },
        "brand_slogan": copy.get("brand_slogan", ""),
        "brand_category": copy.get("brand_category", ""),
        "logo_description": logo.get("full_description", ""),
        "pattern_elements": pattern_elements,
        "mood": [],
        "confidence": "high",
        # Keep raw domain results for debugging
        "_raw": {
            "logo_detail": logo,
            "pattern_rules": patterns.get("usage_rules", []),
            "brand_values": copy.get("brand_values", ""),
            "typo_hierarchy": typo.get("hierarchy_notes", ""),
        }
    }
    return profile


# ── Main ──────────────────────────────────────────────────────────

def main():
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*60}")
    print(f"  BRAND ANALYZER v3 — Modular Sub-Call Architecture")
    print(f"  {timestamp}")
    print(f"{'='*60}")
    
    results = {}
    all_meta = {}
    
    domains = [
        ("colors",     COLORS_SYSTEM,     COLORS_USER),
        ("typography", TYPOGRAPHY_SYSTEM,  TYPOGRAPHY_USER),
        ("logo",       LOGO_SYSTEM,       LOGO_USER),
        ("copy",       COPY_SYSTEM,       COPY_USER),
        ("patterns",   PATTERNS_SYSTEM,   PATTERNS_USER),
    ]
    
    for domain, system_prompt, user_msg in domains:
        provider, model = MODEL_ROUTES[domain]
        pages = PAGE_GROUPS[domain]
        image_paths = [f"{PAGES_DIR}/page_{p:02d}.png" for p in pages]
        
        print(f"\n  ┌─ {domain.upper()}")
        print(f"  │  Model: {model}")
        print(f"  │  Pages: {pages}")
        
        try:
            caller = CALLERS[provider]
            result, meta = caller(system_prompt, user_msg, image_paths, model)
            results[domain] = result
            all_meta[domain] = meta
            print(f"  │  Tokens: {meta['tokens_in']} in / {meta['tokens_out']} out")
            print(f"  │  Time: {meta['time']}s")
            
            # Quick preview
            if domain == "colors":
                for c in result.get("colors", []):
                    print(f"  │  {c.get('hex', '?')} {c.get('name_cn', '?')} Pantone:{c.get('pantone', '?')}")
            elif domain == "typography":
                print(f"  │  CN: {result.get('chinese_font', '?')}")
                print(f"  │  EN: {result.get('english_font', '?')}")
            elif domain == "logo":
                desc = result.get("full_description", "?")
                print(f"  │  {desc[:120]}...")
            elif domain == "copy":
                print(f"  │  Slogan: {result.get('brand_slogan', '?')}")
                print(f"  │  Category: {result.get('brand_category', '?')}")
            elif domain == "patterns":
                for m in result.get("motifs", []):
                    print(f"  │  {m.get('name_cn', '?')}: {m.get('visual_description', '?')[:60]}")
            
            print(f"  └─ ✅ OK")
            
        except Exception as e:
            print(f"  └─ ❌ FAILED: {e}")
            results[domain] = {}
            all_meta[domain] = {"error": str(e)}
    
    # ── Merge ──
    print(f"\n  Merging results...")
    profile = merge_results(results)
    
    # Save profile
    profile_path = output_dir / f"taijibao_profile_v3_{timestamp}.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    print(f"  Profile: {profile_path}")
    
    # Save raw domain results
    raw_path = output_dir / f"taijibao_raw_v3_{timestamp}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"domains": results, "meta": all_meta}, f, indent=2, ensure_ascii=False)
    
    # ── Score ──
    print(f"\n  Scoring...")
    from score_brand_analysis import score_profile, print_report
    report = score_profile(profile)
    print_report(report)
    
    # Save score
    score_path = output_dir / f"taijibao_score_v3_{timestamp}.json"
    with open(score_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # ── Cost Summary ──
    total_time = sum(m.get("time", 0) for m in all_meta.values())
    print(f"\n  ┌─ COST SUMMARY")
    print(f"  │  Total time: {total_time:.1f}s")
    for domain, meta in all_meta.items():
        if "error" not in meta:
            print(f"  │  {domain}: {meta['model']} — {meta['tokens_in']}+{meta['tokens_out']} tokens, {meta['time']}s")
    print(f"  └─")


if __name__ == "__main__":
    main()
