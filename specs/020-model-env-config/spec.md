# Feature Specification: 020-model-env-config (plan-as-spec, approved in-session 2026-07-14)

**Why**: Kevin (the deployed fork) swapped the planning models to GPT-5.5 by EDITING CODE,
which conflicts with every future pull. Model choice is deployment configuration, not code.
Env-var model NAMES alone cannot de-fork him: gpt-* models need the OpenAI SDK, claude-* the
Anthropic SDK, so the fix is a provider-agnostic client routed by model name.

**Design**:
- NEW `harness/model_client.py`: `text_models()` (env `XCELA_TEXT_MODELS`, comma-separated
  fallback chain, default `claude-opus-4-5,claude-sonnet-4-6`), `image_model()` (env
  `XCELA_IMAGE_MODEL`, default `gpt-image-2`), `call_text_model(model, messages|prompt,
  max_tokens, image_path=None)` routing claude-* -> Anthropic messages.create (content
  blocks, base64 images) and everything else -> OpenAI chat.completions (data-URI
  image_url, max_completion_tokens), returning raw text; `call_text_chain(...)` with
  today's exact warn-per-failure/raise-at-end semantics. Client factories are module-level
  and injectable for free tests.
- Call sites rewired (behavior byte-identical under default env + Anthropic):
  scene_author._call_author (text chain), blind_score.score_once (vision chain),
  calibrate_from_reference._vision_call (vision chain; reference_style imports it),
  approve.py (legacy: chain[0] for the opus site, chain[-1] for the sonnet sites),
  generate.py (image_model(), recorded in the run manifest).
- `.env.example` + README document both vars; the 018 coverage check scans model_client.
- Kevin's de-fork: revert his code edits, set `XCELA_TEXT_MODELS=gpt-5.5` in .env.

**Success**: default env produces today's exact models/requests (pinned); a gpt-* override
routes to the OpenAI branch with correct multimodal payloads (fake-client proven); no bare
`anthropic.Anthropic()` remains outside model_client in live code; full sweep green.

**Tasks**: T001 module + sites + tests + docs (one commit); T002 ship (push both remotes,
VM restart) + the Kevin de-fork instructions appended to his message.
