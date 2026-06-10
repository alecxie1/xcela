"""
太极堡 Brand Generation Test — v0.1
Tests the core pipeline: brand spec → structured prompt → GPT Image 2 generation

Brand: 太极堡 (Taichi Burger)
Source: 太极堡VI-250303.pdf (32-page brand guidelines)
"""

import os
import sys
import base64
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load hermes .env with override so it wins over shell env
load_dotenv(Path.home() / ".hermes" / ".env", override=True)

# ── Brand Spec (extracted from VI manual) ──────────────────────────

BRAND_SPEC = {
    "name": {
        "chinese": "太极堡",
        "english": "TAICHI BURGER",
    },
    "colors": {
        "primary": {
            "name": "银朱红 Vermilion",
            "hex": "#D72321",
            "rgb": (215, 33, 33),
            "cmyk": (0, 97, 100, 3),
            "pantone": "2035C",
        },
        "secondary": [
            {
                "name": "大地金 Earth Gold",
                "hex": "#D7A569",
                "rgb": (219, 165, 105),
                "cmyk": (5, 31, 63, 5),
                "pantone": "7509C",
            },
            {
                "name": "墨湖黑 Ink Black",
                "hex": "#000000",
                "rgb": (0, 0, 0),
                "cmyk": (60, 40, 40, 100),
                "pantone": "Rich Black",
            },
            {
                "name": "珍珠白 Pearl White",
                "hex": "#EEE4D8",
                "rgb": (238, 228, 216),
                "cmyk": (0, 3, 7, 7),
                "pantone": "11-0605",
            },
        ],
    },
    "typography": {
        "chinese": "锦华明朝体",
        "english": "Helvetica (Thin / Light / Regular)",
    },
    "logo": {
        "description": "Red circular mark containing a stylized animal silhouette (fox/wolf profile) with flowing tai-chi-inspired curves. Creates yin-yang balance of red form and white negative space.",
        "usage": "Can be used standalone or with wordmark. Horizontal bilingual combination preferred.",
    },
    "patterns": {
        "description": "Five spice motifs as geometric icons: 八角 (star anise), 花椒 (Sichuan peppercorn), 桂皮 (cinnamon), 胡椒 (black pepper), 香叶 (bay leaf). Black silhouettes with white negative space, symmetrical, rotated 45°. Used as repeating four-square continuous pattern.",
    },
    "brand_voice": {
        "values": "Employee-first culture — respect, growth, dignity. The brand believes serving employees well leads to serving customers well.",
        "category": "东方汉堡 (Eastern Burger) — Chinese-style gourmet burgers",
        "slogan": "手作多汁，东方汉堡 (Handmade & Juicy, Eastern Burger)",
    },
}


# ── Prompt Assembly ────────────────────────────────────────────────

def build_prompt(campaign_theme: str, format_name: str, dimensions: tuple[int, int]) -> str:
    """Build a structured prompt from brand spec + campaign theme."""
    
    c = BRAND_SPEC["colors"]
    primary = c["primary"]
    secondary = c["secondary"]
    
    prompt = f"""Create a professional marketing banner for {BRAND_SPEC['name']['chinese']} ({BRAND_SPEC['name']['english']}).

CAMPAIGN THEME: {campaign_theme}
FORMAT: {format_name} ({dimensions[0]}×{dimensions[1]}px)

BRAND IDENTITY:
- Category: {BRAND_SPEC['brand_voice']['category']}
- Slogan: {BRAND_SPEC['brand_voice']['slogan']}
- Visual style: Modern Chinese restaurant branding. Clean, bold, premium fast-casual.

COLOR REQUIREMENTS (STRICT):
- Primary: Vermilion red {primary['hex']} — dominant color, used for backgrounds or key elements
- Secondary accent: Earth Gold {secondary[0]['hex']} — for highlights, borders, or accent text
- Dark: Ink Black {secondary[1]['hex']} — for text or contrast areas
- Light: Pearl White {secondary[2]['hex']} — for backgrounds or breathing space

COMPOSITION:
- Leave clear space in the center-right area for headline text overlay (will be added separately)
- The brand's spice pattern motifs (star anise, Sichuan peppercorn, cinnamon, pepper, bay leaf) can appear as subtle decorative elements
- Food imagery should feel handmade, juicy, premium — not fast food
- Style should feel distinctly Chinese/Eastern, not Western burger chain
- Clean negative space, not cluttered

DO NOT include any text, words, letters, or characters in the image. The image should be purely visual — text will be overlaid separately."""

    return prompt


