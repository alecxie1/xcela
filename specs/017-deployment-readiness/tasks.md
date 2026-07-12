# Tasks: Deployment Readiness + Chinese-Ready UI

**Input**: Design documents from `/specs/017-deployment-readiness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/surfaces.md

**Tests**: REQUIRED by the constitution (falsifiable, free). One growing self-test file
`test_deploy_readiness.py`; existing pinned form-greps that cover intentionally translated
strings are UPDATED to pin the CHINESE value in the same commit, never weakened. NO paid call
anywhere in tests; the one paid step is the human flow gate (T012).

**Organization**: grouped by user story; one task = one commit (constitution VII).

## Format: `[ID] [P?] [Story?] Description`

---

## Phase 1: Setup

- [x] T001 Create `test_deploy_readiness.py` scaffold: house check-list style; fixture
      builders `make_brands(tmp)` (a temp brands dir with `<brand>/<logo>.png` files + a
      lean key dict pointing at them, absolute AND brands-relative variants) and a runs-dir
      builder that REUSES `test_export_layers.make_run_dir` by import (the established
      cross-test import pattern); check0 self-checks the fixtures. Commit:
      `feat(017): test scaffold (T001)`.

---

## Phase 2: Foundational (blocking)

- [ ] T002 Create `harness/asset_paths.py` (stdlib-only): `REPO_ROOT`, `brands_dir()` (env
      `XCELA_BRANDS_DIR` else `REPO_ROOT/"brands"`), `resolve_brand_asset(p)` with the
      resolution order absolute-and-exists > brands-relative > repo-relative > `SystemExit`
      naming EVERY tried path (research D1). Test check1: absolute passthrough;
      brands-relative + repo-relative hits; env override respected; the refusal message
      contains all three tried paths (falsifiable values, not presence). Commit:
      `feat(017): brand-asset resolver (T002)`.

---

## Phase 3: User Story 1 - A fresh machine serves the tool (P1) 🎯 MVP

**Goal**: a fresh clone + the two out-of-band items serve the app with zero code edits.

**Independent Test**: scratch-clone bootstrap boots the server; rewritten keys resolve;
missing logo refuses named; existing suites green.

- [ ] T003 [US1] Wire the resolver + kill the fallback + rewrite the keys:
      `harness/scene_author.py` DELETE `LOGO_PATH` (:125) and switch the three consumer
      sites (:1125 thin, :1388, :1627) to `resolve_brand_asset`, LAZY wrt use
      (logo_treatment=omit never resolves; a fed logo with a missing/dangling key refuses
      named); `harness/export_layers.py enumerate_elements` (:88) resolves the key's logo
      through `try_resolve_brand_asset` (non-raising) before the fed-refs compare
      (unresolvable = no logo element, soft honest-null asserted by value); `brand_intake/persist.py place_logo` returns/stores the
      brands-relative `<brand>/<basename>` (validate/assemble tolerate both forms); REWRITE
      `answer_keys/CJXQ.json`, `answer_keys/chajiuxingqiu.json`, `answer_keys/aia.json`
      logo_path to brands-relative, all other bytes unchanged. Tests check2: the rewritten
      CJXQ key resolves to the same absolute file as before on this machine (thin refs
      byte-identical); omit-run needs no logo file; a dangling logo_path refuses with the
      resolver's named SystemExit; place_logo now returns `<brand>/<basename>`; the FULL
      existing sweep stays green (absolute fixture paths pass through). Commit:
      `feat(017): portable brand-asset paths, fallback removed, keys rewritten (T003)`.

- [ ] T004 [P] [US1] `requirements.txt` (pinned freeze of the working venv; header comment:
      Python 3.11, apt `libgl1 libglib2.0-0`, opencv-python-headless alternative) +
      `deploy/bootstrap.sh` (python3.11 check, venv, pip install -r, mkdir output, NAMED
      presence checks for `~/.hermes/.env` and the brands dir covering every committed
      key's logo, next-steps print; never touches secrets) + `deploy/xcela.service`
      (LANG=C.UTF-8, XCELA_* env, Restart=on-failure, TimeoutStopSec=30) + `deploy/Caddyfile` (reverse_proxy
      127.0.0.1:8765, basic_auth + domain placeholders) + `deploy/README.md` (the exact
      out-of-band handoff per plan §2, incl. the restart-after-update note and output/
      retention). Tests check3: requirements parses and pins the core deps (openai,
      anthropic, pillow, numpy, scipy, pymupdf, python-dotenv, opencv-python); `bash -n deploy/bootstrap.sh`
      clean; unit/Caddyfile carry the placeholders; README names both out-of-band items;
      NO secret-shaped strings anywhere in deploy/ (grep). Commit:
      `feat(017): requirements + deploy artifacts (T004)`.

**Checkpoint**: SC-001 provable (quickstart §2 scratch-clone bootstrap).

---

## Phase 4: User Story 2 - A remote tester never loses their run (P2)

**Goal**: refresh/reconnect reopens the run; every past run reachable.

**Independent Test**: list_runs over a fixture output dir; hash-open + picker greps; no-hash
behavior byte-identical.

- [ ] T005 [US2] `frontend/run_view.py` NEW pure `list_runs(output_dir, limit=50)` per
      data-model (id, brand, created from the id timestamp with mtime fallback, gate_state,
      image, export_state; newest-first; tolerant `_load_json`; never raises) +
      `frontend/server.py` `GET /runs` -> `{"runs": [...]}`. Tests check4: a fixture output
      dir with a gated run, a pre-015 run (null gate_state), and an exported run lists
      newest-first with exactly the expected flags; empty dir -> `{"runs": []}`; a corrupt
      gate_state tolerated (null, not a crash); limit honored. Commit:
      `feat(017): run listing (T005)`.

- [ ] T006 [US2] `frontend/index.html`: on load, `location.hash` `#run_<id>` opens that run
      via the viewAttempt path (unknown id = the honest empty run view + the picker);
      `history.replaceState` syncs the hash on every currentRun change; a recent-runs panel
      fetches `/runs` on load (+ a refresh control) and opens an entry on click. Tests
      check5 (form greps, value-bearing): the hash is read on load and written via
      replaceState; the `/runs` fetch and the picker container exist; the hash-absent
      startup path is the pre-017 code path (grep the guard). Commit:
      `feat(017): URL-hash resume + recent-runs picker (T006)`.

