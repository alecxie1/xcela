# Feature Specification: 021-auth-multitenancy

**Feature Branch**: `021-auth-multitenancy`
**Created**: 2026-07-14
**Status**: APPROVED (plan-as-spec, operator-approved in-session 2026-07-14), NOT STARTED.
**Resume note**: implementation has NOT begun; start at T001. The exploration inventory's
key line numbers are embedded in the Context section below and were verified 2026-07-14.

# Login + whitelist users + per-user brands/runs, super sees all

## Context

Kevin's request: no users/permissions exist today; add a login page (whitelist of designated
users), each user sees only their own brands and runs, a super user sees everything. UI can
be simple. The codebase is stdlib-only, disk-backed, stateless-server; the inventory
confirms zero existing auth surface (no cookies, no sessions, no secrets usage), two
dispatch choke points (`do_GET` server.py:360, `do_POST` :414 after the size cap), one
`_send` that needs an optional-headers extension (:351), one run_meta write for run
ownership (:462), an `owner` field that rides through `validate_lean_key` untouched, three
list functions to filter (`server._brands` :50, `brand_manager.list_brands_detail` :42,
`run_view.list_runs` :39), four duplicated topnav blocks, and index.html fetches that never
check status (a shared wrapper needed for 401 handling).

## Binding design decisions

1. **Auth activates only when the users file exists.** No users file = today's behavior
   byte-identical (our dev machines and the reference VM stay open; Kevin opts in by
   creating users). This is the byte-identity pin.
2. **Real passwords** (`hashlib.scrypt` + per-user salt, stdlib), not a bare username
   whitelist (spoofable = worthless). Whitelist = presence in the users file.
3. **Legacy/unowned artifacts are visible to every logged-in user** (their existing brands
   `1234`/平安银行 and past runs keep working for the whole team); NEW artifacts get an
   `owner` and are isolated; `super` sees and manages everything. A super can assign an
   owner to an unowned brand via the manager (the migration path). Unowned brands remain
   manageable by any authenticated user (small-team pragmatism, documented).
4. **Sessions are disk-backed** (`sessions.json` beside the users file): token =
   `secrets.token_urlsafe(32)`, HttpOnly + SameSite=Lax cookie, 30-day expiry, logout
   deletes the token; a server restart logs nobody out.
5. Store location follows the runtime-state pattern: `XCELA_USERS_FILE` env override in
   `harness/asset_paths.py`, default `<repo>/users.json`; gitignored under the existing
   Secrets block; `sessions.json` lives beside it. Hermetic tests via the env var
   (the test_brand_manager.py workspace pattern).

## Components

### frontend/auth.py (HTTP-free core + CLI)
- `enabled()`, `verify(username, password) -> bool` (scrypt n=2^14 r=8 p=1, salt via
  secrets; constant-time compare), `role(username)`, `mint_session(username) -> token`,
  `session_user(cookie_header) -> {user, role} | None` (expiry-checked),
  `drop_session(token)`.
- CLI: `python frontend/auth.py add <user> [--super]` (getpass prompt), `remove`, `list`
  — Kevin's whole user management v1; no admin UI.

### The gate (frontend/server.py)
- `_send` gains optional `headers: dict` emitted before `end_headers()`.
- Choke points at the top of do_GET/do_POST: resolve `self._user` from the cookie; when
  `auth.enabled()` and no session: the four HTML pages 302 to `/login`, every API route
  401 `{"error": "login required"}`; exempt: `GET /login`, `POST /login`,
  `GET /whoami` (returns `{auth: false}` when disabled, else `{user, role}` or 401).
- `/login` page (frontend/login.html: Chinese, username+password+error line);
  `POST /login` verifies + Set-Cookie + `{ok}` ; `POST /logout` drops + clears cookie.
- JS: a tiny shared `jf()` fetch wrapper (401 -> location=/login) replacing the raw
  fetches in index.html and manage.html (onboard.html's existing `jpost` gains the same
  check); each topnav gets a user chip + 退出 button rendered from `/whoami` (hidden when
  auth is off).

### Ownership + filtering
- Runs: `POST /run` writes `owner` into run_meta.json (only when auth enabled);
  `list_runs` entries carry `owner`; the `/runs` route filters (non-super: own + unowned);
  every `/run/<id>/*` route (stages, image, export/plan, export, layers.zip, answer,
  confirm) checks: auth off OR super OR owner==user OR unowned, else 403 named.
- Brands: onboarding save threads the user in (key["owner"] set post-build, pre-validate —
  validate_lean_key ignores extras, proven); `_brands()` and `list_brands_detail()` filter
  the same way (run-creation's brand check uses the filtered list, so a user cannot run on
  another's brand); brand_manager writes require owner/super for OWNED brands (any
  authenticated user for unowned); `update_brand` gains a super-only `owner` payload field
  (assign/transfer). CLI intake stays owner-less (unowned = shared).

### Docs + ops
- .env.example + README (XCELA_USERS_FILE + the enable/disable contract), deploy/README
  (enabling auth: run the CLI, restart; sessions/users are runtime state, never committed),
  playbook 登录 section (whitelist, 退出, 权限模型 in one paragraph).

## Tests (new test_auth.py, hermetic via XCELA_USERS_FILE tmp; plus the byte-identity pin)
- scrypt roundtrip + wrong password + non-whitelisted user by value; session mint/lookup/
  expiry/logout; CLI add/remove/list.
- THE PIN: no users file = open access byte-identical (ephemeral server instance: / and
  /brands answer without a cookie, exactly the check9 pattern); with users = pages 302,
  APIs 401, login sets the cookie, whoami round-trips.
- Ownership matrix BY VALUE over a tmp workspace: userA/userB/super x (owned-A, owned-B,
  unowned) for runs list, brands list, per-run access (403s), brand writes, super
  owner-assign; run creation on another user's brand refused.
- Full sweep green (auth off in every existing suite by construction: no users file).

## Task breakdown (one commit each)
- T001 auth core + asset_paths.users_file + gitignore + CLI + core tests.
- T002 the gate: _send headers, choke points, /login /logout /whoami + login.html + jf()
  wrapper + nav chips + the open-access byte-identity pin.
- T003 ownership: run owner + filters + per-run guards; brand owner + filters + write
  permissions + super assign; the matrix tests.
- T004 docs + full sweep + ship (origin + vm; VM stays auth-OFF) + the Kevin enable-guide
  (paste-able Chinese: pull, python frontend/auth.py add <user> for each teammate +
  one --super, restart; how isolation behaves; legacy artifacts stay shared).
- T005 HUMAN GATE: Kevin creates his users and the team verifies isolation unassisted.

## Out of scope (named, so nobody expects them)
- Password self-service/reset (the CLI re-adds a user to reset), per-user API spend
  accounting, admin web UI for users, sharing/transfer of runs, CSRF tokens (SameSite=Lax
  + JSON POSTs; acceptable for the whitelist team), rate limiting.

## Verification
- Free: test_auth.py + full sweep; ephemeral-server proofs for both auth states.
- Human: Kevin's team logs in, userA cannot see userB's brand/run, super sees all.
