# Inbox brief 011 — render/asset-aware register (stop flat-vector-era `event_prop` leaking into photographic marketing)

## The bug (observed, run_CJXQ_20260701_112628)
A designer picked **render_style = photographic**, **asset_type = "marketing instagram social post"**,
usage_context = "marketing promotional media", brand vibe formality=2 / playfulness=9. The register came
out **`event_prop`**, so the (asset_profile x register) opener chose the "hand-held event prop" framing.
On the photo route that means the prompt frames a real *photographed hand-held prop people pose with* —
the opposite of a marketing social post.

## Root cause (verified in code)
1. `harness/conductor.py::build_subfields` (:144-149) passes `{asset_type, **context}` to the register
   engine. It does **NOT** pass `render_style`. So `register/derive_register.py` is BLIND to whether the
   user asked for a photograph vs a flat graphic.
2. `derive_register` (:95-98) has a vibe override: `base=="marketing" and formality<=3 and playfulness>=7
   => event_prop`. This is the flat-vector / event-sign-era assumption — "playful + informal brand ⇒
   grabbable die-cut prop". It fires for ANY asset, including a photographic marketing post.
3. Contributing: "marketing promotional media" / "instagram" / "social" / "promotional" match NO row in
   `USAGE_RULES` (:23-28), so they fall to the `marketing` default — correct base, but then the override
   flips it.

## The fix (the reconciliation core: DIRECTION must respect what's being MADE)
`event_prop` is a *flat, hand-held, die-cut* register. It should never be inferred for a **photographic**
asset via the soft vibe heuristic. A genuine photo-prop is still expressible — but only through an EXPLICIT
hard signal (a usage_context event_prop keyword like "held for photos"), never via the playful-vibe guess.

Scope (thin route is where render_style lives today; keep it minimal + generalizing):
- **B1 (primary):** thread `render_style` into the register engine and GATE the marketing→event_prop vibe
  override so it does not fire for photographic renders. `render_style` is a soft DIRECTION input; the
  explicit usage_context event_prop keywords remain a hard signal that still wins (a photographed prop is
  legitimate when the human says so outright).
- **B2 (defensive):** add marketing coverage to `USAGE_RULES` ("marketing", "social", "instagram",
  "promotional") so common marketing usage strings match a rule explicitly instead of relying on default.
- Record the gate decision in `_derivation_trace` (falsifiable, inspectable — constitution §III).

## Out of scope
- The legacy render-and-scrub / kit paths (they stay flat_graphic; asset_profile is already fixed there).
- Any change to the opener matrix itself (009 already branches correctly on asset_profile x register — the
  bug is the WRONG register feeding it, not the matrix).
- asset_type-keyword-driven register inference (leave to a later feature if needed; render_style is the
  clean, already-plumbed signal).

## Falsifiable test targets (no paid calls)
- photographic + playful/informal vibe + no event keyword ⇒ register == `marketing` (NOT event_prop).
- flat_graphic + same vibe ⇒ register == `event_prop` (the old behavior is preserved for flat).
- photographic + explicit usage_context "held for photos" ⇒ still `event_prop` (hard signal wins).
- `_derivation_trace` names the render gate when it suppresses the override.
- build_subfields carries render_style through to subfields.json.
- The prior register suites + 009 render_modes stay green.

## Eye-gate (load-bearing, deferred)
One photographic marketing run judged by the human eye: the opener reads as a marketing post, not a prop.
