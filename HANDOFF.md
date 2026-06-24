# HANDOFF — Xcela, for a fresh Hermes chat

**Written:** 2026-06-24, end of a long session. **Purpose:** let a new Hermes chat pick up with
clean context (avoiding context rot). Read this first, then `CLAUDE.md`, then `SYSTEM_MAP.md` top
block (the "REGROUP 2026-06-24 PM" block is the live state).

---

## WHO + WHAT
- **User:** Alec, product/design founder, non-technical but systems-literate. Explain plainly.
  Standing rules: hold positions under pushback; VERIFY subagent/AI self-reports against disk before
  relaying; give a defended pick, not open option lists; no em-dashes in anything written for him.
  Watch his DEADLINE/DEMO REFLEX ("build something to show") and name it when it appears.
- **Project:** Xcela (dir still `handyprint-design-tool`). Turns a non-designer's brief + brand
  assets into handoff-quality DRAFT marketing assets (today: die-cut event signs, 手举牌).
- **Repo:** `/home/alecx/workspace/handyprint-design-tool/`. GitHub remote `github.com/alecxie1/xcela`
  (private; brands/ output/ .env gitignored). **Alec pushes manually.**
- **Python 3.11 in `.venv`** — always `.venv/bin/python`. Keys in `~/.hermes/.env`. Models: Anthropic
  opus-4-5/sonnet-4-6 (author/vision), OpenAI gpt-image-2 (gen). Chroma #00B140 (legacy route only).
- **Workflow:** Hermes = architect/PM (writes specs, VERIFIES on disk). Claude Code (in-repo, fresh
  context per task) = engineer, driven via `claude -p` from the claude-code skill. Spec-driven (Spec
  Kit: `/speckit-specify` etc.). One spec → one task → one falsifiable test → one commit.

## THE BIG ARC OF THIS SESSION (what changed, and why it matters)
This session ran the FIRST un-confounded experiments and made a PROJECT-DEFINING pivot. The headline:
**the deterministic COMPOSITION layer (kit of parts) was CUT — it competed with gpt-image-2 and lost.**

1. **The control test (decisive).** Alec ran raw gpt-image-2 himself on Lily's real 6-sign AIA
   anti-fraud brief + the reference image — it produced 6 varied, on-brief signs in one shot, beating
   our pipeline by his eye. Root-cause (code + git): our intake was a LOSSY hand-translation AND the
   conductor never read `mandatory_elements` / `format_size`. So every prior "pipeline test" was
   confounded — the brains were NEVER tested on a faithful brief.
2. **Spec 002 (faithful intake) — BUILT + verified.** Intake now captures every brief field verbatim;
   `format_size` resolves to a valid gpt-image-2 pixel size; `mandatory_elements` (incl. per-sign,
   e.g. 分别画叉 on s5/s6 only) reach generation. This made a CLEAN test possible.
3. **The faithful kit run (the proof).** Ran the real 6-sign brief through the KIT route:
   2 good / 3 near-duplicates / 1 blank honest-null. Alec's eye: the composition layer makes output
   WORSE on a real brief — it constrains gpt down to its threadbare vocabulary (1 protect layout,
   1 resist layout, sparse icon map). The bitter lesson, on our own task.
4. **The keep/cut/defer decision (SYSTEM_MAP 6/24 PM regroup):**
   - **CUT** (the layer that lost): compose_select, kit layout archetypes, reserve-box zones,
     fit-to-zone clamp. (Kit CODE left in repo behind opt-in, NOT deleted.)
   - **KEEP**: faithful intake (002), register/DIAL (it sets task-vs-brand magnitude; this task reads
     "task-governs / expressive departure", a corporate asset would read the other way), answer_key
     brand locks (hex/font/logo), analyze_brand_v3 (Alec has confidence in it; human verifies the
     answer_key), logo→gpt, human approve/nudge gate, manifest.
   - **DEFER (built, switched OFF, NOT deleted)**: the licensed-font MOAT. Research verdict: gpt-image
     soft-mask CANNOT pixel-lock a zone or render licensed type, so legacy measure→scrub and
     reserve-band are dead ends; the real moat is FURNITURE + DETERMINISTIC TYPESET (gpt paints
     text-free furniture; we own type via SVG/CSS stroke+shadow, rasterize, composite). Separability
     check on the finished campaign: 5/6 signs are flat-band (easy), 1 integrated (hard → honest-null).
     UNPROVEN — needs a SPIKE before any spec.
