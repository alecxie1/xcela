# CLAUDE.md — Xcela (Handyprint Brand Design Tool)

> **The engineer's brief, loaded into every session. Keep it LEAN.** Frontier models
> follow ~100-150 instructions before quality degrades uniformly, so this root file
> stays short and POINTS to detail that loads on demand. When this file and the code
> disagree, the CODE wins, and you fix this file in the same commit.
>
> **Deeper context, read on demand (do NOT inline it here):**
> - `SYSTEM_MAP.md` — project STATUS: what works, the live regroup notes, the roadmap. **Read its top block first.**
> - `docs/ARCHITECTURE.md` — full module map, pipeline, glossary, toolchain, pitfalls.
> - `.claude/rules/*.md` — path-scoped rules that auto-load only when you touch matching files.

## What this is (one line)
Get a non-designer from a messy brief + brand assets to a **handoff-quality DRAFT**
marketing asset (today: die-cut event signs, 手举牌). **Drafts a human finishes, NOT final art.**

## Core principles (do not violate)
1. **Agent-free ≠ human-free.** Kill the AI stagehand (silent glue + invisible judgment).
   Keep the human at the INPUT gates (brief/reference) and TASTE gates (approve/nudge).
   Never design toward "one command, walk away."
2. **Ground truth = the user's eye, not VLM scores.** Vision models over-score. Verify
   artifacts on disk; never trust a model's self-graded PASS.
3. **Falsifiable tests only.** Assert VALUES the wrong implementation cannot satisfy, not
   token-presence (`"stroke" in prompt` is a no-op gate). Build what GENERALIZES, never
   hand-tune to one image.
4. **Generalizes vs task-taste.** Before any fix ask: does this help the TOOL (all
   brands/tasks) or just this IMAGE? Task-taste is a human nudge, do NOT bake it in.
5. **Honest nulls.** When a step can't do its job, emit null + a note and fall back
   explicitly. Never invent geometry or fabricate a result. Record every fallback.
6. **No em-dashes in any text written FOR THE USER.** Use commas, colons, parentheses.

## The intellectual core (or nothing downstream makes sense)
Brand DNA and task needs DIVERGE (AIA = corporate red/sharp/logo/rectangular; an event
sign wants playful/rounded/no-logo/die-cut). **Reconciliation is the whole game:** brand
governs HARD (color, fonts, logo), task governs SOFT (atmosphere, shape, register),
resolved per-dimension into a `register_profile` (anchors_held vs locks_flexed).
**Direction vs magnitude:** subfields set DIRECTION (which register lane); a reference
image sets MAGNITUDE (how far, via blind vision score). See `docs/ARCHITECTURE.md` §2.

## Two job types (drives most branches in the code)
- **Reference job** (a reference image is supplied): analyzer → aligned prompt + fed crop;
  tier-3 SKIPPED; chroma OFF; deliverable = final.png.
