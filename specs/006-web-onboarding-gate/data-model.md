# Phase 1 Data Model: Designer-facing Web Onboarding Gate

Flow: upload PDF -> Draft (suggest pages) -> confirm pages -> extract Locks -> verify (roles +
acknowledge + names + logo) -> validate-loud -> save lean key. The Draft is TRANSIENT; only a
successful save writes committed artifacts.

---

## Entity: Onboarding Draft (transient, server-side)

| Field | Type | Rule |
|-------|------|------|
| `draft_id` | string | opaque id keying the draft dir; returned by upload, used by extract/save |
| `pdf_path` | path | the uploaded PDF saved under the transient draft dir (extractors read it from disk) |
| `suggestions` | object | `page_finder.suggest_pages` output (1-indexed color/fonts/brand_name + text_layer_ratio) |
| `confirmed_pages` | object | the human-confirmed color/name pages (override of the suggestion) |
| `locks` | object | the extracted colors + name candidates (after the extract step) |

**Lifecycle**: created on upload; updated on confirm + extract; DISCARDED on a successful save OR on
abandon (closing the tab / starting a new PDF). Nothing in `answer_keys/` or `brands/` exists until
save. No resumable/persisted draft (v1).

---

## Entity: Page Suggestions (`page_finder.suggest_pages` output, reused)

`{color: [1-idx...], fonts: [1-idx...], brand_name: [1-idx...], text_layer_ratio}` -- 1-INDEXED, the
human confirms/corrects. (Unchanged from 005.)

---

## Entity: Extracted Locks (from `extract_brand_colors` / `read_brand_names`, reused)

- **Colors**: each `{value.hex, source, confidence, evidence, needs_review}` -- role UNSET (assigned by
  the human at the verify gate). If extraction yields ZERO colors -> the gate BLOCKS and returns the
  designer to page-confirm (no fabricated color).
- **Brand-name candidates**: `{cn_candidates, en_candidates, raw}` -- the human confirms the actual
  brand / brand_en.

---

## Entity: Verify-gate item (the acknowledgment unit, reused 005 semantics)

Per color: `{hex, rgb, role (human-assigned), name_cn, name_en, needs_review, _ack}` where `_ack` in
{confirm, edit, keep-flagged}. Save is blocked while any `needs_review` item is unacknowledged
(`unacknowledged_flags`); `finalize_items` strips `_ack` and persists `needs_review: true` for a
kept-flagged item.

---

## Entity: Lean answer_key (the saved output, reused 005 shape)

`build_lean_key(...)` -> the consumed subset (names + `fields.colors.items[]` with roles + printed_html
+ rgb + top-level `logo_path` + provenance; `typography.styles` absent/honest-null in v1). Written ONLY
on a valid save. Consumed UNCHANGED by the thin route + the 004 live-runner.

---

## Entity: Uploaded files (multipart)

| File | Step | Rule |
|------|------|------|
| brand PDF | upload | required; saved to the draft dir; read by the extractors |
| logo | save | required; placed under `brands/<brand>/` via `persist.place_logo`; save fails loud if absent |

---

## Entity: Save Result

| Outcome | Trigger |
|---------|---------|
| success | a primary color assigned + a real logo + every flag acknowledged + brand id free -> key written, logo placed, draft discarded |
| FAIL LOUD (4xx + named reason, no write) | no primary color; OR no/unreal logo; OR an unacknowledged flag; OR the brand id already has an answer_key (collision) |

---

## Falsifiable properties (seed the tests; constitution §III)

- `multipart.parse_multipart(body, content_type)` round-trips an uploaded file: the file bytes + a text
  field come back intact.
- `onboard.start_draft(pdf_bytes)` over the synthetic fixture returns a draft_id + suggestions whose
  `color` contains the hex-token page (1-indexed), not the color-mention page.
- `onboard.extract_draft(draft_id, confirmed_pages)` returns colors with hex + needs_review; a
  confirmed page set yielding ZERO colors returns a BLOCK (no fabricated color, no empty gate).
- `onboard.save_draft(...)` with a primary + real logo + acknowledged flags writes an
  `answer_keys/<brand>.json` that passes `validate_lean_key` and yields a non-empty thin prompt with
  the primary hex; it FAILS LOUD (no file) on missing primary / logo, an unacknowledged flag, or an
  existing brand id; the draft dir is gone after a successful save.
- A saved brand appears in `frontend.server._brands()` (the onboard -> generate handoff).
- The standalone 005 CLI (`brand_intake/intake.py`) still runs the full flow (it calls the same
  `persist.*`); the web gate added no dependency it needs.
