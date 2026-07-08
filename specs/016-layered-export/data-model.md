# Data Model: Layered Export (016)

## Entities

### Element (in-memory, produced by `enumerate_elements`)
| Field | Type | Rule |
|---|---|---|
| id | str | stable, deterministic: `text_1..N` (message order), `logo`, `product_1..N` (input order) |
| kind | str | `text` \| `logo` \| `product` |
| text | str | verbatim message line; present iff kind=text |
| ref | str | original asset path; present iff kind=logo/product; MUST exist on disk |

Enumeration sources: `inputs.json signs[0].messages`, brand key `logo_path` (gated on membership
in `run_manifest generation.reference_image`), `inputs.json product_images`. Zero elements =
refuse to plan (SystemExit, named reason).

### Export plan (free, returned by `export_plan` and `GET /run/<id>/export/plan`)
```json
{
  "elements": [ {"id": "text_1", "kind": "text", "text": "瓜田冰爽特供"}, ... ],
  "calls": 6,
  "per_image_usd": 0.08,
  "cost_usd": 0.48,
  "source_image": ".../sign_s1/generated.png",
  "size": "1536x1024"
}
```
`calls = len(elements) + 1` (the background). `size` from `run_manifest generation.size`.

### Export state (`<run_dir>/export_state.json`)
```json
{
  "state": "exporting" | "done" | "failed",
  "plan": { ...export plan... },
  "cost_stated": "$0.48",
  "created": "ISO", "updated": "ISO",
  "started_at": "ISO",      // set when a WORKER adopts the state (absent on a fresh
                            // server-side reservation)
  "pid": 12345,             // the adopting worker's process id (liveness probe)
  "error": "..."            // failed only
}
```

State machine (ownership = started_at + a LIVE pid; `state_blocks_new_export` is the one
arbiter every surface calls):
```
(absent) --POST/CLI (gate done, plan valid; state written BEFORE first paid call)--> exporting
exporting(live)  --all calls + zip complete--> done
exporting(live)  --ANY interruption incl. SIGINT (BaseException)--> failed
exporting(live)  --repeat request--> no-op (no second spend, even mid-flight)
exporting(STUCK: unadopted reservation, or dead pid after a hard kill)
                 --explicit retry (cost restated, recovered_stuck)--> exporting
done             --repeat request--> no-op
failed           --explicit retry (cost restated; stale export_error.txt cleared)--> exporting
```
Preconditions to leave (absent): `gate_state.state == "done"`, source image exists, >=1 element.
Restart safety: every UI render derives purely from this file + the manifest; a stuck
exporting renders as `stale: true` so the UI offers the retry the machine accepts.
Export failures write `export_error.txt` (NEVER `run_error.txt`, which means the RUN failed).

### Layer record (one entry in `<run_dir>/export_manifest.json`, appended progressively)
| Field | Type | Rule |
|---|---|---|
| id / kind / text / ref | | copied from Element |
| prompt | str | the exact isolation prompt used |
| status | str | `ok` \| `null` |
| note | str | null reason (named threshold) or "" |
| opaque_frac | float | from strip_chroma |
| stray_component_px_dropped | int | from strip_chroma (dropped detached pieces, visible) |
| despilled_px | int | from strip_chroma |
| green_residual_px_in_preview | int | from strip_chroma |
| bbox | [x0,y0,x1,y1] | opaque bounding box (position-drift measurement); ok only |
| files | dict | ok: {cutout, preview}; null: {raw} |

Manifest root: `{"layers": [...], "background": {"prompt": ..., "model_continued": true,
"files": {...}}, "source_image": ..., "size": ...}`.

### layers.zip (`<run_dir>/layers.zip`)
| Member | When |
|---|---|
| export_manifest.json | always |
| background.png + background_preview.jpg | always (unkeyed, model-continued) |
| `<id>.png` (RGBA cutout) + `<id>_preview.jpg` | per ok layer |
| `<id>_raw.png` | per null layer (manual salvage; NO cutout ever) |

## File layout added to a run dir (ONLY new files; nothing pre-existing is rewritten)
```
run_*/
├── export_state.json
├── export_manifest.json
├── export/
│   ├── text_1/{isolated.png, cutout.png, preview_white.png, preview.jpg}
│   ├── logo/{...}
│   ├── product_1/{...}
│   └── background/{background.png, background_preview.jpg}
└── layers.zip
```
