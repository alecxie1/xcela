# CONDUCTOR_SPEC.md — the brand-general conductor (`harness/conductor.py`)

**Author of this spec:** Hermes, for a Claude Code build session. 2026-06-17.
**Read `CLAUDE.md` and `SYSTEM_MAP.md` first.** This spec assumes both.

---

## 0. THE ONE THING TO UNDERSTAND BEFORE YOU TOUCH ANYTHING

The image pipeline is **already built and proven**. Do NOT rebuild it. `scene_author.py`
already chains the entire single-sign flow end to end (verified 2026-06-17 by reading its
`main()`, lines ~835-1000):

```
scene_author.py main():
  Step 1  load_brand(brand)                    # from answer_keys/<brand>.json
  Step 2  author_tier3(...)                    # the scene plan (Anthropic call)
  Step 3  assemble_final_prompt(...)           # + write composite_spec.json (flat_graphic)
  Step 4  generate_variant(prompt, [logo, ref])# gpt-image-2, headline left blank on chroma
  Step 5  closed_loop(...)                      # measure -> patch ghosts -> re-anchor to
                                                 # detected optical center -> composite the
                                                 # LICENSED font -> strip green -> cutout.png
                                                 # + preview_white.png + compliance manifest
```

A single proven command (this produced the clean chroma_sign1_v2 deliverable):

```
.venv/bin/python harness/scene_author.py \
    --brand aia --asset-profile flat_graphic --chroma-contain \
    --intent-file <intent.json> --register-profile <register_profile.json> \
    --ref-image <style_ref.png> --must-include "<line1>;<line2>" \
    --out output/<run>/sign_<id>
```

**Therefore the conductor's job is NOT image generation.** It is the *human-gate wrapper and
the prep chain* around scene_author. That is the only thing missing, and it is small.

---

## 1. WHAT THE CONDUCTOR MUST DO (and must NOT do)

### The gap it closes
Today a human (Hermes) hand-runs three things that scene_author cannot do for itself:
1. **Turn a non-designer's answers into the files scene_author consumes** (the intent dict,
   the must-include message lines, the reference selection). scene_author takes these as CLI
   flags a non-designer would never know to set.
2. **Produce the `register_profile.json`** that scene_author's `--register-profile` expects.
   That profile is the output of the register prep chain
   (`register/calibrate_from_reference.py` then `register/derive_register.py`), which is run
   by hand today.
3. **Stop, show the draft, take a plain-language nudge, and re-run the touched sign.**
   `harness/approve.py` exists but nothing chains it after scene_author.

### CRITICAL — the human stays in the loop (do not violate)
This tool is **agent-free, NOT human-free.** Read SYSTEM_MAP "AGENT-FREE != HUMAN-FREE".
The conductor must KEEP the human at these gates and must NOT try to be clever and skip them:

| Gate | Who | What |
|------|-----|------|
| Brief + context | 👤 HUMAN | The conductor ASKS guided questions; the human gives direction. The tool does NOT read a messy brief with an LLM and guess. |
| Reference image | 👤 HUMAN | The human supplies/points at the reference. |
| Approve / nudge | 👤 HUMAN | The conductor STOPS, shows the draft, takes a nudge, re-runs. Taste is the human's. |

The conductor automates only the **glue and the prep** (building the intent/profile files,
sequencing the primitives, looping over messages). It never decides taste and never invents
the brief.

### Do NOT
- Do NOT rebuild scene_author / closed_loop_composite / measure_canvas / generate / compositing
  / chroma logic. Call the existing modules.
- Do NOT hardcode brand names, file paths, message strings, or per-sign boxes. The reference
  anti-pattern is `harness/coverredraw_signs2to5.py` — a per-job driver with
  `base="output/aia_sign2_toolrun/generated.png"` hardcoded four times. The conductor is the
  GENERAL version of that. If any AIA-specific literal appears in conductor.py, it is wrong.
- Do NOT call gpt-image-2 in your self-test (it is slow + costs money). See the build/run split
  in section 6.
- Do NOT git commit (the human reviews and commits).
- Do NOT use em-dashes in any user-facing string the conductor prints (standing rule).

---

## 2. FILES TO READ FIRST (get exact interfaces from the source, do not guess)

You MUST read these and use their REAL signatures. I (Hermes) verified the first four; read
the register-prep two yourself and use whatever their actual CLI is.

