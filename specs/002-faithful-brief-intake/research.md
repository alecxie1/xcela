# Phase 0 Research: Faithful Self-Service Brief Intake + Review

All decisions are grounded in the ACTUAL code (verified this session): `ask_questions`,
`validate_inputs`, `build_subfields`, `build_intent`, `build_compositions`, the kit route, and
`scene_author` kit mode. The spec's "Note for /speckit-plan" required this reuse check.

---

## D1. The verified intake gap (what is dropped today)

**Finding**: `harness/conductor.py` `ask_questions` captures asset_type, reference + relationship,
formality, playfulness, logo_treatment, brand_strictness, occasion (audience + usage_context are
defaulted/derived, not asked). It does NOT capture `format_size`, `mandatory_elements`, or
`forbidden_elements`. A repo-wide grep confirms **no consumer of `format_size` /
`mandatory_elements` / `forbidden_elements` exists in `harness/` or `register/`** — they have zero
path to generation. Generation size is hardcoded `1536x1024` in both `scene_author` paths, and
`CANVAS = (1536, 1024)` is hardcoded for the fit clamp.

**Decision**: Extend `ask_questions` to capture EVERY `brief_schema_v3` field, asking the three
dropped fields plus surfacing audience + usage_context as explicit (defaulting to today's derived
values). The form writes the inputs JSON the conductor already accepts. This is the smallest change
that makes intake lossless and keeps the surface thin over the core.

**Alternatives considered**: a separate intake tool that re-implements the question flow —
rejected (duplicates `ask_questions`, drifts from the core). A free-text brief parser — rejected on
principle (constitution §I; re-introduces the translator confound).

---

## D2. Where the new fields live in the inputs JSON

**Decision**: Add three CAMPAIGN-LEVEL top-level fields to the conductor inputs:
`format_size` (string, e.g. `"60x40cm"`), `mandatory_elements` (list of strings), and
`forbidden_elements` (list of strings) — mirroring how `asset_type` already sits top-level.
`audience` + `usage_context` remain in `context` (bucket B) but become human-settable. Per-sign
content (`messages`, `hero_icon`) is unchanged.

**Rationale**: `brief_schema_v3` places `format_size` in bucket A (artifact-level) and
`mandatory_elements` / `forbidden_elements` in bucket C (content-level, campaign-wide for the AIA
brief: `分别画叉` applies to every sign). Campaign-level keeps the wiring simple and matches the
brief. `validate_inputs` stays backward-compatible (the fields are optional; absent → empty/None).

**Alternatives considered**: per-sign `mandatory_elements` — deferred; the AIA brief is
campaign-wide, and per-sign can be added later without breaking the schema.

---

## D3. `format_size` → a valid gpt-image-2 pixel size (FR-005, revised by spec edit)

**Decision**: A new stdlib `harness/format_size.py` with
`resolve_size(format_size, target_area=1_572_864) -> {requested_size, width, height, orientation,
aspect_requested, aspect_resolved, aspect_delta, pixels, target_area, note, needs_review}`. It does
NOT snap to three fixed canvases; it anchors to a configurable target area. The algorithm:
1. Parse the two physical numbers (e.g. `60x40cm` → 60, 40); honest-null default on unparseable.
2. `aspect = w_phys / h_phys`. CLAMP to `[1/3, 3]`; if clamped, set `needs_review` + record the
   delta (an aspect beyond 3:1 is clamped, never distorted).
3. Compute the valid pixel size that preserves the (clamped) aspect and sits NEAREST a configurable
   `target_area` (default 1,572,864 px = 1536x1024 ≈ 1.57 MP), under the real gpt-image-2
   constraints: both edges multiples of 16; max edge ≤ 3840; total pixels in `[655_360, 8_294_400]`.
   (Scale the aspect so area ≈ target_area, round each edge to a multiple of 16, clamp into budget,
   then record `aspect_resolved` + `aspect_delta`.)
4. `orientation` = landscape / portrait / square from width vs height.
5. Record `requested_size`, resolved `width`×`height`, orientation, both aspects + delta, pixels,
   `target_area`, and any `note` / `needs_review`.

