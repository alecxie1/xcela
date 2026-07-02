# Implementation Plan: Role-Tagged References (Style + Product)

**Branch**: `013-role-tagged-references` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-role-tagged-references/spec.md`

## Summary

Split the do-everything reference into roles. The STYLE reference keeps today's exact semantics
(required, drives calibration + dial + exemplar feed). PRODUCT references are new: 0..6 per-run
photos of the brand's actual products, uploaded on the form, saved into the run dir through the
shared `save_upload` home, threaded as a repeatable `--product-image` flag at BOTH conductor call
sites, appended to `generate_variant`'s existing multi-image list AFTER the current
[style, logo] prefix (prefix byte-stable), and bound by a conditional PRODUCT FIDELITY prompt
section. Zero product refs = prompt AND generation input list byte-identical to today.

**The brand-asset seam (operator direction honored)**: the tool already has TWO asset homes. The
logo is a BRAND-level asset: onboarding places it under `brands/<brand>/` (`persist.place_logo`),
the answer key's `logo_path` points at it, and `scene_author` resolves and feeds it on EVERY run.
Product shots in 013 are deliberately the OTHER kind: CAMPAIGN-level assets (this launch's
watermelon cups are not next month's mooncakes), so they ride per-run in the run dir like the
style reference, not in the brand key. The two homes compose in one place, the generation refs
list: [style(run), logo(brand), products(run)]. A durable brand-level PRODUCT LIBRARY (evergreen
hero shots picked at onboarding, reusable across campaigns) is a natural follow-on and is
explicitly deferred to the brand-key-enrichment feature (015 in the roadmap), where it would
reuse this feature's entire feed path and only change where the paths come from.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`), stdlib-only modules stay stdlib (the OpenAI client
is already a `generate.py` dependency); frontend stays no-framework HTML + vanilla JS

**Primary Dependencies**: none new. `generate_variant` already accepts a LIST of image paths and
feeds them all to `images.edit` (the proven multi-image mechanism this feature extends)

**Storage**: product uploads land in the run dir (`product_1.<ext>`..`product_N.<ext>`) beside
`reference.jpg`; brief gains an optional `product_images` list (paths); manifest records them

**Testing**: one new standalone self-test (`test_product_refs.py`): pure prompt/argv/parse
assertions + the stubbed-`run_step` execute pattern; form checks are greps (weakest gate,
declared); no paid calls

**Target Platform**: local Linux/WSL2, thin route only

**Project Type**: CLI pipeline + thin local web form

**Performance Goals**: N/A (same single generation call; more input images, zero extra spend)

**Constraints**: byte-identical prompt + generation refs when no product images (FR-004/SC-002);
calibration argv provably identical with/without products (FR-005/SC-003); cap = 6 product
images (1 style + 1 logo + 6 products = 8 inputs, comfortably inside the images.edit documented
16-image limit); over-cap is a visible form rejection, never truncation (FR-008)

**Scale/Scope**: 5 files edited (`generate.py` untouched), 1 new self-test, ~110 lines

## Constitution Check

*GATE: evaluated pre-Phase-0, re-checked post-Phase-1. All PASS.*

| Principle | Verdict | How |
|---|---|---|
| I. Agent-free, not human-free | PASS | A new INPUT gate: the human supplies product truth as files; no model analyzes, crops, or judges them; the tool only carries them through. |
| II. Eye is ground truth | PASS | Structure proves the images and the fidelity section REACH generation; whether the branded cups actually appear is SC-006, the paid CJXQ rerun judged by the operator. The spec is explicit that prompt obedience stays probabilistic. |
| III. Falsifiable tests | PASS | Values: the exact product paths in the executed argv and refs list (a plan-only or dropped-thread build fails); the no-products prompt and refs byte-identical to inlined pre-feature baselines (a scaffolding build fails); calibrate argv equality with/without products (a leaky build fails); over-cap rejection with a message (a silent-truncate build fails). |
| IV. Generalize | PASS | "Product" is any must-appear object photo, brand-agnostic; the cap and the feed path are the same for every brand and campaign. |
| V. Honest nulls | PASS | No products = no section, no extra refs, byte-identical; over-cap fails loud at the gate; manifest records every product file used. |
| VI. Reconciliation per-dimension | PASS | The feature IS the seam: product = brand-HARD content (like the logo, which stays brand-level via onboarding); style = task-SOFT exemplar. Calibration (magnitude) is isolated from product refs by test. |
| VII. Repo durable context | PASS | CLAUDE.md + SYSTEM_MAP in the closing commit; the brand-level product library deferral is written down here and in research, not carried in chat. |
| Cost discipline | PASS | Same one paid call per sign; all tests free; SC-006 is the one deferred paid run. |
| Output rule | PASS | No em-dashes in new labels or prompt text. |

## Project Structure

### Documentation (this feature)

```text
specs/013-role-tagged-references/
├── plan.md              # This file
├── research.md          # Phase 0 (6 decisions incl. the onboarding/brand-asset seam)
├── data-model.md        # Phase 1 (brief/refs/prompt/form/manifest deltas)
├── quickstart.md        # Phase 1 (free validation + the branded-cups eye-gate)
├── contracts/
│   └── product_refs_contract.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
harness/scene_author.py    # EDIT: --product-image (repeatable, argparse append); PRODUCT
                           #   FIDELITY prompt section in assemble_thin_prompt (conditional);
                           #   thin refs list gains products APPENDED after [style, logo]
harness/conductor.py       # EDIT: _scene_author_thin_argv gains product_images; BOTH call
                           #   sites pass inputs["product_images"]; manifest records them;
                           #   MAX_PRODUCT_IMAGES = 6 validation (fail loud over cap)
frontend/index.html        # EDIT: existing upload relabeled "Style reference"; new optional
                           #   <input type="file" multiple> product-shots control; startRun
                           #   appends parts product_1..product_N (distinct names: the
                           #   multipart parser keys files by part name, last-wins on collision)
frontend/server.py         # EDIT: parse_run_form collects product_* file parts (0..N) and
                           #   enforces the cap; write_run_inputs saves them via the shared
                           #   uploads.save_upload as product_i.<ext> and injects
                           #   form["product_images"]
frontend/inputs_writer.py  # EDIT: pass product_images (list of paths) through to the brief
                           #   verbatim when present; absent = key absent (byte-compat)
harness/generate.py        # NOT touched: generate_variant already takes a list
test_product_refs.py       # NEW free self-test (see contract)
CLAUDE.md / SYSTEM_MAP.md  # EDIT: currency in the closing commit
```

**Structure Decision**: no new modules. Uploads reuse the ONE save-upload home
(`frontend/uploads.py`, the 007 rule); the generation feed reuses `generate_variant`'s existing
list contract; the brand-level logo path is untouched (onboarding remains its only writer).

**Explicitly NOT touched** (FR-005/FR-010): `register/` (calibrate + derive), `harness/kit.py`,
legacy render-and-scrub, `brand_intake/` + the onboarding wizard (the brand-asset home gains no
new writer in 013; the product library variant is the documented 015 deferral),
`frontend/multipart.py` (distinct part names avoid any parser change), `harness/generate.py`.

## Complexity Tracking

No constitution violations. Empty.
