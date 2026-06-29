# Implementation Plan: Designer-facing Web Onboarding Gate

**Branch**: `006-web-onboarding-gate` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-web-onboarding-gate/spec.md`

## Summary

005 gave the designer a terminal path from a brand PDF to a verified lean `answer_keys/<brand>.json`
(cold-brand-verified: chajiuxingqiu). 006 is the designer-facing SURFACE: a browser wizard that wraps
the proven 005 PURE modules, the same way 004 wrapped the thin route. Upload a PDF -> confirm the
suggested spec pages -> review the extracted locks -> assign roles + acknowledge flags + upload the
logo -> validate-loud + save. The saved key is consumed unchanged by the thin route and appears in the
004 live-runner brand dropdown (its `/brands` already lists `answer_keys/*.json`).

Two decisions the brief flagged for the plan are RESOLVED here, grounded in the code:
1. **Draft state = a server-side draft DIRECTORY keyed by a draft_id** (transient; discarded on save
   or abandon). Forced by reality: the extractors (`fitz` + `extract_colors`) read the PDF FROM DISK,
   so the uploaded PDF must live on disk regardless; the draft dir is the natural transient home.
   Stateless client re-post is rejected (it would re-upload a multi-MB PDF every step).
2. **No big intake refactor.** The shared logic is already pure (suggest/extract/assemble/validate/gate
   helpers). Only the WRITE tail (place logo + write key + id-collision check) is inline in
   `intake.main()`; extract that into a small shared `brand_intake/persist.py` both the CLI and the web
   gate call, so they write IDENTICALLY. The differing control flow (CLI linear pass vs 3 HTTP steps)
   stays separate.

The one genuinely-new server capability is **multipart upload parsing** (the 004 server is JSON-only),
done with a tiny stdlib parser (no new dependency, and avoiding the deprecated `cgi` module).

## Technical Context

**Language/Version**: Python 3.11 (`.venv`). Frontend = the existing stdlib `http.server` app
(`frontend/`) extended with onboarding routes + one onboarding screen (vanilla JS, no framework/build).

**Primary Dependencies**: none new. Reuses `brand_intake/*` (005 pure modules + extractors:
PyMuPDF / rapidocr-local / Pillow) and the 004 `frontend/` stdlib server pattern. Multipart parsing is
hand-rolled stdlib (no `cgi`, no new dep).

**Storage**: Files. A transient draft dir per onboarding (uploaded PDF + in-progress state) under a
scratch path, discarded on save/abandon. On save: `answer_keys/<brand>.json` (committed brand data) +
the logo under gitignored `brands/<brand>/` — the identical artifacts the 005 CLI writes.

**Testing**: Falsifiable STRUCTURAL self-tests in the `test_*.py` style (stdlib + the synthetic-PDF
fixture `tests_support/make_pdf`). NO paid model calls; the deterministic OCR path is local, and tests
target the PURE wizard/persist/multipart logic, not live HTTP or a model. The one paid sign stays the
back-half eye-gate (004 / CLI).

**Target Platform**: Localhost web app on the designer's machine (same host runs the CLI + reads the
write paths). Single-designer, single-flight.

**Project Type**: Single project + the thin local web frontend (extended). No hosted/multi-user service.

**Performance Goals**: Not latency-bound. The extract step runs local OCR (seconds) -> a loading
state, NOT a paid-cost label (contrast 004's paid Run button). No paid call anywhere in 006.

**Constraints**: THIN over the agent-free core (wrap the 005 pure modules + the extractors; never
reimplement extraction/validation/gate/generation; never call stdin-bound `intake.main()`). The UI
auto-decides NO brand lock (pages suggested, roles/names/flags human). Fail-loud / honest-null at every
stage (validate-loud save; zero-color block; id-collision block; logo real or fail). Draft transient
(only save writes). Standalone 005 CLI preserved. No em-dashes in user-facing text.

**Scale/Scope**: v1 = onboard ONE new brand through the browser. No brand-management dashboard, no
resumable drafts, no VLM semantic layer, no font-pairing widget, no logo auto-crop (all out of scope).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Agent-free, NOT human-free | The wizard IS the input gate in the browser: pages suggested + human-confirmed, roles human-assigned, names human-confirmed, every needs_review human-acknowledged. No model auto-detects pages or decides a lock. | PASS |
| II. Ground truth = the eye | Tests assert STRUCTURE only; the cold-brand OCR + the one paid sign are the human's smoke / eye-gate. No VLM PASS as proof. | PASS |
| III. Falsifiable tests only | save writes a key that passes validate_lean_key + yields the primary hex; save FAILS LOUD on missing primary/logo and on an id collision; an unacknowledged flag blocks save; zero-color extraction blocks; the saved brand appears in `_brands()`; the standalone CLI still runs; the multipart parser round-trips an uploaded file. Each fails a wrong build. | PASS |
| IV. Generalize, do not hand-tune | Wraps the 005 modules (brand-general); no AIA/brand literals in the new code; `_brands()` is data-driven over answer_keys/. | PASS |
| V. Honest nulls, never invented | validate-loud save (no silent degrade); zero-color -> block + re-pick (no fabricated color); kept-flag persists needs_review in the key; abandoned draft discarded (no partial write); logo real or fail (no taichi default). | PASS |
| VI. Reconciliation per-dimension | Untouched. The saved key feeds derive_register / assemble_thin_prompt unchanged; 006 adapts to that read surface. | PASS |
| VII. Repo is durable; thin / reuse | Stdlib only (no new dep, multipart hand-rolled); the standalone 005 CLI runs with the web gate absent; shared persist helpers keep CLI + web writing identically (DRY); one-module-one-test-one-commit; CLAUDE.md + SYSTEM_MAP updated in the staling commit. | PASS |

**Cost discipline**: No paid model calls in any automated test; the deterministic path is local. The one
paid sign is the human's back-half eye-gate after the build. PASS.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-web-onboarding-gate/
├── spec.md              # Feature spec (clarified 2026-06-28: transient draft + zero-color block)
├── plan.md              # This file
├── research.md          # Phase 0: draft model, intake refactor, multipart, reuse map
├── data-model.md        # Phase 1: draft, page suggestions, locks, lean key, validation
├── contracts/
│   ├── http-endpoints.md       # GET /onboard + POST upload/extract/save (multipart + JSON)
│   ├── draft-model.md          # the transient server-side draft dir + lifecycle
│   ├── persist-contract.md     # the shared brand_intake/persist helpers (CLI + web)
│   └── multipart-contract.md   # the stdlib multipart parser
├── quickstart.md        # Phase 1: free structural validation + the human browser smoke
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
brand_intake/
├── persist.py            # NEW (shared, CLI + web): place_logo(brand, src) -> dest under brands/<brand>/;
│                         #   write_key(brand, key) -> answer_keys/<brand>.json; key_exists(brand) -> bool
│                         #   (the id-collision guard). The single home for "place logo + write key".
└── intake.py             # CHANGED: refactor the write tail of main() to call persist.* (DRY); the CLI
                          #   flow is otherwise unchanged and still runs standalone.

frontend/
├── multipart.py          # NEW (stdlib, PURE): parse_multipart(body, content_type) -> {fields, files}.
│                         #   Hand-rolled boundary parsing; no cgi (deprecated), no new dependency.
├── onboard.py            # NEW: the wizard orchestration over a transient draft dir, calling the 005
│                         #   PURE modules + persist. start_draft(pdf_bytes) -> {draft_id, suggestions};
│                         #   extract_draft(draft_id, pages) -> {locks, names} (blocks on zero colors);
│                         #   save_draft(draft_id, verified, logo_bytes) -> key path (validate-loud,
│                         #   id-collision block, finalize_items). Discard on save/abandon. Testable
│                         #   without HTTP (bytes/paths in, dicts out).
├── server.py             # CHANGED: add GET /onboard (serve the screen), POST /onboard/upload
│                         #   (multipart PDF), POST /onboard/<id>/extract (JSON confirmed pages),
│                         #   POST /onboard/<id>/save (multipart logo + JSON verified locks). Thin glue
│                         #   delegating to onboard.py; reuse the multipart helper + _send + single-flight.
└── index.html / onboard.html  # CHANGED/NEW: the 3-step onboarding wizard screen (upload -> confirm
                          #   pages -> extract+verify -> save), inline vanilla JS; cost-free loading
                          #   state on extract; in-browser fail-loud errors. No em-dashes.

test_multipart.py         # NEW: parse a synthetic multipart body -> fields + uploaded file bytes round-trip.
test_onboard.py           # NEW: the wizard pure flow over the synthetic fixture: upload->draft+suggest;
                          #   extract->locks (+ zero-color block); save->valid key (validate pass) +
                          #   fail-loud (no primary / no logo) + id-collision block + acknowledgment gate
                          #   + saved brand appears in frontend.server._brands() + standalone CLI intact.
```

**Structure Decision**: The genuinely-new capability is split into PURE, testable modules:
`frontend/multipart.py` (stdlib upload parsing — the one new server capability), `frontend/onboard.py`
(the wizard orchestration over a transient draft dir, callable without HTTP), and a small shared
`brand_intake/persist.py` (place-logo + write-key + id-collision, called by BOTH `intake.py` and the
web gate so they write identically). `server.py` gains four thin routes that delegate to `onboard.py`;
the screen is vanilla JS. Nothing in the 005 extraction/validation/gate logic or the back-half is
changed (FR-009); `intake.py` only swaps its write tail for `persist.*` and still runs standalone
(FR-011 / SC-006). The transient draft dir is forced by the extractors reading the PDF from disk; only
a successful `save_draft` writes the committed key (the clarified discard-on-abandon).

## Complexity Tracking

> No constitution violations. Section intentionally empty.
