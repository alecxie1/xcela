# Research: Layered Export (016)

All unknowns resolved; no NEEDS CLARIFICATION remain. Facts verified against the live codebase
and current API documentation on 2026-07-08.

## D1. Can gpt-image-2 emit layers natively? NO (the feature-shaping fact)

- **Decision**: build layers via per-element chroma repaint + local deterministic keying.
- **Rationale**: the gpt-image-2 API outputs only flat `png`/`jpeg`/`webp` via `output_format`;
  it has NO layered output, and the `background: transparent` option that existed in
  gpt-image-1.5 was REMOVED (only auto/opaque remain). "Native autolayer" claims refer to the
  ChatGPT web app's Photoshop integration, which is not API-accessible. Verified via current
  OpenAI docs and multiple 2026 third-party analyses (apiyi PSD guide, Epsilla layered-PSD
  pipeline writeup, vdoo transparency guide).
- **Alternatives considered**:
  - Local segmentation (SAM/rembg + psd-tools): rejected. Heavy new deps (torch), and it slices
    the FLAT image, so occluded content does not exist: a moved layer leaves a hole. Cutouts,
    not layers.
  - PSD assembly (psd-tools): deferred. A zip of PNG/JPG per Richard's ask; PSD is packaging
    sugar a v2 could add without touching the extraction.
  - Waiting for native support: not on any announced roadmap.

## D2. Isolation route: chroma repaint on #00B140

- **Decision**: one `images.edit` call per element: the approved image is the FIRST reference,
  the prompt demands exactly that one element reproduced at its original position/size/colors on
  a flat pure `#00B140` field, canvas size = the run's `generation.size`. Logo/product elements
  pass the original asset as a SECOND reference (deterministic disambiguation, no VLM guessing).
- **Rationale**: reuses the tool's proven chroma vocabulary (the die-cut path already prompts
  for and keys #00B140); keying is model-free and measurable, so every layer is honestly
  gradeable and nullable. Same-canvas-size keeps position comparable.
- **Prompt skeletons** (assembled by pure functions, tested for value-bearing clauses):

  Isolation:
  > CRITICAL FRAMING, READ FIRST: The FIRST supplied image is a finished design. Repaint
  > EXACTLY ONE element from it: {desc}. Reproduce that element EXACTLY as it appears in the
  > finished design: identical position on the canvas, identical size, identical colors,
  > styling and details. Everything else on the canvas must be a perfectly flat, uniform
  > backdrop of pure solid #00B140 (bright chroma green), like a green screen. NOTHING may be
  > drawn on the green: no shadows, no glow, no reflections, no other elements, no scene. The
  > element itself must not contain any color close to #00B140. Keep the exact canvas size.

  {desc} per kind: text → `the text "{verbatim line}" with its exact typography`; logo → `the
  brand logo (the SECOND supplied image is the original logo asset)`; product → `the product
  shown in the SECOND supplied image, as it appears in the finished design`.

  Background:
  > The supplied image is a finished design. Repaint it with these foreground elements REMOVED:
  > {list of descs}. Continue the background scene naturally behind where they were, matching
  > the surrounding textures, colors and lighting. Change NOTHING else: identical canvas size,
  > identical remaining composition. Add no new elements and no text.

## D3. Keying reuse: `strip_chroma` as-is

- **Decision**: call `harness/closed_loop_composite.py:strip_chroma(final_png, out_dir,
  key_hex)` (:428) unchanged, one out_dir per layer.
- **Rationale**: proven on the die-cut path; already returns the exact honesty stats needed
  (`opaque_frac`, `stray_component_px_dropped`, `despilled_px`,
  `green_residual_px_in_preview`) plus `cutout.png` (RGBA) and `preview_white.png`.
- **Known limitation accepted**: largest-component keep can drop detached glyph clusters on a
  text layer; `stray_component_px_dropped` exposes it in the manifest. Changing the keying would
  risk the die-cut path's byte-identity, so v1 does not.

## D4. Honest-null thresholds (deterministic, falsifiable)

- `opaque_frac > 0.95` → null "model ignored the chroma directive (full-frame content)".
- `opaque_frac < 0.001` → null "empty frame".
- `green_residual_px_in_preview > 2000` → null "dirty key field (green residue)".
- `stray_component_px_dropped > kept px` → null "largest-component keep dropped the MAJORITY
  of the content" (post-review hardening: a multi-glyph text line keyed down to one glyph must
  not ship as an unqualified ok cutout; the keying itself stays unchanged, only the judgment
  gained a fourth threshold).
- Null layers ship `<id>_raw.png` (the un-keyed model output, manual salvage) + manifest note;
  never a cutout. Values chosen against synthetic fixtures; a wrong implementation (always-ok or
  always-null) fails the fixture checks.

## D5. Element enumeration source of truth

- **Decision**: `inputs.json signs[0].messages` (one text element per verbatim line),
  `answer_keys/<brand>.json logo_path` gated on membership in
  `run_manifest generation.reference_image` (the run's actual fed list, verified shape:
  `[reference.png, <logo>, product_1.jpg]` on run_CJXQ_20260708_151506), and
  `inputs.json product_images` in order.
- **Rationale**: constitution IV + the project's no-VLM-guessing rule; these artifacts exist in
  every thin-route run dir and are already the manifest ground truth.
- **Granularity**: one layer per message line (the finisher's editable unit); recorded as
  revisable if the eye-gate shows per-line drift too costly.

## D6. Spend guard: the 015 contract applied to export

- **Decision**: mirror `decide_confirm` (frontend/server.py:88): free plan endpoint BEFORE the
  click; `export_state.json` written before the first paid call; exporting/done no-op; retry
  accepted ONLY from failed; 409 unless `gate_state.state == "done"`; disk-backed rendering.
  Deliberate divergence from confirm: failed → retry allowed (an export crash must not brick the
  run's only export; confirm has re-derive, export has nothing else).
- **Cost source**: server passes its `PER_RUN_COST_USD` (:36) into the module's `per_image_usd`
  parameter; harness never imports frontend.

## D7. Test strategy (free)

- Injectable `generate_fn` on the orchestrator (cleaner than 015's sys.modules stub); the stub
  records (prompt, refs, out_path, size) and writes synthetic chroma PNGs so the REAL
  `strip_chroma` executes in-tests.
- Synthetic fixtures: PIL images at 1536x1024, a red rectangle on flat #00B140 (ok layer), a
  full-noise frame (null: ignored), a pure-green frame (null: empty).
- Byte-identity: tree-hash an unexported run dir before/after module import + run_view render;
  full prior-suite sweep unchanged.
