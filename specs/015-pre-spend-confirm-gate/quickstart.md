# Quickstart: Pre-Spend Confirm Gate (validation guide)

**Feature**: 015-pre-spend-confirm-gate

All steps below are FREE except the final human eye-gate. Run from the repo root with the
project venv (`.venv/bin/python`).

## 1. The feature self-test (structural, no paid calls)

```bash
.venv/bin/python test_confirm_gate.py
```

Expected: all checks green. The suite asserts (see contracts/ for exact shapes):
- derive phase makes ZERO generation calls (stubbed run_step; no `generate` import in
  `--prompt-only`).
- `--phase full` artifacts byte-identical to the pre-015 baseline (thin route), kit/legacy
  argv untouched.
- derive_register WITHOUT `--assumptions-out`: profile + trace byte-identical to the
  pre-015 baseline (the 011/014 literal pins still hold; formal-row addition proven
  inert for all pinned inputs).
- Per shipped assumption option: write-back + re-derive == fresh-run derivation with that
  value from the start (FR-006 round-trip identity).
- Replaying the archived 173925 defect subfields emits the `register_lane` assumption
  record (SC-003's structural half).
- Confirm idempotency: second confirm on `generating`/`done` state triggers no second
  launch (stubbed).
- Prompt drift: inputs mutated after confirm -> generate phase fails loud, state reset.
- Zero-guess inputs -> `assumptions.json == []` and the gate stage still renders
  (FR-008).
- multipart/route tests: answer route refuses unknown ids and non-awaiting states.

## 2. No-regression sweep (the prior suites stay green)

```bash
for t in test_conductor test_render_and_scrub test_thin_route test_render_modes \
         test_register_render_aware test_explicit_usage_wins test_lossless_brief \
         test_product_refs test_reference_upload test_frontend_intake \
         test_frontend_runner test_frontend_stages test_frontend_nav; do
  .venv/bin/python $t.py || break; done
```

## 3. Free end-to-end dry pass (browser, no image spend)

```bash
pkill -f frontend/server.py; .venv/bin/python frontend/server.py
```

In the browser: fill a brief with a deliberately unmatched usage phrase (e.g. "goes viral
on rednote") and a garbage size ("about poster size"), Run. Expected, all pre-spend:
- The run stops at the gate: register summary + prompt visible, `generated.png` absent.
- Two assumption rows (register lane, format size) naming cause and offering picks.
- Pick "marketing piece": the gate refreshes in seconds; the register stage now shows an
  explicit match, the row set recomputes; still no image.
- Walk away: the run dir persists with the honest "awaiting confirmation, no image spend"
  manifest note. Restart the server; reopen the run URL; the gate re-renders from disk.

## 4. The ONE paid eye-gate (SC-006, human-judged)

Continue from step 3 (or a fresh brief): at the gate, change one answer, watch the plan
update free, press Confirm (cost stated). Expected: exactly one generation; the image
matches the confirmed framing (register lane and prompt seen at the gate). Then press the
post-image Nudge with a note: the rerun lands on a NEW gate (clarification Q2) before any
second spend. Judge by eye; record the verdict in SYSTEM_MAP.

## Success criteria mapping

| Spec | Verified by |
|------|-------------|
| SC-001 | step 1 (zero-generation assertion) + step 3 |
| SC-002 | step 3 (free answer loop, seconds) |
| SC-003 | step 1 (173925 replay emits the lane record) |
| SC-004 | step 3 with a complete brief (zero rows, one click) |
| SC-005 | steps 1-2 (byte-identity + sweep) |
| SC-006 | step 4 (human eye) |
