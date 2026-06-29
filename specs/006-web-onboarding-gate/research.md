# Phase 0 Research: Designer-facing Web Onboarding Gate

Grounded in the code read this session: the 004 `frontend/server.py` (stdlib `ThreadingHTTPServer` +
`BaseHTTPRequestHandler`; `do_GET`/`do_POST`; `_send`; single-flight `_inflight` lock; `_brands()`
lists `answer_keys/*.json`; **bodies are JSON-only** via `json.loads(self.rfile.read(length))`) and the
005 `brand_intake/` pure modules (`suggest_pages`, `extract_brand_colors` / `read_brand_names`,
`build_lean_key` / `lean_projection`, `validate_lean_key`, `unacknowledged_flags` / `finalize_items`;
plus `intake.main()`'s inline write tail).

---

## D1. Draft state = a transient server-side draft DIR keyed by draft_id (the brief's open question)

**Decision**: Each onboarding gets a `draft_id` and a transient draft directory under a scratch path.
Upload writes the PDF there; the confirmed pages + in-progress locks are held against that draft_id
across the 3 requests. Discarded on a successful save or on abandon (no resumable draft, per the
clarification). Only `save_draft` writes the committed `answer_keys/<brand>.json` + the logo.

**Rationale**: The extractors are file-based -- `extract_colors.render_page` / `extract_text_layer.
page_text` open the PDF FROM DISK via `fitz`. The uploaded PDF MUST live on disk for extraction
regardless, so a server-side draft dir is not extra state, it is the natural home for the file the
pipeline already needs. The clarified "transient, discard on abandon, only save writes" maps directly:
the draft dir is scratch; nothing in `answer_keys/` or `brands/` appears until save.

**Alternatives considered**: stateless client re-post (the browser holds the draft, re-posts it whole
each step) -- REJECTED: it would re-upload a multi-MB PDF on every step, and the server would still
have to write it to disk for the extractors. Persisted/resumable drafts -- REJECTED by the
clarification (out of scope; transient only).

---

## D2. No big intake refactor; extract a shared `persist.py` (the brief's other open question)

**Decision**: Do NOT refactor `intake.main()`'s linear flow into a shared orchestration -- the CLI's
single linear pass and the web's 3-HTTP-step flow are genuinely different control flows, and the
SHARED logic is ALREADY pure (suggest / extract / `build_lean_key` / `validate_lean_key` /
`unacknowledged_flags` / `finalize_items`). The ONLY duplication risk is the WRITE tail: `intake.main()`
inlines "place the logo under `brands/<brand>/` + write `answer_keys/<brand>.json`". Extract that into a
small shared `brand_intake/persist.py` (`place_logo`, `write_key`, `key_exists`) that BOTH `intake.py`
and `frontend/onboard.py` call, so the CLI and the web gate write byte-identical artifacts.

**Rationale**: DRY where it matters (one home for the write + the id-collision check), without churning
the proven CLI. `intake.py` swaps ~10 inline lines for `persist.*` and still runs standalone (FR-011).
`key_exists` gives the id-collision guard (FR-014) one definition both surfaces share.

**Alternatives considered**: a full shared orchestrator -- REJECTED (the control flows differ; forcing
one shape adds coupling for no gain). Duplicate the write logic in the server -- REJECTED (two homes
for "write the key" drift; the silent-logo landmine must be guarded in exactly one place).

---

## D3. Multipart upload parsing = a tiny stdlib parser (the one genuinely-new server capability)

**Decision**: Add `frontend/multipart.py` `parse_multipart(body: bytes, content_type: str) ->
{fields: {name: str}, files: {name: (filename, bytes)}}`, a small hand-rolled boundary parser. The
upload routes read the raw body (`self.rfile.read(Content-Length)`) and call it.

**Rationale**: The 004 server is JSON-only (`json.loads(self.rfile.read())`); real file upload (FR-002,
a designer picks files in a browser) needs multipart/form-data. The repo is stdlib-first with no new
deps; Python 3.11's `cgi.FieldStorage` still works but `cgi` is DEPRECATED (removed in 3.13), so a
~30-line boundary splitter (or `email.parser.BytesParser` on the reconstructed part) is the durable,
dependency-free choice. PURE (bytes in, dict out) so it is unit-testable without HTTP.

**Alternatives considered**: `cgi.FieldStorage` -- REJECTED (deprecated, 3.13 removal is a footgun). A
new dep (e.g. `python-multipart`) -- REJECTED (violates the no-new-dep / thin ethos). Base64-in-JSON
upload -- REJECTED (awkward for the designer; multipart is the browser-native path).

---

## D4. The 3-step wizard routes (thin over `onboard.py`)

**Decision**: Extend `server.py` with four routes that delegate to `frontend/onboard.py`:
- `GET /onboard` -> serve the onboarding screen.
- `POST /onboard/upload` (multipart: the PDF) -> `onboard.start_draft(pdf_bytes)` -> `{draft_id,
  suggestions}` (1-indexed page suggestions from `page_finder`).
- `POST /onboard/<id>/extract` (JSON: confirmed pages) -> `onboard.extract_draft(...)` -> `{locks,
  names}`; if zero colors, return a BLOCK status that the UI shows + sends back to page-confirm (FR-004).
- `POST /onboard/<id>/save` (multipart: the logo + JSON: verified locks/roles/acks/names) ->
  `onboard.save_draft(...)` -> validate-loud + id-collision check + write key + place logo + discard
  draft; 4xx + named reason on any fail (no file written).

**Rationale**: Mirrors the 004 thin-glue pattern (routes delegate to pure modules; `_send` + the
single-flight lock reused). `onboard.py` holds the wizard logic as functions callable WITHOUT HTTP, so
the falsifiable tests drive `start_draft`/`extract_draft`/`save_draft` directly over the synthetic
fixture, no live server, no model.

---

## D5. The onboard -> generate handoff is already wired (SC-005, free)

**Finding (verified)**: 004's `GET /brands` returns `sorted(p.stem for p in ANSWER_KEYS.glob("*.json"))`.
So a key 006 writes to `answer_keys/<brand>.json` appears in the live-runner brand dropdown with NO
extra wiring. The test asserts the saved brand is in `frontend.server._brands()`.

**Rationale**: The two surfaces share the same data dir; onboard then generate is one app for free.

---

## D6. No paid calls; OCR is local (FR-012 / cost discipline)

**Decision**: Tests drive `multipart.parse_multipart`, `onboard.start_draft/extract_draft/save_draft`,
and `persist.*` over the synthetic fixture PDF (`tests_support/make_pdf`) -- model-free assertions
(page suggestion, the locks shape, validate-loud, the gate, the write). The real-OCR cold-brand run +
the one paid sign are the human smoke (the back-half eye-gate), not automated.

**Rationale**: rapidocr is local/free but slow + nondeterministic on a synthetic render; the
falsifiable surface is the wizard/persist/multipart logic, not the OCR organ (already proven in 005).

---

## Reuse summary (verified against code)

| Existing capability | File | Reused for |
|---------------------|------|-----------|
| stdlib server pattern (`_send`, do_GET/POST, single-flight, `_brands()`) | `frontend/server.py` | D4 routes, D5 handoff |
| `page_finder.suggest_pages` (1-indexed) | `brand_intake/page_finder.py` | upload step |
| `extract_brand_colors` / `read_brand_names` | `brand_intake/extract.py` | extract step |
| `build_lean_key` / `validate_lean_key` | `brand_intake/assemble_key.py` + `validate_key.py` | save step (validate-loud) |
| `unacknowledged_flags` / `finalize_items` | `brand_intake/intake.py` | verify-gate save logic |
| the synthetic-PDF fixture | `tests_support/make_pdf.py` | all 006 free tests |

| Genuinely NEW | Why nothing existing covers it |
|---------------|-------------------------------|
| `frontend/multipart.py` | the 004 server is JSON-only; no upload parsing exists |
| `frontend/onboard.py` | no wizard orchestration over a transient draft exists |
| `brand_intake/persist.py` | the write tail is inline in intake.main(); the web gate needs one shared home |
| onboarding routes + screen in `server.py` / html | no onboarding UI exists (004 is the back-half only) |
