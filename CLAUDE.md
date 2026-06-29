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
- `harness/conductor.py` — the human-gate ORCHESTRATOR (top of the tree, stdlib-only; routes
  kit brands through the kit path, kit-less brands through the legacy render-and-scrub path).
- `harness/scene_author.py` — the single-sign engine (tier-3 author OR aligned-prompt OR
  kit reserve-box mode via `--kit-profile` + `--composition`).
- `harness/kit.py` — KIT loader/validator (stdlib) + derived `kit_profile` (answer key wins).
- `harness/compose_select.py` — deterministic meaning→icon + collision-avoiding archetype pick.
- `harness/format_size.py` — (002, stdlib) brief `format_size` → valid gpt-image-2 pixel size,
  aspect-preserving nearest a configurable target area (default ~1.57 MP). Profile-agnostic.
- `harness/prompt_elements.py` — (002, stdlib) verbatim mandatory/forbidden → prompt clause.
- `harness/review.py` — (002, stdlib) read-only self-service review digest over a run's artifacts.
- `harness/closed_loop_composite.py` — PLACEMENT (place_measured + legacy closed_loop).
- `harness/measure_canvas.py` — the SENSOR (OCR + container geometry).
- `harness/composite_text.py` — licensed-font COMPOSITOR + compliance manifest + fit-to-zone clamp.
- `register/` — reconciliation engine (derive_register = direction, calibrate = magnitude,
  reference_style_to_prompt = the analyzer + dial).
- `extract_colors.py` / `extract_text_layer.py` — (proven, model-free) deterministic brand extractors
  (OCR+pixel reconcile / text-layer fonts). REUSED by 005; `render_page` is 1-INDEXED.
- `brand_intake/` — (005, stdlib) brand-onboarding FRONT-half over those extractors: `page_finder`
  (suggest 1-indexed spec pages), `extract` (reuse wrappers), `assemble_key` + `validate_key` (lean
  key + fail-loud), `intake.py` (CLI: PDF -> verify gate -> answer_keys/<brand>.json). NOT the v3 scaffold.
- `frontend/` — (004 + 006, stdlib) THIN local web app over the CLI. 004 live-runner: `inputs_writer`
  (form -> 002 JSON), `run_view` (run dir -> progressive stages), `runner` (build/launch `conductor
  --thin`), `server.py` + `index.html`. 006 onboarding gate: `onboard.py` (3-step wizard over a
  transient draft, wraps the 005 brand_intake modules), `multipart.py` (stdlib upload), `onboard.html`
  + the `/onboard/*` routes. Shells out + reads artifacts; never reimplements generation/extraction.
- `brand_intake/persist.py` — (006, shared) the one write home (key_exists/place_logo/write_key) the
  005 CLI and the 006 web gate both call.
- `answer_keys/<brand>.json` — brand DNA. `config/<brand>.yaml` — thin-spine config.
  `kits/<brand>.json` — human-authored Kit of Parts (icon + layout vocabularies; committed DATA).
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

## Current frame (live state in SYSTEM_MAP §6/23 regroup)
The "kit of parts + bespoke per-message composition" reframe (feature
`001-kit-of-parts-composition`) is BUILT through US3 and passes its falsifiable structural
self-tests. It replaces the 6/18 "ONE TEMPLATE, N TEXTS" machine FOR KIT BRANDS: each sign
gets a meaning-driven icon + a distinct layout archetype, the reserved text zone is disjoint
from the icon zone (no scrub), and type is fit-clamped to its zone. The reference is
internalized into the kit, not cloned. Kit-less brands keep the legacy render-and-scrub path.
**Still pending: T020, the ONE paid run judged by the human eye** (structure green ≠ pixels
correct). Spec/plan/tasks: `specs/001-kit-of-parts-composition/`. Details: `docs/ARCHITECTURE.md` §9.

## Top pitfalls (full list in docs/ARCHITECTURE.md §11)
- Legacy `place_measured` inherits gpt's text size (failure (a)); the KIT path instead uses
  `composite_text.fit_text_to_zone` (type sized DOWN to the reserved zone, honest-null if it
  cannot fit). Use the kit path for kit brands; the clamp is the generalizing fix.
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

**Active feature:** `006-web-onboarding-gate` — BUILT (US1-US3) + structurally green (18 checks:
multipart 3, onboard 9, verify_reuse 6; all prior 001-005 suites green). The designer-facing WEB gate:
a 3-step browser wizard (upload PDF -> confirm suggested pages -> extract+verify -> validate-loud +
save) that wraps the proven 005 `brand_intake/` PURE modules in the 004 local-web pattern (NOT
`intake.main()`) and writes a lean `answer_keys/<brand>.json` the thin route + the 004 live-runner
consume unchanged (the `/brands` dropdown lists `answer_keys/*.json`, so onboard->generate is free,
verified end-to-end over HTTP). `frontend/onboard.py` (wizard over a TRANSIENT draft, discard on
save/abandon), `frontend/multipart.py` (stdlib upload, no `cgi`), `brand_intake/persist.py` (shared
write home, CLI + web). Fail-loud on no primary / logo / unacknowledged flag / existing id; zero-color
blocks; styles honest-null; standalone CLI preserved. Pending: the human browser smoke + paid sign
(T017). Run: `.venv/bin/python frontend/server.py` then open `/onboard`.
Prior built: 001-005 (005 fully verified, T015 cold-brand chajiuxingqiu onboarded end to end).

Prior built features: `001-kit-of-parts-composition` (US3, paid eye gate pending),
`002-faithful-brief-intake` (faithful intake + wired dropped fields + review), `003-thin-spine`
(the prompt-compose thin route `conductor --thin`, the engine 004 wraps), `004-frontend-live-runner`
(thin local web live-runner, operator paid run T016 pending).
<!-- SPECKIT END -->
