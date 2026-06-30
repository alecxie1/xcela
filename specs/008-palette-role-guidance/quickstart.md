# Quickstart: Role-aware Brand Palette + Exactly-one-primary

Free structural validation first (constitution: build + verify on the free surfaces before any paid
call), then the human eye-gate on a real sign.

## Prerequisites

- Python 3.11 `.venv` (run everything as `.venv/bin/python`).
- A brand answer_key with several roled colors (e.g. `aia`), or onboard a fresh one through the gate.

## 1. Free structural self-tests (NO paid calls)

```bash
# the new feature test (role instructions + blank fallback + background guard + anchor + gate sync)
.venv/bin/python test_palette_roles.py

# validator + onboarding regression (now exactly-one-primary)
.venv/bin/python test_brand_key.py
.venv/bin/python test_onboard.py

# generation regression: the thin route still assembles correctly
.venv/bin/python test_thin_route.py
```

Expected: each prints `RESULT: N/N checks passed` and exits 0. The new test asserts (each a VALUE a wrong
build cannot satisfy):
- a key with primary + secondary + accent (+ background + text) -> the assembled prompt has EACH color's
  hex AND its role instruction (accent "use sparingly"; secondary "support the primary"; text "legible").
- a blank/unknown-role color still appears with the "part of the brand palette" fallback.
- background guard: present with a reference, absent (fallback) without a reference, color still listed.
- the single-primary anchor is unchanged (`_primary_color_hex`).
- the gate (onboard.html options + intake.py prompt) offers exactly the named `ROLE_GUIDANCE` roles.
- `validate_lean_key` raises on 0 and on >=2 primaries, passes on exactly 1.

## 2. Onboarding gate smoke (free)

```bash
.venv/bin/python frontend/server.py    # http://localhost:8765, open /onboard
```

- Confirm the color role dropdown offers all 5 roles (primary / secondary / accent / background / text)
  and the "exactly one primary" instruction is visible.
- Try saving with two colors marked primary -> a clear in-browser error, no key written.

## 3. Human eye-gate (the one paid sign, SC-007; NOT automated)

```bash
.venv/bin/python frontend/server.py    # open /, pick a reference, run (paid, about $0.08)
```

Generate a sign for a brand whose palette has accent / text / background roles, and judge by EYE
(constitution §II): does the output use the accent as small highlights, the text color for type, the
background as the field, with the primary dominant - not just the primary everywhere? Record the verdict
in `SYSTEM_MAP.md`. This folds into the existing back-half paid run; 008 ships no separate paid run.