**Rationale**: The spec edit is explicit on two points: (a) the "3 fixed sizes" model is WRONG —
gpt-image-2 accepts a continuum; popular sizes are examples, not the allowed set. (b) The resolver
anchors to a TARGET AREA (default the proven 1536x1024 operating point), NOT the hard pixel floor —
the floor would land 3:2 at ~1008x672, a resolution regression below every good AIA run. With the
default target, 3:2 lands EXACTLY on 1536x1024 as a consequence (never hardcoded), and every aspect
inherits the same ~1.57 MP quality/cost tier. The resolver is pure stdlib, importable by both the
conductor (manifest + the `--size WxH` it passes) and `scene_author` (generation size + fit-clamp
`canvas_wh`), computed once and threaded. Print resolution is out of reach by design (cap ~8.29 MP;
60x40cm @ 300DPI ≈ 33 MP) — the tool emits a valid-aspect DRAFT.

**Falsifiable properties**: edges multiples of 16, max edge ≤ 3840, pixels in budget,
`aspect_resolved` within tolerance of the (clamped) requested aspect, orientation matching the
aspect's sign, AND with the default target: 3:2 → 1536x1024, portrait → 1024x1536, 1:1 → ~1248x1248,
3:1 → ~2160x720. A >3:1 banner clamps to 3:1 with `needs_review`. Unparseable → default size +
non-null `note`.

**Alternatives considered**: snap to three fixed orientations — REJECTED by the spec edit. SMALLEST
valid preserving aspect (the min-budget floor) — REJECTED: it regresses 3:2 to ~1008x672, below the
proven baseline. A human-picked orientation field — rejected earlier (adds a field; size and
orientation could disagree).

---

## D4. `mandatory_elements` / `forbidden_elements` → the generation prompt (FR-004)

**Decision**: The conductor attaches the campaign `mandatory_elements` + `forbidden_elements` to
each sign's `composition.json` (verbatim). `scene_author` kit mode reads them and
`assemble_kit_prompt` injects them: mandatory elements as an explicit REQUIRED-elements clause
(e.g. "Each sign MUST include: 分别画叉 ..."), forbidden elements appended to the existing NEGATIVES
clause. The run manifest echoes both verbatim.

**Rationale**: `composition.json` is already the per-sign input to `scene_author` kit mode and a
source the manifest + review read, so attaching the campaign elements there is the thinnest wiring
(no new argv plumbing per sign). The actual prompt clause is built by a NEW profile-agnostic helper
`harness/prompt_elements.py` (`elements_clause(mandatory, forbidden) -> str`) so the SAME verbatim
injection is reusable by the future photo/poster dialect, not baked into the kit prompt (D8).
Verbatim injection honors faithful passthrough (FR-003): the tool places the literal text, it does
not rephrase or interpret it (so `设计两种样式` is rendered as the instruction it is, never expanded
into N generations). Falsifiable: a brief with `分别画叉` yields a generation prompt / composite spec
containing that string, and the manifest records it; absent → nothing fabricated (honest null).

**Scope note**: v1's proving brand (AIA) uses the KIT route, so `assemble_kit_prompt` calls
`elements_clause`. The legacy route gets the same call for parity, but its falsifiable test rides the
kit route (the only one with a v1 brand). The helper itself is profile-agnostic, so the future
photo/poster path calls it unchanged.

**Alternatives considered**: pass via new `scene_author` argv flags — also fine, but
`composition.json` already carries per-sign data and is read by review, so it is the lower-friction
home.

---

## D5. Resolved size threaded to generation + fit (the de-hardcoding)

**Decision**: The conductor resolves the pixel size ONCE (D3) and passes `--size <WxH>` to the kit
`scene_author` invocation. `scene_author` kit mode uses that size for `generate_variant(size=...)`
and derives `canvas_wh` from it for `compose_kit_headline` (replacing the hardcoded `CANVAS`). The
manifest records `format_size` + the full size resolution.

**Rationale**: Two hardcoded `1536x1024` sites + `CANVAS = (1536, 1024)` are the only blockers to
honoring `format_size`. Threading ONE resolved `WxH` removes all three consistently (generation and
the fit clamp MUST agree on canvas dimensions or the composited text mis-places). The fit clamp is
already dimension-agnostic (`fit_text_in_zone_frac(canvas_wh=...)` + fractional zones), so arbitrary
sizes work without touching it. Falsifiable: a portrait brief yields a portrait `WxH` (H > W) in the
scene_author `--explain` / manifest, and the fit clamp uses the matching canvas.

**Alternatives considered**: leave generation at 1536x1024 and only record size — rejected; FR-005
requires `format_size` to DRIVE the output dimensions, not just be logged.

---

## D6. Self-service review digest (FR-008, US3)

