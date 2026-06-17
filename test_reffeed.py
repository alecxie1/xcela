"""Ref-as-visual-channel test: FEED a cropped ref panel directly to gpt-image-2
and see if the output lands closer to the 定稿 than the parse-only version.

Isolates ONE variable: the fed reference image. No chroma (would confound bg),
no licensed-font composite (this is a STYLE-proximity test, not a font test).
"""
import base64, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.home() / ".hermes" / ".env", override=True)
from openai import OpenAI

client = OpenAI(timeout=240.0, max_retries=1)   # per-call timeout (no infinite hang)

# Aligned prompt: explicitly MATCH the ref (do not fight it), change ONLY the message.
PROMPT = (
    "Use the ATTACHED reference image as the EXACT visual-style template. Create ONE new "
    "hand-held event sign (手举牌) in the IDENTICAL design language: same bold rounded white "
    "Chinese typography with thin outline, same crimson-red (#C41E3A) + gold palette, same "
    "thick white die-cut sticker stroke around the whole shape, same playful flat-vector "
    "cartoon icon style WITH a hero icon protruding past the sign edge, same friendly "
    "grabbable photo-prop energy. NOT corporate, NOT a photograph, NOT 3D.\n\n"
    "CHANGE ONLY THE MESSAGE to two large centered lines: 守住钱袋子 (line 1) / 护好幸福家 "
    "(line 2). Render these characters big, bold, white, in the same rounded font as the "
    "reference.\n\n"
    "HERO ICON: a cartoon golden money bag (钱袋子) with a white ¥ symbol, protruding past the "
    "edge like the reference's protruding icon. Optional small house-with-heart accent for 幸福家.\n\n"
    "ONE single die-cut sign. NO logo, NO brand mark anywhere. Crisp, saturated, playful."
)

crops = {
    "crop1": "/mnt/c/Users/Alecx/Downloads/cropped ref 1.png",
    "crop2": "/mnt/c/Users/Alecx/Downloads/cropped ref 2.png",
}

for tag, path in crops.items():
    out_dir = Path(f"output/reffed_sign1_{tag}")
    out_dir.mkdir(parents=True, exist_ok=True)
    t = time.time()
    print(f"[{tag}] feeding {Path(path).name} -> gpt-image-2 ...", flush=True)
    with open(path, "rb") as f:
        resp = client.images.edit(
            model="gpt-image-2",
            image=[f],
            prompt=PROMPT,
            size="1024x1024",
            quality="high",
        )
    b64 = resp.data[0].b64_json
    if not b64:
        print(f"[{tag}] NO IMAGE DATA", flush=True)
        continue
    out_png = out_dir / "generated.png"
    out_png.write_bytes(base64.b64decode(b64))
    print(f"[{tag}] saved {out_png} ({out_png.stat().st_size:,} bytes) in {time.time()-t:.0f}s", flush=True)

print("DONE")
