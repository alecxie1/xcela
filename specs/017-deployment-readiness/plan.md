# Implementation Plan: Deployment Readiness + Chinese-Ready UI

**Branch**: `017-deployment-readiness` | **Date**: 2026-07-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-deployment-readiness/spec.md`

## Summary

Everything deployment needs that does NOT depend on Richard's answers: portable brand-asset
paths (one resolver, committed keys rewritten relative, the /mnt/c fallback dies), a pinned
requirements.txt + committed deploy/ artifacts (bootstrap, systemd unit, Caddyfile, out-of-band
handoff README), env-configurable bind/port + upload cap + worker wall-clock timeout, GET /runs
+ URL-hash resume + recent-runs picker, Chinese input robustness (Chinese keywords added INSIDE
the existing USAGE_RULES tuples; fullwidth/Chinese-unit size normalization), Chinese UI chrome
(frontend-only) and the Chinese playbook at /playbook. English behavior byte-identical, pinned.

## Technical Context

**Language/Version**: Python 3.11 (`.venv`); frontend stays no-framework HTML + vanilla JS.

**Primary Dependencies**: NO new Python deps. deploy/ targets Ubuntu 24.04 + systemd + Caddy
(templates only; provisioning out of scope).

**Storage**: files only. New: `deploy/*`, `requirements.txt`, `frontend/playbook.html`,
`harness/asset_paths.py`. Rewritten: the three committed `answer_keys/*.json` logo paths.

**Testing**: new `test_deploy_readiness.py` (project self-test style, all FREE) + updates to
existing pinned form-greps where UI strings intentionally change (updated to pin the CHINESE
value, never weakened). Full sweep must stay green.

**Target Platform**: any fresh Linux (dev WSL2 unchanged; defaults byte-identical).

**Project Type**: existing repo; one tiny new harness module + server/frontend edits + data
rewrite + deploy artifacts.

**Performance Goals**: none new; /runs lists at most 50 entries from cheap disk reads.

**Constraints**: byte-identity for English inputs and default configs (FR-013); constitution
(falsifiable tests, honest nulls, no paid calls in tests); register change follows the
011/014/015 additive pattern with pinned literals.

**Scale/Scope**: ~7 code/data tasks + 1 docs/proof task + 1 human flow gate.

## Constitution Check

| Principle | Status | How |
|---|---|---|
| I. Agent-free, not human-free | PASS | No gate is removed; the run list only REOPENS runs; spend still requires the explicit confirm/export clicks. |
| II. Eye is ground truth | PASS | SC-007 is a human flow gate through the Chinese UI; structural tests prove wiring only. |
| III. Falsifiable tests | PASS | Byte-identity pins (English derivations, current size parses, default bind), value-bearing greps (Chinese strings, named refusals), stubbed timeout/cap checks. |
| IV. Generalize, no hand-tune | PASS | The resolver serves every brand; Chinese keywords are lane vocabulary (all brands), not per-brief tuning. |
| V. Honest nulls | PASS | Missing logo = named refusal (the silent fallback is REMOVED); nonexistent run id in the URL = honest message; timeout = named error admitting paid calls may have happened. |
| VI. Reconciliation per-dimension | PASS | A Chinese usage match is an explicit human statement (extends the existing rows, inherits the 014 suppression). |
| VII. Repo durable context | PASS | deploy/README documents the out-of-band handoff; CLAUDE.md + SYSTEM_MAP in the closing commit. |
| Cost discipline | PASS | All tests free; the one human gate is a normal ~$0.08 run. |

## Design detail (binding decisions)

### 1. Portable asset paths (US1)

- NEW `harness/asset_paths.py` (stdlib-only, import-light: usable by scene_author,
  export_layers, brand_intake/persist):
  - `REPO_ROOT = Path(__file__).resolve().parent.parent`
  - `brands_dir() -> Path`: env `XCELA_BRANDS_DIR` else `REPO_ROOT / "brands"`.
  - `try_resolve_brand_asset(p: str) -> str | None`: absolute and exists -> as-is; else
    `brands_dir()/p`; else `REPO_ROOT/p`; else None. Pure given the filesystem.
  - `resolve_brand_asset(p: str) -> str`: the raising form over try_resolve: `SystemExit`
    naming every tried path (FR-002; never a substitute).
- `harness/scene_author.py`: DELETE `LOGO_PATH` (:125). At the three consumer sites
  (:1125 thin, :1388, :1627 legacy/kit), replace `brand_key.get("logo_path", LOGO_PATH)`
  with resolution that is LAZY with respect to use: when `logo_treatment=omit` skips feeding
  the logo, no resolution happens (a logo-less brand can still run with omit); when the logo
  IS fed, `resolve_brand_asset(brand_key["logo_path"])`, and a missing/dangling key refuses
  named.
- `harness/export_layers.py enumerate_elements` (:88): resolve the key's logo through
  `asset_paths.try_resolve_brand_asset` (the non-raising form: same order, returns None
  instead of SystemExit) before the fed-refs membership compare; an unresolvable logo means
  no logo element (the run demonstrably did not feed it), asserted by value in check2.
- `brand_intake/persist.py place_logo`: return/store the BRANDS-RELATIVE path
  (`<brand>/<basename>`) so newly onboarded keys are portable; `assemble_key`/`validate_key`
  tolerate both forms (absolute legacy keys keep working per FR-001).
- DATA: rewrite `answer_keys/CJXQ.json`, `chajiuxingqiu.json`, `aia.json` logo_path to
  brands-relative (`CJXQ/jos cha logo.png`, `aia/assets/AIA-logo.png`, ...). On this machine
  they resolve to the same absolute files (run_manifest bytes unchanged here).

### 2. Environment + deploy artifacts (US1)

- `requirements.txt`: pinned freeze of the working venv (opencv-python kept as-is; the
  libgl1/libglib2.0-0 system prerequisite documented; `opencv-python-headless` noted as the
  server-side alternative). Python 3.11 stated.
- `deploy/bootstrap.sh`: python3.11 check, venv create, `pip install -r requirements.txt`,
  `mkdir -p output`, PRESENCE checks with named messages for the two out-of-band items
  (`~/.hermes/.env`, a brands dir containing every committed key's logo), prints next steps.
  Never touches secrets.
- `deploy/xcela.service`: systemd template (WorkingDirectory=repo, `LANG=C.UTF-8`,
  `Environment=XCELA_BIND=127.0.0.1 XCELA_PORT=8765`, ExecStart=.venv/bin/python
  frontend/server.py, Restart=on-failure, TimeoutStopSec=30 for a bounded stop). Keys keep loading from `~/.hermes/.env` via the
  app's existing dotenv (HOME set by the unit's User).
- `deploy/Caddyfile`: reverse_proxy 127.0.0.1:8765 + `basic_auth` placeholder + auto-TLS
  domain placeholder.
- `deploy/README.md`: the exact handoff: clone, bootstrap, scp the brands dir + key file,
  caddy hash-password, systemctl enable, RESTART-AFTER-UPDATE note (the known server.py
  reload gotcha), retention note for output/.

### 3. Server config + guards (US4)

- `frontend/server.py main()`: bind from `XCELA_BIND` (default "127.0.0.1"), port from argv
  (existing contract, wins) else `XCELA_PORT` else 8765. Defaults byte-identical.
- Upload cap: `MAX_UPLOAD_BYTES` (env `XCELA_MAX_UPLOAD_MB`, default 32MB). ONE check at the
  top of `do_POST` against Content-Length -> 413 `{"error": "upload too large: <n>MB
  exceeds the <cap>MB cap"}` (the contract wording, pinned in check9) before any handler,
  run dir, or lock.
- Worker timeout: `_spawn_worker` gains `subprocess.run(..., timeout=WORKER_TIMEOUT_S)` (env
  `XCELA_WORKER_TIMEOUT_S`, default 1800); on `TimeoutExpired`, write the error file ("worker
  timed out after Ns; paid calls may already have completed, inspect the run dir") and fall
  through to the existing finally (lock frees). An export killed this way lands in the 016
  stuck-state machinery (dead pid -> reclaimable retry) BY CONSTRUCTION.

### 4. Run browsing (US2)

- `frontend/run_view.py`: NEW pure `list_runs(output_dir, limit=50) -> list` newest-first:
  `{id, brand, created, gate_state, image, export_state}` from run_meta/gate_state/
  export_state + generated.png presence; `_load_json` tolerance throughout; never raises.
- `frontend/server.py`: `GET /runs` -> `{"runs": list_runs(OUTPUT)}`.
- `frontend/index.html`: on load, a `location.hash` of `#run_...` opens that run (reusing the
  viewAttempt path; unknown id renders the honest run_view empty state + the picker);
  `history.replaceState` syncs the hash whenever currentRun changes; a recent-runs panel
  (fetch /runs on load + a refresh control) lists entries and opens on click. Hash absent +
  picker untouched = pre-017 behavior byte-identical.

### 5. Chinese input robustness (US3)

- `register/derive_register.py`: Chinese keywords added INSIDE the existing tuples (NOT new
  rows), so precedence and the 014 suppression (which compares row identity to
  `MARKETING_USAGE_KEYWORDS`) hold with zero new logic. The spec's "additive rows" language
  is satisfied as additive RULE VOCABULARY; the falsifiable surface is FR-009's behavior.
  - Extend the `MARKETING_USAGE_KEYWORDS` tuple LITERAL at its definition with ("朋友圈",
    "小红书", "社交媒体", "公众号", "微博", "营销", "宣传", "推广", "海报") (NEVER a
    later `+=`, which would rebind the name and break the 014 row-identity suppression);
    suppression + REGISTER_LANE round-trip inherit.
  - event row tuple extended in place with `("手举牌", "举牌", "应援", "打卡", "活动现场")` (keeps first-row
    precedence; deliberately NOT bare 活动, which appears inside 促销活动).
  - wall row extended with `("上墙", "墙贴", "张贴")`; formal row with `("正式文件", "公告", "通知")`.
  - Multi-character keywords only (the spec's over-match edge case).
- `harness/format_size.py resolve_size`: a normalization pre-pass on the raw string:
  fullwidth digits -> ASCII, `×`/`Ｘ`/`ｘ`/`＊` -> "x", fullwidth spaces stripped,
  `厘米`/`公分` -> "cm", `毫米` -> "mm", `英寸` -> "in". Identity on pure-ASCII input
  (current parses byte-identical, pinned).

### 6. Chinese UI chrome + playbook (US3)

- `frontend/index.html` + `frontend/onboard.html`: labels, help text, buttons, stage titles,
  and JS-rendered status strings -> simplified Chinese. IDs, names, and select VALUES
  unchanged (canonical English values still submitted; asserted). A small `ZH` dict maps the
  gate panel's closed server vocabulary (assumption dimensions, option labels like
  "marketing piece", lane/render names) to Chinese at render time, falling back to the
  English string when unmapped (server payloads untouched).
- Existing test form-greps that pin intentionally-translated strings (e.g. test_confirm_gate
  check13's zero-rows branch text, test_lossless_brief label greps) are UPDATED in the same
  commit to pin the CHINESE value (contract evolution, never weakened). Inventory at
  implementation time via a grep of test files against index/onboard strings.
- `frontend/playbook.html` (Chinese, app-styled, SINGLE source) served at `GET /playbook`;
  nav link added to the 010 shared header on both pages. Content per FR-012, including the
  common-messages table (English server string -> Chinese meaning) and the feedback-channel
  placeholder. docs/ gets a one-line pointer (FR-012's "sourced in docs/" is satisfied by the
  pointer; duplicating the content in markdown would guarantee drift).

## Project Structure

```text
specs/017-deployment-readiness/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/surfaces.md
└── checklists/requirements.md

harness/asset_paths.py            # NEW resolver (stdlib)
harness/scene_author.py           # LOGO_PATH deleted; resolver at 3 sites
harness/export_layers.py          # resolver in enumerate_elements
harness/format_size.py            # normalization pre-pass
register/derive_register.py       # Chinese keywords inside existing tuples
brand_intake/persist.py           # place_logo stores brands-relative
answer_keys/{CJXQ,chajiuxingqiu,aia}.json   # rewritten logo_path
frontend/server.py                # env bind/port, upload cap, worker timeout, /runs, /playbook
frontend/run_view.py              # list_runs
frontend/index.html  onboard.html # Chinese chrome, hash resume, recent-runs, ZH dict
frontend/playbook.html            # NEW served playbook
deploy/{bootstrap.sh, xcela.service, Caddyfile, README.md}
requirements.txt
test_deploy_readiness.py          # NEW free suite
```

**Structure Decision**: one tiny shared module for the resolver (three consumers across
harness/ and brand_intake/); everything else lands in the files that own the behavior today.

## Complexity Tracking

No constitution violations; table not needed.
