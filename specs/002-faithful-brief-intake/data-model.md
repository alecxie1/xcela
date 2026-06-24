# Phase 1 Data Model: Faithful Self-Service Brief Intake + Review

Entities are the artifacts that flow brief → inputs → run → review. "Faithful" means every value
the human entered appears verbatim downstream; nothing is inferred, rephrased, or dropped.

---

## Entity: Structured Brief (human-entered, via the extended CLI form)

The full `brief_schema_v3` field set the human fills. Captured by the extended `ask_questions`.

| Field | Bucket | Type | Notes |
|-------|--------|------|-------|
| `asset_type` | A | string | already captured |
| `format_size` | A | string (e.g. `60x40cm`) | **NEW capture** (currently dropped) |
| `usage_context` | B | string | now human-settable (was derived from asset_type) |
| `audience` | B | string | now human-settable (was defaulted) |
| `vibe.formality` / `vibe.playfulness` / `vibe.warmth` | D | int 0-10 | already captured |
| `logo_treatment` | D | enum | already captured |
| `brand_strictness` | D | enum | already captured |
| `occasion` | — | string | already captured |
| `reference_image` + `reference_relationship` | ref | path + enum | already captured |
| `mandatory_elements` | C | list[string] | **NEW capture** (currently dropped; e.g. `分别画叉`) |
| `forbidden_elements` | C | list[string] | **NEW capture** (currently dropped) |
| `signs[].messages` / `signs[].hero_icon` | C | list / string | already captured (per-sign) |
| `brand` | — | string (CLI arg) | the human picks; assets load from brand data |

**Validation**: every entered value is recorded verbatim. Blank optional fields are recorded empty
(honest null), never invented. No agent transforms any value.

---

## Entity: Conductor Inputs (emitted JSON — the lossless brief image)

The artifact the conductor already consumes (`--inputs`), extended with three campaign-level
top-level fields. Backward-compatible (new fields optional).

```json
{
  "asset_type": "手举牌 hand-held event sign",
  "format_size": "60x40cm",
  "reference_image": "...",
  "reference_relationship": "template — extend this series",
  "mandatory_elements": ["分别画叉", "设计两种样式"],
  "forbidden_elements": [],
  "context": { "usage_context": "...", "audience": "...", "vibe": {...},
               "logo_treatment": "omit", "brand_strictness": "...", "occasion": "..." },
  "signs": [ { "id": "s1", "messages": ["..."], "hero_icon": null }, ... ]
}
```

**Rules (falsifiable)**:
- The sign count equals the brief's (no collapsing 6 → 2).
- Every entered field appears verbatim (FR-002).
- `format_size`, `mandatory_elements`, `forbidden_elements` are present when entered.

---

## Entity: Size Resolution (`format_size.resolve_size` output)

| Field | Type | Rule |
|-------|------|------|
| `requested_size` | string | echo of `format_size` |
| `width` / `height` | int | resolved gpt-image-2 pixel size; BOTH multiples of 16 |
| `orientation` | enum | `landscape` / `portrait` / `square`, from width vs height |
| `aspect_requested` | float | from the physical size (after clamp to [1/3, 3]) |
| `aspect_resolved` | float | width / height of the resolved pixel size |
| `aspect_delta` | float | |aspect_resolved − aspect_requested|; near 0 for clean aspects |
| `pixels` | int | width × height; within [655_360, 8_294_400] |
| `target_area` | int | the area the resolver aims for; defaults to 1_572_864 (1536x1024 ≈ 1.57 MP), configurable |
| `note` | string \| null | honest-null note (unparseable → default size) |
| `needs_review` | bool | true when the requested aspect was clamped (> 3:1) |

**Constraints (the valid gpt-image-2 set, a continuum — NOT three fixed canvases)**: both edges
multiples of 16; max edge ≤ 3840; aspect ≤ 3:1; total pixels in [655_360, 8_294_400]. The resolver
returns the valid size preserving the (clamped) aspect that sits NEAREST `target_area` (default the
proven 1536x1024 operating point, NOT the hard floor). With the default target: 3:2 → 1536x1024,
portrait → 1024x1536, 1:1 → ~1248x1248, 3:1 → ~2160x720. `canvas_wh = (width, height)` is threaded
to both generation and the fit clamp. Print resolution is out of reach by design (draft only).

---

## Entity: Per-sign Composition (extended)

The existing `composition.json` (feature 001) gains the campaign elements so they reach the prompt
and the manifest/review.

| Field | Type | Source |
|-------|------|--------|
| (existing) `chosen_icon` / `chosen_archetype` / `text_zone` / `needs_review` | — | feature 001 |
| `mandatory_elements` | list[string] | campaign inputs (verbatim) |
| `forbidden_elements` | list[string] | campaign inputs (verbatim) |

---

## Entity: Run Manifest (extended)

`conductor_manifest.json` gains a faithful record of the previously-dropped fields.

| Field | Type | Rule |
|-------|------|------|
| `format_size` | string | verbatim from inputs |
| `size_resolution` | object | the Size Resolution (width/height + orientation + aspect_delta + note + needs_review) |
| `mandatory_elements` | list[string] | verbatim |
| `forbidden_elements` | list[string] | verbatim |
| `brief_fields_received` | object | the full inputs echoed (the "what the pipeline actually got") |

**Rules**: SC-002 — `mandatory_elements` and `format_size` appear in the manifest AND the
generation prompt/spec. A `mandatory_elements` ∩ `forbidden_elements` conflict sets a campaign-level
`needs_review` with the reason (constitution §V).

---

## Entity: Run Review Bundle (`review.py` output)

A read-only digest assembled from existing artifacts; nothing recomputed.

| Field (per sign) | Source artifact |
|------------------|-----------------|
| output image path (final.png / generated.png) | `sign_*/` |
| chosen icon / layout archetype / reserved text_zone | `sign_*/composition.json` |
| compliance summary (licensed / non-compliant) | `sign_*/final.png.compliance.json` |
| `needs_review` + reason | `sign_*/composition.json` + `run_manifest.json` |
| inputs the pipeline received | `conductor_manifest.json.brief_fields_received` / `inputs.json` |
| campaign mandatory / forbidden / format_size / orientation | `conductor_manifest.json` |

Also written to `review.md` in the run dir.

---

## Falsifiable properties (seed the tests; constitution §III)

- `resolve_size(...)` invariants: for any valid brief size the resolved width and height are
  multiples of 16, max edge ≤ 3840, `pixels` in [655_360, 8_294_400], and `aspect_resolved` within
  tolerance of the requested aspect. With the DEFAULT target area: `"60x40cm"` (3:2) → `1536x1024`
  (landscape); `"40x60cm"` (2:3) → `1024x1536` (portrait); `"50x50cm"` (1:1) → ~`1248x1248` (square);
  a >3:1 banner → clamped to 3:1 + `needs_review`; a <1:3 extreme-portrait → clamped to 1:3 +
  `needs_review` (symmetric); `"garbage"` → a default size + non-null `note`.
- A brief with messages, `mandatory_elements`, `format_size`, and 6 signs produces inputs with 6
  signs and every field verbatim (none dropped, none rephrased).
- A dry-run of a brief containing `分别画叉` + `60x40cm` yields: the plan/manifest records both, and
  the kit `scene_author --explain` (or the assembled prompt) contains `分别画叉`.
- The conductor runs from a pre-written inputs JSON carrying the new fields with NO form (standalone).
- The review digest over a synthetic run dir lists each sign's image + icon + archetype + text_zone
  + needs_review.
- A `mandatory_elements` ∩ `forbidden_elements` conflict sets `needs_review` (not silently resolved).
