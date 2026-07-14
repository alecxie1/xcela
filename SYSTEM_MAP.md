# SYSTEM MAP — Handyprint Brand Design Tool
_Single source of truth for "what is this whole thing." Updated 2026-07-14._

> **▶ BUILD STATUS 2026-07-14 (latest): features 019 (brand manager) + 020 (model-env config) are BUILT; the Kevin comms + their unassisted use are the pending human gates.**
> FEATURE 020 (same day): model choice is deployment CONFIG. harness/model_client.py is the ONE
> text/vision call home: XCELA_TEXT_MODELS (comma chain, default the claude opus->sonnet pair) +
> XCELA_IMAGE_MODEL (default gpt-image-2); the provider is inferred from the model name
> (claude-* -> Anthropic content blocks; anything else -> OpenAI chat.completions with data-URI
> image_url parts + max_completion_tokens); client factories injectable (the suite proves both
> payload shapes BY VALUE with fakes, the chain's warn-then-fallback-then-raise semantics, and
> the pinned defaults). Five sites rewired: scene_author._call_author (parse-failure still
> falls through the chain), blind_score.score_once, calibrate _vision_call (reference_style
> imports it), approve's legacy tiers (chain[0]/chain[-1]), generate.py (call + manifest both
> record image_model()). ZERO bare anthropic.Anthropic() outside model_client (grep-guarded).
> Kevin's GPT-5.5 code fork becomes ONE .env line: XCELA_TEXT_MODELS=gpt-5.5.
> test_model_config 4/4; the FULL 32-suite sweep green. Spec: `specs/020-model-env-config/`.
> Trigger: Kevin's team (deployed at xcela.handyprint.cn, verified byte-identical UI to ours;
> his only real change is the GPT-5.5 model swap) misread our five committed demo keys as
> production brands with complete assets. The structural fix + the feature they asked for:
> ANSWER KEYS ARE RUNTIME STATE (asset_paths.keys_dir, env XCELA_ANSWER_KEYS_DIR; the demo keys
> now live in committed tests_support/demo_keys/ for the suites; answer_keys/ is gitignored, so
> a deployed clone's pull DELETES our demo keys while user-onboarded keys survive untracked;
> the full sweep is proven green with answer_keys/ EMPTIED, the fresh-clone truth, which flushed
> out nine runtime-dependent suites now pinning the env, and test_onboard writes into a seeded
> tmp workspace). THE BRAND DATABASE: frontend/brand_manager.py (HTTP-free: tolerant
> list_brands_detail with honest logo_resolved via try_resolve; update_brand validated on a deep
> copy so refusals leave the file byte-identical; replace_logo staged under the original
> basename; delete_brand = the KEY only, server-side retype confirmation, assets remain and the
> response says so) + GET /brands/detail + POST /brand/<id>/update|logo|delete through
> _brand_write (single-flight lock held for the write, path-traversal ids rejected) +
> manage.html (品牌管理, Chinese, nav on all four pages) + the run form's per-brand asset status
> line (✗ 缺少 logo 素材 = 出图会被明确拒绝) + a playbook section. ONE logo format guard
> (extension + magic-byte sniff; PNG/JPG/WebP, the gpt-image-2 set) shared by the manager AND
> the onboarding wizard (answers Kevin's 只能识别JPG report with a named refusal at upload
> time). Fixed en route: persist.place_logo wrote to the fixed repo brands dir, ignoring
> XCELA_BRANDS_DIR (a 017 leftover the hermetic suite caught). Tests: test_brand_manager 6/6
> (fully hermetic tmp keys+brands workspaces per check); the FULL sweep green BOTH with runtime
> keys present and with answer_keys/ emptied. PENDING T005: the Kevin message (pull to get
> 品牌管理 + the demo keys vanish; the screenshot feature he flagged is OUR 017 run-resume
> picker; 020 will make model names .env vars so his GPT-5.5 swap stops being a fork) and the
> human gate: his team manages brands unassisted. Spec: `specs/019-brand-manager/`.

> **▶ BUILD STATUS 2026-07-13: feature 018 (GitHub handoff) is BUILT T001-T004; T005 (the push + the CTO's clone-to-first-run gate) is PENDING on Alec's GitHub credentials.**
> Richard's team decision: everything to GitHub, THEIR CTO deploys himself with THEIR keys. The
> repo is now configured the standard way: harness/runtime_env.py is the ONE loader (real
> environment variables > <repo>/.env > ~/.hermes/.env legacy, never overriding; the pre-018
> override-flag accident that let a FILE beat the environment is dead and grep-guarded;
> require() gives named missing-key refusals), wired at all six live model-boundary modules;
> .env.example documents every variable the code reads (both keys + the five XCELA_* knobs);
> deploy/ is rewritten for a third-party deployer (bootstrap accepts <repo>/.env OR the legacy
> home file; the unit gains EnvironmentFile; OUR SGP1 box at https://xcela-17ad22.xcela.net is
> reframed as the reference deployment and stays up as staging until theirs works). The repo
> root now reads as the live system: 25 early-research one-offs + 7 manual pre-spec tests moved
> to legacy/ (with the promote-back-with-a-spec rule); provenance.py moved BACK when the sweep
> caught extract_text_layer's live import (the initial scan covered the packages but not the
> root extractors; four suites went red and now prove the boundary); root README.md gives an
> outsider the purpose, layout, quickstart, env table, tests, and costs. Tests:
> test_deploy_readiness 11/11 (hermetic env-precedence BY VALUE, no-override grep, six sites,
> .env.example coverage derived from the code's own environ reads); the FULL 30-suite sweep
> green after the moves. PENDING T005: `git push origin master` with Alec's credentials
> (github.com/alecxie1/xcela, private; invite the CTO in the GitHub UI), then the HUMAN GATE:
> the CTO goes clone -> README -> .env with his keys -> serve -> one gated run without asking
> us anything. Spec/tasks: `specs/018-github-handoff/`.

> **▶ BUILD STATUS 2026-07-12: feature 017 (deployment readiness + Chinese-ready UI) is BUILT + structurally green; its human flow gate T012 is PENDING.**
> The answer-independent deployment slice: everything a fresh Linux VM and a Chinese-speaking
> testing team need that does NOT wait on Richard's answers (docs/DEPLOYMENT_QUESTIONS.md still
> governs provisioning: provider/domain/auth/feedback-channel). PORTABLE ASSETS: the new
> harness/asset_paths.py resolver (absolute-and-exists > XCELA_BRANDS_DIR-relative >
> repo-relative > SystemExit naming every tried path); the /mnt/c LOGO_PATH fallback is DELETED
> (a missing logo now refuses loudly, never silently substitutes); the three committed answer
> keys rewritten brands-relative (proven resolving to the same files); resolution is lazy wrt
> logo_treatment=omit; export enumeration soft-nulls via try_resolve; persist.place_logo writes
> brands-relative so future keys are born portable; validate_key resolves the same order.
> ENVIRONMENT: requirements.txt (verbatim 64-dep freeze; Python 3.11; libgl1 note) + deploy/
> (bootstrap.sh with NAMED out-of-band checks incl. a per-key logo resolution report;
> xcela.service LANG=C.UTF-8 TimeoutStopSec=30; Caddyfile TLS + basic_auth placeholders;
> README with the exact secrets/brands handoff, never committed). GUARDS: XCELA_BIND/PORT (pure
> _bind_config, defaults byte-identical), ONE do_POST 413 preamble (XCELA_MAX_UPLOAD_MB=32,
> body never drained, Connection: close, proven against a real ephemeral server instance),
> XCELA_WORKER_TIMEOUT_S=1800 (a wedged worker is killed, the error admits paid calls may have
> completed, the single-flight lock FREES, and a killed export lands in the 016 dead-pid
> retryable state by construction). REMOTE RESUME: run_view.list_runs (newest-first by the run
> id's PARSED timestamp, never the dir name: lexicographic sorted run_aia above run_CJXQ, caught
> red by the suite) + GET /runs + the recent-runs picker + URL-hash resume (setCurrentRun is the
> ONE currentRun assignment home; a refresh or dropped cross-border connection reopens the run).
> CHINESE INPUT: keywords INSIDE the existing USAGE_RULES tuple LITERALS (the 014
> MARKETING_USAGE_KEYWORDS identity suppression inherits; 朋友圈/小红书/海报-class -> marketing,
> 手举牌/活动现场-class -> event with row precedence, 上墙-class wall, 公告-class formal;
> deliberately never bare 活动); format_size normalizes fullwidth digits/×/厘米/公分/毫米/英寸
> (identity on ASCII, the 3:2 anchor pinned). CHINESE CHROME (frontend-only): every label/
> button/stage/status string simplified Chinese; value-less selects gained value= attributes so
> every canonical submit value is UNCHANGED (form-grep proven); the ZH dict renders the gate's
> closed vocabulary with an honest English fallback (lane options drift-guarded); server strings
> stay English by design, bridged by the playbook's message table. PLAYBOOK: /playbook serves
> frontend/playbook.html (single source; docs/PLAYBOOK.md points at it): the draft charter, the
> costed journey ($0.08 confirm, ~$0.5 export), field guidance, single-flight etiquette quoting
> the real 409, a common-messages table quoting REAL server strings, FAQ, and the
> feedback-channel placeholder. Tests: test_deploy_readiness 10/10 (resolver order by value,
> wiring incl. scene_author's 3 sites + no-fallback grep, deploy artifact pins, run listing
> incl. the cross-brand order trap, resume wiring incl. the one-assignment-home count, Chinese
> lanes + suppression + byte-identity vs the imported 011 literal + fullwidth==ASCII sizes,
> chrome + option-value preservation + ZH drift guard, playbook content by value, guards against
> a REAL server instance); the FULL 30-suite sweep green (four suites' form-grep pins updated to
> the CHINESE values, dated in place: confirm_gate, lossless_brief, product_refs,
> palette_roles). SC-001 PROVEN live: a fresh /tmp clone bootstrapped from deploy/, booted on
> env config, served /brands + /runs + /playbook, and its own export --plan-only resolved the
> rewritten relative CJXQ key via XCELA_BRANDS_DIR from a foreign repo root (5 elements).
> DEPLOYED 2026-07-12: LIVE at https://xcela-17ad22.xcela.net (DigitalOcean SGP1, no login: the
> unguessable hostname is the gate; full record + push-to-deploy procedure in deploy/README.md
> PRODUCTION section; free suites green ON the VM; the push->pull->restart->serve round trip
> proven). PENDING: **T012, the ONE human flow gate (SC-007)**: one end-to-end run through the
> CHINESE UI over the LIVE URL (Chinese brief incl. a 朋友圈-class usage + a fullwidth size,
> gate, confirm ~$0.08, judge, optional export, then a deliberate refresh resuming from the
> URL/picker); ideally driven by the China-side designer as his first real task.
> Spec: `specs/017-deployment-readiness/`.

