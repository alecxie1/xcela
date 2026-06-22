---
paths:
  - "harness/closed_loop_composite.py"
  - "harness/measure_canvas.py"
  - "harness/composite_text.py"
---

# Placement layer rules (closed_loop_composite / measure_canvas / composite_text)

You are editing the PLACEMENT layer — the most failure-prone part of the tool and the
site of the current known failure. Read `docs/ARCHITECTURE.md` §9 and §11 before changing
logic here.

## Hard rules
- **Do NOT call `reanchor()` from the render-and-scrub path.** `reanchor()` centers
  PLANNED-size text on detected FREE SPACE — that is the reserve-box paradigm and the
  OPPOSITE of render-and-scrub's job (place the licensed font at gpt's MEASURED geometry).
  `place_measured` must never import or call it.
- **`place_measured` builds its spec from MEASURED geometry + the `--must-include` lines +
  the register/answer-key font.** It must NEVER read tier-3 / `write_composite_spec`.
- **Honest-null on capture failure is PATH-SPECIFIC:** no-ref job → free-space
  `closed_loop` fallback (reanchor is defined; the container has free space). Ref job →
  LEAVE gpt's text in place, set `needs_review=true`, never guess geometry, never
  free-space-fallback. Preserve this branch exactly.
- **Font compliance is non-negotiable.** A layer resolving to `fallback_system` must WARN
  loudly; `MISSING` must hard-fail. Never silently substitute a font. Never weaken the
  compliance manifest.
- **Honest nulls everywhere:** if a detection step fails, emit null + a note and record it
  in the run manifest. Never invent geometry.

## Known failure you are likely here to address (6/18, see SYSTEM_MAP)
- (a) `place_measured` reproduces gpt's text size with NO fit-to-margin clamp, so oversized
  painted text overflows the sign. Any fix must GENERALIZE (a real fit-within-container
  constraint), not hand-tune one image.
- (b) `patch_ghosts` scrub damages graphics it overlaps; on a ref job `interior_mask` is
  None so the scrub is less protected.
- ROOT CAUSE is the FRAME (one-template-N-texts), not these functions. Before a deep fix,
  confirm with the user that we're patching the current path vs building the kit-of-parts
  reframe. Do not silently start a large rewrite here.

## Test before you spend
- After any change, run `.venv/bin/python test_render_and_scrub.py` (free, no paid calls).
- `harness/scene_author.py ... --explain` exits before any model call — use it to verify
  mode/source/chroma routing without spending.
- A green self-test only proves STRUCTURE. Pixel quality (scrub cleanliness, placement
  match, fit) is validated ONLY by the human eye on a real `output/run_*/sign_*/final.png`.
- Chroma path in `measure_canvas` is the proven one; the legacy HSV path is fragile — do
  not route new work through HSV.