| File | Why | Verified by Hermes? |
|------|-----|---------------------|
| `harness/scene_author.py` (esp. `main()` ~835-1008, and `chroma_contain_active`, `load_brand`) | The single-sign engine you wrap. Note every CLI flag. | ✅ yes |
| `harness/closed_loop_composite.py` (`closed_loop()`, `main()`) | What scene_author Step 5 calls. CLI: `--image --spec --brand --chroma-key --out`. | ✅ yes |
| `harness/generate.py` (`generate_variant`) | Takes `logo_path` as str OR list (logo + style ref). Don't re-wrap. | ✅ yes |
| `register/reference_style_to_prompt.py` | The analyzer to WIRE (section 5). CLI: `--image --message(repeatable) --hero-icon --out`; writes `aligned_prompt.txt` + `style_descriptor.json`. Pure fn: `assemble_aligned_prompt(descriptor, message_lines, hero_icon)`. | ✅ yes |
| `register/calibrate_from_reference.py` | First half of register prep. **Read it for the real CLI/функcions.** | ⚠️ read yourself |
| `register/derive_register.py` | Produces `register_profile.json` that scene_author consumes. **Read it for the real CLI.** | ⚠️ read yourself |
| `harness/approve.py` (`main()` + the nudge functions) | The approve/nudge gate to chain. Read its real interface. | ⚠️ read yourself |
| `config/aia.yaml` | The per-brand config shape. The conductor reads this kind of file. | ✅ yes |
| `answer_keys/aia.json` | What `load_brand` consumes. (`taichi.json`, `xiucai.json` also exist.) | ✅ exists |

---

## 3. THE CONDUCTOR CLI (what to build)

New file: `harness/conductor.py`. It must be brand-general and runnable with no Hermes.

```
.venv/bin/python harness/conductor.py --brand <brand_id> [options]

Required:
  --brand <id>            Brand id; loads config/<id>.yaml + answer_keys/<id>.json.

Input gate (one of):
  (interactive default)   With no --inputs, the conductor ASKS the human a short, fixed set
                          of guided questions (see section 4), then writes the answers to
                          <out>/inputs.json before proceeding. This IS the human input gate.
  --inputs <file.json>    Skip the questions and load a pre-filled inputs file (for
                          reproducibility, testing, and re-runs). Same schema the interactive
                          path writes. MUST exist for --dry-run.

Control:
  --out <dir>             Run folder. Default: output/run_<brand>_<timestamp>/.
  --dry-run               Do EVERYTHING except the expensive/external calls (no gpt-image-2,
                          no Anthropic scene authoring, no vision). Instead PRINT the exact
                          ordered list of primitive commands the conductor WOULD run, fully
                          parameterized, and write <out>/plan.json. This is the falsifiable
                          test surface (section 6). Must require --inputs.
  --no-approve            Skip the interactive approve gate (batch/test use). Default: gate ON.
```

---

## 4. THE INPUTS SCHEMA (the human-input gate's contract)

The guided questions produce ONE json file, `inputs.json`. Keep the question set SHORT and
plain-language (the user is a non-designer). This schema is also what `--inputs` loads, so the
interactive path and the file path are identical downstream.

```json
{
  "brand": "aia",
  "asset_type": "hand-held event sign (手举牌)",
  "reference_image": "/abs/path/to/style_reference.png",
  "signs": [
    { "id": "s1", "messages": ["守住钱袋子", "护好幸福家"],
      "hero_icon": "a cartoon golden money bag with a white ¥, protruding past the edge" },
    { "id": "s2", "messages": ["远离非法金融", "抵制高息诱惑"], "hero_icon": null }
  ],
  "context": {
    "occasion": "anti-fraud public-awareness campaign",
    "register_hint": "friendly, playful, grabbable photo-prop; NOT corporate",
    "must_include": []
  }
}
```

Notes:
- `signs[]` is a LIST so one campaign = N signs (the showcase was 6). The conductor loops
  scene_author over this list. This is the general version of the hardcoded coverredraw batch.
- `reference_image` and `register_hint` feed the register prep + the analyzer.
- The interactive questions map 1:1 to these fields. Do not add fields the human isn't asked.
  Do not invent a messy-brief parser — the human answers structured questions.

---

