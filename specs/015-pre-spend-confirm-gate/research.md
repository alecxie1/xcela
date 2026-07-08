# Research: Pre-Spend Confirm Gate

**Feature**: 015-pre-spend-confirm-gate | **Date**: 2026-07-08

All unknowns deferred from clarification are resolved here. Code references verified against
the working tree on 2026-07-08.

## R1. Where the run splits (the derive/generate seam)

**Decision**: two surgical stop points, no restructuring.
1. `harness/scene_author.py` thin driver: `final_prompt.txt` is written (~line 1077) BEFORE
   the generation block begins (~line 1081). A new `--prompt-only` flag returns immediately
   after the prompt is saved (plus a small manifest note), touching nothing else.
2. `harness/conductor.py` gains `--phase derive|generate|full` (default `full`):
   - `derive`: run calibrate (SKIPPED when `calibration.json` already exists in `--out`),
     derive_register, and scene_author thin with `--prompt-only`; write `assumptions.json`
     + `gate_state.json`; stop. No approve gate step.
   - `generate`: requires `--out` pointing at an existing derive-phase run dir; re-runs the
     scene_author thin step WITHOUT `--prompt-only`.
   - `full`: today's behavior, byte-identical (the flag defaults to it; kit/legacy routes
     ignore the flag entirely in v1 and fail loud if `--phase derive` is combined with a
     non-thin route).

**Rationale**: the seams already exist as line boundaries; the conductor already accepts
`--out` (reuse a run dir) and its steps are independent subprocesses. No state needs to be
held in memory across phases: everything the generate phase needs is on disk.

**Alternatives considered**: (a) server-side orchestration of individual step scripts
(rejected: the server must never reimplement conductor sequencing, the 004 principle);
(b) a blocking conductor that waits for a confirm file (rejected: holds a process open
across a human-scale wait, fragile over server restarts).

## R2. How assumptions are detected (structured emission, never trace parsing)

**Decision**: every guessing site emits a STRUCTURED record; nothing regex-parses prose.
- `register/derive_register.py` gains an optional `--assumptions-out <path>` flag. When
  present, it writes its guess records (register base default, magnitude fallback source)
  as JSON to that path. When absent: behavior and ALL output bytes identical to today.
- Conductor-level guesses are appended by the conductor derive phase from values it already
  computes: `normalize_render_style` fallback (conductor.py:113-116), `normalize_dial`
  fallback (conductor.py:105), `format_size` unparseable-default / aspect-clamp
  (`fmtsize.resolve_size` result carries `defaulted`/`needs_review`).
- The union is written to the run dir as `assumptions.json`.

**Rationale**: parsing `_derivation_trace` prose would be a token-presence gate
(constitution §III forbids the class), and coupling to prose wording would break on any
trace rewording. Emitting at the site is deterministic and testable per site.

**Critical constraint honored**: `register_profile.json` BYTES ARE PINNED by the 011/014
suites (asserted against inlined literals). Assumptions therefore go to a SEPARATE file via
an opt-in flag; the profile is untouched. A drift-guard test asserts: derive WITHOUT the
flag produces byte-identical profile + trace to the pre-015 baseline.

## R3. The v1 assumption dimensions (inventory, fire conditions, controls)

| # | Dimension | Fires when | Control (constrained) |
|---|-----------|-----------|----------------------|
| 1 | Register lane | usage_context matched NO USAGE_RULES row (base defaulted to marketing, derive_register.py:101-103), including the empty case | direct lane pick: event prop / marketing / formal |
| 2 | Format size | `resolve_size` could not parse, or aspect was clamped (`needs_review`) | pick from common sizes + "keep 1536x1024" |
| 3 | Register magnitude | no calibration available (calibration step failed or absent), slider-source fallback chain engaged (derive_register.py:147-167) | the two vibe sliders (writes context.vibe) |
| 4 | Render style | `normalize_render_style` received a non-empty UNRECOGNIZED value | pick: flat vector / photographic |
| 5 | Relationship dial | `normalize_dial` received a non-empty UNRECOGNIZED value (fell to "extend") | pick: extend / match style / mood |

Rows 4 and 5 cannot fire from the browser form (both are selects since 012) but CAN fire on
hand-written/legacy inputs JSON; they are cheap to emit and make the gate honest for CLI
users who later view the run. Row 1 is the load-bearing case (the 173925 class). Blank
usage_context also fires row 1: a default on an empty input is still a guess the operator
should see.

