# Contract: run manifest additions

`conductor_manifest.json` must faithfully record the previously-dropped fields so SC-002 holds and
the review digest (and a human) can see exactly what the pipeline received.

## Additions

```json
{
  "...": "existing manifest fields unchanged",
  "format_size": "60x40cm",
  "size_resolution": {
    "requested_size": "60x40cm", "width": 1536, "height": 1024, "orientation": "landscape",
    "aspect_requested": 1.5, "aspect_resolved": 1.5, "aspect_delta": 0.0,
    "pixels": 1572864, "target_area": 1572864, "note": null, "needs_review": false
  },
  "mandatory_elements": ["分别画叉", "设计两种样式"],
  "forbidden_elements": [],
  "brief_fields_received": {
    "asset_type": "...", "format_size": "60x40cm", "context": { "...": "..." },
    "mandatory_elements": ["分别画叉", "..."], "signs": [ { "id": "s1", "messages": ["..."] } ]
  },
  "needs_review_campaign": null
}
```

## Rules (falsifiable)

1. `format_size`, `mandatory_elements`, `forbidden_elements` are recorded VERBATIM from the inputs;
   `size_resolution` is the computed Size Resolution (SC-002, half of it; the other half is presence
   in the generation prompt/spec). The 1536x1024 above is a CONSEQUENCE of the default ~1.57 MP target
   area for a 3:2 brief, not a hardcoded canvas — a different aspect or target yields a different size.
2. `brief_fields_received` is the inputs the conductor actually consumed (the "what the pipeline
   got" the review surfaces). It equals the inputs JSON (lossless).
3. A `mandatory_elements` ∩ `forbidden_elements` conflict sets `needs_review_campaign` to a
   human-readable reason (no em-dashes); the run continues (honest null, not a silent resolution).
4. When `format_size` is absent/unparseable, `size_resolution.note` explains the fallback (a default
   valid size); when the requested aspect exceeds 3:1, `size_resolution.needs_review` is true and the
   clamp is recorded. The size is never silently invented or distorted.
5. Existing non-negotiables in the per-sign records (compliance manifest, per-sign `needs_review`)
   are unchanged (SC-005).
