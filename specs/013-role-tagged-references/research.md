# Research: Role-Tagged References (013)

**Phase 0 output.** No external unknowns beyond one service limit (D4). Evidence:
`harness/generate.py` (generate_variant already takes a path LIST -> images.edit),
`harness/scene_author.py` ~1055-1063 (thin refs = [style_ref, logo], logo resolved from the
answer key's `logo_path`), `brand_intake/persist.py:31` (place_logo: onboarding owns the
brand-level asset home `brands/<brand>/`), `frontend/multipart.py:28` (files keyed by part
name, last-wins), `frontend/server.py:43-70` (parse_run_form / write_run_inputs),
`frontend/uploads.py:19` (save_upload, the one upload home).

## D1. Per-run vs brand-level home for product shots (the onboarding question)

**Decision**: Product references are PER-RUN (campaign) assets: uploaded on the run form, saved
in the run dir, referenced by the brief. The brand-level asset home (`brands/<brand>/`, written
only by onboarding via `place_logo`) is NOT extended in 013.

**Rationale**: The operator flagged that the logo and other brand material are fed at
onboarding, and the plan must respect that seam. The seam is real and it CUTS THE OTHER WAY for
013's motivating case: the watermelon-launch cups are campaign-specific, not durable brand DNA;
storing them beside the logo would rot (next campaign's products differ) and would force a
brand-key write on every campaign, which the onboarding gate is not shaped for. The logo stays
the exemplar of a brand-level asset (fed on every run, unchanged); products are the exemplar of
a campaign-level asset (fed on this run). Both meet in ONE place, the generation refs list, so a
future brand-level PRODUCT LIBRARY (evergreen hero shots chosen at onboarding, e.g. the
signature cup) reuses this feature's whole feed path and only changes where paths come from.
That library is explicitly deferred to the brand-key-enrichment feature (015 in the roadmap
sketch) and recorded here so the decision is durable.

**Alternatives considered**: extending onboarding now to collect product shots into
`brands/<brand>/` + the answer key: rejected for 013 (campaign assets rot there; doubles the
feature's surface into `brand_intake/` + the wizard; the eye-gate case needs per-run anyway).
A hybrid (run upload with a "save to brand" checkbox): rejected, that IS the 015 feature.

## D2. Where product images enter the generation refs list

**Decision**: Appended AFTER the existing list: `[style_ref, logo] + products`. The pre-feature
prefix is byte-stable; zero products leaves the list exactly `[style_ref, logo]`.

**Rationale**: Strongest possible SC-002 no-regression argument (the existing two-element list
is untouched as a prefix, provable by equality). `generate_variant` already accepts the list
verbatim, so `harness/generate.py` needs no change. Image order also mirrors prompt order: the
fidelity section names the product images as "the additional supplied images", last in, matching
their position.

**Alternatives considered**: inserting products between style and logo: no functional gain,
breaks prefix equality. Feeding products INSTEAD of the style ref when present: rejected,
style and product are different jobs (the whole point).

## D3. The PRODUCT FIDELITY prompt section

**Decision**: A conditional section in `assemble_thin_prompt`, placed with the reference
exemplar note (the existing "A reference image is provided as a visual exemplar" block), reading:

```
PRODUCT FIDELITY (the N additional supplied image(s) are the brand's REAL products): carry
these exact products into the composition faithfully. Same shapes, same printed branding and
label text, same colors. Do NOT redraw them as generic products, do NOT invent replacements.
Only their backgrounds may be discarded.
```

Absent products = no section (byte-identity). The only-the-headline text guard is not weakened:
it governs GENERATED text; text depicted inside supplied product photos is covered by "same
printed branding and label text".

**Rationale**: Mirrors the proven LOGO instruction pattern ("use the supplied brand logo
faithfully"), names the images by their supplied role so the model can bind instruction to
input, and explicitly licenses background discard (the busy-background edge case) without any
preprocessing. This is a prompt contract, so obedience is probabilistic; SC-006 owns the pixel
claim (the spec says this in as many words).

**Alternatives considered**: per-image captions (--product-image path:caption): more human
typing for unclear gain; deferred until the eye-gate shows binding failures. Segmenting/cropping
product shots first: out of scope by spec.

## D4. The cap

**Decision**: `MAX_PRODUCT_IMAGES = 6` (a named conductor constant). 1 style + 1 logo + 6
products = 8 input images, comfortably inside the images.edit documented limit of 16 input
images for the gpt-image family. Enforced at BOTH gates: the server's parse_run_form (visible
form error) and conductor input validation (fail-loud for CLI briefs). Never truncated.

**Rationale**: FR-008 demands a documented cap with loud failure. 6 covers a product LINE (the
CJXQ case is 3 cups) with headroom, while keeping total inputs low enough that the style
exemplar and logo are not diluted among too many images.

## D5. Multipart capture without touching the parser

**Decision**: The form appends file parts named `product_1`..`product_N` (distinct names);
`parse_run_form` collects `files[k]` for keys matching `product_*`, sorted numerically, enforces
the cap, and returns them alongside the existing reference tuple. `write_run_inputs` saves each
via the shared `uploads.save_upload` as `product_<i><ext>` and injects `form["product_images"]`
(a list of saved paths). `frontend/multipart.py` is untouched.

**Rationale**: The parser keys files by part name with last-wins collision (multipart.py:52), so
same-named parts would silently drop files, exactly the silent-loss defect class 012 just
killed. Distinct names cost three lines of JS and zero parser risk. save_upload's basename guard
already covers path traversal; passing an explicit `name=` sidesteps duplicate-filename
collisions between product files.

**Alternatives considered**: upgrading parse_multipart to return lists for repeated names:
touches a shared 006 module used by onboarding for zero added capability. JSON-embedding base64
files in the form field: bloats memory and abandons the existing upload path.

## D6. Threading + test surface

**Decision**: `inputs["product_images"]` (optional list) -> `_scene_author_thin_argv` gains
`product_images=None` and appends repeatable `--product-image <path>` flags -> BOTH call sites
(build_plan thin loop AND execute thin loop) pass it -> scene_author argparse
`action="append"` -> thin refs list + prompt section. Manifest: the sign-level record gains the
product list (and generate_variant's existing `reference_image` metadata already lists ALL fed
paths, giving a second audit surface for free). `test_product_refs.py` asserts: prompt section
values + no-products byte-identity (against an inlined pre-013 literal); argv carried/omitted at
BOTH sites (stubbed run_step); calibrate argv equality with/without products (SC-003); refs-list
construction ([style, logo] prefix + products appended, zero-products equality);
parse_run_form 0/2/7-file cases (7 rejects with a message); form greps (style-reference label,
multiple-file control, distinct part naming in the JS).

**Rationale**: Each assertion names the wrong build it kills: plan-only threading (the
twice-caught drift), empty scaffolding, calibration leakage, silent truncation, parser
collision. The repeatable-flag pattern (`action="append"`) matches how argparse handles
multi-value options without inventing a delimiter that could appear in filenames.
