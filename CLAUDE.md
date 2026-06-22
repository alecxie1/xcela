# CLAUDE.md — Xcela (Handyprint Brand Design Tool)

> **The engineer's brief, loaded into every session. Keep it LEAN.** Frontier models
> follow ~100-150 instructions before quality degrades uniformly, so this root file
> stays short and POINTS to detail that loads on demand. When this file and the code
> disagree, the CODE wins, and you fix this file in the same commit.
>
> **Deeper context, read on demand (do NOT inline it here):**
> - `SYSTEM_MAP.md` — project STATUS: what works, the live regroup notes, the roadmap. **Read its top block first.**
> - `docs/ARCHITECTURE.md` — full module map, pipeline, glossary, toolchain, pitfalls.
> - `.claude/rules/*.md` — path-scoped rules that auto-load only when you touch matching files.

## What this is (one line)
Get a non-designer from a messy brief + brand assets to a **handoff-quality DRAFT**
marketing asset (today: die-cut event signs, 手举牌). **Drafts a human finishes, NOT final art.**

## Core principles (do not violate)
1. **Agent-free ≠ human-free.** Kill the AI stagehand (silent glue + invisible judgment).
   Keep the human at the INPUT gates (brief/reference) and TASTE gates (approve/nudge).
   Never design toward "one command, walk away."
2. **Ground truth = the user's eye, not VLM scores.** Vision models over-score. Verify
   artifacts on disk; never trust a model's self-graded PASS.
3. **Falsifiable tests only.** Assert VALUES the wrong implementation cannot satisfy, not
   token-presence (`"stroke" in prompt` is a no-op gate). Build what GENERALIZES, never
   hand-tune to one image.
4. **Generalizes vs task-taste.** Before any fix ask: does this help the TOOL (all
   brands/tasks) or just this IMAGE? Task-taste is a human nudge, do NOT bake it in.
5. **Honest nulls.** When a step can't do its job, emit null + a note and fall back
   explicitly. Never invent geometry or fabricate a result. Record every fallback.
6. **No em-dashes in any text written FOR THE USER.** Use commas, colons, parentheses.

## The intellectual core (or nothing downstream makes sense)
Brand DNA and task needs DIVERGE (AIA = corporate red/sharp/logo/rectangular; an event
sign wants playful/rounded/no-logo/die-cut). **Reconciliation is the whole game:** brand
governs HARD (color, fonts, logo), task governs SOFT (atmosphere, shape, register),
resolved per-dimension into a `register_profile` (anchors_held vs locks_flexed).
**Direction vs magnitude:** subfields set DIRECTION (which register lane); a reference
image sets MAGNITUDE (how far, via blind vision score). See `docs/ARCHITECTURE.md` §2.

## Two job types (drives most branches in the code)
- **Reference job** (a reference image is supplied): analyzer → aligned prompt + fed crop;
  tier-3 SKIPPED; chroma OFF; deliverable = final.png.
- **No-reference job**: Claude authors a tier-3 scene; chroma ON (#00B140); deliverable =
  cutout.png. Full table in `docs/ARCHITECTURE.md` §3.

## Where things live (one-liner each; full map in docs/ARCHITECTURE.md §5)
- `harness/conductor.py` — the human-gate ORCHESTRATOR (top of the tree, stdlib-only).
- `harness/scene_author.py` — the single-sign engine (tier-3 author OR aligned-prompt).
- `harness/closed_loop_composite.py` — PLACEMENT (place_measured + legacy closed_loop).
- `harness/measure_canvas.py` — the SENSOR (OCR + container geometry).
- `harness/composite_text.py` — licensed-font COMPOSITOR + compliance manifest.
- `register/` — reconciliation engine (derive_register = direction, calibrate = magnitude,
  reference_style_to_prompt = the analyzer + dial).
- `answer_keys/<brand>.json` — brand DNA. `config/<brand>.yaml` — thin-spine config.
- `brands/ output/ .env` — GITIGNORED (licensed fonts, client IP, secrets, big PNGs).

## Toolchain
- Python 3.11 in `.venv`. Always run as `.venv/bin/python <script>`.
- Install a dep: `uv pip install --python .venv/bin/python <pkg>`.
- API keys load from `~/.hermes/.env` via dotenv. Never hardcode or print keys.
- Models: Anthropic `claude-opus-4-5` → `claude-sonnet-4-6` (authoring/vision);
  OpenAI `gpt-image-2` (generation). Canvas 1536×1024. Chroma key #00B140.

## How to test (the FREE structural surfaces — use BEFORE spending)
```
.venv/bin/python test_conductor.py            # conductor self-test (dry-run, no paid calls)
.venv/bin/python test_render_and_scrub.py     # axis A+B self-test (--explain, no paid calls)
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/dry --dry-run --no-approve      # plan only, NO model calls
```
The one PAID run: `.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json`
→ judge `output/run_*/sign_*/final.png` with the HUMAN EYE. **Never put paid image
generation inside a self-test.** A green self-test ≠ correct output; only the eye validates pixels.

## Dev workflow (spec-driven — supersedes the old "no commits" line in *_SPEC.md files)
- The REPO is the durable context (this file + SYSTEM_MAP + specs + tests + git history).
  Hold the project in the repo, not the conversation.
- **One spec → one task → one module → one falsifiable test → one commit.** Small enough
  to fit a fresh context. Spec Kit (`/specify`, `/plan`, `/tasks`, `/implement`) drives this.
- Commit per task. `origin` = github.com/alecxie1/xcela (private; IP/secrets gitignored).
- Keep this file + SYSTEM_MAP current in the SAME commit that makes them stale. A stale
  brief actively misleads the next session.

## Current frame + known failure (live state in SYSTEM_MAP §6/18 regroup)
The 6/18 reference run passes self-tests + font compliance but FAILS the eye: (a) text
oversized/overflowing, (b) scrub damages graphics, (c) the two signs are identical behind
different text. ONE root cause: render-and-scrub + dial=`extend` is a "ONE TEMPLATE, N
TEXTS" machine. Fixing measure/scrub does NOT bridge this — it's the wrong frame.
**Target frame (AIA, agreed):** "kit of parts + bespoke per-message composition." The
reference is a STYLE SYSTEM to internalize, not a panel to clone. **Not yet built — no
code until the spec is written and aligned.** Details: `docs/ARCHITECTURE.md` §9.

## Top pitfalls (full list in docs/ARCHITECTURE.md §11)
- `place_measured` inherits gpt's text size — no fit-to-margin clamp yet (failure (a)).
- `measure`'s legacy HSV path is fragile; the chroma path is the proven one.
- Don't reuse `reanchor()` for render-and-scrub (it centers planned text on free space —
  the opposite of matching gpt's painted geometry).
- VLM vision extraction is non-deterministic (figure/ground inversion, topic↔register).

<!-- SPECKIT START -->
## Spec Kit (active workflow)
Specs live in `specs/`. Slash commands: `/speckit-specify` (write the spec), `/speckit-plan`
(technical plan), `/speckit-tasks` (break into testable tasks), `/speckit-implement` (build
one task at a time). When working a feature, READ ITS SPEC + PLAN in `specs/<feature>/` first.
`.specify/memory/constitution.md` holds project principles that bind every spec.
<!-- SPECKIT END -->