> **▶ BUILD STATUS 2026-07-10: feature 016 (layered export) is COMPLETE: built, structurally green, eye-gate T009 PASSED (attempt 2).**
> Richard's ask delivered: the run view's stage 6 exports the approved design as PER-ELEMENT LAYERS in
> layers.zip. The load-bearing fact: gpt-image-2 CANNOT emit layered or transparent output (flat
> PNG/JPEG/WebP only; gpt-image-1.5's transparency was removed), so layers are BUILT, not requested:
> one images.edit call per element repaints ONLY that element (identical position/size/colors, exact
> canvas) on the proven chroma green #00B140, and the EXISTING strip_chroma (reused unchanged, one
> out_dir per layer) keys it to a true RGBA cutout; plus ONE background call (elements removed,
> flagged model_continued in the manifest, plausible-not-truth); white-bg JPG previews satisfy the
> literal 多个JPG ask. Elements are enumerated DETERMINISTICALLY from run artifacts (verbatim message
> lines; the logo ONLY if run_manifest generation.reference_image actually fed it; product photos;
> zero elements = loud refusal, never a paid background-only export). HONEST NULLS per layer:
> thresholds on the keying stats (opaque_frac > 0.95 = chroma directive ignored, < 0.001 = empty,
> green residual > 2000 = dirty field) mark a layer null; the zip then ships the RAW model output +
> a named manifest note, never a fabricated cutout; POST-REVIEW HARDENING added a FOURTH null
> (stray-dropped px outnumbering kept px = the largest-component keep erased the majority of a
> multi-glyph element; the keying itself unchanged). The audit manifest carries per layer: prompt,
> 4 keying stats, opaque bbox (position drift is MEASURED, accepted for v1 per the draft charter),
> files. SPEND: the 015 contract applied whole: free GET /run/<id>/export/plan labels the button
> (N+1 calls, exact $) BEFORE any click; POST /run/<id>/export is the only spending route;
> decide_export writes an "exporting" RESERVATION pre-launch (state-before-spend) which the
> subprocess worker ADOPTS via started_at + its pid; repeats no-op while a LIVE worker owns the
> state; retry accepted from failed AND from verifiably-stuck exporting (unadopted reservation,
> dead worker pid; state_blocks_new_export is the ONE arbiter; ANY interruption incl. SIGINT lands
> in failed via BaseException): no crash/kill can brick the run's only export; 409 unless the run's
> confirm gate reached done; a server restart re-renders from disk; the manifest is appended
> progressively so a crash leaves a truthful partial. An 8-angle adversarial code review
> (2026-07-08) drove the hardening: background prompt no longer references a nonexistent second
> image (with_ref_hint split), export failures write export_error.txt (NEVER run_error.txt, which
> poisoned the run view as "Run failed"), the shared _export_preflight makes plan/spend
> preconditions identical by construction (missing source = 404 on both), raw exceptions can no
> longer escape the export routes (named 409s), the UI recovers from a failed cost check (free
> retry click), drops stale cross-run plan fetches (a spend can never be authorized under another
> run's stated price), restarts the poll interval on attempt switches, and the cost constant
> identity is now actually drift-guarded in tests. New: harness/export_layers.py (CLI: --run-dir
> [--plan-only], injectable generate_fn so tests never touch the paid client), server
> decide_export + export_plan_view + _export_preflight + _spawn_worker (shared with 015's
> launcher) + 3 routes, ONE additive run_view export stage (honest null on unexported/pre-016
> dirs; stale-worker detection via pid liveness), the stage-6 opt-in button (starts disabled until
> the free plan labels it; exactly one spending POST; never-automatic form-grep pinned). Tests:
> test_export_layers 10/10 (real strip_chroma on synthetic #00B140 fixtures with probed alpha +
> bbox + the majority-drop null; stubbed orchestrator: N+1 calls, contract refs, progressive
> manifest, exact zip member set; state machine incl. reservation adoption, dead-pid reclaim,
> SIGINT->failed; decide contract triples incl. stuck-reclaim + cost drift guard; full audit
> schema; tree-hash byte-identity incl. real pre-016 run dirs); the FULL 30-suite sweep green
> (test_confirm_gate's pinned run_view key set gains exactly the one additive export stage,
> 14/14). FREE live proof: --plan-only on run_CJXQ_20260708_151506 enumerates
> 3 text lines + logo + product_1 = 6 calls, $0.48. T009 ATTEMPT 1 (2026-07-08, that run, $0.48,
> operator-judged): **PARTIAL FAIL**. Strong: text_1 verbatim + position-faithful, product_1
> near-perfect (1px stray), background continuation clean (mascots kept, no hallucinated text/cups),
> every spend/manifest mechanism exact. Failures: text_2's cutout lost `COCONUT"` (largest-component
> keep dropped 38,541px, 39%, under the null bar, shipped "ok"); the logo layer painted 茶救星球 as
> large text instead of copying the JO'S CHA lockup (the known thin-route logo softness, isolation
> form), ~3x scale. T009-v2 FIXES applied 2026-07-09: (1) strip_chroma gains keep_all_components
> (DEFAULT False = die-cut path byte-identical, render_and_scrub 5/5; export layers pass True: an
> element is legitimately multi-part), the majority-drop null stays armed for the legacy mode;
> (2) the logo isolation desc demands a literal COPY of the asset ("copied EXACTLY ... do NOT
> redraw/restyle/translate/substitute", same position + size as the finished design).
> T009 ATTEMPT 2 PASSED 2026-07-10 (the same run rerun with the v2 fixes, $0.48, attempt-1
> artifacts archived as export_attempt1/ in the run dir): ZERO dropped pixels on every layer
> (text_2 carries the full `"WATERMELON COCONUT"`), the logo layer is the real 茶救星球 / JO'S CHA
> 蔬果茶 lockup, product/texts/background all read as their elements. Operator verdict: the
> INDIVIDUAL layer files are good, the stacked recomposition is not right but that is NOT a
> problem: the logo has no standalone instance in the original (it exists only on cup labels, so
> its painted position is model-invented) and positional drift is accepted by the draft charter;
> the layers ARE the deliverable, a finisher places them. **Feature 016 COMPLETE.** Operator
> note: RESTART frontend/server.py for the new routes. Spec: `specs/016-layered-export/`.

> **▶ BUILD STATUS 2026-07-08: feature 015 (pre-spend confirm gate) is BUILT + structurally green.**
> The dimension interview, scoped to the evidence: the tool now SHOWS ITS GUESSES BEFORE YOU PAY. Every
> browser run stops after deriving its plan (`conductor --phase derive`: calibrate + derive_register +
> scene_author `--prompt-only`, zero image spend) at a gate showing the derived register, anchors/flexes,
> the final prompt, and ONE row per recorded assumption, emitted STRUCTURED at the guess sites (never
> regex-parsed from prose): unmatched/blank register lane, magnitude fallback (derive_register
> `--assumptions-out`, profile bytes untouched, all 011/014 pins hold), unrecognized render/dial,
> unparseable/clamped size (conductor records). Rows carry CONSTRAINED controls only (picks / bounded
> numbers; clarification Q1): an answer applies a SHIPPED option's canonical recognized value (the lane
> pick writes a USAGE_RULES keyword = an explicit human statement per 014; one additive hard row makes
> the formal pick deterministic, pinned inert for all baselines), then re-derives FREE on the same run
> dir (calibration.json reused, the vision calls never repeat in the answer loop). `POST /run/<id>/confirm`
> is the ONLY spending route (idempotent, cost-stated, state-before-launch); `--phase generate` re-runs the
> sign step with `--verify-prompt`: any drift between the confirmed final_prompt.txt and a fresh assembly
> fails loud pre-spend and resets the gate. Nudge reruns land on their OWN gate (clarification Q2:
> "no browser run spends without a confirmed plan", asserted at the launch sites). Zero-guess briefs show
> zero rows + one confirm click (FR-008); walking away leaves an honest unspent draft; a server restart
> re-renders the gate from disk (stateless routes). FR-006 round-trip identity proven for ALL 13 shipped
> options (applied == fresh run, byte-comparable profile + plan, each answer kills its own row). CLI
> byte-identity everywhere: `--phase full` default, kit/legacy untouched, runner argv without phase,
> pre-015 run dirs render as before. Tests: test_confirm_gate 14/14 incl. a REAL free subprocess
> end-to-end (derive stops pre-spend; tampered generate blocked free); the full 26-suite prior sweep
> passes UNCHANGED. EYE-GATE T017 PASSED 2026-07-08 (operator-judged): the FREE dry pass
> (`run_CJXQ_20260708_143643`) LIVE-CAUGHT the 173925 defect class pre-spend (unmatched usage -> vibe
> promotion -> event_prop, visible as a gate row instead of a wrong image; the marketing pick re-derived
> free with the 014 suppression trace, calibration reused, answers survived a server restart, the draft
> abandoned honestly unspent); the PAID leg (`run_CJXQ_20260708_144718` zero-row confirm, then the nudge
> landing on its OWN gate as `run_CJXQ_20260708_145952`) produced an image matching the confirmed framing:
> flat rectangular 60x40 marketing poster, three verbatim message lines, real branded cups with printed
> JO'S CHA labels, mascots + tree + cabin per the binding note, and a CLEAN brand lockup (the 014
> stray-character softness did not recur). Feature COMPLETE. Minor taste note: a doubled opening quote
> before "WATERMELON COCONUT" (the brief's own curly quotes; a canvas touch-up, not a tool defect).
> Spec: `specs/015-pre-spend-confirm-gate/`.

> **▶ HOUSEKEEPING 2026-07-08 (post-014 sweep):** `answer_keys/CJXQ.json` is now COMMITTED: it is the
> PRODUCTION key for 茶救星球 / JO'S CHA (web-onboarded via the 006 wizard, verified 2026-06-30, the key
> behind every recent eye-gate run); `answer_keys/chajiuxingqiu.json` stays as the 005 T015 verify-test
> artifact for the same brand, historical, not production. Five older eye-gates are CLOSED as satisfied
> de facto, evidence cited in each feature's tasks.md: 004 T016 + 007 T012 (the 011/012/014 paid runs were
> all launched from the live-runner form; run dirs carry the form-written inputs.json + picker-uploaded
> reference.png), 006 T017 (CJXQ.json verified_by=web IS the wizard end to end on the real VI PDF), 008
> T011 (the role-tagged key drove three operator-passed gates), 010 T010 (both pages driven as one app
> through real work). 001 T020 is closed as RAN-BUT-NOT-PASSED: the kit run happened 2026-06-23
> (`run_aia_20260623_110905`, structurally clean; the eye comparison was CONFOUNDED, see the 6/23 regroup)
> and the effort pivoted to the intake fix + the thin route; the kit path is DORMANT, a clean kit eye-PASS
> is still owed IF that path is revived. 013 T009 CLOSED 2026-07-08: PASSED on
> `run_CJXQ_20260708_151506` (photographic render, one branded cup shot as product_1.jpg, launched
> through the 015 gate; operator-judged). Both product-fidelity lanes are now eye-verified; 013 is
> fully closed. BRAND-KEY ENRICHMENT (the durable brand-level product library, formerly "015" on the
> roadmap before that number went to the confirm gate) is DEFERRED by operator decision 2026-07-08:
> it changes zero pixels (it reuses the 013 feed path verbatim, only where paths come from), its whole
> value is skipping re-upload of evergreen shots, and observed usage so far is campaign-specific
> products ("this launch's watermelon cups are not next month's mooncakes", the 013 plan's own seam
> note). Revisit when re-upload friction is actually felt. 016-layered-export shipped and closed
> (see the latest build-status block). NEXT NAMED FEATURE: **017-deployment-readiness**
> (2026-07-10): deploy the tool for Richard's team in mainland China + a Chinese playbook. BLOCKED
> on Richard's answers to `docs/DEPLOYMENT_QUESTIONS.md` (18 bilingual questions, forwarded
> 2026-07-10: team size/roles, taste-gate ownership, volume/budget, office network reach to
> foreign-hosted sites, brand assets + VI PDFs, cloud account ownership, login style, feedback
> channel, timeline). PROVISIONAL PLAN pending those answers (portability audit done): a small
> Ubuntu VM in Singapore or Tokyo (OpenAI/Anthropic are blocked from the mainland AND unsupported
> in Hong Kong, so egress must come from a supported region the team can reach); Caddy reverse
> proxy with auto-TLS + basic auth in front (today the server binds 127.0.0.1 with ZERO auth and
> every visitor could spend); 017 code scope: portable answer-key logo_path (the committed keys
> carry absolute /home/alecx paths into the gitignored brands/), kill the /mnt/c LOGO_PATH
> fallback (scene_author.py:125), pinned requirements.txt (none exists; deps live only in the
> local .venv; opencv needs headless/libgl1), bind/port via env (default byte-identical), upload
> size cap + worker wall-clock timeout, GET /runs + URL-hash resume (the UI currently loses the
> run view on refresh: session-only attempts[]), deploy/ (systemd unit + Caddyfile + bootstrap
> script; secrets and brands/ provisioned out-of-band, never committed); Chinese-primary playbook
> served at /playbook. Deployment eye/flow gate: one end-to-end run driven by a team member in
> China before calling it done.
> Known taste backlog: thin-route logo LOCKUP softness (stray character in the 014 run; nudge today, the
> licensed/composite moat is the real fix).

