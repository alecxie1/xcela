# Implementation Plan: 022-form-size-progress

**Input**: `specs/022-form-size-progress/spec.md` (plan-as-spec, 019/021 convention: the
spec embeds the verified ground truth; this file adds only the technical mapping).

## Technical Context

- Python 3.11 stdlib + vanilla HTML/JS frontend (no new dependencies, no new modules).
- The change is deliberately THIN: `resolve_size` already handles px (unit-agnostic
  aspect math), and the form's JS (`formState()` in `frontend/index.html`) is the one
  place the brief string is composed — so US1 is frontend-only plus a parser
  normalization line, and US2 is frontend-only.

## File map (what each touch is)

| File | Change |
|---|---|
| `harness/format_size.py` | `像素` joins the `厘米`-class unit normalization (identity on ASCII pinned) |
| `test_format_size.py` | px value pins: `750x300px` -> aspect 2.5; `７５０×３００像素` normalizes; ASCII identity |
| `frontend/index.html` | US1: the one size field becomes W + H numeric inputs + cm/px select; `formState()` composes `"WxHunit"` (defaults 60/40/cm -> exactly `"60x40cm"`, THE pin); client-side loud refusal on blank/zero; the FR-005 draft-expectation note. US2: elapsed-seconds counter + typical-duration copy on the derive and generate waits, cleared when the wait ends; constants in ONE place; no progress bars |
| `test_form_size_progress.py` | NEW suite: composed-string byte-identity by value (grep-pinned form wiring), wait-expectation wiring pins, no-percentage guard |
| `frontend/playbook.html` | the 尺寸 row of the field table mentions px + the draft (aspect-only) contract |
| `CLAUDE.md` / `SYSTEM_MAP.md` | status current in the same commits |

## Structure decision

No new modules. The server, `inputs_writer`, the conductor argv, the register engine, and
the 015 gate are UNTOUCHED — the brief string contract (`format_size` as free text) is
preserved byte-identically, which is what keeps every downstream consumer and pinned suite
stable. UI checks are value-bearing greps (repo convention for vanilla-JS surfaces) plus
the one human flow gate (SC-004).

## Constitution check

- III (falsifiable): every new check asserts VALUES (composed string equality, resolved
  aspect numbers), never token presence.
- V (honest nulls): no progress percentage anywhere; duration copy is stated as
  approximate observed ranges; the aspect-only px contract is stated at the input.
- Cost discipline: zero paid calls in all new tests; the human gate is a FREE derive.
