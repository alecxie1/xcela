# Implementation Plan: Faithful Self-Service Brief Intake + Review

**Branch**: `002-faithful-brief-intake` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-faithful-brief-intake/spec.md`

## Summary

The pipeline was never tested on a faithful brief: intake was a lossy hand-translation (6 signs →
2; `分别画叉` / `设计两种样式` / size dropped) and the conductor contract is under-wired (it reads
neither `mandatory_elements` nor `format_size` — verified: **no consumer of either exists in
`harness/` or `register/`**). This feature fixes the INTAKE so a clean test becomes possible.

Technical approach (grounded in the actual code), THIN over the agent-free core:
(1) **Faithful intake** — extend the existing conductor CLI question form (`ask_questions`) to
capture every `brief_schema_v3` field, including the three it drops (`format_size`,
`mandatory_elements`, `forbidden_elements`), and emit the inputs JSON the conductor already
accepts, verbatim, with the real sign count. (2) **Wire the dropped fields** — a stdlib
`format_size` resolver computes the VALID gpt-image-2 pixel size (edges multiples of 16) that
PRESERVES the brief's aspect and sits NEAREST a configurable TARGET AREA (default ~1.57 MP, the
proven 1536x1024 operating point), honoring the real constraints (max edge ≤ 3840, aspect ≤ 3:1,
pixel budget 655,360–8,294,400); it does NOT snap to fixed canvases. The hardcoded `1536x1024` /
`CANVAS` become resolved-size-driven. `mandatory_elements` / `forbidden_elements` flow verbatim
into the generation prompt and the manifest. (3) **Self-service review** — a stdlib `review` CLI
prints a digest of the existing `run_*/` artifacts for the human's eye.

Two cross-cutting constraints shape the design: the new code is **asset-profile-AGNOSTIC** (no
`flat_graphic` / die-cut / landscape / 3:2 assumptions, so the future photo/poster dialect is pure
addition), and the agent-free core still runs headless from one CLI command with the surface
absent (test-proven). v1 stops at the plumbing: the human runs the paid pipeline and judges.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`; deps via `uv pip install --python .venv/bin/python`)

**Primary Dependencies**: stdlib only for intake/review/format_size (keeps the conductor
import-light, no API keys to import). Existing: Pillow (fit clamp, dimension-agnostic), openai
gpt-image-2 (generation, human-run), anthropic (authoring, unchanged).

**Storage**: Files. Inputs JSON (the conductor `--inputs` artifact), per-run artifacts under
`output/run_*/` (gitignored). Brand data in `answer_keys/` + `kits/` + `brands/`.