> **▶ BUILD STATUS 2026-07-04: feature 014 (explicit usage wins over the vibe guess) is BUILT + structurally green.**
> The register engine's LAST known leak between stated intent and register is closed. Observed on
> `run_CJXQ_20260701_173925`: a flat-vector "promotional social media post" from the playful CJXQ brand
> matched the explicit marketing keyword 'social' (the 011 US4 row), then the flat-vector-era vibe
> promotion (formality<=3 + playfulness>=7 promotes marketing->event_prop) OVERRODE that explicit human
> match and the post rendered as a hand-held die-cut sign. 011's gate was render-keyed only (photo lane);
> on the flat lane a machine guess still beat a human statement (constitution I violation, the same class
> 011 killed). New, in `register/derive_register.py` ONLY (~14 lines): the marketing row is hoisted to the
> named `MARKETING_USAGE_KEYWORDS` constant used AS the row in USAGE_RULES (identity comparison, cannot
> drift from the matcher); the match loop records which row + keyword produced the base; ONE elif between
> the 011 photo gate and the promotion suppresses when the base came from that row, tracing "usage_context
> explicitly matched 'social' (a human marketing statement, not a guess) => promotion SUPPRESSED". Photo
> gate stays FIRST: exactly one suppression line when both gates apply (FR-006), the 011 photo trace
> byte-unchanged. BLAST RADIUS PINNED: wall-posted + playful stays event_prop BYTE-IDENTICAL on both the
> flat and absent lanes (asserted against the imported 011 baseline literal, so over-suppression cannot
> ship); the unmatched default still promotes (a vibe guess on top of a default guess is legitimate);
> event rows keep absolute precedence ("instagram photo" -> event_prop via 'photo', zero suppressions,
> both lanes). Tone retention (011) applies to the newly suppressed cases automatically (keys on
> register+vibe): the result is a playful flat MARKETING poster, not a corporate one, not a prop. VERIFIED
> LIVE free: the exact 173925 subfields.json now derives marketing + the keyword suppression + tone flexes,
> no die-cut. Tests: test_explicit_usage_wins 4/4 (all four keywords x three non-photo renders; double
> gate single-entry; byte-identity both lanes; default promotion; precedence both lanes; 011 photo lane
> pinned); seven-suite sweep green (register_render_aware 8/8 survives, its check7 never asserted the
> final register). EYE-GATE PASSED (SC-005, T007, 2026-07-07): the operator judged
> `run_CJXQ_20260707_141245`, the exact 173925 re-brief (flat vector, "promotional social media post",
> vibe 2/8): register=marketing via ONE 'social' suppression line, no die-cut flex, the flat+marketing
> rectangular opener, and the image reads as a playful flat rectangular marketing poster (bubbly type,
> candy palette, mascots on flat scenery), NOT a hand-held sign. Feature COMPLETE. BONUS: the run carried
> one product shot and the output composes the REAL branded JO'S CHA cups (printed 茶救星球 logos visible,
> photoreal cups over flat-vector scenery), demonstrating 013's product fidelity on the flat lane; 013's
> formal T009 (photographic rerun judged against run_..._164912) remains open at the operator's option.
> Minor taste note for the finishing human: the top logo lockup rendered with a stray character
> ("JO'S CHA蔬"), the known thin-route logo-paint softness, a nudge or composite-moat item, not a gate
> failure. Spec/plan/tasks: `specs/014-explicit-usage-wins/`.

