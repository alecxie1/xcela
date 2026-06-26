# `brand_intake/` — brand-onboarding front-half (feature 005)

The path from a brand-guideline PDF to a human-VERIFIED lean `answer_keys/<brand>.json` that the
EXISTING thin route (`conductor.py --thin`) consumes UNCHANGED.

It is the BODY around proven ORGANS: it REUSES the deterministic extractors `extract_colors.py`
(OCR caption + pixel-cluster reconcile, `needs_review` on disagreement) and `extract_text_layer.py`
(text-layer fonts/names). It does NOT build on `analyze_brand_v3.py` (a hardcoded taichi scaffold
that exits 0 on failure).

Stdlib + the extractors' existing deps (PyMuPDF, rapidocr, Pillow). No new dependency, NO paid model
calls in the deterministic color/name path.

Stages (each fails loud or emits honest-null + a note, never green-on-empty):
- `page_finder.py` — PURE: `suggest_pages(pdf)` -> 1-INDEXED color/font/brand-name pages (regex over
  the text layer; the human confirms). Replaces the extractors' hardcoded `BRANDS` page dicts.
- `extract.py` — REUSE wrappers: `extract_brand_colors` (-> `extract_colors`) + `read_brand_names`.
- `assemble_key.py` — PURE: `build_lean_key(...)` -> the consumed-subset answer_key only.
- `validate_key.py` — PURE: `validate_lean_key(key)` -> FAILS LOUD on a missing primary color or a
  missing / unreal `logo_path` (contains the silent-taichi-logo landmine in `scene_author`).
- `intake.py` — the standalone CLI: suggest -> human CONFIRM pages -> extract -> human VERIFY gate
  (assign color roles, ACKNOWLEDGE every `needs_review`) -> validate -> write `answer_keys/<brand>.json`
  + place the logo under gitignored `brands/<brand>/`.

`typography.styles` is honest-null in v1 (hand-authored later; the font directive goes generic).
Spec / plan / contracts: `specs/005-brand-intake-front-half/`.
