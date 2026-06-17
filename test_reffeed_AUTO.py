"""Generate from the AUTO-generated aligned prompts (#20 output), feeding each
back to gpt-image-2 with its source crop. ONLY variable vs test_reffeed.py:
hand-written prompt -> analyzer-generated prompt. Tests whether the automated
bridge stands alone (no Hermes hand-writing the style clause).
"""
import base64, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.home() / ".hermes" / ".env", override=True)
from openai import OpenAI

client = OpenAI(timeout=240.0, max_retries=1)

jobs = {
    "crop1": ("/mnt/c/Users/Alecx/Downloads/cropped ref 1.png", "output/refstyle_crop1/aligned_prompt.txt"),
    "crop2": ("/mnt/c/Users/Alecx/Downloads/cropped ref 2.png", "output/refstyle_crop2/aligned_prompt.txt"),
}

for tag, (img_path, prompt_path) in jobs.items():
    prompt = Path(prompt_path).read_text(encoding="utf-8").strip()
    out_dir = Path(f"output/reffed_AUTO_{tag}")
    out_dir.mkdir(parents=True, exist_ok=True)
    t = time.time()
    print(f"[{tag}] feeding {Path(img_path).name} + AUTO prompt -> gpt-image-2 ...", flush=True)
    with open(img_path, "rb") as f:
        resp = client.images.edit(model="gpt-image-2", image=[f], prompt=prompt,
                                   size="1024x1024", quality="high")
    b64 = resp.data[0].b64_json
    if not b64:
        print(f"[{tag}] NO IMAGE DATA", flush=True)
        continue
    out_png = out_dir / "generated.png"
    out_png.write_bytes(base64.b64decode(b64))
    print(f"[{tag}] saved {out_png} ({out_png.stat().st_size:,} bytes) in {time.time()-t:.0f}s", flush=True)

print("DONE")
