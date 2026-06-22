# ARCHITECTURE — Xcela (Handyprint Brand Design Tool)

> Deep reference. `CLAUDE.md` is the lean always-loaded brief and points here for
> detail. Read the section you need; you do NOT need to read this whole file every
> session. `SYSTEM_MAP.md` carries live STATUS; this file carries how-it-is-built.

---

## 1. PURPOSE + PRINCIPLES (full)

Get a non-designer from a messy brief + brand assets to a handoff-quality DRAFT
marketing asset, on-brand where the brand must govern, on-occasion where the task must
govern. It produces drafts a human finishes, NOT final art (the guardrail against
tunneling toward a "magic button").

The 6 core principles are in CLAUDE.md. Expanded notes:
- **Agent-free ≠ human-free** is THE founding constraint. The dependency being killed is
  the *AI stagehand* (an agent silently gluing steps + judging invisibly =
  unshippable/unreproducible). The human designer stays BY DESIGN at INPUT gates
  (brief/context/reference) and TASTE gates (approve/nudge). Automate the glue + drudgery,
  never the essential inputs or taste.
- **Falsifiable tests:** a real prior bug — a self-test scored a "thick WHITE stroke"
  requirement as PASS because the token "stroke" appeared, while the actual value was
  charcoal. Assert the VALUE (stroke is white-ish), never mere presence.

---

## 2. THE INTELLECTUAL CORE — reconciliation

Brand visual language and task visual language DIVERGE. AIA DNA: corporate red, sharp
gothic, mandatory logo, rectangular. An anti-fraud festival photo-prop wants: playful,
rounded, die-cut, no logo. They clash. Reconciliation resolves the clash PER-DIMENSION
into a `register_profile` with `anchors_held` (kept locked) vs `locks_flexed` (released).

**Direction vs magnitude (the mechanism):**
- Guided **subfields** set register DIRECTION: which lane (event_prop / marketing /
  formal), logo or not, strictness.
- A **reference image** sets register MAGNITUDE: the actual slider coordinates, via a
  blind vision score (no brand context).
