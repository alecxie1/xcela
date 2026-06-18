# CONDUCTOR_INPUTS_RECONCILIATION.md

**Purpose:** correct the CONDUCTOR_SPEC section-4 `inputs.json` so the campaign-level
questions collect the REAL fields `register/derive_register.py` consumes, wire
`calibrate_from_reference` into `derive_register` so a reference still sets magnitude, and
pin the safe (non-injecting) path for the ref-style analyzer. Read after CONDUCTOR_SPEC.md.
This note is the contract `conductor.py` builds against where it differs from that spec.

Authored against the code (verified 2026-06-17), not the spec. Where the two disagree, this
note follows the code (per CONDUCTOR_SPEC rule 7.6).

---

## 1. THE PROBLEM (one paragraph)

CONDUCTOR_SPEC section 4 collapses all register-bearing input into two free-text strings
(`context.occasion`, `context.register_hint`). But `derive_register.py` (the only thing that
produces the `register_profile.json` scene_author needs) requires a STRUCTURED `--subfields`
file and reads these keys and no others:

```
vibe.formality   vibe.playfulness   usage_context   logo_treatment   brand_strictness   reference_diff(optional)
```

There is no code path from `register_hint` text to those fields. Built as specified, the
conductor could never produce a real register profile, would fall into the spec's own
"honest-null -> run without a profile" escape on EVERY run, and would silently delete one of
the tool's two intellectual cores (the held-vs-flexed register mechanism, the AIA logo-omit /
playful-shape behavior). The fix is already in the repo: `brief_schema_v3.json` buckets B and
D ARE those fields. The input gate should collect them directly.

---

## 2. THE CORRECTED inputs.json

The only structural change: replace the vague `context` with brief_schema_v3 bucket-B/D field
names VERBATIM, so the conductor writes `context` straight back out as the `subfields.json`
`derive_register` consumes. No translation step, so no judgment glue. `signs[]` is unchanged.

```json
{
  "brand": "aia",
  "asset_type": "手举牌 hand-held event sign",
  "reference_image": "/abs/path/to/style_reference.png",
  "reference_relationship": "template — extend this series (clone look, change message)",

  "context": {
    "usage_context": "held for photos / posed with",
    "audience": "general public",
    "setting": "event / festival",
    "vibe": { "formality": 2, "playfulness": 8, "warmth": 7 },
    "logo_treatment": "omit",
    "brand_strictness": "expressive departure",
    "occasion": "anti-fraud public-awareness campaign"
  },

  "signs": [
    { "id": "s1", "messages": ["守住钱袋子", "护好幸福家"],
      "hero_icon": "a cartoon golden money bag with a white ¥, protruding past the edge" },
    { "id": "s2", "messages": ["远离非法金融", "抵制高息诱惑"], "hero_icon": null }
  ]
}
```

`context` field names match brief_schema_v3 exactly. The conductor builds the subfields file as
`subfields = { "asset_type": <top-level>, **context }` and hands it to `derive_register`, which
reads what it needs and ignores the rest. Identity pass-through, not inference.

---

## 3. WHAT FEEDS WHAT (the honest wiring table)

Every input field, its consumer, and whether the consumer is real today. The "(not wired)"
rows are collected for provenance and future use; the conductor must NOT pretend they steer
the register. This is the falsifiable-honesty the project requires.

| inputs field | consumed by | effect |
|---|---|---|
| `context.usage_context` | derive_register | USAGE_RULES -> base register ("held for photos" => event_prop) |
| `context.vibe.formality` | derive_register | confirms/overrides tier; sets slider magnitude when no calibration |
| `context.vibe.playfulness` | derive_register | same |
| `context.logo_treatment` | derive_register | `omit`/`subtle` flex the logo lock; scene_author then drops the logo from generation |
| `context.brand_strictness` | derive_register | `expressive departure` + a ref-diff can release the primary-color anchor |
| `context.vibe.warmth` | (not wired) | in brief_schema_v3, but derive_register never reads it. Provenance only |
| `context.audience` | (not wired) | schema says "drives playfulness ceiling"; not implemented in code. Provenance only |
| `context.setting` | (not wired) | provenance only |
| `context.occasion` | scene_author (intent) | free-text, templated into the per-sign intent dict (occasion/subject framing) |
| `reference_image` | calibrate + scene_author `--ref-image` + analyzer | sets register magnitude; visual channel to gpt-image-2; analyzer source |
| `reference_relationship` | (not wired) | brief_schema_v3 governing dial (template/style/inspiration). No code consumes it yet. Record in manifest only |
| `signs[].messages` | scene_author `--must-include` + intent.headline_message + analyzer `--message` | the headline lines for that sign |
| `signs[].hero_icon` | analyzer `--hero-icon` | per-sign protruding hero device |

