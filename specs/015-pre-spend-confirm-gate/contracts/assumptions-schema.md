# Contract: assumptions.json + gate_state.json

**Feature**: 015-pre-spend-confirm-gate

## `<run_dir>/assumptions.json`

Ordered list (pipeline order). Recomputed whole on every derive phase; never appended to.

```json
[
  {
    "id": "register_lane",
    "dimension": "job register (what kind of piece this is)",
    "assumed_value": "marketing (default: your usage words matched no known pattern)",
    "cause": {"input": "context.usage_context",
               "value": "goes viral on rednote",
               "reason": "unmatched"},
    "options": [
      {"label": "marketing piece",
       "writes": {"field": "context.usage_context", "value": "marketing"}},
      {"label": "hand-held event prop",
       "writes": {"field": "context.usage_context", "value": "held for photos"}},
      {"label": "formal piece",
       "writes": {"field": "context.usage_context", "value": "formal document"}}
    ],
    "source": "derive_register"
  },
  {
    "id": "format_size",
    "dimension": "output size",
    "assumed_value": "1536x1024 (could not parse \"about poster size\")",
    "cause": {"input": "format_size", "value": "about poster size", "reason": "unparseable"},
    "options": [
      {"label": "60x40cm landscape", "writes": {"field": "format_size", "value": "60x40cm"}},
      {"label": "40x60cm portrait",  "writes": {"field": "format_size", "value": "40x60cm"}},
      {"label": "square",            "writes": {"field": "format_size", "value": "50x50cm"}},
      {"label": "keep 1536x1024",    "writes": {"field": "format_size", "value": "1536x1024px"}}
    ],
    "source": "conductor"
  },
  {
    "id": "magnitude",
    "dimension": "style intensity (how far from corporate)",
    "assumed_value": "moderated event_prop defaults (no calibration available)",
    "cause": {"input": "reference_image", "value": null, "reason": "fallback"},
    "options": [
      {"label": "set directly",
       "writes": {"field": "context.vibe",
                   "value": {"formality": "<int 0-10>", "playfulness": "<int 0-10>"}}}
    ],
    "source": "derive_register"
  }
]
```

Rules:
- `reason` enum: `blank | unmatched | unparseable | clamped | fallback`.
- Every `writes.value` MUST round-trip: applying it and re-deriving equals a fresh run
  that had it from the start (asserted per shipped option, FR-006).
- `id` values are stable keys (`register_lane`, `format_size`, `magnitude`,
  `render_style`, `relationship_dial`); the UI keys controls off `id`, wording may evolve.
- Zero guesses -> `[]` (the gate then renders summary + confirm only, FR-008).
- No em-dashes in any `dimension` / `assumed_value` / `label` string (FR-013).

## `<run_dir>/gate_state.json`

```json
{
  "state": "awaiting_confirmation",
  "created": "2026-07-08T14:00:00",
  "updated": "2026-07-08T14:03:10",
  "answers_applied": [
    {"assumption_id": "register_lane", "chosen_label": "marketing piece",
     "written": {"field": "context.usage_context", "value": "marketing"},
     "at": "2026-07-08T14:03:10"}
  ],
  "confirmation": null
}
```

- `state` enum: `awaiting_confirmation | confirmed | generating | done` (see
  data-model.md state machine; abandonment is passive).
- On confirm, `confirmation` becomes
  `{"confirmed_prompt_sha": "<sha256>", "cost_stated": "$0.08", "confirmed_at": "..."}`.
- Written by: conductor derive phase (create/reset), server answer route
  (`answers_applied` append via the re-derive cycle), server confirm route
  (`confirmed`), conductor generate phase (`generating`, `done`, or reset on drift).
