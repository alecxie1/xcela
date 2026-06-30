# Contract: the (asset_profile x register) thin opener + negatives

`assemble_thin_prompt` speaks the right dialect per render mode and frames the asset per register. Brand
identity stays the HARD lock (unchanged blocks); only the opener + negatives change.

## Opener (verbatim text in research.md Decision 2)

`is_graphic = asset_profile == "flat_graphic"`; `is_event_prop = (register_profile or {}).get("inferred_register") == "event_prop"`.

- `is_graphic and is_event_prop` -> the EXISTING die-cut hand-held prop opener, BYTE-UNCHANGED.
- `is_graphic and not is_event_prop` -> the rewritten rectangular marketing poster opener (NO "hand-held
  event sign", no em-dash).
- `not is_graphic and is_event_prop` -> the new photographic hand-held event prop opener.
- `not is_graphic and not is_event_prop` -> the new photographic marketing poster opener.

## Negatives

- text guards (BOTH modes): `no gibberish or garbled text, no extra Chinese text beyond the headline above,
  no tagline, no watermark`.
- flat-only render clause (is_graphic): `no photographic shading, no 3D realism` prepended -> the flat
  NEGATIVES line is BYTE-IDENTICAL to today.

## Unchanged

`_primary_color_hex` + the register directive (magnitude/anchor), the headline-text block, the
mandatory/forbidden clause, the logo block, the reference-exemplar note, and the BRAND LOCK COLORS block
(feature 008). The slogan is still not injected.

## Falsifiable tests (`test_render_modes.py`, no paid calls)

- photo (asset_profile="photo"): the prompt CONTAINS photographic language ("PHOTOGRAPHIC" / "photographic
  realism") and does NOT contain "FLAT VECTOR" or "no photographic shading"; it STILL contains the text
  guards ("no extra Chinese", "no gibberish") and the verbatim headline. A build ignoring the profile fails.
- flat + marketing register (not event_prop): the opener does NOT contain "hand-held event sign" and reads
  as a rectangular poster ("rectangular", "poster/flyer"). A hard-coded-event-sign build fails.
- flat + event_prop: the opener contains "hand-held event photo-prop sign" + "die-cut" and the NEGATIVES
  line contains "no photographic shading" (byte-unchanged regression).
- photo + event_prop: a photographic hand-held prop opener (photographic language + prop framing); allowed
  (no error / no block).
