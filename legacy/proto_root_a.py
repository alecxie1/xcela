"""Root-A prototype: generate the event_prop sign as ONE die-cut object on a
TRANSPARENT background, then prove the alpha channel IS the exact container mask
(killing the detection fragility that caused signs #2-#5's placement failures)."""
import base64, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path.home() / ".hermes" / ".env", override=True)
from openai import OpenAI
import numpy as np
from PIL import Image

c = OpenAI()

prompt = '''A single FLAT VECTOR die-cut hand-held event photo-prop sign (手举牌) for an AIA (友邦保险) anti-fraud awareness event.

CRITICAL FRAMING — READ FIRST: Render ONE single die-cut sign as ONE discrete object floating on a FULLY TRANSPARENT background. The sign is a speech-bubble / cloud shape that occupies about 78% of the frame, CENTERED, with clearly EMPTY TRANSPARENT margin around ALL of its edges. NOTHING may be drawn outside the sign's outline — no background color, no scattered elements beyond the sign, no second panel, no full-bleed fill. EVERYTHING (color fill, icons, text, decorations) lives strictly INSIDE the single die-cut shape. The region outside the die-cut shape MUST be fully transparent (alpha = 0).

REGISTER: playful event photo-prop — formality ~4/10, playfulness ~7/10. Bubbly, eye-catching, grabbable. NOT corporate, NOT a photograph, NOT 3D.

CONTAINER SHAPE: one rounded speech-bubble / cloud form with a thick 14px WHITE stroke outline (die-cut sticker pop) and a small triangular tail at lower-left. Soft pillowy curves.

FILL (inside the bubble only): solid 友邦红 AIA Red #D31145 with a subtle radial gradient (#E8466A center to #D31145 edge). Brand anchor color held.

RESERVED HEADLINE AREA: leave a COMPLETELY BLANK area in the upper-center of the bubble interior (roughly the middle 60% of width, upper-middle height) — no text, no icons, no marks. A headline is added later in post. Make this blank zone the obvious focal area.

ICONS (supporting cast, lower third of the bubble interior ONLY): a cartoon 钱袋子 money bag in #FFD23F with a white ¥ and two googly eyes (friendly mascot, ~140px tall), a small #4ECDC4 house with a heart, a small shield with a checkmark, a few #FFD23F sparkles and confetti dots. Never in the reserved headline zone.

FOOTER: a small rounded #333D47 banner near the bubble's bottom interior holding white 28px text "友邦保险 AIA · 防范非法金融，守护幸福生活".

HIERARCHY: the (future) headline dominates the upper-center; icons are secondary in the lower third; all of it inside ONE die-cut shape. NO logo, brand mark, or emblem anywhere.

Flat vector, crisp, saturated playful palette anchored by #D31145. Everything outside the single die-cut shape is fully transparent.'''

prompt = '''A single FLAT VECTOR die-cut hand-held event photo-prop sign (手举牌) for an AIA (友邦保险) anti-fraud awareness event.

CRITICAL FRAMING — READ FIRST: Render ONE single die-cut sign as ONE discrete object CENTERED on a perfectly flat, uniform CHROMA-KEY background of pure solid #00B140 (bright chroma green). The sign is a speech-bubble / cloud shape that occupies about 78% of the frame, CENTERED, surrounded on ALL edges by the flat #00B140 green emptiness. The green is a removable backdrop — like a green screen. NOTHING may be drawn on the green except the one sign: no scattered elements, no second panel, no shadows on the green, no other color touching the green. EVERYTHING (color fill, icons, text, decorations) lives strictly INSIDE the single die-cut shape. The entire area outside the die-cut shape MUST be pure uniform #00B140 green with nothing on it.

REGISTER: playful event photo-prop — formality ~4/10, playfulness ~7/10. Bubbly, eye-catching, grabbable. NOT corporate, NOT a photograph, NOT 3D.

CONTAINER SHAPE: one rounded speech-bubble / cloud form with a thick 14px WHITE stroke outline (die-cut sticker pop) and a small triangular tail at lower-left. Soft pillowy curves.

FILL (inside the bubble only): solid 友邦红 AIA Red #D31145 with a subtle radial gradient (#E8466A center to #D31145 edge). Brand anchor color held.

RESERVED HEADLINE AREA: leave a COMPLETELY BLANK area in the upper-center of the bubble interior (roughly the middle 60% of width, upper-middle height) — no text, no icons, no marks. A headline is added later in post. Make this blank zone the obvious focal area.

ICONS (supporting cast, lower third of the bubble interior ONLY): a cartoon 钱袋子 money bag in #FFD23F with a white ¥ and two googly eyes (friendly mascot, ~140px tall), a small #4ECDC4 house with a heart, a small shield with a checkmark, a few #FFD23F sparkles and confetti dots. Never in the reserved headline zone. None of these may use green — keep all icon colors away from #00B140 so they don't blend with the backdrop.

FOOTER: a small rounded #333D47 banner near the bubble's bottom interior holding white 28px text "友邦保险 AIA · 防范非法金融，守护幸福生活".

HIERARCHY: the (future) headline dominates the upper-center; icons are secondary in the lower third; all of it inside ONE die-cut shape. NO logo, brand mark, or emblem anywhere.

Flat vector, crisp, saturated playful palette anchored by #D31145. Everything outside the single die-cut shape is pure flat #00B140 chroma green.'''

