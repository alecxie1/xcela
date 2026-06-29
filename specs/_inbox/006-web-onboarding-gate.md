# SPEC BRIEF for /speckit-specify — Feature 006: Designer-facing web onboarding gate

Paste the body below as the /speckit-specify description (or point Claude Code at this file).
This is the DECISION MAP. Forks are resolved or explicitly flagged, grounded in the ACTUAL code
(005 `brand_intake/` pure modules + the 004 `frontend/` web pattern, both confirmed this session).
Alec drives /speckit-specify himself; this is the substrate so the spec fills a known shape.

---

## Problem / why
The brand-onboarding FRONT-half (feature 005) is built and works FROM THE TERMINAL: a designer with a
shell can point `brand_intake/intake.py` at a brand PDF, confirm the suggested spec pages, verify the
extracted locks, and walk out with a human-VERIFIED lean `answer_keys/<brand>.json` the thin route
consumes unchanged. But Richard's internal designer does NOT live in a terminal. Today there is no way
for them to onboard a cold brand without the CLI. The capability exists; the designer-facing SURFACE
does not. 006 builds that surface.

This is the same move 004 made for the back-half: 004 wrapped the agent-free thin route in a THIN
local web gate (stdlib server + static page over pure modules, never reimplementing generation). 006
wraps the agent-free 005 onboarding in the SAME kind of gate. The organs exist and are proven; 006 is
the web BODY around them.

## Goal (scopes "done" — READ THIS)
A designer, in the browser, uploads a brand PDF + a logo, confirms the auto-suggested spec pages,
verifies each extracted brand lock (assign color roles, acknowledge every needs_review), and saves a
validated lean `answer_keys/<brand>.json` — with NO terminal. "Done" = the designer onboards a
never-seen brand entirely in the browser, the saved key passes the EXISTING `validate_lean_key`, and
the new brand then appears in the 004 live-runner's brand dropdown (which already lists
`answer_keys/*.json`) so they can immediately generate a sign for it. Onboard then generate, one local
app, no shell.

## LOCKED decisions (do NOT relitigate in the spec — argued and settled)

