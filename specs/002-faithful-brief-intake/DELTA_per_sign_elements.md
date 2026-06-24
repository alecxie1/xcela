# DELTA SPEC (002 follow-up): per-sign mandatory/forbidden elements

**Branch:** `002-faithful-brief-intake` (you are already on it). One task, one test, one commit.

## Why
002 wired `mandatory_elements` / `forbidden_elements` at the CAMPAIGN level only:
`harness/conductor.py build_compositions()` copies the campaign list onto EVERY sign. That
cannot faithfully represent Lily's real AIA brief, where `分别画叉` (draw an X) applies to
ONLY 2 of 6 signs (the scam-type signs), not the money-bag protect signs. Stamping `分别画叉`
onto all 6 is exactly the lossy-intake failure 002 exists to kill, one level up. Fix: let each
sign carry its OWN elements that COMPOSE with the campaign-level ones.

## Read first (verify against actual code, do not trust this doc over the code)
- `CLAUDE.md`, `.specify/memory/constitution.md`
- `specs/002-faithful-brief-intake/spec.md` (FR-003/FR-004 verbatim-passthrough rules)
- `harness/conductor.py` — `build_compositions()` (~L222-247) and `validate_inputs()` (~L403-422)
- `harness/prompt_elements.py` — `elements_clause()`, `has_conflict()`
- `test_brief_wiring.py` — the existing wiring test to extend

## The change (semantics)
1. **Per-sign optional fields.** A `signs[]` item MAY carry `mandatory_elements` and/or
   `forbidden_elements` (each a list[str]). Both OPTIONAL; absent = empty list (honest null,
   constitution §V). Back-compat: existing inputs without them behave EXACTLY as today.
2. **Composition = order-preserving union (campaign first, then per-sign), de-duplicated.**
   Effective mandatory for a sign = campaign `mandatory_elements` ++ that sign's
   `mandatory_elements`, dropping exact-duplicate strings while preserving first-seen order.
   Same for forbidden. Campaign-level = "applies to all signs"; per-sign = "this sign only".
   So a campaign with `mandatory_elements: []` and s5/s6 each `["分别画叉"]` yields `分别画叉`
   on s5 and s6 ONLY, and `[]` on s1-s4.
3. **Verbatim passthrough (FR-003).** Copy strings byte-for-byte. NEVER rephrase, reorder
   (beyond the defined campaign-then-per-sign concatenation), interpret, or expand into variant
   counts. No agent/LLM anywhere in this path.
4. **Conflict detection per sign (constitution §V).** The existing campaign conflict check stays.
   ADDITIONALLY, if a sign's EFFECTIVE mandatory ∩ effective forbidden is non-empty, that sign
   gets `needs_review` + a reason naming the conflicting item(s). Do not silently resolve.
5. **validate_inputs**: accept the per-sign fields; if present they MUST be lists of strings
   (raise SystemExit with a clear message otherwise). Absent is fine.

## Files to change
- `harness/conductor.py`: `build_compositions()` (union logic onto each `comp`), `validate_inputs()`
  (accept + type-check per-sign fields). Touch NOTHING else in the routing.
- Docs (keep current in the SAME commit, constitution §VII):
  `specs/002-faithful-brief-intake/data-model.md` (Per-sign Composition entity: note per-sign
  elements + union rule), `contracts/inputs-schema.md` (signs[] may carry the two fields; union
  semantics). Do not rewrite unrelated sections.

## Falsifiable test (REQUIRED — assert VALUES a wrong build cannot satisfy, constitution §III)
Extend `test_brief_wiring.py` (or add `test_per_sign_elements.py`) with checks that FAIL on the
current campaign-only build:
- **Targeting:** inputs with campaign `mandatory_elements: []`, signs s1..s6 where ONLY s5 and s6
  carry `["分别画叉"]` → after `build_compositions`, s5 and s6 compositions contain `分别画叉` and
  s1-s4 do NOT. (The current build would put it on all or none — this asserts per-sign targeting.)
- **Union + dedup:** campaign `["A"]` + a sign `["A","B"]` → that sign's effective mandatory ==
  `["A","B"]` (order preserved, "A" not duplicated); a sign with no per-sign field → `["A"]`.
- **Verbatim:** the exact CJK string `分别画叉` survives byte-for-byte (assert equality, not `in`).
- **Per-sign conflict:** a sign with effective mandatory ∩ forbidden non-empty → `needs_review` set
  with a reason naming the item; a clean sign → not flagged by this rule.
- **Back-compat:** an inputs dict with NO per-sign fields produces the SAME result as today
  (campaign list on every sign).
Run the FULL existing suite too (`test_conductor.py test_brief_wiring.py test_faithful_intake.py
test_format_size.py test_review.py`) and paste real pass/fail output.

## Hard rules
- Do NOT call image generation / any paid endpoint. This is structural wiring only.
- Do NOT launch background processes or poll loops. Run tests as foreground blocking calls.
- `.venv/bin/python` for everything. Stdlib only in conductor/prompt_elements (no new deps).
- Honest reporting: if something fails or you couldn't verify it, say so plainly. Do not
  fabricate test output; print actual results from disk.

## Definition of done
- All new + existing self-tests green (paste the real terminal output).
- A dry-run of an inputs file where only s5/s6 carry `分别画叉` shows it on s5/s6 ONLY in the
  per-sign `composition.json` (report which signs got it).
- conductor.py + docs + test committed on `002-faithful-brief-intake` with a clear message.
- Report: files changed, the exact union/dedup logic used, test output, and the dry-run targeting result.
