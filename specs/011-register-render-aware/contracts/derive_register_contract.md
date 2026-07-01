# Contract: derive_register (011 deltas)

The interface is the pure function `derive_register(subfields, brand_key, calibration=None)`
in `register/derive_register.py` (also exposed as the `--subfields/--brand/--out/--calibration`
CLI; the CLI contract is unchanged, the new field rides inside the subfields file).

## Inputs (delta)

- `subfields["render_style"]`: optional string, raw human term. Interpreted photographic iff
  `strip().lower()` is `"photographic"` or `"photo"`; every other value AND absence is flat
  (the historical default).

## Behavior table (the falsifiable contract)

Vibe columns use the promoting combination: playful = `formality<=3 and playfulness>=7`.
"Event usage" means the usage_context matches an event-prop row in USAGE_RULES
(e.g. "held for photos"). Rows marked NEW change with this feature; all others must be
byte-identical to pre-feature behavior.

| # | render_style | vibe | usage_context | register | required cues / trace obligations | |
|---|---|---|---|---|---|---|
| 1 | photographic | playful | no event language | `marketing` | trace names render_style as the suppression reason; `brand_locks_flexed` contains `font:rounded` + `palette:playful-accents` and NOT `shape:die-cut`; `font_role_hint` = `rounded display`; `shape_language_hint` stays the marketing default verbatim ("clean card or full-bleed, generous margins"; no die-cut wording; do NOT edit the hint string itself); trace lists the retained cues | NEW |
| 2 | flat / any non-photo | playful | no event language | `event_prop` | identical to pre-feature output (promotion fires, no new trace lines) | unchanged |
| 3 | ABSENT | playful | no event language | `event_prop` | identical to pre-feature output, byte-for-byte profile | unchanged |
| 4 | photographic | playful | event language present | `event_prop` | explicit human keyword wins; the gate never touches a usage-rule base | unchanged |
| 5 | photographic | formal (`formality>=8`) | no event language | `formal` | the gate only concerns the playful promotion; formal path untouched | unchanged |
| 6 | any | any | contains "marketing" / "social" / "instagram" / "promotional" (and no earlier-row keyword) | `marketing` | trace records an explicit keyword match, not the unmatched default | NEW |
| 7 | unrecognized string (e.g. "watercolor") | playful | no event language | `event_prop` | treated as flat (honest default); no crash, no trace noise | NEW (must equal row 2) |

## Trace contract

- The suppression line appears exactly when row 1 fires, and names the raw render_style value.
- The tone-retention line appears exactly when the retained cues are added, and names the vibe
  as the reason.
- No other rows may gain, lose, or reword trace lines.

## Drift guard

`_render_is_photo` (register engine) and `normalize_render_style` (harness/conductor.py) must
agree on: `"photographic"`, `"photo"`, `" PHOTOGRAPHIC "`, `"flat vector"`, `""`, `None`,
`"watercolor"`. Asserted by the 011 self-test importing both modules.

## Consumer guarantee (FR-008)

`scene_author`, `kit.py`, and the 009 opener matrix read the profile unchanged: no new profile
keys, no removed keys, no type changes. Kit/legacy routes never see `render_style` in their
subfields, so their profiles are byte-identical.
