# SYSTEM MAP — Handyprint Brand Design Tool
_Single source of truth for "what is this whole thing." Updated 2026-07-01._

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
| B | Guided subfields (4-bucket schema) | brief_schema_v3.json | 🟡 schema done, FORM unbuilt (UI) |
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
| CONDUCTOR | Brand-general human-gate orchestrator | harness/conductor.py, test_conductor.py | ✅ built 6/18 + self-test 5/5 (AGENT-FREE); ⚠️ output fails eyeball — see 6/18 regroup |
| AXIS A | Render-and-scrub placement | closed_loop_composite.place_measured | 🟡 built + self-test 5/5; ❌ FAILS eyeball: text overflow + scrub damages icon (template-swap frame is wrong) |
| AXIS B | Reference-relationship dial (extend/match_style/mood) | reference_style_to_prompt.RUNG_TEMPLATES | 🟡 built; "extend" CLONES one panel → signs too similar (6/18). Job needed "vary within a system," not clone |
| — | X-mark handling (分别画叉, signs #4/#5) | cover_redraw X-redraw | 🟡 worked pre-chroma; re-testing in chroma batch |
| — | Brief-intake LLM (messy text→subfields) | — | 🔴 unbuilt (judgment glue — point 1) |
| — | Text-localization OCR (place text in PNG) | — | 🔴 unbuilt — the one true blocker to agent-free flat path (point 3) |
| — | Reference STYLE analyzer (auto, in-pipeline) | reference_style_to_prompt.py | ✅ WIRED 6/18 (conductor injects aligned_prompt as scene_author --aligned-prompt). ⚠️ vision-extract non-determinism remains; "extend" rung clones one panel (point c) |
| A | IP cutout from client source (PSD/PDF/img on white) | psd_to_cutout.py | ✅ BUILT 6/16 — edge-connected bg removal; falsifiable self-test (137 interior comps preserved). ⚠️ leaves ENCLOSED bg pockets; see deferred optimization |
| — | Server (Vercel frontend + long backend) | — | 🔴 unbuilt (decided: not pure serverless) |
| — | Version control hygiene | .git | 🟡 4 commits (freeze/backup/conductor/render-scrub) — work IS committed, but cadence coarse + NO remote/off-machine backup (gh not installed) |

---

## USER JOURNEY — WHAT ACTUALLY HAPPENS TODAY (2026-06-17)

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

**EXPECT today:** every transform above is individually real and verified; with Hermes driving you
  get on-brand drafts a human finishes. The hard engineering (font compliance, chroma containment,
  occlusion gate) is genuine.
**DON'T EXPECT (yet):** to run journey 3 — it's the target, not built. Today the in-between glue and
  the PNG-reading are still Hermes (journey 2), and only AIA has a config. The "tool" today = proven
  parts bin + thin spine + Hermes as the assembler.
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