5. **Spec 003 (thin spine) — BUILT + verified.** The new default-intended route: intake → dial →
   `assemble_thin_prompt` (ONE prompt from the brief) → gpt-image-2 composes the WHOLE sign → STOP at
   raw `generated.png`. No kit, no compose, no measure, no composite. Opt-in via `--thin`
   (back-compat: AIA still defaults to kit until a later spec flips it).
6. **The thin paid run (VALIDATION — the win).** `output/run_aia_20260624_125701/` (route=thin):
   **6 distinct on-brief signs, ZERO dupes, ZERO blanks.** s4 (which the kit route blanked) came back
   as a full sign; s5 drew X marks on BOTH the money bag AND Bitcoin (分别画叉 understood). The
   thin-spine architecture is VALIDATED by Alec's eye. Two prompt bugs found + FIXED (commit 6295054):
   (a) brand slogan was injected as text → gpt hallucinated a tagline 健康长久好生活 onto all 6 signs
   (removed); (b) 分别画叉 was framed "render exactly" → gpt painted the literal characters (reframed
   as a DESIGN INSTRUCTION: depict/do, don't render the text). NOT yet re-run after the fix.

## CURRENT STATE (verified on disk this session)
- Branch: **`002-faithful-brief-intake`** (all 002 + 003 work lives here; NOT merged to master;
  master still at c7b154f). Alec pushes manually.
- Full self-test suite: **39/39 green across 7 files** (test_conductor, test_brief_wiring,
  test_faithful_intake, test_format_size, test_review, test_per_sign_elements, test_thin_route).
  All FALSIFIABLE (assert values, not token-presence). Hermes re-ran them, did not relay CC's word.
- Last commits: 6295054 (prompt fix) ← 3e5f086 (thin spine, Hermes-finished after CC turn-limit) ←
  4348b77 (keep/cut decision + faithful brief) ← 4da39b0 (per-sign elements) ← ...
- Key data files: `inputs_lily_aia.json` (the faithful 6-sign brief, committed),
  `output/run_aia_20260624_125701/` (the validated thin run, gitignored pixels).

## IMMEDIATE NEXT STEP: FRONTEND (Alec drives the speckit)
Alec wants a frontend to VISUALIZE + DEMO the thin spine — a LIVE RUNNER (type a brief, watch the
thin spine execute stage by stage). The thin spine now EXISTS and is validated, so it's unblocked.

**CRITICAL PROCESS NOTE: Alec will DRIVE the frontend `/speckit-specify` HIMSELF** (in Claude Code).
He explicitly wants to hold the pen on the frontend spec (it's his product-design domain). Do NOT
auto-drive it. When he pastes the generated spec.md back, Hermes switches to VERIFY mode (check it
against `.specify/memory/constitution.md` + the thin-spine reality before he plans/builds).

Frontend design constraints to honor (from this session):
- THIN over the agent-free core: the UI shells out to the EXISTING CLI
  (`conductor.py --thin`); it MUST NOT reimplement generation. Standalone core stays runnable.
- It visualizes the THIN route stages: intake(002 fields) → register/dial → assembled prompt →
  gpt-image-2 composes → raw generated.png → human gate. (NOT the cut kit layer.)
- Live-runner button calls paid gpt-image-2 (~$0.50/6-sign run) — label the cost; human triggers it.

## OUTSTANDING (not blocking the frontend, but track)
1. **Re-run the thin route after the prompt fix** (commit 6295054) to confirm the tagline is gone and
   分别画叉 renders as actual X marks (not literal text). Paid (~$0.50), needs Alec's eye. Command:
   `.venv/bin/python harness/conductor.py --brand aia --inputs inputs_lily_aia.json --no-approve --thin`
2. **The MOAT spike** (furniture + deterministic typeset) — the deferred licensed-font work. Needs a
   spike (does gpt leave clean empty furniture? does SVG/CSS typeset look native?) before a spec.
3. Throwaway scripts still untracked: `baseline_gptimage_only.py`, `ocr_*.py`, `specs/_inbox/`.
   Evidence of the control experiment; commit or prune at will.

## STANDING LESSONS (re-confirmed this session)
- VLM vision OVER-SCORES (called every sign "production-ready"); mechanical OCR (rapidocr) is the
  trustworthy reader; Alec's native-reader eye is ground truth. Never relay a VLM PASS as proof.
- Claude Code `claude -p` can hit `error_max_turns` mid-build (turn-burn). CHECK THE FILESYSTEM
  before re-running — the work is usually on disk; finish the last mile yourself (cheaper than a
  re-run). This session: CC built the thin spine but ran out before tests+commit; Hermes finished it.
- A green self-test is a CLAIM. Re-run it yourself, read the test source for falsifiability, and trace
  the one load-bearing link the test skips (e.g. does the resolved size reach the actual generate call).
