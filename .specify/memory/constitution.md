# Xcela Constitution
<!-- The principles that bind EVERY spec, plan, and task in this project. A spec that
violates the constitution is wrong, not the constitution. Hand-crafted from hard-won
lessons; do not auto-generate or dilute. -->

**Version:** 1.0.0 | **Ratified:** 2026-06-22 | **Project:** Xcela (Handyprint Brand Design Tool)

## Purpose
Get a non-designer from a messy brief + brand assets to a handoff-quality DRAFT marketing
asset. We produce **drafts a human finishes, NOT final art.** Every feature serves that
sentence or it does not belong.

## Core Principles

### I. Agent-free, NOT human-free (NON-NEGOTIABLE)
The dependency we kill is the AI stagehand: an agent silently gluing steps together and
judging invisibly. That makes output unshippable and unreproducible. The human designer
STAYS in the loop by design, at INPUT gates (brief, context, reference) and TASTE gates
(approve, nudge). No feature may be designed toward "one command, walk away." Automate the
glue and the drudgery; never automate the essential inputs or the taste.

### II. Ground truth is the user's eye, not a model score (NON-NEGOTIABLE)
Vision models over-score and rubber-stamp. No feature may treat a VLM's self-graded PASS as
proof of correctness. Verify artifacts on disk. Pixel quality (fidelity, scrub cleanliness,
placement, fit) is validated ONLY by the human eye on a real output file. A green automated
test proves STRUCTURE, never beauty.

### III. Falsifiable tests only (NON-NEGOTIABLE)
Every test must assert a VALUE the wrong implementation cannot satisfy, never mere
token-presence. (`"stroke" in prompt` once passed a charcoal stroke for a white-stroke
requirement: that is a no-op gate and is forbidden.) Before writing a test, name the
property a naive/wrong build would fail, and assert that property.

### IV. Generalize, do not hand-tune
Before any change ask: does this make the TOOL better (generalizes across brands/tasks) or
just this ONE image better (task-specific taste)? Generalizing improvements get built.
Task-specific taste is a human nudge or a canvas touch-up and must NOT be baked into the
tool. Never tune the system to pass one specific image.

### V. Honest nulls, never invented results
When a step cannot do its job, it emits null plus a note and falls back explicitly; it
never invents geometry, fabricates output, or guesses silently. Every fallback is recorded
in the run manifest so the run is auditable. Reporting a blocker honestly beats a
plausible-looking fake.

### VI. Reconciliation is the core, governed per-dimension
Brand DNA and task needs diverge. Brand governs HARD where it must (primary color, licensed
fonts, logo); task governs SOFT where it must (atmosphere, shape, register). The clash is
resolved per-dimension (anchors_held vs locks_flexed), with subfields setting DIRECTION and
any reference setting MAGNITUDE. Features must respect this split, not collapse it.

### VII. The repo is the durable context
The project lives in the repo (CLAUDE.md, SYSTEM_MAP.md, specs, tests, git history), not in
any chat. One spec → one task → one module → one falsifiable test → one commit, each small
enough to fit a fresh context. Keep CLAUDE.md and SYSTEM_MAP current in the SAME commit that
makes them stale.

## Cost discipline
Image generation (gpt-image-2) is the expensive, slow step. Never place a paid generation
inside an automated test. Build and verify on the FREE structural surfaces (`--dry-run`,
`--explain`, the self-tests) first; run the one paid pipeline command only when structure
is green and a human is ready to judge the pixels.

## Output rule
Any text written FOR THE USER (docs, messages, deliverables) uses NO em-dashes. Use commas,
colons, parentheses, or restructure.

## Governance
This constitution supersedes ad-hoc instructions, including the stale "No git commits" line
in older `*_SPEC.md` files. A spec or plan that conflicts with a NON-NEGOTIABLE principle is
rejected, not negotiated. Amendments bump the version and are recorded here with a date and
a one-line rationale.
