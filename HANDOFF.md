# HANDOFF — Xcela, for a fresh Hermes chat

**Written:** 2026-06-22, end of a long session. **Purpose:** let a new Hermes chat pick up
with clean context. Read this first, then `CLAUDE.md`, then `SYSTEM_MAP.md` top block.

---

## WHO + WHAT
- **User:** Alec, product/design founder, non-technical but systems-literate. Explain plainly.
  Standing rules: hold positions under pushback; verify subagent/AI self-reports before
  relaying; give a defended pick, not open option lists.
- **Project:** Xcela (formerly handyprint-design-tool). Turns a non-designer's brief + brand
  assets into handoff-quality DRAFT marketing assets (today: die-cut event signs, 手举牌).
  Drafts a human finishes, NOT final art.
- **Repo:** `/home/alecx/workspace/handyprint-design-tool/` (dir name unchanged; project
  renamed Xcela). GitHub remote: `github.com/alecxie1/xcela` (private).
- **Python 3.11 in `.venv`** — always run `.venv/bin/python <script>`. Keys load from
  `~/.hermes/.env`. Models: Anthropic opus-4-5→sonnet-4-6 (author/vision), OpenAI
  gpt-image-2 (gen). Canvas 1536x1024. Chroma key #00B140.

## HOW WE NOW WORK (the workflow shift — this session's meta-change)
- The REPO is the durable context, not the chat. Spec-driven development via **GitHub Spec
  Kit** (installed this session). Commands in Claude Code: `/speckit-specify`, `-clarify`,
  `-plan`, `-tasks`, `-implement`.
- Hermes = architect/PM (writes specs, verifies). Claude Code (in-repo, fresh context per
  task) = engineer. One spec → one task → one falsifiable test → one commit.
- `.specify/memory/constitution.md` = NON-NEGOTIABLE principles binding every spec.
- Durable context files: `CLAUDE.md` (lean root brief), `docs/ARCHITECTURE.md` (deep,
  on-demand), `.claude/rules/placement.md` (path-scoped), `SYSTEM_MAP.md` (live status).
- LESSON LEARNED: WebUI background `delegate_task` is NOT durable (3 research agents died
  silently this session). Run research IN-SESSION (web_search/web_extract), never
  background-delegate work the user is waiting on.

## THE PRODUCT IN ONE PICTURE
Pipeline: BRAND ANALYSIS → RECONCILIATION (register engine, works) → COMPOSITION+GENERATION
→ PLACEMENT (licensed font) → HUMAN GATE (approve/nudge). The intellectual core is
RECONCILIATION: brand DNA governs HARD (color/font/logo), task governs SOFT
(atmosphere/shape/register), resolved per-dimension. Subfields set DIRECTION; a reference
image sets MAGNITUDE.

## WHAT JUST SHIPPED (spec 001: kit-of-parts) — STATUS: CODE BUILT + LOGIC-VERIFIED, PIXELS NOT YET
The 6/18 run failed the eye on 3 counts (one root cause: render-and-scrub + dial=extend was
a "one template, N texts" machine — oversized text, scrub damaged graphics, signs identical
behind different text). Spec 001 reframes to "kit of parts + bespoke per-message
composition": the kit holds human-authored VOCABULARIES (palette, border, font, accent,
icon, layout); the tool DETERMINISTICALLY selects per message; honest-nulls (asks the human)
when no confident match. Reference = a style SYSTEM to internalize, NOT a panel to clone.

Alec's 4 clarify decisions (now in spec.md, all consistent — select-then-ask):
1. Icon: tool proposes from human-authored vocab, human approves at taste gate.
2. Kit conflict: per-dimension split (answer key wins hard locks, reference wins soft).
3. No icon match: honest-null + needs_review (never auto-substitute).
4. More messages than layouts: pick distinct archetypes; reuse+flag when exhausted; tool
   does NOT auto-jitter (slight variation is the human finishing layer).

New code (all committed on master, 6 commits 3a2c917..0af581e + docs 742e4f2):
- `kits/aia.json` + `kits/README.md` — the authored AIA kit vocabulary (COMMITTED brand
  data; unlike gitignored brands/ fonts).
- `harness/kit.py` — kit loader/validator + derive kit_profile (reuses register engine).
- `harness/compose_select.py` — deterministic per-message icon+layout selection.
- `harness/scene_author.py` — US3 kit reserve-box mode (paint icon, reserve text zone).
- `harness/composite_text.py` — US2 fit-to-zone type clamp (fixes oversized text).
- `harness/conductor.py` — kit route wired in.
- 5 new test files: test_kit / test_compose_select / test_fit_to_zone /
  test_kit_reserve_box (+ updated test_conductor, test_render_and_scrub).

VERIFICATION DONE (Hermes ran the tests, not just relayed the agent's word):
- All 6 test files PASS (28 checks). They are FALSIFIABLE (assert geometric inequalities,
  real icon values, honest-null behavior) — not token-presence theater. Confirmed by reading
  the test source.
- NOT YET DONE: the PAID run + Alec's EYE. Per constitution §II, green tests prove STRUCTURE,
  never pixels. The kit-of-parts signs have NOT been generated or eyeballed yet. The agent's
  commit msg says frame is "BUILT" — that means code+logic, NOT validated output. Do not
  claim the 3 failures are fixed until Alec eyeballs a real run.
- THE VALIDATION COMMAND (paid, ~2 signs):
  `.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json`
  then judge `output/run_*/sign_*/final.png` by eye vs `desiredresultaia.jpg`.
  NOTE: conductor may need a flag/inputs tweak to take the new kit route — check
  `specs/001-kit-of-parts-composition/quickstart.md` for the exact invocation.

## NEXT FOCUS (Alec's stated priority): A FRONTEND TO VISUALIZE + DEMO
Alec wants to build a frontend to visualize the pipeline and have a demo. NOT yet specced.
Open questions for the next chat to settle WITH Alec before any build:
- Demo for WHOM? (himself / Handyprint stakeholders / the Hanzi Li collaboration pitch?)
- Visualize WHAT? (the final signs gallery? the pipeline stages/reconciliation? the
  approve-nudge loop interactive?)
- STANDALONE-vs-HOST rule (Alec's standing worry): the core must run AGENT-FREE (one
  command, no Hermes) BEFORE a web host wraps it. A host over a Hermes-dependent core is
  hollow. Confirm the conductor runs clean standalone first.
- Likely the right move: spec 002 via Spec Kit (`/speckit-specify` a frontend), same
  workflow. Keep it a thin visualization over the EXISTING agent-free conductor outputs.
- Watch Alec's DEADLINE/DEMO REFLEX: an upcoming call triggers "build something to show" →
  premature deliverable. The honest artifact (working pipeline + findings) usually lands
  better with a technical peer than rushed plumbing.

## IMMEDIATE TODO AT START OF NEXT CHAT
1. Alec is about to push 10 commits to GitHub manually (master ahead of origin/master by 10).
   Confirm `git status` shows synced if he says he pushed.
2. If continuing spec 001: run the PAID validation + get Alec's eye on the signs. That is the
   real "is it fixed" gate, still outstanding.
3. If starting the frontend: settle the 4 open questions above with Alec first, then
   `/speckit-specify`. Do not start coding before the demo's audience + purpose are clear.
