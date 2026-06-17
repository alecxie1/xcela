# Handyprint Brand Design Tool — Claude Code orientation

**Read `SYSTEM_MAP.md` first.** It is the single source of truth for what this project is,
what works vs what doesn't, and the user journeys. Everything below is a quick index.

## What this is (one line)
Get a non-designer from a messy brief + brand assets to a **handoff-quality DRAFT** marketing
asset. It produces **drafts a human finishes, NOT final art.**

## Core principles (do not violate)
- **Agent-free does NOT mean human-free.** We are removing the *AI-in-the-loop* (an agent
  silently gluing steps together and judging invisibly). The *human designer* stays in the loop
  BY DESIGN, at input gates (brief/context/reference) and taste gates (approve/nudge). Never
  design toward "one command does everything / no human needed."
- **Ground truth = the user's eye**, not VLM scores (VLMs over-score; do not trust a model's
  self-graded PASS — verify artifacts on disk).
- **Falsifiable tests only.** Self-tests must check correctness, not token-presence. Do not
  hand-tune to pass one specific image; build what GENERALIZES to all brands/tasks.
- **The tool makes drafts a human finishes** — do not tunnel toward "final art."
- Any text written FOR THE USER (docs, messages) uses NO em-dashes (his standing rule).

## Layout
- `harness/` — the thin one-command spine (`run_harness.py`) + scene_author, generate,
  composite_text, closed_loop_composite, measure_canvas, approve, gates
- `register/` — register engine (calibrate_from_reference / derive_register / blind_score) +
  reference_style_to_prompt.py (BUILT but not yet wired into the generate path)
- `answer_keys/` — extracted + (partly human-verified) brand DNA, one JSON per brand
- `config/` — per-brand run config (only `aia.yaml` exists today)
- `docs/`, `*_SPEC.md` — the WHY behind each layer + build contracts
- `brands/`, `output/` — **GITIGNORED** (licensed fonts + client IP + generated PNGs). Local
  only; a fresh clone will not have them.

## Run
- Thin spine (agent-free, AIA only): `python harness/run_harness.py aia`
- Activate venv first: `source .venv/bin/activate`
- The full pipeline that produced the showcase AIA signs is currently chained by Hermes by hand
  (see SYSTEM_MAP "Journey 2"). Turning that into one conductor script is the current goal.

## Current goal (2026-06-17)
Build ONE conductor ("orchestrator") for the AIA flat-graphic sign task: run the proven
primitives in order and STOP at the human gates (input + approve). The only genuinely NEW code
needed is an OCR text-locator (replaces Hermes eyeballing the generated PNG to find the text
area) plus wiring `register/reference_style_to_prompt.py` into the generate path. Everything
else already exists and is individually proven — this is mostly sequencing, not new capability.
