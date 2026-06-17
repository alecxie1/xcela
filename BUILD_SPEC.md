# BUILD SPEC — Reference-Style Analyzer (#20)

**You are building ONE Python module for the Handyprint brand-design tool.**
Read this whole file, then read the four context files listed below BEFORE writing any code.
Do not git commit anything. Do not touch any file except the one new module and the one
self-test script named below.

---

## THE GOAL IN ONE SENTENCE

Auto-generate the "match this reference exactly" gpt-image-2 prompt clause **from a reference
image**, replacing the version a human currently hand-writes by eye. This is the single piece
that lets the tool feed reference images to gpt-image-2 WITHOUT a human in the loop.

## WHY (context you need to understand the gap)

A test just proved that FEEDING a cropped reference panel directly to gpt-image-2 (plus an
"aligned prompt" that describes the ref's style and tells the model to match it) produces
output dramatically closer to the client's final than describing the brand in text alone.

BUT: that aligned prompt was **hand-written by a human looking at the crop**. See the exact
hand-written gold prompt in `test_reffeed.py`, the `PROMPT` constant (lines ~16-29). Your job
is to make a function that PRODUCES an equivalent prompt automatically from the image.

The tool ALREADY reads a ref image's style — see `register/calibrate_from_reference.py`
(`STYLE_PROMPT`, `_vision_call`). What's missing is the step that turns that structured read
into the aligned generation prompt. You are building that missing step.

## CONTEXT FILES TO READ FIRST (in this order)

1. `test_reffeed.py` — the `PROMPT` constant is the GOLD aligned prompt you must learn to
   reproduce automatically. Study every style commitment it makes.
2. `register/calibrate_from_reference.py` — reuse its `_vision_call(image_path, prompt)` helper
   (import it) and its fence-stripping JSON pattern. Its `STYLE_PROMPT` is a NARROWER version of
   what you need; your extraction prompt must be a superset (see "what to capture" below).
3. `harness/assemble_prompt.py` — the project's templating philosophy: a pure function,
   deterministic, same input -> same output. Mirror that style (fixed skeleton, only values vary).
4. `SYSTEM_MAP.md` — the top banner + the pipeline diagram, for how this fits the whole tool.

---

## WHAT TO BUILD

### File: `register/reference_style_to_prompt.py`

A CLI module with two pure-ish functions and a `main()`:

#### 1. `extract_style_descriptor(image_path: str) -> dict`
- Reuse `_vision_call` from `calibrate_from_reference` (import it:
  `from register.calibrate_from_reference import _vision_call` — or mirror it if the import
  path is awkward; the repo root is on sys.path when run as `.venv/bin/python register/...`).
- Use an EXTENDED structured-JSON extraction prompt that captures EVERYTHING the gold prompt in
  `test_reffeed.py` commits to. The current `STYLE_PROMPT` misses several. Your descriptor JSON
  MUST include these keys:
  - `colors`: list of `{hex, role}` where role is one of `field/background`, `primary_accent`,
    `secondary_accent`, `text`. (The gold prompt knew crimson was the field and gold was the
    accent — role matters.)
  - `font_feel`: describe weight + roundness (e.g. "bold, heavy, rounded"), and `font_color`.
  - `text_treatment`: stroke/outline? (the gold prompt said "thin white outline"/"thick white
    die-cut stroke") — capture both the TYPE outline and the whole-shape die-cut stroke.
  - `container_shape`: the die-cut sticker shape + the thick white cut-line around the whole sign.
  - `icon_style`: e.g. "playful flat-vector cartoon".
  - `hero_icon_device`: BOOLEAN-ish — does a hero icon PROTRUDE past the sign edge? Describe it.
    (This protruding-icon device is one of the three things the human eye graded; it MUST be
    captured.)
  - `overall_energy`: short phrase (e.g. "friendly, grabbable photo-prop").
  - `negatives`: what the style is NOT (e.g. "not corporate, not a photograph, not 3D") — infer
    from what's absent.
- Strict JSON out, fence-strip like the sibling code does. Pin the vision model via the existing
  MODELS chain in `calibrate_from_reference` (proven on these images).

#### 2. `assemble_aligned_prompt(descriptor: dict, message_lines: list[str], hero_icon: str | None) -> str`
- PURE, DETERMINISTIC. Fixed skeleton, only the descriptor values + message get spliced in.
- The skeleton must mirror the gold prompt's SHAPE:
  - Opens: "Use the ATTACHED reference image as the EXACT visual-style template. Create ONE new
    hand-held event sign (手举牌) in the IDENTICAL design language: {style commitments}."
  - Style commitments: assembled from the descriptor (same font feel, same {field hex} +
    {accent hex} palette, same die-cut stroke, same icon style, same protruding hero-icon device
    if present, same energy). Include the negatives.
  - "CHANGE ONLY THE MESSAGE to {N} large centered lines: {message_lines}. Render big, bold,
    {font_color}, in the same {font_feel} font as the reference."
  - "HERO ICON: {hero_icon if provided, else derive a sensible default from the descriptor's
    hero_icon_device}."
  - Closes: "ONE single die-cut sign. NO logo, NO brand mark anywhere. Crisp, saturated."
- If `hero_icon` arg is None, fall back to a generic instruction derived from the descriptor.

#### 3. `main()` — CLI
```
.venv/bin/python register/reference_style_to_prompt.py \
    --image "/mnt/c/Users/Alecx/Downloads/cropped ref 1.png" \
    --message "守住钱袋子" --message "护好幸福家" \
    --hero-icon "a cartoon golden money bag (钱袋子) with a white ¥ symbol, protruding past the edge" \
    --out output/refstyle_crop1
```
- `--message` repeatable (one per line). `--hero-icon` optional. `--out` required (a dir).
- Writes `aligned_prompt.txt` (the final prompt string) and `style_descriptor.json` (the
  extracted descriptor) into `--out`. Print both paths + their byte sizes on success.

---

## SELF-TEST (you run this; it is CHEAP — vision calls + text only, NO image generation)

### File: `test_refstyle_selftest.py` (repo root)
- For BOTH crops (`/mnt/c/Users/Alecx/Downloads/cropped ref 1.png` and `cropped ref 2.png`):
  run the analyzer with the SAME task the gold prompt uses (message lines 守住钱袋子 /
  护好幸福家, hero icon = golden money bag with ¥).
- Then DIFF each auto-generated prompt against the hand-written gold `PROMPT` from
  `test_reffeed.py` at the level of STYLE COMMITMENTS. Print a checklist (✓/✗) for whether the
  auto-prompt captured each of these commitments that the gold prompt made:
  1. protruding hero icon device
  2. thick white die-cut sticker stroke around the whole shape
  3. crimson/red field color
  4. gold accent color
  5. bold + rounded font weight
  6. white headline type
  7. "NOT corporate / NOT photo / NOT 3D" negatives
  8. the correct message (守住钱袋子 / 护好幸福家)
- Print a final line: `CAPTURED X/8 style commitments` for each crop.

**Definition of done:** the module runs without error on both crops, writes both output files
per crop (report real byte sizes from disk via `os.path.getsize`), and the self-test reports
**≥ 6 / 8** style commitments captured for EACH crop. If it captures fewer, say so plainly and
report exactly which commitments were missed — do NOT pretend it passed.

---

## HARD RULES (these have broken past delegated builds — obey verbatim)

1. **Do NOT launch any background process. Do NOT poll or monitor anything in a loop.** Every
   step is ONE synchronous foreground blocking call. (Vision calls return in seconds; you do NOT
   generate any images in this build — that is done separately by the orchestrator afterward.)
2. **Do NOT call gpt-image-2 / images.edit / any image generation.** This build stops at
   producing the PROMPT TEXT + descriptor. Image generation and the visual comparison are the
   orchestrator's job, run directly. Your self-test is text-only.
3. Use `.venv/bin/python` (the repo venv at the project root). The API key loads from
   `~/.hermes/.env` exactly like the sibling scripts (`load_dotenv(Path.home()/".hermes"/".env")`).
4. **Do NOT git commit, git add, or git push.** Leave changes on disk only.
5. Touch ONLY `register/reference_style_to_prompt.py` and `test_refstyle_selftest.py`. Do not
   edit any existing file.
6. **Honest reporting.** If a vision call fails, JSON won't parse, or the checklist falls short,
   report it plainly with the real error. Print real file sizes read from disk, not assumed ones.
   Never fabricate output. A truthful "captured 5/8, missed die-cut stroke and negatives" is a
   GOOD result we can act on; a fabricated "8/8 " is worthless.

## FINISH YOUR REPORT WITH (exact evidence)

- The absolute path + byte size of `register/reference_style_to_prompt.py`.
- For each crop: the `CAPTURED X/8` line and the full ✓/✗ checklist.
- The full text of ONE auto-generated `aligned_prompt.txt` (crop 1) so the orchestrator can eyeball it.
- Any commitment the analyzer MISSED, named explicitly.
