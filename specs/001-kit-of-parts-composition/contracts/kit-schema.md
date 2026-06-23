# Contract: `kits/<brand>.json` (authored kit vocabulary)

Human-authored brand DATA. The ONLY place brand-specific composition literals live (FR-008).
Loaded + validated by `harness/kit.py`. A wrong/invalid kit must fail validation loudly, not
silently degrade.

## Schema

```json
{
  "brand": "aia",
  "modes": ["protect", "warn", "resist"],
  "accent_vocabulary": ["diamond", "star", "lightning", "dot"],
  "icon_vocabulary": [
    {
      "id": "money_bag",
      "meaning_cues": ["钱袋", "钱袋子", "储蓄", "存款", "守住钱"],
      "mode": "protect",
      "icon_description": "rounded flat-vector money bag with a ¥ mark, bevelled, kit palette",
      "asset_path": null
    },
    {
      "id": "megaphone_x",
      "meaning_cues": ["非法金融", "高息", "诈骗", "诱惑", "抵制"],
      "mode": "resist",
      "icon_description": "megaphone with a bold red X overlay, flat-vector, kit palette",
      "asset_path": null
    }
  ],
  "layout_vocabulary": [
    {
      "id": "protect_solid",
      "modes": ["protect"],
      "panel_treatment": "warm solid crimson field, gold frame, white stitched border",
      "icon_zone": {"x_frac": 0.34, "y_frac": 0.10, "w_frac": 0.32, "h_frac": 0.34},
      "text_zone": {"x_frac": 0.12, "y_frac": 0.52, "w_frac": 0.76, "h_frac": 0.34},
      "accent_treatment": "gold diamonds in corners"
    },
    {
      "id": "warn_panel",
      "modes": ["warn", "resist"],
      "panel_treatment": "white panel with red headline for alarm, gold frame",
      "icon_zone": {"x_frac": 0.10, "y_frac": 0.12, "w_frac": 0.28, "h_frac": 0.30},
      "text_zone": {"x_frac": 0.42, "y_frac": 0.18, "w_frac": 0.48, "h_frac": 0.64},
      "accent_treatment": "lightning accents"
    }
  ],
  "_authored_by": "human",
  "_authored_date": "2026-06-22"
}
```

## Validation rules (enforced by `harness/kit.py`; falsifiable)

1. `brand` matches the answer-key brand id passed to the conductor.
2. `modes` non-empty; every `icon_vocabulary[].mode` and every `layout_vocabulary[].modes[]`
   element is in `modes`.
3. `icon_vocabulary` non-empty; each entry has unique `id` and non-empty `meaning_cues`.
4. No two icon entries share an identical `meaning_cues` set.
5. `layout_vocabulary` has >= 2 entries with unique `id`s.
6. For EVERY archetype, `icon_zone` and `text_zone` are within [0,1] and DO NOT overlap.
7. Every declared `mode` is served by at least one archetype (so any matched icon has a layout).

A kit failing any rule → `harness/kit.py` raises with the specific rule violated (no silent
fallback to a partial kit).
