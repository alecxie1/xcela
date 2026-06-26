"""ocr_readback.py — mechanical, NON-leading text check.
Ask the pixels what characters are actually painted; diff vs intended.
Same OCR engine on baseline (model-painted text) and tool (composited licensed font),
so any systematic difference is signal, not OCR noise.
"""
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()

INTENDED = {
    "守住钱袋子": ["护好幸福家"],
}
JOBS = [
    ("BASELINE s1", "output/baseline_gptimage_only/baseline_s1.png", ["守住钱袋子", "护好幸福家"]),
    ("BASELINE s2", "output/baseline_gptimage_only/baseline_s2.png", ["远离非法金融", "抵制高息诱惑"]),
    ("TOOL s1", "output/run_aia_20260623_110905/sign_s1/final.png", ["守住钱袋子", "护好幸福家"]),
    ("TOOL s2", "output/run_aia_20260623_110905/sign_s2/final.png", ["远离非法金融", "抵制高息诱惑"]),
]

def run(path):
    res, _ = ocr(path)
    if not res:
        return []
    # res: list of [box, text, score]
    return [(t.strip(), round(float(s), 2)) for _, t, s in res]

for label, path, intended in JOBS:
    print(f"\n===== {label} =====")
    print(f"  INTENDED: {' | '.join(intended)}")
    found = run(path)
    joined = "".join(t for t, _ in found)
    print(f"  OCR READ: {found}")
    # crude per-line presence
    for line in intended:
        hit = line in joined
        print(f"    '{line}' present verbatim? {hit}")
