# Quickstart: validating Faithful Brief Intake + Review

Prove the feature works end to end. Free STRUCTURAL surfaces first (no spend), then the one PAID
run is the HUMAN's (v1 is plumbing; the human runs the pipeline and renders the verdict). A green
self-test proves structure, never beauty (constitution §II).

## Prerequisites

- Python 3.11 env at `.venv` (run everything as `.venv/bin/python ...`).
- API keys in `~/.hermes/.env` only for the human's paid run; NOT needed for dry-run/self-tests.
- Brand data present: `answer_keys/aia.json`, `kits/aia.json`, `brands/aia/...` (fonts + logo).

## Step 1 — Size resolution (free)

```
.venv/bin/python test_format_size.py
```
Expect: every resolved size has both edges multiples of 16, max edge ≤ 3840, pixels in
[655_360, 8_294_400], and `aspect_resolved` ≈ the requested aspect. With the default target area,
`60x40cm` (3:2) → `1536x1024`; `40x60cm` → `1024x1536`; `50x50cm` → ~`1248x1248`; a >3:1 banner →
clamped to 3:1 + `needs_review`; `garbage` → a default valid size + a non-null note (honest null).

## Step 2 — Faithful intake (free)

```
.venv/bin/python test_faithful_intake.py
```
Expect: a scripted brief (all fields incl. `format_size`, `mandatory_elements` with `分别画叉`,
6 signs) drives `ask_questions` and the emitted inputs contain EVERY field verbatim, with 6 signs
(no collapsing, no rephrasing, no drop).

## Step 3 — The dropped fields reach generation (free, no model calls)

```
.venv/bin/python test_brief_wiring.py
```
Expect: a dry-run of a brief containing `分别画叉` + `60x40cm` yields a plan/manifest recording both;
the resolved orientation is landscape; the kit `scene_author --explain` (or the assembled prompt)
contains `分别画叉`. The current build drops both; this is the property asserted.

## Step 4 — Standalone proof + review digest (free)

```
.venv/bin/python test_conductor.py     # incl. standalone: conductor runs from a pre-written
                                       # inputs JSON with the new fields, NO form (SC-004)
.venv/bin/python test_review.py        # digest over a synthetic run dir
```
Expect: the conductor self-test stays green AND the standalone check passes; the review digest lists
each sign's image + icon + archetype + text_zone + needs_review.

## Step 5 — Author the real AIA brief, then run it (human)

```
.venv/bin/python harness/conductor.py --brand aia          # the extended intake form
# ... fill all 6 signs, 分别画叉, 设计两种样式 (verbatim), 60x40cm, the reference, vibe, etc.
```
This emits `inputs.json` and runs the pipeline (the one PAID step). Then:

```
.venv/bin/python harness/review.py --run output/run_aia_<ts>
```
Open each `final.png` and judge by eye (constitution §II). Confirm SC-001..005:
- SC-001: every item you entered (6 signs, 分别画叉, two styles, 60x40cm) is in the emitted inputs.
- SC-002: `mandatory_elements` + `format_size` are in the manifest AND the generation prompt/spec.
- SC-003: you review the multi-sign output in the digest and render a verdict (the clean test runs).
- SC-004: the pipeline ran from one CLI command (the form just wrote the inputs).
- SC-005: compliance manifest present, honest nulls + needs_review surfaced, gates intact, no em-dashes.

## References

- Data shapes: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Decisions + reuse map: [research.md](./research.md)
