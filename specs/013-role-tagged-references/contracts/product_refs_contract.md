# Contract: Role-Tagged References (013)

Verified by `test_product_refs.py` (free, no paid calls). "Both call sites" = build_plan's thin
argv AND the argv `execute()` constructs with `run_step` stubbed (the twice-caught drift class).

## A. Prompt (assemble_thin_prompt)

| # | product_images | Obligation |
|---|---|---|
| 1 | 2 paths | PRODUCT FIDELITY section present, states the supplied images are the brand's REAL products, demands same shapes / printed branding / label text / colors, forbids generic redraws, licenses background discard; every other section byte-unchanged |
| 2 | none/empty | prompt BYTE-IDENTICAL to a pre-013 assembly (inlined baseline literal) |

## B. Threading

| # | Obligation |
|---|---|
| 3 | `--product-image <path>` appears once per product, in order, at BOTH call sites when the brief carries them; absent entirely when it does not |
| 4 | scene_author argparse collects repeated `--product-image` into an ordered list |
| 5 | conductor fail-louds (named error, no launch) on >6 product paths or a missing file |

## C. Generation refs list (thin route)

| # | Obligation |
|---|---|
| 6 | refs == [style_ref, logo] + products (products appended, prefix byte-stable) |
| 7 | zero products: refs == [style_ref, logo] exactly (pre-feature equality) |

## D. Calibration isolation (SC-003)

| # | Obligation |
|---|---|
| 8 | the calibrate step argv is IDENTICAL for the same brief with and without product_images (product truth never reaches magnitude/register) |

## E. Upload / form surface (greps + parse tests)

| # | Obligation |
|---|---|
| 9 | parse_run_form: 0 product parts -> empty list (today's behavior); 2 parts (`product_1`,`product_2`) -> both tuples in order; 7 parts -> ValueError naming the cap (no silent truncation) |
| 10 | write_run_inputs saves products via the shared save_upload as `product_<i><ext>` and injects `form["product_images"]` with the saved paths |
| 11 | form greps: style-reference label on the existing upload; an optional multiple-file product control; the JS appends DISTINCT part names product_1..N |
| 12 | no em-dash in new labels or the new prompt section |

## F. No-regression

| # | Obligation |
|---|---|
| 13 | all existing suites pass unchanged (conductor, render_and_scrub, render_modes, register_render_aware, frontend_nav, lossless_brief) |
| 14 | a legacy inputs JSON without `product_images` plans and executes byte-identically |

## G. Deferred human eye-gate (SC-006)

ONE paid rerun of the CJXQ watermelon brief WITH the branded cup shots as product references:
the composition carries the actual 茶救星球 JO'S CHA cups (printed logos visible) rather than
generic look-alikes, retaining the 012 run's style/scene quality. Operator-judged, recorded in
SYSTEM_MAP.
