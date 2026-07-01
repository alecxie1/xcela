# Research: Lossless Brief (012)

**Phase 0 output.** No external unknowns; every decision resolves from the code. Key evidence:
`harness/conductor.py` (`_scene_author_thin_argv` ~248, `build_plan` thin loop ~372, `execute`
thin loop ~880, `normalize_dial` 85-101), `harness/scene_author.py` (`assemble_thin_prompt`
846-975, `--style-notes` split-on-";" at ~994 and ~1429), `frontend/index.html` (form controls),
`frontend/server.py:155` + `frontend/runner.py:19-24` (the notes channel), the CJXQ audit runs.

## D1. How asset_type + occasion reach the prompt

**Decision**: Two new scene_author CLI flags (`--asset-type`, `--occasion`), passed verbatim by
`_scene_author_thin_argv`, which gains the two parameters; BOTH conductor call sites (build_plan's
thin loop AND execute's thin loop) pass them from `inputs`. `assemble_thin_prompt` gains
`asset_type=None, occasion=None` and emits one conditional SCENE/SUBJECT section.

**Rationale**: Verbatim pass-through with no intermediate composition keeps the human's words
inspectable at every hop (argv, prompt file). Threading BOTH call sites, and testing the execute
path with the stubbed-`run_step` pattern, is the direct application of the 009 drift bug (real
runs silently dropped a field build_plan carried; caught only by the eye).

**Alternatives considered**: one combined `--scene` string composed in the conductor: rejected,
the conductor would be gluing words together (judgment creep) and the prompt could no longer
attribute which field said what. Reusing `--intent-file`: rejected, that is the kit/legacy tier-3
channel and the thin route deliberately does not read it.

## D2. Scene section placement and framing (the leakage defense)

**Decision**: The section renders immediately after the opener, before the HEADLINE block:

```
SCENE / SUBJECT (compositional context ONLY, not text: no words from this section may be
painted anywhere on the asset):
  Asset: <asset_type verbatim>
  Occasion: <occasion verbatim>
```

Lines render only for non-empty fields; when both are empty the section is absent entirely
(FR-003 byte-identity). The existing only-the-headline guard and text negatives are untouched.

**Rationale**: Placement before the HEADLINE block means the "these are the ONLY words" contract
still reads as the last word on text. The do-not-paint framing mirrors the mandatory-elements
clause's proven "do NOT render the instruction text itself" wording. The residual risk (gpt
paints Chinese it sees: the slogan lesson) cannot be closed structurally, which is why SC-007's
eye-gate explicitly checks for painted scene words.

**Alternatives considered**: paraphrasing/translating occasion into safe English: rejected
(model-based rewriting, non-deterministic, violates verbatim honesty). Putting scene text only in
the manifest: rejected, that is the current defect.

## D3. Design notes: frontend-only, riding the existing channel

**Decision**: Add a `design_notes` textarea to the form. On ANY run (first or nudge), the
frontend composes `style_notes = [design_notes, nudge].filter(non-empty).join("; ")` into the
form JSON it already sends. Server, runner, conductor, scene_author: zero changes; the channel
already splits `--style-notes` on ";" into the multi-note list that renders as the binding
design-rules block.

**Rationale**: The ";"-join IS the channel's existing multi-note contract (scene_author splits on
";" at both consumption sites). Reusing it end to end means US2 is a form-only change and FR-005
(nudge appends, not replaces) falls out of the join. Known quirk, documented not hidden: a ";"
inside a single note splits it into two notes; both halves still land in the same binding block,
so the instruction survives, at worst as two bullets.

**Alternatives considered**: a new `design_notes` key through server/runner/conductor: rejected,
a second channel to the same prompt block violates the one-home rule and widens the test surface
for zero user value.

## D4. Retiring audience + warmth (and the hero_icon non-event)

**Decision**: Delete the two controls (and their JS reads) from `index.html`.
`inputs_writer.to_inputs` stays tolerant: absent form keys produce the same empty/None values it
already produces today, and legacy JSON carrying the fields flows through verbatim (the CLI path
never touches inputs_writer). The manifest's inert-provenance recording is untouched. hero_icon:
the form has NO control today (only the writer's tolerant read), so US3's hero_icon claim is
satisfied by leaving the writer tolerant; nothing to delete.

**Rationale**: FR-006 constrains the FORM surface, not the JSON contract; keeping the writer
tolerant is the cheapest back-compat guarantee and keeps old saved briefs bit-runnable.

**Alternatives considered**: stripping the fields from the writer output too: rejected, breaks
byte-compat of inputs.json for no gain, and the manifest provenance intentionally records them.

## D5. The dial dropdown values

**Decision**: `<select id="reference_relationship">` with exactly three options whose SUBMITTED
values are `extend`, `match style`, `mood` (labels carry plain-language descriptions, e.g.
"Extend it: keep this look, change the message"). Those three strings hit `normalize_dial`'s
exact-value and keyword paths deterministically (`extend` in DIAL_VALUES; "match" -> match_style;
"mood" -> mood). `normalize_dial` itself is unchanged, so legacy free-text JSON still normalizes.

**Rationale**: 1:1 deterministic mapping with zero engine change; the engine keeps its lenient
parser for legacy inputs while the form can no longer produce lossy prose.

**Alternatives considered**: submitting the canonical `match_style` token: fine too, but the
spaced form matches how the current example text reads and both map identically; renaming lanes
or adding a fourth: out of scope (014 territory).

## D6. Test surface

**Decision**: One new `test_lossless_brief.py` with: (1) scene-section VALUE assertions on
`assemble_thin_prompt` (exact strings present; both-blank case byte-identical to a pre-feature
assembly captured by calling with the parameters omitted); (2) argv threading asserted on BOTH
`build_plan` steps and captured `execute` commands (stubbed `run_step`, the render_modes check-5
pattern); (3) form-surface greps: absent audience/warmth controls, no free-text dial input,
3-option select present, design_notes present, no sign-era label, new verbatim label wording
present (greps declared the weakest gate, per the 010 precedent); (4) writer back-compat: legacy
form state with audience/warmth still lands in context verbatim; absent keys still produce a
valid brief.

**Rationale**: Each assertion names a property a wrong build fails: dropped threading, empty
scaffolding, plan-only wiring, dead controls resurrected, label regression, back-compat break.

**Alternatives considered**: extending three existing suites instead: rejected, this feature's
surface spans conductor+scene_author+frontend and a single suite keeps the falsifiable map in
one place (matching how 011 did it).