**NOT emitted in v1**: `warmth` (collected by no surface, defaulted to 5 in
`inputs_writer.py:67`, and not used by register direction; retiring or collecting it is a
separate cleanup, out of 015 scope, noted for the backlog). The vibe PROMOTION on a
defaulted base (guess-on-guess, legitimate per 014) is not its own row: the lane pick row
subsumes it (an explicit pick makes the promotion moot).

## R4. Write-back canonicalization (answers become subfields)

**Decision**: each assumption option carries a concrete write-back: `(inputs_field,
canonical_value)`. Applying an answer rewrites that field in the run dir's `inputs.json`,
then re-runs the derive phase on the same `--out`.
- Lane pick "event prop" -> `context.usage_context = "held for photos"` (hard row 1 of
  USAGE_RULES, absolute precedence).
- Lane pick "marketing" -> `context.usage_context = "marketing"` (the named
  MARKETING_USAGE_KEYWORDS row; per 014 the vibe promotion cannot override it).
- Lane pick "formal" -> requires ONE additive USAGE_RULES row, e.g.
  `(("formal document", "official notice"), "formal")`, appended LAST: no existing keyword
  collides, all pinned baselines lack these phrases (byte-identity preserved and asserted),
  and only an explicit pick or an explicit typed phrase ever hits it. Write-back:
  `context.usage_context = "formal document"`. (Verify `REGISTER_HINTS` covers "formal";
  it is an existing register value via the formality>=8 override.)
- Format-size pick -> `format_size = "<W>x<H>cm"` canonical string.
- Vibe sliders -> `context.vibe.formality/playfulness` integers.
- Render style / dial picks -> `render_style` / `reference_relationship` verbatim select
  values (the same strings the form sends).

**Rationale**: writing recognized canonical INPUT values (not derived-value overrides)
keeps the single derivation path: FR-006 path independence holds by construction and is
asserted per option (write-back + re-derive == fresh run with that value from the start).
The pick IS the human statement; the manifest records that the value came from the gate
(provenance note), so the run stays auditable.

**Alternative rejected**: a first-class `register_override` input that bypasses
USAGE_RULES: a second derivation channel to test and a §VI violation risk (collapsing the
per-dimension resolution).

## R5. Gate state, idempotent confirm, restart-safety

**Decision**: gate state lives on disk in the run dir (`gate_state.json`:
`awaiting_confirmation | confirmed | generating | done | abandoned` + timestamps + answer
provenance). The server is stateless about gates (it already is about runs): every route
re-reads artifacts.
- `POST /run/<id>/confirm`: refuses unless state is `awaiting_confirmation`; writes
  `confirmed` + launches phase generate; a second confirm sees `generating|done` and
  no-ops with a note (FR-012). The state write happens before the launch (single-threaded
  stdlib server: no race within one process; the state file check also guards a restarted
  server).
- Abandonment is passive: a run left in `awaiting_confirmation` IS the honest draft
  (FR-010); the conductor's derive phase writes the manifest note "derived, awaiting
  confirmation; no image spend" at stop time, so no cleanup job is needed.
- Server restart: state and artifacts are all on disk; reopening the run URL re-renders
  the gate from files. (Resolves the clarify-deferred resumability question.)

## R6. Prompt drift guard on confirm (FR-007)

**Decision**: the generate phase re-assembles the prompt (same deterministic inputs) and
compares to the confirmed `final_prompt.txt`. Identical (the normal case, assembly is
pure): proceed. Different (inputs.json touched out-of-band, code changed between phases):
FAIL LOUD with a named error and reset state to `awaiting_confirmation` so the gate
re-renders fresh. Never generate from unseen values.

## R7. Nudge reruns through the gate

**Decision**: the nudge flow keeps its contract (new run dir, style_notes appended via the
";"-join channel) but launches PHASE DERIVE instead of a full run; the new run dir arrives
at its own gate (fresh calibration: new run dir has no calibration.json; the reference is
re-copied as today). Confirm generates. `frontend/runner.py` argv builders stay pure and
gain the phase parameter; `build_conductor_argv` keeps its exact current output for the
legacy shape (drift-guard: existing tests updated only where the flow intentionally
changed).

## R8. What the gate displays (reuse of run_view)

**Decision**: `frontend/run_view.py` stages payload gains a `gate` stage: `assumptions.json`
content + `gate_state.json` + the already-served register profile and prompt. The
index.html run view renders the gate panel when the gate stage is present and state is
`awaiting_confirmation`: derivation summary (lane, anchors_held, locks_flexed, the same
plain rendering `print_register_profile_plain` uses), assumption rows with their constrained
controls, read-only display of explicit inputs, and the confirm button labeled with the
paid cost (reusing the existing "$0.08" label convention). Zero assumption rows: summary +
confirm only (FR-008).
