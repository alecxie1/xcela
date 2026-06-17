# BUILD SPEC: harness/approve.py — Tier-3 Approval Loop (Gate 2)

## Context (read these first)
- `brief_schema_v2.json` — the 3-tier architecture. You are building the
  `_human_loop` described in tier_3_scene_construction and step_3_approve.
- `harness/scene_author.py` — the proven engine. REUSE its functions by import
  (load_brand, author_tier3, assemble_final_prompt). Do not duplicate logic.
- `output/scene_author_run2_mustinclude/tier3_scene.json` — example of a real
  tier-3 scene object (the data you'll be summarizing and editing).

## What this is
The product's core interaction: a non-designer marketing manager cannot READ a
tier-3 scene JSON, but they CAN react to a plain-language description of it.
The loop: author scene → show plain-language summary → human approves or
nudges in plain language → ONLY the touched fields get re-authored → repeat
until "yes" → generate the image.

## Build: `harness/approve.py`

CLI:
  .venv/bin/python harness/approve.py --brand taichi --out output/approve_run1 \
      [--must-include "..."] [--no-generate] [--script responses.txt]

### Flow
1. **Author**: call scene_author.author_tier3() (with optional must_include).
   Save tier3_scene.json to out dir (versioned: tier3_v1.json, tier3_v2.json...).
2. **Summarize** (new function `summarize_scene(tier3) -> str`): one Anthropic
   call (model claude-sonnet-4-6, cheap+fast) that turns the scene JSON into a
   SHORT friendly paragraph a non-designer instantly understands. Style:
   "Here's the plan: a fresh teal poster fading to cream. Your burger sits on
   a walnut wood stand at center-right, tomatoes and basil scattered around...
   Your headline 限时上新 goes top-left in red." Rules: no hex codes, no px
   coordinates, no jargon (say "soft warm light" not "f/2.8 key light 10
   o'clock"). End with: anything you'd like to change?
3. **Prompt the human** (stdin input()): they type either an approval
   ("yes"/"y"/"looks good"/"ok") or a plain-language nudge ("make the
   background warmer", "no basket", "bigger headline").
   - Approval detection: simple lowercase match on a small approval set PLUS
     if ambiguous, treat as nudge (safer to over-edit than to generate wrong).
4. **Apply nudge** (new function `apply_nudge(tier3, nudge) -> (tier3', changed)`):
   one Anthropic call (claude-opus-4-5): give it the current tier-3 JSON + the
   nudge text. Instructions: edit ONLY the fields the nudge touches, leave
   every other field byte-identical, return STRICT JSON {changed_fields:
   [...], scene: {full updated tier-3}}. Validate: parse JSON, verify
   non-changed fields really are identical (deep compare); if the model
   mutated untouched fields, restore them from the previous version and note
   it. Save as tier3_v2.json etc.
5. **Loop**: re-summarize ONLY as a short diff line ("Updated: background is
   now warmer cream-beige. Everything else unchanged.") + repeat step 3.
   Max 5 nudge rounds (then force-ask approve/abort).
6. **Generate**: on approval, assemble_final_prompt() + generate via the same
   gpt-image-2 path scene_author.py uses (logo-only reference). Skip entirely
   if --no-generate.
7. **Audit trail**: write session.json to out dir: every version, every nudge
   string, every changed_fields list, timestamps. This is experiment data —
   we measure how many nudges users need.

### --script mode (for your own testing)
--script <file>: read newline-separated canned human responses instead of
stdin (last line should be "yes"). Lets you test the loop non-interactively.

## Definition of done (DO ALL OF THIS)
1. `approve.py` exists, imports cleanly, --help works.
2. TEST RUN (no image cost): run with --no-generate and a script file with
   exactly these 3 responses:
     make the background a warmer cream tone, less green
     remove the peppercorns
     yes
   Verify: v1→v2 changed ONLY background-related fields (palette_resolved
   background entries / background), v2→v3 removed only the peppercorn prop,
   nothing else drifted (assert deep-equality of untouched fields).
   Print the summary text and the diff lines in your final report.
3. If validation catches the model mutating untouched fields, your restore
   logic must handle it — show evidence it works (or that it wasn't needed).
4. Keep it ~200 lines. No frameworks, no classes unless they earn it.
5. Do not modify scene_author.py except, if strictly necessary, extracting an
   import-safe helper (no behavior change). Do not git commit.

## Env
- venv: .venv (python 3.11) — use .venv/bin/python
- Keys in ~/.hermes/.env (ANTHROPIC_API_KEY, OPENAI_API_KEY), load via dotenv
  exactly like scene_author.py does.
