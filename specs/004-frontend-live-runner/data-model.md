# Phase 1 Data Model: Frontend Live-Runner (single-sign)

Entities flow: form state → single-sign inputs JSON → (conductor run) → run-dir stages → taste action
→ (new run dir on nudge). "Verbatim" means every literal value the operator typed appears byte-for-
byte downstream; nothing is inferred, rephrased, or dropped.

---

## Entity: Single-sign Form State (browser)

The feature-002 fields for ONE sign + the brand. Rendered as labeled inputs (no NL prose box).

| Field | Type | Notes |
|-------|------|-------|
| `brand` | enum (dropdown) | over existing `answer_keys/*.json`; selects, never authors |
| `asset_type` | string | free text |
| `format_size` | string | e.g. `60x40cm` (002 `format_size.py` resolves it) |
| `reference_image` | file path | REQUIRED in v1; Run blocked without it |
| `reference_relationship` | string | e.g. `template - extend this series` |
| `context.vibe.formality/playfulness/warmth` | int 0-10 | three sliders; DRIVE the register branch |
| `context.logo_treatment` | enum | omit / subtle / faithful |
| `context.brand_strictness` | enum | expressive departure / ... |
| `context.occasion` / `context.usage_context` / `context.audience` | string | free text |
| `mandatory_elements` / `forbidden_elements` | list[string] | chips; verbatim (e.g. 分别画叉) |
| the ONE sign: `messages` | list[string] | the headline line(s), verbatim |
| sign `mandatory_elements` / `forbidden_elements` | list[string] (optional) | per-sign, verbatim |

**Validation**: a blank optional field is recorded empty (honest null), never invented. No value is
transformed.

---

## Entity: Single-sign Inputs JSON (`inputs_writer` output)

The 002-shape artifact the conductor consumes, with EXACTLY ONE `signs[]` entry.

```json
{
  "asset_type": "...", "format_size": "60x40cm",
  "reference_image": "/abs/path/ref.png", "reference_relationship": "...",
  "mandatory_elements": ["分别画叉"], "forbidden_elements": [],
  "context": { "usage_context": "...", "audience": "...",
               "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
               "logo_treatment": "omit", "brand_strictness": "expressive departure", "occasion": "..." },
  "signs": [ { "id": "s1", "messages": ["..."], "hero_icon": null } ]
}
```

**Rules (falsifiable)**:
- `len(signs) == 1` (single-sign invariant).
- Every typed literal appears byte-for-byte (`messages`, `mandatory_elements`, the three vibe ints).
- The JSON passes `conductor.validate_inputs` (the form cannot emit a brief the CLI rejects).
- No field rephrased, reordered, or inferred (FR-003).

---

## Entity: Run / Attempt

One `output/run_<brand>_<timestamp>/` directory = one (re)run attempt. A first run and each nudge
each produce a NEW attempt dir; prior attempts persist so the operator can compare. Identified by the
run-dir name (the `<id>` in the HTTP routes).

---

## Entity: Run Stages (`run_view` output, polled progressively)

Read from the attempt's run dir; each stage is present-with-content OR absent-with-note.

| Stage | Source artifact | Shown |
|-------|-----------------|-------|
| brief echo | `inputs.json` / the written inputs | the fields the conductor received |
| register / dial | `register_profile.json` | inferred_register, formality/playfulness, anchors_held, locks_flexed |
| assembled prompt | `sign_s1/final_prompt.txt` | the full prompt text |
| generated sign | `sign_s1/generated.png` | the image |
| notes | `conductor_manifest.json` | honest-null / needs_review notes |

**Rules**: stages render PROGRESSIVELY as artifacts land (dial + prompt before the image, D3). A
missing artifact is reported as absent + the manifest note (honest null, §V), never fabricated. The
reader consumes the artifact PATHS, not a parallel in-UI computation (SC-003).

---

## Entity: Taste Action

One of:
- `approve` → stop; the current attempt's sign is the deliverable.
- `nudge(note)` → re-invoke the conductor with `--style-notes "<note>"`; a NEW attempt dir is
  produced and the note appears as a binding clause in its `final_prompt.txt`.

(Reject-without-rerun is out of scope.)

---

## Entity: Conductor Run Trigger (`runner.build_conductor_argv` output)

The CLI invocation the UI builds (pure; testable without executing):

```
conductor.py --brand <brand> --thin --no-approve --inputs <single_sign.json> [--style-notes "<note>"]
```

**Rules (falsifiable)**: always carries `--thin` + `--no-approve` + `--inputs`; carries
`--style-notes` IFF a nudge note is supplied; never passes `--out` (so each call makes a new run dir).

---

## Falsifiable properties (seed the tests; constitution §III)

- `inputs_writer(form_state)` → JSON with exactly one `signs[]` entry; `messages`,
  `mandatory_elements`, and the three vibe integers equal the typed values byte-for-byte; output
  passes `conductor.validate_inputs`.
- `run_view(run_dir)` over a synthetic dir with `register_profile.json` + `final_prompt.txt` but NO
  `generated.png` → register + prompt present, image ABSENT (progressive surface); a missing artifact
  yields absent + the manifest note, never a fabricated value.
- `build_conductor_argv(inputs, brand)` → contains `--thin --no-approve --inputs`, no `--out`;
  `build_conductor_argv(inputs, brand, style_notes="x")` additionally contains `--style-notes x`.
- conductor `--style-notes "x"` (dry-run) → the thin `scene_author` argv carries `--style-notes x`.
- the thin route runs end-to-end from one CLI command with the frontend absent (standalone).