| Decision | Locked value | Rationale |
|---|---|---|
| What it wraps | the PROVEN 005 PURE modules: `page_finder.suggest_pages`, `extract.extract_brand_colors` / `read_brand_names`, `assemble_key.build_lean_key`, `validate_key.validate_lean_key`, and the gate helpers `intake.unacknowledged_flags` / `finalize_items` | the deterministic, model-free, fail-loud capability is already built + tested (005 20/20). 006 adds a surface, not new extraction logic |
| What it does NOT reuse | `intake.main()` (the stdin `input()` CLI flow) | stdin-bound, not browser-drivable — exactly the 004 lesson (the conductor's `input()` approve gate could not be driven from a browser). The web server calls the PURE modules, not the CLI's interactive main |
| Where it lives | EXTEND the existing 004 `frontend/` local app: a new onboarding screen + routes in `frontend/server.py` + `frontend/index.html` (or a sibling page), same stdlib `http.server` pattern, no new dependency | one local tool the designer opens; the 005 brief already flagged "same server vs separate" and the same-app answer keeps onboard + generate in one place. No framework, no build step (004 ethos) |
| Input modality | REAL multipart file UPLOAD of the PDF and the logo (not a server-side path) | designer-facing: a designer picks files in a browser; the 004 path-text-field was acceptable only because 004 was the single OPERATOR on his own machine. Save the upload server-side, then the existing modules read it |
| The flow | a 3-STEP WIZARD with mid-flow human input: (1) upload PDF -> suggest pages; (2) confirm/correct pages -> run extractors -> show locks + provenance + needs_review; (3) assign color roles + acknowledge every flag + supply brand names + upload logo -> validate -> save | onboarding is inherently interactive; this is the verify gate (constitution §I) moved to the browser. NOT a single fire-and-forget POST like 004 |
| The verify gate | acknowledgment-gated, IDENTICAL semantics to 005: every `needs_review` lock is confirm / edit / keep-flagged before save; a kept flag is written into the saved key; hard-fail only on a missing primary color or logo_path | reuse `validate_lean_key` + `unacknowledged_flags` / `finalize_items` verbatim; the web gate is a new front-end on the same decision logic |
| No AI judgment | the UI MUST NOT auto-decide ANY brand lock: page-finding only SUGGESTS (human confirms), roles are human-assigned, flags are human-acknowledged, brand names are human-confirmed candidates | the whole point (constitution §I); an "AI picks the primary color" shortcut is the v3 silent-judgment disease |
| Standalone core | the 005 CLI (`brand_intake/intake.py`) MUST still run end-to-end with the web gate absent | constitution §I/§VII; the web surface is removable, the agent-free core stands alone (test it) |

## The web stages (what the designer sees; each fails loud or honest-null + a note, never green-on-empty)
```
1. UPLOAD: pick the brand PDF (+ later the logo). Server saves it; runs page_finder.suggest_pages.
2. CONFIRM PAGES: show the suggested 1-indexed color / font / brand-name pages; designer
   confirms or corrects each (the suggestion is a starting point, not an auto-decision).
3. EXTRACT (shows a loading state — OCR is local but takes seconds, NOT a paid call): run
   extract_brand_colors + read_brand_names on the confirmed pages; show each color swatch + hex +
   provenance + needs_review, and the CN/EN brand-name candidates.
4. VERIFY GATE: designer assigns a role to each color (one primary), confirms the brand names,
   uploads the logo, and ACKNOWLEDGES every needs_review (confirm / edit / keep-flagged).
5. SAVE: build_lean_key -> validate_lean_key (FAIL LOUD on a missing primary / logo_path, shown as a
   clear in-browser error, never a silent degrade) -> write answer_keys/<brand>.json + place the logo
   under brands/<brand>/. Then: "this brand is now available in the live-runner."
```

## Verified codebase state (STEP ZERO — confirm before building)
- 005 PURE modules exist + are tested (no paid calls): `page_finder.suggest_pages(pdf) -> {color,
  fonts, brand_name (all 1-indexed), text_layer_ratio}`; `extract.extract_brand_colors(pdf,
  color_pages_1idx) -> {records, note}` (records carry `value.hex` + `needs_review`, role UNSET);
  `extract.read_brand_names(pdf, name_pages_1idx) -> {cn_candidates, en_candidates, raw, note}`;
  `assemble_key.build_lean_key(...)`; `validate_key.validate_lean_key(key)` (raises
  `KeyValidationError` on missing primary / unreal logo_path); `intake.unacknowledged_flags(items)` /
  `finalize_items(items)` (acknowledgment-gate logic, keep-flagged persists `needs_review`).
- `extract_colors` runs rapidocr (LOCAL ONNX, NO paid API) -> the EXTRACT step has latency but spends
  nothing; the UI needs a loading state, NOT a cost label (contrast 004's paid Run button).
- 004 `frontend/`: stdlib `http.server` `server.py` (GET `/`, `/brands`; POST `/run`; GET
  `/run/<id>/stages`, `/image`) + `index.html` (vanilla JS polling) + pure `inputs_writer` /
  `run_view` / `runner`. `/brands` ALREADY lists `answer_keys/*.json`, so a key saved by 006 appears
  in the live-runner with no extra wiring — confirm this.
- Storage: `brands/<brand>/` is gitignored (logo lands there); `answer_keys/<brand>.json` is committed
  brand data. Same artifacts the 005 CLI writes — 006 writes the identical files.
- `intake.main()` is interactive (`input()` prompts) — do NOT call it from the server; reuse the pure
  modules. (The 005 CLI flow may be refactored into a shared pure orchestration function both the CLI
  and the server call — resolve at /speckit-plan, see open question.)

## Forks already resolved (do not reopen)
- Placement: extend the 004 `frontend/` app (LOCKED above). Not a separate server.
- Input: real file upload (LOCKED). Not a server-side path field.
- Font-to-lane pairing (`typography.styles`): OUT of v1, honest-null, same as 005. The designer
  hand-authors `styles` later; a styles-pairing widget is a later enhancement (the new brand's first
  sign carries a generic font directive — the documented FR-010 honest-null, see 005 SC-005).
- Image-only (scanned) PDFs: the degraded path 005 already documents (colors still OCR off captions;
  fonts route to the VLM fallback, more needs_review). v1 web gate surfaces the degradation honestly,
  does not perfect it.

## Out of scope (v1)
- The VLM SEMANTIC layer (tone / imagery_style / motifs / category / logo description) — still
  deferred; the thin route reads none of it.
- Logo EXTRACTION / auto-crop from the PDF — the designer uploads the logo.
- Multi-user / auth / hosted deployment — a LOCAL single-designer tool, like the 004 live-runner.
- A brand-management dashboard (edit/delete existing keys) — v1 is onboard-a-new-brand.
- Changing the back-half or the 005 extraction logic — 006 is a surface; it adapts to them.
- The font-pairing widget (see resolved forks).

## Falsifiable tests (constitution §III — assert VALUES a wrong build cannot satisfy; NO paid calls)
- The save endpoint, given confirmed pages + verified locks for a synthetic PDF (the
  `tests_support/make_pdf` fixture), writes an `answer_keys/<brand>.json` that passes the EXISTING
  `validate_lean_key` AND yields a non-empty thin prompt with the primary hex (reuse the 005 surface).
- The save endpoint FAILS LOUD (4xx + a named reason, no file written) when the primary color is
  unassigned OR the logo is missing — assert no degraded key is saved (the v3 / silent-logo anti-pattern).
- An unacknowledged needs_review flag blocks save (the acknowledgment gate, asserted via the pure
  helper the route calls); a keep-flagged lock writes `needs_review: true` into the saved key.
- The page-suggest endpoint returns the hex-token page (1-indexed) for color, not a color-mention
  page, over the synthetic fixture (the UI consumes `page_finder.suggest_pages`, not a re-implementation).
- A saved brand then appears in the 004 `/brands` list (the onboard -> generate handoff holds).
- Standalone: `brand_intake/intake.py` still runs the full flow from one CLI command with the web gate
  absent (the agent-free core is intact, the UI added no dependency it needs).
- No paid model calls anywhere in the automated tests (the deterministic OCR path is local; build +
  test on the synthetic fixture + the pure modules).

## Hard rules
- NO paid model calls in any automated test. The deterministic color/name path is model-free/local;
  the one paid sign is still the back-half eye-gate (004 / CLI), not part of 006.
- REUSE the 005 pure modules + the 004 server pattern; do NOT reimplement extraction, validation, the
  gate logic, or generation. Do NOT call `intake.main()` from the server.
- The UI MUST NOT auto-decide any brand lock (pages SUGGESTED, roles/flags/names HUMAN). No agent
  judgment in the gate (§I).
- Every stage FAILS LOUD or shows honest-null + the note (§V); a validation failure is a clear
  in-browser error, never a silent save of a degraded key. `logo_path` real or fail loud.
- The saved key MUST be consumed by the EXISTING thin route + the 004 live-runner UNCHANGED.
- The standalone 005 CLI stays runnable with the web gate absent (§VII).
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII). NO em-dashes in user-facing text.

## Definition of done
- A designer onboards a never-seen brand entirely in the browser: upload PDF -> confirm pages ->
  verify locks (roles + acknowledge flags) -> upload logo -> save a validated lean answer_key.
- The saved key passes `validate_lean_key` and appears in the 004 live-runner brand dropdown.
- Page-finding suggests; the human confirms. No lock is auto-decided.
- Save fails loud (in-browser) on a missing primary color / logo_path (assert with a test).
- Structural tests green (paste real output), including the save-writes-valid-key + fail-loud +
  acknowledgment-gate + standalone-CLI-intact tests.
- Report: files changed, the route/flow shape, how the web gate reaches the pure modules, test output,
  and a real cold-brand onboarded through the browser end to end (the human smoke, AFTER the build).

## Open question for /speckit-plan (flag, do not solve in the spec)
The 3-step wizard needs server-side DRAFT STATE across requests (uploaded PDF + confirmed pages +
in-progress verified locks before the final save). Two candidates: (a) a stateful server session
keyed by a draft id (the server holds the draft in memory / a temp dir between steps), or (b) a
stateless client that re-posts the accumulating state each step (the browser holds the draft, posts it
whole at save). Resolve at /speckit-plan against the 004 server shape and the constitution's
thin-surface rule. RELATED: whether to refactor the 005 `intake.py` linear flow into a shared PURE
orchestration function that BOTH the CLI and the web server call (so the gate logic has one home), or
leave the CLI as-is and have the server compose the pure modules directly. Decide at /speckit-plan;
do not assume.
```
