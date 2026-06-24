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
    { "id": "s1", "messages": ["守住钱袋子", "护好幸福家"], "hero_icon": null },
    { "id": "s5", "messages": ["警惕高息诱惑"], "hero_icon": null,
      "mandatory_elements": ["分别画叉"] }   // NEW (per-sign; this sign only)
  ]
}
```

## Per-sign elements (002 delta)

A `signs[]` item MAY ALSO carry `mandatory_elements` and/or `forbidden_elements` (each an OPTIONAL
list[string]; this sign only). The EFFECTIVE elements for a sign are the order-preserving union of
the campaign-level list (applies to all signs) and that sign's own list, exact-duplicate strings
dropped, campaign first. So a campaign with `mandatory_elements: []` and only s5/s6 carrying
`["分别画叉"]` puts `分别画叉` on s5 and s6 ONLY — not on s1-s4. This is what lets Lily's `分别画叉`
(draw an X) apply to just the scam-type signs, the lossy-intake failure one level up.

## Rules (falsifiable)

1. `format_size`, `mandatory_elements`, `forbidden_elements` are top-level (campaign-wide), echoing
   how `asset_type` already sits top-level.
2. `validate_inputs` continues to accept inputs WITHOUT the new fields (back-compat); when present,
   each is recorded verbatim and reaches the manifest.
3. The sign count equals the brief's; no collapsing (a 6-sign brief stays 6 signs).
4. No value is rephrased, reordered, or inferred (FR-003): literal strings pass through byte-for-byte.
5. `mandatory_elements` / `forbidden_elements` are lists of strings; an empty list is allowed and
   distinct from absent (both honest, neither fabricated).
6. Per-sign `mandatory_elements` / `forbidden_elements` (OPTIONAL) MUST be lists of strings when
   present (`validate_inputs` raises `SystemExit` otherwise); absent is fine and unchanged from today.
   The effective per-sign list = order-preserving, de-duplicated union of campaign ++ that sign's.
7. If a sign's effective mandatory ∩ effective forbidden is non-empty, that sign is flagged
   `needs_review` with a reason naming the item(s) (constitution §V); never silently resolved.
