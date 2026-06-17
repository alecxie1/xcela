# BUILD SPEC — `psd_to_cutout` tool primitive

**You are building ONE Python module + ONE self-test for the Handyprint brand-design tool.**
Read this whole file, then read the context files listed below BEFORE writing code.
Do not git commit. Touch ONLY the two files named in "What to build".

---

## THE GOAL IN ONE SENTENCE

Turn a client-supplied IP-character source (a `.psd`, a `.pdf`, or a flat image) where the
character sits on a solid/white background into a CLEAN TRANSPARENT-BACKGROUND cutout PNG —
reliably, as a reusable tool primitive, not a one-off script.

## WHY (context)

The current design task gave us the mascot 友小规 as a 62MB PSD on a white background. Clients
routinely hand over IP this way, so "source-on-white → clean cutout" is a RECURRING capability
the tool needs, not a one-off. A throwaway script already proved the method works on this exact
file; your job is to make it a proper, parameterized, self-verifying module.

**THE CORE INSIGHT (do not lose this):** you must NOT "remove all white pixels" — the character
HAS white parts (white shirt, white socks, eye-whites, the white "AIA" text on his hat). Naive
white-removal punches holes in him. The correct method is **edge-connected background removal**:
only remove white that is CONNECTED TO THE IMAGE BORDER. The character's solid black outline
contains the interior, so interior white is preserved. On the 友小规 fixture there are ~137
interior white components that MUST survive and exactly 1 white component touching the border
(the background).

## CONTEXT FILES TO READ FIRST

1. `SYSTEM_MAP.md` — top banner + pipeline diagram (how assets/brand library fit).
2. `extract_colors.py` and `extract_text_layer.py` — the repo's house style for a small,
   argparse-driven, single-purpose extraction module loading env via
   `load_dotenv(Path.home()/".hermes"/".env")` (this module needs NO API key, but match the
   structure, docstring style, and `.venv/bin/python module.py --args` CLI shape).
3. There is NO existing cutout code to extend — this is a new primitive. Place it at repo root
   next to the other `extract_*.py` modules.

## ENVIRONMENT (already verified — do not reinstall)

- Use `.venv/bin/python` (uv-managed venv; there is NO `.venv/bin/pip` — do NOT try to pip
  install. If a package were missing you'd use `uv pip install --python .venv/bin/python <pkg>`,
  but everything you need is ALREADY present).
- Installed and confirmed: `numpy`, `scipy` (use `scipy.ndimage.label`), `Pillow` (PIL),
  `psd-tools` (v1.17.2, `from psd_tools import PSDImage`), `PyMuPDF` (`import fitz`).
- Fixtures on disk (read-only inputs — do NOT modify, do NOT copy into the repo):
  - PSD:  `/mnt/c/Users/Alecx/Downloads/友小规.psd`  (CMYK, canvas 4724x7364, 1 real vector layer)
  - PDF:  `/mnt/c/Users/Alecx/Downloads/友小规.pdf`  (flattened; largest embedded image 4724x7364 png)
- A known-good hand-run cutout already exists at `brands/aia/assets/youxiaogui_cutout.png`
  (3884x6429 RGBA). Your module's output should be equivalent in quality. You MAY load it for
  comparison in the self-test, but the PRIMARY tests are intrinsic (below), not a diff against it.

---

## WHAT TO BUILD

### File 1: `psd_to_cutout.py` (repo root)

A CLI module. Core function + helpers + `main()`.

#### `load_source_as_rgb(path: str) -> PIL.Image (RGB)`
Accept three input kinds by extension:
- `.psd` → `PSDImage.open(path).composite()` → convert to RGB. (CMYK-safe: composite()
  returns a PIL image already; ensure final mode is RGB.)
- `.pdf` → open with `fitz`, take page 0, extract the LARGEST embedded image via
  `page.get_images(full=True)` + `doc.extract_image(xref)`; if no embedded image, fall back to
  `page.get_pixmap(dpi=300)`. Convert to RGB.
- `.png/.jpg/.jpeg/.webp` → open directly, convert to RGB.
Raise a clear error on anything else.

#### `cutout_on_white(img_rgb, white_threshold: int = 240, content_pad: int = 30) -> PIL.Image (RGBA)`
1. Content-crop: trim near-white margins (a pixel is "near-white" if ALL channels >= white_threshold).
   Keep `content_pad` px of margin. If the image is entirely near-white, raise a clear error.
