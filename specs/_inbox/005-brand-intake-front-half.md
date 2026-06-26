# SPEC BRIEF for /speckit-specify — Feature 005: Brand-intake front-half (PDF to verified answer_key)

Paste the body below as the /speckit-specify description (or point Claude Code at this file).
This is the DECISION MAP. Every fork was argued and resolved with Alec (2026-06-26), grounded in a
live code audit AND an independent Claude Code review (14/14 claims confirmed, 5 integration gaps
surfaced). Alec drives /speckit-specify himself; this is the substrate so the spec fills a known
shape, not rediscovers forks.

---

## Problem / why
The back-half (brief to sign, thin route) is built and validated. But onboarding a NEW brand has no
working path. The thing branded the "analyzer" (`analyze_brand_v3.py`) is a HARDCODED SCAFFOLD, not
a runnable program: it takes no arguments, reads pre-rendered taichi PNGs from `/tmp/taijibao_pages`,
never ingests an arbitrary PDF, scores against a hardcoded taichi key, and EXITS 0 ON TOTAL FAILURE
(confirmed by running it). Richard wants his internal designer using the tool on REAL (new-brand)
cases ASAP for feedback. New brands are the real cases, so the front-half is on the critical path.

The working capability is the DETERMINISTIC extractors (`extract_colors.py`, `extract_text_layer.py`),
proven this session on a cold brand (chajiuxingqiu): colors extracted at ΔE < 1, model-free, with a
self-check that flags `needs_review` on disagreement. This feature builds the BODY around those
proven organs: PDF in, human-gated extraction, a LEAN verified answer_key out.

## Goal (scopes "done" — READ THIS)
A path where the designer points at a brand-guideline PDF and walks out with a human-VERIFIED
`answer_keys/<brand>.json` that the EXISTING thin route consumes unchanged. Same intake to process to
HUMAN-GATE pattern as the back-half; here the gate is VERIFY-the-extraction (constitution §I input
gate). "Done" = a designer onboards a brand the system has never seen and then runs the back-half on
it, end to end, with the human verifying every brand lock before it is saved.

## LOCKED decisions (do NOT relitigate in the spec — argued and settled)

| Decision | Locked value | Rationale |
|---|---|---|
| Extraction engine | REUSE `extract_colors.py` + `extract_text_layer.py` (deterministic, proven). DO NOT build on `analyze_brand_v3.py` (hardcoded taichi scaffold). | The deterministic path is the proven, model-free, self-checking capability; v3 is a cadaver wired to taichi |
| Output schema | a LEAN answer_key: ONLY the fields the thin route consumes | empirically proven: a key stripped to these 4 produces a BYTE-IDENTICAL gpt prompt vs the fat AIA key |
| Page-finding | DETERMINISTIC heuristic SUGGESTS the spec pages, human CONFIRMS | proven this session (the color page is the one with real hex tokens, not the 8 that merely mention color); keeps the human at the input gate (§I) without dumb scanning. NOT AI auto-detect (that is the v3 silent-judgment disease) |
| Logo | designer SUPPLIES the logo file; `logo_path` MUST be written with a real brand-correct path or FAIL LOUD | reviewer-found landmine: `scene_author` defaults a missing `logo_path` to a HARDCODED taichi logo and silently feeds it to gpt (cross-brand contamination, violates §V) |
| New-key validation | the front-half MUST validate the key it writes and FAIL LOUD on missing locks | the conductor only checks the key EXISTS, never completeness; a partial key degrades silently today (blank hex to "primary brand color  stays" in the prompt) |
| VLM semantic layer | DEFER entirely (tone, imagery_style, motifs, category, logo description) | the thin route reads NONE of these; extracting them re-enters exactly the VLM-semantic territory v3 fails at (§IV: build for the tool, not to fit one benchmark) |
| Fail-loud | every stage hard-fails or emits honest-null + note; NEVER green-on-empty | v3's exit-0-on-total-failure is the anti-pattern (§V) |

