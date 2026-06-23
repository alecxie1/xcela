# Contract: `kit_profile.json` (derived runtime kit)

Produced ONCE per campaign by `harness/kit.py` from the authored kit + `answer_keys/<brand>.json`
+ `register_profile.json` + (optional) `calibration.json`. Written to the run root and consumed
by every sign. The answer key WINS every conflict (clarified / D6).

## Schema

```json
{
  "brand": "aia",
  "register": "event_prop",
  "palette": [
    {"role": "primary", "hex": "#D31145", "source": "answer_key"},
    {"role": "secondary", "hex": "#C9A227", "source": "answer_key"},
    {"role": "background", "hex": "#FFFFFF", "source": "answer_key"}
  ],
  "font_role": "rounded display",
  "font_family": "汉仪元隆黑",
  "font_index_key": "75W",
  "frame_treatment": "gold frame + white stitched border, bevelled 3D",
  "anchors_held": ["primary_color"],
  "locks_flexed": ["logo:omit", "shape:die-cut", "palette:playful-accents"],
  "conflict_resolutions": [
    "palette.primary: reference dominant #E11D3A diverged from answer-key #D31145 -> answer key wins"
  ],
  "notes": []
}
```

## Rules (falsifiable)

1. Every `palette` entry whose role exists in the answer key carries the ANSWER-KEY hex, never
   the reference hex, and any such clash is recorded in `conflict_resolutions`.
2. `font_family` / `font_index_key` resolve from `answer_keys/<brand>.json` `typography.styles`
   (HARD lock); they are never overridden by the reference.
3. `frame_treatment` and other SOFT dimensions may come from reference `style_evidence` when
   there is no answer-key conflict.
4. If reference style extraction failed, `notes` records it and the profile is built answer-key-only
   (honest null, constitution V) rather than inventing style.
5. `anchors_held` / `locks_flexed` are carried through from `register_profile` / calibration
   (reconciliation preserved, constitution VI).
