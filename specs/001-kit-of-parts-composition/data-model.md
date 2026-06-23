# Phase 1 Data Model: Kit of Parts + Bespoke Composition

Canvas is 1536x1024. All zone geometry is expressed as fractions of the canvas in [0,1].
"Authored" = human-written brand data. "Derived" = computed at runtime. "Per-sign" = produced
once per message during composition.

---

## Entity: Kit (campaign constant)

The kit has an AUTHORED part (`kits/<brand>.json`) and a DERIVED part (`kit_profile.json`,
produced once per campaign by `harness/kit.py`). Together they are the constant shared by every
sign in the campaign.

### IconVocabularyEntry (authored — in `kits/<brand>.json`)

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Unique within the vocabulary (e.g. `money_bag`). |
| `meaning_cues` | string[] | Non-empty. Authored keyword/phrase cues used for deterministic matching (D2). |
| `mode` | enum | One of the brand's declared rhetorical modes (e.g. `protect` / `warn` / `resist`). Ties the icon to a layout family. |
| `icon_description` | string | What gpt-image-2 should paint in the icon zone (the SELECTION is deterministic; the RENDER is generative). |
| `asset_path` | string \| null | Optional future: a real icon asset to composite instead of describing. v1 = null. |

**Validation**: every `mode` must appear in the kit's `modes` list; `id` unique; `meaning_cues`
non-empty. No two entries may share an identical full `meaning_cues` set (ambiguous match).

### LayoutArchetype (authored — in `kits/<brand>.json`)

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Unique within the vocabulary (e.g. `warn_panel`, `protect_solid`). |
| `modes` | enum[] | Non-empty subset of the kit's `modes` this archetype serves. |
| `panel_treatment` | string | Background/panel spec (e.g. "white panel + red headline for alarm", "warm solid crimson"). Drives the generation prompt. |
| `icon_zone` | Zone | `{x_frac,y_frac,w_frac,h_frac}` where the hero icon is painted. |
| `text_zone` | Zone | `{x_frac,y_frac,w_frac,h_frac}` reserved CLEAR for the composited headline. |
| `accent_treatment` | string \| null | Optional accent vocabulary cue (diamonds/stars/dots) consistent with the kit. |

**Validation**: `icon_zone` and `text_zone` MUST NOT overlap (non-collision by construction,
FR-005). Both zones MUST lie within [0,1] and inside a safe die-cut margin. `modes` non-empty and
all in the kit's `modes`. At least two archetypes total (the kit must offer distinctness).

### Kit authored file shape (`kits/<brand>.json`)

| Field | Type | Rules |
|-------|------|-------|
| `brand` | string | Must match the answer-key brand id. |
| `modes` | string[] | The brand's rhetorical modes (e.g. `["protect","warn","resist"]`). |
| `icon_vocabulary` | IconVocabularyEntry[] | Non-empty. |
| `layout_vocabulary` | LayoutArchetype[] | >= 2 entries. |
| `accent_vocabulary` | string[] \| null | Optional shared accent set. |
| `_authored_by` / `_authored_date` | string | Provenance. |

### KitProfile (derived — `kit_profile.json`, one per campaign)

Produced by `harness/kit.py` from the answer key + register_profile + reference calibration.
Answer key WINS every conflict (D6 / clarified).

| Field | Type | Source |
|-------|------|--------|
| `brand` | string | answer key |
| `palette` | {role→hex}[] | answer key colors (HARD); reference fills only non-conflicting roles |
| `font_role` | string | `register_profile.font_role_hint` resolved via `typography.styles` |
| `font_family` / `font_index_key` | string | answer-key `typography.styles[...]` (HARD lock) |
| `frame_treatment` | string | derived from reference `style_evidence` (SOFT) |
| `register` | enum | `register_profile.inferred_register` |
| `anchors_held` | string[] | from register_profile / calibration (HARD held) |
| `locks_flexed` | string[] | from register_profile / calibration (SOFT flexed) |
| `conflict_resolutions` | string[] | every reference-vs-answer-key clash and that answer key won (auditable) |
| `notes` | string[] | honest-null notes (e.g. reference style extraction failed → answer-key-only kit) |