---

## Phase 5: User Story 3 - A Chinese-speaking tester works in Chinese (P2)

**Goal**: Chinese briefs match lanes and sizes directly; the UI and playbook read in Chinese.

**Independent Test**: lane/size checks with byte-identity pins; Chinese chrome greps with
unchanged submit values; the served playbook.

- [ ] T007 [US3] `register/derive_register.py`: add the Chinese keywords INSIDE the existing
      tuples exactly per data-model (marketing set incl. 朋友圈/小红书/海报; event set incl.
      手举牌, NOT bare 活动; wall; formal) + `harness/format_size.py resolve_size`
      normalization pre-pass (fullwidth digits/×/spaces, 厘米/公分/毫米/英寸). Tests check6:
      朋友圈推广海报 derives marketing WITH the 014 suppression trace and ZERO usage
      assumptions in the sink; 手举牌 + 营销 in one context derives event_prop (row
      precedence); the wall-posted baseline profile stays byte-identical to the imported
      011 literal; ６０×４０厘米 resolves byte-identically to 60x40cm; a set of current
      ASCII size strings parse byte-identically (pinned); post-normalization garbage still
      takes the honest default + note; one MIXED-language context (上墙 + "marketing")
      derives via the wall row's precedence (the spec's mixed edge case). Commit:
      `feat(017): Chinese usage vocabulary + size normalization (T007)`.

- [ ] T008 [US3] Chinese chrome: `frontend/index.html` + `frontend/onboard.html` labels,
      help, buttons, stage titles, and JS status strings -> simplified Chinese; ids/names/
      select VALUES unchanged; the `ZH` display dict renders the gate panel's closed server
      vocabulary (assumption dimensions, REGISTER_LANE_OPTIONS labels, render/dial names)
      with English fallback. UPDATE (never weaken) the existing pinned form-greps that
      covered translated strings (inventory by grepping test_*.py against the two pages;
      known: test_confirm_gate check13's zero-rows text, test_lossless_brief label greps,
      test_export_layers check6 button strings if touched). Tests check7: Chinese greps for
      the load-bearing labels; formState() submit keys/values unchanged (grep the JS);
      every REGISTER_LANE_OPTIONS label has a ZH entry (drift-guarded by importing the
      options and grepping the dict). Commit:
      `feat(017): Chinese UI chrome + gate display dict (T008)`.

