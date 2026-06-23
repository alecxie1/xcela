# `kits/` — human-authored Kit of Parts (brand DATA)

Each `kits/<brand>.json` is the AUTHORED half of a brand's Kit of Parts for the
event-sign task (feature `001-kit-of-parts-composition`): a meaning→icon vocabulary and
a layout-archetype vocabulary. It is **committed brand data**, not generated output, so
unlike `brands/` (licensed fonts, gitignored) and `output/` (regenerable PNGs), this
directory IS tracked in git.

The human authors and refines a kit at the INPUT gate (constitution §I). The tool reads
it to deterministically PROPOSE a per-message icon + layout; the human approves or
overrides at the taste gate. No AIA-specific composition literals live in code (FR-008);
they all live here.

- **Schema + validation rules**: `specs/001-kit-of-parts-composition/contracts/kit-schema.md`
- **Loader/validator + derived runtime profile**: `harness/kit.py`
  (the DERIVED layer — palette, font, frame — is computed into `kit_profile.json` from
  `answer_keys/<brand>.json` + `register_profile`; the answer key wins every conflict).
- **Deterministic selection**: `harness/compose_select.py`

A kit that violates any schema rule fails loudly in `harness/kit.py` (no silent partial kit).
