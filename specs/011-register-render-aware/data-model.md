# Data Model: Render-Aware Register (011)

**Phase 1 output.** No new artifacts, no new files at run time. Two existing JSON artifacts gain
deltas; one in-code rule table gains a row. Schemas below show only the deltas.

## 1. subfields.json (run-dir glue artifact, written by `write_glue_artifacts`)

| Field | Type | Presence | Meaning |
|---|---|---|---|
| `render_style` | string | NEW, OPTIONAL; present only on the THIN route and only when the brief carries it | The human's requested rendering style, RAW and verbatim from the brief inputs (e.g. `"photographic"`, `"flat vector"`). Not normalized here (identity pass-through). |

**Validation**: none added; any value (or absence) is legal. Interpretation happens inside
`derive_register` via `_render_is_photo` (photographic/photo, case/whitespace-insensitive, means
photographic; everything else means flat, the historical default).

**Invariant (no-regression)**: on the kit and legacy routes `subfields.json` is byte-identical to
pre-feature output (the key is never written there).

## 2. register_profile.json (written by `derive_register`)

No schema change: same keys, same types. Value-level deltas:

| Field | Delta |
|---|---|
| `inferred_register` | For a photographic + playful/informal + no-event-language job the value is now `marketing` (was `event_prop`). All other input combinations are unchanged. |
| `brand_locks_flexed` | Can now contain `font:rounded` and `palette:playful-accents` while the register is `marketing` (playful-tone retention). MUST NOT contain `shape:die-cut` unless the register is `event_prop`. |
| `font_role_hint` / `font_resolved` | Under playful-tone retention the hint is `rounded display` (and step 5 resolves the licensed rounded family), while the register stays `marketing`. |
| `tone_hint` | Under playful-tone retention: playful-marketing wording instead of the restrained marketing default. |
| `shape_language_hint` | UNCHANGED under retention: stays the marketing default verbatim, "clean card or full-bleed, generous margins" (the format cue never follows the vibe; the string is not edited). |
| `_derivation_trace` | Two new possible entry kinds: (a) the render-gate suppression line, naming the raw `render_style` value as the reason the vibe promotion did not fire; (b) the tone-retention line, listing the retained cues and naming the vibe as the reason. Both appear ONLY when the respective decision fires; otherwise the trace is unchanged. |

## 3. USAGE_RULES (in-code rule table, `register/derive_register.py`)

New LAST row: `(("marketing", "social", "instagram", "promotional"), "marketing")`.
First-matching-row-wins semantics unchanged; all existing rows keep precedence, so explicit
event-prop phrases still capture the base register before this row is consulted.

## 4. Entity relationships (unchanged, shown for orientation)

```text
brief inputs (thin route)
  └── render_style ──> subfields.json (raw, thin-only)   [NEW edge]
subfields.json + answer_key (+ calibration) ──> derive_register ──> register_profile.json
register_profile.json ──> scene_author thin prompt (hints + brand_locks_flexed)  [unchanged]
```

## 5. State transitions

None. `derive_register` remains a pure function; the register decision table gains one guarded
edge (photo suppresses the vibe promotion) and one cue-enrichment step (tone retention), both
deterministic.