## The LEAN answer_key schema (the extraction target — proven sufficient)
A new brand's key carries ONLY what the thin pipeline reads. Proven empirically: stripping the real
AIA key to these fields yields a byte-identical gpt prompt; the dropped fields have NO code path into
the per-job pipeline (verified by diffing `derive_register` + `assemble_thin_prompt` output, with a
control that confirmed the diff DETECTS a consumed-field change).

CONSUMED (must extract / supply):
- `brand` / `brand_en` (and `fields.brand_name_cn.value` / `brand_name_en.value`) — text layer
- `fields.colors.items[]` with at least `role` (one MUST be "primary") + `printed_html` (hex) —
  deterministic extractor (PROVEN, ΔE < 1)
- `logo_path` — designer supplies a real file; REQUIRED or fail loud (see landmine above)
- `fields.typography.styles` (the register-lane font map) — OPTIONAL. This is HAND-AUTHORED human
  judgment ("the compliant-but-playful pick for event_prop"), NOT extractable from a PDF. If the
  designer skips it, honest-null: `derive_register` omits `font_resolved` and the font directive goes
  generic. No crash, lesser font control. The verify UI MAY let the designer pair fonts to lanes.
- provenance: `source_pdf`, `verified_by`, `verified_date` — cheap, human-useful, keep

DELIBERATELY OMITTED for new brands (proven zero effect on the image):
- `type` / `scoring` tags on every field (these feed `score_v4.py`, the BENCHMARK, not generation)
- `typography._candidates_rejected` / `_provenance` / `_confidence`, the 3 English fonts, `rules`
- `category`, `motifs`, `tone`, `imagery_style`, `logo_appearance` (legacy/VLM author only)
- `slogan` (read but DELIBERATELY not injected — the tagline-hallucination fix)
NOTE: the new key will be deliberately THINNER than AIA's. AIA is fat because it was built to be
GRADED. The MVP key is built to be CONSUMED. Do not copy AIA's shape; copy its consumed subset.

## The MVP body, stage by stage (this is what does NOT exist yet — it is a real build)
```
PDF in
  → render pages to images (NEW: nothing ingests an arbitrary PDF today)
  → heuristic SUGGESTS color/font/brand-name pages (NEW: regex over text layer — real hex tokens,
     font-name patterns; the human CONFIRMS/corrects the suggested page numbers)
  → run the PROVEN extractors on the confirmed pages (extract_colors + extract_text_layer)
  → grab brand names (text layer)
  → designer supplies the logo asset (input gate)
  → assemble the LEAN answer_key
  → VALIDATE LOUD (primary color present? logo_path real? else fail with a named reason)
  → HUMAN VERIFY GATE: show each extracted lock + its provenance/needs_review flag; human edits/approves
  → write answer_keys/<brand>.json (+ place/verify logo asset under brands/<brand>/)
```
The extractors are the proven ORGANS. Everything else on that line is the missing BODY.

## Verified codebase state (STEP ZERO — confirm before building)
- `extract_colors.py`: deterministic (fitz + rapidocr + PIL, NO LLM). OCRs the hex/RGB caption AND
  pixel-clusters the swatch, reconciles, sets `needs_review` on ΔE disagreement. FOOTGUN: `render_page`
  is 1-INDEXED (`doc[page_no - 1]`); a 0-indexed caller renders the wrong page and can return [].
- `extract_text_layer.py`: auto-detects image-only PDFs (text_layer_ratio < 0.05) and routes
  fonts/motifs to a vision_model fallback. Has a hardcoded `BRANDS` dict (taichi/xiucai only) with
  per-brand page numbers — there is NO page-finding logic today (that is what this feature adds).
- `analyze_brand_v3.py`: hardcoded taichi scaffold, exits 0 on failure. DO NOT build on it. It MAY be
  cannibalized for its per-domain VLM prompts IF the deferred semantic layer is ever revived (not now).
- The thin route reads the answer_key via `assemble_thin_prompt` (names + colors only) and
  `derive_register` (typography.styles to font_resolved). `--thin` BYPASSES kit_mode, so a new brand
  needs NO `kits/<brand>.json`. `config/<brand>.yaml` is legacy-only (run_harness), NOT loaded by the
  conductor — a new brand needs NO config.yaml. (Both confirmed by the independent review.)
