# Data Model: Pre-Spend Confirm Gate

**Feature**: 015-pre-spend-confirm-gate | **Date**: 2026-07-08

Three entities, all file-backed in the run dir (no database, no in-memory server state).

## DerivationDraft (the stopped run)

The existing run dir, extended. Identity: the run dir name (`run_<brand>_<timestamp>`),
exactly as today.

| Field / artifact | Source | Notes |
|------------------|--------|-------|
| `inputs.json` | form via inputs_writer; MUTATED by write-backs | the only file answers touch |
| `calibration.json` | calibrate step, once per run dir | never re-run on answer changes |
| `register_profile.json` | derive_register | bytes pinned by 011/014 suites; unchanged shape |
| `sign_s1/final_prompt.txt` | scene_author --prompt-only | the confirmed prompt |
| `assumptions.json` | NEW: conductor derive phase (union of engine + conductor records) | rewritten on every re-derive |
| `gate_state.json` | NEW: conductor derive phase + server transitions | see state machine |
| `conductor_manifest.json` | conductor | gains gate provenance notes (answers applied, spend status) |

**State machine** (`gate_state.json.state`):

```
awaiting_confirmation ──confirm──> confirmed ──launch──> generating ──png lands──> done
        │  ▲                                                   │
        │  └── answer applied (re-derive) keeps/returns state  │ (drift guard failure
        │      awaiting_confirmation                           │  resets to awaiting_confirmation)
        └────── (no action; run left as-is) = abandoned draft (honest, passive)
```

- `awaiting_confirmation`: derive phase complete, zero image spend. The ONLY state that
  accepts answers or confirm.
- `confirmed` -> `generating`: server writes `confirmed` before launching phase generate
  (idempotency guard); the generate phase writes `generating` on start, `done` when
  `generated.png` lands.
- Abandonment is not a stored transition: a draft left `awaiting_confirmation` IS the
  abandoned state; the manifest note "derived, awaiting confirmation; no image spend"
  makes it honest (FR-010).

**Validation rules**: answers accepted only in `awaiting_confirmation`; confirm accepted
only in `awaiting_confirmation`; generate phase refuses to run unless state is `confirmed`
and `final_prompt.txt` exists; drift-guard failure resets to `awaiting_confirmation` with a
named error note.

## AssumptionRecord (one surfaced guess)

One entry in `assumptions.json` (list, ordered by pipeline stage). Recomputed whole on
every derive; never accumulated (spec edge case).

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | stable key, e.g. `register_lane`, `format_size`, `magnitude`, `render_style`, `relationship_dial` |
| `dimension` | string | operator-facing name of what was decided |
| `assumed_value` | string | what the tool chose, in plain words |
| `cause` | object | `{input: <inputs.json field>, value: <what the operator supplied>, reason: "blank" \| "unmatched" \| "unparseable" \| "clamped" \| "fallback"}` |
| `options` | list | constrained choices: `{label, writes: {field: <inputs field path>, value: <canonical value>}}` |
| `source` | string | emitting site: `derive_register` or `conductor` |

**Validation rules**: every option's `writes.value` must be a value the emitting site
recognizes (round-trip identity is asserted per shipped option in the self-test); `options`
is never empty; a record with `reason: "fallback"` for magnitude carries slider options
(two integer fields) instead of picks.

**Relationships**: `cause.input` names a field of DerivationDraft's `inputs.json`; applying
an option mutates exactly that field (plus provenance in the manifest), nothing else.

## Confirmation (the operator's commitment)

Recorded inside `gate_state.json` when state moves to `confirmed`:

| Field | Type | Meaning |
|-------|------|---------|
| `confirmed_prompt_sha` | string | hash of `final_prompt.txt` at confirm time; the generate phase's drift guard compares against a fresh re-assembly |
| `answers_applied` | list | `{assumption_id, chosen_label, written: {field, value}}` per applied answer, in order (provenance, §V) |
| `cost_stated` | string | the cost label shown on the button (audit of FR-011) |
| `confirmed_at` | string | timestamp |

**Validation rules**: exactly one Confirmation per generation; a second confirm request in
`generating`/`done` returns the existing state (no-op, FR-012); a drift-guard reset clears
`confirmed_prompt_sha` so the next confirm re-hashes.
