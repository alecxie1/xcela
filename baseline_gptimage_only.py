"""baseline_gptimage_only.py — RAW gpt-image-2 control (NO Xcela pipeline).

Purpose: isolate the pipeline's contribution. Reuse the EXACT same generation
wrapper the tool uses (harness/generate.py:generate_variant -> model=gpt-image-2,
images.edit, 1536x1024, quality=high), but feed it ONLY:
  - the uncropped brief image (briefaia.jpg) as the style reference
  - a plain-language task prompt a non-designer would type
No register, no kit, no compose_select, no reserve-box, no licensed-font
composite, no measure. Same two messages the tool rendered, for a head-to-head.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "harness"))
from generate import generate_variant  # noqa: E402

BRIEF = "/mnt/c/Users/Alecx/Downloads/briefaia.jpg"
OUT = Path("output/baseline_gptimage_only")

# A realistic, good-faith NON-DESIGNER prompt: states the task, the style (via the
# reference image + words), the exact text, the format. NOT our engineered prompt.
def naive_prompt(line1: str, line2: str) -> str:
    return (
        "Make a die-cut hand-held event sign (手举牌) in the SAME playful sticker "
        "style as the attached reference image, for an anti-fraud / anti-money-"
        "laundering public awareness campaign. "
        f"The sign must prominently show this Chinese text in two lines: "
        f"\u201c{line1}\u201d and \u201c{line2}\u201d. "
        "Use the same bright red, white and gold color scheme, the white outline "
        "border, the rounded die-cut sticker shape, and a friendly cartoon icon "
        "like the reference. One single sign, centered, on a plain background."
    )

SIGNS = [
    ("s1", "守住钱袋子", "护好幸福家"),
    ("s2", "远离非法金融", "抵制高息诱惑"),
]

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, l1, l2 in SIGNS:
        prompt = naive_prompt(l1, l2)
        out_path = str(OUT / f"baseline_{sid}.png")
        print(f"=== {sid}: {l1} / {l2} ===")
        print(f"PROMPT: {prompt}")
        meta = generate_variant(prompt, BRIEF, out_path)
        print(f"  -> {meta['output']}  ({meta['model']}, {meta['size']}, q={meta['quality']})\n")
    print("DONE: raw gpt-image-2 baseline, no pipeline.")