Honest call-out: of the bucket-B/D fields the user asked to collect, only `usage_context`,
`vibe.formality`, `vibe.playfulness`, `logo_treatment`, and `brand_strictness` actually move the
register today. `audience`, `setting`, `warmth`, and `reference_relationship` are collected
because they belong to the schema and are useful provenance, but wiring them into the register
leap is future work, not part of this build. The conductor records them; it does not fake their
influence.

---

## 4. REGISTER PREP WIRING (calibrate -> derive)

Both steps are CAMPAIGN-LEVEL: one reference and one vibe produce ONE register profile shared
by all signs. Run order:

```
IF reference_image present:
  calibrate_from_reference.py --image <ref> --brand <brand> --out <out>
      -> writes <out>/calibration.json   (register_target = magnitude, from a BLIND vision score)
  derive_register.py --subfields <out>/subfields.json --brand <brand>
                     --calibration <out>/calibration.json --out <out>
      -> writes <out>/register_profile.json
ELSE (no reference):
  derive_register.py --subfields <out>/subfields.json --brand <brand> --out <out>
      -> register magnitude from moderated register defaults (event_prop => 5/7),
         NOT the raw subfield extremes (derive_register's documented overshoot fix)
```

What this means for the human's vibe sliders, stated plainly so we do not mislead:
- The sliders ALWAYS set DIRECTION (which register bucket).
- With a reference, the reference's blind score sets the MAGNITUDE (the slider numbers become
  direction-only; calibration overrides them). This is the proven "reference sets magnitude"
  mechanism, and it is the reason to wire `--calibration` rather than running the two steps
  independently.
- With no reference, magnitude comes from moderated per-register defaults, and only falls back
  to the raw slider numbers if the register has no default entry.

Honest-null: if `reference_image` is set but `calibrate` fails (vision error / non-parse),
the conductor runs `derive_register` WITHOUT `--calibration`, and records in the manifest that
calibration was attempted and failed and magnitude fell back to defaults. It never invents a
calibration. If `derive_register` itself fails, the conductor runs scene_author without
`--register-profile` (a supported path) and says so. Never a silent neuter.

---

## 5. THE QUESTION SET (short, adaptive, accept-all)

`--brand` is a CLI arg, so brand DNA (colors/fonts/logo) is never asked. The interactive gate
shows each field with its default and the human presses Enter to accept or types a new value
(brief_schema_v3 "accept-all" behavior). Active context questions a non-designer answers, in
order, defaults in brackets:

1. Asset type?  [手举牌 hand-held event sign]
2. Reference image path? (Enter to skip)  [none]
3. How formal, 0 casual to 10 official?  [5]   +   How playful, 0 serious to 10 fun?  [5]
4. Logo on it? required / subtle / omit?  [required/prominent]
5. How tightly on-brand? strict VI / brand + accents / expressive departure?  [brand + accents]

