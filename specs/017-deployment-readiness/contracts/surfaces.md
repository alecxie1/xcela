# Contracts: Deployment Readiness + Chinese-Ready UI (017)

## HTTP (frontend/server.py; additive only)

### GET /runs  (FREE, zero writes)
- 200 `{"runs": [run-listing entries, newest-first, <=50]}` (see data-model). Empty list on a
  fresh server (honest empty state, not an error).

### GET /playbook  (FREE)
- 200 text/html: the Chinese playbook page (frontend/playbook.html), linked from the shared
  header on both existing pages.

### do_POST preamble (every POST route)
- Content-Length > cap -> 413 `{"error": "upload too large: <n>MB exceeds the <cap>MB cap"}`
  BEFORE any handler, run dir, or lock. Cap from XCELA_MAX_UPLOAD_MB (default 32).

### Unchanged routes
Every existing route keeps its exact contract; run_view's per-run payload is unchanged
(list_runs is a NEW surface, not a change to /run/<id>/stages).

## Server process

- Bind: XCELA_BIND (default 127.0.0.1). Port: argv[1] wins (existing contract), else
  XCELA_PORT, else 8765. No env, no argv = byte-identical to today.
- `_spawn_worker`: subprocess.run gains timeout=XCELA_WORKER_TIMEOUT_S (default 1800s); on
  TimeoutExpired the error file (run_error.txt / export_error.txt per caller) carries a named
  message stating paid calls may already have completed; the single-flight lock frees in the
  existing finally. A timed-out export lands in the 016 dead-pid stuck state (retryable).

## Python (internal)

```python
# harness/asset_paths.py (stdlib-only)
brands_dir() -> Path            # env XCELA_BRANDS_DIR else <repo>/brands
resolve_brand_asset(p) -> str   # absolute-and-exists > brands-relative > repo-relative
                                # > SystemExit naming every tried path

# frontend/run_view.py
list_runs(output_dir, limit=50) -> list   # pure, tolerant, newest-first (see data-model)
```

- `scene_author`: `LOGO_PATH` constant REMOVED. Logo resolution happens only when the logo is
  actually fed (logo_treatment=omit runs never resolve); missing/dangling logo_path = the
  resolver's named SystemExit.
- `export_layers.enumerate_elements`: the key's logo resolves through the same resolver
  before the fed-refs membership compare; unresolvable = no logo element.
- `derive_register`: Chinese keywords INSIDE the existing tuples; row identities unchanged
  (MARKETING_USAGE_KEYWORDS remains THE marketing row object; 014 suppression inherits).
- `format_size.resolve_size`: normalization pre-pass, identity on ASCII input.
- `brand_intake/persist.place_logo`: returns/stores `<brand>/<basename>` (brands-relative).

## UI (frontend/index.html, onboard.html)

- `location.hash` `#run_<id>` on load opens that run; `history.replaceState` syncs the hash on
  every currentRun change; unknown id renders the honest empty run view + the picker.
- Recent-runs panel: populated from GET /runs on load + manual refresh; click opens the run
  via the existing attempt-switch path (clears panels, restarts the poll interval).
- All chrome strings simplified Chinese; element ids/names and select VALUES unchanged (the
  submitted form JSON for a given interaction is byte-identical to today); the gate panel
  renders server vocabulary through the ZH dict with English fallback.
- No hash + no picker interaction = pre-017 rendering byte-identical.

## Committed data

- `answer_keys/{CJXQ,chajiuxingqiu,aia}.json`: logo_path rewritten brands-relative; every
  other byte unchanged.
- `requirements.txt`: pinned freeze; header comment names Python 3.11 + apt prerequisites.
- `deploy/`: bootstrap.sh, xcela.service, Caddyfile, README.md; placeholders only, no secrets.
