# Quickstart: Connect Onboard + Live-runner Into One App (+ UI Touch-up)

Free structural greps first (they prove the WIRING exists), then the human eye + flow check (the real
proof, §II). No paid calls anywhere in this feature.

## Prerequisites

- Python 3.11 `.venv` (run everything as `.venv/bin/python`).
- At least one onboarded brand (e.g. `aia`) so the live-runner dropdown is non-empty.

## 1. Free structural self-tests (NO paid calls)

```bash
# the new wiring test (both nav links, the preselect, the handoff link, no em-dash)
.venv/bin/python test_frontend_nav.py

# no-regression: the frontend server helpers + prior suites unchanged
.venv/bin/python test_frontend_intake.py
.venv/bin/python test_frontend_runner.py
.venv/bin/python test_frontend_stages.py
.venv/bin/python test_reference_upload.py
.venv/bin/python test_onboard.py
```

Expected: each prints `RESULT: N/N checks passed` and exits 0. `test_frontend_nav.py` asserts the WIRING
(presence greps): both pages link both ways; the live-runner reads `?brand=` and targets the brand select;
the onboard success builds a `/?brand=` link; no em-dash. These are the weakest gate; the eye is the proof.

## 2. Server + browser (the REAL proof - human eye, §II; free, no generation)

```bash
pkill -f "frontend/server.py" 2>/dev/null; .venv/bin/python frontend/server.py   # http://localhost:8765
```

(Restart the server so it serves the edited pages; hard-refresh the browser, Cmd/Ctrl-Shift-R.)

Judge by EYE - no spend needed for any of this:
- On `/` (live-runner), the header shows a nav; click "Onboard a brand" -> lands on `/onboard`. From
  `/onboard`, click "Generate a sign" -> back to `/`. One click each way (SC-001).
- Onboard a brand end to end; on success, click "Generate a sign for this brand" -> the live-runner opens
  with THAT brand already selected in the dropdown (SC-003). Then open `/?brand=doesnotexist` -> it falls
  back to the default with no error (SC-004).
- Both pages read as ONE consistent, polished product; the live-runner form is grouped and easy to scan;
  nothing looks broken and the run flow still works (SC-005). Record the eye verdict.

No paid image generation is required to validate this feature; the one paid sign remains the back-half
eye-gate owned by the earlier features (007/008/009), not 010.
