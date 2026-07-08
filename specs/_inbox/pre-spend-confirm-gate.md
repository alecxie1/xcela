# Inbox brief — pre-spend confirm gate (the dimension interview, scoped to the evidence)

_Status: candidate next feature (number assigned at /speckit-specify time). Competes with
015 brand-key enrichment for the next slot; they are independent. Evaluated 2026-07-08;
verdict: the interview's core is necessary and evidence-backed, the full wizard/visual-
picker UX is over-built for today. This brief is the minimal honest form._

## The problem (the recurring failure class)

Features 011, 012, and 014 were ALL repairs of the same seam: the machine deciding where
the human had (or would have had) a statement. Each defect was discovered only AFTER a
paid misrender (e.g. `run_CJXQ_20260701_173925`, a flat marketing post rendered as a
hand-held sign), then cost a diagnosis session + a spec + a feature. The class, not the
instances, is the target.

Today the operator commits money BEFORE seeing what the tool decided: `POST /run` runs
calibrate -> derive_register -> assemble prompt -> PAID generate in one uninterruptible
background run (`frontend/server.py` `_launch_async` -> `runner.launch`). The register
profile and prompt appear in the stages UI seconds before the image, un-gated. The only
human gate (`showGate` in `index.html`) is AFTER the spend; every correction is a full
paid rerun (the nudge button). The conductor's own approve gate (step 6) is
post-generation and skipped with `--no-approve` on the web path anyway.

## Evidence the input gate still guesses (verified 2026-07-08, re-verify before speccing)

All traced, none confirmable pre-spend:
- usage_context matches no USAGE_RULES row -> `marketing` base (default guess),
  `register/derive_register.py:101-103`; the vibe promotion may then stack a second guess
  on top (legitimate per 014, but still a guess).
- Unrecognized/blank render_style -> `flat_graphic`, `harness/conductor.py:113-116`.
- Unrecognized reference_relationship -> `extend` dial, `harness/conductor.py:105`.
- Unparseable format_size -> 1536x1024 (+ `needs_review` on aspect clamp),
  `harness/format_size.py:33-60`.
- Magnitude fallback chain when calibration is absent, `register/derive_register.py:147-167`.
- `warmth` is never collected by the form yet always defaults to 5,
  `frontend/inputs_writer.py:67` (either collect it or retire it in this feature).

Supporting principle, already evidence-backed in the repo (SYSTEM_MAP 6/23 regroup): the
winning instruction in the confounded T020 experiment was `reference_relationship`, a
field Lily left BLANK and Alec hand-supplied. "Users don't know what they want; fields
make them decide." A blank field = a machine default = the 011/014 failure lane.

## The feature (slim; reuse what exists)

**"The tool shows its guesses before you pay."**
1. Split the thin run at the derive/generate seam: phase 1 = calibrate + derive_register +
   assemble_thin_prompt (cheap: two small vision calls, zero image generation); STOP.
   Phase 2 = generate, only on operator confirmation.
2. Confirm surface on the existing stages UI (`frontend/run_view.py` already serves
   register + prompt progressively): show the derived register lane, anchors_held vs
   locks_flexed, and every `_derivation_trace` line matching the known guess/fallback
   markers as explicit "assumed X because Y was blank/unmatched - confirm or change" rows,
   with the SAME constrained controls the form already has (selects/sliders). The traces
   ARE the question list: ambiguity detection is deterministic, no LLM judgment glue
   (constitution-aligned). A run with zero guess lines shows a plain confirm, no friction.
3. Answers write back into subfields -> re-derive (free, deterministic, seconds) ->
   refreshed confirm surface. Confirm -> phase 2 generates. Answers-become-subfields is
   exactly the interview's contract.

Why this beats the full interview: it catches BOTH failure classes. Bad guesses on absent
input, AND engine bugs on present input: 014's defect (explicit "social media post"
overridden into a die-cut register) would have been visible as "register: event_prop" on
the confirm screen before the paid call. It converts every future register/derivation bug
from "paid misrender + a feature" into "caught free at the gate."

## Deferred (the full-interview upgrades; keep the idea, don't build yet)

- Visual pickers (thumbnail exemplars per option per dimension): real curated-content
  work; layer on only if operators demonstrably struggle with the textual confirm surface.
- Multi-step wizard flow: adds friction to the 90% case where the derivation is right.
- LLM-authored clarify questions: violates the agent-free ethos while the deterministic
  trace-driven list suffices.

## Out of scope

- The kit/legacy paths (no stages UI; their gates are the CLI approve loop).
- Changing any derivation logic; this feature only SURFACES + lets the human overwrite
  inputs. Register engine behavior byte-identical for identical subfields.
- The post-generation approve/nudge gate (unchanged; it remains the taste gate).

## Falsifiable test targets (no paid calls)

- Phase 1 run produces register_profile + prompt artifacts and NO generation call
  (stubbed-execute assertion, the 009/012 drift-guard pattern).
- The guess-extraction is a pure function over `_derivation_trace` + manifest notes:
  known guess lines in -> question rows out; a trace with zero guess markers -> zero rows.
- An answer round-trips: write-back -> re-derive produces a profile identical to a fresh
  run whose form had that value from the start (byte-comparable subfields).
- Confirm -> phase 2 uses the phase-1 run dir (no re-calibration, no drift between the
  confirmed profile and the generated prompt).
- Legacy one-shot mode (`--no-approve`-style bypass) stays byte-identical for the CLI.

## Eye-gate (load-bearing, deferred)

One live browser run: the operator sees the derived register + guess rows before any
spend, changes one answer, watches the profile update free, then pays once and the image
matches the confirmed framing.