- [ ] T009 [US3] `frontend/playbook.html` (Chinese, app-styled, single source) + `GET
      /playbook` in `frontend/server.py` + the nav link in the shared header of both pages + the one-line docs/ pointer (FR-012).
      Content per FR-012: the draft charter, the journey with costs (~$0.08 confirm is the
      only spend; nudges re-derive free; layered export ~$0.5 opt-in), field guidance incl.
      which fields accept free Chinese, single-flight etiquette (busy 409 = wait), the
      common-messages table (English server string -> Chinese meaning; incl. "no second
      spend", the gate refusals, run_error), troubleshooting, the feedback-channel
      placeholder. Tests check8: the route serves 200 text/html; value greps: both cost
      figures, the 409 etiquette line, at least three common-message rows, the placeholder
      marker; both pages carry the nav link. Commit:
      `feat(017): served Chinese playbook (T009)`.

---

## Phase 6: User Story 4 - The server survives remote misuse (P3)

- [ ] T010 [US4] `frontend/server.py`: bind from `XCELA_BIND`, port argv > `XCELA_PORT` >
      8765 (defaults byte-identical); ONE `do_POST` preamble check of Content-Length
      against `XCELA_MAX_UPLOAD_MB` (default 32) -> 413 named BEFORE any handler/lock;
      `_spawn_worker` subprocess timeout from `XCELA_WORKER_TIMEOUT_S` (default 1800) ->
      on TimeoutExpired the error file carries the named message ("paid calls may already
      have completed") and the finally frees the lock. Tests check9: empty env computes
      ("127.0.0.1", 8765); an oversize Content-Length returns 413 with the pinned wording ("exceeds the ...MB cap") and
      creates no run dir and leaves the lock free; a stubbed sleeping worker with a tiny
      timeout writes the named error file and frees the lock; a timed-out EXPORT lands in
      the 016 dead-pid stuck state and decide_export accepts the retry (composition proof).
      Commit: `feat(017): server env config + upload cap + worker timeout (T010)`.

---

## Phase 7: Polish & Cross-Cutting

- [ ] T011 Fresh-clone proof + full sweep + docs currency: run quickstart §2 (scratch clone,
      `deploy/bootstrap.sh`, server boot with `XCELA_BRANDS_DIR` pointing at the real
      brands dir, `/brands` + `/runs` + `/playbook` respond); run the FULL suite sweep in
      the main repo (green; only the explicitly updated Chinese pins changed); update
      CLAUDE.md (active-feature block: BUILT + structurally green) + SYSTEM_MAP (017
      build-status block) in this same commit. Commit:
      `test(017): fresh-clone proof + full sweep + docs currency (T011)`.

- [ ] T012 HUMAN FLOW GATE (SC-007; the one paid step, ~$0.08 + optional export,
      operator-scheduled, never automated): one end-to-end run through the CHINESE UI
      (Chinese brief incl. 朋友圈-class usage + fullwidth size, gate judged, confirm, image
      judged, optional export + download, then a deliberate refresh reopening the run from
      the URL and the picker). Ideally driven by a China-side tester over the deployed URL
      once provisioning happens; until then locally by the operator. Record the verdict +
      run id in SYSTEM_MAP and here.

---

## Dependencies & Execution Order

- T001 -> T002 (fixtures before the resolver checks) -> T003 (the resolver's consumers).
- T004 is [P]-independent after T001 (pure new files) but sequenced after T003 in practice
  (bootstrap's presence check reads the rewritten keys).
- US2 (T005 -> T006), US3 (T007; T008 -> T009), US4 (T010) are independent of each other
  after Phase 2; the single growing test file makes the practical order linear
  T001..T010. [P] marks the one true file-independence (T004).
- T011 after all code tasks; T012 after T011, human-scheduled.

## Implementation Strategy

MVP = Phases 1-3 (T001-T004): a fresh machine can serve the tool. Phases 4-6 are the
remote-team usability + safety slices, each independently testable. T011 proves the world
unchanged (byte-identity + fresh-clone) and T012 hands the flow to the eye. Stop-and-validate
at every checkpoint: `.venv/bin/python test_deploy_readiness.py` cumulative green.
