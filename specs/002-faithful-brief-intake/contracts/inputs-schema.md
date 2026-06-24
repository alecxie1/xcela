# Contract: extended conductor inputs JSON (the lossless brief image)

The artifact the conductor already consumes (`--inputs`), extended with the three previously-dropped
campaign-level fields. Backward-compatible: the new fields are OPTIONAL; an absent field is treated
as empty (honest null), never invented.

## Schema (additions in **bold**)

```json
{
  "asset_type": "手举牌 hand-held event sign",
  "format_size": "60x40cm",                         // NEW (bucket A)
  "reference_image": "/path/to/ref.png",
  "reference_relationship": "template — extend this series",
  "mandatory_elements": ["分别画叉", "设计两种样式"],  // NEW (bucket C)
  "forbidden_elements": [],                          // NEW (bucket C)
  "context": {
    "usage_context": "held for photos / posed with",
    "audience": "general public",
    "vibe": { "formality": 2, "playfulness": 8, "warmth": 7 },
    "logo_treatment": "omit",
    "brand_strictness": "expressive departure",
    "occasion": "anti-fraud public-awareness campaign"
  },
  "signs": [
    { "id": "s1", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": null }
  ]
}
```

## Rules (falsifiable)

1. `format_size`, `mandatory_elements`, `forbidden_elements` are top-level (campaign-wide), echoing
   how `asset_type` already sits top-level.
2. `validate_inputs` continues to accept inputs WITHOUT the new fields (back-compat); when present,
   each is recorded verbatim and reaches the manifest.
3. The sign count equals the brief's; no collapsing (a 6-sign brief stays 6 signs).
4. No value is rephrased, reordered, or inferred (FR-003): literal strings pass through byte-for-byte.
5. `mandatory_elements` / `forbidden_elements` are lists of strings; an empty list is allowed and
   distinct from absent (both honest, neither fabricated).
