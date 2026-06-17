# BUILD SPEC: scene_author.py — Tier-3 Scene-Authoring Experiment

## Context
This repo generates brand marketing posters with gpt-image-2. We just adopted a
3-tier brief architecture (see `brief_schema_v2.json`, READ IT FIRST):
- Tier 1 (brand identity, locked): from `answer_keys/taichi.json`
- Tier 2 (campaign intent, human-authored): thin, manager-level input
- Tier 3 (scene construction, SYSTEM-authored): staging/props/palette/text-layout

THE EXPERIMENT: can an LLM author Tier-3 from thin Tier-2 intent well enough to
match a hand-written expert prompt? Build the pipeline; a human will grade the
output against a real reference poster afterward.

## CRITICAL CONTAMINATION RULE
The scene-authoring LLM must receive ONLY the inputs listed below. Do NOT add
any scene hints (no colors beyond brand colors, no staging ideas, no prop
suggestions) into the meta-prompt. If you (Claude Code) know or guess what the
target poster looks like — do not encode it. The whole experiment is whether
the model invents a good scene UNAIDED.

## Build: `harness/scene_author.py`

A CLI script, run as:
  .venv/bin/python harness/scene_author.py --brand taichi --out output/scene_author_run1

### Step 1 — load inputs
- Brand answer key: `answer_keys/taichi.json` (tier-1 identity)
- Hardcode this tier-2 intent dict (this is the thin manager brief):
  ```python
  TIER2_INTENT = {
      "subject": "new limited-edition garden fresh tomato cheeseburger",
      "asset_type": "wide horizontal poster",
      "occasion": "seasonal limited-time launch (autumn)",
      "headline_message": "限时上新 — 秘制番茄罗勒芝士堡, campaign window 10月17日-10月31日",
      "feeling": "fresh, garden-to-table, premium, NOT the usual heavy red/gold brand look",
      "reference_image": "logo only"
  }
  ```

### Step 2 — author tier-3 via Anthropic API
- Use the `anthropic` python package (pip install into .venv if missing).
- API key: load from `~/.hermes/.env` (ANTHROPIC_API_KEY) via python-dotenv.
- Model: claude-opus-4-5 (fallback claude-sonnet-4-6 if opus errors).
- Meta-prompt: instruct the model it is an expert art director. Give it:
  (a) tier-1 brand identity JSON, (b) tier-2 intent JSON, (c) the tier-3 field
  list from brief_schema_v2.json (palette_resolved w/ gradient stops,
  background, hero_staging w/ surface+angle+lighting+DoF, props w/ placement,
  text_layout as positioned layers w/ colors, composition).
  Require it to decide on-VI vs off-VI from the intent (the feeling field
  signals departure) and output STRICT JSON only.
- Save raw tier-3 JSON to `<out>/tier3_scene.json`.

### Step 3 — assemble final generation prompt
- Deterministic python (no LLM): render tier-3 JSON + tier-1 lock lines into a
  flat text prompt, same general shape as harness/templates/poster.txt.j2 but
  richer (background block, hero staging block, props block, text layout block,
  mood block). Write the assembled prompt to `<out>/final_prompt.txt`.

### Step 4 — generate
- Call gpt-image-2 via OpenAI `images.edit`, exactly like `harness/generate.py`
  does (read that file and reuse/import its approach).
- Reference image: ONLY the brand logo at
  `/mnt/c/Users/Alecx/Downloads/taichi burger real logo.jpg`
  (do NOT pass any poster image).
- size=1536x1024, quality=high.
- OPENAI_API_KEY also in ~/.hermes/.env.
- Save to `<out>/generated.png`.

### Step 5 — run it for real
- Actually execute the script end-to-end. Verify `<out>/tier3_scene.json`,
  `<out>/final_prompt.txt`, `<out>/generated.png` all exist and are non-trivial
  (png > 100KB). Print the tier-3 JSON and final prompt to stdout in your
  summary so the orchestrator can inspect them.
- If the Anthropic call or image call fails, print the exact error — do not
  fabricate outputs.

## Conventions
- Python 3.11 venv at `.venv` (use `.venv/bin/python`, never system python).
- Keep it ~150 lines, single file, no framework. Reuse existing harness code
  where sensible (import from harness/).
- Do not modify existing harness files; new file only.
- Git: do not commit; leave working tree for human review.