## 5. THE FLOW (what conductor.py executes, in order)

```
1. INPUT GATE
   - if --inputs: load it. else: ask the guided questions -> write <out>/inputs.json.

2. LOAD BRAND
   - read config/<brand>.yaml + answer_keys/<brand>.json (use scene_author.load_brand; do
     not reimplement). Fail loudly with a clear message if the brand has no answer key.

3. REGISTER PREP  (produces the register_profile.json scene_author needs)
   - run register/calibrate_from_reference.py + register/derive_register.py on the human's
     reference_image + context.register_hint, per their REAL interfaces (read those files).
   - write <out>/register_profile.json.
   - Honest-null: if the reference is missing or calibration fails, say so and either fall
     back to no register profile (scene_author runs without --register-profile, which is a
     supported path) or stop with a clear message. Never invent a profile.

4. (OPTIONAL) WIRE THE REF-STYLE ANALYZER  -- see section 5a. Default ON when a reference
   image is supplied; degrade gracefully if it fails.

5. PER-SIGN LOOP  (for each sign in inputs.signs):
   - invoke scene_author for ONE sign with the assembled flags:
       --brand <brand> --asset-profile flat_graphic --chroma-contain
       --register-profile <out>/register_profile.json
       --ref-image <reference_image>
       --must-include "<sign.messages joined by ';'>"
       --intent-file <out>/intent_<sign.id>.json   (built from inputs.context + sign)
       --out <out>/sign_<sign.id>
     Run it as ONE synchronous foreground call (subprocess or direct import). NO background
     process, NO polling loop (see section 7).
   - scene_author writes generated.png, final.png, cutout.png, preview_white.png,
     final.png.compliance.json, placement_report.json into the sign folder. Collect those.

6. APPROVE GATE  (unless --no-approve)
   - show the human the draft(s) (print paths to final.png / preview_white.png; the human
     opens them). Ask: approve, or nudge? A nudge re-runs only the touched sign via approve.py
     (read its real interface) or by re-invoking scene_author with adjusted flags.

7. WRITE RUN MANIFEST
   - <out>/conductor_manifest.json: brand, inputs path + sha, per-sign status + output paths,
     register_profile path, the exact scene_author command used per sign, compliance summary
     (licensed vs non-licensed font layers, pulled from each final.png.compliance.json), and
     any honest-null/fallback notes. This manifest is the provenance record.
```

### 5a. Wiring the ref-style analyzer (the "built but not wired" island)
`register/reference_style_to_prompt.py` extracts a style descriptor from the reference and
assembles an aligned "match this reference exactly" prompt. scene_author currently passes the
reference image to gpt-image-2 (visual channel) but does NOT use the analyzer's text. Wire it
the LEAST invasive way:
- Option A (preferred, low-risk): the conductor calls `extract_style_descriptor()` +
  `assemble_aligned_prompt()` and passes the result into scene_author as additional
  `--style-notes` (scene_author already accepts `--style-notes`, a supported flag). This feeds
  the semantic channel without modifying scene_author's internals.
- Do NOT re-architect scene_author's prompt assembly. If Option A doesn't cleanly fit, write
  the aligned prompt to `<out>/sign_<id>/aligned_prompt.txt` and note in the manifest that it
  was generated but not injected, so the human can decide. Honest partial > silent guess.
- Per SYSTEM_MAP: the fed IMAGE already rescues an imperfect text read, so this wiring is a
  reliability upgrade, not a gate. If it fails, the run still proceeds on the image channel.

---

## 6. DEFINITION OF DONE + FALSIFIABLE SELF-TEST (the part that matters)

The build is done when `conductor.py` exists, is brand-general, keeps the human gates, and
passes a self-test that a WRONG or no-op implementation cannot pass. **The self-test must NOT
call gpt-image-2 or any paid/slow endpoint** (build/run split — the human runs the real
generation afterward and judges the images by eye).

Write `test_conductor.py` (in repo root, like the other `test_*.py`). It must assert STRUCTURAL
correctness via `--dry-run`, on properties a hardcoded/no-op conductor fails:

