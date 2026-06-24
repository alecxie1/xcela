# Contract: single-sign inputs JSON (`inputs_writer` output)

The form writes the feature-002 conductor-inputs shape with EXACTLY ONE `signs[]` entry. The
authoritative field contract is `specs/002-faithful-brief-intake/contracts/inputs-schema.md`. The
stale repo-root `brief_schema.json` (subject / poster|banner / mood_shift) is NOT used.

## Shape

```json
{
  "asset_type": "手举牌 hand-held event sign",
  "format_size": "60x40cm",
  "reference_image": "/abs/path/ref.png",
  "reference_relationship": "template - extend this series",
  "mandatory_elements": ["分别画叉"],
  "forbidden_elements": [],
  "context": {
    "usage_context": "held for photos / posed with",
    "audience": "general public",
    "vibe": { "formality": 2, "playfulness": 8, "warmth": 7 },
    "logo_treatment": "omit",
    "brand_strictness": "expressive departure",
    "occasion": "anti-fraud public-awareness campaign"
  },
  "signs": [
    { "id": "s1", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": null,
      "mandatory_elements": [], "forbidden_elements": [] }
  ]
}
```

## Rules (falsifiable)

1. `len(signs) == 1` (single-sign invariant).
2. `messages`, `mandatory_elements`, and the three `vibe` integers equal the typed values
   byte-for-byte (no rephrase / reorder / inferred field, FR-003).
3. The output passes `conductor.validate_inputs` (back-compat with the real CLI).
4. A blank optional field is written empty (honest null), never invented.
5. `reference_image` is present (REQUIRED in v1); the form blocks Run otherwise.
