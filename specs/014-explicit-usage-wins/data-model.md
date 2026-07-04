# Data Model: Explicit Usage Wins Over the Vibe Guess (014)

**Phase 1 output.** No new artifacts, no schema changes; value-level deltas in one module and
one JSON artifact.

## 1. USAGE_RULES (in-code rule table)

| Item | Delta |
|---|---|
| marketing keywords row | unchanged content, now referenced via the named constant `MARKETING_USAGE_KEYWORDS` (same tuple object used in the table, identity-comparable) |
| row order / other rows | unchanged (event rows keep absolute precedence) |
| match loop | additionally records the matched row alongside the already-recorded keyword; no trace change from the loop itself |

## 2. The promotion branch (marketing base + formality<=3 + playfulness>=7)

Decision order (if / elif / else, one outcome, at most one suppression entry):

1. render is photographic (011 gate, wording byte-unchanged) -> suppress, photo trace line
2. NEW: base row is `MARKETING_USAGE_KEYWORDS` -> suppress, trace line naming the matched
   keyword (e.g. "usage explicitly matched 'social' ... promotion SUPPRESSED, register stays
   marketing"); no em-dash
3. else -> promote to `event_prop` (byte-identical legacy path: wall-posted, sign-era rows,
   unmatched default)

## 3. register_profile.json (value-level deltas)

| Field | Delta |
|---|---|
| `inferred_register` | flat/absent-render + promoting vibe + marketing-keyword usage: now `marketing` (was `event_prop`). All other combinations unchanged. |
| `brand_locks_flexed` | for those cases: `font:rounded` + `palette:playful-accents` via the EXISTING tone retention (no `shape:die-cut`); mechanism unchanged, it keys on register+vibe |
| `_derivation_trace` | one new possible entry kind: the keyword suppression line; appears ONLY when gate 2 fires; the photo line and all legacy lines byte-unchanged |

## 4. State transitions

None. One deterministic condition added to an existing decision chain.