**Testing**: Falsifiable STRUCTURAL self-tests in the existing `test_*.py` style (stdlib;
`--dry-run` / `--explain` free surfaces). NO paid image generation in any test (the run is the
human's). Pixel quality is human-eye only (constitution §II).

**Target Platform**: Linux CLI pipeline (WSL2), stdlib-orchestrated subprocess tree rooted at
`harness/conductor.py`.

**Project Type**: Single project (CLI image-design pipeline). The "surface" is an extension of the
existing CLI form (clarified) + a CLI review digest. No new UI stack.

**Performance Goals**: Not latency-bound. Cost-bound: one paid gpt-image-2 call per sign, run by
the human. Intake / review / size resolution are deterministic and free.

**Output size model (gpt-image-2)**: a CONTINUUM of valid pixel sizes, not three fixed canvases.
Valid-size constraints: both edges multiples of 16px; max edge ≤ 3840px; aspect ratio ≤ 3:1; total
pixels between 655,360 and 8,294,400. The resolver returns the valid size that preserves the
brief's aspect and sits NEAREST a configurable TARGET AREA, defaulting to the proven 1536x1024
(~1.57 MP) operating point (anchoring to the baseline avoids a resolution regression and gives every
aspect the same quality/cost tier). The target is NOT the hard floor. With the default target,
3:2 → exactly 1536x1024 (a CONSEQUENCE, never hardcoded), portrait → 1024x1536, 1:1 → ~1248x1248,
3:1 → ~2160x720. Print resolution is out of reach by design (60x40cm @ 300DPI ≈ 7087x4724 > the
cap): the tool emits a valid-aspect DRAFT; the print-res vector rebuild is the human's step.

**Constraints**: Thin over the agent-free core (shell out to / import the existing CLI; never
reimplement generation/placement/measurement/judgment). ASSET-PROFILE-AGNOSTIC new code (no
flat_graphic / die-cut / orientation assumptions). Faithful verbatim passthrough (no agent
inference). Honest nulls + needs_review. Human input + taste gates preserved. Licensed-font
compliance manifest preserved. No em-dashes in user-facing text. No paid generation in tests.

**Scale/Scope**: v1 is AIA (the brand with ground truth); brand-general by design, proven later.
The reference AIA brief is 6 signs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | Intake is a human-filled form (no LLM parses a brief); review is a digest for the human's eye. Human at the input gate (fields, reference, brand) and the taste gate (review/approve/nudge). No agent translator, no agent judge. | PASS |
| II. Ground truth = the eye | Review surfaces real artifacts for the verdict; tests assert STRUCTURE only (verbatim fields, mandatory-in-prompt, size invariants + target, standalone path). No VLM self-score. | PASS |
| III. Falsifiable tests only | Each test asserts a VALUE a wrong build fails: every entered field verbatim in inputs+manifest; `分别画叉` in the generation prompt + manifest; the resolver returns ×16 edges preserving aspect nearest the default ~1.57 MP target (3:2 → 1536x1024, portrait → 1024x1536, 1:1 → ~1248x1248) and clamps >3:1 to needs_review; the conductor runs from a pre-written inputs JSON with the new fields. The current build drops all of these. | PASS |
| IV. Generalize, do not hand-tune | The size resolver, the mandatory/forbidden wiring, and the review digest are brand-general AND asset-profile-agnostic (no AIA / flat_graphic / orientation literals; the 1536x1024 target is a configurable default, not a hardcoded canvas). AIA is the proving brand. | PASS |
| V. Honest nulls | Unparseable `format_size` → default size + recorded note. Aspect > 3:1 → clamp to 3:1 + needs_review (never distorted). `mandatory_elements` ∩ `forbidden_elements` → needs_review. Blank optional field → recorded empty, never invented. | PASS |
| VI. Reconciliation per-dimension | Unchanged. `format_size` / `mandatory_elements` are GENERATION inputs, orthogonal to the register lane; the register reconciliation is untouched. | PASS |
| VII. Repo is durable; thin core | Surfaces thin over the existing CLI; the standalone path preserved and test-proven. One-module-one-test-one-commit decomposition. CLAUDE.md + SYSTEM_MAP updated in the commit that makes them stale. | PASS |

**Cost discipline**: No paid generation in any test; all wiring verified on `--dry-run` /
`--explain` / synthetic run dirs. The one paid run is the human's. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-faithful-brief-intake/
├── spec.md              # Feature spec (clarified 2026-06-23; target-area size model + profile-agnostic)
├── plan.md              # This file
├── research.md          # Phase 0: decisions (intake gap, size resolver, wiring, profile-agnostic)
├── data-model.md        # Phase 1: inputs + size-resolution + manifest + review entities
├── contracts/
│   ├── inputs-schema.md          # extended conductor inputs JSON
│   ├── manifest-contract.md      # what the run manifest must now record
│   ├── cli-contract.md           # intake extension + size resolver + scene_author --size + review CLI
│   └── review-digest-contract.md # what the review digest presents (profile-agnostic)
├── quickstart.md        # Phase 1: validation guide
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
harness/
├── conductor.py          # CHANGED: ask_questions captures ALL brief_schema_v3 fields incl. the 3
│                         #   dropped ones; inputs schema gains them top-level; resolve size once;
│                         #   thread --size + mandatory/forbidden to scene_author; manifest records
│                         #   them verbatim. Still emits flat_graphic (asset_type captured, not yet
│                         #   used to SELECT a profile — future spec); no orientation/profile assumptions.
├── scene_author.py       # CHANGED: kit mode reads --size (arbitrary WxH canvas) + mandatory/
│                         #   forbidden (from composition.json); assemble_kit_prompt injects them via
│                         #   a PROFILE-AGNOSTIC clause helper; generation size + fit-clamp canvas
│                         #   become resolved-size-driven (no hardcoded 1536x1024 / CANVAS).
├── format_size.py        # NEW (stdlib, profile-agnostic): resolve_size(format_size, target_area=...)
│                         #   -> valid gpt-image-2 pixel size preserving aspect nearest the target area;
│                         #   clamp >3:1 (needs_review); honest-null default.
├── prompt_elements.py    # NEW (stdlib, profile-agnostic): mandatory/forbidden -> verbatim prompt
│                         #   clause (REQUIRED elements + NEGATIVES), reusable by any render dialect.
├── review.py             # NEW (stdlib): review digest over run_*/ artifacts; degrades gracefully
│                         #   for non-kit / future photo runs (honest null on missing artifacts).
├── generate.py           # REUSED: size param already exists (no change).
└── composite_text.py     # REUSED: fit clamp already takes canvas_wh (dimension-agnostic; no change).

brief_schema_v3.json      # REUSED: already defines every field incl. the two unwired ones.
conductor_inputs_example.json  # UPDATED: add format_size + mandatory_elements for the AIA brief.

test_format_size.py       # NEW: size invariants + target-area landing (3:2->1536x1024, portrait->
                          #   1024x1536, 1:1->~1248x1248) + clamp>3:1 + honest-null default.
test_faithful_intake.py   # NEW: ask_questions captures every field verbatim into inputs (no drop).
test_brief_wiring.py      # NEW: dry-run a brief with 分别画叉 + 60x40cm -> plan/manifest/prompt carry them.
test_review.py            # NEW: digest over a synthetic run dir; graceful on missing artifacts.
test_conductor.py         # CHANGED: standalone proof (pre-written inputs JSON w/ new fields, NO form).
```

**Structure Decision**: Single project, extending the existing `harness/` subprocess tree. THREE
NEW stdlib modules — `format_size.py` (the size resolver: aspect-preserving, nearest a configurable
target area), `prompt_elements.py` (a profile-agnostic mandatory/forbidden clause builder so the
wiring is reusable by the future photo/poster dialect, not baked into the kit prompt), and
`review.py` (read-only digest). The intake extension and field wiring are edits to `conductor.py` +
`scene_author.py`. Nothing in generation/placement/measurement is rebuilt (FR-009). The new code
makes NO `flat_graphic` / orientation assumptions (asset_type captured faithfully but not yet used
to select a profile — explicit FUTURE spec), so the photo/poster path is pure addition. The
standalone CLI path is preserved and test-proven (FR-010 / SC-004).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