---

## Entity: Composition (per-sign)

Produced per message by `harness/compose_select.py` (+ the fit clamp), written to
`output/run_*/sign_*/composition.json`.

| Field | Type | Rules |
|-------|------|-------|
| `sign_id` | string | from inputs |
| `message` | string[] | the headline line(s) for this sign |
| `detected_mode` | enum \| null | rhetorical mode resolved from the matched icon entry; null if no match |
| `chosen_icon` | string \| null | IconVocabularyEntry.id, or null + `needs_review` if no confident match (V) |
| `icon_match_score` | number | deterministic cue-match score (for audit/falsifiability) |
| `chosen_archetype` | string \| null | LayoutArchetype.id; null only if mode unresolved |
| `archetype_reused` | bool | true when the layout vocabulary was exhausted → `needs_review` (D3) |
| `text_zone` | Zone | copied from the chosen archetype (composition owns the zone) |
| `fitted_type` | FitResult | result of the fit-to-zone clamp |
| `needs_review` | bool | true if any of: no icon match, archetype reused, type cannot fit |
| `needs_review_reason` | string \| null | human-readable reason (no em-dashes) |

### FitResult (per-sign — output of the fit-to-zone clamp, D5)

| Field | Type | Rules |
|-------|------|-------|
| `fits` | bool | true if the headline fits the zone with margin at some size >= min |
| `final_size_px` | int \| null | the largest fitting size; null if it cannot fit |
| `rendered_box_frac` | Zone \| null | the measured rendered text box; MUST be inside `text_zone` with margin when `fits` |
| `margin_px` | int | the enforced margin on all edges |
| `min_size_px` | int | the floor below which we honest-null instead of clipping |

---

## State / lifecycle (per campaign run)

1. Load inputs (human) → validate (existing conductor).
2. Derive shared `register_profile` (+ calibration if reference). [reuse `register/`]
3. Build `kit_profile.json` once (authored kit + derived layer; answer key wins). [new `kit.py`]
4. For each sign:
   a. Match meaning → mode + icon (deterministic). Miss → null + needs_review. [new `compose_select.py`]
   b. Select distinct layout archetype (collision-avoiding). Exhausted → reuse + flag. [new `compose_select.py`]
   c. Reserve `text_zone` from the archetype; run fit-to-zone clamp. Can't fit → null + needs_review. [new clamp in `composite_text.py`]
   d. Build reserve-box generation prompt (paint bg + icon in icon_zone, keep text_zone clear); generate. [reuse `scene_author`]
   e. Composite licensed headline into `text_zone` at `final_size_px` + compliance manifest. [reuse `composite_text`]
5. Surface all icon/layout proposals + needs_review at the approve/nudge gate (human taste). [reuse conductor]
6. Write per-sign `composition.json`, `run_manifest.json`; campaign `conductor_manifest.json`.

---

## Falsifiable properties (seed the tests; constitution III)

- A 钱袋子/储蓄 message resolves `chosen_icon = money_bag` (not a default, not null).
- A nonsense/meaningless message yields `chosen_icon = null` AND `needs_review = true`.
- Two messages of different modes yield two DIFFERENT `chosen_archetype` values.
- When archetypes are exhausted, the extra sign has `archetype_reused = true` AND `needs_review = true`.
- For every archetype, `icon_zone` and `text_zone` do not overlap.
- A long headline yields `final_size_px` strictly less than a short headline's in the same zone,
  and its `rendered_box_frac` lies inside `text_zone` with margin.
- A headline that cannot fit at `min_size_px` yields `fits = false`, `final_size_px = null`,
  `needs_review = true` (never a clipped/overflowing render).
- On a reference-vs-answer-key palette conflict, `kit_profile.palette` holds the answer-key hex
  and `conflict_resolutions` records that the answer key won.
