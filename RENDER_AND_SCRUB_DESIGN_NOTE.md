# RENDER-AND-SCRUB + DIAL-DRIVEN PROMPT — design note (evaluate before build)

Written after reading the real code (scene_author, closed_loop_composite, measure_canvas,
composite_text, coverredraw_signs2to5, reference_style_to_prompt, conductor, generate).
This is the "evaluate first" deliverable. It states the reuse map, the ONE place the task
prompt's framing disagrees with the code, the two-axis divergence, and the exact build.
No paid calls were made. No code changed yet.

---

## 0. VERDICT

The change is sound and most of it is reuse. There is ONE disagreement to absorb before
building (section 1). Axis B (dial wording) is small and low risk. Axis A (render-and-scrub)
is a genuinely NEW placement primitive, but its pieces already exist in the repo and one
script (coverredraw) already implements the exact capture-and-place pattern by hand.

---

## 1. THE ONE DISAGREEMENT (code vs the task prompt's framing)

The task prompt says, of Axis A: "reuse closed_loop_composite ... it already MEASURES the
painted canvas, detects gpt's text boxes, masks them out ... then re-anchors." The first half
is true; the "then re-anchors" half is the wrong primitive for what Axis A needs, and a builder
who reuses `reanchor()` verbatim would get the OPPOSITE of placement-match.

What `closed_loop_composite.reanchor()` actually does (lines 255-329, read it):
- it stacks the headline lines centered on the DETECTED FREE-SPACE optical center,
- at the PLAN's `size_px` (shrunk only to fit), in the PLAN's `color`.
That is the reserve-a-box paradigm: find the empty zone, drop planned-size planned-color text
into it. It deliberately ignores where/how big/what color gpt actually rendered the headline.

