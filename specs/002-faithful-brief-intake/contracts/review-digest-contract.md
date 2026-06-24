# Contract: review digest (`harness/review.py --run <dir>`)

A read-only, self-service digest that gives the human ONE place to render the eye verdict
(constitution §II). It recomputes nothing; it assembles existing `run_*/` artifacts.

## Output (printed + written to `<run_dir>/review.md`)

```
RUN: output/run_aia_<ts>            brand: aia
format_size: 60x40cm  ->  resolved: 1536x1024 (landscape, aspect 1.50)
mandatory_elements: 分别画叉; 设计两种样式      forbidden_elements: (none)

INPUTS THE PIPELINE RECEIVED: <echo of brief_fields_received> (6 signs)

PER SIGN:
  s1  image: sign_s1/final.png
      icon: money_bag   layout: protect_solid   text_zone: (0.12,0.52,0.76,0.34)
      compliance: 2 layer(s), 2 licensed, 0 non-compliant
      needs_review: false
  s2  image: sign_s2/final.png
      icon: megaphone_x layout: resist_panel    text_zone: (0.44,0.18,0.48,0.64)
      compliance: 2 licensed, 0 non-compliant
      needs_review: true  -> <reason>
  ...
```

## Rules (falsifiable)

1. For every sign in the run, the digest shows: the output image path, the chosen icon, the layout
   archetype, the reserved text zone, the compliance summary, and the `needs_review` flag + reason.
2. The digest shows the campaign fields the pipeline received (format_size, resolved orientation,
   mandatory/forbidden) and the inputs (`brief_fields_received`).
3. The digest READS ONLY; it never calls generation, placement, measurement, or compose_select
   (thin, FR-009). Missing artifacts (e.g. no final.png yet, or a run with no kit `composition.json`
   such as a future photo/poster run) are reported as such (honest null), not fabricated — the
   digest is asset-profile-AGNOSTIC and does not assume kit fields exist (D8).
4. No em-dashes in the printed/written digest (output rule).
