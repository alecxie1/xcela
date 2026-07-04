# Research: Explicit Usage Wins Over the Vibe Guess (014)

**Phase 0 output.** No unknowns; all three decisions resolve from `register/derive_register.py`
as it stands after 011 (USAGE_RULES with the appended marketing row; the match loop appending
"matched <keyword> => <base>" to the trace; the promotion branch with the 011 photo gate).

## D1. How the engine knows the base came from the marketing row

**Decision**: Name the marketing keywords as a module constant `MARKETING_USAGE_KEYWORDS =
("marketing", "social", "instagram", "promotional")` and use that constant AS the row in
`USAGE_RULES` (identity-comparable). The match loop, which already computes `hit` (the keyword)
for the trace, additionally records `base_row = keywords` when a row matches. The promotion
branch then tests `base_row is MARKETING_USAGE_KEYWORDS`.

**Rationale**: Zero new bookkeeping structures: the loop already has both values in hand; naming
the tuple makes the suppression condition read as policy ("the marketing-keywords row") rather
than as a magic literal, and identity comparison cannot accidentally match a different row that
happens to share a keyword. The constant also gives the new test a stable import surface.

**Alternatives considered**: re-scanning the usage string for marketing keywords inside the
promotion branch: duplicates matching logic and diverges the moment the row changes (drift).
Tagging rows with a flag field (3-tuples): touches every row for a one-row need.

## D2. Gate ordering in the promotion branch (the FR-006 single-entry rule)

**Decision**: `if _render_is_photo(...)` FIRST (the 011 gate, wording untouched), `elif base_row
is MARKETING_USAGE_KEYWORDS` SECOND (the new gate), `else` promote. When both gates apply
(photo + marketing keyword) the photo entry wins the trace.

**Rationale**: Exactly one suppression entry falls out of if/elif by construction (FR-006), and
putting photo first keeps EVERY existing photo-lane trace byte-identical, including the 011
suite's photo assertions and any saved run artifacts an operator might diff. Both causes are
true in the double case; the constitution requires a true, named reason, not all reasons.

**Alternatives considered**: keyword gate first: equally correct logically but rewrites the
photo-lane trace for photo+keyword briefs, churning byte-identity for no benefit. Emitting both
entries: fails FR-006 and reads as engine confusion to the human reviewer.

## D3. Test surface and the reused baseline

**Decision**: New `test_explicit_usage_wins.py` with four checks: (1) flat/absent-render +
promoting vibe + each marketing keyword yields `marketing`, ONE suppression line naming the
keyword, tone retention cues present, `shape:die-cut` absent, no em-dash in the new line;
(2) no-regression pair: the wall-posted + playful absent-render profile equals
`test_register_render_aware.EXPECTED_PREFEATURE_PROFILE` byte-for-byte (imported, the fixture is
identical and that literal is still the current output), and an unmatched free-text usage +
playful still promotes to `event_prop` via "matched no rule" + "vibe overrides"; (3) precedence:
"instagram photo" resolves `event_prop` through the event row with zero suppression entries;
(4) double gate: photographic + "instagram feed" + promoting vibe yields `marketing` with
EXACTLY one line containing "SUPPRESSED", and it names the render (the D2 ordering).

**Rationale**: Each check kills a named wrong build: unfixed (1), over-suppressing (2),
row-order-broken (3), double-tracing (4). Importing the existing baseline literal instead of
capturing a new one follows the 013 precedent (test_product_refs imports the 012 literal) and
keeps one canonical byte-identity anchor per fixture. Verified against the existing suites: the
011 test's check7 ("instagram feed") asserts only the match trace line and the precedence case,
never the final register, so it stays green after the fix; every other existing check uses
wall-posted or event usages, untouched by the new gate.
