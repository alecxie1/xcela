# Contract: CLI phases (conductor, scene_author, derive_register)

**Feature**: 015-pre-spend-confirm-gate

## harness/conductor.py

New flag: `--phase {full|derive|generate}`, default `full`.

- `--phase full` (default): BYTE-IDENTICAL to today for every route (thin, kit, legacy),
  proven against pre-015 artifacts in the self-test. Scripted/CLI users see no change
  without opting in (FR-009).
- `--phase derive` (thin route only; combined with kit/legacy -> named fail-loud error):
  1. calibrate: SKIPPED iff `<out>/calibration.json` exists (resume), else run as today.
  2. derive_register: as today PLUS `--assumptions-out <out>/assumptions_register.json`.
  3. scene_author thin: as today PLUS `--prompt-only`.
  4. Write `<out>/assumptions.json` (conductor records + engine records, ordered),
     `<out>/gate_state.json` (`awaiting_confirmation`), manifest note
     `"derived, awaiting confirmation; no image spend"`.
  5. Exit 0. ZERO generation calls (asserted via stubbed run_step).
- `--phase generate` (requires `--out` of an existing derive run):
  1. Refuse (named error) unless `gate_state.json` is `confirmed` and
     `sign_s1/final_prompt.txt` exists.
  2. Re-run the scene_author thin step WITHOUT `--prompt-only`; scene_author re-assembles
     and drift-checks (below). Write `generating` -> `done` around it.
  3. Finish manifest as today (deliverable, compliance summary).

Calibrate/derive argv MUST be provably independent of applied answers except through
`inputs.json` content (the 013 calibration-isolation pattern: argv equality assertions).

## harness/scene_author.py (thin driver)

New flags: `--prompt-only` and `--verify-prompt` (thin mode only).

- `--prompt-only`: assemble_thin_prompt -> write `final_prompt.txt` -> write a partial
  `run_manifest.json` (`generation: null` + an honest note) -> return. NO import of
  `generate`, no refs assembly, no model call.
- `--verify-prompt` (passed ONLY by the conductor generate phase): re-assemble; if
  `final_prompt.txt` is missing OR the fresh prompt differs from its content, FAIL LOUD
  (named drift error, nonzero exit, zero generation); the conductor resets gate state to
  `awaiting_confirmation`. If equal: proceed to generation exactly as today.
- NEITHER flag: today's behavior byte-identical. (Contract amendment during T002: the
  drift check is an EXPLICIT flag, not an existing-file heuristic, because the legacy CLI
  approve-gate nudge re-runs this step on the SAME dir with an intentionally changed
  prompt and must keep overwriting freely.)

## register/derive_register.py

New optional flag: `--assumptions-out <path>`.

- Absent: byte-identical behavior AND output (profile + trace pinned against the pre-015
  baseline; the 011/014 literal pins keep holding).
- Present: additionally write the engine's AssumptionRecords (see
  `assumptions-schema.md`): the register-lane default record (usage_context matched no
  row, incl. blank) and the magnitude-fallback record (slider source not calibration).
- ONE additive USAGE_RULES row for the formal lane pick:
  `(("formal document", "official notice"), "formal")` appended LAST. Existing pinned
  baselines contain none of these phrases: their profiles stay byte-identical (asserted).
