"""ocr_alec_batch.py — mechanical, NON-leading readback of Alec's 6 raw gpt-image-2 signs.
No intended text passed to OCR. Just report what characters are painted + confidence,
and whether the actual licensed font file could even be involved (it cannot: raw model).
"""
import glob
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
files = sorted(glob.glob("/mnt/c/Users/Alecx/Downloads/ChatGPT Image Jun 23, 2026, 02_46_0*.png"))
for p in files:
    res, _ = ocr(p)
    name = p.split("/")[-1]
    print(f"\n===== {name} =====")
    if not res:
        print("  (no text detected)")
        continue
    for _, t, s in res:
        print(f"  {float(s):.2f}  {t.strip()!r}")
