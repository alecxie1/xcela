#!/usr/bin/env python3
"""test_frontend_nav.py - falsifiable self-test for the unified frontend (feature 010).

No paid calls. HONESTLY LABELLED: these are PRESENCE GREPS (the weakest gate, §III). They fail a genuinely
wrong build (one-directional nav, a missing handoff link, a preselect that never reads the param, an
em-dash) but they do NOT prove the look or the flow - the HUMAN EYE is the real proof (§II), and here it is
FREE (nav + flow + look, no generation). Covers:
  1. no em-dash in either page's user-facing text (FR-009).
  2. US1: both pages carry BOTH nav links (bidirectional) + an active-view marker.
  3. US2: onboard save-success builds a /?brand= handoff link; the live-runner reads ?brand= and targets
     the brand select.

Run:  .venv/bin/python test_frontend_nav.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
INDEX = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
ONBOARD = (REPO / "frontend" / "onboard.html").read_text(encoding="utf-8")


def check1_no_em_dash():
    i = "—" not in INDEX
    o = "—" not in ONBOARD
    return i and o, f"index no em-dash={i}; onboard no em-dash={o}"


def check2_bidirectional_nav_and_active():
    # both pages link BOTH ways (a one-directional build fails)
    idx_to_onboard = 'href="/onboard"' in INDEX
    onb_to_index = 'href="/"' in ONBOARD
    # active-view marker on each page (FR-001; C1 - make it structural, not eye-only)
    idx_active = 'aria-current="page"' in INDEX
    onb_active = 'aria-current="page"' in ONBOARD
    passed = idx_to_onboard and onb_to_index and idx_active and onb_active
    return passed, (f"index->/onboard={idx_to_onboard}; onboard->/={onb_to_index}; "
                    f"index active={idx_active}; onboard active={onb_active}")


def check3_handoff_and_preselect():
    # onboard save-success builds a /?brand= handoff link
    handoff = "/?brand=" in ONBOARD
    # the live-runner reads the brand query param AND targets the brand select
    reads_param = ("URLSearchParams" in INDEX or "location.search" in INDEX) and '"brand"' in INDEX
    targets_select = '$("brand")' in INDEX or 'getElementById("brand")' in INDEX
    passed = handoff and reads_param and targets_select
    return passed, f"onboard handoff /?brand={handoff}; index reads brand param={reads_param}; targets select={targets_select}"


CHECKS = [
    ("no em-dash in either page (FR-009)", check1_no_em_dash),
    ("bidirectional nav + active-view marker on both pages (US1)", check2_bidirectional_nav_and_active),
    ("onboard /?brand= handoff + live-runner preselect wiring (US2)", check3_handoff_and_preselect),
]


def main():
    print("=" * 78)
    print("test_frontend_nav.py - falsifiable self-test (010, presence greps, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} - {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed  (presence-level; the human eye is the real proof)")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
