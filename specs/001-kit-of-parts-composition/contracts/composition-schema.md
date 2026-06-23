# Contract: `composition.json` (per-sign) + fit-to-zone result

Produced per message by `harness/compose_select.py` and the fit-to-zone clamp. Written to
`output/run_*/sign_*/composition.json`. This is the auditable record of every bespoke choice.

## Schema

```json
{
  "sign_id": "s1",
  "message": ["守住钱袋子", "护好幸福家"],
  "detected_mode": "protect",
  "chosen_icon": "money_bag",
  "icon_match_score": 2,
  "chosen_archetype": "protect_solid",
  "archetype_reused": false,
  "text_zone": {"x_frac": 0.12, "y_frac": 0.52, "w_frac": 0.76, "h_frac": 0.34},
  "fitted_type": {
    "fits": true,
    "final_size_px": 132,
    "rendered_box_frac": {"x_frac": 0.16, "y_frac": 0.55, "w_frac": 0.68, "h_frac": 0.28},
    "margin_px": 24,
    "min_size_px": 48
  },
  "needs_review": false,
  "needs_review_reason": null
}
```

## Match rule (pins the confidence floor; falsifiable)

`icon_match_score` = the count of distinct `meaning_cues` that occur as substrings of the joined
message text. An entry is eligible only if its score >= 1. The winner is the SINGLE highest-scoring
eligible entry. The match is honest-null when the top score is 0 (no cue hit) OR two+ entries tie
for the top score (ambiguous). No generative fallback decides the icon (D2).

## Honest-null cases (constitution V; falsifiable)

| Case | Fields |
|------|--------|
| No confident icon match (top score 0, or ambiguous tie) | `chosen_icon: null`, `detected_mode: null`, `needs_review: true`, reason names "no icon match" |
| Layout vocabulary exhausted | `archetype_reused: true`, `needs_review: true`, reason names the reused archetype |
| Headline cannot fit | `fitted_type.fits: false`, `final_size_px: null`, `needs_review: true`, reason names "text does not fit zone" |

## Rules (falsifiable)

1. When `fits: true`, `rendered_box_frac` lies strictly inside `text_zone` with at least
   `margin_px` on every edge.
2. `text_zone` equals the chosen archetype's `text_zone` (composition owns the zone; type is
   sized to it, FR-004).
3. Across a campaign, two signs with different `detected_mode` have different `chosen_archetype`
   while the vocabulary has supply (FR-003).
4. `needs_review` is the OR of the three honest-null cases above; `needs_review_reason` is
   human-readable and contains no em-dashes (output rule).
