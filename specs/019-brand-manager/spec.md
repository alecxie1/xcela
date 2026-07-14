# Feature Specification: 019-brand-manager

**Feature Branch**: `019-brand-manager`
**Created**: 2026-07-14
**Status**: Approved (plan-as-spec: the approved session plan, verbatim; the design section
is binding, tasks tracked in tasks.md)

# A brand database (view / edit / delete), keys become runtime state

## Context

Kevin's team misread our five committed answer keys as production-ready brands with full
assets; the real intent was self-onboarding. Alec's direction: instead of visibility hacks,
ship a simple BRAND DATABASE: users view, edit, modify, and delete brands themselves. This
subsumes the misunderstanding (they delete/inspect what they don't want), Kevin's asset-list
request, and future brand maintenance.

Investigated facts that bind the design:
- Kevin made NO UI changes (their live index.html is byte-identical to ours; the
  "unrecognized feature" in Alec's screenshot is our 017 recent-runs picker). His one real
  change is the backend model swap (GPT-5.5), out of 019's scope (a follow-up makes model
  names env vars so he can un-fork).
- Committed keys cannot be user-deleted on a deployed clone (git pull resurrects them), so
  the five demo keys MUST leave git for delete to mean anything: `answer_keys/` becomes
  runtime state (gitignored), demo keys move to committed `tests_support/demo_keys/`.
- Churn is contained: conductor's key check is CLI-entry only (:1399-1401);
  `scene_author.load_brand` (:327) is the runtime reader; `persist.key_path/ANSWER_KEYS` and
  `server.ANSWER_KEYS/_brands` are the other consumers. Seven suites read key files directly
  (repoint to tests_support/demo_keys); suites that subprocess real derives (test_confirm_gate
  et al.) get the location via a new env override.
- `validate_lean_key` is the existing edit gate (fail loud); `persist.write_key` writes;
  `key_exists` is the onboarding collision guard (an EDIT is a deliberate overwrite and uses
  a distinct route). `asset_paths.try_resolve_brand_asset` gives honest logo status.
- gpt-image-2 accepts PNG/JPG/WebP only: the logo guard (Kevin's "只能识别JPG" report) lands
  once, shared by the wizard and the manager's logo-replace.

## Design

### US1 - keys are runtime state (P1, the enabler)
- `asset_paths.keys_dir()`: env `XCELA_ANSWER_KEYS_DIR` else `REPO_ROOT/"answer_keys"`,
  consumed by persist (key_path/write), server (_brands + ANSWER_KEYS uses), conductor's CLI
  check (:1399-1401), scene_author.load_brand, and any register consumer found at impl.
- `git rm --cached` the five demo keys; `answer_keys/` gitignored (+ .gitkeep); the five move
  (committed) to `tests_support/demo_keys/` for the suites. Local working copies stay on
  disk (dev machines unaffected at runtime).
- Suites: the seven direct readers repoint to tests_support/demo_keys; subprocess-spawning
  checks export `XCELA_ANSWER_KEYS_DIR=tests_support/demo_keys` (read-only cases) or a tmp
  copy (write cases). Full sweep must stay green.
- Ops consequence, documented: on `git pull`, deployed clones LOSE the five demo keys from
  disk (desired on Kevin's box; on OUR reference VM, T004 copies them back as runtime state).
  User-created keys (e.g. their "1234") are untracked and survive.

### US2 - the brand manager (P1, the feature)
- New page `frontend/manage.html` (品牌管理), added to the shared nav on all pages.
- Routes (thin, HTTP-free deciders in the established style):
  - `GET /brands/detail`: `[{brand, name_cn, name_en, colors:[{hex, role}], logo_path,
    logo_resolved, verified_by, verified_date}]` (logo_resolved via try_resolve; read-only).
  - `POST /brand/<id>/update`: names + color roles/hexes; `validate_lean_key` gates; write via
    persist.write_key (deliberate overwrite; the wizard's key_exists guard untouched).
  - `POST /brand/<id>/logo`: multipart replace; the shared format guard (png/jpg/jpeg/webp,
    named refusal); place_logo + key update + validate.
  - `POST /brand/<id>/delete`: deletes the KEY file only (assets under brands/<id>/ remain on
    disk; the response says so honestly); UI requires typing the brand id to confirm.
  - All manage WRITES refuse with the single-flight 409 while a run is in flight (a derive
    mid-flight must not lose its key).
- UI: table of brands with color swatches, logo thumbnail + ✓素材齐全/✗缺少logo, edit-in-place
  for names/roles, the logo replace control, the guarded delete. Playbook gains a 品牌管理
  section; the run form shows the selected brand's asset status line (Kevin's ask).

### US3 - logo format guard (P2)
- One shared validator (extension + a cheap header sniff) used by wizard save AND manager
  logo-replace; wizard input accept narrows. Named error, never a generation-time surprise.

### Tests (new test_brand_manager.py + updates; all free)
- keys_dir override by value; the seven repointed suites green; a tmp-keys workspace proves
  update/delete/list end-to-end (HTTP-free deciders); validate rejects a bad edit (unchanged
  file after refusal, byte-compared); delete refuses while inflight; format guard by value
  (png ok, svg named refusal); /brands/detail honesty on a dangling logo; full sweep.

## Task breakdown (one commit each)
- T001 `keys_dir()` + consumer wiring + env override + suite repoints + demo keys move +
  gitignore. (The big mechanical one; full sweep green is its bar.)
- T002 manage deciders + routes + `GET /brands/detail` + tests.
- T003 `frontend/manage.html` + nav + run-form asset-status line + playbook section + greps.
- T004 shared logo format guard (wizard + manager) + tests; docs currency (CLAUDE.md /
  SYSTEM_MAP / README layout); full sweep; push origin + vm; VM ops (copy demo keys back as
  runtime state, restart).
- T005 comms: paste-able Chinese message to Kevin (pull to get 品牌管理; demo brands now
  deletable/gone from git; the screenshot feature is ours; his model swap: a follow-up will
  make models .env-configurable so he can un-fork) + HUMAN GATE: Kevin/designer manage their
  brands without us.

## Out of scope (named follow-ups)
- 020 candidate: XCELA_TEXT_MODELS / XCELA_IMAGE_MODEL env config (de-fork Kevin's GPT-5.5
  swap; byte-identical defaults).
- SGP droplet teardown: pending Alec's confirmation the designer is fully on their URL.

## Verification
- Free: new suite + full sweep; scratch-clone boot shows an EMPTY brand list (fresh-deploy
  truth); reference VM after T004 still lists our brands (runtime copies).
- Human: Kevin pulls and manages brands unassisted; the designer's dropdown shows only their
  real brands.
