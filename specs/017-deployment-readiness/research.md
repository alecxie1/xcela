# Research: Deployment Readiness + Chinese-Ready UI (017)

All unknowns resolved against the live codebase (verified 2026-07-12) and the 2026-07-10
portability audit. No NEEDS CLARIFICATION remain.

## D1. Asset-path resolution order

- **Decision**: absolute-and-exists wins (legacy keys keep working), then
  `XCELA_BRANDS_DIR`-relative (default `<repo>/brands`), then repo-relative, else a named
  SystemExit listing every tried path.
- **Rationale**: backward compatible (a user's uncommitted local key with an absolute path
  still runs), portable (committed keys carry brands-relative paths), honest (a dangling path
  can never silently substitute; the old `/mnt/c` fallback at scene_author.py:125 did exactly
  that and is removed).
- **Alternatives**: repo-relative-only in keys (breaks legacy local keys); an install-time key
  rewrite step (mutates committed data per machine, drift magnet).

## D2. Chinese usage matching: extend the EXISTING tuples, not new rows

- **Decision**: append Chinese keywords inside the current keyword tuples
  (`MARKETING_USAGE_KEYWORDS` and the event/wall/formal rows in `USAGE_RULES`,
  register/derive_register.py:25-45).
- **Rationale**: verified structure: rows are `(keywords_tuple, register)` with first-match
  precedence, and the 014 vibe-promotion suppression compares the matched row's identity to
  `MARKETING_USAGE_KEYWORDS`; extending that tuple gives Chinese marketing matches the
  explicit-human-statement suppression with ZERO new logic, and event-row precedence is
  inherited rather than re-established. English derivations are byte-identical because
  Chinese substrings never occur in English briefs (pinned).
- **Keyword choices** (multi-character only, per the spec's over-match edge case): marketing
  朋友圈/小红书/社交媒体/公众号/微博/营销/宣传/推广/海报; event 手举牌/举牌/应援/打卡/活动现场
  (NOT bare 活动: it appears inside 促销活动, a marketing phrase); wall 上墙/墙贴/张贴; formal
  正式文件/公告/通知. 海报 maps to marketing: the wall row already resolves to the marketing
  base too, so a wall-ish poster phrase reaching either row lands in the same lane.
- **Alternatives**: separate Chinese rows (needs new suppression wiring + ordering decisions);
  a translation pre-pass on usage_context (a model call on the free path: forbidden).

## D3. Size normalization location

- **Decision**: a pure pre-pass at the top of `format_size.resolve_size` (harness/
  format_size.py:41): fullwidth digits and multiplication signs to ASCII, 厘米/公分 -> cm,
  毫米 -> mm, 英寸 -> in, fullwidth spaces stripped.
- **Rationale**: resolve_size is the single entry both the browser (via conductor) and the
  CLI use; normalization is identity on ASCII so every current parse is byte-identical
  (pinned); an unparseable string after normalization still takes the existing
  honest-default + note path (the 015 gate row).

## D4. Worker timeout interacts safely with the 016 export state machine

- **Decision**: `subprocess.run(timeout=...)` in `_spawn_worker`; on expiry write the error
  file and let the existing finally free the lock.
- **Rationale**: verified: a timed-out EXPORT worker leaves state "exporting" with a dead
  pid, which `state_blocks_new_export` (016) already treats as verifiably-stuck and
  retryable, so no new state machinery is needed; a timed-out conductor worker surfaces via
  run_error.txt exactly like a crash. The message admits paid calls may have completed
  (honest nulls).

## D5. Run listing + resume

- **Decision**: pure `run_view.list_runs` (id, brand, created, gate_state, image,
  export_state; newest-first, limit 50) + `GET /runs` + URL-hash sync via
  `history.replaceState` + a recent-runs panel reusing the viewAttempt open path.
- **Rationale**: run_view is the established read-only run-dir consumer with tolerant JSON
  helpers; the hash is the smallest state that survives refresh/reconnect; replaceState
  avoids history spam; absent hash + untouched panel is provably byte-identical to today.
- **Alternatives**: server-side sessions (state the server must own; against the
  disk-backed-everything pattern); localStorage (survives refresh but not device/browser
  changes, and hides state from the URL the team will paste into chats).

## D6. Server strings stay English; the UI translates its OWN chrome + a display dict

- **Decision**: translate only frontend-owned strings; render the gate panel's closed server
  vocabulary through a `ZH` display dict with English fallback; the playbook carries a
  common-messages table for the English server strings.
- **Rationale**: server strings are contract-pinned across the falsifiable suite (renaming
  them re-pins dozens of value checks for edge-case-only surfaces); the gate vocabulary is
  small and CLOSED (REGISTER_LANE_OPTIONS labels, assumption dimensions, render/dial names),
  so a dict is complete, and the English fallback is honest for anything new.

## D7. Playbook: one source, served

- **Decision**: `frontend/playbook.html` authored directly (app-styled, Chinese), served at
  `GET /playbook`, linked from the shared header; docs/ holds a pointer.
- **Rationale**: the repo is stdlib-only (no markdown renderer); a served HTML page is the
  artifact the team actually uses; a parallel markdown copy would drift (the 007/012 lesson
  about duplicated truth). The spec's "sourced in docs/" intent (durable, reviewable source)
  is met by the committed HTML plus the docs/ pointer.

## D8. requirements.txt content

- **Decision**: freeze the working venv verbatim (openai, anthropic, python-dotenv, pillow,
  numpy, scipy, pymupdf, pyyaml, fonttools, opencv-python, rapidocr-onnxruntime, google-*
  legacy); document `libgl1 libglib2.0-0` as apt prerequisites and opencv-python-headless as
  the server-side alternative; state Python 3.11.
- **Rationale**: the frozen truth of the machine every eye-gate passed on beats a curated
  minimal set that risks omitting a transitive import on the dormant paths; slimming is a
  separate, testable exercise later.
