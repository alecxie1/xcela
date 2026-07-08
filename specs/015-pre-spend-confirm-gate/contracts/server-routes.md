# Contract: server routes + stages extension

**Feature**: 015-pre-spend-confirm-gate

All routes stateless over run-dir artifacts (restart-safe). Existing routes unchanged
unless listed.

## `POST /run` (CHANGED behavior, same request contract)

Same multipart request as today (`form` JSON field + `reference` file + `product_1..N`).
Change: launches conductor `--phase derive` instead of a full run. Response unchanged
(`{run: <id>}`); the stages view then shows the gate when the derive phase lands.
A nudge POST (the existing rerun with a note) behaves identically: new run dir, phase
derive, its own gate (clarification Q2).

## `POST /run/<id>/answer` (NEW)

Request: `{"assumption_id": "register_lane", "label": "marketing piece"}` (the server
resolves the write from the run dir's own `assumptions.json`; the client never sends raw
field/value pairs, so only shipped options are applicable).

Behavior:
1. Refuse (409-style JSON error, named) unless `gate_state.json` is `awaiting_confirmation`.
2. Refuse (named error) if `assumption_id`/`label` matches no record in `assumptions.json`
   (FR fail-loud; keeps previous derivation, US2 scenario 3).
3. Apply `writes` to the run dir's `inputs.json`; append provenance to `gate_state.json`.
4. Re-run conductor `--phase derive --out <run_dir>` (calibration.json present -> vision
   calls skipped; zero image spend).
5. Response: `{ok: true}`; the client re-polls stages for the refreshed gate.

## `POST /run/<id>/confirm` (NEW)

1. Read `gate_state.json`:
   - `awaiting_confirmation`: write `confirmed` (+ prompt sha + cost label), launch
     conductor `--phase generate --out <run_dir>` async (the existing `_launch_async`
     pattern incl. `run_error.txt` on failure), respond `{ok: true, state: "confirmed"}`.
   - `confirmed | generating | done`: NO-OP, respond `{ok: true, state: <current>,
     note: "already confirmed; no second spend"}` (FR-012).
2. Drift-guard failure inside the generate phase resets state to
   `awaiting_confirmation` and surfaces via the existing `run_error.txt` channel; the gate
   re-renders fresh.

## `GET /run/<id>/stages` (EXTENDED)

Existing stages (brief, register, prompt, image) unchanged. New stage `gate`:

```json
{"gate": {"present": true,
           "state": "awaiting_confirmation",
           "assumptions": [ ...assumptions.json content... ],
           "answers_applied": [ ... ],
           "cost_label": "$0.08"}}
```

`present: false` with a note for pre-015 run dirs (honest null; old runs render as today).

## UI contract (`index.html` run view)

- Gate panel renders when `gate.present && state == "awaiting_confirmation"`: derivation
  summary (register lane, anchors_held, locks_flexed from the register stage), read-only
  explicit inputs, one row per assumption (label + cause sentence + constrained control),
  confirm button labeled with the paid cost. Zero rows: summary + confirm only.
- `state in {confirmed, generating}`: panel shows "generating (paid)" progress;
  `done`: today's image + approve/nudge gate.
- Nudge button behavior unchanged in wording; its rerun lands on a new gate.
- No em-dashes in any user-facing string (FR-013).