**Decision**: A new stdlib `harness/review.py` with `--run <run_dir>` that READS only and prints a
per-sign digest: the output image path (final.png / generated.png), the inputs the pipeline
actually received (from `conductor_manifest.json` / `inputs.json`), the composition picks (chosen
icon, layout archetype, reserved text zone from `sign_*/composition.json`), the compliance summary,
and every `needs_review` flag + reason. It also writes a `review.md` digest in the run dir.

**Rationale**: The clarified modality is "CLI / printed digest." Everything the review needs is
already written by the conductor + scene_author (`conductor_manifest.json`, per-sign
`composition.json`, `final.png(.compliance.json)`, `run_manifest.json`). The digest recomputes
nothing (thin, constitution §VII) and gives the human one place to render the eye verdict
(constitution §II). Falsifiable: over a synthetic run dir, the digest lists each sign's image +
icon + archetype + text_zone + any needs_review.

**Alternatives considered**: a local web gallery — rejected by the clarification (no new UI stack in
v1). Re-deriving picks in review — rejected (would duplicate compose_select; thin means read-only).

---

## D7. Standalone proof (FR-010 / SC-004)

**Decision**: The intake form only WRITES the inputs JSON; the conductor already runs headless from
`--inputs`. A test asserts the conductor accepts a pre-written inputs JSON containing the new fields
(`format_size`, `mandatory_elements`) and wires them, with NO form involved (dry-run). This is the
standalone proof: the surface is removable without breaking the core.

**Rationale**: Constitution §I/§VII (thin over the agent-free core; the core stands alone). The
existing `--inputs` + `--dry-run` path is exactly this surface; the test pins it.

---

## D8. Asset-profile-agnostic new code (spec edit)

**Decision**: The new 002 code — `format_size.py`, `prompt_elements.py`, the manifest additions, and
`review.py` — makes NO `flat_graphic` / die-cut / landscape / 3:2 assumptions:
- `format_size.py` is pure aspect math (any orientation falls out of the constraints).
- `prompt_elements.py` builds a render-dialect-neutral clause (REQUIRED elements + NEGATIVES) that
  any prompt assembler can call.
- `review.py` reads whatever artifacts a run wrote and degrades gracefully (honest null) when a run
  has no kit `composition.json` (e.g. a future photo/poster run), rather than assuming kit fields.
- `asset_type` is captured FAITHFULLY at intake and recorded, but 002 does NOT yet use it to SELECT
  a render profile — the conductor still emits `flat_graphic` and the `poster` / `photo` dialects
  stay stubbed.

**Rationale**: The spec edit makes photographic / realistic poster output (taichi, the AIA mother's
day poster) explicit FUTURE project scope. Baking flat-graphic assumptions into the new plumbing now
would force rework later. Keeping the new code profile-agnostic makes the future
`asset_type → asset_profile` + photo/poster dialect a PURE ADDITION (its own spec), not a refactor.
Falsifiable: the size resolver returns portrait and square sizes (not only landscape), and the
review digest does not crash on a run lacking kit composition fields.

**Out of scope (deferred, per the spec)**: wiring `asset_type` to actually select a profile, and
building the photo/poster render dialect. Future spec.

---

## Reuse summary (verified against code)

| Existing capability | File | Reused for |
|---------------------|------|-----------|
| `ask_questions` interactive form (injectable `ask`) | `harness/conductor.py` | D1 intake extension |
| `--inputs` load + `validate_inputs` + `--dry-run` plan | `harness/conductor.py` | D2 schema, D7 standalone |
| kit route: `build_compositions` + per-sign `composition.json` | `harness/conductor.py` | D4 mandatory/forbidden attach |
| kit mode + `assemble_kit_prompt` + `compose_kit_headline` | `harness/scene_author.py` | D4 injection, D5 canvas threading |
| `generate_variant(size=...)` | `harness/generate.py` | D5 size (already parameterized) |
| fit clamp `fit_text_in_zone_frac(canvas_wh=...)` | `harness/composite_text.py` | D5 canvas (already parameterized) |
| run artifacts (manifests, composition.json, compliance) | `output/run_*/` | D6 review digest |
| every brief field incl. the two unwired ones | `brief_schema_v3.json` | D1 field list |

| Genuinely NEW | Why nothing existing covers it |
|---------------|-------------------------------|
| `harness/format_size.py` | No size resolver exists; size is hardcoded `1536x1024` in 2 sites + `CANVAS` |
| `harness/prompt_elements.py` | No profile-agnostic mandatory/forbidden clause builder exists |
| `harness/review.py` | No review digest exists |
| intake capture of the 3 dropped fields + their wiring | No consumer of them exists anywhere (verified) |