Axis A wants the inverse: place the licensed glyphs at gpt's MEASURED position, size, and color.
So Axis A must NOT call `reanchor()`. It needs a new capture-and-place step. The task prompt's
own UNKNOWN 1 already concedes this ("match gpt's rendered size and fill color and position, not
a planned size"), so the spec is internally consistent; only the early "then re-anchors" line is
misleading. Following the code, not that line.

Reused as-is (the prompt is right about these): `patch_ghosts()` is the scrubber (dilated ink
mask + per-row gradient interpolation fill, lines 94-164) and `measure()` is the sensor.

---

## 2. REUSE MAP (what exists vs what is new)

| Need (Axis A) | Status | Source |
|---|---|---|
| Detect WHERE gpt rendered the headline (position + extent) | EXISTS | `measure()` returns `ghost_text_boxes[]` with `bbox_frac` + `quad_frac`. When `expected=[headline lines]`, gpt's painted headline fuzzy-matches (>=0.6) and is classified as a "ghost" box. Naming clash (it is the INTENDED text, not a ghost) but the geometry is exactly what we want. |
| Scrub gpt's rendered text, leave no trace | EXISTS | `patch_ghosts()` (dilated mask + gradient-preserving fill). Reuse unchanged. |
| Fit licensed-font size to gpt's rendered pixel height | EXISTS (pattern) | `coverredraw_signs2to5.fit_size()` (lines 106-120) and `closed_loop._line_metrics()` invert size->height. Reuse the pattern. |
| Sample gpt's rendered ink color | EXISTS (pattern) | `coverredraw` takes `median(arr0[ink_mask])` (line 207). Same ink/bg split `patch_ghosts` already computes. Small new helper. |
| Build composite spec from captured geometry | NEW (small) | per line: `anchor_frac`=bbox center, `anchor`="mm", `size_px`=fitted, `color`=sampled, `content`/`font_role`/`brand`/`weight_hint` from inputs. Exactly the dict `composite()` consumes. coverredraw builds the same dict by hand (lines 243-251). |
| Overlay licensed glyphs at captured geometry | EXISTS | `composite_text.composite()` unchanged. |
| Strip chroma -> cutout (no-ref jobs only) | EXISTS | `strip_chroma()` unchanged. |
| Place at FREE SPACE, planned size (old reserve-box path) | EXISTS | `closed_loop()` + `reanchor()`. Kept behind a flag for A/B + rollback. |

Conclusion: Axis A = one new orchestrator function (capture -> scrub -> build-spec-from-capture
-> composite) that REUSES patch_ghosts + measure + composite + strip_chroma. It does not reuse
reanchor. coverredraw proves the capture-and-place math already works; we are writing the GENERAL,
OCR-driven version (coverredraw hardcodes per-sign boxes; we read them from measure()).

---

## 3. THE TWO AXES, AND WHERE THEY DIVERGE (stated unambiguously, per the task)

AXIS A  RENDER-AND-SCRUB  (UNIVERSAL — every flat_graphic job, ref or no-ref)
  Generation prompt asks gpt to render the COMPLETE sign INCLUDING the headline (no reserved
  blank box). Then: measure gpt's headline boxes -> capture position+size+color -> scrub the
  pixels -> overlay licensed glyphs at the captured geometry. Placement is MEASURED, not planned.

AXIS B  DIAL-DRIVEN PROMPT  (PER-TASK — only the generation prompt WORDING, only for ref jobs)
  `reference_relationship` is a 3-rung dial that selects the aligned-prompt wording. It changes
  only what the generation prompt SAYS; it does not touch Axis A.

DIVERGENCE (the unambiguous statement the task asked for):
- NO-REFERENCE job: Axis A only. Generation prompt = the existing register/tier-3 prompt, but in
  render-full-text mode (headline painted, no reserved box). Has NO dial. Keeps chroma + cutout.
- REFERENCE job: Axis A AND Axis B. Generation prompt = the dial-selected aligned prompt
  (image=[ref] fed to gpt-image-2). Chroma is DISABLED (the sign is rendered on the reference's
  own background, so there is no green field to key); cutout is deferred; final.png is the
  deliverable. Axis A still runs (capture/scrub/place), driven by OCR boxes + color, which do NOT
  depend on container/chroma detection, so placement is robust even when the sign is full-bleed.

---

## 4. AXIS A PRIMITIVE — `place_measured(image, lines, brand, weight_hint, chroma_key_hex|None)`

New function in `closed_loop_composite.py` (so it sits with the scrubber it reuses). Algorithm:

```
1. measure(image, expected=lines, chroma_key_hex)         # reuse the sensor
2. map each expected line -> its matched ghost box (by matched_expected / best fuzzy).
   CAPTURE per line: anchor_frac = bbox center; target_h_px = bbox height in px;
                     ink_color = median of ink pixels in the (padded) bbox (ink = far from
                     local bg, same split patch_ghosts uses). Detection is OCR-based
                     (measure ghost_text_boxes), NOT cover_redraw.text_masks — those red/dark
                     thresholds are AIA-specific and would not generalize. Reuse only the
                     brand-general helpers: cover_redraw.size_for_height + the spec shape.
   HONEST-NULL, PATH-SPECIFIC (guardrail, approved 2026-06-18):
     - NO-REFERENCE job: if not exactly one box per line (OCR merged/split/missed), fall back
       to the existing closed_loop()/reanchor free-space path (reanchor is DEFINED there: the
       container has detectable free space) and record "capture ambiguous -> free-space fallback".
     - REFERENCE job: reanchor is UNDEFINED (no reserved free-space box on a full-bleed ref).
       So LEAVE gpt's rendered text in place: do NOT scrub, do NOT overlay; set
       needs_review=true and record it in the run manifest. Never guess geometry, never
       free-space-fallback a ref job.
3. patch_ghosts(image, those boxes, container_color)      # reuse the scrubber (unchanged)
4. for each line: size_px = fit so _line_metrics height ~= target_h_px (coverredraw.fit_size
   pattern); build spec entry {content, font_role:'chinese_primary', brand, weight_hint,
   anchor_frac, anchor:'mm', size_px, color:ink_color}.
5. composite(scrubbed_image, spec) -> final.png + compliance manifest   # reuse
6. ocr_readback gate on final (reuse) ; if chroma_key_hex: strip_chroma -> cutout   # reuse
```

TIER-3 INDEPENDENCE (guardrail, approved 2026-06-18): place_measured sources the composite
headline LINES from `--must-include` and the FONT (font_role chinese_primary + weight_hint)
from the register profile / brand answer key. It NEVER reads `write_composite_spec(tier3)`, on
EITHER the ref or the no-ref path (uniform composite). `write_composite_spec(tier3)` is called
ONLY in `--reserve-headline-box` (old) mode; it is never invoked on ref jobs (which skip tier3),
so `write_composite_spec(tier3=None)` can never happen.

UNKNOWN 1 (placement-match) is handled in steps 2+4: position + size + fill color matched.
Outline/stroke match is the stretch goal: `composite()` already supports stroke_width/stroke_color;
detecting gpt's outline color is a second color-ring sample, attempted only if cheap, else left
and noted for the human's eye. Do NOT block on it.

This primitive does not import or call `reanchor()`.

---

## 5. AXIS B — the dial and three rungs

`register/reference_style_to_prompt.py`:
- `assemble_aligned_prompt(descriptor, message_lines, hero_icon, relationship="extend")` gains the
  dial. All three rung templates live in ONE labeled dict `RUNG_TEMPLATES` so the human edits
  wording easily.
  - `extend`: the PROVEN gold wording, verbatim shape from test_reffeed.py 16-29 ("Use the
    ATTACHED reference image as the EXACT visual-style template ... CHANGE ONLY THE MESSAGE to ...").
  - `match_style`: "STYLE reference ... adopt its visual language ... compose a FRESH layout ...
    Render the message text."
  - `mood`: "LOOSE inspiration for mood and energy only ... design an original sign ... Render the
    message text."
  ALL THREE instruct gpt to RENDER the headline text (Axis A needs painted text to capture).
  None reserve a blank area.
- `main()` gains `--relationship {extend,match_style,mood}` (default extend), passed through.

---

## 6. scene_author.py changes

- New `--aligned-prompt <path>`: when present (ref job), the generation prompt is that file's
  contents; SKIP `assemble_final_prompt` (and skip tier-3 authoring, an Anthropic call we do not
  need — the aligned prompt is self-contained; composite lines come from `--must-include`).
- New `--reserve-headline-box`: opt-in to the OLD reserve-box behavior (reservation prompt +
  closed_loop reanchor-to-free-space). DEFAULT (flag absent) = render-and-scrub. Mirrors the
  existing `--no-closed-loop` escape-hatch philosophy so the human can A/B and roll back.
- `assemble_final_prompt(..., render_headline=True)` (no-ref default): include the composited
  headline layers in the TEXT LAYOUT block (stop excluding them) and OMIT the RESERVED HEADLINE
  AREA block. `--reserve-headline-box` restores the old exclude+reserve behavior.
- Reference + chroma cannot coexist: when `--aligned-prompt` is set, force chroma OFF and record
  `chroma_disabled_for_reference=true` in run_manifest. ref-feed wins. (logo:omit branch already
  feeds image=[ref]; keep it.)
- Step 5 composite: render-and-scrub mode calls `place_measured(...)`; `--reserve-headline-box`
  mode calls the existing `closed_loop(...)`. `--no-closed-loop` (blind open-loop) still honored.

## 7. conductor.py changes

- Wire `inputs.reference_relationship` free text -> a clean dial enum {extend, match_style, mood}
  (map the existing long labels: "template..."->extend, "style..."->match_style,
  "inspiration..."->mood). Validate.
- `ask_questions`: ask the dial as a 3-choice question ONLY when a reference image is present.
- `_analyzer_argv`: pass `--relationship <dial>`.
- STOP discarding aligned_prompt.txt. Pass it to scene_author as `--aligned-prompt <sign_dir>/
  aligned_prompt.txt`. The analyzer runs BEFORE scene_author in the per-sign plan (it already
  does), so the file exists when scene_author needs it.
- Manifest: record `reference_relationship` (the dial), which rung wording was used, and set
  `injected_into_generation=true` for reference jobs (no longer false).

## 8. UNKNOWN 2 — cutout

Reference jobs disable chroma, so there is no green to strip and no clean cutout: final.png (the
composited face) is the deliverable. DEFER the cutout for ref jobs; record `cutout: "deferred
(reference job, no chroma backdrop)"` honestly. No-reference jobs keep chroma + cutout unchanged.

---

## 9. WHAT THE FREE SELF-TEST CAN AND CANNOT PROVE (honest boundary)

FREE (no image gen) and in the self-test:
  1. dial selects 3 measurably-different wordings; extend carries the proven shape.
  2. aligned prompt is INJECTED (conductor passes --aligned-prompt; scene_author uses it; manifest
     no longer says injected=false for ref jobs) — asserted via dry-run plan/argv.
  3. render-and-scrub is the DEFAULT: the generation prompt has no reserve-a-blank-box instruction
     for both a ref job and a no-ref job.
  4. no-ref job still planned end-to-end (register prompt + render-and-scrub).
  5. brand-generality preserved (aia vs taichi; no brand literal in conductor.py).
  Plus: unit-test the pure helpers (size-fit inverts height; color-sample picks ink over bg) on
  synthetic arrays — still free.

ONLY THE PAID RUN + THE HUMAN'S EYE can validate: actual image fidelity to the reference, scrub
cleanliness (no halo/trace left), and placement-match quality (does the licensed overlay sit
seamlessly where/size/color gpt painted). The self-test cannot judge pixels. Stated plainly in
the final report.

---

## 10. THE ONE PAID VALIDATION COMMAND (human runs this, not me)

```
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json
```
(conductor_inputs_example.json already has reference_relationship: "template ..." -> extend.)
Look at, per sign: final.png. Judge (a) does it match the reference's visual language, (b) is
gpt's headline fully scrubbed with no ghost/halo, (c) does the licensed-font headline sit at the
same position/size/color gpt painted, seamlessly. placement_report.json records the captured
geometry, the fallback (if any), and the readback gate.

---

## 11. RISK / SCOPE

This mutates two proven crown-jewel files (scene_author Step 3/5, closed_loop_composite gains a
new primitive). The new primitive is the risk; it is bounded by reuse and by the honest-null
fallback to the existing free-space path. The default flips (reserve-box -> render-and-scrub) but
the old path stays one flag away for rollback. No brand literals leak into conductor/scene_author.
```
