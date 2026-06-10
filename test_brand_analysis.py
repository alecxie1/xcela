"""
太极堡 Brand Analysis Test — Claude Vision
Analyzes brand PDF pages and produces a structured JSON brand profile.
No OpenAI needed — uses Anthropic Claude Vision only.
"""

import base64, json, os, sys
from pathlib import Path

import anthropic

SYSTEM_PROMPT = """You are a senior brand strategist. Analyze the brand asset image(s) provided.
Return ONLY a JSON object with this exact schema — no markdown, no explanation, no fences:

{
  "brand_name": "...",
  "brand_name_english": "...",
  "palette": [{"hex":"#RRGGBB","name":"...","role":"primary|secondary|accent|neutral|background"}],
  "typography": {"chinese_font":"...","english_font":"...","feel":"...","weight_tendency":"..."},
  "mood": ["3-6 adjectives"],
  "style_descriptors": ["3-6 phrases"],
  "imagery_direction": "1-2 sentences",
  "logo_description": "precise visual description of the logo mark",
  "pattern_elements": ["list of decorative motifs/patterns"],
  "brand_category": "...",
  "brand_slogan": "...",
  "dos": ["3-4 concrete design rules"],
  "donts": ["3-4 concrete design rules"],
  "headline_treatments": [{"text":"on-brand sample headline","rationale":"why it works"}],
  "confidence": "high|medium|low"
}

Rules:
- palette: 3-6 colors, hex MUST be observed values from the image
- Be design-actionable; ban generic filler like "professional" or "modern"
- If the brand is Chinese, infer market and give Chinese sample headlines
- logo_description must be precise enough to guide an AI image generator
- pattern_elements: describe each pattern motif individually"""


def analyze_brand_pages(image_paths: list[str]) -> dict:
    """Analyze multiple brand guideline pages with Claude Vision."""
    client = anthropic.Anthropic()
    
    content = []
    for path in image_paths:
        with open(path, "rb") as f:
            raw = f.read()
        b64 = base64.standard_b64encode(raw).decode()
        ext = Path(path).suffix.lower()
        media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": b64}
        })
    
    content.append({
        "type": "text",
        "text": "Analyze these brand guideline pages. They are from the same brand's VI (Visual Identity) manual. Extract the complete brand profile as JSON."
    })
    
    print(f"  Sending {len(image_paths)} pages to Claude Vision...")
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    
    text = msg.content[0].text.strip()
    # Strip accidental fences
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    
    return json.loads(text)


def main():
    pages_dir = Path("/tmp/taijibao_pages")
    output_dir = Path("/home/alecx/workspace/handyprint-design-tool/output")
    output_dir.mkdir(exist_ok=True)
    
    # Select the most informative pages for brand analysis
    # Page 4: Overview (logo + wordmark combinations)
    # Page 5: Logo graphic detail
    # Page 7: Logo combinations
    # Page 13: Logo colors (standard + reversed)
    # Page 15: Background usage rules
    # Page 22: Typography
    # Page 24: Primary brand color (with exact values)
    # Page 25: Secondary brand colors (with exact values)
    # Page 27: Brand patterns
    # Page 28: Four-square continuous pattern
    key_pages = [4, 5, 13, 22, 24, 25, 27, 28]
    
    image_paths = [str(pages_dir / f"page_{p:02d}.png") for p in key_pages]
    
    # Verify all pages exist
    for p in image_paths:
        if not os.path.exists(p):
            print(f"  ❌ Missing: {p}")
            sys.exit(1)
    
    print(f"\n🔍 Analyzing 太极堡 brand with Claude Vision...")
    print(f"   Pages: {key_pages}")
    
    profile = analyze_brand_pages(image_paths)
    
    # Save the profile
    profile_path = output_dir / "taijibao_brand_profile.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Brand profile extracted!")
    print(f"   Saved: {profile_path}")
    print(f"\n📋 Profile summary:")
    print(f"   Brand: {profile.get('brand_name', '?')} ({profile.get('brand_name_english', '?')})")
    print(f"   Colors: {len(profile.get('palette', []))} extracted")
    for c in profile.get("palette", []):
        print(f"     {c['hex']} — {c['name']} ({c['role']})")
    print(f"   Typography: {profile.get('typography', {}).get('chinese_font', '?')} / {profile.get('typography', {}).get('english_font', '?')}")
    print(f"   Mood: {', '.join(profile.get('mood', []))}")
    print(f"   Logo: {profile.get('logo_description', '?')[:100]}...")
    print(f"   Patterns: {len(profile.get('pattern_elements', []))} motifs")
    print(f"   Slogan: {profile.get('brand_slogan', '?')}")
    print(f"   Confidence: {profile.get('confidence', '?')}")
    
    # Pretty-print full JSON
    print(f"\n📄 Full JSON profile:")
    print(json.dumps(profile, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
