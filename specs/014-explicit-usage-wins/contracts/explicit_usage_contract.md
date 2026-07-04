# Contract: Explicit Usage Wins (014)

Verified by `test_explicit_usage_wins.py` (pure `derive_register` imports, free). Vibe columns
use the promoting combination (formality<=3, playfulness>=7). "mk-keyword" = usage matches the
marketing-keywords row ("marketing", "social", "instagram", "promotional").

| # | render | usage matches | register | obligations |
|---|---|---|---|---|
| 1 | flat / ABSENT / unrecognized | mk-keyword row | `marketing` | NEW: exactly one trace line, contains "SUPPRESSED", names the matched keyword; tone retention cues present (`font:rounded`, `palette:playful-accents`, rounded display font role); `shape:die-cut` ABSENT; no em-dash in the new line |
| 2 | flat / ABSENT | wall-posted row | `event_prop` | BYTE-IDENTICAL to `test_register_render_aware.EXPECTED_PREFEATURE_PROFILE` in BOTH cases (imported literal; the flat lane writes no render trace line today, so the profiles are identical; over-suppression or new flat-lane tracing fails here) |
| 3 | flat / ABSENT | no rule (default base) | `event_prop` | unchanged: "matched no rule" + "vibe overrides" lines; the vibe guess on a default base is legitimate |
| 4 | any | event row (even with mk words, e.g. "instagram photo") | `event_prop` | rule-order precedence; ZERO suppression entries |
| 5 | photographic | mk-keyword row | `marketing` | double gate: EXACTLY one "SUPPRESSED" line, and it names the render (photo gate first, 011 trace byte-unchanged) |
| 6 | photographic | wall-posted row | `marketing` | the 011 photo-gate case, byte-unchanged (photo suppression line as today) |

## No-regression sweep

All existing suites green unchanged, in particular `test_register_render_aware` 8/8 (its check7
asserts the match trace and precedence only, never the final register of the "instagram feed"
case, so it survives; every other check uses wall-posted or event usages).

## Deferred eye path (SC-005, the cheap variant)

FREE: a dry-run + standalone `derive_register.py` trace on a flat marketing-keyword brief shows
register=marketing, no die-cut flex, the keyword suppression line. The eye confirms on the next
natural flat paid run (a flat rectangular marketing poster, playful tone, no hand-held sign); no
dedicated paid run required.
