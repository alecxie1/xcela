# Contract: CLI surface (intake extension + size wiring + review)

All surfaces are THIN over the existing CLI core (FR-009). The agent-free core still runs from one
command with the surface absent (FR-010 / SC-004).

## `harness/conductor.py` (CHANGED)

- `ask_questions` (the intake form) captures EVERY `brief_schema_v3` field, adding prompts for:
  `format_size`, `mandatory_elements` (semicolon-separated, verbatim), `forbidden_elements`
  (semicolon-separated, verbatim), and making `usage_context` + `audience` explicit (defaulting to
  today's derived values). It writes the inputs JSON the conductor already accepts.
- Unchanged flags: `--brand`, `--inputs`, `--out`, `--dry-run`, `--no-approve`. No new REQUIRED flags.
- New behavior: resolve the pixel size ONCE from `format_size` via `format_size.resolve_size`;
  attach campaign `mandatory_elements` / `forbidden_elements` to each sign's `composition.json`;
  pass `--size <WxH>` to the kit `scene_author` invocation; record `format_size`, `size_resolution`,
  `mandatory_elements`, `forbidden_elements`, and `brief_fields_received` in the manifest. Still
  emits `flat_graphic` (asset_type is captured faithfully but NOT yet used to select a profile —
  future spec); the conductor bakes in no orientation/profile assumptions.
- `--dry-run` MUST surface the resolved size + the campaign elements in the plan/manifest WITHOUT
  any model call (free structural surface).

## `harness/format_size.py` (NEW, stdlib, profile-agnostic)

```
resolve_size(format_size: str, target_area: int = 1_572_864) -> {
  "requested_size": str, "width": int, "height": int,
  "orientation": "landscape|portrait|square",
  "aspect_requested": float, "aspect_resolved": float, "aspect_delta": float,
  "pixels": int, "target_area": int, "note": str | None, "needs_review": bool
}
```
- Parse two physical numbers; `aspect = w/h`; CLAMP to [1/3, 3] (clamp → `needs_review`).
- Compute the valid gpt-image-2 pixel size preserving the (clamped) aspect that sits NEAREST
  `target_area` (default 1_572_864 = 1536x1024 ≈ 1.57 MP, configurable, NOT the hard floor), under the
  real constraints: both edges multiples of 16; max edge ≤ 3840; pixels in [655_360, 8_294_400].
- Does NOT snap to fixed canvases. With the default target, 3:2 → 1536x1024, portrait → 1024x1536,
  1:1 → ~1248x1248, 3:1 → ~2160x720 (consequences of the target, never hardcoded).
- Unparseable / empty → a default valid size + a `note` (honest null).

## `harness/prompt_elements.py` (NEW, stdlib, profile-agnostic)

```
elements_clause(mandatory: list[str], forbidden: list[str]) -> str
```
- Builds a render-dialect-NEUTRAL clause: a VERBATIM "REQUIRED elements" list + a "NEGATIVES" list.
- No flat_graphic / die-cut assumptions; callable by `assemble_kit_prompt` now and the future
  photo/poster assembler unchanged. Empty lists → empty clause (nothing fabricated).

## `harness/scene_author.py` (CHANGED — kit mode)

- New flag `--size <WxH>` (default `1536x1024` for back-compat). Kit mode uses it for
  `generate_variant(size=...)` AND derives `canvas_wh = (W, H)` from it for `compose_kit_headline`
  (replacing the hardcoded `CANVAS`). Arbitrary valid sizes work (the fit clamp is dimension-agnostic).
- `assemble_kit_prompt` injects the campaign elements by calling `prompt_elements.elements_clause`
  with the composition's `mandatory_elements` / `forbidden_elements` (verbatim). The clause builder
  is profile-agnostic so the future photo/poster assembler reuses it unchanged.
- `--explain` (already exits before any model call) MUST reflect the resolved size + that
  mandatory/forbidden are present in the prompt source.

## `harness/review.py` (NEW, stdlib)

```
.venv/bin/python harness/review.py --run output/run_aia_<ts>
```
- Reads `conductor_manifest.json`, each `sign_*/composition.json`, `sign_*/final.png(.compliance.json)`,
  `sign_*/run_manifest.json`. Prints a per-sign digest (image path, chosen icon, layout archetype,
  reserved text zone, compliance summary, needs_review + reason) plus the campaign fields
  (format_size, orientation, mandatory/forbidden) and the inputs the pipeline received.
- Writes `review.md` into the run dir. READS ONLY; recomputes nothing.

## Test surfaces (free; constitution cost discipline)

```
.venv/bin/python test_format_size.py     # size invariants (x16 edges, aspect preserved, in budget, clamp>3:1)
.venv/bin/python test_faithful_intake.py # ask_questions captures every field verbatim into inputs
.venv/bin/python test_brief_wiring.py    # dry-run: 分别画叉 + 60x40cm in plan/manifest/prompt
.venv/bin/python test_review.py          # digest over a synthetic run dir
.venv/bin/python test_conductor.py       # standalone proof + existing checks
```
No paid generation in any test. The one paid run is the human's.