- **Proof (6/18 run):** Alec typed formality 2 / playfulness 8 (extremes), but the
  reference blind-scored 6/5, so the profile landed at 6/5, not 2/8. Extremes picked the
  lane; the reference dialed how far. AIA red held (ref #C41E3A ≈ brand #D31145, ΔRGB 23);
  font resolved to the compliant-but-playful 汉仪元隆黑.

This is the deep tension Richard named (品牌 DNA vs task language). It is the intellectual
core of the tool; everything else is plumbing around it.

---

## 3. THE TWO JOB TYPES (full table — drives most branches in code)

| | Reference job | No-reference job |
|---|---|---|
| Trigger | `inputs.reference_image` set | none |
| Style source | analyzer → aligned prompt + fed ref crop | tier-3 scene authored by Claude |
| Dial (Axis B) | `extend` / `match_style` / `mood` | none |
| tier-3 authoring | SKIPPED | runs (Anthropic call) |
| Chroma containment | OFF (sign on ref's own bg) | ON (#00B140 green) |
| Deliverable | `final.png` (cutout deferred) | `cutout.png` + `preview_white.png` |
| Capture-fail fallback | leave gpt's text, flag `needs_review` | free-space `closed_loop` reanchor |

Conductor decides job type from `inputs.reference_image`; scene_author decides from the
presence of `--aligned-prompt`.

---

## 4. THE PIPELINE (full flow)

```
INPUTS (per brand, once)         INPUTS (per job)
  logo / VI manual / fonts         subfields (the form) + reference image [optional]
        │                                  │
        ▼                                  ▼
  A. BRAND ANALYSIS                  B. TASK ANALYSIS
  extract_* → answer_keys/<b>.json   subfields → DIRECTION (derive_register)
  (colors, typography roles,         reference → MAGNITUDE (calibrate_from_reference)
   licensed font index)                     │
        └──────────► C. RECONCILIATION ◄────┘
              register_profile {anchors_held, locks_flexed, font_resolved, sliders}
                                  │
                                  ▼
              D. SCENE / PROMPT  (scene_author.py)
              no-ref: author tier-3 + assemble prompt (+chroma)
              ref:    use analyzer's aligned prompt verbatim (tier-3 skipped, chroma off)
                                  │
                                  ▼
              E. GENERATION  (gpt-image-2 images.edit, generate.py)
              feeds [logo and/or ref crop] + prompt → generated.png
                                  │
                                  ▼
              F. PLACEMENT (licensed font)  (closed_loop_composite.py)
              render-and-scrub (default): measure gpt's painted headline → scrub →
                overlay licensed font at MEASURED geometry
              reserve-box (legacy): reserve blank zone → measure → patch → re-anchor
              → compliance manifest + OCR-readback gate
                                  │
                                  ▼
              G. HUMAN GATE  (conductor approve loop)
              show drafts → approve / nudge <sign>: <change> / abort
                                  │
                                  ▼
              DRAFT OUT → human finishes on canvas
```

**Two entry points (do not confuse):**
- `harness/run_harness.py aia` — THIN spine: template-fill + generate only. AIA-only,
  reference stubbed, NO scene_author/register/composite. Basic on-brand variants only.
- `harness/conductor.py` — the REAL spine. Full chain + human gates. Build on this.

---

## 5. MODULE MAP (every file, what it owns)

### `harness/`
- **conductor.py** (729 ln) — brand-general human-gate ORCHESTRATOR. Pure stdlib (no
  numpy/anthropic import → trivially testable). Sequences proven scripts as foreground
  subprocesses with honest-null fallbacks. `--dry-run` (plan only, no paid calls),
  `--no-approve`. Top of the tree.
- **scene_author.py** (1125 ln) — single-sign engine. Authors tier-3 (no-ref) or consumes
  an aligned prompt (ref); assembles final prompt; calls generate; runs placement (Step 5).
  `--explain` prints resolved mode/source/chroma as JSON and EXITS before any model call
  (FREE structural test surface).
- **closed_loop_composite.py** (889 ln) — PLACEMENT actuator:
  - `place_measured()` — Axis A render-and-scrub (default path).
  - `closed_loop()` — legacy reserve-box: measure→patch→reanchor→composite.
  - `patch_ghosts()` — scrubber (dilated ink mask + gradient-preserving fill).
  - `reanchor()` — centers planned text on detected free space (reserve-box ONLY).
  - `strip_chroma()` — green backdrop → cutout.png + preview_white.png.
  - `ocr_readback()` — occlusion gate (re-reads the final image).
- **measure_canvas.py** (517 ln) — the SENSOR. OCR every text box (flags ghost headlines
  matching expected text); recover container + free space. `detect_container_chroma`
  (deterministic, color distance from key) vs legacy HSV `detect_container` (fragile).
  `measure()` is the public entry.
- **composite_text.py** (327 ln) — licensed-font COMPOSITOR. Resolves a layer to a real
  font file via answer key typography + library_index; writes `<out>.compliance.json`
  tagging each layer licensed_exact / licensed_family_other_weight / fallback_system /
  MISSING. Silent fallback = cardinal sin → warns LOUDLY; MISSING hard-fails.
- **generate.py** — gpt-image-2 wrapper (images.edit, 240s timeout, 1 retry).
- **assemble_prompt.py** — thin-spine template filler (run_harness only).
- **approve.py** — standalone tier-3 nudge loop. NOTE: the conductor does NOT chain this;
  it re-invokes scene_author with the nudge as `--style-notes` (approve.py authors a FRESH
  tier-3, can't nudge a specific already-generated sign).
- **cover_redraw.py / coverredraw_signs2to5.py** — AIA-specific X-mark cover-and-redraw.
  coverredraw_signs2to5 is the hardcoded-per-job anti-pattern the conductor generalizes;
  do not extend it.

### `register/`
- **derive_register.py** — DIRECTION. Pure rule table: subfields → register_profile, every
  decision in `_derivation_trace` (no LLM; inspectable + falsifiable).
- **calibrate_from_reference.py** — MAGNITUDE. Two vision calls: blind Step-0 score +
  style-evidence extraction; cross-checks vs brand DNA → anchors_held / locks_flexed.
- **blind_score.py** — blind VLM scoring on the Step-0 rubric (the falsification instrument).
- **reference_style_to_prompt.py** — the reference STYLE analyzer. One vision call → style
  descriptor; `assemble_aligned_prompt()` (pure) → the gpt-image-2 prompt. Holds
  `RUNG_TEMPLATES` (Axis B dial: extend / match_style / mood). WIRED 6/18 via
  `scene_author --aligned-prompt`.

### data / config
- **answer_keys/<brand>.json** — extracted brand DNA: colors (role+hex), typography (roles,
  a `styles` map font_role_hint→family, a `library_index` path, VI rules). AIA verified;
  taichi/xiucai partial.
- **config/<brand>.yaml** — per-brand run config for the THIN spine only. AIA only.
- **intents/*.json** — per-sign Tier-2 intent dicts (no-ref path).
- **brief_schema_v3.json** — the 4-bucket guided-subfields schema (the intake form).
- **conductor_inputs_example.json** — canonical `--inputs` example (a ref job).

### gitignored (LOCAL ONLY — a fresh clone lacks these)
- **brands/** — licensed fonts + client IP + VI PDFs (confidential, ~188M).
- **output/** — generated PNGs (regenerable, ~141M).
- **.env** — secrets (keys actually load from ~/.hermes/.env).

---

## 6. TOOLCHAIN (full)
- Python 3.11.15 in `.venv`. Run as `.venv/bin/python <script>`.
- Installed deps (no requirements.txt yet — see §12): numpy 2.4.6, Pillow 12.2.0,
  scipy 1.17.1, rapidocr-onnxruntime 1.4.4, onnxruntime 1.26.0, anthropic 0.105.2,
  openai 2.41.0, PyYAML 6.0.3, python-dotenv 1.2.2, fonttools 4.63.0.
- Install: `uv pip install --python .venv/bin/python <pkg>`.
- Keys from ~/.hermes/.env via load_dotenv. Models: opus-4-5→sonnet-4-6 (author/vision),
  gpt-image-2 (gen). Canvas 1536×1024. Chroma #00B140.

---

## 7. TEST SURFACES (full)
FREE (no paid calls), run before spending:
```
.venv/bin/python test_conductor.py            # 5 checks, dry-run
.venv/bin/python test_render_and_scrub.py     # 5 checks, --explain
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/dry --dry-run --no-approve
.venv/bin/python harness/scene_author.py --brand aia --asset-profile flat_graphic \
    --aligned-prompt /tmp/x.txt --explain
```
PAID (real generation), the one validation command:
```
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json
```
Outputs → `output/run_<brand>_<timestamp>/`. Judge final.png with the HUMAN EYE.
Cost discipline: never put paid generation in a self-test; build/verify on free surfaces.

---

## 8. DEV WORKFLOW (full)
The project outgrew chat-driven dev. Model now:
- REPO = durable context (CLAUDE.md + SYSTEM_MAP + specs + tests + git history).
- One spec → one task → one module → one falsifiable test → one commit. Small enough for
  one fresh context. Spec Kit drives this (`/specify`, `/plan`, `/tasks`, `/implement`).
- ⚠️ Many `*_SPEC.md` files still say "No git commits" — that is SUPERSEDED. Commit work.
- origin = github.com/alecxie1/xcela (private). Push after a session for off-machine backup.
- Parallel work: Claude Code `--worktree <name>` isolates a branch in `.claude/worktrees/`.
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit as the change that staled them.

---

## 9. CURRENT FRAME + KNOWN FAILURE (live state: SYSTEM_MAP 6/18 regroup)
The 6/18 reference run (output/run_aia_20260618_121133/) passes self-tests + font
compliance but FAILS the human eye on 3 counts, ONE root cause:
- (a) headline text oversized — overflows the die-cut; s2's text runs off-canvas.
- (b) scrub damages/covers graphics (text-on-icon collision, s1).
- (c) the two signs are the SAME sign behind different text — not a varied family.

Root cause (one frame): render-and-scrub + dial=`extend` is structurally a "ONE TEMPLATE,
N TEXTS" machine. It measures gpt's oversized text and reproduces the overflow (no
fit-to-margin constraint); scrubbing the text region tears up whatever it overlapped;
feeding one ref panel + "extend" tells gpt to CLONE it. Fixing measure/patch_ghosts does
NOT bridge this — wrong frame.

Target frame (AIA-specific, agreed 6/18): "kit of parts + bespoke per-message
composition." The reference is a STYLE SYSTEM to internalize, not a panel to clone. Each
sign composed fresh from its message's meaning (icon that MEANS the message + a layout for
its rhetorical mode + a reserved text zone with type fitted INTO it), unified by a shared
kit (palette/border/font/accent vocabulary). The AIA 定稿 ground truth confirms it: those
panels DIFFER from each other. NOT yet built — no code until the spec is written + aligned.

> Open meta-problem (named, not solved): every design task has a different "unit of work,"
> and discovering it took weeks for AIA. Reaching the right frame FASTER for a new task
> type is itself unsolved. Don't assume AIA's frame transfers to the next brand/asset.

---

## 10. GLOSSARY
- **register** — the formality/playfulness "voice" (event_prop / marketing / formal).
- **anchors_held / locks_flexed** — brand dimensions kept locked vs released for this task.
- **tier-3 scene plan** — the structured composition spec Claude authors for a no-ref job.
- **chroma containment** — render a die-cut sign as ONE object on flat #00B140 so the
  cutout is recovered deterministically by color distance (gpt can't do transparent bg).
- **ghost text** — headline text gpt PAINTS. Reserve-box: an intruder to scrub. Render-and-
  scrub: the INTENDED text we measure then replace. Same OCR machinery, opposite intent.
- **render-and-scrub (Axis A)** — measure gpt's painted headline, scrub it, overlay the
  licensed font at the MEASURED geometry. Default placement path.
- **reserve-box (legacy)** — reserve a blank zone, place planned-size text at the detected
  free-space center. Behind `--reserve-headline-box`.
- **the dial (Axis B)** — extend / match_style / mood: how closely a ref job clones the
  reference. Selects prompt WORDING only.
- **licensed_exact** — compliance verdict that the exact mandated licensed font file was
  used (the only fully-compliant resolution).

---

## 11. PITFALLS (full)
- `measure`'s legacy HSV path is fragile; the chroma path is proven. Ref jobs have NO
  chroma, so placement there leans on OCR geometry alone.
- `place_measured` inherits gpt's text size — no fit-to-margin clamp (failure (a)).
- Scrub damage happens wherever painted text overlapped a graphic; on a ref job
  `interior_mask` is None so the scrub is less protected.
- A green self-test ≠ correct output. Self-tests assert STRUCTURE, not pixel quality. Only
  the human eye validates fidelity/scrub/placement.
- Don't reuse `reanchor()` for render-and-scrub — it centers PLANNED-size text on FREE
  SPACE, the opposite of matching gpt's painted geometry.
- VLM vision extraction is non-deterministic — inverts figure/ground on dark backdrops,
  conflates subject-topic with register. The fed ref IMAGE rescues an imperfect text read;
  don't over-trust the descriptor alone.

---

## 12. TODO / DEBT
- No requirements.txt / pyproject.toml — deps implicit. Freeze: `uv pip freeze` →
  requirements.txt for reproducible clones.
- 12 `*_SPEC.md` files carry the stale "No git commits" line — supersede when touched.
- Repo layout is flat (~30 scripts). As the kit-of-parts reframe lands, modularize so one
  task touches one module.
- Only AIA has a config + verified answer key. Brand-generality is designed-in, unproven
  on a second brand.