- Binary assets (logo, font files) live under gitignored `brands/<brand>/`; the JSON references paths
  there. The front-half must place/verify those files, not only write JSON.

## Forks already resolved (do not reopen)
- Page-finding: heuristic-suggest + human-confirm (LOCKED above). Alec explicitly chose the heuristic
  IN scope for the MVP (designer confirms guesses, not types raw page numbers blind).
- Logo extraction from the PDF: OUT. Designer supplies the file. Auto-crop is a later enhancement.
- Image-only (scanned) PDFs: extractors already route to a VLM fallback for fonts/motifs; colors still
  OCR off the caption. v1 may treat a fully image-only brand as a degraded path (more needs_review),
  not a hard requirement to perfect.

## Falsifiable tests (constitution §III — assert VALUES a wrong build cannot satisfy; NO paid calls)
- Run the page-finding heuristic on a real multi-page VI PDF; assert it returns the page that actually
  contains hex tokens (e.g. for chajiuxingqiu the color page), NOT a page that merely mentions color.
- Extraction on a cold brand returns colors whose hex matches the printed spec (assert the actual hex
  string, e.g. chajiuxingqiu yields #31B4E7 / #73C900 / #94D4EB), and flips `needs_review` when OCR vs
  pixel disagree beyond threshold (assert the flag on a known-garbled read).
- The assembled lean answer_key, fed to `assemble_thin_prompt` + `derive_register`, produces a NON-EMPTY
  prompt with the primary color hex present (assert the hex appears; assert no blank "color  stays").
- Validation FAILS LOUD (raises / nonzero) on a key missing a primary color OR missing logo_path —
  assert it does NOT silently produce a degraded prompt (the v3 / silent-logo anti-pattern).
- A lean key (names + colors + logo + styles only) yields a prompt BYTE-IDENTICAL to the same brand's
  fat-key prompt (the proven generalization invariant — regression guard).
- Standalone: the whole front-half runs from ONE CLI command on a PDF path with NO model calls in the
  deterministic path (colors/names), so the build + tests spend nothing.

## Hard rules
- NO paid model calls in any automated test. The deterministic color/name path is model-free; build
  and verify there. Any VLM fallback (image-only fonts) is exercised only in a human-run smoke test.
- REUSE the proven extractors; do not reinvent color/text extraction. Do not build on the v3 scaffold.
- Every stage FAILS LOUD or emits honest-null + a recorded note (§V). No green-on-empty, no silent
  fallback (especially logo_path).
- The output answer_key MUST be consumable by the EXISTING conductor/thin route UNCHANGED (the
  front-half adapts to the back-half's read surface, not vice versa).
- Keep CLAUDE.md + SYSTEM_MAP current in the SAME commit (§VII). NO em-dashes in user-facing text.

## Definition of done
- A designer-driven path takes a never-seen brand PDF to a human-verified `answer_keys/<brand>.json`.
- Page-finding heuristic suggests the spec pages; the human confirms/corrects them.
- The deterministic extractors run on the confirmed pages; provenance + needs_review surface to the human.
- Validation fails loud on a missing primary color or logo_path (assert with a test).
- The resulting lean key runs through the EXISTING thin back-half end to end (one paid sign is the
  human eye-gate AFTER the build, not inside it).
- Structural tests green (paste real output), including the byte-identical-prompt regression guard.
- Report: files changed, the page-finding mechanism, the validation rules, test output, and a real
  cold-brand extraction (e.g. chajiuxingqiu or mahoupao) as evidence.

## Open question for /speckit-plan (flag, do not solve in the spec)
Where does this front-half live relative to the 004 frontend? Two candidates: (a) a second screen in
the same live-runner server (brand-onboarding tab to back-half tab), or (b) a separate CLI/flow for
now and wire the UI later. Resolve at /speckit-plan against the 004 server shape; do not assume.