# ── Image Generation ───────────────────────────────────────────────

def generate_image(prompt: str, dimensions: tuple[int, int], output_path: str, logo_path: str = None):
    """Call GPT Image 2 (gpt-image-1 endpoint) to generate a brand image."""
    
    from openai import OpenAI
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Map dimensions to closest supported size
    # gpt-image-1 supports: 1024x1024, 1536x1024, 1024x1536
    w, h = dimensions
    if w > h:
        size = "1536x1024"  # landscape
    elif h > w:
        size = "1024x1536"  # portrait
    else:
        size = "1024x1024"  # square
    
    print(f"  Generating {size} image...")
    print(f"  Prompt length: {len(prompt)} chars")
    
    # Try with reference image if logo available
    if logo_path and os.path.exists(logo_path):
        print(f"  Using reference image: {logo_path}")
        with open(logo_path, "rb") as f:
            logo_data = f.read()
        
        result = client.images.edit(
            model="gpt-image-1",
            image=logo_data,
            prompt=prompt,
            size=size,
            quality="high",
        )
    else:
        print("  No reference image — generating from prompt only")
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality="high",
        )
    
    # Save the result
    image_b64 = result.data[0].b64_json
    if image_b64:
        image_bytes = base64.b64decode(image_b64)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"  ✅ Saved: {output_path} ({len(image_bytes) // 1024}KB)")
    else:
        # Fallback to URL if b64 not available
        url = result.data[0].url
        print(f"  Image URL: {url}")
        import urllib.request
        urllib.request.urlretrieve(url, output_path)
        print(f"  ✅ Downloaded: {output_path}")
    
    return output_path


# ── Extract logo from PDF page 5 as reference image ───────────────

def extract_logo_from_pdf(pdf_path: str, output_path: str):
    """Extract page 5 (logo page) as a high-res image for reference."""
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[4]  # page 5 (0-indexed)
    pix = page.get_pixmap(dpi=300)
    pix.save(output_path)
    doc.close()
    print(f"  Extracted logo page: {output_path} ({pix.width}x{pix.height})")
    return output_path


# ── Main ───────────────────────────────────────────────────────────

def main():
    pdf_path = "/mnt/c/Users/Alecx/Downloads/太极堡VI-250303.pdf"
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Step 1: Extract logo reference
    print("\n🔧 Step 1: Extracting logo reference from PDF...")
    logo_path = str(output_dir / "taijibao_logo_ref.png")
    extract_logo_from_pdf(pdf_path, logo_path)
    
    # Step 2: Define test campaign
    campaign_theme = "夏日特惠 — 新品麻辣牛肉堡上市 (Summer Special — New Spicy Beef Burger Launch)"
    
    # Step 3: Generate for WeChat banner format
    print("\n🎨 Step 3: Generating WeChat Banner (landscape)...")
    wechat_prompt = build_prompt(campaign_theme, "WeChat Banner", (900, 500))
    print(f"\n📝 Prompt preview:\n{wechat_prompt[:300]}...")
    
    wechat_output = str(output_dir / f"taijibao_wechat_{timestamp}.png")
    generate_image(wechat_prompt, (900, 500), wechat_output)
    
    # Step 4: Generate square post format  
    print("\n🎨 Step 4: Generating Square Post...")
    square_prompt = build_prompt(campaign_theme, "Square Social Post", (1080, 1080))
    square_output = str(output_dir / f"taijibao_square_{timestamp}.png")
    generate_image(square_prompt, (1080, 1080), square_output)
    
    print("\n✅ Done! Generated 2 brand images.")
    print(f"   Output dir: {output_dir}")
    

if __name__ == "__main__":
    main()
