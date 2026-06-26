# PENDING SPEC-KIT INTAKE — Feature 002: Faithful self-service brief intake + review

> **What this file is:** the natural-language `/speckit-specify` brief for feature 002,
> authored by Hermes (architect/PM role) on 2026-06-23. It is NOT a generated spec. To turn
> it into `specs/002-*/spec.md`, run `/speckit-specify` in Claude Code with the body below as
> the description. Adjust scope first if needed (see the deferred-comparison flag).
>
> **Provenance (the session that produced it):** a control experiment showed raw gpt-image-2,
> given the client brief + the reference image, beat our pipeline's output. Root-causing it
> against the code + git revealed the pipeline never consumed a real brief: intake was a lossy
> hand-translation (6 signs became 2; 分别画叉 / 两种样式 / size dropped) AND the conductor
> contract is under-wired (it never reads `mandatory_elements` or `format_size`). So prior
> "pipeline tests" were confounded; the brains were never tested on faithful input. This
> feature fixes the intake so a clean test becomes possible. Fork chosen: A (fields as the
> spine, per Richard's "users don't know what they want") WITH B's lesson (wire the dropped
> fields; pass literal text through verbatim).

---

## Problem (why this exists)
Every pipeline test to date is confounded and cannot be trusted, for two reasons we
located in the code and git history (2026-06-23):

1. LOSSY HUMAN TRANSLATOR. Nothing in the tool parses a brief. A Hermes chat hand-wrote
   the conductor's --inputs JSON from the client brief, and silently dropped content:
   a 6-sign brief became a 2-sign inputs file; "分别画叉", "设计两种样式", and the
   physical size were all dropped. So "pipeline tests" actually tested
   [lossy hand-translation + pipeline]. That is the agent-in-the-loop dependency the
   constitution (§I) exists to kill, and it was sitting in front of the pipeline.

2. UNDER-WIRED CONTRACT. Even a perfect form-fill loses brief content: the conductor
   never reads mandatory_elements (brief_schema_v3 bucket C, where "分别画叉" lives) or
   format_size (bucket A, "60x40cm"). They have no path to generation at all. The
   X-marks the raw model rendered correctly have zero path through our pipeline.

Net: we have NEVER fed the real, complete brief to the reconciliation engine. We
therefore cannot conclude the engine's "brains" are wrong; we can only conclude the
INTAKE is broken. This feature fixes the intake so a clean, reproducible test becomes
possible.

