"""
太极堡 Full Pipeline Test — GPT Vision Analysis + GPT Image Generation
Uses OpenAI for everything: brand analysis (GPT-4o vision) + image gen (gpt-image-1)
"""

import base64, json, os, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env", override=True)

from openai import OpenAI
client = OpenAI()

# ── Step 1: Extract key pages from PDF ─────────────────────────────

def extract_pages(pdf_path: str, page_nums: list[int], out_dir: str) -> list[str]:
    import fitz
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    paths = []
    for p in page_nums:
        page = doc[p - 1]  # 1-indexed
        pix = page.get_pixmap(dpi=200)
        path = os.path.join(out_dir, f"page_{p:02d}.png")
        pix.save(path)
        paths.append(path)
        print(f"  Extracted page {p} ({pix.width}x{pix.height})")
    doc.close()
    return paths


# ── Step 2: Brand Analysis via GPT-4o Vision ──────────────────────

ANALYSIS_PROMPT = """You are a senior brand strategist analyzing a Visual Identity (VI) manual.
These images are pages from the same brand's guidelines document.

Return ONLY a JSON object — no markdown, no explanation, no code fences:

{
  "brand_name": "...",
  "brand_name_english": "...",
  "palette": [{"hex":"#RRGGBB","name":"...","role":"primary|secondary|accent|neutral|background"}],
  "typography": {"chinese_font":"...","english_font":"...","feel":"..."},
  "mood": ["3-6 adjectives"],
  "style_descriptors": ["3-6 visual style phrases"],
  "imagery_direction": "1-2 sentences on photo/illustration style",
  "logo_description": "precise visual description of the logo mark — shape, colors, motifs, composition",
  "pattern_elements": ["each decorative motif described individually"],
  "brand_category": "...",
  "brand_slogan": "...",
  "dos": ["3-4 concrete design rules from the manual"],
  "donts": ["3-4 concrete design rules from the manual"],
  "headline_treatments": [{"text":"on-brand sample headline in Chinese","rationale":"why"}],
  "confidence": "high|medium|low"
}

CRITICAL RULES:
- Read hex color values CHARACTER BY CHARACTER from the color specification pages. Double-check each digit.
- palette must have 3-6 colors with hex values EXACTLY as printed in the manual
- If you see RGB values like 215/33/33, convert correctly: R=215→D7, G=33→21, B=33→21 → #D72121
- logo_description must be precise enough to guide an AI image generator
- All sample headlines must be in Chinese (this is a Chinese brand)"""


def analyze_brand(image_paths: list[str]) -> dict:
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
        "text": "Analyze these brand guideline pages from the same VI manual. Extract the complete brand profile as JSON. READ COLOR HEX VALUES CAREFULLY — check each character against the printed values."
    })
    
    print(f"\n🔍 Analyzing {len(image_paths)} pages with GPT-4o Vision...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": content}
        ],
        max_tokens=3000,
        temperature=0.1,
    )
    
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    
    tokens = response.usage
    print(f"  Tokens: {tokens.prompt_tokens} in / {tokens.completion_tokens} out")
    
    return json.loads(text)


# ── Step 3: Prompt Assembly from Profile ───────────────────────────

def build_prompt(profile: dict, campaign_theme: str, format_name: str) -> str:
    colors = profile["palette"]
    primary = next((c for c in colors if c["role"] == "primary"), colors[0])
    secondaries = [c for c in colors if c["role"] != "primary"]
    
    color_lines = [f"- PRIMARY: {primary['name']} {primary['hex']} — dominant, use for backgrounds or key elements"]
    for c in secondaries[:3]:
        color_lines.append(f"- {c['role'].upper()}: {c['name']} {c['hex']}")
    
    prompt = f"""Create a professional marketing banner for {profile['brand_name']} ({profile['brand_name_english']}).

CAMPAIGN: {campaign_theme}
FORMAT: {format_name}

BRAND IDENTITY:
- Category: {profile['brand_category']}
- Slogan: {profile['brand_slogan']}
- Visual mood: {', '.join(profile['mood'][:4])}

COLOR REQUIREMENTS (STRICT — use these exact colors):
{chr(10).join(color_lines)}

LOGO REFERENCE: {profile['logo_description']}

COMPOSITION:
- Leave clear space in center-right for headline text overlay (added separately)
- Decorative elements may include: {', '.join(profile.get('pattern_elements', [])[:3])}
- {profile.get('imagery_direction', '')}
- Style: {'; '.join(profile.get('style_descriptors', [])[:3])}

DO NOT include any text, words, letters, or characters in the image. Text will be overlaid separately."""

    return prompt


# ── Step 4: Image Generation ──────────────────────────────────────

def generate_image(prompt: str, dimensions: str, output_path: str):
    print(f"  Generating {dimensions} image...")
    print(f"  Prompt: {len(prompt)} chars")
    
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=dimensions,
        quality="high",
    )
    
    image_b64 = result.data[0].b64_json
    if image_b64:
        image_bytes = base64.b64decode(image_b64)
    else:
        import urllib.request
        image_bytes = urllib.request.urlopen(result.data[0].url).read()
    
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"  ✅ Saved: {output_path} ({len(image_bytes) // 1024}KB)")
    return output_path


# ── Main Pipeline ─────────────────────────────────────────────────

def main():
    pdf_path = "/mnt/c/Users/Alecx/Downloads/太极堡VI-250303.pdf"
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    output_dir.mkdir(exist_ok=True)
    pages_dir = "/tmp/taijibao_pages"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ── Extract key pages ──
    print("📄 Step 1: Extracting key pages from PDF...")
    key_pages = [4, 5, 13, 22, 24, 25, 27, 28]
    image_paths = extract_pages(pdf_path, key_pages, pages_dir)
    
    # ── Analyze brand ──
    profile = analyze_brand(image_paths)
    
    profile_path = output_dir / "taijibao_brand_profile_gpt.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Brand profile extracted → {profile_path}")
    print(f"   Brand: {profile['brand_name']} ({profile.get('brand_name_english', '')})")
    print(f"   Colors:")
    for c in profile.get("palette", []):
        print(f"     {c['hex']} — {c['name']} ({c['role']})")
    print(f"   Slogan: {profile.get('brand_slogan', '?')}")
    print(f"   Confidence: {profile.get('confidence', '?')}")
    
    # ── Generate images ──
    campaign = "夏日特惠 — 新品麻辣牛肉堡上市 (Summer Special — New Spicy Beef Burger Launch)"
    
    # WeChat banner (landscape)
    print(f"\n🎨 Step 3: Generating WeChat Banner...")
    wechat_prompt = build_prompt(profile, campaign, "WeChat Banner (landscape, 900×500)")
    wechat_out = str(output_dir / f"taijibao_wechat_{timestamp}.png")
    generate_image(wechat_prompt, "1536x1024", wechat_out)
    
    # Square post
    print(f"\n🎨 Step 4: Generating Square Post...")
    square_prompt = build_prompt(profile, campaign, "Square Social Post (1080×1080)")
    square_out = str(output_dir / f"taijibao_square_{timestamp}.png")
    generate_image(square_prompt, "1024x1024", square_out)
    
    print(f"\n✅ Pipeline complete!")
    print(f"   Profile: {profile_path}")
    print(f"   WeChat:  {wechat_out}")
    print(f"   Square:  {square_out}")


if __name__ == "__main__":
    main()