- **No-reference job**: Claude authors a tier-3 scene; chroma ON (#00B140); deliverable =
  cutout.png. Full table in `docs/ARCHITECTURE.md` §3.

## Where things live (one-liner each; full map in docs/ARCHITECTURE.md §5)
- `harness/conductor.py` — the human-gate ORCHESTRATOR (top of the tree, stdlib-only; routes
  kit brands through the kit path, kit-less brands through the legacy render-and-scrub path).
- `harness/scene_author.py` — the single-sign engine (tier-3 author OR aligned-prompt OR
  kit reserve-box mode via `--kit-profile` + `--composition`).
- `harness/kit.py` — KIT loader/validator (stdlib) + derived `kit_profile` (answer key wins).
- `harness/compose_select.py` — deterministic meaning→icon + collision-avoiding archetype pick.
- `harness/format_size.py` — (002, stdlib) brief `format_size` → valid gpt-image-2 pixel size,
  aspect-preserving nearest a configurable target area (default ~1.57 MP). Profile-agnostic.
- `harness/prompt_elements.py` — (002, stdlib) verbatim mandatory/forbidden → prompt clause.
- `harness/review.py` — (002, stdlib) read-only self-service review digest over a run's artifacts.
- `harness/closed_loop_composite.py` — PLACEMENT (place_measured + legacy closed_loop).
- `harness/measure_canvas.py` — the SENSOR (OCR + container geometry).
- `harness/composite_text.py` — licensed-font COMPOSITOR + compliance manifest + fit-to-zone clamp.
- `register/` — reconciliation engine (derive_register = direction, calibrate = magnitude,
  reference_style_to_prompt = the analyzer + dial).
- `extract_colors.py` / `extract_text_layer.py` — (proven, model-free) deterministic brand extractors
  (OCR+pixel reconcile / text-layer fonts). REUSED by 005; `render_page` is 1-INDEXED.
- `brand_intake/` — (005, stdlib) brand-onboarding FRONT-half over those extractors: `page_finder`
  (suggest 1-indexed spec pages), `extract` (reuse wrappers), `assemble_key` + `validate_key` (lean
  key + fail-loud), `intake.py` (CLI: PDF -> verify gate -> answer_keys/<brand>.json). NOT the v3 scaffold.
- `frontend/` — (004 + 006 + 007, stdlib) THIN local web app over the CLI. 004 live-runner: `inputs_writer`
  (form -> 002 JSON), `run_view` (run dir -> progressive stages), `runner` (build/launch `conductor
  --thin`), `server.py` + `index.html`. 006 onboarding gate: `onboard.py` (3-step wizard over a
  transient draft, wraps the 005 brand_intake modules), `multipart.py` (stdlib upload), `onboard.html`
  + the `/onboard/*` routes. 007 reference upload: `uploads.py` (`save_upload`, the ONE save-upload home
  for the 004 reference + the 006 logo); `POST /run` is multipart (a `form` JSON field + a `reference`
  file) via `server.parse_run_form` / `write_run_inputs` (the reference saves into the run dir, its path
  becomes `reference_image`). Shells out + reads artifacts; never reimplements generation/extraction.
- `brand_intake/persist.py` — (006, shared) the one write home (key_exists/place_logo/write_key) the
  005 CLI and the 006 web gate both call.
- `answer_keys/<brand>.json` — brand DNA. `config/<brand>.yaml` — thin-spine config.
  `kits/<brand>.json` — human-authored Kit of Parts (icon + layout vocabularies; committed DATA).
- `brands/ output/ .env` — GITIGNORED (licensed fonts, client IP, secrets, big PNGs).

## Toolchain
- Python 3.11 in `.venv`. Always run as `.venv/bin/python <script>`.
- Install a dep: `uv pip install --python .venv/bin/python <pkg>`.
- API keys load from `~/.hermes/.env` via dotenv. Never hardcode or print keys.
- Models: Anthropic `claude-opus-4-5` → `claude-sonnet-4-6` (authoring/vision);
  OpenAI `gpt-image-2` (generation). Canvas 1536×1024. Chroma key #00B140.

## How to test (the FREE structural surfaces — use BEFORE spending)
```
.venv/bin/python test_conductor.py            # conductor self-test (dry-run, no paid calls)
.venv/bin/python test_confirm_gate.py         # 015 pre-spend gate self-test (incl. a real FREE derive run)
.venv/bin/python test_render_and_scrub.py     # axis A+B self-test (--explain, no paid calls)
.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json \
    --out /tmp/dry --dry-run --no-approve      # plan only, NO model calls
```
The one PAID run: `.venv/bin/python harness/conductor.py --brand aia --inputs conductor_inputs_example.json`
→ judge `output/run_*/sign_*/final.png` with the HUMAN EYE. **Never put paid image
generation inside a self-test.** A green self-test ≠ correct output; only the eye validates pixels.

## Dev workflow (spec-driven — supersedes the old "no commits" line in *_SPEC.md files)
- The REPO is the durable context (this file + SYSTEM_MAP + specs + tests + git history).
  Hold the project in the repo, not the conversation.
- **One spec → one task → one module → one falsifiable test → one commit.** Small enough
  to fit a fresh context. Spec Kit (`/specify`, `/plan`, `/tasks`, `/implement`) drives this.
- Commit per task. `origin` = github.com/alecxie1/xcela (private; IP/secrets gitignored).
- Keep this file + SYSTEM_MAP current in the SAME commit that makes them stale. A stale
  brief actively misleads the next session.

## Current frame (live state in SYSTEM_MAP header + journey 4)
The WORKING PRODUCT today is the THIN ROUTE in the browser (journey 4 in SYSTEM_MAP): onboard a
brand once via the `/onboard` wizard (005/006), fill the guided run form (004/012) with a style
reference + optional product photos (007/013), `conductor --phase derive` composes the plan (003)
with render modes (009), a render-aware + explicit-usage register (011/014), and role-aware palette
(008), then STOPS at the 015 pre-spend gate (derived plan + every recorded assumption, answers
re-derive free); the operator confirms (the only spend) and judges final.png; approved runs export
per-element layers.zip (016, eye-verified 2026-07-10). Paid eye-gates passed on CJXQ
(011/012/014/015/016, plus the 013 T009 photographic product run: 013 fully closed).
Next named feature: **017-deployment-readiness** (deploy for Richard's team in China; BLOCKED on
the answers in `docs/DEPLOYMENT_QUESTIONS.md`, forwarded 2026-07-10; provisional plan in the
SYSTEM_MAP housekeeping block: Singapore/Tokyo VM for API egress, Caddy TLS + auth, portable
asset paths + requirements.txt + run-list page, Chinese playbook at /playbook). Brand-key
enrichment (the brand-level product library) is DEFERRED 2026-07-08: zero pixel change, convenience
only, products so far are campaign-specific (rationale in the SYSTEM_MAP housekeeping block). Known taste gap:
thin-route logo lockups are model-probabilistic (nudge today; the licensed/composite moat is the
real fix). The KIT path (001, per-message icon + layout + reserved-zone compositing) is BUILT but
DORMANT since the 6/23 regroup (its T020 eye test was confounded; a clean kit eye-PASS is owed if
revived); kit-less brands keep the legacy render-and-scrub path. Details: `docs/ARCHITECTURE.md` §9.

## Top pitfalls (full list in docs/ARCHITECTURE.md §11)
- Legacy `place_measured` inherits gpt's text size (failure (a)); the KIT path instead uses
  `composite_text.fit_text_to_zone` (type sized DOWN to the reserved zone, honest-null if it
  cannot fit). Use the kit path for kit brands; the clamp is the generalizing fix.
- `measure`'s legacy HSV path is fragile; the chroma path is the proven one.
- Don't reuse `reanchor()` for render-and-scrub (it centers planned text on free space —
  the opposite of matching gpt's painted geometry).
- VLM vision extraction is non-deterministic (figure/ground inversion, topic↔register).

## Spec Kit (active workflow)
Specs live in `specs/`. Slash commands: `/speckit-specify` (write the spec), `/speckit-plan`
(technical plan), `/speckit-tasks` (break into testable tasks), `/speckit-implement` (build
one task at a time). When working a feature, READ ITS SPEC + PLAN in `specs/<feature>/` first.
`.specify/memory/constitution.md` holds project principles that bind every spec.
(Everything between the SPECKIT markers below is MACHINE-MANAGED by the agent-context
extension and gets overwritten on every /speckit run; hand-maintained status lives HERE,
above the markers, never inside them.)

**Active feature:** `021-auth-multitenancy` - BUILT T001-T004 (2026-07-14); T005 = the
HUMAN GATE (Kevin creates users via docs/KEVIN_AUTH_GUIDE.md, his team verifies isolation
unassisted). Shipped: auth core frontend/auth.py (scrypt whitelist, disk 30d sessions,
CLI add/remove/list = the whole user management v1; re-add = password reset; removing the
last user deletes users.json so auth deactivates, never a lockout) + asset_paths.users_file
(XCELA_USERS_FILE); the server gate (choke points in both verbs, /login /logout /whoami,
login.html, jf() 401 wrapper, nav user chips); ownership (run_meta owner via pure
run_meta_payload, filtered /runs //brands//brands/detail, per-run 403 guards incl. spends,
brand visible_to/write_allowed, super-only owner assign in update_brand, onboard owner
threading); docs (README, deploy/README enable section, playbook 登录与权限).
test_auth 13/13 (live ephemeral-server pin/gate/isolation proofs; THE PIN: no users file =
open access byte-identical), full 33-suite sweep green.
Kevin's request: login page, whitelist users (scrypt passwords, stdlib),
per-user isolation of brands and runs, super sees all. Binding decisions in the spec: auth
activates ONLY when the users file exists (no file = today's behavior byte-identical, THE
pin; our deployments stay open), disk-backed sessions (cookie, 30d), legacy/unowned
artifacts visible to every logged-in user, owner on new run_meta + brand keys (validate
ignores extras, proven), three list functions filter, per-run routes 403-guard, super can
assign brand owners. Spec/tasks (plan-as-spec, verified line numbers embedded):
`specs/021-auth-multitenancy/`.

Prior feature `019-brand-manager` - BUILT T001-T004 (2026-07-14); T005 = Kevin comms +
his team managing brands unassisted. Trigger: Kevin's team misread our five committed demo
keys as production brands with assets. Shipped: answer keys are RUNTIME STATE
(asset_paths.keys_dir, env XCELA_ANSWER_KEYS_DIR; the five demo keys moved to committed
tests_support/demo_keys/, answer_keys/ gitignored with local working copies; deployed clones
LOSE the demo keys on pull, which is the point; nine runtime-dependent suites pin the env,
test_onboard gets a seeded tmp because it WRITES; proven green with answer_keys EMPTIED);
frontend/brand_manager.py (list/update/replace_logo/delete, all through validate_lean_key,
refusals leave files byte-identical, delete = key only + retype confirm server-side) + routes
(GET /brands/detail, POST /brand/<id>/update|logo|delete via _brand_write: single-flight
lock, traversal-guarded ids) + manage.html (品牌管理, nav on all four pages) + the run form's
per-brand asset status line + the ONE logo format guard (ext + magic-byte sniff,
PNG/JPG/WebP) shared by the wizard and the manager (Kevin's 只能识别JPG report). Fixed en
route: persist.place_logo ignored XCELA_BRANDS_DIR (017 leftover). test_brand_manager 6/6
(hermetic tmp workspaces); full sweep green. Spec/tasks: `specs/019-brand-manager/`
(plan-as-spec). Feature `020-model-env-config` BUILT same day: harness/model_client.py is
the ONE text/vision call home (XCELA_TEXT_MODELS chain + XCELA_IMAGE_MODEL, providers
inferred from the name: claude-* -> Anthropic blocks, else OpenAI chat with data-URI images
+ max_completion_tokens; injectable client factories); five sites rewired (scene_author
author chain with parse-in-loop preserved, blind_score, calibrate _vision_call,
approve tier mapping chain[0]/chain[-1], generate + manifest record image_model()); no bare
anthropic.Anthropic() outside model_client (grep-guarded); defaults byte-identical (pinned).
Kevin's GPT-5.5 fork becomes one .env line. test_model_config 5/5 (fake-client payload
shapes by value; check5 = the yaoyj merge). Spec: `specs/020-model-env-config/`.
Kevin's `yaoyj` branch MERGED 2026-07-14: his base-URL + gpt-5.5 feature, resolved to the
020 architecture (his per-site OpenAI clients superseded by model_client; the surviving
delta is OPENAI_BASE_URL/ANTHROPIC_BASE_URL documented in .env.example + README, honored
natively by both pinned SDKs and proven by value in check5). His whole deployment is now
config: XCELA_TEXT_MODELS=gpt-5.5 + OPENAI_BASE_URL=<relay> + OPENAI_API_KEY.
Ops: `vm` remote RETIRED 2026-07-14 (Kevin's team self-deploys on Alicloud; ship = origin
only, never push vm).

Prior feature `018-github-handoff` - BUILT T001-T004 (2026-07-13); T005 = the push to
origin (needs Alec's GitHub credentials) + the CTO's clone-to-first-run human gate. Richard's
team decision: everything to GitHub, THEIR CTO deploys with THEIR keys. Shipped: ONE env
loader `harness/runtime_env.py` (real env > <repo>/.env > ~/.hermes/.env legacy, never
overriding; the override=True accident is dead, grep-guarded; `require()` for named
missing-key refusals) wired at all six live dotenv sites; `.env.example` documenting every
read variable (gitignore gains !.env.example); deploy/ rewritten for a third-party deployer
(bootstrap accepts either .env home; unit gains EnvironmentFile; our SGP1 box reframed as the
reference deployment); 25 early-research scripts + 7 manual tests swept to `legacy/`
(provenance.py moved BACK when the sweep caught extract_text_layer's live import: the root
extractors were outside the scan; root Python is now exactly the 30 suites + 2 extractors +
provenance.py); an outsider-facing root README.md (purpose, layout, quickstart, env table,
costs). test_deploy_readiness 11/11 incl. the hermetic precedence-by-value check; full
30-suite sweep green. Spec/tasks: `specs/018-github-handoff/`.

Prior feature `017-deployment-readiness` - BUILT (US1-US4) + structurally green
(test_deploy_readiness 10/10; the FULL 30-suite sweep green with the pinned form-greps
updated to the CHINESE values, dated in place, never weakened). The answer-independent
deployment slice (hosting provisioning stays blocked on docs/DEPLOYMENT_QUESTIONS.md):
portable brand-asset paths via `harness/asset_paths.py` (absolute-and-exists >
XCELA_BRANDS_DIR-relative > repo-relative > named refusal; the /mnt/c LOGO_PATH fallback is
GONE; the three committed keys rewritten brands-relative; resolution lazy wrt logo_treatment;
export enumeration soft-nulls via try_resolve; validate_key resolves the same order);
requirements.txt (verbatim 64-dep freeze, Python 3.11 + libgl1 header) + deploy/ (bootstrap
with named out-of-band checks incl. per-key logo resolution, systemd unit LANG=C.UTF-8
TimeoutStopSec=30, Caddyfile TLS+auth placeholders, handoff README); server env knobs
(XCELA_BIND/PORT via pure _bind_config, MAX_UPLOAD_MB=32 as ONE do_POST 413 preamble that
never drains the body, WORKER_TIMEOUT_S=1800 killing wedged workers, freeing the single-flight
lock, and composing with the 016 dead-pid retry); GET /runs (run_view.list_runs, newest-first
by the id's PARSED timestamp) + URL-hash resume (setCurrentRun is the one assignment home) +
the recent-runs picker; Chinese input (keywords INSIDE the existing USAGE_RULES tuple literals
so 014 identity-suppression inherits: 朋友圈/小红书/海报-class -> marketing, 手举牌-class ->
event, never bare 活动; format_size fullwidth/厘米 normalization, identity on ASCII); Chinese
UI chrome (value= attributes preserve every canonical submit value; the ZH dict renders the
gate vocabulary with English fallback, lane-option drift-guarded); the Chinese playbook at
/playbook (real server strings quoted in the message table; feedback placeholder pending
Richard). SC-001 PROVEN live: a fresh /tmp clone bootstrapped, booted on env config, served
/brands /runs /playbook, and its export --plan-only resolved the rewritten relative CJXQ key
against XCELA_BRANDS_DIR from a foreign repo root. PENDING: T012, the ONE human flow gate
(SC-007: one end-to-end run through the Chinese UI, ~$0.08; ideally China-side once
provisioned). Spec/plan/tasks: `specs/017-deployment-readiness/`.

Prior feature `016-layered-export` - BUILT (US1-US3) + structurally green
(test_export_layers 10/10; the FULL 30-suite prior sweep passes, test_confirm_gate's pinned
run_view key set gaining exactly the ONE additive export stage). Richard's ask: at the final
step, split the approved design into per-element layers, zipped. gpt-image-2 CANNOT emit layers
or transparency natively, so layers are BUILT: one paid edit call per deterministically
enumerated element (verbatim message lines from inputs.json, the logo ONLY if it was in the
run's generation.reference_image, product photos; zero elements = loud refusal) repainting ONLY
that element on the proven chroma green #00B140, keyed to a true RGBA PNG by the EXISTING
strip_chroma (closed_loop_composite.py, reused unchanged), plus ONE background call (elements
removed, flagged model_continued); layers.zip = RGBA cutouts + white-bg JPG previews + raw
outputs for honest-null layers (thresholds on the keying stats; never a fabricated cutout) +
the audit manifest (prompts, keying stats, bboxes for drift measurement). Spend follows the 015
contract: the free plan endpoint states N+1 calls + cost BEFORE the click; decide_export writes
an exporting RESERVATION pre-launch which the subprocess worker ADOPTS (started_at + pid);
repeats no-op while a LIVE worker owns the state; retry from failed AND verifiably-stuck
exporting (unadopted reservation / dead pid; SIGINT lands in failed, nothing bricks the export);
409 unless the gate is done; disk-backed (restart-safe); byte-identity tree-hash-proven for
unexported runs and real pre-016 dirs. Post-review hardening (8-angle review 2026-07-08): a
fourth honest-null (majority stray drop), export_error.txt separate from run_error.txt, shared
_export_preflight (plan/spend preconditions identical), no raw exceptions out of export routes,
UI stale-fetch/latch/poller fixes, cost-constant drift guard now real.
New harness/export_layers.py (injectable generate_fn; `--plan-only` free surface, proven live
on run_CJXQ_20260708_151506: 5 elements, 6 calls, $0.48) + decide_export/export_plan_view + 3
routes + additive run_view stage + the opt-in stage-6 button (form-grep pinned never-automatic).
T009 attempt 1 (2026-07-08, $0.48): operator-judged PARTIAL FAIL (text_2 lost a word to the
largest-only keep; the logo layer redrew brand text instead of copying the lockup); v2 fixes
applied 2026-07-09 (strip_chroma keep_all_components, default-off so die-cut stays
byte-identical, export layers opt in; copy-EXACTLY logo isolation desc). EYE-GATE T009
ATTEMPT 2 PASSED 2026-07-10 (same run rerun, $0.48, operator-judged): zero dropped pixels on
every layer, the full "WATERMELON COCONUT" line, the real lockup on the logo layer; the
individual layers ARE the deliverable and read handoff-quality (the stacked recomposition's
logo collision is not a defect: the original has no standalone lockup instance, so its
position is model-invented, and drift is accepted by the draft charter). Feature COMPLETE.
Known follow-on candidates, not scheduled: brand-key enrichment (deferred), the
licensed/composite moat (the real logo fix). Spec/plan/tasks: `specs/016-layered-export/`.

Prior feature `015-pre-spend-confirm-gate` - BUILT (US1-US3) + structurally green
(test_confirm_gate 14/14; the FULL 26-suite prior sweep passes UNCHANGED). The dimension
interview in its evidence-scoped form: every BROWSER run stops at a pre-spend gate.
`POST /run` launches `conductor --phase derive` (calibrate + derive_register + scene_author
`--prompt-only`: register profile, final_prompt.txt, structured `assumptions.json`,
`gate_state.json` awaiting, ZERO image spend); the UI's 3b panel shows the derived plan +
one row per recorded guess (unmatched/blank register lane, magnitude fallback, unrecognized
render/dial, unparseable/clamped size), each with CONSTRAINED controls (picks / bounded
numbers, never free-text retype); `POST /run/<id>/answer` applies only SHIPPED options
(canonical recognized values; the lane pick writes a USAGE_RULES keyword, an explicit human
statement per 014 semantics; ONE additive hard row (("formal document","official
notice"),"formal") makes the formal pick deterministic) then re-derives FREE on the same
run dir (calibration reused, vision calls never repeated); `POST /run/<id>/confirm` is the
ONLY spending route (idempotent: state written before launch, repeat confirms no-op even
mid-generation) and `--phase generate` verifies the confirmed prompt via scene_author
`--verify-prompt` (drift = fail loud + gate reset, never generate from unseen values).
FR-006 proven: all 13 shipped options round-trip (applied == fresh run, row killed).
Byte-identity pinned: `--phase full` default, kit/legacy, derive_register without
`--assumptions-out`, runner argv without phase, pre-015 run dirs in the UI. Assumptions
are emitted STRUCTURED at the guess sites (never regex-parsed from trace). EYE-GATE T017
PASSED 2026-07-08 (operator-judged): the free dry pass live-caught the 173925 defect class
pre-spend on `run_CJXQ_20260708_143643` (the gate row replaced the wrong image); the paid
leg confirmed once, the nudge landed on its own gate (`run_..._145952`), and the image
matches the confirmed framing (clean brand lockup this run). Feature COMPLETE.
Spec/plan/tasks: `specs/015-pre-spend-confirm-gate/`.

Prior feature `014-explicit-usage-wins` - BUILT (US1-US3) + structurally green
(test_explicit_usage_wins 4/4; the seven-suite sweep incl. register_render_aware 8/8 green).
The LAST register leak is closed: the flat-vector-era vibe promotion (playful+informal promotes
marketing->event_prop) no longer overrides an EXPLICIT match on the marketing-keywords row.
`MARKETING_USAGE_KEYWORDS` is a named constant used AS the row in USAGE_RULES (identity-comparable,
cannot drift from the matcher); the match loop records base_row + keyword; ONE elif between the 011
photo gate and the promotion suppresses with a trace line naming the keyword ("a human marketing
statement, not a guess"). Photo gate FIRST: exactly one suppression line in the double-gate case,
011 photo trace byte-unchanged. Wall-posted + playful stays event_prop BYTE-IDENTICAL on both flat
and absent lanes (pinned against the imported 011 literal); the unmatched default still promotes
(a vibe guess on a default guess is legitimate); event rows keep absolute precedence ("instagram
photo" -> event_prop, zero suppressions). Tone retention applies automatically (keys on
register+vibe). Fixes run_CJXQ_20260701_173925 (a flat "promotional social media post" rendered as
a hand-held sign); the exact defect subfields now derive marketing + tone, verified live. Scope:
`register/derive_register.py` ONLY (~14 lines). EYE-GATE T007 PASSED 2026-07-07
(`run_CJXQ_20260707_141245`, the exact 173925 re-brief, operator-judged: a playful flat rectangular
marketing poster, not a sign): feature COMPLETE. The run also demonstrated 013 product fidelity on the
flat lane (real branded cups, printed logos); 013's formal photographic T009 later PASSED 2026-07-08
(see the 013 block). Spec/plan/tasks: `specs/014-explicit-usage-wins/`.

Prior feature `013-role-tagged-references` - BUILT (US1-US3) + structurally green
(test_product_refs 9/9; conductor + render_and_scrub + render_modes + register_render_aware +
frontend_nav + lossless_brief + reference_upload + frontend_runner/stages + thin_route all green).
References now carry ROLES: the STYLE reference keeps its exact semantics (required; calibration
magnitude + dial + exemplar, refs[0]); PRODUCT references (0..MAX_PRODUCT_IMAGES=6, NEW) are
brand-HARD content, per-run campaign assets: uploaded as distinct multipart parts product_1..N
(the parser is last-wins per name), saved via the ONE shared save_upload as product_<i>.<ext>,
threaded as repeatable --product-image at BOTH conductor call sites (stubbed-execute drift guard),
APPENDED to the generation refs after the byte-stable [style, logo] prefix
(scene_author._thin_generation_refs, pure; generate.py untouched, images.edit already takes a
list), and bound by a conditional PRODUCT FIDELITY prompt section (same shapes/printed branding/
label text/colors, no generic redraws, backgrounds discardable). Zero products = prompt AND refs
byte-identical (proven against the pre-013 literal); calibrate/derive argv provably identical with
and without products (calibration isolation); over-cap or missing files fail LOUD (never
truncated); manifests record the product list. The brand-asset seam is deliberate: logo stays
BRAND-level (onboarding places brands/<brand>/, fed every run); products are CAMPAIGN-level
(run-dir uploads); a durable brand-level product library is DEFERRED to brand-key enrichment
(would reuse this feed path, only changing where paths come from; deferral reaffirmed 2026-07-08).
Scope: scene_author thin prompt + refs, conductor threading/validation, server multipart + writer,
form controls; register engine, calibration, kit/legacy, generate.py, multipart.py untouched.
EYE-GATE T009 PASSED 2026-07-08 (`run_CJXQ_20260708_151506`, photographic render + one branded cup
shot, launched through the 015 gate, operator-judged): both product-fidelity lanes are eye-verified
(flat via the 014 T007 run, photographic via this run). Feature fully CLOSED. Spec/plan/tasks:
`specs/013-role-tagged-references/`.

Prior feature `012-lossless-brief` - BUILT (US1-US5) + structurally green
(test_lossless_brief 6/6; conductor + render_and_scrub + render_modes + register_render_aware +
frontend_nav all green). The INPUT GATE stopped leaking: `asset_type` + `occasion` now reach the thin
prompt VERBATIM as a SCENE/SUBJECT context section (never-paintable framing per the slogan lesson;
absent fields = NO section, byte-identical prompt proven against an inlined pre-012 literal; threaded
at BOTH conductor call sites with a stubbed-execute drift guard, the 009 lesson); the form gains a
`design_notes` field feeding the existing `--style-notes` binding channel on the FIRST run (nudges
APPEND via the ";"-join contract; frontend-only, server/runner untouched); the inert audience + warmth
controls are RETIRED (inputs_writer stays tolerant, legacy JSON verbatim, manifest provenance intact);
`reference_relationship` is a 3-option select (extend / match style / mood, 1:1 onto normalize_dial;
free text no longer silently collapses to the default dial); the sign-era message label now states the
verbatim-text contract. Scope: form + writer + conductor thin argv + one scene section in
assemble_thin_prompt; register engine / 009 openers / kit / legacy / server / runner untouched.
EYE-GATE T010 PASSED 2026-07-01 (`run_CJXQ_20260701_164912`, operator-judged: subject fidelity improved,
zero occasion words painted, design note obeyed): feature COMPLETE. Observed gap logged in SYSTEM_MAP,
out of 012 scope: thin-route logo presence is model-probabilistic (nudge today; composite moat / 013
product refs are the real fix). Spec/plan/tasks: `specs/012-lossless-brief/`.

Prior feature `011-register-render-aware` - BUILT (US1-US4) + structurally green
(test_register_render_aware 8/8; conductor 7/7 + render_and_scrub 5/5 + render_modes 5/5 no-regression).
The register engine is RENDER-AWARE on the thin route: `build_subfields(thin=True)` passes the brief's
`render_style` VERBATIM into subfields.json (kit/legacy never see the key, their subfields byte-identical);
`derive_register._render_is_photo` (mirrors `normalize_render_style`, drift-guarded) GATES the
flat-vector-era playful-vibe marketing->event_prop promotion for photographic renders, with the suppression
traced by name (flat/absent/unrecognized byte-identical to the pre-011 baseline, proven against an inlined
literal); explicit event-prop usage still WINS (the gate suppresses the machine guess, never the human
signal); TONE retained per §VI (format follows the task, tone follows the vibe): marketing + promoting vibe
flexes font:rounded + palette:playful-accents (NEVER shape:die-cut), rounded display font role + playful
tone_hint, marketing shape hint verbatim; USAGE_RULES gains a LAST row (marketing/social/instagram/
promotional match explicitly, event keywords keep precedence). Scope: `register/derive_register.py` +
`conductor.build_subfields` ONLY; the 009 opener matrix, scene_author, kit/legacy paths untouched.
EYE-GATE T011 PASSED 2026-07-01 (`run_CJXQ_20260701_154416`, operator-judged: a playful photographic
marketing poster, not a prop, not corporate): feature COMPLETE. The first T011 attempt exposed a latent
009 plan/execution drift (execute() dropped asset_profile on the thin call site, real runs always flat);
fixed in 265a524, guarded by render_modes check 5 (now 5/5), which also satisfies 009's eye-gate T012.
Plus fix(register): explicit logo_treatment=faithful now traces "logo lock HELD" (honest null).
Spec/plan/tasks: `specs/011-register-render-aware/`.

Prior built features: `010-unified-frontend` (BUILT US1-US3, structurally green test_frontend_nav 3/3;
the two `frontend/` pages are ONE app: shared header/nav on both with active-view marker, onboard
save-success -> `/?brand=<id>` handoff + live-runner preselect, UI touch-up with 5 `<fieldset>`s; PURE
frontend, no server change; eye/flow gate T010 closed 2026-07-08, satisfied de facto by the operator
driving both pages through the CJXQ onboarding + the 011/012/014 form-launched runs),
`009-asset-render-modes` (BUILT US1-US3, structurally green render_modes 5/5 +
thin_route 7/7; the task drives render mode + framing on the thin route via `render_style` ->
`normalize_render_style` -> asset_profile + the (asset_profile x register) opener matrix + negatives split;
flat event-sign path byte-unchanged; eye-gate T012 satisfied 2026-07-01 via the 011 T011 run after the
execute-path drift fix 265a524),
`008-palette-role-guidance` (BUILT US1-US2, structurally green: palette_roles 6/6 +
brand_key 10/10 + onboard 10/10; every brand color drives behavior on the thin route via
`scene_author.ROLE_GUIDANCE` + role-aware color block; exactly-one-primary in the shared `validate_lean_key`;
the gate offers 5 roles; eye-gate T011 closed 2026-07-08, satisfied de facto by the role-tagged CJXQ key
driving three operator-passed gates), `001-kit-of-parts-composition` (US3; T020 RAN 2026-06-23,
structurally clean but the eye test was confounded, see the 6/23 regroup; kit path dormant since the
thin-route pivot, a clean kit eye-PASS still owed if revived),
`002-faithful-brief-intake` (faithful intake + wired dropped fields + review), `003-thin-spine`
(the prompt-compose thin route `conductor --thin`, the engine 004 wraps), `004-frontend-live-runner`
(thin local web live-runner; operator run T016 closed 2026-07-08, satisfied de facto: the 011/012/014
eye-gate runs were all launched from this form and judged), `005-brand-intake-front-half` (fully
verified, T015 cold-brand chajiuxingqiu onboarded end to end), `007-reference-upload` (BUILT US1-US3,
structurally green test_reference_upload 6/6; the live-runner takes the reference as a file UPLOAD via the
shared `frontend/uploads.py` `save_upload`, `POST /run` multipart, contract unchanged; plus a follow-on
fix that surfaces conductor failures in the UI via `run_error.txt`; eye-gate T012 closed 2026-07-08,
satisfied de facto: every CJXQ run dir carries the picker-uploaded reference.png, outputs judged),
`006-web-onboarding-gate` (BUILT US1-US3, structurally green: multipart 3 + onboard 9 +
verify_reuse 6; the designer-facing browser wizard wrapping the 005 PURE modules; `frontend/onboard.py` +
`frontend/multipart.py` + `brand_intake/persist.py`; eye-gate T017 closed 2026-07-08, satisfied de facto:
`answer_keys/CJXQ.json` verified_by=web IS the wizard run on the real 茶救星球 PDF, paid outputs on that
key operator-judged in the 011/012/014 gates).

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/017-deployment-readiness/plan.md
<!-- SPECKIT END -->