1. **Brand-generality (kills hardcoding).** Run `--dry-run` with `--brand aia` and again with a
   second brand that has an answer key (`taichi` or `xiucai`). Assert the emitted plan.json
   primitive commands reference `answer_keys/<brand>.json` and `config/<brand>.yaml` for the
   brand passed — i.e. the two runs differ in their brand paths. A conductor with `aia`
   hardcoded (the coverredraw anti-pattern) produces identical aia paths for both and FAILS.
   Also assert: `grep -i "aia" conductor.py` finds NO brand literal in the logic (only maybe a
   help-string example). Hardcoded brand id in code = fail.

2. **Human input actually drives output (kills input-ignoring no-op).** Run `--dry-run` twice
   with two `--inputs` files that differ ONLY in `signs[].messages`. Assert the per-sign
   scene_author commands in plan.json carry the DIFFERENT message strings in `--must-include`.
   A conductor that ignores inputs and calls scene_author with defaults emits identical
   commands and FAILS.

3. **Correct primitive sequence, in order (proves it wraps, not reimplements).** Assert
   plan.json lists, per sign, the ordered steps: register-prep -> scene_author(flat_graphic,
   chroma-contain, with the register_profile + ref + messages) -> [approve]. Assert it
   INVOKES `harness/scene_author.py` and `register/derive_register.py` (by name) rather than
   containing its own gpt-image-2 / compositing calls. `grep` conductor.py for
   `images.edit`, `gpt-image-2`, `b64decode` — any hit means it reimplemented generation and
   FAILS (it must delegate to the proven modules).

4. **Sign count generality.** `--dry-run` with a 1-sign inputs file and a 3-sign inputs file:
   assert plan.json contains exactly 1 and exactly 3 scene_author invocations respectively.
   Proves the N-sign loop is real, not a fixed unrolled batch.

5. **Human gates present.** Assert: with no `--inputs` the code path calls the question/ask
   function before any primitive (grep the code path or assert it prompts); and the approve
   gate is invoked unless `--no-approve`. A conductor that runs straight through with no gates
   FAILS. (You may assert this structurally without real stdin by checking the gate functions
   are on the default path.)

Report the self-test as N/5 with WHAT each asserted and the real values it compared (not just
"PASS"). If a check is red, say so plainly and stop — do not paper over it.

**One real end-to-end smoke is allowed but OPTIONAL and must be explicitly flagged as costing
an image call:** if you want to prove the wrapper truly drives scene_author, do ONE real sign
for `--brand aia` and report the actual output file sizes from disk (`cutout.png`,
`final.png.compliance.json`). If you do this, run it as ONE synchronous foreground call and
report honestly if the API errors. If you skip it, say so; the human will run the real batch.

---

## 7. HARD RULES FOR THIS BUILD (learned from prior delegated builds, non-negotiable)

1. **NO background processes, NO self-polling.** Every long step is ONE synchronous foreground
   blocking call with its own timeout. Do not launch a background job and poll it — that has
   burned the entire turn budget in past builds. (scene_author / generate already set their own
   internal API timeouts.)
2. **Honest reporting.** If something fails, say so plainly with the real error. Do NOT
   fabricate file contents, sizes, or "PASS" results. Print real sizes from disk via `stat`.
3. **Self-test asserts VALUES/STRUCTURE, not token presence.** A check like `"scene_author" in
   plan_text` is a no-op gate. Assert the actual brand path, the actual message strings, the
   actual invocation count. A test that passes by echoing this spec's vocabulary back is wrong.
4. **Do not git commit.** Leave the working tree dirty for the human to review.
5. **Env:** API keys load from `~/.hermes/.env` (the existing modules already do
   `load_dotenv(Path.home()/".hermes"/".env")`). Use the venv: `.venv/bin/python`.
6. **If you discover this spec is wrong about an interface** (e.g. derive_register's real CLI
   differs from what you assumed), FOLLOW THE CODE, not the spec, and note the discrepancy in
   your final report so the human can fix the spec. The source files are ground truth.

---

## 8. FINAL REPORT (what to tell the human at the end)

- What you built (`conductor.py` line count, `test_conductor.py`).
- The self-test result as N/5 with the real compared values per check.
- Whether you ran the optional real-image smoke; if so, the actual on-disk output sizes.
- The exact one-line command the human runs to drive a real AIA campaign through it.
- Anything in this spec that turned out wrong against the real code, and what you did instead.
- Any gate or wiring you could only do partially, stated honestly (partial + flagged beats
  silent + guessed).
```
