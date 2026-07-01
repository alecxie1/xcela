# Data Model: Lossless Brief (012)

**Phase 1 output.** No new entities, no schema changes; the brief's JSON contract is unchanged.
Deltas are to which fields FLOW and to the form surface.

## 1. Brief (inputs JSON)

| Field | Before | After |
|---|---|---|
| `asset_type` | recorded; inert on thin | flows verbatim into the thin prompt's SCENE section |
| `context.occasion` | recorded; inert on thin | flows verbatim into the SCENE section |
| `context.audience` | form control; inert | NO form control; still accepted + recorded (provenance) |
| `context.vibe.warmth` | form control; inert | NO form control; still accepted + recorded (provenance) |
| `signs[].hero_icon` | no form control; inert on thin | unchanged (writer tolerance only) |
| `reference_relationship` | free text, lossy keyword bucketing | form submits one of `extend` / `match style` / `mood`; engine normalization unchanged (legacy JSON still lenient) |
| form-state `style_notes` | nudge-only | union of the new `design_notes` field and any nudge, ";"-joined by the frontend; rides the existing form JSON -> runner -> `--style-notes` channel (NOT part of inputs.json, unchanged) |

**Validation rules**: none added. Empty strings behave as absent everywhere (honest null).

## 2. Thin prompt (assembled text)

New conditional section, after the opener, before the HEADLINE block:

```
SCENE / SUBJECT (compositional context ONLY, not text: no words from this section may be
painted anywhere on the asset):
  Asset: <asset_type verbatim>
  Occasion: <occasion verbatim>
```

- Each line renders only when its field is non-empty; the whole section is ABSENT when both are
  empty (byte-identity, FR-003).
- Every other section (openers, headline guard, register directive, colors, logo, elements,
  binding rules, negatives) byte-unchanged.
- The binding design-rules block is unchanged in format; it now also receives first-run notes.

## 3. Form surface (index.html)

| Control | Before | After |
|---|---|---|
| audience input | present | removed |
| warmth slider | present | removed |
| reference_relationship | free-text input | 3-option select (extend / match style / mood), described in plain language |
| design notes | absent (nudge-only) | textarea, flows to the binding block on first run |
| message label | "Sign message line(s) (one per line, verbatim)" | asset-generic: the exact text rendered verbatim on the asset, the only words allowed; no "sign" era wording |

## 4. CLI surface (scene_author, thin route only)

Two new optional flags: `--asset-type <str>`, `--occasion <str>`. Absent flags = absent section.
`_scene_author_thin_argv` passes them from the brief at BOTH conductor call sites.

## 5. State transitions

None. All changes are pure data flow; no new decision logic anywhere.
