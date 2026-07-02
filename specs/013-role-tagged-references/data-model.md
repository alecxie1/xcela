# Data Model: Role-Tagged References (013)

**Phase 1 output.** One new optional brief field; no schema breaks; the brand-asset home is
untouched.

## 1. Reference roles (the conceptual model)

| Role | Cardinality | Home | Written by | Consumed by |
|---|---|---|---|---|
| style | exactly 1 (required, unchanged) | run dir (`reference.jpg`) | run form upload (007 path) | calibration (magnitude), dial, generation refs[0] |
| logo | exactly 1 per brand (unchanged) | `brands/<brand>/` via answer key `logo_path` | ONBOARDING (`persist.place_logo`), never the run form | LOGO prompt line, generation refs[1] |
| product | 0..6 per run (NEW) | run dir (`product_1..N.<ext>`) | run form upload (shared `save_upload`) | PRODUCT FIDELITY prompt section, generation refs[2..], manifest |

Calibration and the register engine NEVER see product refs (FR-005).

## 2. Brief (inputs JSON)

| Field | Delta |
|---|---|
| `product_images` | NEW, OPTIONAL: ordered list of saved file paths (0..6). Absent or empty = pre-feature behavior byte-for-byte. Legacy briefs without the key run unchanged. |
| `reference_image` | unchanged (the style reference) |

**Validation**: conductor fail-louds on >6 entries or non-existent paths (honest null, named
error); the server rejects >6 uploaded files with a visible message BEFORE launching.

## 3. Generation inputs (refs list fed to generate_variant)

```
[style_reference, logo] + product_images     # products appended; prefix byte-stable
[style_reference, logo]                      # zero products: exactly today's list
```

`harness/generate.py` unchanged (already accepts a list; its returned metadata already records
all fed paths).

## 4. Thin prompt

New conditional section (with the exemplar-note block): PRODUCT FIDELITY, stating the N
additional supplied images are the brand's real products, to be carried faithfully (shapes,
printed branding, label text, colors), backgrounds discardable, no generic redraws. Absent
products = section absent, prompt byte-identical.

## 5. Multipart / form surface

| Item | Delta |
|---|---|
| existing reference upload | relabeled "Style reference (how the asset should feel)" |
| product-shots control | NEW: `<input type="file" multiple>`, optional, labeled "what must appear in it"; JS appends parts `product_1`..`product_N` (distinct names; parser is last-wins per name) |
| `parse_run_form` | returns product file tuples 0..6, sorted by index; >6 raises ValueError with a human message |
| `write_run_inputs` | saves each product via `uploads.save_upload(name="product_<i><ext>")`, injects `form["product_images"]` |

## 6. Manifests

- Sign-level `run_manifest.json`: `generation.reference_image` already lists ALL fed paths
  (free audit surface); scene_author's manifest gains `product_images`.
- `conductor_manifest.json`: records `product_images` from the brief (FR-006).

## 7. State transitions

None. Pure data flow; the only new decision logic is the cap check (a comparison).