Validated design principle (Richard, confirmed by Alec's own gpt-image-2 experiment):
non-designers do not know what to say. The single instruction that won Alec's raw test
("extend these 4 signs, keep the same visual language and DNA") maps exactly to the
EXISTING reference_relationship="template" field, an instruction the client briefer
omitted. Structured fields capture what free text misses. Fields are the spine.

## Goal (user value)
Alec authors the full, faithful brief HIMSELF through a structured intake surface, and
reviews the resulting signs HIMSELF, with NO agent acting as translator or judge. This
removes the confound and produces the first clean, reproducible run of the real pipeline
on a real complete brief.

## User stories
US1 (P1) Self-service faithful intake. The human fills the brief_schema_v3 structured
  fields directly (asset_type, format_size, usage_context, audience, vibe sliders,
  logo_treatment, brand_strictness, per-sign messages, mandatory_elements,
  forbidden_elements, occasion), drops a reference image, picks a brand. The tool emits
  the conductor inputs with ZERO human-translator loss. Falsifiable: every field entered
  appears verbatim in the generated inputs and run manifest; nothing is dropped, and
  nothing is inferred or rephrased by an agent.

US2 (P1) The previously-dropped fields reach generation. mandatory_elements (e.g.
  分别画叉) and format_size (e.g. 60x40cm) actually flow through to scene_author / the
  generation prompt and are recorded in the run manifest; format_size drives orientation
  and aspect. Falsifiable: a brief containing "分别画叉" yields a generation prompt/spec
  that contains that instruction, and a 60x40cm size is recorded and drives aspect. The
  current (wrong) build drops both; that is the property the test asserts.

US3 (P1) Self-service review. After a run, the human sees, in one place: the output sign
  images, the structured inputs the pipeline ACTUALLY received, the per-sign composition
  picks (icon, layout archetype, reserved text zone), and every needs_review flag, so the
  human judges by eye (constitution §II) and can see exactly what the pipeline got.

## Out of scope (v1)
- LLM/agent parsing of a free-text brief into fields. REJECTED on principle: it
  re-introduces the exact translator confound this feature removes (constitution §I).
  The human types the structured fields. Free-text brief content is allowed ONLY as
  verbatim passthrough into literal fields (messages, mandatory_elements), never as an
  agent-inferred mapping.
- Side-by-side raw-model vs pipeline comparison on identical inputs. Deferred to a later
  spec; valuable, but v1 is faithful intake + review first. (Flagged for Alec.)
- The eventual stakeholder/demo frontend. Different audience, later spec.
- Brand-generality: v1 targets AIA (the only brand with ground truth); generality is
  designed-in but proven later (constitution §IV).
- Implementation technology (framework, UI library): deferred to /speckit-plan.

## Hard constraints (guardrails)
- THIN OVER THE AGENT-FREE CORE (standalone-vs-host, constitution §I/§VII): the intake
  surface MUST shell out to or import the EXISTING CLI (conductor.py, scene_author.py,
  generate.py). It MUST NOT reimplement generation, placement, measurement, or judgment.
  The core MUST still run headless from one CLI command with the frontend absent, and a
  test MUST prove that standalone path is unbroken.
- AGENT-FREE, NOT HUMAN-FREE: human at the input gate (types fields, drops reference,
  picks brand) and the taste gate (reviews, approves, nudges). No silent agent glue.
- FAITHFUL PASSTHROUGH: literal text (messages, mandatory_elements) passes through
  verbatim; the tool never rephrases, reorders, or "improves" it (mirror approve.py's
  existing nudge discipline).
- REFERENCE IS FIRST-CLASS and feeds BOTH channels (visual FED to gpt-image-2 + semantic
  PARSED for register), per brief_schema_v3 reference_input. ref+prompt > ref > prompt is
  designed-in, not optional.
- BRAND ASSETS load per-brand from existing brand data (answer_keys/, kits/, brands/
  fonts+logo+VI). The human PICKS the brand; the human does not re-enter assets.
- PRESERVE ALL NON-NEGOTIABLES: licensed-font compliance manifest, honest nulls +
  needs_review, the human approve/nudge gate, no em-dashes in user-facing text,
  no paid generation inside any automated test (cost discipline).

## Success criteria (all human-eye per §II unless marked structural)
- SC-001: Alec completes the full AIA brief (all 6 signs, 分别画叉, two styles, 60x40cm)
  through the intake surface with ZERO Hermes involvement, and the generated conductor
  inputs contain every item he entered. (structural + eye)
- SC-002: mandatory_elements and format_size appear in the run manifest AND the
  generation prompt/spec. (structural, falsifiable)
- SC-003: Alec reviews the multi-sign output in the surface and renders an eye verdict
  (the clean test finally runs).
- SC-004: With the frontend absent, the pipeline still runs end-to-end from one CLI
  command. (structural, the standalone proof)
- SC-005: All NON-NEGOTIABLE guarantees still hold (font compliance, honest nulls, gates,
  no em-dashes).

## Note for /speckit-plan
Verify reuse against the ACTUAL code before proposing modules: conductor.py already loads
--inputs and validates signs[]; brief_schema_v3.json already defines every field including
the two unwired ones; scene_author/composite_text/measure already exist. The likely work
is (1) an intake surface that writes the inputs JSON the conductor already accepts, (2)
wiring mandatory_elements + format_size from inputs through build_intent/scene_author into
the prompt + manifest, (3) a review surface that reads the run_*/ artifacts already
written. Confirm before building anything new.
