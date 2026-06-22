# CLAUDE.md — Handyprint Brand Design Tool

> **This file is the engineer's brief. It is loaded into every fresh AI session.**
> Read it fully before touching code. It carries the whole project so you do not
> have to reconstruct it from the chat. When this file and the code disagree, the
> CODE wins — and you fix this file in the same commit.
>
> **`SYSTEM_MAP.md` is the companion source of truth** for project STATUS (what
> works vs what doesn't, the live regroup notes, the roadmap). CLAUDE.md = how the
> system is built + how to work in it. SYSTEM_MAP = where the project stands today.
> Read the top regroup block of SYSTEM_MAP.md after this file.

---

## 0. ONE-SENTENCE PURPOSE

Get a **non-designer** from a messy brief + brand assets to a **handoff-quality
DRAFT** marketing asset (today: die-cut event signs, 手举牌) — on-brand where the
brand must govern, on-occasion where the task must govern. **It produces drafts a
human finishes, NOT final art.** That last clause is the guardrail against
tunneling toward "one magic button that outputs finished work."

---

## 1. CORE PRINCIPLES (do not violate — these are load-bearing)

1. **Agent-free ≠ human-free.** The dependency we are killing is the *AI stagehand*
   (an agent silently gluing steps + judging invisibly = unshippable,
   unreproducible). The *human designer* stays in the loop BY DESIGN at the INPUT
   gates (brief/context/reference) and the TASTE gates (approve/nudge). Never design
   toward "type one command, walk away." Automate the glue + drudgery, never the
   essential inputs or taste.
2. **Ground truth = the user's eye, not VLM scores.** Vision models over-score and
   rubber-stamp. Never trust a model's self-graded PASS. Verify artifacts on disk;
   the human's eyeball is the final gate.
3. **Falsifiable tests only.** A self-test must check CORRECTNESS, not token-presence.
   `"stroke" in prompt` is a no-op gate (it passed a charcoal stroke for a "white
   stroke" requirement once — real bug). Assert VALUES the wrong implementation
   cannot satisfy. Do not hand-tune to pass one specific image; build what
   GENERALIZES across brands/tasks.
4. **Generalizes vs task-taste.** Before any fix ask: does this make the TOOL better
   (generalizes to all brands/tasks) or just this IMAGE better (one-off taste)?
   Generalizes → build it. Task-taste → it's a human nudge or canvas touch-up, do
   NOT bake it in. (Examples judged task-taste: "text slightly bigger", a specific
   font swap. Judged generalizing: chroma containment, the occlusion gate.)
5. **Honest nulls.** When a step can't do its job, emit `null` + a note and fall
   back explicitly — never invent geometry, never fabricate a result. Every
   fallback is recorded in the run manifest.
6. **No em-dashes in any text written FOR THE USER** (docs, messages, deliverables).
   Use commas, colons, parentheses, or restructure. (Standing rule from Alec.)

---

## 2. THE INTELLECTUAL CORE (read this or nothing downstream makes sense)

**The deep tension:** a brand's visual language and a task's visual language
DIVERGE. AIA's DNA is corporate red, sharp gothic type, mandatory logo, rectangular.
But an anti-fraud event sign people pose with at a festival wants playful, rounded,
die-cut, no logo. They clash. **Reconciliation is the whole game:** brand DNA
governs HARD where it must (primary color, licensed fonts, logo), the task governs
SOFT where it must (atmosphere, shape, register). The clash is resolved
**per-dimension** into a `register_profile` with `anchors_held` vs `locks_flexed`.

**Direction vs magnitude (the mechanism that makes register smart):**
- The human's guided **subfields** set register DIRECTION (which lane: event_prop /
  marketing / formal; logo or not; strictness).
- A **reference image** sets register MAGNITUDE (how far — the actual slider
  coordinates), via a blind vision score.
- Proof it works: in the 6/18 run, Alec typed formality **2** / playfulness **8**
  (extremes), but the reference blind-scored **6/5**, so the profile landed at
  **6/5**, not the raw 2/8. The extremes picked the *lane*; the reference dialed in
  *how far*. Meanwhile AIA red held (ref #C41E3A ≈ brand #D31145, ΔRGB 23) and the
  font resolved to the compliant-but-playful 汉仪元隆黑.

---

## 3. THE TWO JOB TYPES (this distinction drives almost every branch in the code)

| | **Reference job** | **No-reference job** |
|---|---|---|
| Trigger | a reference image is supplied | none |
| Style source | analyzer → aligned prompt + fed ref crop | tier-3 scene authored by Claude |
| Dial (Axis B) | yes: `extend` / `match_style` / `mood` | none |
| tier-3 authoring | **SKIPPED** | runs (Anthropic call) |
| Chroma containment | **OFF** (sign renders on ref's own bg) | **ON** (#00B140 green) |
| Deliverable | `final.png` (cutout deferred) | `cutout.png` + `preview_white.png` |
| Capture-fail fallback | leave gpt's text, flag `needs_review` | free-space `closed_loop` reanchor |

The conductor decides job type from `inputs.reference_image`; `scene_author` decides
from the presence of `--aligned-prompt`.

---

## 4. THE PIPELINE (one flow, two entry points)

```
INPUTS (per brand, once)         INPUTS (per job)
  logo / VI manual / fonts         subfields (the form) + reference image [optional]
        │                                  │
        ▼                                  ▼
  A. BRAND ANALYSIS                  B. TASK ANALYSIS
  extract_* → answer_keys/<b>.json   subfields → register DIRECTION (derive_register)
  (colors, typography roles,         reference → register MAGNITUDE (calibrate_from_reference)
   licensed font index)                     │
        └──────────► C. RECONCILIATION ◄────┘
              register_profile {anchors_held, locks_flexed, font_resolved, slider coords}
                                  │
                                  ▼
              D. SCENE / PROMPT  (scene_author.py)
              no-ref: author tier-3 scene plan + assemble prompt (+chroma)
              ref:    use analyzer's aligned prompt verbatim (tier-3 skipped, chroma off)
                                  │
                                  ▼
              E. GENERATION  (gpt-image-2 via images.edit, generate.py)
              feeds [logo and/or ref crop] + prompt → generated.png
                                  │
                                  ▼
              F. PLACEMENT (licensed font)  (closed_loop_composite.py)
              render-and-scrub (default): measure gpt's painted headline →
                scrub it → overlay licensed font at MEASURED geometry
              reserve-box (legacy): reserve blank zone → measure → patch →
                re-anchor to free-space center
              → compliance manifest + OCR-readback gate
                                  │
                                  ▼
              G. HUMAN GATE  (conductor approve loop / approve.py)
              show drafts → approve / nudge <sign>: <change> / abort
                                  │
                                  ▼
              DRAFT OUT → human finishes on canvas
```

**Two entry points, do not confuse them:**
- `harness/run_harness.py aia` — the THIN spine. Template-fill + generate only.
  AIA-only, reference stubbed, NO scene_author/register/composite. Good for "basic
  on-brand variants," NOT the showcase signs.
- `harness/conductor.py` — the REAL spine (the orchestrator). Runs the full chain
  above with human gates. This is what produces the real signs and what we build on.

---

## 5. MODULE MAP (every file, what it owns)

### `harness/` — the spine + primitives
- **`conductor.py`** — the brand-general human-gate ORCHESTRATOR (729 lines). Pure
  stdlib (no numpy/anthropic import — trivially testable). Sequences the proven
  scripts as foreground subprocesses, with honest-null fallbacks. Has `--dry-run`
  (plan only, no paid calls) and `--no-approve`. THIS is the top of the tree.
- **`scene_author.py`** — the single-sign engine (1125 lines). Authors tier-3 (no-ref)
  or consumes an aligned prompt (ref); assembles the final prompt; calls generate;
  runs placement (Step 5). Has `--explain` (prints resolved mode/source/chroma as
  JSON and EXITS before any model call — a FREE structural test surface).
- **`closed_loop_composite.py`** — the PLACEMENT actuator (889 lines). Contains:
  - `place_measured()` — Axis A render-and-scrub (the default path).
  - `closed_loop()` — legacy reserve-box: measure→patch→reanchor→composite.
  - `patch_ghosts()` — scrubber (dilated ink mask + gradient-preserving fill).
  - `reanchor()` — centers planned text on detected free space (reserve-box only).
  - `strip_chroma()` — green backdrop → cutout.png + preview_white.png.
  - `ocr_readback()` — the occlusion gate (re-reads the final image).
- **`measure_canvas.py`** — the SENSOR (517 lines). OCR every text box (flags ghost
  headlines that match expected text); recover the container + free space. Two
  paths: `detect_container_chroma` (deterministic, by color distance from key) and
  legacy HSV `detect_container` (fragile). `measure()` is the public entry.
- **`composite_text.py`** — the licensed-font COMPOSITOR (327 lines). Resolves a
  text layer to a real font file via the answer key's typography + library_index;
  writes a `<out>.compliance.json` manifest tagging each layer `licensed_exact` /
  `licensed_family_other_weight` / `fallback_system` / `MISSING`. **Silent fallback
  is the cardinal sin — it warns LOUDLY; MISSING hard-fails.**
- **`generate.py`** — gpt-image-2 wrapper (`images.edit`, 240s timeout, 1 retry).
- **`assemble_prompt.py`** — thin-spine template filler (used by run_harness only).
- **`approve.py`** — standalone tier-3 nudge loop (author→summarize→nudge→generate).
  NOTE: the conductor does NOT chain approve.py; it re-invokes scene_author with the
  nudge as `--style-notes` (approve.py authors a FRESH tier-3, can't nudge a specific
  already-generated sign).
- **`cover_redraw.py` / `coverredraw_signs2to5.py`** — AIA-specific cover-and-redraw
  (X-mark handling). `coverredraw_signs2to5` is the hardcoded-per-job anti-pattern
  the conductor generalizes; don't extend it.

### `register/` — the reconciliation engine
- **`derive_register.py`** — DIRECTION. Pure rule table: subfields → register_profile.
  Every decision appended to `_derivation_trace` (no LLM; inspectable + falsifiable).
- **`calibrate_from_reference.py`** — MAGNITUDE. Two vision calls: blind Step-0 score
  (formality/playfulness) + style-evidence extraction; cross-checks vs brand DNA →
  anchors_held / locks_flexed. Writes calibration.json.
- **`blind_score.py`** — blind VLM scoring on the Step-0 rubric (the falsification
  instrument; energy was dropped as a decoy, grab is the target outcome).
- **`reference_style_to_prompt.py`** — the reference STYLE analyzer. One vision call
  → style descriptor; `assemble_aligned_prompt()` (pure) → the gpt-image-2 prompt.
  Holds `RUNG_TEMPLATES` (Axis B dial: extend / match_style / mood). WIRED into the
  conductor as of 6/18 (`scene_author --aligned-prompt`).

### data / config
- **`answer_keys/<brand>.json`** — extracted brand DNA. `fields.colors` (role+hex),
  `fields.typography` (roles, a `styles` map font_role_hint→licensed family, a
  `library_index` path, VI rules). One per brand. AIA verified; taichi/xiucai partial.
- **`config/<brand>.yaml`** — per-brand run config for the THIN spine only. AIA only.
- **`intents/*.json`** — per-sign Tier-2 intent dicts (no-ref path).
- **`brief_schema_v3.json`** — the 4-bucket guided-subfields schema (the intake form).
- **`conductor_inputs_example.json`** — the canonical `--inputs` example (ref job).

### docs / specs (the WHY — read on demand, not every session)
- **`SYSTEM_MAP.md`** — STATUS source of truth. Read its top regroup block.
- **`*_SPEC.md`** (repo root) — one build contract per feature.
- **`docs/*.md`** — design notes (the reasoning behind each layer).
- **`RENDER_AND_SCRUB_DESIGN_NOTE.md`** — the most recent build's reuse map + the
  two-axis design (start here for the current placement path).

### gitignored (LOCAL ONLY — a fresh clone will not have these)
- **`brands/`** — licensed fonts + client IP + VI PDFs (confidential AND ~188M).
- **`output/`** — generated PNGs (regenerable, ~141M).
- **`.env`** — secrets. Keys load from `~/.hermes/.env` via python-dotenv.

---

## 6. TOOLCHAIN

- **Python 3.11.15** in `.venv` (the project venv). Always run scripts as
  `.venv/bin/python <script>` (or `source .venv/bin/activate` first).
- **Installed deps** (no `requirements.txt` exists yet — see TODO below):
  numpy 2.4.6, Pillow 12.2.0, scipy 1.17.1, rapidocr-onnxruntime 1.4.4,
  onnxruntime 1.26.0, anthropic 0.105.2, openai 2.41.0, PyYAML 6.0.3,
  python-dotenv 1.2.2, fonttools 4.63.0.
- **Install a new dep:** `uv pip install --python .venv/bin/python <pkg>`.
- **API keys:** loaded from `~/.hermes/.env` via `load_dotenv(...)` at the top of
  each script that needs them. Do NOT hardcode keys; do NOT print them.
- **Models:** tier-3 authoring + vision use Anthropic `claude-opus-4-5` →
  fallback `claude-sonnet-4-6`. Image generation uses OpenAI `gpt-image-2`
  (`images.edit`). Canvas is always **1536×1024**. Chroma key is **#00B140**.

---

## 7. HOW TO RUN + HOW TO TEST (the FREE structural surfaces)

**Free (no paid calls) — use these to verify structure before spending a cent:**
```
.venv/bin/python test_conductor.py            # conductor self-test (5 checks, dry-run)
.venv/bin/python test_render_and_scrub.py     # axis A+B self-test (5 checks, --explain)
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/dry --dry-run --no-approve      # writes plan.json + glue, NO model calls
.venv/bin/python harness/scene_author.py --brand aia --asset-profile flat_graphic \
    --aligned-prompt /tmp/x.txt --explain      # prints mode/source/chroma, EXITS pre-model
```
These exit before any vision/Anthropic/gpt-image-2 call. **Always run the relevant
free surface after a change; only spend on a paid run when structure is green.**

**Paid (real generation) — the one validation command:**
```
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json
```
Outputs land in `output/run_<brand>_<timestamp>/`. Judge `final.png` per sign with
the HUMAN EYE (text fits with margin? scrub clean? placement matches?). The
`conductor_manifest.json` + per-sign `render_scrub_report.json` record what happened.

**Cost discipline:** image gen is the expensive, slow step. Never put a paid
generation inside a self-test. Build/verify on the free surfaces; run the paid
pipeline directly afterward.

---

## 8. DEV WORKFLOW (the new spec-driven model — supersedes the old "no commits" rule)

The project outgrew chat-driven development. The model now:
- **The REPO is the durable context** (this file + SYSTEM_MAP + specs + tests + git
  history). Hold the project in the repo, not in the conversation.
- **One spec → one task → one module → one falsifiable test → one commit.** Keep
  each task small enough to fit a fresh context window. Touch one module, not twelve.
- **Commit per task** with a clear message. **⚠️ Many `*_SPEC.md` files still say
  "No git commits" — that instruction is SUPERSEDED. Commit your work.** Keep the
  client IP / secrets out (already gitignored: `brands/`, `output/`, `.env`).
- **Remote:** `origin` → github.com/alecxie1/xcela (private). Push after a session so
  work is backed up off-machine.
- **Parallel work:** Claude Code `--worktree <name>` isolates a branch in
  `.claude/worktrees/` so two tasks don't collide.
- **Keep this file + SYSTEM_MAP current in the SAME commit as the code change** that
  makes them stale. A stale brief is worse than none — it actively misleads the next
  fresh session. (The 6/17 version of this file claimed the analyzer was "not wired"
  and the conductor "unbuilt" days after both shipped.)

---

## 9. CURRENT FRAME + KNOWN FAILURE (read SYSTEM_MAP's 6/18 regroup for the live state)

The 6/18 reference run (`output/run_aia_20260618_121133/`) produced 2 signs that
PASS the self-tests and font compliance but FAIL the human eye on 3 counts with ONE
root cause:
- (a) headline text oversized — overflows the die-cut; s2's text runs off-canvas.
- (b) the scrub damages/covers graphics (text-on-icon collision on s1).
- (c) the two signs are the SAME sign behind different text — not a varied family.

**Root cause (one frame): render-and-scrub + dial=`extend` is structurally a "ONE
TEMPLATE, N TEXTS" machine.** It measures gpt's oversized text and faithfully
reproduces the overflow (no fit-to-margin constraint exists); scrubbing the text
region tears up whatever it overlapped; and feeding one reference panel + "extend"
tells gpt to CLONE it. Fixing `measure`/`patch_ghosts` does NOT bridge this — it is
the wrong frame.

**The agreed target frame (AIA-specific, 6/18):** "**kit of parts + bespoke
per-message composition**." The reference is a STYLE SYSTEM to internalize, not a
panel to clone. Each sign is composed fresh from its message's meaning (icon that
MEANS the message + a layout for its rhetorical mode + a reserved text zone with type
fitted INTO it), unified by a shared kit (palette/border/font/accent vocabulary).
The AIA 定稿 ground truth confirms it: those panels DIFFER from each other.
**This reframe is NOT yet built. No code until the design note is written + aligned.**

> Open meta-problem (named, not yet solved): every design task has a different "unit
> of work," and discovering it took weeks of trials for AIA. How to reach the right
> frame FASTER for a new task type is itself unsolved. Don't assume AIA's frame
> transfers to the next brand/asset.

---

## 10. GLOSSARY (terms used everywhere)

- **register** — the formality/playfulness "voice" of an asset (event_prop /
  marketing / formal). The thing reconciliation tunes.
- **anchors_held / locks_flexed** — brand dimensions kept locked vs released for this
  task (the per-dimension output of reconciliation).
- **tier-3 scene plan** — the structured composition spec Claude authors for a no-ref
  job (palette, staging, container_shape, text_layout, headline_reservation).
- **chroma containment** — rendering a die-cut sign as ONE object on flat #00B140 so
  the cutout is recovered deterministically by color distance (gpt-image-2 can't do
  transparent backgrounds).
- **ghost text** — headline text gpt PAINTS into the image. In reserve-box mode it's
  an unwanted intruder to scrub; in render-and-scrub it's the INTENDED text we
  measure then replace (same OCR machinery, opposite intent — naming clash in code).
- **render-and-scrub (Axis A)** — measure gpt's painted headline, scrub it, overlay
  the licensed font at the MEASURED geometry. The default placement path.
- **reserve-box (legacy)** — reserve a blank zone, place planned-size text at the
  detected free-space center. Behind `--reserve-headline-box` for rollback/A-B.
- **the dial (Axis B)** — `extend` / `match_style` / `mood`: how closely a reference
  job clones the reference. Selects prompt WORDING only.
- **licensed_exact** — the compliance verdict that the exact mandated licensed font
  file was used (the only fully-compliant resolution).

---

## 11. PITFALLS (hard-won — don't relearn these)

- **`measure`'s legacy HSV path is fragile;** the chroma path is the proven one.
  Reference jobs have NO chroma, so placement there leans on OCR geometry alone.
- **`place_measured` inherits gpt's text size** — there is currently no "fit within
  the sign with margin" clamp. (This is failure (a) above.)
- **Scrub damage** happens wherever painted text overlapped a graphic; on a ref job
  `interior_mask` is None so the scrub is less protected.
- **A green self-test ≠ correct output.** The self-tests assert structure
  (sequence, injection, brand-generality), NOT pixel quality. Only the human eye
  validates fidelity/scrub/placement. Always eyeball the paid run.
- **Don't reuse `reanchor()` for render-and-scrub** — it centers PLANNED-size text on
  FREE SPACE, the opposite of matching gpt's painted geometry.
- **VLM vision extraction is non-deterministic** — it can invert figure/ground on
  dark backdrops and conflate subject-topic with register. The fed ref IMAGE rescues
  an imperfect text read, but don't over-trust the descriptor alone.

---

## 12. TODO / DEBT (housekeeping the next sessions should pick up)

- **No `requirements.txt` / `pyproject.toml`** — deps are implicit. Freeze them so a
  fresh clone is reproducible (`uv pip freeze` → `requirements.txt`).
- **12 `*_SPEC.md` files carry the stale "No git commits" line** — supersede or note
  when you next touch each.
- **Repo layout is flat** (~30 scripts at two levels). As the kit-of-parts reframe
  lands, modularize so one task touches one module (the spec-driven goal).
- **Only AIA has a config + verified answer key.** Brand-generality is designed-in but
  unproven on a second brand.
