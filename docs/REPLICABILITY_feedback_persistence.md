# Replicability Design Note — Feedback Persistence (2026-06-11)

**Alec's insight (mid-batch):** applying 2 client feedback rules via `--style-notes` is a
SPECIAL CASE for the AIA job. The goal is a one-size-fits-all tool. Re-typing per-job
feedback does not generalize.

## The resolution: sort feedback by NATURE, persist it by SCOPE

Feedback is not monolithic. Each rule is one of two kinds:

1. **Universal design law** → belongs as a DEFAULT in the asset profile (e.g. flat_graphic).
   - Example: 突出文字主旨 (text is host, graphics guest) — true for almost all informational signage.
   - Action: candidate to bake into ASSET_PROFILES["flat_graphic"] as a soft default.

2. **Brand / client taste** → belongs in a PERSISTENT PER-BRAND style profile, NOT a global default.
   - Example: 形状可以变异 (organic, non-rigid shapes) — AIA's stated taste here, but a bank or
     law firm might demand rigid geometry. NOT universal.
   - Action: store in answer_keys/<brand>.json under a new "style_profile" key, auto-loaded by
     scene_author every run for that brand. Type once → applies forever, that brand only.

## The architecture (the real "one size fits all")
"One size fits all" does NOT mean identical rules for every job. It means:
- STABLE SLOTS (the tier-3 schema + asset profiles) that any brand fits into, AND
- PER-BRAND PERSISTENCE so each brand's accumulated preferences/feedback auto-apply.

The tool generalizes via STRUCTURE, not via a single universal ruleset.

## Feedback lifecycle (target design)
client review → critique → sort (universal vs brand-taste) →
  universal → asset-profile default (helps ALL brands)
  brand-taste → answer_keys/<brand>.json:style_profile (helps THIS brand, every future job)
→ next job for that brand auto-loads style_profile, no re-typing.

## Build tasks (optimizations, NOT blockers)
1. Add `style_profile` (list[str]) to answer-key schema; scene_author auto-loads + merges with
   any per-run --style-notes (run-specific overrides/additions on top of persistent brand prefs).
2. Seed answer_keys/aia.json:style_profile with the 2 AIA rules from this round.
3. Evaluate moving 突出文字主旨 (text-primary) into flat_graphic profile default (universal).
4. Future: "N distinct directions" mode for multi-variation asks (replaces manual must_include
   nudging for variation-2 — see batch note).

## For THIS batch (decision)
All 6 AIA signs are ONE campaign with ONE set of client feedback → apply both style-notes
consistently across the whole batch. Correct and consistent. The persistence refactor is for
FUTURE jobs/brands, and does not block shipping this campaign.