2. Build `is_white` mask (all channels >= white_threshold).
3. **Edge-connected background detection** using `scipy.ndimage.label`:
   - label connected components of `is_white`;
   - the background = the union of all white components that touch ANY image border row/col;
   - everything else (including the ~137 interior white components) stays opaque.
4. Return RGBA: alpha = 0 on background, 255 elsewhere. (Keep it crisp/binary — do NOT
   feather; downstream compositing handles placement.)
5. **Sanity guard (loud, not silent):** compute removed-fraction. If < 5% removed, raise/return
   a clear WARNING that the background may not be white (nothing was removed). If > 95% removed,
   warn that the subject may have been eaten. These guard against silently emitting garbage.

#### `main()` — CLI
```
.venv/bin/python psd_to_cutout.py \
    --input "/mnt/c/Users/Alecx/Downloads/友小规.psd" \
    --output brands/aia/assets/youxiaogui_cutout_auto.png \
    [--white-threshold 240] [--content-pad 30]
```
On success print: input path, detected source kind, pre-crop size, post-crop size, removed
fraction, interior-white-component count, and the output path + byte size (read from disk with
`os.path.getsize`). Also write a sibling `<output>.report.json` with those same numbers.

### File 2: `test_psd_to_cutout.py` (repo root)

A DETERMINISTIC, pixel-level self-test on the 友小规 PSD fixture. NO API calls, NO image
generation, NO network. Import the functions from `psd_to_cutout`. Run the cutout, then assert
these FALSIFIABLE properties and print a ✓/✗ table + a final `PASSED`/`FAILED` line:

1. **Output is RGBA with a real alpha channel** whose values include BOTH 0 and 255
   (`alpha.getextrema() == (0, 255)`).
2. **Background removed at the corners:** all four corner pixels have alpha == 0.
3. **Interior preserved (THE key test — catches naive remove-all-white regression):** using
   `scipy.ndimage.label` on the white mask of the SOURCE, there must be MANY interior white
   components (assert >= 50; the fixture has ~137) that do NOT touch the border, and EVERY pixel
   belonging to those interior components must be OPAQUE (alpha == 255) in the output. If the
   implementation regressed to naive white-removal, these would be transparent and this MUST fail.
4. **No border-disconnected transparent holes:** every transparent pixel in the output must
   belong to a transparent component that touches the image border (i.e. label the transparent
   mask; assert no transparent component is fully interior). This is the structural guarantee of
   edge-connected fill.
5. **Sane opaque fraction:** opaque pixels are between 20% and 90% of the cropped canvas
   (catches "ate everything" / "removed nothing").

Print the real numbers behind each assertion (component counts, fractions, extrema), not just
pass/fail.

---

## HARD RULES (these broke past delegated builds — obey verbatim)

1. **Do NOT launch background processes. Do NOT poll/monitor in a loop.** Every step is ONE
   synchronous foreground call. (This build does no slow work — no image gen, no API. The PSD
   composite + flood fill run in seconds.)
2. **Do NOT generate images, call any LLM/vision API, or hit the network.**
3. Use `.venv/bin/python`. Do NOT pip install (everything is present).
4. **Do NOT git commit / add / push.** Leave changes on disk.
5. Touch ONLY `psd_to_cutout.py` and `test_psd_to_cutout.py`. Do NOT modify the fixtures, the
   existing `youxiaogui_cutout.png`, or any other file.
6. Write the module's CLI output to `brands/aia/assets/youxiaogui_cutout_auto.png` (a NEW file,
   so the hand-run `youxiaogui_cutout.png` stays intact for comparison).
7. **Honest reporting.** If a test fails, say so plainly with the real numbers — a truthful
   "interior-preservation FAILED, 137 components went transparent" is valuable; a fabricated PASS
   is worthless. Print real file sizes and array stats from actual computation, never assumed.
8. Make the module GENERIC (works for any source-on-white), not hardcoded to 友小规. The fixture
   is only the test subject.

## FINISH YOUR REPORT WITH (exact evidence)

- Absolute path + byte size of `psd_to_cutout.py`.
- The full ✓/✗ self-test table WITH the real numbers (interior component count, corner alpha
  values, opaque fraction, alpha extrema) and the final PASSED/FAILED line.
- The output cutout's path, dimensions, and byte size, and the contents of its `.report.json`.
- State plainly whether the interior-preservation test (test 3) passed — that is the one that
  proves the cutout isn't punching holes in the character.