> **▶ BUILD STATUS 2026-07-01 (latest): feature 013 (role-tagged references: style + product) is BUILT + structurally green.**
> The single do-everything reference is SPLIT INTO ROLES. Motivation: the 012 eye-gate run
> (`run_CJXQ_20260701_164912`) lost the printed cup logos because product fidelity was a requested favor
> (a prompt line + the logo file) rather than a supplied fact; a realism note made the model regenerate
> generic photoreal cups instead of carrying the reference's branded ones. New: the STYLE reference keeps
> today's exact semantics (required; calibration magnitude + relationship dial + visual exemplar; refs[0]);
> PRODUCT references (0..6, `conductor.MAX_PRODUCT_IMAGES`, mirrored in server.py with a drift-guard test)
> are per-run photos of the REAL products: uploaded on the form as an optional multi-file control whose
> files ride as DISTINCT multipart parts product_1..N (frontend/multipart.py is last-wins per part name,
> so same-named parts would silently drop files, the loss class 012 killed), saved through the ONE shared
> `uploads.save_upload` home as product_<i>.<ext> in the run dir, passed VERBATIM through
> `inputs_writer` -> `inputs.product_images` -> repeatable `--product-image` at BOTH conductor call sites
> (build_plan AND execute, asserted with the stubbed-run_step pattern), APPENDED to the generation input
> list after the byte-stable [style, logo] prefix (the new pure `scene_author._thin_generation_refs`;
> `harness/generate.py` untouched, images.edit already accepts a list, 8 total inputs max vs the API's 16),
> and bound by a conditional PRODUCT FIDELITY prompt section (the N supplied images are the brand's REAL
> products: same shapes, printed branding, label text, colors; no generic redraws; only backgrounds
> discardable). HONEST NULLS + ISOLATION: zero products = prompt AND refs list byte-identical to pre-013
> (proven against inlined literals); over-cap or missing files fail LOUD at both gates (form error +
> validate_inputs named error), never truncated; calibrate/derive argv provably IDENTICAL with and without
> products (product truth never reaches magnitude/register, so 011 is untouched); both manifests record the
> product list. THE BRAND-ASSET SEAM (per the operator's direction): the logo stays a BRAND-level asset
> (onboarding's persist.place_logo -> brands/<brand>/, fed on every run); product shots are CAMPAIGN-level
> (per-run uploads); both meet only in the generation refs list. A durable brand-level PRODUCT LIBRARY
> (evergreen hero shots chosen at onboarding) is DEFERRED to 015 brand-key enrichment and would reuse this
> exact feed path. Tests: test_product_refs 9/9 (fidelity section + byte-identity, refs prefix equality,
> argparse append, BOTH-call-sites threading, cap + missing fail-loud, calibration isolation, legacy shape,
> multipart 0/2/7 + shared-home saves + cap drift guard, form greps); all prior suites green incl.
> reference_upload 6/6 updated to the extended parse_run_form 3-tuple; NO paid calls. PENDING +
> LOAD-BEARING: SC-006, the human eye-gate (T009): ONE paid rerun of the CJXQ watermelon brief WITH the
> branded cup shots as product refs, judged against run_..._164912: the actual 茶救星球 JO'S CHA cups
> (printed logos visible) instead of generic look-alikes, 012's style/scene quality retained.
> Spec/plan/tasks: `specs/013-role-tagged-references/`.

> **▶ BUILD STATUS 2026-07-01 (later): feature 012 (lossless brief / field honesty) is BUILT + structurally green.**
> The INPUT GATE stopped leaking. A field audit of the CJXQ watermelon run found the form collecting
> intent that never reached generation: `asset_type` + `occasion` stopped in glue artifacts only the
> unused kit/legacy route reads; audience / warmth / hero_icon were collected and inert; free text in
> `reference_relationship` was keyword-bucketed and the nuance DISCARDED (a real user's "grab the
> product hero shots..." survived only as the default dial); and the strongest free-text lever (the
> binding `--style-notes` block) was unreachable at brief time. New: (1) `assemble_thin_prompt` gains a
> SCENE/SUBJECT context section carrying asset_type + occasion VERBATIM, framed never-paintable (the
> slogan lesson), rendered ONLY when non-empty (both-blank = byte-identical prompt, proven against an
> inlined pre-012 literal); threaded via `--asset-type`/`--occasion` at BOTH conductor call sites
> (build_plan AND execute), with the execute argv asserted via the stubbed-run_step pattern (the 009
> drift lesson applied preemptively). (2) a `design_notes` textarea on the first-run form feeds the
> existing binding channel; a nudge APPENDS via the channel's ";"-join contract (frontend-only;
> server/runner/conductor untouched). (3) audience + warmth controls RETIRED from the form;
> `inputs_writer` stays tolerant so legacy JSON passes verbatim (manifest provenance intact).
> (4) `reference_relationship` is a 3-option select (extend / match style / mood) mapping 1:1 onto
> `normalize_dial`; the engine keeps its lenient parser for legacy inputs. (5) the sign-era "Sign
> message line(s)" label now states the verbatim-text contract (asset-generic). Scope: `index.html` +
> `inputs_writer.py` + conductor thin argv + one scene section in scene_author; register engine (011),
> 009 openers, kit/legacy, server/runner byte-untouched. Tests: test_lossless_brief 6/6 (scene values +
> blank byte-identity, BOTH-call-sites threading, notes channel, retired controls + back-compat, dial
> mapping, label contract; form checks are greps, the weakest gate, declared per the 010 precedent);
> all 5 prior suites green; NO paid calls. EYE-GATE PASSED (SC-007, T010, 2026-07-01): the operator
> judged `run_CJXQ_20260701_164912` (re-brief of the watermelon post, scene section + design note live)
> against `run_..._154416`: subject fidelity clearly improved (true photographic hero shots, tropical
> scene) AND zero occasion/scene words painted (the never-paintable framing held on real Chinese
> marketing copy) AND the design note obeyed. Feature COMPLETE. OBSERVED GAP (out of 012 scope,
> logged for the backlog): the brand logo did not appear on the cups this run; the logo file WAS fed and
> the LOGO prompt line present (pipeline correct, trace shows logo lock HELD), but the thin route's raw
> gpt output makes logo presence model-probabilistic, especially when a realism note makes the model
> regenerate products instead of carrying the reference's branded cups. Today's countermeasure: an
> approve-gate nudge naming the placement. The real fix is the known deferred licensed/composite moat
> (or 013 role-tagged product references). Spec/plan/tasks: `specs/012-lossless-brief/`.

> **▶ BUILD STATUS 2026-07-01: feature 011 (render-aware register) is BUILT + structurally green.**
> The register inference no longer mis-frames photographic marketing jobs from playful brands as hand-held
> event props. The old heuristic was flat-vector-era: "playful+informal vibe" promoted any `marketing` job to
> `event_prop` regardless of what was being made (observed live: a watermelon-product Instagram post framed
> as a photo-prop). New, on the THIN route only: `conductor.build_subfields(inputs, thin=)` passes the
> brief's `render_style` VERBATIM into `subfields.json` (kit/legacy routes never receive the key, their
> subfields stay byte-identical); `derive_register._render_is_photo` (mirrors `normalize_render_style`
> across the subprocess boundary, drift-guarded by a both-modules agreement test) GATES the playful-vibe
> marketing->event_prop promotion when the render is photographic, appending ONE trace line that names the
> raw render_style; flat / absent / unrecognized values take the historical path with a byte-identical
> profile (proven against an inlined pre-011 baseline literal). An EXPLICIT event-prop usage phrase ("held
> for photos") still wins over the gate: the usage-rule table runs upstream, so the human signal is never
> suppressed, only the machine guess is (§I). The two-axis split (§VI): FORMAT follows the task (no
> shape:die-cut flex, marketing shape_language_hint verbatim, chroma containment stays off), TONE follows
> the brand vibe (marketing + formality<=3/playfulness>=7 flexes font:rounded + palette:playful-accents,
> resolves the rounded display font role, playful tone_hint), so a playful brand's marketing post stays
> playful WITHOUT becoming a prop or collapsing corporate. Also: USAGE_RULES gains a LAST row
> (marketing / social / instagram / promotional match explicitly; "instagram photo" still lands on the
> event row via 'photo', precedence-guarded). Scope: `register/derive_register.py` +
> `conductor.build_subfields` ONLY; the 009 opener matrix, scene_author, kit/legacy paths byte-untouched.
> Tests: test_register_render_aware 7/7 (plumbing, drift guard, gate, tone retention, US2 byte-identity,
> US3 human-wins, US4 keywords); conductor 7/7 + render_and_scrub 5/5 + render_modes 4/4 no-regression;
> NO paid calls. EYE-GATE PASSED (SC-007, T011, 2026-07-01): the operator judged
> `output/run_CJXQ_20260701_154416` (CJXQ photographic watermelon marketing post): a real photographed
> scene, rectangular poster, playful tone intact (bubbly type, candy palette, mascots), logo faithful,
> headline verbatim; not a prop, not corporate. Feature COMPLETE. The FIRST T011 attempt (run_..._152554)
> rendered FLAT and EXPOSED a latent 009 plan/execution drift: `execute()` omitted asset_profile at the
> thin scene_author call site, so REAL runs always fell back to flat_graphic while dry-run plans showed
> photo (the 009 tests only asserted build_plan). Fixed same day (fix(009) 265a524): execute resolves
> normalize_render_style and passes it; render_modes check 5 now drives execute() itself with run_step
> stubbed and is the permanent drift guard (verified RED pre-fix). Also fix(register) a8e0934: an explicit
> logo_treatment that is not omit/subtle (e.g. faithful) now traces "logo lock HELD" (honest null);
> absent stays silent (byte-identity preserved). The passing run also satisfies 009's pending eye-gate
> T012 (the output demonstrably LOOKS photographic). Spec/plan/tasks: `specs/011-register-render-aware/`.

> **▶ BUILD STATUS — 2026-06-30: feature 010 (connect onboard + live-runner into one app + UI touch-up) is BUILT + structurally green.**
> The two `frontend/` pages (`/` live-runner + `/onboard` wizard) now read and navigate as ONE app. (A) a
> shared header/nav on BOTH pages cross-links "Generate a sign" (`/`) and "Onboard a brand" (`/onboard`),
> the current view marked active (`aria-current`); before, only onboard linked back and the live-runner had
> a bare header. (C) a post-onboard HANDOFF: the onboard save-success renders a "Generate a sign for this
> brand" link to `/?brand=<id>` (via `innerHTML`), and the live-runner's `loadBrands()` reads `?brand=` and
> preselects that brand after `/brands` loads (graceful fallback to the default if the param is absent or the
> brand is not in the list). Plus a UI touch-up: a shared nav style, focus rings, softer cards, and the
> live-runner's long flat form grouped into 5 `<fieldset>`s (brand+asset / reference / voice+vibe / context /
> elements+message). PURE frontend (only `index.html` + `onboard.html` edited); NO new server route, NO
> back-half change - the nav snippet is duplicated per page (no static-asset route), drift-guarded by a
> both-pages-carry-both-links test. HONESTY (§II/§III): the value is a HUMAN-EYE judgment (one app, clean,
> smooth flow); the automated tests (`test_frontend_nav` 3/3) are PRESENCE GREPS (both nav links + active
> markers, the `/?brand=` handoff, the preselect wiring, no em-dash) + a no-regression run - the weakest
> gate, so the eye is the real proof. But unlike 009, THIS eye-gate is FREE (nav + flow + look, no
> generation). Tests: frontend_nav 3/3; all prior 001-009 frontend/thin suites green; NO paid calls.
> PENDING: T010, the free human eye/flow check (nav both ways; onboard -> preselected generate;
> `/?brand=unknown` fallback; one consistent polished look). Spec/plan/tasks: `specs/010-unified-frontend/`.
> DEFERRED: a full single-page merge (in-page tab switching).

> **▶ BUILD STATUS — 2026-06-30: feature 009 (beyond flat-vector event signs / render modes) is BUILT + structurally green.**
> The tool no longer renders ONLY flat-vector die-cut event signs. On the thin route the designer now picks a
> RENDER STYLE (flat vector / photographic) and the TASK drives the render dialect + framing, so a photographic
> poster and a flat rectangular flyer are possible, not just a die-cut sign. Before, the conductor hard-wired
> `ASSET_PROFILE="flat_graphic"` and the opener hard-coded "hand-held event sign" in both flat branches. New: a
> `render_style` control in `index.html` carried verbatim by `inputs_writer`; `conductor.normalize_render_style`
> maps the user term to the engine `asset_profile` (photographic->photo, else->flat_graphic, honest-null
> fallback) and threads it into `_scene_author_thin_argv` (the manifest records render_style + the resolved
> profile); `assemble_thin_prompt` is (asset_profile x register)-aware - flat+event_prop UNCHANGED
> (byte-identical regression), flat+marketing rewritten to a rectangular poster (drops "hand-held event sign"),
> and two NEW photographic openers (event prop / marketing poster); the negatives are split so the
> render-agnostic text guards (no extra Chinese / no gibberish / no tagline / no watermark) apply in BOTH modes
> while the flat-only render negatives (no photographic shading / 3D) stay flat-only (the flat line is
> byte-identical). Brand still governs color/font/logo HARD; the task governs render style + shape SOFT (§VI).
> Photographic is allowed for ANY register; shape is derived from the register, not a second control. Scope:
> the THIN route ONLY (kit / tier-3 / no-reference-cutout / legacy render-and-scrub / measure-composite
> UNCHANGED; deliverable final.png, chroma auto-off for non-flat). Tests: render_modes 5/5 + thin_route 7/7;
> all prior 001-008 suites green; NO paid calls. EYE-GATE (T012) SATISFIED 2026-07-01 via the 011 T011 run
> (`run_CJXQ_20260701_154416`): the generated poster demonstrably LOOKS photographic (§II). That same gate
> first CAUGHT a latent 009 defect: `execute()` omitted asset_profile at the thin call site, so real runs
> always rendered flat while dry-run plans showed photo; fixed in 265a524, permanently guarded by
> render_modes check 5 (drives execute() with run_step stubbed). Spec/plan/tasks: `specs/009-asset-render-modes/`.
> DEFERRED (a separate later feature): generalizing the kit / no-reference / cutout paths, and asset_type-driven
> opener specificity.

> **▶ BUILD STATUS — 2026-06-30: feature 008 (role-aware brand palette + exactly-one-primary) is BUILT + structurally green.**
> Every brand color now drives real design behavior on the thin route, not just the primary. Before, the
> thin prompt listed all colors with a bare `[role]` label and only the primary was reinforced, so a
> designer's accent / background / text assignments were silently discarded. New: `scene_author.ROLE_GUIDANCE`
> (a module constant) maps each role to a CONFIRMED instruction (primary = dominant anchor, secondary =
> supporting, accent = sparing highlights, background = backdrop, text = legible type), and a blank / unknown
> role falls back to a generic palette line (honest-null, never dropped). `assemble_thin_prompt`'s color
> block emits `name: #hex [role] - <instruction>` (available palette with role GUIDANCE; brand identity stays
> the HARD lock, the header keeps "must read as this brand's"). `background` is guarded by `has_reference`:
> on a chroma / no-reference job the backdrop instruction is suppressed (color still listed) so it never
> fights the #00B140 chroma key; today's reference-only live path is unaffected. Onboarding now enforces
> EXACTLY ONE primary in the shared `validate_lean_key` (>=1 -> ==1; raises a named error on zero AND on
> two-or-more; CLI + web inherit), and the verify gate (web `onboard.html` + CLI `intake.py`) offers all 5
> roles (added accent + text), kept in sync with the map by a structural test. `_primary_color_hex` (the
> anchor) is untouched. Tests: palette_roles 6/6, brand_key 10/10 + onboard 10/10 (new multiple-primary
> fail-loud), all prior 001-007 suites green; NO paid calls. Scope: thin prompt + validator + gate pickers
> ONLY (kit / tier-3 / legacy color paths, typography, the asset profile, the conductor contract UNCHANGED).
> PENDING: the human eye-gate (a sign whose palette uses accent / text / background, judged by eye that the
> full palette is used per role, T011, folds into the back-half paid run). Spec/plan/tasks:
> `specs/008-palette-role-guidance/`. The generalize-beyond-flat-vector-signs item (photographic posters) is
> a SEPARATE deferred feature.

> **▶ BUILD STATUS — 2026-06-29: feature 007 (reference-image upload in the live-runner) is BUILT + structurally green.**
> The 004 live-runner now takes the reference image as a real file UPLOAD (a file picker) instead of a
> typed absolute server path. This kills the absolute-path footgun (a typo silently became a
> file-not-found at the paid step) and makes the live-runner consistent with the 006 onboarding upload,
> in the SAME `frontend/` local app. New `frontend/uploads.py` (`save_upload(file_tuple, dest_dir,
> name)`) is the ONE save-upload home, called by BOTH the new `/run` reference-save AND the refactored
> 006 logo-save (DRY; the inline `_onboard_save` write now goes through it). `POST /run` is now multipart
> (a `form` JSON field + a `reference` file) parsed by two HTTP-free helpers in `server.py`:
> `parse_run_form` fails loud (4xx, nothing launched) on a missing reference BEFORE any run dir /
> single-flight; `write_run_inputs` saves the upload INTO the run dir preserving its extension (e.g.
> `output/run_*/reference.jpg`) and injects that path as `reference_image`. The conductor / CLI input
> contract is UNCHANGED (`reference_image` is still a path on disk); `inputs_writer.py` + `multipart.py`
> are reused unchanged; the frontend adapts (the standing rule). The 002 verbatim invariant holds for the
> other fields. Tests: reference_upload 6/6 (save_upload roundtrip+traversal-sanitize, /run-assembly
> points at the saved file with the extension preserved, file-input grep, fail-loud on a missing
> reference, the 002 verbatim invariant, the standalone thin-route contract intact); all prior 001-006
> suites green; NO paid calls. PENDING: the human browser smoke (pick a real reference in the UI) + the
> one paid sign, folded into 004's pending paid eye-gate (T012 / 004 T016). Spec/plan/tasks:
> `specs/007-reference-upload/`.

> **▶ BUILD STATUS — 2026-06-28: feature 006 (designer-facing web onboarding gate) is BUILT + structurally green.**
> A designer can now onboard a cold brand entirely in the browser (no terminal): a 3-step wizard in
> the existing `frontend/` local app — upload the brand PDF -> confirm the suggested 1-indexed spec
> pages -> extract + verify the locks (assign color roles, confirm names, acknowledge each
> needs_review, upload the logo) -> validate-loud + save a lean `answer_keys/<brand>.json`. It WRAPS
> the proven 005 `brand_intake/` PURE modules in the 004 local-web pattern; it never reimplements
> extraction/validation/gate logic and never calls the stdin-bound `intake.main()`. New: `frontend/
> onboard.py` (wizard over a TRANSIENT draft dir, discarded on save/abandon), `frontend/multipart.py`
> (stdlib upload parsing, no `cgi`, no new dep), `brand_intake/persist.py` (the ONE write home the CLI
> and the web gate share). Fail-loud (4xx, no write) on a missing primary color / logo / unacknowledged
> flag / existing brand id; a zero-color page set BLOCKS + returns to page-confirm; `typography.styles`
> honest-null. The saved brand appears in the 004 live-runner dropdown automatically (`/brands` lists
> `answer_keys/*.json`) -> onboard then generate, one local app (verified end-to-end over HTTP). Tests:
> multipart 3/3, onboard 9/9, verify_reuse 6/6; all prior 001-005 suites green; NO paid calls.
> PENDING: the human browser smoke (upload a real cold-brand PDF in the UI) + the one paid sign through
> the back-half (T017). Spec/plan/tasks: `specs/006-web-onboarding-gate/`.

> **▶ BUILD STATUS — 2026-06-26: feature 005 (brand-intake front-half) is BUILT + structurally green.**
> The brand-onboarding FRONT-half now exists: a PDF to a human-VERIFIED lean `answer_keys/<brand>.json`
> the existing thin route consumes UNCHANGED. New `brand_intake/` package (page_finder + extract
> wrappers + assemble_key + validate_key, all PURE, + the `intake.py` CLI verify gate) REUSES the
> proven deterministic extractors (`extract_colors` / `extract_text_layer`), NOT the dead v3 scaffold.
> Page-finding suggests 1-indexed spec pages (real hex-token page, not a color-mention page); the human
> confirms. Validation FAILS LOUD on a missing primary color / logo_path (contains the silent-taichi-
> logo landmine `scene_author` falls back to). Verify gate is acknowledgment-gated (confirm/edit/
> keep-flagged); `typography.styles` honest-null in v1. A `derive_register` probe corrected SC-005 to a
> TWO-PART invariant: lean-with-styles == fat byte-identical (the dropped graded/legacy fields are
> zero-effect); the real styles-absent new-brand key differs ONLY in the font-directive line (the
> FR-010 honest-null). Tests: verify_reuse 6/6, page_finder 5/5, brand_key 9/9; all prior suites
> (001-004) green; `--no-gate` ran end-to-end on a synthetic PDF, no paid call. PENDING: the human
> cold-brand OCR smoke (e.g. chajiuxingqiu) + the one paid sign through the back-half (T015).
> Spec/plan/tasks: `specs/005-brand-intake-front-half/`.

> **▶ BUILD STATUS — 2026-06-24: feature 004 (frontend live-runner) is BUILT + structurally green.**
> A THIN local web frontend over the agent-free CLI (`frontend/`): the operator types ONE single-sign
> brief, presses Run (paid, cost-labeled), and watches the THIN route's stages appear progressively
> from the run dir (brief, register/dial, assembled prompt, generated sign), then approves or
> nudge-reruns (each nudge = a new run dir, prior attempts comparable). The UI shells out to
> `conductor.py --thin --no-approve [--style-notes]` and reads artifacts; it never reimplements
> generation. The ONE engine change was a top-level `conductor --style-notes` pass-through. Tests:
> test_frontend_intake 4/4, test_frontend_stages 5/5, test_frontend_runner 3/3, test_conductor 7/7;
> all prior suites (001/002/003) stay green. Pending: the operator's PAID single-sign run + eye
> verdict (~$0.08). Spec/plan/tasks: `specs/004-frontend-live-runner/`. The keep/cut decision below
> still stands (thin route is the engine; the kit composition layer is parked).

> **▶ REGROUP — 2026-06-24 PM (the project-defining keep/cut decision):**
> The faithful 6-sign paid run (`output/run_aia_20260624_104106/`) gave the FIRST un-confounded
> verdict by Alec's eye, and it is decisive: on Lily's real brief the kit COMPOSITION layer produced
> 2 good signs, 3 near-duplicates (s3/s5/s6 all `resist_panel`+`megaphone_x`), and 1 blank honest-null
> (s4, no icon match). Alec's standalone gpt-image-2 on the same brief produced 6 varied on-brief signs
> in ONE shot. Conclusion (the bitter lesson, on our own task): the deterministic composition layer
> COMPETES with the model and LOSES — it constrains gpt down to its own threadbare vocabulary. It is
> not neutral; it makes output WORSE on the real distribution of briefs.
>
> **THE DECISION (keep what complements the model; cut what competes with it):**
>   • CUT (delete as the default path): `compose_select` (meaning→icon), the kit layout-archetype
>     vocabulary, reserve-box icon_zone/text_zone, the fit-to-zone clamp. These are the layer that lost.
>   • KEEP (active): faithful intake (002), the register/DIAL (Alec: the task sits at the
>     task-governs-hard end of the dial — expressive departure — which is a per-job dial READING, not
>     proof the dial is useless; a corporate asset would read the other way, so the dial stays),
>     answer_key brand locks (hex/font/logo), `analyze_brand_v3` VLM extraction (Alec has confidence in
>     it; human verifies the answer_key), logo fed to gpt, the human approve/nudge gate, the manifest.
>   • DEFER (built, switched OFF this interim — NOT deleted): the licensed-font MOAT
>     (`build_font_index`, `resolve_font`, `composite_text`, compliance). Node-5 font-swap dropped for
>     now to de-risk; returns as its own spec. Research verdict for that future spec: gpt-image (soft
>     mask, per OpenAI docs) CANNOT pixel-lock a zone or render licensed type, so the legacy
>     measure→scrub→redraw (a) and reserve-band (b) are both dead ends; the real moat is FURNITURE +
>     DETERMINISTIC TYPESET (gpt paints text-free furniture; we own 100% of type via SVG/CSS
>     stroke+shadow+skew, rasterize, composite). Separability check on `desiredresultaia.jpg`: 5/6 signs
>     are flat-band (easy to typeset), 1 is integrated (hard → honest-null). Favorable, but UNPROVEN —
>     it needs a SPIKE (does gpt leave clean empty furniture? does typeset look native?) before any spec.
>
> **THE INTERIM BUILD (Alec's chosen milestone): PROVE THE THIN SPINE, not ship the product.**
>   Spine = intake(002) → register/dial → assemble ONE prompt/sign (verbatim text + 分别画叉 + palette
>   hex + dial hint + reference + logo) → gpt-image-2 composes the WHOLE sign → deliverable = RAW
>   generated.png (gpt-painted text, KNOWN-TEMPORARY debt) → human gate → manifest. Explicitly: the
>   interim tool does NOT yet beat "run the prompt yourself" — the moat is what makes it a product, and
>   it is deferred ON PURPOSE. "Done" = the agent-free spine runs end-to-end and each stage is visible.
>   Do NOT re-bundle the moat into this milestone (that re-creates the over-build trap we just escaped).
>
> **NOT YET DONE:** the thin-spine pivot is DECIDED but NOT SPEC'd or built. Next: spec the thin spine
>   (route kit brands through prompt-compose, retire compose_select/archetype as default) for Claude
>   Code; then later, the moat spike + spec. Visual keep/cut map captured in this session's chat.

> **▶ REGROUP — 2026-06-24 (superseded by the PM block above; the intake fix is BUILT and now the
> composition layer above it is being CUT — kept for lineage):**
> Spec 002 (faithful self-service brief intake + review) is BUILT through US3 and passes its
> falsifiable structural self-tests. The intake confound the 6/23 PM block located is fixed:
>   • INTAKE no longer drops fields: `conductor.ask_questions` now captures EVERY `brief_schema_v3`
>     field VERBATIM (incl. the previously-dropped `format_size`, `mandatory_elements`,
>     `forbidden_elements`); the manifest echoes the inputs the pipeline actually received.
>   • The two under-wired fields now REACH generation: `harness/format_size.py` resolves the brief
>     size to a valid gpt-image-2 pixel size (aspect-preserving, nearest a configurable ~1.57 MP
>     target — 3:2→1536x1024, 1:1→1248x1248, 3:1→2160x720; >3:1/<1:3 clamp + needs_review), and
>     `mandatory_elements` (e.g. 分别画叉) flow VERBATIM into the kit prompt via
>     `harness/prompt_elements.py` + the manifest. The hardcoded 1536x1024 / CANVAS is gone.
>   • `harness/review.py` gives the human one read-only digest of a run (images + inputs received +
>     composition picks + needs_review) to render the eye verdict. New 002 code is asset-profile-AGNOSTIC.
>   • Tests: test_format_size 7/7, test_faithful_intake 4/4, test_brief_wiring 4/4, test_review 4/4,
>     test_conductor 6/6; the 001 suite stays green. NO paid generation in any test.
>
> **NOT YET DONE:** the human's PAID run on the faithful 6-sign brief + the eye verdict (the first
> CLEAN test, SC-003). Structure is green; only the eye validates pixels (constitution §II).
> **FUTURE SPEC (explicitly out of 002 scope):** `asset_type → asset_profile` selection + the
> photographic `poster`/`photo` render dialect (taichi, AIA mother's day). 002 kept the new code
> profile-agnostic so that path is pure addition. Spec/plan/tasks: `specs/002-faithful-brief-intake/`.

> **▶ REGROUP — 2026-06-23 PM (superseded by 2026-06-24 above; the intake fix is now BUILT):**
> A control experiment + code/git root-cause this session invalidated our prior pipeline tests
> and reframed the whole problem from "fix the brains" to "fix the intake."
>
> **THE EXPERIMENT:** T020 finally ran (kit run `output/run_aia_20260623_110905/`): structurally
> clean (distinct icon+layout per sign, text fit per-zone 139px vs 114px, licensed font exact,
> zero needs_review). BUT Alec then ran raw gpt-image-2 himself (full Lily brief + the 4-panel
> reference, no pipeline) and by his eye it beat our output by a considerable margin, producing
> all 6 signs with the 分别画叉 X-marks. Alec's verdict: "our only advantage is licensed font."
>
> **THE CONFOUND (both sides were contaminated, so the test is NOT clean — important):**
>   • Pipeline side: it was fed a STARVED, hand-translated input (2 of 6 signs; 分别画叉 / 两种样式 /
>     size all dropped). The translator was a past Hermes chat, not the tool. (constitution §I violation)
>   • Raw side: Alec PREPENDED "extend these 4 signs, keep the same visual language and DNA" to Lily's
>     brief, i.e. he hand-supplied the reconciliation. That prepend maps 1:1 to the EXISTING
>     `reference_relationship="template"` field that Lily's brief omitted.
>   ⇒ We CANNOT conclude raw > pipeline on equal inputs. We CAN conclude: (1) the intake is broken;
>     (2) Richard's "users don't know what they want, fields make them decide" is now evidence-backed
>     (the winning instruction was a field Lily left blank).
>
> **THE ROOT CAUSE (located in code + git, not theorized):**
>   • LOSSY HUMAN TRANSLATOR: nothing in the tool parses a brief; a chat hand-wrote `--inputs` JSON
>     and silently dropped content. Every "pipeline test" to date secretly tested
>     [lossy hand-translation + pipeline]. The brains were NEVER tested on a faithful brief.
>   • UNDER-WIRED CONTRACT: `conductor.py` never reads `mandatory_elements` (bucket C, where 分别画叉
>     lives) or `format_size` (bucket A, 60x40cm). `grep harness/` confirms NO consumer exists.
>     The X-marks have zero path through our pipeline.
>   • Divergence point: the conductor was BORN (commit 07d733b) consuming a digested 10-field
>     `brief_schema_v3` form, not Alec's mental model of "ref + prompt + brand assets." They never matched.
>
> **METHODOLOGY NOTE (verification, not vibes):** VLM vision over-scored throughout (called every sign
> "production-ready / approved"); mechanical CJK OCR (rapidocr) was the trustworthy reader and DISAGREED
> with the VLM on 3 of Alec's 6 signs (护/拥, 集/渠, 抵/拒). Native-reader Alec confirmed OCR correct,
> VLM wrong on all 3. Lesson re-affirmed (constitution §II): the eye + mechanical OCR beat the VLM.
>
> **DECISION → PENDING SPEC 002 (Fork A chosen, with B's lesson):** fix the intake so a CLEAN test
> becomes possible. Fields are the spine (per Richard + the evidence); wire the dropped fields
> (`mandatory_elements`, `format_size`) through to generation + manifest; pass literal text verbatim;
> reference stays first-class feeding BOTH channels (ref+prompt > ref > prompt, already designed-in).
> Self-service intake + review so Alec authors the brief and judges himself, with NO agent translator.
> Brief authored at `specs/_inbox/002-faithful-brief-intake.md` (run `/speckit-specify` against it).
> Comparison (raw vs pipeline on identical inputs) deferred to a later spec. The eventual stakeholder
> frontend is also later. v1 = faithful intake first, because no comparison is honest until intake is fixed.
>
> **STILL TRUE FROM THE AM BLOCK BELOW:** the kit-of-parts CODE (spec 001) is built + structurally green;
> T020 has now RUN. What changed is our READ of it: structure-green ≠ competitive, and we now know the
> input it was tested on was starved. Do not rip out the register/kit brains; they were never fairly tested.

> **▶ REGROUP — 2026-06-23 AM (superseded by the PM block above; kept for lineage):**
> The kit-of-parts reframe (Spec Kit feature `001-kit-of-parts-composition`) is BUILT through US3 and
> passes its falsifiable structural self-tests. The 6/18 "ONE TEMPLATE, N TEXTS" failure is addressed
> at the FRAME level, not patched.
>
> **BUILT (structure green; pixels still need the paid eye gate, T020):**
>   • `kits/aia.json` — human-authored Kit of Parts (meaning→icon vocabulary + layout-archetype
>     vocabulary), brand DATA, the ONLY place AIA composition literals live.
>   • `harness/kit.py` — stdlib loader/validator (7 schema rules, honest KitError) + derived
>     `kit_profile.json` (answer key wins every conflict). `test_kit.py` 6/6.
>   • `harness/compose_select.py` — deterministic meaning→icon (pinned cue-count rule, honest-null on
>     zero-cut/ambiguous-tie) + collision-avoiding archetype selection (reuse+flag). `test_compose_select.py` 5/5.
>   • `composite_text.fit_text_to_zone` — fit-to-zone clamp: type sized DOWN to the reserved zone with
>     margin, honest-null if it cannot fit (fixes failure (a)). `test_fit_to_zone.py` 4/4.
>   • `scene_author` kit reserve-box mode — paints panel + chosen icon in the icon zone, keeps the text
>     zone CLEAR, composites the fitted licensed headline into it (no scrub → fixes (b); distinct
>     icon+layout per message → fixes (c)). `test_kit_reserve_box.py` 3/3 (incl. compliance-all-licensed).
>   • `conductor.py` — data-driven routing: a brand WITH a kit takes the kit route (reference feeds the
>     kit, never clones); a brand WITHOUT a kit keeps the legacy render-and-scrub/aligned-prompt route.
>     `test_conductor.py` 5/5; `test_render_and_scrub.py` 5/5 (legacy checks pointed at the kit-less brand).
>
> **HOW THE 6/18 FAILURE IS ADDRESSED (frame, not patch):** (a) fit-to-zone clamp = a real
>   fit-within-container constraint (generalizes). (b) icon_zone and text_zone are DISJOINT by kit-schema
>   construction, so no scrub step exists to damage graphics. (c) each sign deterministically gets a
>   meaning-driven icon + a distinct layout archetype; the reference is internalized into the kit, not cloned.
>
> **NOT YET DONE:** T020 — the ONE paid run (`conductor.py --brand aia --inputs conductor_inputs_example.json`)
>   judged by the HUMAN EYE against `desiredresultaia.jpg` (SC-001..005). Structure is green; only the eye
>   validates the pixels (constitution §II). Spec/plan/tasks: `specs/001-kit-of-parts-composition/`.

> **▶ REGROUP — 2026-06-18 (superseded by 2026-06-23 above; the BIG RETHINK is now BUILT):**
> Two things settled this session; one big rethink opened.
>
> **SETTLED — BUILT SINCE THE 6/17 BLOCK (commit 32420f0):**
>   • `harness/conductor.py` (729 lines) — the brand-general human-gate orchestrator — is BUILT and
>     passes its falsifiable self-test 5/5, AGENT-FREE (ran with plain python, no Hermes). It chains
>     calibrate→derive_register→[analyzer]→scene_author and STOPS at the input + approve gates.
>   • Axis A render-and-scrub (`closed_loop_composite.place_measured`) + Axis B reference dial
>     (`reference_style_to_prompt.RUNG_TEMPLATES`) BUILT; self-test 5/5. The reference STYLE analyzer
>     is now WIRED (conductor injects `aligned_prompt` as `scene_author --aligned-prompt`).
>   • The conductor RAN end-to-end and produced 2 AIA reference-job signs (run_aia_20260618_121133),
>     2/2 licensed-compliant.
>
> **SETTLED — EYEBALL VERDICT (Alec, 6/18): those 2 signs FAIL human review on 3 counts, ONE root cause:**
>   (a) headline text far oversized — overflows the die-cut; s2's text runs off the canvas.
>   (b) scrub damages/covers graphics (text-on-icon collision, s1); measure geometry suspect.
>   (c) the 2 signs are the SAME sign behind different text — not a varied family.
>   ROOT CAUSE (one frame): render-and-scrub + dial=extend is structurally a "ONE TEMPLATE, N TEXTS"
>   machine. (a) text is MEASURED from gpt (which paints it oversized) then reproduced → inherits the
>   overflow; no fit-to-margin constraint exists. (b) scrubbing gpt's text region damages whatever it
>   overlapped. (c) feeding ONE reference panel + "extend" tells gpt to CLONE it → every sign identical.
>   Fixing measure/scrub does NOT bridge this — it is the WRONG FRAME.
>
> **BIG RETHINK OPENED (NO code until aligned):** reverse-engineer how a HUMAN goes brief→final and
>   rebuild the unit of work around it. Working hypothesis (under discussion, NOT yet the plan): a human
>   designs each sign as a BESPOKE COMPOSITION — icon chosen to MEAN the message + a per-sign layout
>   that reserves zones + text FITTED into its zone with margin — unified by a shared KIT OF PARTS, NOT
>   one template cloned. The reference is a STYLE SYSTEM to internalize, not a panel to clone. (Ground
>   truth confirms it: the AIA 定稿 panels DIFFER from each other.) Full human-process model to be
>   captured to docs/ once aligned with Alec.
>
> **WORKFLOW SHIFT (Alec's 6/18 meta-realization — the real headline):** the project is now a real
>   codebase and chat-driven development is the bottleneck (context limits, hallucination risk). Move to
>   SPEC-DRIVEN dev: the REPO is the durable context (specs + this map + tests + CLAUDE.md); Hermes is
>   the architect/PM; Claude Code (in-repo, fresh context per task) is the engineer; commit often (the
>   the 1-commit risk below was STALE — there are 4 real commits; the true gaps are coarse
>   cadence + NO off-machine backup, no remote); modularize so no task needs the whole tree in context.
>
> **CONFIG:** Hermes context auto-compress threshold moved 50% → 80% this session.

> **▶ REGROUP — 2026-06-17 (superseded by 2026-06-18 above; kept for lineage):**
> Alec asked "what works vs what doesn't, and where does the tool end and Hermes begin?"
> Answer, verified against the code this session (not the status table):
>
> **THE BOUNDARY (the thing that was never drawn). There are TWO pipelines, not one:**
>   • CLEAN SPINE = `harness/run_harness.py aia` — the only true one-command, agent-free path.
>     It does template-fill (assemble_prompt) + generate + manifest. It does NOT call the smart
>     layers (scene_author / register / composite), reference-selection is STUBBED, and only
>     `config/aia.yaml` exists so it only runs for AIA. `run_harness` HAS been run once
>     (output/run_aia_20260610_102753 exists) — but the SHOWCASE signs came from the scene_author
>     eventprop_*/chroma_* folders, NOT from this thin path.
>   • REAL PIPELINE = the ~15 individually-proven scripts (extract*, register/*, scene_author,
>     generate, measure_canvas, closed_loop_composite, approve) that produced the good AIA signs.
>     These are chained BY HERMES, by hand, with Hermes's eye at 4 judgment points. This is the
>     Hermes-in-loop dependency Alec has worried about from day one. It is real, and now located.
>
> **▶ UPDATE 2026-06-17 (post-verification, supersedes the OCR-blocker framing below):**
> Read the actual code. TWO corrections to my earlier claims this session:
>   1. The OCR text-locator I called "the one true blocker, unbuilt" is ALREADY BUILT + PROVEN.
>      `measure_canvas.py` OCRs the painted image (rapidocr+scipy installed), recovers the
>      container, and emits free_space_bbox + optical_center — real values across ~12 saved sign
>      runs. `closed_loop_composite.py` already chains measure->patch->re-anchor->composite
>      licensed font->strip chroma. Nothing to build there.
>   2. `scene_author.py` is ALREADY a complete single-sign conductor for flat_graphic: its main()
>      runs load_brand -> author scene -> assemble prompt -> generate(logo+ref) -> closed_loop
>      composite -> cutout deliverable. Brand-parameterized (--brand), NOT aia-specific. The clean
>      chroma_sign1_v2 deliverable came from `scene_author --chroma-contain`.
>   => The real Hermes-in-loop gap is NARROW: (a) turning a non-designer's answers into the
>      intent/message/reference files scene_author consumes; (b) running register-prep
>      (calibrate_from_reference -> derive_register) to make the register_profile scene_author
>      needs; (c) chaining approve.py after. The hardcoded-per-job anti-pattern is
>      coverredraw_signs2to5.py (base="output/aia_signN..." x4). The conductor = the GENERAL
>      version of that, keeping the human at the input + approve gates.
>   => SPEC WRITTEN: CONDUCTOR_SPEC.md (build harness/conductor.py + test_conductor.py). Falsifiable
>      dry-run self-test (brand-generality, input-drives-output, correct primitive sequence, N-sign
>      loop, gates present) — NO image gen in the build. Ready to hand to Claude Code.
>
> **CRUCIAL DISTINCTION (Alec, 6/17): AGENT-FREE ≠ HUMAN-FREE.** The dependency we are killing is
>   HERMES-in-the-loop (an AI silently gluing steps + judging invisibly = unshippable, unreproducible).
>   The HUMAN-in-the-loop STAYS BY DESIGN — the designer gives inputs and makes taste calls at defined
>   gates. The tool is NEVER "type one command, walk away." It runs on the human's inputs and STOPS for
>   the human where a human is needed. We automate the glue + drudgery, never the essential inputs/taste.
>
> **THE 4 HAND-OFF POINTS, SORTED into 3 buckets (NOT all become code):**
>   → BECOMES CODE (mechanical, zero taste, the "clicks"):
>     • Locating where text landed in the generated PNG — Hermes eyeballs it today; OCR primitive
>       unbuilt. The ONE genuine new engineering piece; one true blocker to flat path. (task 25)
>     • Running steps in order, passing output→input (sequencing). = the orchestrator's job.
>   → STAYS / BECOMES EXPLICIT HUMAN INPUT (essential, by design — the tool ASKS):
>     • Brief + context — tool asks guided questions (subfields). Human gives DIRECTION, tool does NOT
>       guess. NOT "build an LLM to read the brief." (reframes old task 26)
>     • Reference image — human supplies/picks it; analyzer then reads it (analyzer BUILT, just needs
>       WIRING — verified 6/17 grep: zero imports outside register/+tests). (task 20e)
>     • Brand setup — human supplies logo/VI/fonts once.
>   → STAYS HUMAN JUDGMENT (taste = the whole point):
>     • Approve/nudge the draft (approve.py) + pick among variations.
>   What we REMOVE = only the invisible AI stagehand (Hermes reading the brief, eyeballing the PNG,
>   deciding what runs next, pasting prompt fragments). None of that was ever the designer's job.
>
> **PRESERVED LOAD-BEARING FINDINGS (still true):**
>   • Ref-feed beats parse-only (Alec's eye 3/3). Fed IMAGE overrides imperfect TEXT read; the #20
>     analyzer's imperfect vision read is NOT a gate because the image rescues it. n=1/crop, the
>     muddled-vs-strongly-wrong boundary is uncharacterized → don't overclaim on a NEW brand.
>   • Ground truth for AIA = Yibo's 6-panel 定稿 (brands/aia/assets/aia_dinggao_final_6panel.png).
>   • Over-cloning is NOT a tool dial; slight composition variation = human finishing layer.
>   • RISK: 31 scripts, ONE git commit (harness freeze). Almost everything is UNCOMMITTED.
>
> **RECOMMENDATION (defended in chat 6/17):** do NOT build the host. Build ONE orchestrator (a
>   CONDUCTOR, not a magic button) for the AIA flat-graphic sign: it ASKS the human for context + a
>   reference (human-input gates), runs the proven primitives in order (register→scene_author→generate→
>   OCR-locate→composite→gates, all code), then STOPS and shows the draft for approve/nudge (human-
>   judgment gate). The only NEW build is the OCR text-locator. Wire the ref analyzer. The human is
>   present at the input + approval gates throughout; Hermes is present NOWHERE. Run it, watch where it
>   breaks. That = the falsifiable standalone test: free of the AI agent, NOT free of the human (task 6).


> **Read this first when you lose the thread.** It replaces holding the project in your head.
> The detailed WHY of any decision lives in docs/*.md (linked per section).

---

## THE ONE-SENTENCE PURPOSE
Get a **non-designer** from a messy brief + brand assets to a **handoff-quality DRAFT**
marketing asset — on-brand where the brand must govern, on-occasion where the task must govern.
**It produces drafts a human finishes, NOT final art.** (This line is the guardrail against
tunneling — see "good enough" below.)

---

## THE PIPELINE (one flow)

```
INPUTS (per brand, supplied once)          INPUTS (per job)
  • logo file                                • brief (messy text)
  • VI manual PDF                            • reference image(s)  [optional]
  • font files (otf/ttf/ttc)                 • guided subfields    [the form, schema v3]
  • past posters [ideal]
        │                                          │
        ▼                                          ▼
┌─ A. BRAND ANALYSIS (read VI ONCE) ─┐     ┌─ B. TASK ANALYSIS ──────────────┐
│ extract_colors / extract_text_layer│     │ subfields → bucket A/B/C/D       │
│ extract_typography → answer_key     │     │ calibrate_from_reference (blind  │
│ build_font_index → brands/<b>/fonts │     │   score → register TARGET)       │
│ provenance + human verify           │     │ derive_register → register_profile│
└──────────────┬──────────────────────┘     └──────────────┬───────────────────┘
               │                                            │
               └─────────────► C. RECONCILIATION ◄──────────┘
                   "weight" mechanism (Richard's word for what we built):
                   brand DNA governs HARD (logo, hex, font files);
                   task governs SOFT (atmosphere, occasion, register);
                   reference calibrates MAGNITUDE; subfields set DIRECTION.
                   Output: a register_profile w/ anchors_held + locks_flexed.
                                        │
                                        ▼
                          D. SCENE AUTHORING  (scene_author.py)
                          tier-3 scene plan: palette/staging/props/text_layout/
                          container_shape/hierarchy/font_role + headline_reservation.
                          Lock-relaxation authority: register can override corporate priming.
                                        │
                                        ▼
                          E. GENERATION  (gpt-image-2, generate.py)
                          flat_graphic die-cut → CHROMA-KEY containment (#00B140):
                          one contained sign on green; headline area left BLANK.
                                        │
                                        ▼
                          F. CLOSED-LOOP COMPOSITE  (measure→patch→place)
                          measure_canvas: recover container by chroma (deterministic),
                            OCR ghosts, find optical center.
                          closed_loop_composite: patch ghosts/plates, RE-ANCHOR to
                            detected center, composite LICENSED font (compliance manifest),
                            strip green → cutout.png + preview_white.png.
                          GATES: contained / centered / licensed_exact / no-green /
                            OCR-readback legibility (gate f).
                                        │
                                        ▼
                          G. HUMAN GATE  (approve.py — the nudge loop)
                          plain-language summary → human approves or nudges →
                          re-run only touched fields. THIS is where final taste lives.
                                        │
                                        ▼
                                   DRAFT OUT  →  human finishes (canvas/touch-up)
```

> **⚠️ HONEST NOTE (6/17):** the diagram above is the INTENDED flow. Today only the boxes are
> proven (each ✅ in the table below). The ARROWS between A→G — deciding what runs when, feeding
> each box the right inputs, reading the PNG to place text — are run by Hermes, not by code.
> The clean `run_harness.py` covers only a thin slice (template-fill + E) for AIA. See journey map.

---

## PROVEN vs PENDING (status table)

| # | Component | Key files | Status |
|---|-----------|-----------|--------|
| A | VI color/text extraction + provenance | extract_colors, extract_text_layer, provenance | ✅ proven |
| A | Typography extraction (VI → font mandate) | extract_typography | ✅ proven |
| A | Font library + name-table index | build_font_index, brands/aia/fonts/ | ✅ proven (31 HanYi fonts) |
| A | Answer-key human-verify pass | answer_keys/*.json | 🟡 partial (Tier-1 verify still owed) |
| B | Guided subfields (4-bucket schema) | brief_schema_v3.json | ✅ FORM built as the 004 live-runner + 012 lossless brief (guided fields, verbatim threading); v3 scaffold itself superseded |
| B | Reference blind-score → register target | register/blind_score, calibrate_from_reference | ✅ proven (Step-0 falsified OK) |
| B | derive_register (subfields→profile) | register/derive_register | ✅ proven (direction+magnitude) |
| C | Reconciliation / "weight" mechanism | brief_schema_v2 locks + register_profile | ✅ proven (held vs flexed) |
| D | Scene authoring (tier-3) | scene_author | ✅ proven (ties expert hand-write) — ⚠️ NOT in run_harness path |
| D | Register lock-relaxation authority | scene_author --register-profile | ✅ proven (corporate→event_prop) |
| E | gpt-image-2 generation | generate | ✅ proven; ⚠️ API timeout fix added 6/12 |
| E | Chroma-key containment (Root A) | scene_author --chroma-contain, proto_root_a | ✅ proven (sign #1 v2 clean) |
| F | measure_canvas (OCR + geometry) | measure_canvas | ✅ chroma path proven; HSV path fragile (legacy) |
| F | Closed-loop composite + gates | closed_loop_composite, composite_text, cover_redraw | ✅ proven (incl. occlusion gate f) |
| F | Font compliance (licensed_exact + manifest) | composite_text | ✅ proven |
| G | Approval / nudge loop | approve.py | ✅ built (recolor/removal/restore verified) |
| SPINE | One-command harness (agent-free) | harness/run_harness.py, config/aia.yaml | 🟡 runs, but template-fill ONLY (no D/F), AIA-only, ref stubbed, no saved run folder |
| CONDUCTOR | Brand-general human-gate orchestrator | harness/conductor.py, test_conductor.py | ✅ built 6/18 + self-test green (AGENT-FREE); the THIN route (`--thin`) has since passed the 011/012/014 operator eye-gates (the 6/18 "fails eyeball" note applied to the pre-thin kit/legacy output) |
| THIN ROUTE | Prompt-compose spine (003) + render modes (009) + render-aware register (011) + lossless brief (012) + product refs (013) + explicit usage (014) | harness/scene_author.py, register/derive_register.py | ✅ built + structurally green (seven-suite sweep); three paid eye-gates PASSED on CJXQ (154416 / 164912 / 141245) |
| FRONTEND | Local web app: live-runner (004) + onboarding wizard (006) + reference/product uploads (007/013) + unified nav (010) | frontend/ | ✅ built + structurally green; drives all recent paid runs; eye-gates closed de facto 2026-07-08 |
| INTAKE | Brand onboarding front-half (005) + web gate (006) | brand_intake/, frontend/onboard.py | ✅ proven live: chajiuxingqiu (CLI, T015) + CJXQ (web, production key) |
| AXIS A | Render-and-scrub placement | closed_loop_composite.place_measured | 🟡 built + self-test 5/5; ❌ FAILS eyeball: text overflow + scrub damages icon (template-swap frame is wrong) |
| AXIS B | Reference-relationship dial (extend/match_style/mood) | reference_style_to_prompt.RUNG_TEMPLATES | 🟡 built; "extend" CLONES one panel → signs too similar (6/18). Job needed "vary within a system," not clone |
| — | X-mark handling (分别画叉, signs #4/#5) | cover_redraw X-redraw | 🟡 worked pre-chroma; re-testing in chroma batch |
| — | Brief-intake LLM (messy text→subfields) | — | ⚪ superseded: the 004/012 guided FORM collects the brief losslessly, no LLM glue needed (the human IS the input gate, §I) |
| — | Text-localization OCR (place text in PNG) | — | 🔴 unbuilt — the one true blocker to agent-free flat path (point 3) |
| — | Reference STYLE analyzer (auto, in-pipeline) | reference_style_to_prompt.py | ✅ WIRED 6/18 (conductor injects aligned_prompt as scene_author --aligned-prompt). ⚠️ vision-extract non-determinism remains; "extend" rung clones one panel (point c) |
| A | IP cutout from client source (PSD/PDF/img on white) | psd_to_cutout.py | ✅ BUILT 6/16 — edge-connected bg removal; falsifiable self-test (137 interior comps preserved). ⚠️ leaves ENCLOSED bg pockets; see deferred optimization |
| — | Server (Vercel frontend + long backend) | frontend/server.py | 🟡 LOCAL thin web app built (004/006/007/010, stdlib http.server); cloud/hosted deploy still unbuilt |
| — | Version control hygiene | .git | ✅ per-task commit cadence (spec-driven workflow) + private remote origin (github.com/alecxie1/xcela; IP/secrets gitignored) |

---

## USER JOURNEY — WHAT ACTUALLY HAPPENS (journeys 1-3 written 2026-06-17, journey 4 is TODAY)

**Journey 1 — the clean one-command path (real, but thin):**
  1. `python harness/run_harness.py aia`
  → N on-brand poster variants + manifest (field→slot provenance, file hashes). Deterministic, agent-free.
  LIMITS: AIA only (one config), template-fill (no scene_author / register / composite), no brief intake,
  no compositing, reference stubbed. Good for "basic on-brand variants," NOT the showcase signs.

**Journey 2 — the real pipeline (what made the good signs; HERMES is the assembler):**
  1. Alec pastes a messy brief to Hermes.            [Hermes reads + picks task]    ← AI stagehand
  2. Hermes analyzes the reference image.            [Hermes eye / manual analyzer]  ← AI stagehand
  3. register calibrate + derive → register_profile. [script; Hermes feeds inputs]
  4. scene_author → tier-3 scene plan.               [script; Hermes feeds inputs]
  5. generate (gpt-image-2, chroma-contain).         [script]
  6. Hermes looks at the PNG to find the text area.  [Hermes eye]                   ← AI stagehand
  7. measure_canvas + closed_loop_composite + gates. [scripts; Hermes interprets]    ← AI stagehand
  8. approve.py nudge loop.                           [Hermes drives]
  → handoff-quality DRAFT. Proven on AIA signs — but NOT runnable without Hermes.

**Journey 3 — THE TARGET (conductor + human gates, NO Hermes). What we're building toward:**
  1. Tool ASKS context questions (subfields).         [👤 HUMAN gives direction]
  2. Human points it at the reference image.          [👤 HUMAN supplies]
  3. analyzer reads ref → register → scene_author →    [⚙️ CODE, in order, no AI judgment]
     generate → OCR-locate text → composite + gates.
  4. Tool shows the draft.                             [👤 HUMAN approves or nudges]
  5. Nudge re-runs only the touched step.             [👤 HUMAN, then ⚙️ CODE]
  6. Draft out.                                        [👤 HUMAN finishes on canvas]
  The "command" only kicks off step 1; the human is present at 1,2,4,5,6 throughout. The only NEW
  code vs journey 2 = the OCR locator (step 3) + wiring the analyzer + the conductor that sequences
  and STOPS at the gates. Steps 3's scripts already exist and are proven.

**Journey 4 — TODAY (2026-07, the thin route in the browser; Hermes-free, three eye-gates passed):**
  1. Onboard a brand once: `/onboard` wizard (upload VI PDF → confirm pages → verify locks +
     assign color roles → upload logo → save key).                    [👤 HUMAN verifies, ⚙️ CODE extracts]
  2. Fill the run form at `/`: brand, verbatim message lines, asset type / occasion / render
     style, vibe sliders, design notes, STYLE reference upload (+ 0-6 product photo uploads).  [👤 HUMAN]
  3. `conductor --phase derive`: calibrate + derive_register → assemble_thin_prompt; STOPS at
     the PRE-SPEND GATE (015): derived register + prompt + every recorded assumption as a
     confirmable row; answers re-derive free.                          [⚙️ CODE, then 👤 HUMAN input gate]
  4. Operator confirms (cost stated) → `--phase generate` (drift-guarded) → gpt-image-2 with
     [style, logo, products...] refs; stages stream in the browser.    [👤 HUMAN spend gate, ⚙️ CODE]
  5. Operator judges final.png by eye; nudge = binding note → a new run dir at its own gate.  [👤 HUMAN taste gate]
  This IS journey 3's shape, delivered via the thin route (prompt-compose) rather than the
  measure/composite back-half; the composite moat (licensed-font compositing on the thin route)
  remains the deferred hardening. Proven live on CJXQ: onboarding (web key) + the 011/012/014
  paid eye-gate runs, all form-launched.

**EXPECT today:** journey 4 end to end for any onboarded brand (flat OR photographic marketing
  assets, product-faithful with uploaded shots); every transform individually real and verified.
  The hard engineering (font compliance, chroma containment, occlusion gate) is genuine.
**DON'T EXPECT (yet):** the KIT path's paid validation (001 T020 open); pixel-exact text (thin
  route paints type; logo lockups are model-probabilistic — the composite moat is the fix); a
  hosted/cloud deployment (the app is local).
**STANDALONE, DEFINED CORRECTLY:** remove the AI STAGEHAND (the ← marks in journey 2), keep the 👤
  HUMAN gates (journey 3). Agent-free, NOT human-free. The designer is required at the input + taste
  gates by design; only the invisible AI glue gets replaced — some by code (OCR, sequencing), some by
  an explicit human-input prompt (brief/context/reference). NOT "all judgment points become code."

---

## THE "GOOD ENOUGH" GUARDRAIL (anti-tunneling)
Before ANY fix, ask: **does this make the TOOL better (generalizes to all brands/tasks),
or just this IMAGE better (task-specific taste)?**
- Generalizes → build it. (chroma containment, occlusion gate, font intelligence)
- Task-specific taste → do NOT bake in. It's a human nudge or canvas touch-up.
Examples judged: 霸蛮 font / "text slightly bigger" = TASK TASTE → nudge, not a build.
  Chroma containment = GENERALIZES → built.
The tool is "good enough" when the DRAFT is reliably handoff-quality — NOT when it outputs
finals. Finals are a human surface (approval loop + canvas), by design.

### DEFERRED OPTIMIZATION — auto enclosed-pocket removal in psd_to_cutout (logged 6/16)
**What:** edge-connected fill leaves ENCLOSED white pockets (bg walled off from the image
border by the character's black outline — gaps between arm/tool/body). Alec found 2 on 友小规
(tool side). Fixed THIS image manually via component-removal guarded by his blue-circle boxes
(only remove white comps ≥80% inside a circle; protected the 152k-px shirt comp at 4%-in-box).
Output: youxiaogui_cutout_v2.png.
**Generalizable rule (the build, when we build it):** a trapped pocket is a non-border white
component whose neighbors are ONLY the black outline + (now-)transparent bg — clothing white
instead touches skin/red/etc. That neighbor-palette test separates pocket-white from
eye/shirt/sock-white deterministically, no human circles needed. Ship as optional 2nd pass
`--fill-enclosed-pockets` (default OFF), self-test = removes the 2 known 友小规 pockets while
keeping all 137 interior comps.
**WHY DEFERRED (Alec's call 6/16):** whether a pocket matters depends on STICKER MATERIAL —
invisible on solid-fill, visible on transparent die-cut. Material is an OPEN LILY QUESTION.
Building before we know if the defect bites a deliverable = solving ahead of the requirement.
**TRIGGER TO BUILD:** Lily confirms transparent/die-cut material, OR we hit a 2nd character
where pockets bite. Until then: logged, not chased.

---

## OPEN DESIGN QUESTIONS (the live ones)
1. **Multi-variation + recursive weight-honing** (Richard's 权重 idea): generate 4 drafts with
   DIFFERENT weight configs, human picks, weights converge toward winner, future drafts inherit.
   BLOCKED ON: (a) we generate 1 at a time, (b) random-walk not characterized — can't yet tell
   "variation came from weight change" vs "gpt-image-2 noise." → v2 optimization, sequence AFTER
   single-shot is solid. Don't chase now.
2. **Random-walk characterization**: how much output variance is prompt vs sampling noise?
   Needed before any "pick best of N" loop is legitimate (else you learn a weight that did nothing).
3. **Mid-register STEERING** (not just landing): can we hit an arbitrary formality target (e.g. 5-6),
   not just the extremes? Untested — needs a mid-register job.
4. **Brief-intake automation**: messy client message → structured subfields. The last big
   judgment-glue piece before the tool runs from raw input.
5. **Formality axis is noisy** (playfulness stable): calibrate from n≥3 blind-score mean.

---

## KEY DOCS (the WHY behind each layer)
- docs/REFERENCE_ANALYSIS_register_design_note.md — register: 3 signals, diff-is-register, calibration
- docs/FONT_INTELLIGENCE_design_note.md — 3-layer font (extract/select/render)
- docs/AUTOMATION_GAPS_2026-06-10.md — what Hermes still hand-runs vs the tool (the seed of the 6/17 regroup)
- docs/REPLICABILITY_feedback_persistence.md — style_profile persistence, universal vs brand-taste
- brief_schema_v3.json — the 4-bucket guided subfields (artifact/use-context/content/tone+brand)
- SPEC files (*_SPEC.md, repo root) — each build's contract + verification

## THE DEEP TENSION (Richard nailed it, your words to him)
Brand DNA's visual language vs the task's visual language DIVERGE. Reconciliation = the whole
game: DNA governs primary color/font/logo (high weight); task governs atmosphere/occasion/register
(low or zero VI weight). They clash; the register_profile is where the clash is resolved
per-dimension (anchors_held vs locks_flexed). This is the intellectual core of the tool.