That is ~5 active prompts (item 3 is the register pair). `usage_context` defaults from
asset_type (brief_schema_v3: asset_type carries a default use-context; 手举牌 => "held for
photos"), and `audience`/`setting`/`warmth` take schema defaults silently. A fast user accepts
all and answers nothing but the per-sign content. The defaults are brand-SAFE (logo required,
brand+accents): the human flips logo->omit and strictness->expressive for an event prop, which
is exactly the taste call that should be a human's.

Per-sign content (not "context" questions, this is what they actually want printed): for each
sign, ask the message line(s) and an optional hero-icon description. This populates `signs[]`.

The calibration gate from brief_schema_v3 (`"register profile shown to human in plain language
BEFORE generation"`) is satisfied by printing the derived register (inferred_register, the two
sliders, anchors_held, locks_flexed) for eyeball before the per-sign loop. This is a cheap,
no-cost human checkpoint and worth keeping.

---

## 6. REF-STYLE ANALYZER: SAFE PATH (no --style-notes injection)

`reference_style_to_prompt.assemble_aligned_prompt()` returns a COMPLETE, standalone
gpt-image-2 prompt ("Use the ATTACHED reference image as the EXACT visual-style template.
Create ONE new... CHANGE ONLY THE MESSAGE..."). It is NOT a notes fragment. scene_author's
`--style-notes` are injected as binding bullet rules INSIDE the tier-3 authored prompt, so
piping a whole second prompt there makes two prompts fight (and SYSTEM_MAP already records that
feeding-without-agreement failed: 太标识类).

Safe path, per the user's instruction:
- When a reference is present, run the analyzer per sign (it needs the sign's messages +
  hero_icon), and write `aligned_prompt.txt` + `style_descriptor.json` into the sign folder.
- Record in the manifest: `analyzer_ran: true`, `injected_into_generation: false`,
  the file paths. The human can choose to use the aligned prompt manually.
- Do NOT pass it into `--style-notes`. The fed reference image is already the visual channel
  via scene_author `--ref-image`; SYSTEM_MAP says the image rescues an imperfect text read, so
  this is a recorded artifact, not a generation input. No reference => skip the analyzer.
- The analyzer makes a vision call, so under `--dry-run` it is LISTED in the plan, not run.

---

## 7. PER-SIGN INTENT TEMPLATE (deterministic synthesis)

scene_author serializes the whole `intent` dict into the author prompt (scene_author.py:522),
so the conductor templates one per sign from `context` + the sign, no inference:

```json
{
  "subject":          "<occasion> hand-held sign (手举牌) for <brand>",
  "asset_type":       "<inputs.asset_type>",
  "occasion":         "<context.occasion>",
  "headline_message": "<sign.messages joined by '，'> (exact headline)",
  "feeling":          "<phrase derived from inferred_register: e.g. event_prop -> 'playful, grabbable photo-prop, NOT corporate'>",
  "reference_image":  "<basename of reference_image, or 'logo only'>"
}
```

`feeling` is derived from the DERIVED register (a fixed per-register phrase table), not
re-inferred from free text, so it stays deterministic. `--must-include` carries the sign's
messages (the lines that must appear); if the campaign adds `mandatory_elements` later, they
append here.

---

## 8. RESULTING CONDUCTOR STEP ORDER (and dry-run plan)

```
1. INPUT GATE        --inputs <file> | ask the ~5 questions -> write <out>/inputs.json
2. LOAD BRAND        scene_author.load_brand(brand); fail loudly if no answer key
3. SUBFIELDS         write <out>/subfields.json = { asset_type, **context }
4. REGISTER PREP     [calibrate if ref] -> derive_register(--calibration if ref) -> register_profile.json
                     print the register profile in plain language (calibration gate)
5. PER SIGN (loop over signs[]):
     a. [analyzer if ref] -> sign folder aligned_prompt.txt (recorded, NOT injected)
     b. write intent_<id>.json
     c. scene_author --brand --asset-profile flat_graphic --chroma-contain
                     --register-profile register_profile.json --ref-image <ref>
                     --must-include "<messages>" --intent-file intent_<id>.json
                     --out <out>/sign_<id>
6. APPROVE GATE      unless --no-approve: show draft paths, take nudge, re-run touched sign
7. MANIFEST          <out>/conductor_manifest.json: per-sign cmd + status + outputs,
                     register profile path, calibration outcome, analyzer recorded-not-injected,
                     reference_relationship recorded-not-wired, compliance summary
```

Architecture consequence: the conductor PLANS an ordered list of fully-parameterized command
strings (calibrate, derive_register, analyzer, scene_author, approve). `--dry-run` writes them
to `plan.json` and executes NOTHING (no vision, no Anthropic, no gpt-image-2). Real mode runs
each as ONE synchronous foreground subprocess (CONDUCTOR_SPEC rule 7.1: no background, no
polling). This command-planner shape is what makes the section-6 self-test (which greps
`plan.json` for the real `scene_author.py` / `derive_register.py` invocations) meaningful.

---

## 9. WHAT CHANGED VS CONDUCTOR_SPEC (summary for the diff)

- `inputs.json`: `context` now holds brief_schema_v3 bucket B/D field names (usage_context,
  audience, setting, vibe{formality,playfulness,warmth}, logo_treatment, brand_strictness,
  occasion) instead of `register_hint`. `reference_relationship` added (recorded, not wired).
- Added an explicit `subfields.json` build step (identity pass-through) feeding derive_register.
- Pinned the `calibrate --out -> derive_register --calibration` linkage (spec left it implicit).
- Pinned the analyzer SAFE path (record aligned_prompt.txt; do NOT inject into --style-notes).
- Added the plain-language register calibration gate before the per-sign loop.
- Everything else in CONDUCTOR_SPEC (wrap don't rebuild, human gates, dry-run self-test,
  brand-generality, no hardcoded literals, no git commit) stands unchanged.
```
