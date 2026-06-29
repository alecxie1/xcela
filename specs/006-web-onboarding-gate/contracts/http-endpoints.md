# Contract: onboarding HTTP endpoints (added to `frontend/server.py`)

Four thin routes delegating to `frontend/onboard.py`. They reuse the 004 server's `_send`, the
single-flight `_inflight` lock, and the local-only posture. The server holds NO wizard logic.

| Route | Method | Body | Behavior |
|-------|--------|------|----------|
| `/onboard` | GET | - | serve the onboarding wizard screen (the static page) |
| `/onboard/upload` | POST | multipart (PDF) | `parse_multipart` -> `onboard.start_draft(pdf_bytes)` -> `{draft_id, suggestions}` (1-indexed page suggestions) |
| `/onboard/<id>/extract` | POST | JSON (confirmed pages) | `onboard.extract_draft(id, pages)` -> `{locks, names}`; on ZERO colors -> `{block: "no colors found ..."}` (the UI returns to page-confirm) |
| `/onboard/<id>/save` | POST | multipart (logo) + JSON (verified locks/roles/acks/names) | `onboard.save_draft(...)` -> `{brand, key_path}` on success; 4xx + `{error: <named reason>}` and NO write on any fail |

## Rules (falsifiable)

1. `/onboard/upload` and `/onboard/save` parse multipart bodies (via `frontend/multipart.py`); the 004
   JSON-only path is unchanged for `/run` etc.
2. `/onboard/<id>/save` FAILS LOUD (4xx + a named reason, NO file written) on: no primary color, a
   missing/unreal logo, an unacknowledged needs_review flag, OR an existing brand id (collision).
3. `/onboard/<id>/extract` returns a BLOCK (not an empty success) when zero colors are extracted.
4. On a successful save the draft is discarded; the new brand appears in `GET /brands`.
5. The server NEVER calls a paid model and NEVER calls `intake.main()`; it delegates to `onboard.py`,
   which composes the 005 pure modules.
6. Single-flight: an onboarding save is serialized like the 004 run (no concurrent writes).
7. No em-dashes in any response string or served page.
