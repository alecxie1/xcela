# Contract: Lossless Brief (012)

Behavior table for the brief-to-prompt path. Verified by `test_lossless_brief.py` (free, no paid
calls). "Both call sites" means build_plan's thin argv AND the argv `execute()` constructs with
`run_step` stubbed (the 009 drift-guard pattern).

## A. Scene/subject threading

| # | asset_type | occasion | Obligation |
|---|---|---|---|
| 1 | non-empty | non-empty | prompt contains a SCENE/SUBJECT section with BOTH values verbatim; section frames itself as context that must not be painted; the HEADLINE only-words guard is byte-unchanged |
| 2 | non-empty | empty | section present with the Asset line only; no empty Occasion scaffolding |
| 3 | empty | empty | prompt BYTE-IDENTICAL to a pre-feature assembly (no section, no blank lines) |
| 4 | any | any | `--asset-type` / `--occasion` appear in the scene_author argv at BOTH call sites exactly when non-empty |

## B. Design notes channel

| # | first-run notes | nudge | Obligation |
|---|---|---|---|
| 5 | "products realistic" | none | binding block contains the note verbatim on the first run |
| 6 | "products realistic" | "bolder type" | frontend submits the ";"-join; the split channel renders BOTH as binding rules (append, never replace) |
| 7 | empty | empty | no binding block (byte-identical to today) |

Channel invariant: server.py, runner.py, conductor `--style-notes`, and scene_author's ";"-split
are all UNCHANGED; only the form composes the string.

## C. Form surface (grep gate; declared the weakest gate, 010 precedent)

| # | Obligation |
|---|---|
| 8 | no `id="audience"` and no `id="warmth"` control in the served page |
| 9 | `id="reference_relationship"` is a select with exactly the 3 option values `extend`, `match style`, `mood`, and no free-text path |
| 10 | a design-notes control exists and its value reaches the submitted form JSON's `style_notes` composition |
| 11 | no "Sign message" era label; the message label states the verbatim-text contract (exact words rendered, the only words allowed) |
| 12 | no em-dash in any new label/description/prompt-header text |

## D. Back-compat

| # | Obligation |
|---|---|
| 13 | a legacy form state carrying audience/warmth still lands in `context` verbatim via inputs_writer; absent keys still produce a valid brief |
| 14 | a legacy inputs JSON with free-text reference_relationship still normalizes through `normalize_dial` unchanged (engine untouched) |
| 15 | register engine (011 suite), render modes (009 suite), conductor + frontend suites all pass unchanged |

## E. Deferred human eye-gate (SC-007)

One paid re-brief of the CJXQ watermelon post: subject fidelity visibly improved over the pre-012
run AND zero scene/occasion words painted on the asset (the slogan-lesson check). Judged by the
operator, recorded in SYSTEM_MAP.