print("generating (chroma-key bg, single object)...")
r = c.images.generate(model="gpt-image-2", prompt=prompt, size="1536x1024",
                      quality="high", output_format="png")
png = base64.b64decode(r.data[0].b64_json)
out = Path("output/protoA_sign1/generated.png"); out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(png)
print("saved", out, len(png), "bytes")

# ---- Chroma-key analysis: recover the sign mask by color distance from #00B140 ----
img = Image.open(out).convert("RGB")
arr = np.array(img).astype(int)
H, W, _ = arr.shape
key = np.array([0, 0xB1, 0x40])
dist = np.sqrt(((arr - key) ** 2).sum(axis=2))
mask = dist > 90          # sign = far from green; background = near green
transparent_frac = float((dist <= 90).mean())   # "green backdrop" fraction
# write an RGBA cutout (alpha from chroma key) so downstream gets a clean container
rgba = np.dstack([arr.astype(np.uint8), (mask * 255).astype(np.uint8)])
Image.fromarray(rgba, "RGBA").save("output/protoA_sign1/cutout.png")
if mask.any():
    ys, xs = np.nonzero(mask)
    bbox = [round(xs.min()/W, 3), round(ys.min()/H, 3), round(xs.max()/W, 3), round(ys.max()/H, 3)]
    coverage = float(mask.mean())
    bbox_area = max(1, (xs.max()-xs.min()) * (ys.max()-ys.min()))
    solidity = float(mask.sum()/bbox_area)
    cx, cy = round((xs.min()+xs.max())/2/W, 3), round((ys.min()+ys.max())/2/H, 3)
else:
    bbox = coverage = solidity = cx = cy = None

# connected-components: how many separate opaque blobs? (1 = single contained sign)
from scipy import ndimage
lbl, ncomp = ndimage.label(mask)
sizes = ndimage.sum(mask, lbl, range(1, ncomp+1)) if ncomp else []
big = int((np.array(sizes) > 0.01*H*W).sum()) if ncomp else 0

report = {
    "transparent_frac": round(transparent_frac, 3),
    "container_bbox_frac": bbox,
    "sign_coverage_of_canvas": round(coverage, 3) if coverage else None,
    "bbox_solidity": round(solidity, 3) if solidity else None,
    "container_center": [cx, cy],
    "opaque_components_total": int(ncomp),
    "opaque_components_large": big,
}
print(json.dumps(report, indent=2))
Path("output/protoA_sign1/alpha_report.json").write_text(json.dumps(report, indent=2))

# Verdict on Root-A hypothesis
ok = (transparent_frac > 0.12 and big == 1 and bbox and 0.02 < bbox[0] and bbox[2] < 0.98
      and coverage and 0.4 < coverage < 0.85)
print("\nROOT-A CASCADE-COLLAPSE:", "PASS — alpha is a clean single-object container mask" if ok
      else "PARTIAL/FAIL — inspect report (transparency or single-object containment not clean)")
